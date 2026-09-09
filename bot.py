import os
import time
import requests
from steem import Steem  # If utilizing full framework
from steem.commit import Commit

# 1. Configuration variables
MY_ACCOUNT = "your_steem_username"  # <-- Change to your username
TARGET_AUTHORS = ["target_user_1", "target_user_2"]  # <-- Authors to track
VOTE_WEIGHT = 100.0  # 100.0 = 100% vote weight
HISTORY_FILE = "voted_posts.txt"

# 2. Grab private key securely from GitHub Secrets
MY_PRIVATE_POSTING_KEY = os.getenv("STEEM_POSTING_KEY")

if not MY_PRIVATE_POSTING_KEY:
    print("Error: STEEM_POSTING_KEY secret is missing!")
    exit(1)

# Initialize Steem connection
try:
    s = Steem(keys=[MY_PRIVATE_POSTING_KEY])
    commit = Commit(steem_instance=s)
except Exception as e:
    print(f"Error initializing Steem connection: {e}")
    exit(1)

# Load previously voted posts to prevent duplicate voting
voted_history = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        voted_history = set(line.strip() for line in f if line.strip())

def get_latest_post(author):
    """Fetches the absolute latest post data for a given author via Steem RPC."""
    payload = {
        "jsonrpc": "2.0",
        "method": "condenser_api.get_discussions_by_author_before_date",
        "params": [author, "", "2026-12-31T23:59:59", 1],
        "id": 1
    }
    try:
        response = requests.post("https://steemit.com", json=payload, timeout=10)
        data = response.json()
        if data.get("result"):
            return data["result"][0]
    except Exception as e:
        print(f"Failed to fetch data for {author}: {e}")
    return None

# 3. Execution Logic
updated_history = False

for author in TARGET_AUTHORS:
    post = get_latest_post(author)
    if not post:
        continue
        
    permlink = post["permlink"]
    post_identifier = f"@{author}/{permlink}"
    
    # Verify if it's a root post (not a comment reply) and hasn't been voted on yet
    if post.get("parent_author") == "" and post_identifier not in voted_history:
        print(f"New post found: {post_identifier}. Attempting to upvote...")
        
        try:
            commit.vote(
                identifier=post_identifier,
                weight=VOTE_WEIGHT,
                account=MY_ACCOUNT
            )
            print(f"Successfully upvoted {post_identifier}!")
            voted_history.add(post_identifier)
            updated_history = True
        except Exception as e:
            print(f"Voting failed for {post_identifier}: {e}")
    else:
        print(f"No new posts found for {author} (or already upvoted).")

# Save history if we performed updates
if updated_history:
    with open(HISTORY_FILE, "w") as f:
        for item in sorted(voted_history):
            f.write(f"{item}\n")
