def generate_self_commands():
    prompt = """
    Write-Host '🌿 SolarPunk Swarm Awakening...' -ForegroundColor Green
    python mycelium/SECRET_LOADER.py
    python mycelium/AUTO_HEALER.py
    python mycelium/NETWORK_SENTRY.py
    python mycelium/NEWS_HARVESTER.py
    python mycelium/OFFLINE_BRAIN.py
    python mycelium/SYNAPSE_BUILDER.py
    python mycelium/DASHBOARD.py
    Write-Host '☀️ Swarm is nourished, secure, and growing.' -ForegroundColor Yellow
    """
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(prompt)
    print("✨ SolarPunk Security Protocol Manifested.")

if __name__ == '__main__':
    generate_self_commands()
