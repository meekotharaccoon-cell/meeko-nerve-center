Write-Host "🌱 SolarPunk Sync Initiated..." -ForegroundColor Green

# 1. Pull the latest spores from the cloud
git pull origin main

# 2. Run the intake to see if you emailed any new intelligence
python mycelium/GMAIL_INTAKE.py

# 3. Run the bridge to interweave any new files
python mycelium/KNOWLEDGE_BRIDGE.py

# 4. Generate the 'Proof of Life' dashboard
python mycelium/README_GENERATOR.py

# 5. Commit the growth back to the internet
git add .
git commit -m "SWARM: Interweaving new knowledge bridges (SolarPunk protocol)"
git push origin main

Write-Host "✨ Swarm Synchronized. Check your GitHub Pages for the updated Capability Map." -ForegroundColor Cyan
