"""
DISTRIBUTION ENGINE v1.0
Opens Pinterest, Twitter, and RedBubble tabs with pre-filled content
One click = one post. Zero copy/paste.
"""

import os
import json
import webbrowser
from datetime import datetime
from pathlib import Path

class DistributionEngine:
    def __init__(self):
        self.log_file = Path("distribution_log.txt")
        self.queue_file = Path("social_queue.json")
        self.load_queue()
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[{timestamp}] {message}")
        
    def load_queue(self):
        if self.queue_file.exists():
            with open(self.queue_file, "r", encoding="utf-8") as f:
                self.queue = json.load(f)
        else:
            self.queue = []
            
    def save_queue(self):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(self.queue, f, indent=2)
            
    def generate_pinterest_pin(self, article_title):
        """Create Pinterest pin URL with pre-filled content"""
        base_url = "https://www.pinterest.com/pin/create/button/"
        params = {
            "url": "https://amazon.com",
            "media": "https://placehold.co/1000x1500/2563eb/white?text=Gaza+Rose",
            "description": f"{article_title}\n\nEvery purchase supports humanitarian aid via UNRWA USA.\n#Gaza #Humanitarian #Art #Palestine"
        }
        url = f"{base_url}?url={params['url']}&media={params['media']}&description={params['description']}"
        return url
        
    def generate_tweet_url(self, article_title, affiliate_link):
        """Create Twitter intent URL with pre-filled content"""
        base_url = "https://twitter.com/intent/tweet"
        text = f"{article_title}\n\nEvery purchase sends aid to Gaza via UNRWA USA.\n\n{affiliate_link}"
        return f"{base_url}?text={text}"
        
    def open_pinterest_tabs(self, count=5):
        """Open multiple Pinterest pin tabs"""
        self.log(f"📌 Opening {count} Pinterest tabs...")
        for i in range(count):
            url = self.generate_pinterest_pin(f"Gaza Rose Collection #{i+1}")
            webbrowser.open_new_tab(url)
        self.log(f"✅ {count} Pinterest tabs opened")
        
    def open_twitter_tabs(self, count=3):
        """Open multiple Twitter intent tabs"""
        self.log(f"🐦 Opening {count} Twitter tabs...")
        affiliate_link = f"https://amazon.com/dp/B0XXX?tag=autonomoushum-20"
        for i in range(count):
            url = self.generate_tweet_url(f"Support Gaza through art #{i+1}", affiliate_link)
            webbrowser.open_new_tab(url)
        self.log(f"✅ {count} Twitter tabs opened")
        
    def open_redbubble_tab(self):
        """Open RedBubble upload page"""
        self.log(f"🎨 Opening RedBubble upload...")
        webbrowser.open_new_tab("https://www.redbubble.com/portfolio/images/new")
        self.log(f"✅ RedBubble upload tab opened")
        
    def run_daily_distribution(self):
        """Run all distribution channels"""
        self.log("="*60)
        self.log("🚀 DAILY DISTRIBUTION ENGINE STARTED")
        self.log("="*60)
        
        self.open_pinterest_tabs(5)
        self.open_twitter_tabs(3)
        self.open_redbubble_tab()
        
        self.log("="*60)
        self.log("✅ DAILY DISTRIBUTION COMPLETE")
        self.log("📌 Click 'Save' on Pinterest tabs")
        self.log("🐦 Click 'Tweet' on Twitter tabs")
        self.log("🎨 Upload your Gaza Rose designs to RedBubble")
        self.log("="*60)

if __name__ == "__main__":
    engine = DistributionEngine()
    engine.run_daily_distribution()
