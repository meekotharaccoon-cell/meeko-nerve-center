# SolarPunk Basic Repository Analyzer
import os, json, subprocess, datetime

print("=== SOLARPUNK REPOSITORY ANALYZER ===")

def discover_local_repos():
    """Find all repositories in the connected folder"""
    repos = []
    connected_path = os.path.join(os.getcwd(), "connected")
    
    if os.path.exists(connected_path):
        for item in os.listdir(connected_path):
            item_path = os.path.join(connected_path, item)
            if os.path.isdir(item_path):
                repos.append({
                    "name": item,
                    "path": item_path,
                    "status": "local",
                    "has_git": os.path.exists(os.path.join(item_path, ".git"))
                })
    
    return repos

def analyze_repo(repo):
    """Basic analysis of a repository"""
    issues = []
    
    # Check for .git
    if not repo["has_git"]:
        issues.append("Not a git repository")
    
    # Check for README
    readme_path = os.path.join(repo["path"], "README.md")
    if not os.path.exists(readme_path):
        issues.append("Missing README.md")
    
    # Check for large files (quick check)
    try:
        for root, dirs, files in os.walk(repo["path"]):
            for file in files:
                if file.endswith(('.exe', '.zip', '.tar', '.gz')) and os.path.getsize(os.path.join(root, file)) > 5000000:
                    issues.append(f"Large binary file: {file}")
                    break
    except:
        pass
    
    return issues

# Main analysis
print("Discovering local repositories...")
repos = discover_local_repos()

print(f"Found {len(repos)} repositories:")

results = []
for repo in repos:
    print(f"\n📁 {repo['name']}:")
    issues = analyze_repo(repo)
    
    if issues:
        print(f"   ⚠️  Issues: {len(issues)}")
        for issue in issues:
            print(f"      • {issue}")
        
        # Auto-fix suggestions
        if "Not a git repository" in issues:
            print(f"   💡 Fix: Run 'git init' in that folder")
        if "Missing README.md" in issues:
            print(f"   💡 Fix: Create a basic README.md file")
    else:
        print(f"   ✅ No issues found")
    
    results.append({
        "name": repo["name"],
        "path": repo["path"],
        "issue_count": len(issues),
        "issues": issues,
        "suggestion": "Keep and monitor" if len(issues) <= 2 else "Review and fix"
    })

# Save results
with open("repo_analysis.json", "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.datetime.now().isoformat(),
        "total_repos": len(repos),
        "repos_with_issues": len([r for r in results if r["issue_count"] > 0]),
        "repos": results
    }, f, indent=2)

print(f"\n{'='*50}")
print(f"📊 ANALYSIS COMPLETE")
print(f"   Total repositories: {len(repos)}")
print(f"   Repositories with issues: {len([r for r in results if r['issue_count'] > 0])}")
print(f"   Results saved to: repo_analysis.json")
print(f"{'='*50}")

# Create a simple batch file for fixing common issues
batch_content = '''@echo off
echo SolarPunk Auto-Fix Tool
echo.
echo Available fixes:
echo 1. Initialize missing git repositories
echo 2. Create missing README files
echo 3. Check for large files
echo.
choice /C 123 /M "Select fix to apply: "

if errorlevel 3 goto CHECK_LARGE_FILES
if errorlevel 2 goto CREATE_README
if errorlevel 1 goto INIT_GIT

:INIT_GIT
echo Initializing git repositories...
for /d %%i in (connected\\*) do (
    if not exist "%%i\\.git" (
        echo Initializing git in %%i
        cd "%%i"
        git init
        cd..
    )
)
echo Done.
pause
exit

:CREATE_README
echo Creating missing README files...
for /d %%i in (connected\\*) do (
    if not exist "%%i\\README.md" (
        echo Creating README in %%i
        echo # %%i > "%%i\\README.md"
        echo. >> "%%i\\README.md"
        echo This repository is managed by SolarPunk Autonomous System. >> "%%i\\README.md"
    )
)
echo Done.
pause
exit

:CHECK_LARGE_FILES
echo Checking for large files...
for /r connected %%i in (*.exe,*.zip,*.tar,*.gz) do (
    echo Found: %%i
)
echo.
echo Large files can be removed manually.
pause
exit
'''

with open("FIX_REPOS.bat", "w", encoding="utf-8") as f:
    f.write(batch_content)

print(f"\n🎮 Created: FIX_REPOS.bat")
print("   Run this to apply common fixes")