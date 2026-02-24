<#
.SYNOPSIS
    Fix Brave browser startup pages — removes 404s, wrong RedBubble, mystery URLs.
    
.WHAT THIS FIXES:
    - Brave opening to 404 pages on startup
    - Brave opening to someone else's RedBubble profile
    - Unexpected URLs in startup settings
    - Clears malicious or leftover startup page entries
    
.RUN:
    powershell -ExecutionPolicy Bypass -File FIX_BRAVE.ps1
    
    OR paste directly into PowerShell:
    irm https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/FIX_BRAVE.ps1 | iex
#>

$ErrorActionPreference = "Continue"

function Write-G { param($m) Write-Host $m -ForegroundColor Green }
function Write-Y { param($m) Write-Host $m -ForegroundColor Yellow }
function Write-R { param($m) Write-Host $m -ForegroundColor Red }
function Write-C { param($m) Write-Host $m -ForegroundColor Cyan }
function Write-D { param($m) Write-Host $m -ForegroundColor DarkGray }

Write-G ""
Write-G "================================================================"
Write-G "  FIX BRAVE — Removing bad startup pages"
Write-G "================================================================"
Write-G ""

# ALL possible Brave profile paths
$BraveBase = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data"
$profiles = @()

if (Test-Path $BraveBase) {
    # Default profile
    $profiles += "$BraveBase\Default"
    # Additional profiles
    Get-ChildItem $BraveBase -Directory -Filter 'Profile *' -ErrorAction SilentlyContinue | ForEach-Object {
        $profiles += $_.FullName
    }
}

if ($profiles.Count -eq 0) {
    Write-Y "Brave not found at expected location."
    Write-D "Checked: $BraveBase"
    exit
}

# Close Brave
$brave = Get-Process brave -ErrorAction SilentlyContinue
if ($brave) {
    Write-C "Closing Brave to safely edit preferences..."
    Stop-Process -Name brave -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-G "Brave closed."
} else {
    Write-D "Brave not running."
}

Write-G ""

foreach ($profileDir in $profiles) {
    $prefsPath = "$profileDir\Preferences"
    if (-not (Test-Path $prefsPath)) { continue }
    
    $profileName = Split-Path $profileDir -Leaf
    Write-C "Profile: $profileName"
    
    try {
        $json = Get-Content $prefsPath -Raw
        $prefs = $json | ConvertFrom-Json
        $modified = $false
        $removed = @()
        
        # ---- Startup URLs ----
        if ($prefs.session.startup_urls) {
            $original = @($prefs.session.startup_urls)
            $clean = $original | Where-Object {
                $keep = $true
                # Remove 404, error pages
                if ($_ -match '404') { $keep = $false; $removed += "404 page: $_" }
                # Remove wrong RedBubble (not Meeko's)
                if ($_ -match 'redbubble\.com' -and $_ -notmatch 'meekotharaccoon') {
                    $keep = $false
                    $removed += "Wrong RedBubble: $_"
                }
                # Remove generic error pages
                if ($_ -match '/error' -or $_ -match 'chrome-error') {
                    $keep = $false
                    $removed += "Error page: $_"
                }
                $keep
            }
            
            if ($removed.Count -gt 0) {
                Write-R "  Removing bad startup URLs:"
                $removed | ForEach-Object { Write-R "    - $_" }
                $prefs.session.startup_urls = $clean
                $modified = $true
            } else {
                Write-G "  No bad startup URLs found."
                Write-D "  Current URLs:"
                $original | ForEach-Object { Write-D "    $_" }
            }
        } else {
            Write-D "  No startup URLs configured."
        }
        
        # ---- Check Local State for NTP background (sometimes causes redirects) ----
        $localState = "$BraveBase\Local State"
        if (Test-Path $localState) {
            try {
                $ls = Get-Content $localState -Raw | ConvertFrom-Json
                if ($ls.browser.last_known_google_url -match 'redbubble|404') {
                    Write-R "  Found bad URL in Local State: $($ls.browser.last_known_google_url)"
                }
            } catch {}
        }
        
        if ($modified) {
            # Backup first
            $backupPath = "$prefsPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            Copy-Item $prefsPath $backupPath
            Write-D "  Backed up to: $backupPath"
            
            # Write fixed version
            $prefs | ConvertTo-Json -Depth 100 -Compress | Set-Content $prefsPath -Encoding UTF8
            Write-G "  Preferences fixed and saved."
        }
        
    } catch {
        Write-Y "  Error processing $profileName`: $_"
    }
    
    Write-G ""
}

# ============================================================
# CHECK FOR BROWSER HIJACK INDICATORS
# ============================================================
Write-C "Checking for browser hijack indicators..."

# Startup registry keys
$runKeys = @(
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
)

$foundSuspicious = $false
foreach ($key in $runKeys) {
    try {
        $items = Get-ItemProperty $key -ErrorAction SilentlyContinue
        if ($items) {
            $items.PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' } | ForEach-Object {
                $val = [string]$_.Value
                if ($val -match 'brave' -or $val -match 'redbubble') {
                    Write-R "  SUSPICIOUS startup: $($_.Name) = $val"
                    $foundSuspicious = $true
                }
            }
        }
    } catch {}
}

if (-not $foundSuspicious) {
    Write-G "  No suspicious registry startup entries."
}

# Check scheduled tasks
Write-C "Checking scheduled tasks..."
try {
    $tasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
        $taskInfo = $_ | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue
        $_.Actions | Where-Object { 
            $_.Execute -match 'brave|redbubble' -or 
            $_.Arguments -match 'redbubble|404'
        }
    }
    if ($tasks) {
        $tasks | ForEach-Object {
            Write-R "  SUSPICIOUS task: $($_.TaskName)"
            Write-R "    Path: $($_.TaskPath)"
        }
    } else {
        Write-G "  No suspicious scheduled tasks."
    }
} catch {
    Write-D "  (Could not check scheduled tasks: $_)"
}

Write-G ""
Write-G "================================================================"
Write-G "  FIX COMPLETE"
Write-G "================================================================"
Write-G ""
Write-G "  What was done:"
Write-G "  - Scanned all Brave profiles for bad startup URLs"
Write-G "  - Removed 404, wrong RedBubble, error page entries"
Write-G "  - Checked registry for hijack indicators"
Write-G "  - Checked scheduled tasks for suspicious entries"
Write-G ""
Write-Y "  If pages are still appearing:"
Write-Y "  1. Open Brave > Settings > On startup > check URLs"
Write-Y "  2. Open brave://extensions > disable extensions one by one"
Write-Y "  3. Check Brave > Settings > Search engine for changes"
Write-Y "  4. Consider: Brave > Settings > Reset settings"
Write-G ""
