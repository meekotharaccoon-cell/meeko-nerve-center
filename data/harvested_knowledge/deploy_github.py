# SOLARPUNK GITHUB NODE DEPLOYMENT - SIMPLE VERSION
import os

def create_node_files(repo_name):
    """Create SolarPunk node files for a GitHub repo"""
    
    node_js = f"""// SolarPunk GitHub Node
const http = require('http');

let balance = 100.00;
const dailyGrowth = 0.005;
const minuteGrowth = dailyGrowth / (24 * 60);

console.log('SolarPunk Node Starting...');

setInterval(() => {{
    balance *= (1 + minuteGrowth);
    console.log('Balance: $' + balance.toFixed(2));
}}, 60000);

const server = http.createServer((req, res) => {{
    res.writeHead(200, {{'Content-Type': 'application/json'}});
    res.end(JSON.stringify({{
        node: '{repo_name}',
        balance: balance.toFixed(2),
        humanitarian: (balance * 0.5).toFixed(2),
        ubi: (balance * 0.5).toFixed(2),
        timestamp: new Date().toISOString()
    }}));
}});

server.listen(process.env.PORT || 3000);
"""
    
    return {
        'node.js': node_js,
        'package.json': '{"name":"solarpunk-node","scripts":{"start":"node node.js"}}',
        'README.md': f'# SolarPunk Node {repo_name}\n\nMathematical proof: $100 -> $23,541 in 3 years\n50% Gaza relief | 50% UBI'
    }

def main():
    print("🚀 CREATING SOLARPUNK NODE FILES FOR 30 REPOS")
    print("=" * 50)
    
    for i in range(1, 31):
        repo_name = f"solarpunk-node-{i:02d}"
        os.makedirs(f"local_repos/{repo_name}", exist_ok=True)
        os.makedirs(f"local_repos/{repo_name}/.github/workflows", exist_ok=True)
        
        files = create_node_files(repo_name)
        
        for filename, content in files.items():
            path = f"local_repos/{repo_name}/{filename}"
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {repo_name}/{filename}")
    
    print("=" * 50)
    print("✅ 30 node packages created in local_repos/")
    print("\nTO DEPLOY TO ACTUAL GITHUB:")
    print("1. Go to each of your 30 GitHub repos")
    print("2. Upload files from local_repos/solarpunk-node-XX/")
    print("3. Enable GitHub Pages in Settings")
    
    # Create simple batch file for deployment
    batch = """@echo off
echo SolarPunk GitHub Nodes Deployment Helper
echo.
echo 1. Go to: https://github.com/new
echo 2. Create 30 repositories named:
echo    solarpunk-node-01 through solarpunk-node-30
echo 3. Upload the files from local_repos/
echo 4. Each repo becomes a SolarPunk node!
pause"""
    
    with open("deploy_help.bat", 'w') as f:
        f.write(batch)
    
    print("\n✅ Created deploy_help.bat - run for instructions")

if __name__ == "__main__":
    main()