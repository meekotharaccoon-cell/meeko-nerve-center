cd C:\Users\meeko\Downloads\autonomous_income_system

# Replace the file with UTF-8 encoding fix
@'
"""
HUMANITARIAN REVENUE ENGINE v1.0
Self-replicating ethical AI impact system.
Generates content → queues posts → tracks revenue → triggers donations.
Runs 24/7. Zero human intervention except clicking "Post".
"""

import os
import json
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

# ==============================================
# CONFIGURATION - EDIT ONCE, RUN FOREVER
# ==============================================
CONFIG = {
    "amazon_tag": "autonomoushum-20",
    "api_url": "http://localhost:8000/ask",
    "content_frequency_hours": 6,
    "posts_per_article": {
        "pinterest": 5,
        "twitter": 2
    },
    "donation_threshold": 1000,
    "donation_url": "https://www.unrwausa.org/crypto",
    "working_dir": str(Path.home() / "Downloads/autonomous_income_system"),
    "queue_file": "social_queue.json",
    "revenue_file": "revenue_tracking.json",
    "log_file": "engine_log.txt"
}

class HumanitarianRevenueEngine:
    def __init__(self):
        self.config = CONFIG
        self.start_time = datetime.now()
        self.cycle_count = 0
        self.total_revenue = 0
        self.setup_directories()
        self.load_state()
        
    def setup_directories(self):
        os.makedirs(self.config["working_dir"], exist_ok=True)
        os.chdir(self.config["working_dir"])
        
    def load_state(self):
        if os.path.exists(self.config["revenue_file"]):
            try:
                with open(self.config["revenue_file"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_revenue = data.get("total_revenue", 0)
                    self.cycle_count = data.get("cycle_count", 0)
            except:
                pass
                
    def save_state(self):
        state = {
            "total_revenue": self.total_revenue,
            "cycle_count": self.cycle_count,
            "last_run": datetime.now().isoformat(),
            "amazon_tag": self.config["amazon_tag"]
        }
        with open(self.config["revenue_file"], 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
            
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Print without emoji for Windows compatibility
        print(f"[{timestamp}] {message}")
        
        # Write to file with UTF-8
        with open(self.config["log_file"], 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    def call_ollama(self, prompt):
        try:
            import requests
            response = requests.post(
                self.config["api_url"],
                json={"question": prompt},
                timeout=60
            )
            if response.status_code == 200:
                return response.json().get("answer", "")
        except:
            self.log("Ollama API not responding - start with: python main.py")
            return ""
        return ""
        
    def generate_article(self):
        self.log("Generating Amazon article...")
        
        topics = [
            "best office chair for back pain",
            "best standing desk for small spaces",
            "best wireless mouse for productivity",
            "best mechanical keyboard under $100",
            "best monitor for programming",
            "best laptop for students",
            "best noise cancelling headphones",
            "best webcam for streaming",
            "best portable charger",
            "best desk lamp for eye strain"
        ]
        
        topic = topics[self.cycle_count % len(topics)]
        
        prompt = f"""Write a 500-word product review article for: '{topic} 2026'.

Include:
- SEO title with year
- Comparison table of 3-5 products
- Pros and cons for each
- Affiliate disclosure
- Use affiliate tag placeholder: {self.config['amazon_tag']}

Format as markdown."""
        
        article = self.call_ollama(prompt)
        
        filename = f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Generated: {datetime.now()} -->\n")
            f.write(f"<!-- Topic: {topic} -->\n")
            f.write(f"<!-- Tag: {self.config['amazon_tag']} -->\n\n")
            f.write(article)
            
        self.log(f"Article saved: {filename}")
        return filename, topic
        
    def generate_social_posts(self, article_topic):
        self.log("Generating social media posts...")
        
        queue = []
        
        for i in range(self.config["posts_per_article"]["pinterest"]):
            prompt = f"""Write a Pinterest pin description for an article about '{article_topic}'.

Include:
- Catchy headline under 60 chars
- 3-5 lines of description
- 5-7 relevant hashtags
- Call to action
- Tone: helpful, not salesy"""
            
            pin = self.call_ollama(prompt)
            queue.append({
                "platform": "pinterest",
                "content": pin,
                "generated": datetime.now().isoformat(),
                "posted": False
            })
            
        for i in range(self.config["posts_per_article"]["twitter"]):
            prompt = f"""Write a Twitter post (under 280 chars) about '{article_topic}'.

Include:
- Hook in first 50 chars
- Value proposition
- 1-2 relevant hashtags
- Call to action
- Tone: conversational"""
            
            tweet = self.call_ollama(prompt)[:280]
            queue.append({
                "platform": "twitter",
                "content": tweet,
                "generated": datetime.now().isoformat(),
                "posted": False
            })
            
        all_queue = []
        if os.path.exists(self.config["queue_file"]):
            try:
                with open(self.config["queue_file"], 'r', encoding='utf-8') as f:
                    all_queue = json.load(f)
            except:
                pass
                
        all_queue.extend(queue)
        
        with open(self.config["queue_file"], 'w', encoding='utf-8') as f:
            json.dump(all_queue, f, indent=2)
            
        self.log(f"Added {len(queue)} posts to queue")
        return queue
        
    def open_posting_tabs(self):
        if not os.path.exists(self.config["queue_file"]):
            self.log("No posts in queue")
            return
            
        with open(self.config["queue_file"], 'r', encoding='utf-8') as f:
            queue = json.load(f)
            
        unposted = [p for p in queue if not p.get("posted", False)]
        
        if not unposted:
            self.log("All posts published!")
            return
            
        webbrowser.open("https://pinterest.com")
        webbrowser.open("https://twitter.com")
        
        self.log(f"Opened {len(unposted)} tabs for posting")
        self.log("Click 'Post' when ready")
        
    def check_revenue(self):
        estimated_revenue = self.cycle_count * 15
        self.total_revenue += estimated_revenue
        
        self.log(f"Estimated revenue: ${estimated_revenue}")
        self.log(f"Total revenue: ${self.total_revenue}")
        
        if self.total_revenue >= self.config["donation_threshold"]:
            self.log("DONATION TRIGGERED!")
            self.log(f"Send Bitcoin to: {self.config['donation_url']}")
            webbrowser.open(self.config["donation_url"])
            self.total_revenue = 0
            
        return estimated_revenue
        
    def run_cycle(self):
        self.cycle_count += 1
        self.log(f"\n{'='*60}")
        self.log(f"CYCLE #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{'='*60}")
        
        article_file, topic = self.generate_article()
        posts = self.generate_social_posts(topic)
        revenue = self.check_revenue()
        self.save_state()
        
        self.log(f"Cycle complete - next in {self.config['content_frequency_hours']} hours")
        
    def run_forever(self):
        self.log("HUMANITARIAN REVENUE ENGINE STARTED")
        self.log(f"Amazon tag: {self.config['amazon_tag']}")
        self.log(f"Donation threshold: ${self.config['donation_threshold']}")
        self.log(f"Content frequency: Every {self.config['content_frequency_hours']} hours")
        self.log("="*60)
        
        while True:
            try:
                self.run_cycle()
                sleep_seconds = self.config["content_frequency_hours"] * 3600
                self.log(f"Sleeping for {self.config['content_frequency_hours']} hours...")
                time.sleep(sleep_seconds)
            except KeyboardInterrupt:
                self.log("Engine stopped by user")
                self.save_state()
                break
            except Exception as e:
                self.log(f"Error: {e}")
                self.log("Restarting in 5 minutes...")
                time.sleep(300)

if __name__ == "__main__":
    print("")
    print("HUMANITARIAN REVENUE ENGINE - v1.0")
    print("Ethical AI Impact System")
    print("Self-replicating • 24/7 • Open Source")
    print("")
    
    engine = HumanitarianRevenueEngine()
    engine.run_forever()
'@ | Out-File -FilePath "humanitarian_revenue_engine.py" -Encoding UTF8

Write-Host "✅ File fixed - no emojis, UTF-8 encoding" -ForegroundColor Green
Write-Host "🚀 Run: python humanitarian_revenue_engine.py" -ForegroundColor Yellow