import os
from beem import Steem
from beem.account import Account
from beem.comment import Comment

# 1. Configuration
MY_ACCOUNT = "gikunju"            # Your Steem account name
TARGET_AUTHOR = "bnwt"            # The account you want to auto-upvote
VOTE_WEIGHT = 100                 # FIX: Defined weight as integer (1 to 100)
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
        
    # extract the first object instance from the history list array
    latest_post = blog_history[0]
    author = latest_post.author
    permlink = latest_post.permlink
    identifier = f"@{author}/{permlink}"
    
    print(f"Analyzing latest post: {identifier}")
    
    # Safely pull the active votes using property access methods
    voters = []
    if hasattr(latest_post, 'active_votes') and latest_post.active_votes:
        voters = [v['voter'] for v in latest_post.active_votes]
    
    if MY_ACCOUNT in voters:
        print(f"Skipping. You have already upvoted this post.")
    else:
        print(f"New post detected! Upvoting with {VOTE_WEIGHT}% power...")
        
        # Instantiate a robust Comment target instance
        target_comment = Comment(identifier, blockchain_instance=stm)
        
        # FIX: Broadcast via the native object module wrapper
        target_comment.upvote(weight=VOTE_WEIGHT, voter=MY_ACCOUNT)
        print("Upvote successfully broadcasted.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    exit(1)
