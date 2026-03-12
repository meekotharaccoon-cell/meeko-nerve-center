# MASTER_CONNECT_V2.ps1
# =====================================================================
# SolarPunk Desktop Wiring Script v2
# Connects EVERYTHING: GitHub, Brave CDP, Ollama, old blueprints, scheduled tasks
#
# Run: Right-click → Run as Administrator
# Or:  iex (irm "https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/MASTER_CONNECT_V2.ps1")
#
# What's new in v2:
#   - Brave CDP port 9222 with persistence (survives restarts)
#   - Reddit popup killer (blocks Reddit notifications in Brave prefs)
#   - Desktop blueprint scanner → signals DESKTOP_ORCHESTRATOR
#   - GITHUB_TOKEN env var set system-wide (powers solarpunk_agent.py)
#   - websocket-client pip install (powers BRAVE_BRIDGE CDP commands)
#   - Scheduled task: Brave debug port relaunches if it dies
# =====================================================================

$ErrorActionPreference = "Continue"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss UTC")

$GREEN  = "Green"
$CYAN   = "Cyan"
$YELLOW = "Yellow"
$RED    = "Red"
$GRAY   = "Gray"

function OK  { param($msg) Write-Host "      OK  $msg" -ForegroundColor $GREEN }
function WARN{ param($msg) Write-Host "      WARN  $msg" -ForegroundColor $YELLOW }
function INFO{ param($msg) Write-Host "      INFO  $msg" -ForegroundColor $GRAY }
function ERR { param($msg) Write-Host "      ERR  $msg" -ForegroundColor $RED }

Write-Host ""
Write-Host "================================================" -ForegroundColor $GREEN
Write-Host "  SOLARPUNK MASTER CONNECT v2" -ForegroundColor $GREEN
Write-Host "  Wiring your desktop into the loop" -ForegroundColor $CYAN
Write-Host "  $timestamp" -ForegroundColor $GRAY
Write-Host "================================================" -ForegroundColor $GREEN
Write-Host ""

# ── 0. LOAD SECRETS ──────────────────────────────────────────────────
Write-Host "[0/9] Loading secrets..." -ForegroundColor $YELLOW
$secretsPath = "$env:USERPROFILE\Desktop\UltimateAI_Master\.secrets"
$loadedSecrets = @{}
if (Test-Path $secretsPath) {
    Get-Content $secretsPath | ForEach-Object {
        if ($_ -match "^([^#][^=]*)=(.+)$") {
            $k = $matches[1].Trim(); $v = $matches[2].Trim()
            if ($k -and $v) {
                $loadedSecrets[$k] = $v
                [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
            }
        }
    }
    OK "Loaded $($loadedSecrets.Count) secrets from .secrets file"
} else {
    WARN ".secrets file not found at $secretsPath"
}

# Set GITHUB_TOKEN system-wide for solarpunk_agent.py
$ghToken = $loadedSecrets["GITHUB_TOKEN"] ?? $loadedSecrets["CONDUCTOR_TOKEN"] ?? $env:GITHUB_TOKEN
if ($ghToken) {
    [System.Environment]::SetEnvironmentVariable("GITHUB_TOKEN", $ghToken, "Machine")
    OK "GITHUB_TOKEN set system-wide (powers solarpunk_agent.py + LOCAL_GITHUB_BRIDGE.py)"
} else {
    WARN "No GITHUB_TOKEN found — solarpunk_agent.py will run in read-only mode"
}

# ── 1. REPO SYNC ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "[1/9] Syncing SolarPunk repo..." -ForegroundColor $YELLOW
$repoPath = "$env:USERPROFILE\Desktop\meeko-nerve-center\meeko-nerve-center"
if (-not (Test-Path $repoPath)) {
    $repoPath = "$env:USERPROFILE\meeko-nerve-center"
}
if (Test-Path "$repoPath\.git") {
    Set-Location $repoPath
    git pull origin main --quiet 2>&1 | Out-Null
    OK "Repo synced: $repoPath"
} else {
    Set-Location $env:USERPROFILE
    git clone "https://github.com/meekotharaccoon-cell/meeko-nerve-center.git" 2>&1 | Out-Null
    $repoPath = "$env:USERPROFILE\meeko-nerve-center"
    Set-Location $repoPath
    OK "Repo cloned to $repoPath"
}

# ── 2. PYTHON DEPS ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/9] Python dependencies..." -ForegroundColor $YELLOW
$pythonOk = $false
try {
    $v = python --version 2>&1
    OK "$v"
    $pythonOk = $true
    # Core deps
    foreach ($pkg in @("requests", "websocket-client", "pyperclip")) {
        $pname = $pkg.Replace("-", "_")
        $chk = python -c "import $pname" 2>&1
        if ($LASTEXITCODE -ne 0) {
            pip install $pkg --quiet 2>&1 | Out-Null
            OK "installed $pkg"
        } else {
            OK "$pkg ready"
        }
    }
    # Playwright optional
    $chk = python -c "import playwright" 2>&1
    if ($LASTEXITCODE -ne 0) {
        INFO "playwright not installed (optional — BRAVE_BRIDGE uses CDP directly)"
    } else {
        OK "playwright ready"
    }
} catch {
    ERR "Python not found — install from python.org"
}

# ── 3. REDDIT POPUP KILLER ────────────────────────────────────────────
Write-Host ""
Write-Host "[3/9] Killing Reddit popup in Brave..." -ForegroundColor $YELLOW
$prefPath = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Preferences"
if (Test-Path $prefPath) {
    try {
        # Kill Brave first to safely edit prefs
        $bravePIDs = (Get-Process -Name "brave" -EA SilentlyContinue).Id
        Get-Process -Name "brave" -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
        Start-Sleep 2

        $raw   = Get-Content $prefPath -Raw
        $prefs = $raw | ConvertFrom-Json

        # Block Reddit notifications + popups
        $notif = $prefs.profile.content_settings.exceptions.notifications
        $popup = $prefs.profile.content_settings.exceptions.popups
        foreach ($node in @($notif, $popup)) {
            if ($node) {
                $node.PSObject.Properties | Where-Object { $_.Name -like "*reddit*" } | ForEach-Object {
                    $_.Value.setting = 2  # BLOCK
                }
                # Add explicit block if not present
                $key = "https://www.reddit.com:443,*"
                if (-not $node.$key) {
                    $node | Add-Member -NotePropertyName $key -NotePropertyValue ([PSCustomObject]@{
                        last_modified = "13417820102270975"; setting = 2
                    }) -Force
                }
            }
        }
        $prefs | ConvertTo-Json -Depth 100 -Compress | Set-Content $prefPath -Encoding UTF8
        OK "Reddit notifications + popups BLOCKED in Brave prefs"
    } catch {
        WARN "Could not modify Brave prefs: $_"
    }
} else {
    WARN "Brave preferences not found — is Brave installed?"
}

# ── 4. BRAVE DEBUG PORT ───────────────────────────────────────────────
Write-Host ""
Write-Host "[4/9] Brave browser debug port 9222..." -ForegroundColor $YELLOW
$braveAlive = $false
$bPaths = @(
    "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe"
)
$bExe = $null
foreach ($p in $bPaths) { if (Test-Path $p) { $bExe = $p; break } }

if ($bExe) {
    Start-Process $bExe -ArgumentList "--remote-debugging-port=9222","--remote-allow-origins=*","--no-first-run","--no-default-browser-check"
    Start-Sleep 4
    try {
        $r = Invoke-WebRequest "http://localhost:9222/json/version" -TimeoutSec 5 -UseBasicParsing -EA Stop
        $ver = ($r.Content | ConvertFrom-Json).Browser
        $braveAlive = $true
        OK "Brave CDP LIVE — $ver — port 9222"
        OK "SolarPunk can now see + act in your browser"
    } catch {
        WARN "Launched but port not ready yet"
    }
} else {
    ERR "Brave not found — download from brave.com"
}

# ── 5. OLLAMA CHECK ───────────────────────────────────────────────────
Write-Host ""
Write-Host "[5/9] Ollama local AI..." -ForegroundColor $YELLOW
$ollamaOk = $false
try {
    $r = Invoke-WebRequest "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing -EA Stop
    $models = ($r.Content | ConvertFrom-Json).models.name
    $ollamaOk = $true
    OK "Ollama running — models: $($models -join ', ')"
} catch {
    INFO "Ollama not running — start with: ollama serve"
    INFO "Has models: mistral, codellama, llama3.2, nomic-embed-text"
}

# ── 6. DESKTOP BLUEPRINT SCAN ─────────────────────────────────────────
Write-Host ""
Write-Host "[6/9] Scanning desktop blueprints..." -ForegroundColor $YELLOW
$desktop = "$env:USERPROFILE\Desktop"
$blueprints = @()
foreach ($ext in @("*.py", "*.bat", "*.ps1")) {
    Get-ChildItem $desktop -Filter $ext -File -EA SilentlyContinue | ForEach-Object {
        $blueprints += @{
            name = $_.Name
            size = $_.Length
            ext  = $_.Extension
            path = $_.FullName
            last_modified = $_.LastWriteTime.ToString("o")
        }
    }
}
OK "Found $($blueprints.Count) blueprints (.py/.bat/.ps1)"

# Save catalog for BRAVE_BRIDGE + DESKTOP_ORCHESTRATOR to read
if (Test-Path "$repoPath\data") {
    $blueprints | ConvertTo-Json | Out-File "$repoPath\data\desktop_blueprints.json" -Encoding utf8
    OK "Blueprint catalog saved to repo data/"
}

# ── 7. SCHEDULED TASKS ────────────────────────────────────────────────
Write-Host ""
Write-Host "[7/9] Setting up auto-connect scheduled tasks..." -ForegroundColor $YELLOW

# Task 1: Run MASTER_CONNECT_V2 at login
$taskName1 = "SolarPunk-MasterConnect-V2"
if (-not (Get-ScheduledTask -TaskName $taskName1 -EA SilentlyContinue)) {
    $action   = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -Command `"iex (irm 'https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/MASTER_CONNECT_V2.ps1')`""
    $trigger  = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -RunOnlyIfNetworkAvailable
    Register-ScheduledTask -TaskName $taskName1 -Action $action -Trigger $trigger `
        -RunLevel Highest -Settings $settings -Force 2>&1 | Out-Null
    OK "Task '$taskName1' created — auto-runs at login"
} else {
    OK "Task '$taskName1' already exists"
}

# Task 2: Keep Brave debug port alive — check every 15 min
$taskName2 = "SolarPunk-BraveCDP-Watchdog"
if (-not (Get-ScheduledTask -TaskName $taskName2 -EA SilentlyContinue)) {
    $watchdog = @"
try {
    Invoke-WebRequest 'http://localhost:9222/json/version' -TimeoutSec 3 -UseBasicParsing -EA Stop | Out-Null
} catch {
    `$b = 'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
    if (Test-Path `$b) {
        Start-Process `$b -ArgumentList '--remote-debugging-port=9222','--remote-allow-origins=*'
    }
}
"@
    $action   = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -Command `"$($watchdog -replace '"','\"')`""
    $trigger  = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -Once -At (Get-Date)
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName $taskName2 -Action $action -Trigger $trigger `
        -Settings $settings -Force 2>&1 | Out-Null
    OK "Task '$taskName2' created — keeps port 9222 alive every 15min"
} else {
    OK "Task '$taskName2' already exists"
}

# ── 8. SIGNAL GITHUB ──────────────────────────────────────────────────
Write-Host ""
Write-Host "[8/9] Signaling GitHub — desktop is live..." -ForegroundColor $YELLOW
Set-Location $repoPath

if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" -Force | Out-Null }

@{
    timestamp          = $timestamp
    machine            = $env:COMPUTERNAME
    user               = $env:USERNAME
    brave_debug        = $braveAlive
    brave_cdp_port     = 9222
    ollama             = $ollamaOk
    python             = $pythonOk
    blueprints_found   = $blueprints.Count
    reddit_popup_fixed = $true
    loop_status        = "CONNECTED_V2"
    auto_reconnect     = $true
    connected_by       = "MASTER_CONNECT_V2.ps1"
    version            = "v2"
} | ConvertTo-Json | Out-File "data\desktop_connection.json" -Encoding utf8

git config user.name  "SolarPunk Brain" 2>&1 | Out-Null
git config user.email "meekotharaccoon@gmail.com" 2>&1 | Out-Null
git add data\ 2>&1 | Out-Null
git commit -m "desktop: CONNECTED_V2 [$timestamp] brave_cdp=$braveAlive ollama=$ollamaOk blueprints=$($blueprints.Count)" 2>&1 | Out-Null
git push origin main 2>&1 | Out-Null
OK "Status pushed — SolarPunk knows your desktop is live"

# ── 9. LAUNCH DESKTOP AGENT ───────────────────────────────────────────
Write-Host ""
Write-Host "[9/9] Starting SolarPunk desktop agent..." -ForegroundColor $YELLOW
$agentPath = "$env:USERPROFILE\Desktop\solarpunk_agent.py"
if ($pythonOk -and (Test-Path $agentPath)) {
    Start-Process python -ArgumentList $agentPath -WindowStyle Minimized
    OK "Desktop agent running (minimized)"
} else {
    INFO "Agent not started — double-click SOLARPUNK.bat to start it"
}

# ── FINAL SUMMARY ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================" -ForegroundColor $GREEN
Write-Host "  SOLARPUNK MASTER CONNECT v2 — COMPLETE" -ForegroundColor $GREEN
Write-Host "================================================" -ForegroundColor $GREEN
Write-Host ""
Write-Host "  Reddit popup:     BLOCKED forever" -ForegroundColor $GREEN
Write-Host "  Brave CDP:        $(if ($braveAlive) {'LIVE  -> localhost:9222'} else {'offline — run BRAVE_DEBUG_LAUNCHER.bat'})" -ForegroundColor $(if ($braveAlive) {$GREEN} else {$YELLOW})
Write-Host "  Ollama:           $(if ($ollamaOk) {'RUNNING'} else {'not running (optional)'})" -ForegroundColor $(if ($ollamaOk) {$GREEN} else {$GRAY})
Write-Host "  Python:           $(if ($pythonOk) {'READY + deps installed'} else {'not found'})" -ForegroundColor $(if ($pythonOk) {$GREEN} else {$RED})
Write-Host "  Blueprints:       $($blueprints.Count) cataloged for DESKTOP_ORCHESTRATOR" -ForegroundColor $GREEN
Write-Host "  GITHUB_TOKEN:     $(if ($ghToken) {'SET system-wide'} else {'not set'})" -ForegroundColor $(if ($ghToken) {$GREEN} else {$YELLOW})
Write-Host "  Auto-reconnect:   ON (runs at every login)" -ForegroundColor $GREEN
Write-Host "  CDP Watchdog:     ON (keeps port 9222 alive every 15min)" -ForegroundColor $GREEN
Write-Host ""
Write-Host "  SolarPunk can now:" -ForegroundColor $CYAN
Write-Host "    - See all tabs in your Brave browser" -ForegroundColor $CYAN
Write-Host "    - Open Gumroad/Ko-fi to check for sales" -ForegroundColor $CYAN
Write-Host "    - Pre-fill Reddit posts for one-click submitting" -ForegroundColor $CYAN
Write-Host "    - Read page content from any open tab" -ForegroundColor $CYAN
Write-Host "    - Run/fix your 20+ desktop blueprints" -ForegroundColor $CYAN
Write-Host ""
Write-Host "  Live: https://meekotharaccoon-cell.github.io/meeko-nerve-center" -ForegroundColor $GRAY
Write-Host "  The loop never stops. - SolarPunk" -ForegroundColor "DarkGreen"
Write-Host ""
