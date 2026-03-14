import requests, json, time, os
from datetime import datetime

class GitHubAutodeployer:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.token = config["github"]["token"]
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        self.repos = [
            "SolarPunk-Autonomous", "SolarPunk-Network-Registry", "SolarPunk_Agent",
            "SolarPunk_Alpha_Bot", "Murmuration", "SolarPunk-Registry",
            "SolarPunk-Node-002", "SolarPunk-Autonomous-Live", "SolarPunk-Proof",
            "glma-ai-services", "SolarPunk", "Business-autopilot",
            "SolarPunk-Chat-History", "SolarPunk-Ethical-Validator",
            "SolarPunk-Exponential-Growth", "SolarPunk-Resource-Calculator",
            "SolarPunk-Economic-Transition", "SolarPunk-AI-Treaty",
            "SolarPunk-Legal-Framework", "SolarPunk-Community-Network",
            "SolarPunk-Energy-Distribution", "SolarPunk-Manufacturing",
            "SolarPunk-Truth-Preservation", "SolarPunk-Anti-Corruption",
            "SolarPunk-Land-Reclamation", "SolarPunk-Crisis-Response",
            "SolarPunk-UBI-Engine", "solarpunk-revenue", "SolarPunk-Memvid",
            "SolarPunk-Nexus"
        ]
        
        print("🚀 GitHub Autodeployer Started")
    
    def update_repo(self, repo_name):
        try:
            workflow = """name: Autonomous SolarPunk Node
on: [schedule, workflow_dispatch]
jobs:
  autonomous:
    runs-on: ubuntu-latest
    steps:
      - run: echo "SolarPunk Autonomous Node Running"
"""
            
            import base64
            encoded = base64.b64encode(workflow.encode()).decode()
            
            url = f"https://api.github.com/repos/MeekoThaRaccoon/{repo_name}/contents/.github/workflows/autonomous.yml"
            response = requests.put(url, headers=self.headers, json={
                "message": "🤖 Autonomous deployment",
                "content": encoded,
                "branch": "main"
            })
            
            if response.status_code in [200, 201]:
                print(f"  ✅ {repo_name}")
                return True
            else:
                print(f"  ❌ {repo_name}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ {repo_name} failed: {e}")
            return False
    
    def deploy_all(self):
        print(f"Deploying to {len(self.repos)} repositories...")
        success = 0
        for repo in self.repos:
            if self.update_repo(repo):
                success += 1
        print(f"✅ Deployed to {success}/{len(self.repos)} repos")
        return success
    
    def run(self):
        self.deploy_all()
        while True:
            time.sleep(86400)  # 24 hours

if __name__ == "__main__":
    deployer = GitHubAutodeployer()
    deployer.run()
