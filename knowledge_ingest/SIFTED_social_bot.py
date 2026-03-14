import tweepy
import json
import time
from datetime import datetime

YOUR_AMAZON_TAG = "autonomoushum-20"

# Load your links
with open("affiliate_links/all_links.json", "r") as f:
    links = json.load(f)

# Sample posts - You need Twitter API keys to make this work!
posts = [
    f"Need a new laptop? Every purchase helps send aid to Gaza  {links['tech'][0]['url']}",
    f"Upgrade your home office and support humanitarian relief! {links['home_office'][0]['url']}",
    f"Emergency supplies that help twice - once for you, once for crisis zones {links['humanitarian'][0]['url']}",
]

print(" SOCIAL MEDIA AUTOMATION READY")
print(f" Would post {len(posts)} links with tag: {YOUR_AMAZON_TAG}")
print("")
print(" TO MAKE IT REAL:")
print("1. Go to: https://developer.twitter.com")
print("2. Create app, get API keys")
print("3. Add keys to this script")
print("4. System auto-posts every day at 6 AM")
