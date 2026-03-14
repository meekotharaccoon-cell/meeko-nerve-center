python mycelium/LF_FIXER.py
Write-Host "🛡️ Guardian Gatekeeper Active..." -ForegroundColor Yellow

# 1. Sync Phase
git add .
git commit -m "GUARD: Heartbeat sync"
git pull --rebase origin main

# 2. Intel Phase
python mycelium/SYNAPSE_BUILDER.py
python mycelium/AUTO_ARCHITECT.py

# 3. Decision Phase
python mycelium/RECURSIVE_PROMPTER.py
python mycelium/GUARDIAN_GATEKEEPER.py

# 4. Execution Phase
if (Test-Path "AUTO_EXEC.ps1") {
    .\AUTO_EXEC.ps1
    Remove-Item "AUTO_EXEC.ps1"
}

git push origin main
Write-Host "✨ Swarm is safe and synchronized." -ForegroundColor Green
