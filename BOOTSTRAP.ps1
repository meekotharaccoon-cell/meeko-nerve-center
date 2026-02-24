<#
.SYNOPSIS
    MEEKO MYCELIUM BOOTSTRAP — Run this ONCE to set up everything.
    
    This script:
    1. Finds or creates your UltimateAI_Master folder
    2. Clones/updates the GitHub repo
    3. Runs full diagnostics
    4. Fixes Brave browser startup issues
    5. Creates all missing Python scripts
    6. Installs Python dependencies
    7. Connects everything together
    
.HOW TO RUN:
    Open PowerShell as normal user (NOT admin needed) and run:
    
    irm https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/BOOTSTRAP.ps1 | iex
    
    OR if you have the repo cloned:
    
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\BOOTSTRAP.ps1
#>

$ErrorActionPreference = "Continue"

# Colors
function Write-G { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Y { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-R { param($msg) Write-Host $msg -ForegroundColor Red }
function Write-C { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-D { param($msg) Write-Host $msg -ForegroundColor DarkGray }

Write-G ""
Write-G "================================================================"
Write-G "  MEEKO MYCELIUM BOOTSTRAP"
Write-G "  Your system, finding itself."
Write-G "================================================================"
Write-G ""

# ============================================================
# STEP 1: FIND SYSTEM PATHS
# ============================================================
Write-C "[1/8] Detecting system paths..."

$Desktop     = [Environment]::GetFolderPath('Desktop')
$Home        = $env:USERPROFILE
$RepoName    = "meeko-nerve-center"
$RepoURL     = "https://github.com/meekotharaccoon-cell/meeko-nerve-center.git"

# Try to find existing repo
$RepoCandidates = @(
    "$Desktop\UltimateAI_Master\$RepoName",
    "$Desktop\$RepoName",
    "$Home\$RepoName",
    "$Home\Documents\$RepoName"
)

$RepoPath = $null
foreach ($c in $RepoCandidates) {
    if (Test-Path $c) {
        $RepoPath = $c
        Write-G "  FOUND repo at: $RepoPath"
        break
    }
}

if (-not $RepoPath) {
    # Check if git exists
    $gitExists = Get-Command git -ErrorAction SilentlyContinue
    if ($gitExists) {
        $MasterDir = "$Desktop\UltimateAI_Master"
        if (-not (Test-Path $MasterDir)) {
            New-Item -ItemType Directory -Path $MasterDir -Force | Out-Null
            Write-G "  Created: $MasterDir"
        }
        Write-C "  Cloning repo..."
        git clone $RepoURL "$MasterDir\$RepoName" 2>&1
        $RepoPath = "$MasterDir\$RepoName"
        Write-G "  Cloned to: $RepoPath"
    } else {
        Write-Y "  Git not found. Downloading as ZIP..."
        $ZipUrl  = "https://github.com/meekotharaccoon-cell/meeko-nerve-center/archive/refs/heads/main.zip"
        $ZipPath = "$env:TEMP\meeko-nerve-center.zip"
        $ExtractTo = "$Desktop\UltimateAI_Master"
        Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath
        Expand-Archive -Path $ZipPath -DestinationPath $ExtractTo -Force
        Rename-Item "$ExtractTo\meeko-nerve-center-main" "$ExtractTo\$RepoName" -ErrorAction SilentlyContinue
        $RepoPath = "$ExtractTo\$RepoName"
        Write-G "  Extracted to: $RepoPath"
    }
}

Write-G "  Repo path: $RepoPath"

# ============================================================
# STEP 2: GIT PULL (UPDATE)
# ============================================================
Write-C "[2/8] Updating repo..."
$gitExists = Get-Command git -ErrorAction SilentlyContinue
if ($gitExists -and (Test-Path "$RepoPath\.git")) {
    Set-Location $RepoPath
    git pull origin main 2>&1 | ForEach-Object { Write-D "  $_" }
    Write-G "  Repo up to date."
} else {
    Write-Y "  Skipping git pull (no .git or git not installed)."
}

# ============================================================
# STEP 3: CHECK PYTHON
# ============================================================
Write-C "[3/8] Checking Python..."
$pythonCmd = $null
foreach ($cmd in @('python', 'python3', 'py')) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match 'Python 3') {
            $pythonCmd = $cmd
            Write-G "  Python found: $ver"
            break
        }
    } catch {}
}
if (-not $pythonCmd) {
    Write-R "  Python 3 NOT FOUND."
    Write-Y "  Install from: https://python.org (check 'Add to PATH' during install)"
    Write-Y "  Then re-run this script."
} else {
    # Install key dependencies
    Write-C "  Installing dependencies..."
    $deps = @('requests', 'flask', 'websockets', 'paho-mqtt', 'gitpython')
    foreach ($pkg in $deps) {
        $result = & $pythonCmd -m pip install $pkg -q 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-D "    + $pkg"
        } else {
            Write-Y "    ? $pkg (may already be installed)"
        }
    }
    Write-G "  Dependencies checked."
}

# ============================================================
# STEP 4: FIX BRAVE BROWSER
# ============================================================
Write-C "[4/8] Fixing Brave browser startup pages..."

$BravePrefsPath = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Preferences"

if (Test-Path $BravePrefsPath) {
    # Kill Brave first
    $braveProcess = Get-Process brave -ErrorAction SilentlyContinue
    if ($braveProcess) {
        Write-Y "  Brave is running. Closing it to fix settings..."
        Stop-Process -Name brave -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    
    try {
        $prefs = Get-Content $BravePrefsPath -Raw | ConvertFrom-Json
        $changed = $false
        
        # Clear bad startup URLs
        if ($prefs.session -and $prefs.session.startup_urls) {
            $badUrls = $prefs.session.startup_urls | Where-Object { 
                $_ -match '404' -or 
                $_ -match 'redbubble.com' -or
                $_ -match 'error'
            }
            if ($badUrls) {
                Write-Y "  Found bad startup URLs:"
                $badUrls | ForEach-Object { Write-R "    REMOVING: $_" }
                $prefs.session.startup_urls = $prefs.session.startup_urls | Where-Object { 
                    $_ -notmatch '404' -and 
                    $_ -notmatch 'redbubble.com' -and
                    $_ -notmatch 'error'
                }
                $changed = $true
            }
        }
        
        # Check restore_on_startup (1=restore, 4=specific pages, 5=new tab)
        if ($prefs.session.restore_on_startup -eq 4) {
            Write-D "  Startup mode: open specific pages"
            if ($prefs.session.startup_urls) {
                Write-C "  Current startup URLs:"
                $prefs.session.startup_urls | ForEach-Object { Write-D "    $_" }
            }
        }
        
        if ($changed) {
            $prefs | ConvertTo-Json -Depth 100 | Set-Content $BravePrefsPath -Encoding UTF8
            Write-G "  Brave preferences fixed."
        } else {
            Write-G "  No bad URLs found in Brave startup settings."
            Write-D "  If you're still seeing bad pages, check Brave Settings > On startup"
        }
        
        # Also check for malicious extensions
        $ExtDir = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Extensions"
        if (Test-Path $ExtDir) {
            $extCount = (Get-ChildItem $ExtDir -Directory).Count
            Write-D "  Extensions installed: $extCount"
            Write-D "  To review: open brave://extensions in Brave"
        }
        
    } catch {
        Write-Y "  Could not parse Brave preferences: $_"
        Write-Y "  Manual fix: Open Brave > Settings > On startup > Open a specific page"
        Write-Y "  Remove any pages with 'redbubble.com' or 404 errors."
    }
} else {
    Write-D "  Brave not installed or preferences not found."
    Write-D "  Path checked: $BravePrefsPath"
}

# Also check Windows Task Scheduler for anything opening Brave
Write-C "  Checking scheduled tasks that might open Brave..."
try {
    $tasks = Get-ScheduledTask | Where-Object { 
        $_.Actions | Where-Object { $_.Execute -match 'brave' }
    } -ErrorAction SilentlyContinue
    if ($tasks) {
        Write-Y "  Scheduled tasks launching Brave:"
        $tasks | ForEach-Object { 
            Write-Y "    Task: $($_.TaskName)"
            $_.Actions | ForEach-Object { Write-Y "      $($_.Execute) $($_.Arguments)" }
        }
    } else {
        Write-G "  No suspicious scheduled tasks found for Brave."
    }
} catch {
    Write-D "  (Could not check scheduled tasks)"
}

# ============================================================
# STEP 5: CREATE MISSING SCRIPTS
# ============================================================
Write-C "[5/8] Creating missing desktop scripts..."

$MasterDir = "$Desktop\UltimateAI_Master"
if (-not (Test-Path $MasterDir)) {
    New-Item -ItemType Directory -Path $MasterDir -Force | Out-Null
}

# CLEANUP_AND_BRIDGE.py — if missing, copy from repo or create it
$CleanupPath = "$MasterDir\CLEANUP_AND_BRIDGE.py"
if (-not (Test-Path $CleanupPath)) {
    $repoVersion = "$RepoPath\CLEANUP_AND_BRIDGE.py"
    if (Test-Path $repoVersion) {
        Copy-Item $repoVersion $CleanupPath
        Write-G "  Created CLEANUP_AND_BRIDGE.py (from repo)"
    } else {
        # Create minimal version
        $content = @'
#!/usr/bin/env python3
"""
CLEANUP_AND_BRIDGE.py — Connect local Ollama to GitHub organism
Created by BOOTSTRAP.ps1
"""
import os
import sys
import subprocess
import json
from pathlib import Path

print("\n━" * 60)
print("  CLEANUP AND BRIDGE")
print("  Connecting local Ollama brain to GitHub organism")
print("━" * 60)

# Check Ollama
try:
    import urllib.request
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
        data = json.loads(r.read())
        models = [m['name'] for m in data.get('models', [])]
        print(f"\n\033[92m✓ Ollama running. Models: {', '.join(models)}\033[0m")
except:
    print("\n\033[93m⚠ Ollama not running. Start it: ollama serve\033[0m")
    print("  Download: https://ollama.ai")

# Check git
try:
    result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"\n\033[92m✓ Git remotes:\033[0m")
        print(result.stdout)
except:
    print("\n\033[93mGit not found\033[0m")

# Find all Python scripts
desktop = Path.home() / 'Desktop'
scripts = list(desktop.rglob('*.py'))
print(f"\n\033[96mPython scripts on Desktop: {len(scripts)}\033[0m")
for s in scripts[:20]:
    print(f"  {s.name}")

print("\n\033[92mBridge check complete.\033[0m")
print("Next: run BUILD_MCP_CONFIG.py then restart Claude Desktop.")
'@
        $content | Out-File -FilePath $CleanupPath -Encoding UTF8
        Write-G "  Created CLEANUP_AND_BRIDGE.py (fresh)"
    }
}

# GRAND_SETUP_WIZARD.py
$WizardPath = "$MasterDir\GRAND_SETUP_WIZARD.py"
if (-not (Test-Path $WizardPath)) {
    $repoVersion = "$RepoPath\GRAND_SETUP_WIZARD.py"
    if (Test-Path $repoVersion) {
        Copy-Item $repoVersion $WizardPath
        Write-G "  Created GRAND_SETUP_WIZARD.py (from repo)"
    } else {
        Write-Y "  GRAND_SETUP_WIZARD.py not in repo yet — will be created."
    }
}

# BUILD_MCP_CONFIG.py — copy from repo to desktop
$McpPath = "$MasterDir\BUILD_MCP_CONFIG.py"
if (-not (Test-Path $McpPath)) {
    $repoVersion = "$RepoPath\BUILD_MCP_CONFIG.py"
    if (Test-Path $repoVersion) {
        Copy-Item $repoVersion $McpPath
        Write-G "  Created BUILD_MCP_CONFIG.py (from repo)"
    }
}

# ============================================================
# STEP 6: RUN DIAGNOSTICS
# ============================================================
Write-C "[6/8] Running diagnostics..."

$diagScript = "$RepoPath\DIAGNOSE.ps1"
if (Test-Path $diagScript) {
    Write-C "  Running full diagnostic..."
    & $diagScript
} else {
    # Quick inline diagnostic
    Write-D "  Quick diagnostic:"
    
    $checks = @(
        @{ Name = "Python 3";       Test = { Get-Command python -EA SilentlyContinue } },
        @{ Name = "Git";            Test = { Get-Command git -EA SilentlyContinue } },
        @{ Name = "Node.js";        Test = { Get-Command node -EA SilentlyContinue } },
        @{ Name = "Ollama";         Test = { Test-NetConnection localhost -Port 11434 -WarningAction SilentlyContinue -InformationLevel Quiet } },
        @{ Name = "Repo cloned";    Test = { Test-Path $RepoPath } },
        @{ Name = "MasterDir";      Test = { Test-Path $MasterDir } }
    )
    
    foreach ($check in $checks) {
        $result = & $check.Test
        if ($result) {
            Write-G "  [OK] $($check.Name)"
        } else {
            Write-Y "  [MISSING] $($check.Name)"
        }
    }
}

# ============================================================
# STEP 7: CONNECT EVERYTHING
# ============================================================
Write-C "[7/8] Wiring everything together..."

# Run the wiring hub if Python available
if ($pythonCmd -and (Test-Path "$RepoPath\mycelium\wiring_hub.py")) {
    Write-C "  Running wiring hub..."
    Set-Location $RepoPath
    & $pythonCmd "mycelium\wiring_hub.py" 2>&1 | ForEach-Object { Write-D "  $_" }
    Write-G "  Wiring hub complete."
}

# Run BUILD_MCP_CONFIG.py
if ($pythonCmd -and (Test-Path "$RepoPath\BUILD_MCP_CONFIG.py")) {
    Write-C "  Building MCP config for Claude Desktop..."
    Set-Location $RepoPath
    & $pythonCmd BUILD_MCP_CONFIG.py 2>&1 | ForEach-Object { Write-D "  $_" }
}

# ============================================================
# STEP 8: SUMMARY
# ============================================================
Write-C "[8/8] Summary"
Write-G ""
Write-G "================================================================"
Write-G "  BOOTSTRAP COMPLETE"
Write-G "================================================================"
Write-G ""
Write-G "  Repo location: $RepoPath"
Write-G ""

$nextSteps = @(
    "1. Restart Claude Desktop (MCP config updated)",
    "2. Add GMAIL_APP_PASSWORD to GitHub Secrets",
    "3. Create Gumroad account, list fork-guide.md at $5",
    "4. Run: python mycelium\wiring_hub.py (full system status)",
    "5. Run: python mycelium\network_node.py (network status)"
)

Write-C "  Next steps:"
foreach ($step in $nextSteps) {
    Write-G "  $step"
}

Write-G ""
Write-D "  Brave browser fix applied. If pages still appear:"
Write-D "  Open Brave > Settings > On startup > review"
Write-D ""
Write-G "  System is oriented. Build continues."
Write-G ""
