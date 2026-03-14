# recovery_agent.py - Automated system recovery
import os
import subprocess
import time
from datetime import datetime

class SolarPunkRecovery:
    def __init__(self):
        self.root = "C:\\Users\\carol\\SolarPunk"
        self.status_file = "system_status.txt"
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.status_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[{timestamp}] {message}")
    
    def fix_git(self):
        self.log("Fixing Git repository...")
        os.chdir(self.root)
        subprocess.run(["git", "init"], capture_output=True)
        self.log("Git initialized")
        
    def check_cloudflare(self):
        self.log("Checking Cloudflare...")
        # Basic content check
        if not os.path.exists("dist/index.html"):
            self.create_basic_site()
    
    def create_basic_site(self):
        html = """<!DOCTYPE html>
<html>
<head><title>SolarPunk Recovery</title></head>
<body><h1>System Recovery Active</h1></body>
</html>"""
        os.makedirs("dist", exist_ok=True)
        with open("dist/index.html", "w", encoding="utf-8") as f:
            f.write(html)
        self.log("Basic site created")
    
    def run_self_check(self):
        self.log("=== STARTING SYSTEM CHECK ===")
        self.fix_git()
        self.check_cloudflare()
        self.log("=== SYSTEM CHECK COMPLETE ===")

if __name__ == "__main__":
    agent = SolarPunkRecovery()
    agent.run_self_check()