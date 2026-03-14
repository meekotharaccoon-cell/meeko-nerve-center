Write-Host "🌀 Initiating Recursive Evolution Loop..." -ForegroundColor Magenta

# 1. Standard Maintenance
python mycelium/DESKTOP_HARVESTER.py
python mycelium/SYSTEM_CONDENSER.py

# 2. The Recursive Step: Let the AI decide the next command
python mycelium/AUTO_RUNNER.py

# 3. Sync everything back to the Cloud Brain
git add .
git commit -m "RECURSIVE: System generated and executed its own commands."
git push origin main

Write-Host "✨ Cycle Complete. The Mycelium is self-governing." -ForegroundColor Green
