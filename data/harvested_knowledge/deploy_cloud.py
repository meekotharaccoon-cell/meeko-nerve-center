# SOLARPUNK CLOUD DEPLOYMENT - SIMPLE VERSION
import os
import json

def main():
    print("🚀 CREATING CLOUD DEPLOYMENT PACKAGE")
    
    # Create simple Node.js server
    server_js = """const http = require('http');
let balance = 100;
const growth = 0.005/1440;

setInterval(() => {
    balance *= (1 + growth);
    console.log('SolarPunk: $' + balance.toFixed(2));
}, 60000);

http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify({
        balance: balance.toFixed(2),
        humanitarian: (balance * 0.5).toFixed(2),
        ubi: (balance * 0.5).toFixed(2)
    }));
}).listen(3000);
"""
    
    package_json = json.dumps({
        "name": "solarpunk-cloud",
        "scripts": {"start": "node server.js"}
    }, indent=2)
    
    # Create directory
    os.makedirs("cloud_deployment", exist_ok=True)
    
    # Save files
    with open("cloud_deployment/server.js", 'w', encoding='utf-8') as f:
        f.write(server_js)
    
    with open("cloud_deployment/package.json", 'w', encoding='utf-8') as f:
        f.write(package_json)
    
    # Create deployment guide
    guide = """# DEPLOY TO CLOUD SERVICES:

## 1. Vercel (easiest):
   - Go to vercel.com
   - Drag "cloud_deployment" folder
   - Instantly deployed!

## 2. Netlify:
   - Go to netlify.com/drop
   - Drag folder
   - Done!

## 3. Heroku:
   - heroku create
   - git push heroku main

## FREE SERVICES:
- Vercel: Free forever
- Netlify: Free forever  
- Render: Free tier
- Railway: Free credits
- Fly.io: Free allowance
- Replit: Free hosting
- Glitch: Free hosting
- GitHub Pages: Free
- GitPod: Free hours
"""
    
    with open("cloud_deployment/DEPLOY.txt", 'w') as f:
        f.write(guide)
    
    print("✅ Created cloud_deployment/ folder")
    print("📁 Contains: server.js, package.json, DEPLOY.txt")
    print("\nJust drag folder to Netlify or Vercel!")

if __name__ == "__main__":
    main()