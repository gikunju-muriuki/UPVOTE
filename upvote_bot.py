import os
import random
import time
from beem import Steem
from beem.account import Account
from beem.comment import Comment

# =========================================================================
# GITHUB ACTIONS RUNTIME DELAY BUFFER
# =========================================================================
upvote_jitter = random.randint(1, 3)
total_delay_seconds = (1 * 1) + upvote_jitter

print("Post verification handshake initialized...")
print(
    f"Waiting {total_delay_seconds / 60:.1f} minutes to guarantee the post is live on the blockchain..."
)
time.sleep(total_delay_seconds)
# =========================================================================

# 1. Configuration
MY_ACCOUNT = "gikunju"
TARGET_AUTHOR = "blog.god"
VOTE_WEIGHT = 100              # 1 to 100
BLOG_FETCH_LIMIT = 20          # How many recent blog entries to inspect
MAX_UPVOTES_PER_RUN = 9        # Safety cap per workflow run to protect VP/RC
VOTE_INTERVAL_SECONDS = 4      # Safely above Steem's 3-second minimum vote interval
STEEM_NODES = [
    "https://api.moecki.online",
    "https://api.campingclub.me",
    "https://api2.justyy.com",
    "https://api3.justyy.com",
    "https://steem-proxy.gikunju.workers.dev",
]

# 2. Extract Key from GitHub Secrets
MY_PRIVATE_POSTING_KEY = os.getenv("STEEM_POSTING_KEY")

if not MY_PRIVATE_POSTING_KEY:
    print("Error: STEEM_POSTING_KEY secret is missing!")
    exit(1)

try:
    print(f"Connecting to nodes: {STEEM_NODES}")
    stm = Steem(node=STEEM_NODES, keys=[MY_PRIVATE_POSTING_KEY])

    target_account = Account(TARGET_AUTHOR, blockchain_instance=stm)
    blog_history = target_account.get_blog(limit=BLOG_FETCH_LIMIT)

    if not blog_history:
        print(f"No posts found for account @{TARGET_AUTHOR}.")
        exit(0)

    upvoted_count = 0

    for post in blog_history:
        if upvoted_count >= MAX_UPVOTES_PER_RUN:
            print(f"Reached per-run cap of {MAX_UPVOTES_PER_RUN} upvotes. Stopping.")
            break

        author = getattr(post, "author", None)
        permlink = getattr(post, "permlink", None)

        if not author or not permlink:
            continue

        # Optional: skip resteemed posts from other authors
        if author != TARGET_AUTHOR:
            print(f"Skipping resteem from @{author}/{permlink}")
            continue

        identifier = f"@{author}/{permlink}"
        voters = []

        if hasattr(post, "active_votes") and post.active_votes:
            voters = [v["voter"] for v in post.active_votes if "voter" in v]

        if MY_ACCOUNT in voters:
            print(f"Skipping (already upvoted): {identifier}")
            continue

        print(f"Unvoted post found: {identifier}. Upvoting with {VOTE_WEIGHT}% power...")
        try:
            target_comment = Comment(identifier, blockchain_instance=stm)
            target_comment.upvote(weight=VOTE_WEIGHT, voter=MY_ACCOUNT)
            upvoted_count += 1
            print(f"Upvote broadcasted ({upvoted_count}/{MAX_UPVOTES_PER_RUN}).")
            print(f"Waiting {VOTE_INTERVAL_SECONDS}s to respect Steem's 3-second vote interval...")
            time.sleep(VOTE_INTERVAL_SECONDS)
        except Exception as vote_err:
            print(f"Warning: Failed to upvote {identifier}: {vote_err}")
            time.sleep(VOTE_INTERVAL_SECONDS)

    print(f"Finished run. Total new upvotes broadcasted: {upvoted_count}")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    exit(1)
