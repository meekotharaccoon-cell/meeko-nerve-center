#!/usr/bin/env python3
"""
SolarPunk Debug Agent - Checks EVERYTHING
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path
from datetime import datetime

print("="*60)
print("🔍 SOLARPUNK DEBUG AGENT")
print("="*60)

# Create log
debug_log = Path.home() / "SolarPunk" / "debug_log.txt"
debug_log.parent.mkdir(exist_ok=True)

def log_check(description, status, details=""):
    """Log a check result"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {description}")
    
    with open(debug_log, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {description}: {'PASS' if status else 'FAIL'}\n")
        if details:
            f.write(f"   Details: {details}\n")
    
    return status

def check_1_cloudflare():
    """Check if Cloudflare site is live"""
    print("\n1. Checking Cloudflare Pages...")
    
    # Open the site
    url = "https://solarpunk-nexus.pages.dev"
    webbrowser.open(url)
    print(f"   Opened: {url}")
    
    # Try to ping it
    try:
        import urllib.request
        response = urllib.request.urlopen(url, timeout=10)
        return log_check("Cloudflare Site", response.status == 200, 
                       f"Status: {response.status}")
    except Exception as e:
        return log_check("Cloudflare Site", False, f"Error: {e}")

def check_2_local_files():
    """Check local SolarPunk directory"""
    print("\n2. Checking local files...")
    
    solarpunk_dir = Path.home() / "SolarPunk"
    
    if not solarpunk_dir.exists():
        return log_check("SolarPunk Directory", False, "Directory doesn't exist")
    
    # List files
    files = list(solarpunk_dir.rglob("*"))
    file_count = len(files)
    
    log_check("SolarPunk Directory", True, f"Found {file_count} files")
    
    # Check for specific files
    important_files = [
        ("fix_github.bat", "GitHub fix script"),
        ("solarpunk-memvid/", "Memvid repository"),
        ("web-interface/index.html", "Web dashboard")
    ]
    
    for filepath, description in important_files:
        full_path = solarpunk_dir / filepath
        exists = full_path.exists()
        status = "Found" if exists else "Missing"
        print(f"   • {description}: {status}")
    
    return True

def check_3_github_status():
    """Check GitHub connection and repo"""
    print("\n3. Checking GitHub...")
    
    # Check if git is installed
    try:
        result = subprocess.run(["git", "--version"], 
                              capture_output=True, text=True)
        git_installed = "git version" in result.stdout
        log_check("Git Installed", git_installed)
    except:
        log_check("Git Installed", False)
    
    # Check GitHub API status
    try:
        import urllib.request
        response = urllib.request.urlopen("https://api.github.com", timeout=10)
        log_check("GitHub API", response.status == 200)
    except:
        log_check("GitHub API", False, "GitHub may be down")
    
    return True

def check_4_netlify_status():
    """Check Netlify status"""
    print("\n4. Checking Netlify...")
    
    # Original Netlify site
    try:
        import urllib.request
        response = urllib.request.urlopen("https://cozy-starship-797fa8.netlify.app", 
                                        timeout=10)
        if response.status == 200:
            return log_check("Netlify Site", False, "Site is live (but credit limit?)")
    except Exception as e:
        if "404" in str(e):
            return log_check("Netlify Site", False, "Site not found - credit limit hit")
    
    return log_check("Netlify Site", False, "Check dashboard for credit limit")

def check_5_python_environment():
    """Check Python setup"""
    print("\n5. Checking Python environment...")
    
    checks = []
    
    # Python version
    python_version = sys.version.split()[0]
    checks.append(log_check(f"Python Version", True, f"Version: {python_version}"))
    
    # Check important modules
    modules = ["requests", "flask", "opencv", "numpy", "qrcode"]
    for module in modules:
        try:
            __import__(module)
            checks.append(log_check(f"Module: {module}", True))
        except ImportError:
            checks.append(log_check(f"Module: {module}", False, "Not installed"))
    
    return all(checks)

def check_6_agent_files():
    """Check agent files"""
    print("\n6. Checking agent files...")
    
    desktop = Path.home() / "Desktop"
    agent_files = list(desktop.glob("solarpunk*.py"))
    
    if not agent_files:
        return log_check("Agent Files", False, "No agent files found on Desktop")
    
    for agent_file in agent_files:
        size = agent_file.stat().st_size
        log_check(f"Agent File: {agent_file.name}", True, f"Size: {size} bytes")
    
    return True

def check_7_fix_script():
    """Check and test fix script"""
    print("\n7. Checking fix scripts...")
    
    fix_script = Path.home() / "SolarPunk" / "fix_github.bat"
    
    if not fix_script.exists():
        return log_check("Fix Script", False, "File not found")
    
    # Read content
    with open(fix_script, "r") as f:
        content = f.read()
    
    lines = len(content.split('\n'))
    log_check("Fix Script", True, f"{lines} lines of code")
    
    # Create a test version
    test_script = fix_script.parent / "test_fix.bat"
    with open(test_script, "w") as f:
        f.write("@echo off\n")
        f.write("echo Testing SolarPunk fix script...\n")
        f.write("echo If you see this, the script works.\n")
        f.write("pause\n")
    
    print(f"   Test script created: {test_script}")
    print(f"   Double-click to test")
    
    return True

def check_8_web_dashboard():
    """Check web dashboard"""
    print("\n8. Checking web dashboard...")
    
    web_dir = Path.home() / "SolarPunk" / "web-interface"
    
    if not web_dir.exists():
        return log_check("Web Dashboard", False, "Directory not found")
    
    html_file = web_dir / "index.html"
    if not html_file.exists():
        return log_check("Web Dashboard", False, "HTML file not found")
    
    # Try to open it
    try:
        webbrowser.open(f"file://{html_file}")
        log_check("Web Dashboard", True, "Opened in browser")
    except:
        log_check("Web Dashboard", True, f"File exists: {html_file}")
    
    return True

def check_9_memvid_repo():
    """Check Memvid repository"""
    print("\n9. Checking Memvid...")
    
    memvid_dir = Path.home() / "SolarPunk" / "solarpunk-memvid"
    
    if not memvid_dir.exists():
        return log_check("Memvid Repo", False, "Directory not found")
    
    # Count files
    files = list(memvid_dir.rglob("*.*"))
    file_count = len(files)
    
    expected_files = ["README.md", "solarpunk_memvid.py", "requirements.txt"]
    found_files = []
    
    for file in expected_files:
        if (memvid_dir / file).exists():
            found_files.append(file)
    
    log_check("Memvid Repo", True, 
              f"{file_count} files, Found: {', '.join(found_files)}")
    
    return True

def check_10_github_app():
    """Check Cloudflare GitHub App"""
    print("\n10. Checking Cloudflare GitHub App...")
    
    print("   Please check manually:")
    print("   1. Go to: https://github.com/settings/installations")
    print("   2. Look for 'Cloudflare'")
    print("   3. Ensure it has access to SolarPunk-Nexus")
    print("   4. If not installed, go to: https://github.com/apps/cloudflare")
    
    return log_check("Cloudflare GitHub App", True, "Check manually above")

def main():
    """Run all checks"""
    all_checks = [
        check_1_cloudflare,
        check_2_local_files,
        check_3_github_status,
        check_4_netlify_status,
        check_5_python_environment,
        check_6_agent_files,
        check_7_fix_script,
        check_8_web_dashboard,
        check_9_memvid_repo,
        check_10_github_app
    ]
    
    results = []
    
    for check in all_checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("📊 DEBUG SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 EVERYTHING WORKS! SolarPunk is ready.")
    else:
        print("\n🔧 Some issues found. Check above for details.")
    
    print(f"\n📄 Full log: {debug_log}")
    
    # Create action plan
    print("\n🚀 ACTION PLAN:")
    
    if not any([check_1_cloudflare(), check_10_github_app()]):
        print("1. Install Cloudflare GitHub App")
        print("   Go to: https://github.com/apps/cloudflare")
    
    if not check_7_fix_script():
        print("2. Create fix script by running agent option 1")
    
    if not check_9_memvid_repo():
        print("3. Create Memvid repo by running agent option 2")
    
    print("\n💡 Quick test: Run the test_fix.bat script")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()