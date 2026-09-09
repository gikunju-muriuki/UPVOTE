import os
from lightsteem.client import Client

# 1. Configuration variables
MY_ACCOUNT = "gikunju"  
TARGET_AUTHORS = ["bnwt"]
VOTE_WEIGHT = 100.0  # 100.0 = 100% vote weight
HISTORY_FILE = "voted_posts.txt"

# 2. Grab private key securely from GitHub Secrets
MY_PRIVATE_POSTING_KEY = os.getenv("STEEM_POSTING_KEY")

if not MY_PRIVATE_POSTING_KEY:
    print("Error: STEEM_POSTING_KEY secret is missing!")
    exit(1)

# Initialize lightsteem with native official fallback nodes
try:
    client = Client(
        nodes=[
            "https://steemit.com",
            "https://steemitdev.com",
            "https://moecki.online"
        ],
        keys=[MY_PRIVATE_POSTING_KEY]
    )
except Exception as e:
    print(f"Error initializing Steem connection: {e}")
    exit(1)

# Load previously voted posts to prevent duplicate voting
voted_history = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        voted_history = set(line.strip() for line in f if line.strip())

def get_latest_post_native(author):
    """Fetches the latest blog entry directly via lightsteem's native client."""
    try:
        # Use the highly resilient condenser_api get_blog method
        # It asks for the latest entry (entry_id 0) and pulls 1 item back
        blog_entries = client.get_blog(author, 0, 1)
        if blog_entries and len(blog_entries) > 0:
            # Extract the core post object out of the blog entry structure
            return blog_entries[0]["comment"]
    except Exception as e:
        print(f"Native blockchain data fetch failed: {e}")
    return None

# 3. Execution Logic
updated_history = False

for author in TARGET_AUTHORS:
    print(f"Checking live blockchain feed for user: {author}...")
    post = get_latest_post_native(author)
    
    if not post:
        print(f"CRITICAL: Failed to communicate with the Steem blockchain entirely.")
        continue
        
    permlink = post.get("permlink")
    author_of_post = post.get("author")
    
    if not permlink or not author_of_post:
        print(f"Could not extract structural fields. Post data returned: {post}")
        continue
        
    post_identifier = f"@{author_of_post}/{permlink}"
    
    # Verify that it is an original post by the target, not a reblog
    is_original_post = (author_of_post.lower() == author.lower())
    
    if is_original_post and post_identifier not in voted_history:
        print(f"SUCCESS: New original post found: {post_identifier}. Upvoting now...")
        
        try:
            # Scaled format: 100% weight = 10000
            scaled_weight = int(VOTE_WEIGHT * 100)
            
            client.broadcast.vote(
                voter=MY_ACCOUNT,
                author=author_of_post,
                permlink=permlink,
                weight=scaled_weight
            )
            print(f"Upvote successfully broadcasted for {post_identifier}!")
            voted_history.add(post_identifier)
            updated_history = True
        except Exception as e:
            print(f"Voting transaction failed: {e}")
    else:
        if not is_original_post:
            print(f"Skipped: The latest item found on @{author}'s blog is a reblog.")
        else:
            print(f"Skipped: Post {post_identifier} was already upvoted in a past run.")

# Save history if updates occurred
if updated_history:
    with open(HISTORY_FILE, "w") as f:
        for item in sorted(voted_history):
            f.write(f"{item}\n")
