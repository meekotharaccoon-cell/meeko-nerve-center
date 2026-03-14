"""
📁 UPDATE ALL 30 REPOS' AI-FIX.YML
Adds SolarPunk node to your existing GitHub Actions
"""

import requests
import base64
import json

# YOUR INFO - FILL THIS IN
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN_HERE"  # Get from: https://github.com/settings/tokens
USERNAME = "MeekoThaRaccoon"
REPOS = [
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

# The SolarPunk step to add to ai-fix.yml
SOLARPUNK_STEP = {
    "name": "🌐 Run SolarPunk Node",
    "env": {
        "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"
    },
    "run": "python solarpunk_node.py"
}

def update_repo_workflow(repo_name):
    """Add SolarPunk step to a repo's ai-fix.yml"""
    print(f"\n🔄 Updating {repo_name}...")
    
    # GitHub API headers
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Get current ai-fix.yml
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/contents/.github/workflows/ai-fix.yml"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"   ❌ Can't find ai-fix.yml in {repo_name}")
        return False
    
    file_data = response.json()
    content = base64.b64decode(file_data['content']).decode('utf-8')
    sha = file_data['sha']
    
    # 2. Parse YAML (simple string method - careful!)
    lines = content.split('\n')
    new_lines = []
    in_steps = False
    steps_added = False
    
    for line in lines:
        new_lines.append(line)
        
        # Find where steps: section ends
        if line.strip().startswith('steps:'):
            in_steps = True
            
        # Find the last step (indented less than previous step)
        if in_steps and not steps_added:
            if line.strip() and not line.strip().startswith('-') and not line.strip().startswith('#'):
                # End of steps found, insert before this line
                solar_step = f'''  - name: "🌐 Run SolarPunk Node"
    env:
      GITHUB_TOKEN: "${{{{ secrets.GITHUB_TOKEN }}}}"
    run: |
      curl -o solarpunk_node.py https://raw.githubusercontent.com/{USERNAME}/SolarPunk-Autonomous/main/solarpunk_node.py
      python solarpunk_node.py'''
                
                new_lines.insert(len(new_lines)-1, solar_step)
                steps_added = True
                in_steps = False
    
    # If we didn't find where to insert, add at end
    if not steps_added:
        solar_step = f'''
  - name: "🌐 Run SolarPunk Node"
    env:
      GITHUB_TOKEN: "${{{{ secrets.GITHUB_TOKEN }}}}"
    run: |
      curl -o solarpunk_node.py https://raw.githubusercontent.com/{USERNAME}/SolarPunk-Autonomous/main/solarpunk_node.py
      python solarpunk_node.py'''
        new_lines.append(solar_step)
    
    # 3. Update file
    new_content = '\n'.join(new_lines)
    update_data = {
        "message": f"Add SolarPunk node to {repo_name}",
        "content": base64.b64encode(new_content.encode()).decode(),
        "sha": sha
    }
    
    update_response = requests.put(url, headers=headers, json=update_data)
    
    if update_response.status_code == 200:
        print(f"   ✅ Updated {repo_name}")
        return True
    else:
        print(f"   ❌ Failed to update {repo_name}: {update_response.text}")
        return False

def main():
    print("🚀 SOLARPUNK NETWORK DEPLOYMENT")
    print(f"Updating {len(REPOS)} repositories...")
    
    # First, upload solarpunk_node.py to your main repo
    print("\n1. Uploading solarpunk_node.py to SolarPunk-Autonomous...")
    
    # You'll do this manually:
    print("""
    MANUAL STEP FOR YOU:
    1. Go to: https://github.com/MeekoThaRaccoon/SolarPunk-Autonomous
    2. Click "Add file" → "Upload files"
    3. Drag the solarpunk_node.py from your Desktop
    4. Click "Commit changes"
    """)
    
    input("Press Enter after you've uploaded solarpunk_node.py to the main repo...")
    
    # Now update all repos
    print("\n2. Updating all 30 repos...")
    success_count = 0
    
    for repo in REPOS:
        if update_repo_workflow(repo):
            success_count += 1
    
    print(f"\n🎉 DEPLOYMENT COMPLETE")
    print(f"Successfully updated: {success_count}/{len(REPOS)} repos")
    print(f"\n🌐 NETWORK STATUS:")
    print(f"Total nodes: {len(REPOS)}")
    print(f"Virtual capital: ${len(REPOS) * 100} ($100 per node)")
    print(f"3-year target: ${len(REPOS) * 23541}")
    
    print(f"\n📊 View network at: https://gist.github.com/MeekoThaRaccoon/306b631bee3be5683c15993ae00b1714")
    print("GitHub Actions will run every 5 minutes automatically!")

if __name__ == "__main__":
    main()