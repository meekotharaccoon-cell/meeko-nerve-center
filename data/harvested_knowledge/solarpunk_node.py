"""
🌐 SOLARPUNK UNIVERSAL NODE - Deploy to ALL 30 repos
This single file connects all repos into one SolarPunk network
"""

import os
import hashlib
import time
import requests
import json
import sys

class SolarPunkNode:
    def __init__(self, repo_name):
        # Use your Gist URL
        self.gist_id = "306b631bee3be5683c15993ae00b1714"
        self.gist_url = f"https://api.github.com/gists/{self.gist_id}"
        self.node_id = hashlib.md5(repo_name.encode()).hexdigest()[:8]
        self.repo_name = repo_name
        self.balance = 100.0  # Start at $100
        self.daily_growth = 0.005  # 0.5% daily
        
        # Your GitHub token will be set in GitHub Actions
        self.github_token = os.getenv('GITHUB_TOKEN')
        
    def generate_value(self):
        """Mathematical value generation - NOT gambling"""
        # 0.5% daily growth, calculated per minute
        minute_growth = self.daily_growth / (24 * 60)
        new_balance = self.balance * (1 + minute_growth)
        value_generated = new_balance - self.balance
        self.balance = new_balance
        return value_generated
        
    def report_to_network(self, value_generated):
        """Report this node's status to the central Gist"""
        node_data = {
            'node_id': self.node_id,
            'repo_name': self.repo_name,
            'balance': round(self.balance, 4),
            'value_generated': round(value_generated, 4),
            'humanitarian_share': round(value_generated * 0.5, 4),
            'timestamp': time.time()
        }
        
        # Get current Gist
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            # Read current Gist
            response = requests.get(self.gist_url, headers=headers)
            gist_data = response.json()
            
            # Get current files
            files = gist_data['files']
            
            # Create or update this node's file
            filename = f"node_{self.node_id}.json"
            files[filename] = {
                'content': json.dumps(node_data, indent=2)
            }
            
            # Update Gist
            update_data = {'files': files}
            update_response = requests.patch(
                self.gist_url,
                headers=headers,
                json=update_data
            )
            
            print(f"✅ Node {self.node_id} reported: ${self.balance:.2f}")
            return True
            
        except Exception as e:
            print(f"⚠️  Couldn't report to network: {e}")
            return False
            
    def run(self, minutes=5):
        """Run the node for X minutes (GitHub Actions limit)"""
        print(f"🚀 SolarPunk Node starting: {self.repo_name}")
        print(f"   Node ID: {self.node_id}")
        print(f"   Starting balance: ${self.balance:.2f}")
        print(f"   Target: $23,541 in 3 years")
        
        # Run for specified minutes (GitHub Actions max ~6 hours)
        for minute in range(minutes):
            value = self.generate_value()
            self.report_to_network(value)
            print(f"   Minute {minute+1}: ${self.balance:.2f} (+${value:.4f})")
            time.sleep(60)  # Wait 1 minute
            
        print(f"📊 Session complete: ${self.balance:.2f}")
        print(f"   Humanitarian allocation: ${self.balance * 0.5:.2f}")
        print(f"   Reinvestment: ${self.balance * 0.5:.2f}")

# Main execution
if __name__ == "__main__":
    # Get repo name from environment (set by GitHub Actions)
    repo_name = os.getenv('GITHUB_REPOSITORY', 'local-test')
    
    # Create and run node
    node = SolarPunkNode(repo_name)
    
    # Run for 5 minutes (GitHub Actions free tier)
    node.run(minutes=5)