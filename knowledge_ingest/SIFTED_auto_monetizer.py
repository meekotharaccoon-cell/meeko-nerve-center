# Auto-adds affiliate links to generated content
import os
import glob
from datetime import datetime

# YOUR AFFILIATE TAGS (edit these)
AMAZON_TAG = "YOUR_AMAZON_TAG_HERE"  # Get from Amazon Associates
SHAREASALE_ID = "YOUR_SHAREASALE_ID"

def add_affiliate_links(content_file):
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add affiliate disclosure at top
    disclosure = f"""
DISCLOSURE: This article contains affiliate links. If you buy through these links, 
I may earn a commission at no extra cost to you. This helps support the content.
"""
    
    # Example: Add Amazon affiliate link for "graphic design" mention
    if "graphic design" in content.lower():
        content += f"\n\n Recommended: [Canva Pro for design](https://www.amazon.com/dp/B08XYZ?tag={AMAZON_TAG})"
    
    if "courses" in content.lower():
        content += f"\n\n Learning: [Online courses platform](https://www.shareasale.com/r.cfm?u={SHAREASALE_ID})"
    
    # Save monetized version
    monetized_file = content_file.replace('.txt', '_monetized.txt')
    with open(monetized_file, 'w', encoding='utf-8') as f:
        f.write(disclosure + "\n" + content)
    
    return monetized_file

def main():
    print(" AUTO-MONETIZER")
    print("="*50)
    
    # Find latest content file
    content_files = glob.glob("content/*.txt")
    if not content_files:
        print("No content files found")
        return
    
    latest = max(content_files, key=os.path.getctime)
    print(f"Monetizing: {os.path.basename(latest)}")
    
    monetized = add_affiliate_links(latest)
    print(f" Monetized: {os.path.basename(monetized)}")
    print(f" Location: {monetized}")
    print("="*50)
    print("REMEMBER: Replace YOUR_AMAZON_TAG_HERE with your actual affiliate tag")
    print("Get it from: https://affiliate-program.amazon.com")

if __name__ == "__main__":
    main()
