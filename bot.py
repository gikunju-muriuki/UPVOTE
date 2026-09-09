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
    """Fetches the absolute latest post object from an author's live blog feed."""
    payload = {
        "jsonrpc": "2.0",
        "method": "bridge.get_account_posts",
        "params": {
            "sort": "blog",
            "account": author,
            "limit": 1
        },
        "id": 1
    }
    
    nodes = [
        "https://api.steemit.com",
        "https://moecki.online",
        "https://justyy.com",
        "https://amarbangla.net"
    ]
    
    for url in nodes:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("result") and len(data["result"]) > 0:
                    # FIXED: Extract index 0 immediately to return the dictionary object
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
    author_of_post = post.get("author")
    
    if not permlink or not author_of_post:
        print(f"Could not extract structural data details for {author}.")
        print(f"Debug post structure: {post}")
        continue
        
    post_identifier = f"@{author_of_post}/{permlink}"
    
    # Ensure this is an original post authored by your target and not a re-blog/comment
    is_original_post = (author_of_post.lower() == author.lower())
    
    if is_original_post and post_identifier not in voted_history:
        print(f"New original post detected: {post_identifier}. Triggering upvote process...")
        
        try:
            # Broadcast format (Weight is scaled 0 to 10000; 100% = 10000)
            scaled_weight = int(VOTE_WEIGHT * 100)
            
            client.broadcast.vote(
                voter=MY_ACCOUNT,
                author=author_of_post,
                permlink=permlink,
                weight=scaled_weight
            )
            print(f"Successfully upvoted {post_identifier}!")
            voted_history.add(post_identifier)
            updated_history = True
        except Exception as e:
            print(f"Voting failed for {post_identifier}: {e}")
    else:
        if not is_original_post:
            print(f"Skipping: Last item found for {author} is a reblog or comment reply.")
        else:
            print(f"Post {post_identifier} has already been processed in a previous cycle.")

# Save history if we performed updates
if updated_history:
    with open(HISTORY_FILE, "w") as f:
        for item in sorted(voted_history):
            f.write(f"{item}\n")
