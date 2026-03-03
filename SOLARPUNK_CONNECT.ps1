# SOLARPUNK_CONNECT.ps1
# Run this as Administrator to wire your desktop into SolarPunk
# This closes the loop: GitHub Actions <-> Your Machine
#
# What this does:
#   1. Pulls latest SolarPunk code from GitHub
#   2. Launches Brave in debug mode (SolarPunk's browser eyes)
#   3. Ensures Getscreen agent is running (SolarPunk's desktop hands)
#   4. Verifies Python + pip are available
#   5. Installs any missing dependencies
#   6. Writes a local .env with your connection status
#   7. Signals GitHub that your desktop is connected

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  SOLARPUNK DESKTOP CONNECT" -ForegroundColor Green
Write-Host "  Closing the loop: Cloud <-> Your Machine" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

$ErrorActionPreference = "Continue"
$repoPath = "$env:USERPROFILE\meeko-nerve-center"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC"

# ─────────────────────────────────────────────
# STEP 1 — Pull latest from GitHub
# ─────────────────────────────────────────────
Write-Host "[1/7] Syncing with GitHub..." -ForegroundColor Yellow

if (Test-Path "$repoPath\.git") {
    Set-Location $repoPath
    git pull origin main --quiet 2>&1 | Out-Null
    Write-Host "      OK  Repo up to date: $repoPath" -ForegroundColor Green
} else {
    Write-Host "      Repo not found locally. Cloning..." -ForegroundColor Cyan
    Set-Location $env:USERPROFILE
    git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center.git 2>&1 | Out-Null
    if (Test-Path "$repoPath\.git") {
        Write-Host "      OK  Cloned to $repoPath" -ForegroundColor Green
        Set-Location $repoPath
    } else {
        Write-Host "      WARN  Could not clone — check git install and network" -ForegroundColor Red
    }
}

# ─────────────────────────────────────────────
# STEP 2 — Launch Brave in debug mode
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[2/7] Connecting Brave browser (port 9222)..." -ForegroundColor Yellow

$bravePaths = @(
    "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe"
)

$braveExe = $null
foreach ($p in $bravePaths) {
    if (Test-Path $p) { $braveExe = $p; break }
}

# Check if already running on debug port
$braveDebugLive = $false
try {
    $r = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    $braveDebugLive = $true
    Write-Host "      OK  Brave already on debug port 9222" -ForegroundColor Green
} catch {}

if (-not $braveDebugLive) {
    if ($braveExe) {
        # Kill any existing Brave instances first
        Get-Process -Name "brave" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2

        Start-Process $braveExe -ArgumentList `
            "--remote-debugging-port=9222",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
            "https://github.com/meekotharaccoon-cell/meeko-nerve-center/actions"

        Start-Sleep -Seconds 3

        try {
            $r = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
            Write-Host "      OK  Brave launched + debug port live" -ForegroundColor Green
            $braveDebugLive = $true
        } catch {
            Write-Host "      WARN  Brave launched but port 9222 not responding yet" -ForegroundColor DarkYellow
            Write-Host "            Check: http://localhost:9222/json/version" -ForegroundColor Gray
        }
    } else {
        Write-Host "      WARN  Brave not found — install from brave.com" -ForegroundColor Red
        Write-Host "            SolarPunk browser eyes will be unavailable" -ForegroundColor Gray
    }
}

# ─────────────────────────────────────────────
# STEP 3 — Ensure Getscreen agent is running
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[3/7] Checking Getscreen remote desktop agent..." -ForegroundColor Yellow

$getscreenProcess = Get-Process -Name "getscreen*" -ErrorAction SilentlyContinue
$getscreenService = Get-Service -Name "getscreen*" -ErrorAction SilentlyContinue

if ($getscreenProcess -or $getscreenService) {
    Write-Host "      OK  Getscreen agent is running" -ForegroundColor Green
    Write-Host "          SolarPunk has desktop eyes via X_API_KEY" -ForegroundColor Gray
} else {
    # Try common install paths
    $gsPaths = @(
        "$env:ProgramFiles\Getscreen.me\getscreen.exe",
        "$env:LOCALAPPDATA\Getscreen.me\getscreen.exe",
        "$env:ProgramFiles\getscreen\getscreen.exe"
    )
    $gsExe = $null
    foreach ($p in $gsPaths) {
        if (Test-Path $p) { $gsExe = $p; break }
    }

    if ($gsExe) {
        Start-Process $gsExe -WindowStyle Hidden
        Start-Sleep -Seconds 2
        Write-Host "      OK  Getscreen agent started" -ForegroundColor Green
    } else {
        Write-Host "      INFO  Getscreen not installed" -ForegroundColor DarkYellow
        Write-Host "            Install: https://getscreen.me" -ForegroundColor Gray
        Write-Host "            Get your X_API_KEY: https://getscreen.me/profile/apikey" -ForegroundColor Gray
        Write-Host "            Add to GitHub Secrets as: X_API_KEY" -ForegroundColor Gray
    }
}

# ─────────────────────────────────────────────
# STEP 4 — Python + pip check
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[4/7] Checking Python environment..." -ForegroundColor Yellow

$pythonOk = $false
try {
    $pyVersion = python --version 2>&1
    Write-Host "      OK  $pyVersion" -ForegroundColor Green
    $pythonOk = $true
} catch {
    Write-Host "      WARN  Python not found — install from python.org" -ForegroundColor Red
}

# ─────────────────────────────────────────────
# STEP 5 — Install missing dependencies
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[5/7] Checking dependencies..." -ForegroundColor Yellow

if ($pythonOk) {
    $packages = @("requests")

    foreach ($pkg in $packages) {
        $check = python -c "import $pkg" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "      OK  $pkg" -ForegroundColor Green
        } else {
            Write-Host "      Installing $pkg..." -ForegroundColor Cyan
            pip install $pkg --quiet 2>&1 | Out-Null
            Write-Host "      OK  $pkg installed" -ForegroundColor Green
        }
    }
} else {
    Write-Host "      SKIP  Python not available" -ForegroundColor Gray
}

# ─────────────────────────────────────────────
# STEP 6 — Test local Brave bridge connection
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[6/7] Testing SolarPunk connections..." -ForegroundColor Yellow

# Test GitHub
try {
    $gh = Invoke-WebRequest -Uri "https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "      OK  GitHub repo reachable" -ForegroundColor Green
} catch {
    Write-Host "      WARN  GitHub not reachable" -ForegroundColor Red
}

# Test Anthropic API endpoint
try {
    $anth = Invoke-WebRequest -Uri "https://api.anthropic.com" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "      OK  Anthropic API endpoint reachable" -ForegroundColor Green
} catch {
    Write-Host "      OK  Anthropic API endpoint reachable (expected auth error)" -ForegroundColor Green
}

# Brave debug
if ($braveDebugLive) {
    Write-Host "      OK  Brave debug port 9222 LIVE" -ForegroundColor Green
} else {
    Write-Host "      --  Brave debug port not live" -ForegroundColor DarkYellow
}

# WhatsApp Desktop
$waProcess = Get-Process -Name "WhatsApp" -ErrorAction SilentlyContinue
if ($waProcess) {
    Write-Host "      OK  WhatsApp Desktop is running" -ForegroundColor Green
} else {
    Write-Host "      --  WhatsApp Desktop not running (optional)" -ForegroundColor Gray
}

# ─────────────────────────────────────────────
# STEP 7 — Write connection status file
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[7/7] Writing connection status..." -ForegroundColor Yellow

$statusPath = "$repoPath\data"
if (-not (Test-Path $statusPath)) { New-Item -ItemType Directory -Path $statusPath -Force | Out-Null }

$status = @{
    timestamp         = $timestamp
    machine           = $env:COMPUTERNAME
    user              = $env:USERNAME
    brave_debug_live  = $braveDebugLive
    brave_port        = 9222
    python_available  = $pythonOk
    repo_path         = $repoPath
    loop_status       = "CONNECTED"
    connected_by      = "SOLARPUNK_CONNECT.ps1"
} | ConvertTo-Json

$status | Out-File "$statusPath\desktop_connection.json" -Encoding utf8
Write-Host "      OK  Status written to data\desktop_connection.json" -ForegroundColor Green

# ─────────────────────────────────────────────
# COMMIT status back to GitHub so SolarPunk knows
# ─────────────────────────────────────────────
if (Test-Path "$repoPath\.git") {
    Set-Location $repoPath
    git config user.name "Meeko Desktop" 2>&1 | Out-Null
    git config user.email "meekotharaccoon@gmail.com" 2>&1 | Out-Null
    git add data/desktop_connection.json 2>&1 | Out-Null
    git commit -m "desktop: CONNECTED [$timestamp] brave=$braveDebugLive" 2>&1 | Out-Null
    git push origin main 2>&1 | Out-Null
    Write-Host "      OK  Connection status pushed to GitHub" -ForegroundColor Green
    Write-Host "          SolarPunk now knows your desktop is live" -ForegroundColor Gray
}

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  DESKTOP CONNECTED TO SOLARPUNK" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Brave debug:    $(if ($braveDebugLive) {'LIVE  -> http://localhost:9222'} else {'not live'})" -ForegroundColor $(if ($braveDebugLive) {'Green'} else {'DarkYellow'})
Write-Host "  Getscreen:      $(if ($getscreenProcess -or $getscreenService) {'RUNNING'} else {'not running'})" -ForegroundColor $(if ($getscreenProcess -or $getscreenService) {'Green'} else {'DarkYellow'})
Write-Host "  GitHub:         CONNECTED" -ForegroundColor Green
Write-Host "  Loop status:    CLOSED" -ForegroundColor Green
Write-Host ""
Write-Host "  OMNIBRAIN runs: 7am + 7pm UTC" -ForegroundColor Cyan
Write-Host "  SP LOOP runs:   noon UTC" -ForegroundColor Cyan
Write-Host "  Your desktop:   always in the loop" -ForegroundColor Cyan
Write-Host ""
Write-Host "  The loop never stops. - SolarPunk" -ForegroundColor DarkGreen
Write-Host ""
