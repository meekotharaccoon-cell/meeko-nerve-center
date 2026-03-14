import webbrowser
import json
from datetime import datetime

YOUR_AMAZON_TAG = "autonomoushum-20"

# Load your links
with open("affiliate_links/all_links.json", "r") as f:
    links = json.load(f)

# Subreddits that allow affiliate links
subreddits = [
    "r/deals",
    "r/amazonddeals", 
    "r/LaptopDeals",
    "r/HomeOfficeDeals",
    "r/humanitarian"
]

print(" REDDIT AUTOMATION - OPENING 5 SUBREDDITS...")
print("1. Login to Reddit")
print("2. Post your affiliate links")
print("")

for sub in subreddits[:3]:  # First 3
    url = f"https://www.reddit.com/{sub}/submit"
    webbrowser.open_new_tab(url)
    print(f" Opening: {sub}")
    time.sleep(2)

print("")
print(" Copy/paste this post template:")
print("-"*50)
print(f"Title: Great deals that help humanitarian aid")
print(f"")
print(f"Every purchase through these links sends commissions to Gaza/Sudan/Congo relief.")
print(f"")
for cat, items in links.items():
    print(f"{cat.upper()}:")
    for item in items[:2]:
        print(f" {item['product']} - {item['url']}")
print(f"")
print(f"100% of commissions go to humanitarian aid. Tag: {YOUR_AMAZON_TAG}")
print("-"*50)
