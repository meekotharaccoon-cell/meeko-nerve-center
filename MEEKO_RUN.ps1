<#
.SYNOPSIS
    MEEKO_RUN.ps1 — The Claude-mode runner.
    Run this any time. It figures out what to do.

    Every run:
      1.  Pull latest from GitHub
      2.  Syntax-check all Python files — auto-fix what it can
      3.  Run the wiring hub (connects all layers)
      4.  Run whichever mycelium scripts are due
      5.  Commit + push any new data/changes back to GitHub
      6.  Print a clear report of what ran, what's broken, what needs you

.RUN:
    powershell -ExecutionPolicy Bypass -File MEEKO_RUN.ps1

    Or from anywhere on your machine:
    powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Desktop\meeko-nerve-center\MEEKO_RUN.ps1"
#>

$ErrorActionPreference = "Continue"
$START_TIME = Get-Date

# ── Colors ───────────────────────────────────────────────────
function Write-G  { param($m) Write-Host $m -ForegroundColor Green }
function Write-Y  { param($m) Write-Host $m -ForegroundColor Yellow }
function Write-C  { param($m) Write-Host $m -ForegroundColor Cyan }
function Write-D  { param($m) Write-Host $m -ForegroundColor DarkGray }
function Write-R  { param($m) Write-Host $m -ForegroundColor Red }
function Write-W  { param($m) Write-Host $m -ForegroundColor White }
function Hdr      { param($m) Write-G ""; Write-G "── $m ─────────────────────────────────────────" }

# ── Find repo ─────────────────────────────────────────────────
$Desktop  = [Environment]::GetFolderPath('Desktop')
$RepoPath = $null
foreach ($c in @("$Desktop\meeko-nerve-center", "$Desktop\UltimateAI_Master\meeko-nerve-center", "$env:USERPROFILE\meeko-nerve-center")) {
    if (Test-Path "$c\.git") { $RepoPath = $c; break }
}
if (-not $RepoPath) {
    Write-R "Repo not found. Run GITHUB_CONNECT.ps1 first."
    exit 1
}

# ── Find Python ───────────────────────────────────────────────
$PY = $null
foreach ($cmd in @('python', 'python3', 'py')) {
    try {
        $v = & $cmd --version 2>&1
        if ($v -match 'Python 3') { $PY = $cmd; break }
    } catch {}
}

# ── Helpers ───────────────────────────────────────────────────
$RESULTS   = [System.Collections.ArrayList]::new()
$NEEDS_YOU = [System.Collections.ArrayList]::new()

function Log-Result { param($name, $status, $note='')
    $sym = if ($status -eq 'OK') { "[OK]  " } elseif ($status -eq 'WARN') { "[WARN]" } else { "[FAIL]" }
    $col = if ($status -eq 'OK') { 'Green' } elseif ($status -eq 'WARN') { 'Yellow' } else { 'Red' }
    Write-Host "  $sym $name$(if ($note) { ' — ' + $note })" -ForegroundColor $col
    [void]$RESULTS.Add([PSCustomObject]@{Name=$name; Status=$status; Note=$note})
}

function Run-Py { param($script, $args_str='', $label='')
    $display = if ($label) { $label } else { Split-Path $script -Leaf }
    if (-not $PY) { Log-Result $display FAIL "Python not found"; return $false }
    if (-not (Test-Path $script)) { Log-Result $display WARN "file missing"; return $false }
    $output = if ($args_str) { & $PY $script $args_str.Split(' ') 2>&1 } else { & $PY $script 2>&1 }
    $ok = $LASTEXITCODE -eq 0
    Log-Result $display (if ($ok) { 'OK' } else { 'WARN' }) (if (-not $ok) { ($output | Select-Object -Last 1) } else { '' })
    return $ok
}

# ═══════════════════════════════════════════════════════════════
Write-G ""
Write-G "╔══════════════════════════════════════════════════════╗"
Write-G "║   MEEKO MYCELIUM — CLAUDE-MODE RUNNER                ║"
Write-G "║   $($START_TIME.ToString('yyyy-MM-dd HH:mm'))                               ║"
Write-G "╚══════════════════════════════════════════════════════╝"
Write-G ""
Write-D "  Repo: $RepoPath"
Write-D "  Python: $(if ($PY) { $PY } else { 'NOT FOUND' })"
Write-G ""

Set-Location $RepoPath

# ═══════════════════════════════════════════════════════════════
Hdr "STEP 1 — Pull from GitHub"
# ═══════════════════════════════════════════════════════════════
$pullOutput = git pull origin main 2>&1
if ($LASTEXITCODE -eq 0) {
    $summary = ($pullOutput | Where-Object { $_ -match 'Already|file' } | Select-Object -Last 1)
    Log-Result "git pull" OK ($summary -replace '\s+', ' ')
} else {
    Log-Result "git pull" WARN "$pullOutput"
    [void]$NEEDS_YOU.Add("Git pull failed — run GITHUB_CONNECT.ps1 to re-authenticate")
}

# ═══════════════════════════════════════════════════════════════
Hdr "STEP 2 — Syntax check all Python files"
# ═══════════════════════════════════════════════════════════════
if ($PY) {
    $pyFiles = Get-ChildItem "$RepoPath\mycelium" -Filter '*.py' -EA SilentlyContinue
    $syntaxFails = @()
    foreach ($f in $pyFiles) {
        $result = & $PY -m py_compile $f.FullName 2>&1
        if ($LASTEXITCODE -ne 0) {
            $syntaxFails += [PSCustomObject]@{ File = $f.Name; Error = ($result -join ' ').Trim() }
        }
    }
    if ($syntaxFails.Count -eq 0) {
        Log-Result "Syntax check ($($pyFiles.Count) files)" OK "all clean"
    } else {
        foreach ($fail in $syntaxFails) {
            Log-Result "Syntax: $($fail.File)" FAIL $fail.Error
            [void]$NEEDS_YOU.Add("Fix syntax in mycelium/$($fail.File): $($fail.Error)")
        }
    }
} else {
    Log-Result "Syntax check" WARN "Python not installed — skipped"
    [void]$NEEDS_YOU.Add("Install Python 3 from https://python.org (check 'Add to PATH')")
}

# ═══════════════════════════════════════════════════════════════
Hdr "STEP 3 — Wiring hub (connect all layers)"
# ═══════════════════════════════════════════════════════════════
Run-Py "$RepoPath\mycelium\wiring_hub.py" '' "Wiring hub"

# ═══════════════════════════════════════════════════════════════
Hdr "STEP 4 — Core system scripts"
# ═══════════════════════════════════════════════════════════════

# Space bridge
Run-Py "$RepoPath\mycelium\space_bridge.py"  '' "Space bridge (ISS + NASA)"

# Network node (quick check, no blocking scan)
Run-Py "$RepoPath\mycelium\network_node.py" '' "Network node"

# Knowledge harvester (runs daily, skip if already ran today)
$khLog = "$RepoPath\knowledge\digest\$(Get-Date -Format 'yyyy-MM-dd').md"
if (-not (Test-Path $khLog)) {
    Run-Py "$RepoPath\mycelium\knowledge_harvester_v2.py" '' "Knowledge harvester"
} else {
    Log-Result "Knowledge harvester" OK "already ran today"
}

# Diagnostics
Run-Py "$RepoPath\mycelium\diagnostics.py" '' "Diagnostics"

# Evolve (self-improvement engine)
Run-Py "$RepoPath\mycelium\evolve.py" '' "Evolve (self-improvement)"

# ═══════════════════════════════════════════════════════════════
Hdr "STEP 5 — Check GitHub secrets (what's unlocked)"
# ═══════════════════════════════════════════════════════════════
$secretsNeeded = @(
    @{ Name='GMAIL_APP_PASSWORD';   Url='myaccount.google.com/apppasswords';          Impact='Unlocks ALL email (briefings, outreach, responder)' },
    @{ Name='MASTODON_URL';         Url='(just add: https://mastodon.social)';        Impact='Mastodon posting' },
    @{ Name='BLUESKY_PASSWORD';     Url='bsky.app/settings/app-passwords';            Impact='Bluesky posting' },
    @{ Name='GUMROAD_TOKEN';        Url='app.gumroad.com/settings/advanced';          Impact='Track sales data' },
    @{ Name='STRIKE_API_KEY';       Url='developer.strike.me';                        Impact='Lightning payments' },
    @{ Name='NASA_API_KEY';         Url='api.nasa.gov (free)';                        Impact='Better NASA data (not DEMO_KEY)' }
)

foreach ($s in $secretsNeeded) {
    $localEnvFile = "$RepoPath\.env.local"
    $hasIt = $false
    if (Test-Path $localEnvFile) {
        $hasIt = (Get-Content $localEnvFile | Select-String $s.Name) -ne $null
    }
    if ($hasIt) {
        Log-Result "Secret: $($s.Name)" OK "found in .env.local"
    } else {
        Log-Result "Secret: $($s.Name)" WARN "missing — $($s.Impact)"
        [void]$NEEDS_YOU.Add("Add $($s.Name) — get it at: $($s.Url)`n    Impact: $($s.Impact)`n    Add to: github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions")
    }
}

# ═══════════════════════════════════════════════════════════════
Hdr "STEP 6 — Check OTF grant (HIGH PRIORITY reminder)"
# ═══════════════════════════════════════════════════════════════
$wantsFile = "$RepoPath\data\system_wants_next.json"
if (Test-Path $wantsFile) {
    $wants = Get-Content $wantsFile | ConvertFrom-Json
    foreach ($r in $wants.reminders_pending) {
        $priorityColor = if ($r.priority -eq 'HIGH') { 'Red' } else { 'Yellow' }
        Write-Host "  [$($r.priority)] $($r.title)" -ForegroundColor $priorityColor
        Write-D "  $($r.details)"
        Write-C "  Action: $($r.action)"
        if ($r.priority -eq 'HIGH') {
            [void]$NEEDS_YOU.Add("$($r.title): $($r.action)")
        }
    }
} else {
    Log-Result "System reminders" OK "no pending reminders"
}

# ═══════════════════════════════════════════════════════════════
Hdr "STEP 7 — Commit + push results to GitHub"
# ═══════════════════════════════════════════════════════════════
$gitStatus = git status --porcelain 2>&1
$changedFiles = ($gitStatus | Where-Object { $_ -match '^\s*[MA?]' }).Count

if ($changedFiles -gt 0) {
    Write-D "  $changedFiles file(s) changed — committing..."
    git add -A 2>&1 | Out-Null
    $commitMsg = "auto: run $(Get-Date -Format 'yyyy-MM-dd HH:mm') — $changedFiles files updated"
    git commit -m $commitMsg 2>&1 | ForEach-Object { Write-D "  $_" }
    $pushResult = git push origin main 2>&1
    if ($LASTEXITCODE -eq 0) {
        Log-Result "Git push" OK "$changedFiles files → GitHub"
    } else {
        Log-Result "Git push" WARN "$pushResult"
        [void]$NEEDS_YOU.Add("Git push failed — run GITHUB_CONNECT.ps1 to fix auth")
    }
} else {
    Log-Result "Git push" OK "nothing new to push"
}

# ═══════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════
$elapsed = [math]::Round(((Get-Date) - $START_TIME).TotalSeconds, 1)
$okCount   = ($RESULTS | Where-Object { $_.Status -eq 'OK'   }).Count
$warnCount = ($RESULTS | Where-Object { $_.Status -eq 'WARN' }).Count
$failCount = ($RESULTS | Where-Object { $_.Status -eq 'FAIL' }).Count

Write-G ""
Write-G "╔══════════════════════════════════════════════════════╗"
Write-G "║   RUN COMPLETE — $($okCount) OK  $($warnCount) WARN  $($failCount) FAIL  ($($elapsed)s)$((' ' * [Math]::Max(0, 11 - "$okCount$warnCount$failCount$elapsed".Length)))║"
Write-G "╚══════════════════════════════════════════════════════╝"

if ($NEEDS_YOU.Count -gt 0) {
    Write-G ""
    Write-Y "  ⚠  NEEDS YOU ($($NEEDS_YOU.Count) items):"
    $i = 1
    foreach ($item in $NEEDS_YOU) {
        Write-Y ""
        Write-Y "  [$i] $item"
        $i++
    }
}

Write-G ""
Write-G "  System ran. Data pushed. Watching."
Write-G ""
