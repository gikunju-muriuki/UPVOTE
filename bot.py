import os
import requests
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

# Initialize lightsteem connection correctly
try:
    # Pass keys directly into the main Client instantiation
    client = Client(
        nodes=["https://api.steemit.com"],
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

def get_latest_post(author):
    """Fetches the latest post data using fallback public RPC nodes from the browser bot."""
    payload = {
        "jsonrpc": "2.0",
        "method": "condenser_api.get_discussions_by_author_before_date",
        "params": [author, "", "2026-12-31T23:59:59", 1],
        "id": 1
    }
    # These match the working nodes shown in your screenshot
    nodes = [
        "https://api.steemit.com",
        "https://api.moecki.online",
        "https://api.justyy.com",
        "https://api.amarbangla.net"
    ]
    
    for url in nodes:
        try:
            # Added a user-agent header to look like a standard web browser request
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("result") and len(data["result"]) > 0:
                    # Explicitly return the first post dictionary from the list
                    return data["result"][0]
        except Exception as e:
            print(f"Node {url} failed: {e}")
            continue
    return None


# 3. Execution Logic
updated_history = False

for author in TARGET_AUTHORS:
    post = get_latest_post(author)
    if not post:
        print(f"Could not retrieve any posts for {author}.")
        continue
        
    permlink = post.get("permlink")
    if not permlink:
        print(f"Could not extract permlink for {author}.")
        continue
        
    post_identifier = f"@{author}/{permlink}"
    
    # Verify if it's a root post (not a comment reply) and hasn't been voted on yet
    if post.get("parent_author") == "" and post_identifier not in voted_history:
        print(f"New post found: {post_identifier}. Attempting to upvote...")
        
        try:
            # Broadcast format (Weight is scaled 0 to 10000; 100% = 10000)
            scaled_weight = int(VOTE_WEIGHT * 100)
            
            client.broadcast.vote(
                voter=MY_ACCOUNT,
                author=author,
                permlink=permlink,
                weight=scaled_weight
            )
            print(f"Successfully upvoted {post_identifier}!")
            voted_history.add(post_identifier)
            updated_history = True
        except Exception as e:
            print(f"Voting failed for {post_identifier}: {e}")
    else:
        print(f"Post {post_identifier} already processed or is a comment reply.")



# Save history if we performed updates
if updated_history:
    with open(HISTORY_FILE, "w") as f:
        for item in sorted(voted_history):
            f.write(f"{item}\n")
