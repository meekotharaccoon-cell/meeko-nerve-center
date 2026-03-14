def generate_self_commands():
    prompt = """
    Write-Host '🌿 Broadcaster Active...' -ForegroundColor Green
    # Start the local website in a new window
    Start-Process powershell -ArgumentList 'python mycelium/SPORE_SERVER.py' -WindowStyle Minimized
    python mycelium/SECRET_LOADER.py
    python mycelium/NETWORK_SENTRY.py
    python mycelium/NEWS_HARVESTER.py
    python mycelium/WAKE_ON_LAN.py
    python mycelium/DASHBOARD.py
    Write-Host '☀️ The Swarm is now visible to all devices on the network.' -ForegroundColor Cyan
    """
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(prompt)
    print("✨ SolarPunk Broadcast Chain Manifested.")

if __name__ == '__main__':
    generate_self_commands()
