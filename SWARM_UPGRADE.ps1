Write-Host "🛸 Nanobot Swarm Releasing..." -ForegroundColor Yellow

# 1. Pull latest from Cloud Brain
git pull origin main

# 2. Harvest stale desktop files into the repo
python mycelium/DESKTOP_HARVESTER.py

# 3. Clean and condense local system
python mycelium/SYSTEM_CONDENSER.py

# 4. Interweave new knowledge
python mycelium/KNOWLEDGE_BRIDGE.py

# 5. Push harvested knowledge to GitHub (Free Storage)
git add .
git commit -m "SWARM: Knowledge harvest and system condense. Reclaiming disk space."
git push origin main

Write-Host "✅ Swarm Cycle Complete. Knowledge preserved in the cloud. Local disk cleaned." -ForegroundColor Green
