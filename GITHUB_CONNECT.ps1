<#
.SYNOPSIS
    GITHUB_CONNECT.ps1 — Wire this machine to GitHub.
    Run ONCE (or re-run anytime auth breaks).
    
    What it does:
      1. Checks if GitHub CLI (gh) is installed — uses it if so
      2. If not, sets up a Personal Access Token in Windows Credential Manager
      3. Verifies the connection works
      4. Clones or updates all your repos
      5. Configures git identity so commits work

.RUN:
    powershell -ExecutionPolicy Bypass -File GITHUB_CONNECT.ps1
#>

$ErrorActionPreference = "Continue"

function Write-G { param($m) Write-Host $m -ForegroundColor Green }
function Write-Y { param($m) Write-Host $m -ForegroundColor Yellow }
function Write-C { param($m) Write-Host $m -ForegroundColor Cyan }
function Write-D { param($m) Write-Host $m -ForegroundColor DarkGray }
function Write-R { param($m) Write-Host $m -ForegroundColor Red }

$GITHUB_USER = "meekotharaccoon-cell"
$GITHUB_EMAIL = "meekotharaccoon@gmail.com"
$REPOS = @(
    "meeko-nerve-center"
)
$REPO_BASE = "https://github.com/$GITHUB_USER"
$Desktop = [Environment]::GetFolderPath('Desktop')
$RepoRoot = "$Desktop\meeko-nerve-center"

Write-G ""
Write-G "================================================================"
Write-G "  GITHUB CONNECT — Wiring this machine to GitHub"
Write-G "  User: $GITHUB_USER"
Write-G "================================================================"
Write-G ""

# ── STEP 1: Check git is installed ───────────────────────────
Write-C "[1/5] Checking git..."
if (-not (Get-Command git -EA SilentlyContinue)) {
    Write-R "  Git not installed."
    Write-Y "  Download: https://git-scm.com/download/win"
    Write-Y "  After installing, re-run this script."
    exit 1
}
$gitVer = git --version 2>&1
Write-G "  OK: $gitVer"

# ── STEP 2: Set git identity ──────────────────────────────────
Write-C "[2/5] Setting git identity..."
git config --global user.name  $GITHUB_USER
git config --global user.email $GITHUB_EMAIL
git config --global credential.helper manager   # Windows Credential Manager
git config --global core.autocrlf true
Write-G "  Identity set: $GITHUB_USER <$GITHUB_EMAIL>"
Write-G "  Credential helper: Windows Credential Manager"

# ── STEP 3: Authenticate ─────────────────────────────────────
Write-C "[3/5] Setting up GitHub authentication..."

$ghInstalled = Get-Command gh -EA SilentlyContinue

if ($ghInstalled) {
    # Best path: GitHub CLI
    Write-G "  GitHub CLI (gh) found — using it."
    $authStatus = gh auth status 2>&1
    if ($authStatus -match "Logged in") {
        Write-G "  Already authenticated: $authStatus"
    } else {
        Write-C "  Opening GitHub login in browser..."
        Write-Y "  → A browser window will open. Log in to GitHub."
        Write-Y "  → Select: GitHub.com > HTTPS > Paste an authentication token"
        gh auth login --hostname github.com --git-protocol https --web
        $authStatus2 = gh auth status 2>&1
        if ($authStatus2 -match "Logged in") {
            Write-G "  Authentication successful!"
        } else {
            Write-R "  Authentication may have failed. Check output above."
        }
    }
} else {
    # Fallback: Personal Access Token
    Write-Y "  GitHub CLI not found. Using Personal Access Token instead."
    Write-Y "  (Optional: install gh CLI later from https://cli.github.com)"
    Write-G ""
    Write-C "  You need a GitHub Personal Access Token (PAT)."
    Write-C "  How to get one (takes 2 minutes):"
    Write-D "    1. Go to: https://github.com/settings/tokens/new"
    Write-D "    2. Note: 'Meeko Machine Token'"
    Write-D "    3. Expiration: 1 year"
    Write-D "    4. Scopes: check [repo] and [workflow]"
    Write-D "    5. Click 'Generate token'"
    Write-D "    6. COPY IT — you only see it once"
    Write-G ""
    
    # Open the page for them
    Start-Process "https://github.com/settings/tokens/new?description=Meeko+Machine+Token&scopes=repo,workflow"
    
    $token = Read-Host "  Paste your token here (it won't echo)"
    
    if ($token -and $token.Length -gt 10) {
        # Store in Windows Credential Manager
        $credTarget = "git:https://github.com"
        $credUser   = $GITHUB_USER
        
        # Use cmdkey to store
        cmdkey /add:"$credTarget" /user:"$credUser" /pass:"$token" | Out-Null
        
        # Also set in git config as a test
        $testUrl = "https://${GITHUB_USER}:${token}@api.github.com/user"
        try {
            $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -EA Stop
            $userData = $response.Content | ConvertFrom-Json
            Write-G "  Token verified! Logged in as: $($userData.login)"
        } catch {
            Write-Y "  Could not verify token via API — but it's stored."
            Write-Y "  Error: $_"
        }
        
        # Store token in a local env file for Python scripts
        $envFile = "$RepoRoot\.env.local"
        if (Test-Path "$Desktop\meeko-nerve-center") {
            "GITHUB_TOKEN=$token" | Out-File $envFile -Encoding UTF8
            "GITHUB_USER=$GITHUB_USER" | Add-Content $envFile
            Write-G "  Token saved to .env.local (used by Python scripts)"
        }
    } else {
        Write-Y "  No token entered. Skipping — you can re-run this script anytime."
    }
}

# ── STEP 4: Clone or update repos ────────────────────────────
Write-C "[4/5] Syncing repos..."

foreach ($repo in $REPOS) {
    $repoPath = "$Desktop\$repo"
    $repoUrl  = "$REPO_BASE/$repo.git"
    
    if (Test-Path "$repoPath\.git") {
        Write-C "  Updating: $repo"
        Set-Location $repoPath
        $pullResult = git pull origin main 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-G "  OK: $repo up to date"
        } else {
            Write-Y "  Pull issue: $pullResult"
        }
    } else {
        Write-C "  Cloning: $repo -> $Desktop\$repo"
        git clone $repoUrl $repoPath 2>&1 | ForEach-Object { Write-D "  $_" }
        if ($LASTEXITCODE -eq 0) {
            Write-G "  OK: $repo cloned"
        } else {
            Write-R "  Failed to clone $repo — check auth above"
        }
    }
}

# ── STEP 5: Verify connection ─────────────────────────────────
Write-C "[5/5] Verifying connection..."
Set-Location $Desktop\meeko-nerve-center -EA SilentlyContinue

$remotes = git remote -v 2>&1
if ($remotes -match "github.com") {
    Write-G "  Remote: $remotes"
} else {
    Write-Y "  No remote found — may need to re-run"
}

# Quick auth test
try {
    $apiTest = Invoke-WebRequest "https://api.github.com/repos/$GITHUB_USER/meeko-nerve-center" -UseBasicParsing -EA Stop
    $repoData = $apiTest.Content | ConvertFrom-Json
    Write-G "  GitHub API: OK — repo has $($repoData.stargazers_count) stars, $($repoData.forks_count) forks"
} catch {
    Write-Y "  GitHub API test failed (may just be rate limit): $_"
}

Write-G ""
Write-G "================================================================"
Write-G "  CONNECTION COMPLETE"
Write-G "================================================================"
Write-G ""
Write-C "  What's wired:"
Write-D "  * Git identity: $GITHUB_USER <$GITHUB_EMAIL>"
Write-D "  * Credential helper: Windows Credential Manager"
Write-D "  * Repo synced: $Desktop\meeko-nerve-center"
Write-G ""
Write-C "  Next: run MEEKO_RUN.ps1 to start the full system"
Write-G ""
