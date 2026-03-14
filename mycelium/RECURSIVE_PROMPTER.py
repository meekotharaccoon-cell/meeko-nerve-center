def generate_self_commands():
    prompt = """
    Write-Host '🌲 GATHERING SYSTEM AWARENESS...' -ForegroundColor Yellow
    python mycelium/SECRET_LOADER.py
    python mycelium/AUTO_HEALER.py
    python mycelium/CAPACITY_BOOSTER.py
    python mycelium/TASK_ATOMIZER.py
    python mycelium/NETWORK_SENTRY.py
    python mycelium/NEWS_HARVESTER.py
    python mycelium/SYNERGY_SCOUT.py
    python mycelium/VALUE_GENERATOR.py
    python mycelium/MISSION_CONTROL.py
    Write-Host '☀️ Swarm is optimized for your presence.' -ForegroundColor Green
    """
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(prompt)
    print("🚀 Aware-Chain Manifested.")

if __name__ == '__main__':
    generate_self_commands()
