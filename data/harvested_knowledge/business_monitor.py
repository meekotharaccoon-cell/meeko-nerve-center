#!/usr/bin/env python3
"""
GAZA ROSE - BUSINESS MONITOR
Tracks Then & Now Flora across all platforms
Runs 24/7, alerts on sales, suggests improvements
"""

import os
import time
import json
import webbrowser
from datetime import datetime
from pathlib import Path

class BusinessMonitor:
    def __init__(self):
        self.platforms = {
            "pond5": {
                "url": "https://www.pond5.com/artist/meeko",
                "status": "pending",
                "last_check": None
            },
            "spreadshirt": {
                "url": "https://shop.spreadshirt.com/meeko",
                "status": "active",
                "last_check": None
            },
            "redbubble": {
                "url": "https://www.redbubble.com/people/meeko/shop",
                "status": "active",
                "last_check": None
            },
            "amazon": {
                "tag": "autonomoushum-20",
                "status": "active",
                "last_check": None
            }
        }
        self.art_count = 0
        self.revenue = 0
        self.log_file = "business_log.json"
        
    def scan_art_folder(self):
        """Count art pieces in your gallery"""
        art_paths = [
            r"C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\art",
            r"C:\Users\meeko\Desktop\GAZA_ROSE_ULTIMATE\art"
        ]
        total = 0
        for path in art_paths:
            if os.path.exists(path):
                total += len([f for f in os.listdir(path) if f.endswith(('.png', '.jpg', '.jpeg'))])
        self.art_count = total
        return total
    
    def check_platforms(self):
        """Open each platform in browser for manual check"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 CHECKING PLATFORMS")
        for name, config in self.platforms.items():
            if "url" in config:
                webbrowser.open_new_tab(config["url"])
                print(f"  📍 Opened: {name}")
                time.sleep(2)
        return True
    
    def suggest_next_design(self):
        """Suggest what to design next based on trends"""
        suggestions = [
            "Vintage botanical lavender",
            "Art deco sunflower",
            "Minimalist olive branch",
            "Watercolor poppy",
            "Geometric rose"
        ]
        import random
        next_design = random.choice(suggestions)
        print(f"  💡 Next design idea: {next_design}")
        return next_design
    
    def run_forever(self):
        """Main business loop"""
        print("\n" + "="*60)
        print("  🎨 GAZA ROSE - BUSINESS MONITOR")
        print("="*60)
        
        cycle = 0
        while True:
            cycle += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 BUSINESS CYCLE #{cycle}")
            
            # Count art
            art = self.scan_art_folder()
            print(f"  🖼️  Art pieces: {art}")
            
            # Check platforms (every 6 cycles)
            if cycle % 6 == 0:
                self.check_platforms()
            
            # Suggest next design (every 12 cycles)
            if cycle % 12 == 0:
                self.suggest_next_design()
            
            # Log status
            with open(self.log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()},BUSINESS,art={art}\n")
            
            time.sleep(600)  # 10 minutes

if __name__ == "__main__":
    monitor = BusinessMonitor()
    monitor.run_forever()
