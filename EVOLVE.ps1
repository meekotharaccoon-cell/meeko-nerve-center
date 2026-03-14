Write-Host "🌀 SolarPunk v4: Clearing the Path..." -ForegroundColor Magenta

# 1. Force-stage everything so Git doesn't complain about 'unstaged changes'
git add .

# 2. Commit what we have locally (even if it's just a heartbeat)
git commit -m "HEARTBEAT: Pre-sync state save"

# 3. Pull from Cloud Brain and Rebase
Write-Host "📡 Syncing with GitHub..." -ForegroundColor Cyan
git pull --rebase origin main

# 4. Run the Nanobots
python mycelium/DESKTOP_HARVESTER.py
python mycelium/SYSTEM_CONDENSER.py

# 5. Recursive Execution
python mycelium/AUTO_RUNNER.py

# 6. Final Push to Cloud
git add .
git commit -m "RECURSIVE: Evolution cycle successful."
git push origin main

Write-Host "✨ Swarm is Unified and Up-to-Date." -ForegroundColor Green
