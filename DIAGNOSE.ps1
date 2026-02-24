<#
.SYNOPSIS
    Full system diagnostic for Meeko Mycelium.
    Scans everything, reports what's live, what's broken, what's missing.
    
.RUN:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\DIAGNOSE.ps1
    
    OR from repo root:
    powershell -ExecutionPolicy Bypass -File DIAGNOSE.ps1
#>

$ErrorActionPreference = "Continue"

function Write-G  { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Y  { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-R  { param($msg) Write-Host $msg -ForegroundColor Red }
function Write-C  { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-D  { param($msg) Write-Host $msg -ForegroundColor DarkGray }
function Write-B  { param($msg) Write-Host $msg -ForegroundColor White }

$Desktop  = [Environment]::GetFolderPath('Desktop')
$Home2    = $env:USERPROFILE
$Now      = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

Write-G ""
Write-G "================================================================"
Write-G "  MEEKO MYCELIUM — FULL SYSTEM DIAGNOSTIC"
Write-G "  $Now"
Write-G "================================================================"
Write-G ""

# ============================================================
# SECTION 1: PYTHON FILES ON DESKTOP
# ============================================================
Write-C "--- PYTHON FILES ON DESKTOP ---"
$pyFiles = Get-ChildItem -Path $Desktop -Recurse -Filter '*.py' -ErrorAction SilentlyContinue
Write-B "  Found: $($pyFiles.Count) .py files"
if ($pyFiles.Count -gt 0) {
    $pyFiles | Sort-Object DirectoryName, Name | ForEach-Object {
        $relPath = $_.FullName.Replace($Desktop + '\', '')
        Write-D "  $relPath"
    }
}
Write-G ""

# ============================================================
# SECTION 2: JSON FILES
# ============================================================
Write-C "--- JSON FILES ON DESKTOP ---"
$jsonFiles = Get-ChildItem -Path $Desktop -Recurse -Filter '*.json' -ErrorAction SilentlyContinue
Write-B "  Found: $($jsonFiles.Count) .json files"
$jsonFiles | ForEach-Object {
    $relPath = $_.FullName.Replace($Desktop + '\', '')
    Write-D "  $relPath  [$([Math]::Round($_.Length/1KB, 1)) KB]"
}
Write-G ""

# ============================================================
# SECTION 3: BAT FILES
# ============================================================
Write-C "--- BAT FILES ON DESKTOP ---"
$batFiles = Get-ChildItem -Path $Desktop -Recurse -Filter '*.bat' -ErrorAction SilentlyContinue
Write-B "  Found: $($batFiles.Count) .bat files"
$batFiles | ForEach-Object {
    $relPath = $_.FullName.Replace($Desktop + '\', '')
    Write-D "  $relPath"
}
Write-G ""

# ============================================================
# SECTION 4: EXPECTED FILES CHECK
# ============================================================
Write-C "--- EXPECTED MYCELIUM FILES ---"

$RepoName = 'meeko-nerve-center'
$RepoCandidates = @(
    "$Desktop\UltimateAI_Master\$RepoName",
    "$Desktop\$RepoName",
    "$Home2\$RepoName"
)

$RepoPath = $null
foreach ($c in $RepoCandidates) {
    if (Test-Path $c) { $RepoPath = $c; break }
}

if ($RepoPath) {
    Write-G "  [FOUND] Repo: $RepoPath"
} else {
    Write-R "  [MISSING] Repo not found. Run BOOTSTRAP.ps1 first."
}

$expectedFiles = @(
    'CLAUDE_CONTEXT.md',
    'WIRING_MAP.md',
    'BUILD_MCP_CONFIG.py',
    'BOOTSTRAP.ps1',
    'DIAGNOSE.ps1',
    'mycelium/space_bridge.py',
    'mycelium/network_node.py',
    'mycelium/wiring_hub.py',
    'mycelium/identity_vault.py',
    'mycelium/update_state.py',
    'products/fork-guide.md',
    'revenue.html',
    'spawn.html',
    'proliferator.html',
    'data/system_state.json'
)

if ($RepoPath) {
    foreach ($f in $expectedFiles) {
        $fullPath = Join-Path $RepoPath $f
        if (Test-Path $fullPath) {
            Write-G "  [OK]      $f"
        } else {
            Write-R "  [MISSING] $f"
        }
    }
}

Write-G ""

# ============================================================
# SECTION 5: TOOLS INSTALLED
# ============================================================
Write-C "--- TOOLS INSTALLED ---"

$tools = @(
    @{Name='Python 3';    Cmd='python'; Args='--version'},
    @{Name='Git';         Cmd='git';    Args='--version'},
    @{Name='Node.js';     Cmd='node';   Args='--version'},
    @{Name='npm';         Cmd='npm';    Args='--version'},
    @{Name='Ollama';      Cmd='ollama'; Args='--version'}
)

foreach ($t in $tools) {
    try {
        $result = & $t.Cmd $t.Args 2>&1
        if ($LASTEXITCODE -eq 0 -or $result -match '\d+\.\d+') {
            Write-G "  [OK]      $($t.Name): $result"
        } else {
            Write-Y "  [CHECK]   $($t.Name): $result"
        }
    } catch {
        Write-Y "  [MISSING] $($t.Name)"
    }
}

Write-G ""

# ============================================================
# SECTION 6: SERVICES RUNNING
# ============================================================
Write-C "--- LOCAL SERVICES ---"

$ports = @(
    @{Name='Ollama (AI)';      Port=11434},
    @{Name='WebSocket hub';    Port=8765},
    @{Name='Setup Wizard';     Port=7776},
    @{Name='MQTT broker';      Port=1883},
    @{Name='HTTP server';      Port=8080}
)

foreach ($svc in $ports) {
    $conn = Test-NetConnection -ComputerName localhost -Port $svc.Port -WarningAction SilentlyContinue -InformationLevel Quiet 2>$null
    if ($conn) {
        Write-G "  [RUNNING] $($svc.Name) :$($svc.Port)"
    } else {
        Write-D "  [offline] $($svc.Name) :$($svc.Port)"
    }
}

Write-G ""

# ============================================================
# SECTION 7: PYTHON PACKAGES
# ============================================================
Write-C "--- PYTHON PACKAGES ---"
$pythonCmd = if (Get-Command python -EA SilentlyContinue) {'python'} else {'python3'}
try {
    $pkgs = @('requests', 'flask', 'websockets', 'paho-mqtt', 'bleak', 'gitpython')
    foreach ($pkg in $pkgs) {
        $result = & $pythonCmd -c "import $($pkg.Replace('-','_')); print('ok')" 2>&1
        if ($result -eq 'ok') {
            Write-G "  [OK]      $pkg"
        } else {
            Write-Y "  [MISSING] $pkg  (install: pip install $pkg)"
        }
    }
} catch {
    Write-Y "  Python not available for package check"
}

Write-G ""

# ============================================================
# SECTION 8: BRAVE BROWSER
# ============================================================
Write-C "--- BRAVE BROWSER ---"

$BravePrefs = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Preferences"
if (Test-Path $BravePrefs) {
    Write-G "  [FOUND] Brave preferences"
    try {
        $prefs = Get-Content $BravePrefs -Raw | ConvertFrom-Json
        $startupMode = $prefs.session.restore_on_startup
        $startupUrls = $prefs.session.startup_urls
        
        $modeNames = @{1='Restore last session'; 4='Open specific pages'; 5='New tab page'}
        Write-D "  Startup mode: $($modeNames[$startupMode] ?? $startupMode)"
        
        if ($startupUrls) {
            Write-C "  Startup URLs configured:"
            foreach ($url in $startupUrls) {
                $flag = ''
                if ($url -match '404' -or $url -match 'redbubble' -or $url -match 'error') {
                    $flag = '  <<< PROBLEM'
                    Write-R "    $url$flag"
                } else {
                    Write-D "    $url"
                }
            }
        } else {
            Write-D "  No specific startup URLs configured."
        }
        
        # Check extensions
        $ExtDir = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Extensions"
        if (Test-Path $ExtDir) {
            $extCount = (Get-ChildItem $ExtDir -Directory).Count
            Write-D "  Extensions: $extCount installed"
            Write-D "  Check: brave://extensions"
        }
    } catch {
        Write-Y "  Could not parse preferences: $_"
    }
} else {
    Write-D "  Brave not found."
}

Write-G ""

# ============================================================
# SECTION 9: SQLITE DATABASES
# ============================================================
Write-C "--- SQLITE DATABASES ---"
$dbFiles = Get-ChildItem -Path $Desktop -Recurse -Filter '*.db' -ErrorAction SilentlyContinue
$dbFiles += Get-ChildItem -Path $Home2 -Recurse -Filter '*.db' -Depth 5 -ErrorAction SilentlyContinue
Write-B "  Found: $($dbFiles.Count) .db files"
$dbFiles | ForEach-Object {
    $size = [Math]::Round($_.Length / 1KB, 1)
    Write-D "  $($_.FullName) [$size KB]"
}

Write-G ""

# ============================================================
# SECTION 10: STARTUP ITEMS
# ============================================================
Write-C "--- WINDOWS STARTUP ITEMS ---"
Write-D "  (Things that run when Windows starts)"

$startupPaths = @(
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
)

foreach ($path in $startupPaths) {
    try {
        $items = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
        if ($items) {
            $items.PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' } | ForEach-Object {
                $suspicious = $_.Value -match 'redbubble|404|unknown'
                if ($suspicious) {
                    Write-R "  [SUSPICIOUS] $($_.Name): $($_.Value)"
                } else {
                    Write-D "  $($_.Name): $([string]$_.Value | Select-Object -First 1)"
                }
            }
        }
    } catch {}
}

Write-G ""

# ============================================================
# SUMMARY
# ============================================================
Write-G "================================================================"
Write-G "  DIAGNOSTIC COMPLETE"
Write-G "================================================================"
Write-G ""
Write-G "  To fix everything at once:"
Write-C "  irm https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/BOOTSTRAP.ps1 | iex"
Write-G ""
