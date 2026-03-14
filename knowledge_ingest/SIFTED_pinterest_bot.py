import webbrowser
import time
import json
from datetime import datetime

YOUR_AMAZON_TAG = "autonomoushum-20"

# Load your links
with open("affiliate_links/all_links.json", "r") as f:
    links = json.load(f)

# Create Pinterest pins (opens browser - you just click "Save")
print(" PINTEREST AUTOMATION - OPENING 3 PINS...")
print("1. Login to Pinterest")
print("2. Click 'Save' on each tab")
print("")

for category, items in links.items():
    for item in items[:1]:  # One per category
        url = f"https://www.pinterest.com/pin/create/button/?url={item['url']}&description={category}%20-%20{item['product']}%20%7C%20Supports%20Humanitarian%20Aid"
        webbrowser.open_new_tab(url)
        print(f" Pin: {item['product']}")
        time.sleep(2)

print("")
print(" 3 Pins opened - Click 'Save' on each tab")
print(" Do this daily at 6 AM to flood Pinterest")
