import os
from beem import Steem
from beem.account import Account

# 1. Configuration
MY_ACCOUNT = "bnwt"            # Your Steem account name
TARGET_AUTHOR = "targetusername"  # The account you want to auto-upvote
VOTE_WEIGHT = 100.0            # Vote weight percentage (1.0 to 100.0)
PROXY_URL = "https://steem-proxy.gikunju.workers.dev"

# 2. Extract Key from GitHub Secrets
MY_PRIVATE_POSTING_KEY = os.getenv("STEEM_POSTING_KEY")

if not MY_PRIVATE_POSTING_KEY:
    print("Error: STEEM_POSTING_KEY secret is missing!")
    exit(1)

try:
    print(f"Connecting to node via proxy: {PROXY_URL}")
    stm = Steem(node=[PROXY_URL], keys=[MY_PRIVATE_POSTING_KEY])
    
    # Load targeted user's account history
    target_account = Account(TARGET_AUTHOR, blockchain_instance=stm)
    
    # Get the single most recent blog post entry
    blog_history = target_account.get_blog(limit=1)
    
    if not blog_history:
        print(f"No posts found for account @{TARGET_AUTHOR}.")
        exit(0)
        
    latest_post = blog_history[0]
    post_author = latest_post['author']
    post_permlink = latest_post['permlink']
    identifier = f"@{post_author}/{post_permlink}"
    
    print(f"Analyzing latest post: {identifier}")
    
    # Check if you have already upvoted by reading active_votes dictionary safely
    voted_users = [v['voter'] for v in latest_post.get('active_votes', [])]
    
    if MY_ACCOUNT in voted_users:
        print(f"Skipping. You have already upvoted this post.")
    else:
        print(f"New post detected! Upvoting with {VOTE_WEIGHT}% power...")
        # Direct broadcast via the initialized client wrapper
        stm.vote(identifier, VOTE_WEIGHT, account=MY_ACCOUNT)
        print("Upvote successfully broadcasted.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    exit(1)
