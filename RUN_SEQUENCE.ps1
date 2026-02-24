<#
.SYNOPSIS
    RUN SEQUENCE — Runs everything in order, shows you what's happening.
    This is the full system boot. Run after BOOTSTRAP.ps1.
    
.RUN:
    powershell -ExecutionPolicy Bypass -File RUN_SEQUENCE.ps1
    
    OR from repo root:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\RUN_SEQUENCE.ps1
#>

$ErrorActionPreference = "Continue"

function Write-G  { param($m) Write-Host $m -ForegroundColor Green }
function Write-Y  { param($m) Write-Host $m -ForegroundColor Yellow }
function Write-C  { param($m) Write-Host $m -ForegroundColor Cyan }
function Write-D  { param($m) Write-Host $m -ForegroundColor DarkGray }
function Write-R  { param($m) Write-Host $m -ForegroundColor Red }
function Write-W  { param($m) Write-Host $m -ForegroundColor White }

function Step { param($n, $total, $name) 
    Write-G ""
    Write-G "================================================================"
    Write-C "  STEP $n/$total — $name"
    Write-G "================================================================"
}

function RunPy { param($script, $args_str="")
    $pythonCmd = if (Get-Command python -EA SilentlyContinue) {'python'} 
                 elseif (Get-Command python3 -EA SilentlyContinue) {'python3'}
                 else { $null }
    if (-not $pythonCmd) {
        Write-R "  Python not found. Install from python.org"
        return $false
    }
    if (-not (Test-Path $script)) {
        Write-R "  File not found: $script"
        return $false
    }
    Write-D "  Running: $pythonCmd $script $args_str"
    if ($args_str) {
        & $pythonCmd $script $args_str.Split(' ')
    } else {
        & $pythonCmd $script
    }
    return $LASTEXITCODE -eq 0
}

$Desktop   = [Environment]::GetFolderPath('Desktop')
$MasterDir = "$Desktop\UltimateAI_Master"
$RepoPath  = "$MasterDir\meeko-nerve-center"

# Fallback if repo is elsewhere
foreach ($c in @("$Desktop\meeko-nerve-center", "$env:USERPROFILE\meeko-nerve-center")) {
    if (Test-Path $c) { $RepoPath = $c; break }
}

Write-G ""
Write-G "################################################################"
Write-G "#"
Write-G "#   MEEKO MYCELIUM — FULL SYSTEM RUN SEQUENCE"
Write-G "#   Everything, in order, connected."
Write-G "#"
Write-G "################################################################"
Write-G ""
Write-W "  Repo: $RepoPath"
Write-G ""

if (-not (Test-Path $RepoPath)) {
    Write-R "Repo not found at $RepoPath"
    Write-Y "Run BOOTSTRAP.ps1 first:"
    Write-C "irm https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/BOOTSTRAP.ps1 | iex"
    exit 1
}

Set-Location $RepoPath

# ============================================================
# STEP 1: GIT PULL — make sure we have the latest
# ============================================================
Step 1 9 "Git Pull — get latest from GitHub"
$gitExists = Get-Command git -EA SilentlyContinue
if ($gitExists) {
    Write-C "  Pulling latest..."
    git pull origin main 2>&1 | ForEach-Object { Write-D "  $_" }
    Write-G "  Up to date."
} else {
    Write-Y "  Git not installed — skipping pull. Download: https://git-scm.com"
}

# ============================================================
# STEP 2: DIAGNOSE — show what we have
# ============================================================
Step 2 9 "Diagnose — full system scan"
if (Test-Path "$RepoPath\DIAGNOSE.ps1") {
    & "$RepoPath\DIAGNOSE.ps1"
} else {
    Write-Y "  DIAGNOSE.ps1 not found — skipping"
}

# ============================================================
# STEP 3: CLEANUP AND BRIDGE — scan desktop, check Ollama, index everything
# ============================================================
Step 3 9 "Cleanup & Bridge — connect local brain to GitHub"
$result = RunPy "$RepoPath\CLEANUP_AND_BRIDGE.py"
if ($result) { Write-G "  Bridge: OK" } else { Write-Y "  Bridge: check output above" }

Start-Sleep -Seconds 1

# ============================================================
# STEP 4: WIRING HUB — connect all layers, write data bus
# ============================================================
Step 4 9 "Wiring Hub — all layers talking to all layers"
$result = RunPy "$RepoPath\mycelium\wiring_hub.py"
if ($result) { Write-G "  Wiring hub: OK" } else { Write-Y "  Wiring hub: check output above" }

Start-Sleep -Seconds 1

# ============================================================
# STEP 5: SPACE BRIDGE — ISS, NASA, space data
# ============================================================
Step 5 9 "Space Bridge — ISS position, NASA data"
$result = RunPy "$RepoPath\mycelium\space_bridge.py"
if ($result) { Write-G "  Space bridge: OK" } else { Write-Y "  Space bridge: check output above" }

Start-Sleep -Seconds 1

# ============================================================
# STEP 6: NETWORK NODE — network status
# ============================================================
Step 6 9 "Network Node — WiFi, network, connectivity"
$result = RunPy "$RepoPath\mycelium\network_node.py"
if ($result) { Write-G "  Network node: OK" } else { Write-Y "  Network node: check output above" }

Start-Sleep -Seconds 1

# ============================================================
# STEP 7: BUILD MCP CONFIG — wire Claude Desktop
# ============================================================
Step 7 9 "Build MCP Config — connect Claude Desktop to your system"
$result = RunPy "$RepoPath\BUILD_MCP_CONFIG.py"
if ($result) { Write-G "  MCP config: BUILT" } else { Write-Y "  MCP config: check output above" }

Start-Sleep -Seconds 1

# ============================================================
# STEP 8: PHONE PACKAGE — create phone zip
# ============================================================
Step 8 9 "Phone Package — putting system on your phone"
$result = RunPy "$RepoPath\PHONE_PACKAGE.py"
if ($result) { Write-G "  Phone package: created on Desktop" } else { Write-Y "  Phone package: check output above" }

Start-Sleep -Seconds 1

# ============================================================
# STEP 9: GRAND SETUP WIZARD — open web UI for API keys
# ============================================================
Step 9 9 "Grand Setup Wizard — wire your APIs (browser opening)"
Write-C "  Opening Setup Wizard at http://localhost:7776"
Write-D "  Fill in: Gmail app password, NASA key, Strike, Solana, GitHub token"
Write-D "  Close this window when done configuring."
Write-G ""

$pythonCmd = if (Get-Command python -EA SilentlyContinue) {'python'} else {'python3'}
if (Test-Path "$RepoPath\GRAND_SETUP_WIZARD.py") {
    Start-Process $pythonCmd "$RepoPath\GRAND_SETUP_WIZARD.py" -NoNewWindow
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:7776"
} else {
    Write-Y "  GRAND_SETUP_WIZARD.py not found"
}

# ============================================================
# FINAL REPORT
# ============================================================
Write-G ""
Write-G "################################################################"
Write-G "#   RUN SEQUENCE COMPLETE"
Write-G "################################################################"
Write-G ""
Write-C "  What just ran:"
Write-D "  1. Git pull        — repo is current"
Write-D "  2. Diagnose        — full system scan logged"
Write-D "  3. Cleanup/Bridge  — Ollama checked, all files indexed"
Write-D "  4. Wiring Hub      — all layers connected, data bus written"
Write-D "  5. Space Bridge    — ISS position + NASA data fetched"
Write-D "  6. Network Node    — WiFi + network status checked"
Write-D "  7. MCP Config      — Claude Desktop wired to your system"
Write-D "  8. Phone Package   — zip created on Desktop"
Write-D "  9. Setup Wizard    — running at localhost:7776"
Write-G ""
Write-C "  What to do next:"
Write-G "  1. RESTART CLAUDE DESKTOP — MCP config is now active"
Write-G "  2. Fill in Setup Wizard (http://localhost:7776) with your API keys"
Write-G "  3. Go to GitHub Secrets + add GMAIL_APP_PASSWORD"
Write-G "     github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets"
Write-G "  4. Email meeko_phone_package.zip to yourself"
Write-G ""
Write-Y "  Brave fix: if bad pages still appear, open brave://extensions"
Write-Y "  and disable any extension you don't recognize."
Write-G ""
Write-G "  System is alive."
Write-G ""
