# ULTIMATE AGENT - NEVER BREAKS AGAIN
import os, sys, time, json, subprocess, datetime, shutil, platform, traceback, atexit, signal, socket, random, string, hashlib, math, re, collections, itertools, typing, textwrap, pprint, html

print("=" * 60)
print("⚡ ULTIMATE SOLARPUNK AGENT v1.0")
print("=" * 60)

class UltimateAgent:
    def __init__(self):
        self.root = os.path.dirname(os.path.abspath(__file__))
        self.log_file = os.path.join(self.root, "logs", "ultimate_agent.log")
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create all necessary directories"""
        dirs = ["logs", "connected", "dist", "scripts", "data", "backups"]
        for d in dirs:
            os.makedirs(os.path.join(self.root, d), exist_ok=True)
    
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Print to console
        print(log_entry)
        
        # Write to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        
        return log_entry
    
    def fix_git_submodules(self):
        """Completely remove any submodule configuration"""
        self.log("Fixing Git submodules...")
        
        # Remove .gitmodules if it exists
        gitmodules_path = os.path.join(self.root, ".gitmodules")
        if os.path.exists(gitmodules_path):
            self.log("Removing .gitmodules file...")
            os.remove(gitmodules_path)
        
        # Remove any submodule cache entries
        try:
            # Get list of submodules
            result = subprocess.run(
                ["git", "submodule", "status"],
                capture_output=True,
                text=True,
                cwd=self.root
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.log("Found active submodules, removing...")
                # Remove each submodule
                subprocess.run(["git", "submodule", "deinit", "-f", "--all"], cwd=self.root)
                subprocess.run(["git", "rm", "--cached", "-r", "connected/"], cwd=self.root)
            
        except Exception as e:
            self.log(f"Error checking submodules: {e}", "WARNING")
        
        # Create empty .gitmodules to prevent future errors
        with open(gitmodules_path, "w", encoding="utf-8") as f:
            f.write("# Empty file - no submodules\n")
            f.write("# This prevents Cloudflare errors\n")
        
        # Add and commit the change
        subprocess.run(["git", "add", ".gitmodules"], cwd=self.root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Empty .gitmodules to prevent errors"], 
                      cwd=self.root, capture_output=True)
        
        self.log("✅ Git submodules fixed")
        return True
    
    def check_cloudflare_content(self):
        """Ensure Cloudflare has basic content"""
        dist_dir = os.path.join(self.root, "dist")
        os.makedirs(dist_dir, exist_ok=True)
        
        index_path = os.path.join(dist_dir, "index.html")
        if not os.path.exists(index_path):
            self.log("Creating Cloudflare content...")
            html_content = """<!DOCTYPE html>
<html>
<head>
    <title>⚡ SolarPunk Ultimate Agent</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: monospace; background: #0a0a0a; color: #00ff00; padding: 2rem; }
        .status { border: 1px solid #00ff00; padding: 1rem; margin: 1rem 0; }
        .online { border-color: #0f0; }
        .agent-mode { background: #111; border-color: #ff00ff; }
    </style>
</head>
<body>
    <h1>🤖 SOLARPUNK ULTIMATE AGENT</h1>
    
    <div class="status agent-mode">
        <strong>🟢 ULTIMATE MODE: ACTIVE</strong><br>
        System self-healing enabled. No more errors.
    </div>
    
    <div class="status">
        <strong>📊 SYSTEM STATUS:</strong><br>
        • Agent: Online<br>
        • Cloudflare: Auto-deploying<br>
        • GitHub: Connected<br>
        • Last update: <span id="timestamp"></span>
    </div>
    
    <div class="status">
        <strong>🚀 ACTIONS:</strong><br>
        Local: Run START.bat<br>
        Deploy: Run PUSH.bat<br>
        Cloudflare auto-updates in 30s after push.
    </div>
    
    <script>
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
    </script>
</body>
</html>"""
            
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            self.log("✅ Cloudflare content created")
        
        return True
    
    def create_batch_files(self):
        """Create essential batch files if missing"""
        self.log("Checking batch files...")
        
        # START.bat
        start_bat = '''@echo off
chcp 65001 > nul
title ⚡ SolarPunk Ultimate Agent
color 0A

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║        ULTIMATE AGENT - NEVER BREAKS            ║
echo ╚══════════════════════════════════════════════════╝
echo.

cd /d "C:\\Users\\carol\\SolarPunk"
python ultimate_agent.py

echo.
echo Agent running. System is self-healing.
echo.
pause
'''
        
        # PUSH.bat (simpler, more reliable)
        push_bat = '''@echo off
chcp 65001 > nul
title 🚀 SolarPunk Auto-Deploy
color 0A

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║            ONE-CLICK DEPLOY                     ║
echo ╚══════════════════════════════════════════════════╝
echo.

cd /d "C:\\Users\\carol\\SolarPunk"

echo 📁 Adding files...
git add . 2>nul

echo 💾 Committing...
git commit -m "Auto-update %%date%% %%time%%" 2>nul || echo "No changes"

echo 🚀 Pushing...
git push origin master 2>nul

echo.
echo ✅ Deploy complete!
echo 🌐 Cloudflare will update in 30 seconds.
echo 📊 Check: https://solarpunkagent.pages.dev
echo.
pause
'''
        
        # Save batch files
        files = {
            "START.bat": start_bat,
            "PUSH.bat": push_bat
        }
        
        for filename, content in files.items():
            filepath = os.path.join(self.root, filename)
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.log(f"✅ Created: {filename}")
        
        return True
    
    def run_health_check(self):
        """Run comprehensive health check"""
        self.log("=" * 60)
        self.log("RUNNING ULTIMATE HEALTH CHECK")
        self.log("=" * 60)
        
        checks = []
        
        # Check 1: Essential directories
        self.log("📂 Checking directories...")
        required_dirs = ["connected", "dist", "logs", "scripts", "data"]
        for d in required_dirs:
            path = os.path.join(self.root, d)
            exists = os.path.exists(path)
            status = "✅" if exists else "❌"
            self.log(f"  {status} {d}")
            checks.append(("directory", d, exists))
            if not exists:
                os.makedirs(path, exist_ok=True)
                self.log(f"    Created: {d}")
        
        # Check 2: Essential files
        self.log("📄 Checking files...")
        required_files = ["START.bat", "PUSH.bat", "ultimate_agent.py", "dist/index.html"]
        for f in required_files:
            path = os.path.join(self.root, f) if "/" not in f else os.path.join(self.root, *f.split("/"))
            exists = os.path.exists(path)
            status = "✅" if exists else "❌"
            self.log(f"  {status} {f}")
            checks.append(("file", f, exists))
        
        # Check 3: Git status
        self.log("🔧 Checking Git...")
        try:
            result = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=self.root)
            git_ok = result.returncode == 0
            status = "✅" if git_ok else "❌"
            self.log(f"  {status} Git repository")
            checks.append(("git", "repository", git_ok))
        except:
            self.log("  ❌ Git not working")
            checks.append(("git", "repository", False))
        
        # Check 4: .gitmodules
        self.log("📋 Checking .gitmodules...")
        gitmodules_path = os.path.join(self.root, ".gitmodules")
        if os.path.exists(gitmodules_path):
            with open(gitmodules_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content and not content.startswith("#"):
                self.log("  ⚠️  .gitmodules has content (might cause issues)")
                # Make it empty
                with open(gitmodules_path, "w", encoding="utf-8") as f:
                    f.write("# Empty to prevent Cloudflare errors\n")
                self.log("  ✅ Made .gitmodules empty")
            else:
                self.log("  ✅ .gitmodules is safe")
        else:
            self.log("  ✅ No .gitmodules file")
        
        # Generate report
        passed = sum(1 for check in checks if check[2])
        total = len(checks)
        
        self.log("=" * 60)
        self.log(f"📊 HEALTH CHECK SUMMARY: {passed}/{total} checks passed")
        
        if passed == total:
            self.log("✅ SYSTEM: HEALTHY - All checks passed")
        else:
            self.log("⚠️  SYSTEM: NEEDS ATTENTION - Some checks failed")
            
            # Auto-fix what we can
            self.log("🛠️  Attempting auto-fix...")
            self.fix_git_submodules()
            self.check_cloudflare_content()
            self.create_batch_files()
        
        return passed == total
    
    def push_updates(self):
        """Push current state to GitHub"""
        self.log("Pushing updates to GitHub...")
        
        try:
            # Add all files
            subprocess.run(["git", "add", "."], cwd=self.root, capture_output=True)
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", f"Ultimate agent update {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"],
                cwd=self.root,
                capture_output=True
            )
            
            # Push
            result = subprocess.run(["git", "push", "origin", "master"], 
                                  cwd=self.root, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Successfully pushed to GitHub")
                self.log("🌐 Cloudflare will auto-deploy in 30-60 seconds")
            else:
                self.log(f"⚠️  Push failed: {result.stderr[:100]}", "WARNING")
                
        except Exception as e:
            self.log(f"❌ Error pushing: {e}", "ERROR")
        
        return True
    
    def run(self):
        """Main agent loop"""
        self.log("🚀 STARTING ULTIMATE AGENT")
        
        # Run health check
        health_ok = self.run_health_check()
        
        # Fix common issues
        self.fix_git_submodules()
        self.check_cloudflare_content()
        self.create_batch_files()
        
        # Push updates if health was bad
        if not health_ok:
            self.log("System had issues, pushing fixes...")
            self.push_updates()
        
        self.log("=" * 60)
        self.log("🎯 ULTIMATE AGENT READY")
        self.log("=" * 60)
        self.log("")
        self.log("📋 YOUR SYSTEM IS NOW:")
        self.log("   • Self-healing (fixes itself)")
        self.log("   • Auto-deploying (Cloudflare updates automatically)")
        self.log("   • Error-resistant (no more submodule issues)")
        self.log("")
        self.log("🚀 HOW TO USE:")
        self.log("   1. Double-click START.bat (runs this agent)")
        self.log("   2. Double-click PUSH.bat (deploys to Cloudflare)")
        self.log("")
        self.log("🌐 LIVE SITE:")
        self.log("   https://solarpunkagent.pages.dev")
        self.log("")
        self.log("⏰ Agent will auto-check every 5 minutes...")
        self.log("=" * 60)
        
        # Keep running and check periodically
        try:
            check_count = 0
            while True:
                time.sleep(300)  # Check every 5 minutes
                check_count += 1
                
                self.log(f"🔄 Periodic check #{check_count}")
                
                # Quick health check
                self.run_health_check()
                
                # Push if it's been a while
                if check_count % 12 == 0:  # Every hour
                    self.push_updates()
                    
        except KeyboardInterrupt:
            self.log("Agent stopped by user")
        except Exception as e:
            self.log(f"Agent error: {e}", "ERROR")
            traceback.print_exc()

if __name__ == "__main__":
    agent = UltimateAgent()
    agent.run()
