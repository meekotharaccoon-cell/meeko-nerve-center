Write-Host "??? Guardian Gatekeeper Active..." -ForegroundColor Yellow

# 1. Force a clean state locally
$status = git status --porcelain
if ($status) {
    Write-Host "?? Staging local changes..." -ForegroundColor Gray
    git add .
    git commit -m "GUARD: Pre-sync checkpoint"
}

# 2. Pull latest from GitHub to prevent 'Rejected' errors
Write-Host "?? Syncing with Cloud Brain..." -ForegroundColor Cyan
git pull --rebase origin main

# 3. Generate the next command
python mycelium/SYNAPSE_BUILDER.py
python mycelium/AUTO_ARCHITECT.py
python mycelium/RECURSIVE_PROMPTER.py

# 4. Check for loops before running
python mycelium/GUARDIAN_GATEKEEPER.py

# 5. Run the vetted command
if (Test-Path "AUTO_EXEC.ps1") {
    .\AUTO_EXEC.ps1
    Remove-Item "AUTO_EXEC.ps1"
}

Write-Host "? Swarm is safe and synchronized." -ForegroundColor Green
