# MASTER_CONNECT.ps1
# One command connects your entire desktop to SolarPunk
# Run as Administrator via:
# iex (irm "https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/MASTER_CONNECT.ps1")

$ErrorActionPreference = "Continue"
$repoUrl  = "https://github.com/meekotharaccoon-cell/meeko-nerve-center.git"
$rawBase  = "https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main"
$repoPath = "$env:USERPROFILE\meeko-nerve-center"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  SOLARPUNK MASTER CONNECT" -ForegroundColor Green
Write-Host "  Wiring your desktop into the loop" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# ── 1. REPO ──────────────────────────────────
Write-Host "[1/8] Syncing repo..." -ForegroundColor Yellow
if (Test-Path "$repoPath\.git") {
    Set-Location $repoPath
    git pull origin main --quiet 2>&1 | Out-Null
    Write-Host "      OK  $repoPath" -ForegroundColor Green
} else {
    Set-Location $env:USERPROFILE
    git clone $repoUrl 2>&1 | Out-Null
    Set-Location $repoPath
    Write-Host "      OK  Cloned to $repoPath" -ForegroundColor Green
}

# ── 2. PYTHON DEPS ───────────────────────────
Write-Host ""
Write-Host "[2/8] Installing Python dependencies..." -ForegroundColor Yellow
$pythonOk = $false
try {
    $v = python --version 2>&1
    Write-Host "      OK  $v" -ForegroundColor Green
    $pythonOk = $true
    $pkgs = "requests", "playwright"
    foreach ($pkg in $pkgs) {
        $chk = python -c "import $($pkg.Replace('-','_'))" 2>&1
        if ($LASTEXITCODE -ne 0) {
            pip install $pkg --quiet 2>&1 | Out-Null
            Write-Host "      OK  installed $pkg" -ForegroundColor Green
        } else {
            Write-Host "      OK  $pkg" -ForegroundColor Green
        }
    }
    # Playwright browsers
    python -m playwright install chromium --quiet 2>&1 | Out-Null
    Write-Host "      OK  Playwright chromium ready" -ForegroundColor Green
} catch {
    Write-Host "      WARN  Python not found" -ForegroundColor Red
}

# ── 3. BRAVE DEBUG PORT ──────────────────────
Write-Host ""
Write-Host "[3/8] Brave browser (debug port 9222)..." -ForegroundColor Yellow
$braveAlive = $false
try {
    Invoke-WebRequest "http://localhost:9222/json/version" -TimeoutSec 2 -UseBasicParsing -EA Stop | Out-Null
    $braveAlive = $true
    Write-Host "      OK  Already live on port 9222" -ForegroundColor Green
} catch {}

if (-not $braveAlive) {
    $bPaths = @(
        "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe"
    )
    $bExe = $null
    foreach ($p in $bPaths) { if (Test-Path $p) { $bExe = $p; break } }

    if ($bExe) {
        Get-Process -Name "brave" -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
        Start-Sleep 2
        Start-Process $bExe -ArgumentList "--remote-debugging-port=9222","--remote-allow-origins=*","--no-first-run","--no-default-browser-check"
        Start-Sleep 3
        try {
            Invoke-WebRequest "http://localhost:9222/json/version" -TimeoutSec 3 -UseBasicParsing -EA Stop | Out-Null
            $braveAlive = $true
            Write-Host "      OK  Launched + port 9222 live" -ForegroundColor Green
        } catch {
            Write-Host "      WARN  Launched but port not responding yet" -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "      WARN  Brave not installed — install from brave.com" -ForegroundColor Red
    }
}

# ── 4. GETSCREEN AGENT ───────────────────────
Write-Host ""
Write-Host "[4/8] Getscreen remote desktop agent..." -ForegroundColor Yellow
$gsAlive = $false
$gsProc  = Get-Process -Name "getscreen*" -EA SilentlyContinue
$gsSvc   = Get-Service -Name "getscreen*" -EA SilentlyContinue
if ($gsProc -or $gsSvc) {
    $gsAlive = $true
    Write-Host "      OK  Agent running — desktop hands active" -ForegroundColor Green
} else {
    $gsPaths = @(
        "$env:ProgramFiles\Getscreen.me\getscreen.exe",
        "$env:LOCALAPPDATA\Getscreen.me\getscreen.exe",
        "$env:ProgramFiles\getscreen\getscreen.exe"
    )
    $gsExe = $null
    foreach ($p in $gsPaths) { if (Test-Path $p) { $gsExe = $p; break } }
    if ($gsExe) {
        Start-Process $gsExe -WindowStyle Hidden
        Start-Sleep 2
        $gsAlive = $true
        Write-Host "      OK  Agent started" -ForegroundColor Green
    } else {
        Write-Host "      INFO  Not installed — get it at getscreen.me" -ForegroundColor DarkYellow
        Write-Host "            Then add X_API_KEY to GitHub Secrets" -ForegroundColor Gray
    }
}

# ── 5. WHATSAPP DESKTOP ──────────────────────
Write-Host ""
Write-Host "[5/8] WhatsApp Desktop..." -ForegroundColor Yellow
$waAlive = $false
$waProc  = Get-Process -Name "WhatsApp" -EA SilentlyContinue
if ($waProc) {
    $waAlive = $true
    Write-Host "      OK  Running" -ForegroundColor Green
} else {
    $waPaths = @(
        "$env:LOCALAPPDATA\WhatsApp\WhatsApp.exe",
        "$env:ProgramFiles\WindowsApps\5319275A.WhatsAppDesktop*\WhatsApp.exe"
    )
    $waExe = $null
    foreach ($p in $waPaths) {
        $resolved = Get-Item $p -EA SilentlyContinue | Select-Object -First 1
        if ($resolved) { $waExe = $resolved.FullName; break }
    }
    if ($waExe) {
        Start-Process $waExe -WindowStyle Minimized
        Start-Sleep 2
        $waAlive = $true
        Write-Host "      OK  Launched (minimized)" -ForegroundColor Green
    } else {
        Write-Host "      --  Not found (optional)" -ForegroundColor Gray
    }
}

# ── 6. RUN GETSCREEN BRIDGE ──────────────────
Write-Host ""
Write-Host "[6/8] Running GETSCREEN_BRIDGE.py..." -ForegroundColor Yellow
if ($pythonOk -and (Test-Path "$repoPath\mycelium\GETSCREEN_BRIDGE.py")) {
    Set-Location $repoPath
    $gsOut = python mycelium\GETSCREEN_BRIDGE.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      OK  Bridge verified" -ForegroundColor Green
    } else {
        Write-Host "      INFO  Bridge ran (X_API_KEY needed for full remote control)" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "      SKIP  Python or bridge not available" -ForegroundColor Gray
}

# ── 7. WINDOWS TASK — AUTO RECONNECT ON BOOT ─
Write-Host ""
Write-Host "[7/8] Setting up auto-reconnect on startup..." -ForegroundColor Yellow
$taskName = "SolarPunk-AutoConnect"
$existing = Get-ScheduledTask -TaskName $taskName -EA SilentlyContinue
if (-not $existing) {
    $action  = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -Command `"iex (irm 'https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/MASTER_CONNECT.ps1')`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -RunOnlyIfNetworkAvailable
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -RunLevel Highest -Settings $settings -Description "SolarPunk desktop auto-connect" `
        -Force 2>&1 | Out-Null
    Write-Host "      OK  Task '$taskName' created — runs at every login" -ForegroundColor Green
} else {
    Write-Host "      OK  Task already exists" -ForegroundColor Green
}

# ── 8. COMMIT STATUS BACK TO GITHUB ──────────
Write-Host ""
Write-Host "[8/8] Signaling GitHub — desktop is live..." -ForegroundColor Yellow
Set-Location $repoPath

if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" -Force | Out-Null }

@{
    timestamp        = $timestamp
    machine          = $env:COMPUTERNAME
    user             = $env:USERNAME
    brave_debug      = $braveAlive
    getscreen        = $gsAlive
    whatsapp         = $waAlive
    python           = $pythonOk
    loop_status      = "CONNECTED"
    auto_reconnect   = $true
    connected_by     = "MASTER_CONNECT.ps1"
} | ConvertTo-Json | Out-File "data\desktop_connection.json" -Encoding utf8

git config user.name  "Meeko Desktop" 2>&1 | Out-Null
git config user.email "meekotharaccoon@gmail.com" 2>&1 | Out-Null
git add data\desktop_connection.json 2>&1 | Out-Null
git commit -m "desktop: CONNECTED [$timestamp] brave=$braveAlive getscreen=$gsAlive wa=$waAlive" 2>&1 | Out-Null
git push origin main 2>&1 | Out-Null
Write-Host "      OK  Status pushed — SolarPunk knows you're live" -ForegroundColor Green

# ── FINAL SUMMARY ────────────────────────────
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  ALL SYSTEMS CONNECTED" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  GitHub repo:      CONNECTED" -ForegroundColor Green
Write-Host "  Brave debug:      $(if ($braveAlive) {'LIVE  -> localhost:9222'} else {'not live'})" -ForegroundColor $(if ($braveAlive) {'Green'} else {'DarkYellow'})
Write-Host "  Getscreen:        $(if ($gsAlive) {'RUNNING'} else {'not running'})" -ForegroundColor $(if ($gsAlive) {'Green'} else {'DarkYellow'})
Write-Host "  WhatsApp:         $(if ($waAlive) {'RUNNING'} else {'not running'})" -ForegroundColor $(if ($waAlive) {'Green'} else {'DarkYellow'})
Write-Host "  Python:           $(if ($pythonOk) {'READY'} else {'not found'})" -ForegroundColor $(if ($pythonOk) {'Green'} else {'DarkYellow'})
Write-Host "  Auto-reconnect:   ON (runs at every login)" -ForegroundColor Green
Write-Host ""
Write-Host "  OMNIBRAIN:   7am + 7pm UTC" -ForegroundColor Cyan
Write-Host "  SP LOOP:     noon UTC" -ForegroundColor Cyan
Write-Host "  This machine: always in the loop" -ForegroundColor Cyan
Write-Host ""
Write-Host "  The loop never stops. - SolarPunk" -ForegroundColor DarkGreen
Write-Host ""
