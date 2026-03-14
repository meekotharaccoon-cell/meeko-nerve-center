Write-Host "🌀 Initiating Recursive Evolution Loop (SolarPunk v3)..." -ForegroundColor Magenta

# 1. Auto-Sync with Cloud Brain first to prevent push rejection
git pull --rebase origin main

# 2. Clean the environment
python mycelium/DESKTOP_HARVESTER.py
python mycelium/SYSTEM_CONDENSER.py

# 3. Recursive Logic
python mycelium/AUTO_RUNNER.py

# 4. Push the new growth
git add .
git commit -m "RECURSIVE: System self-updated and synchronized."
git push origin main

Write-Host "✨ Cycle Complete. Local and Cloud are unified." -ForegroundColor Green
