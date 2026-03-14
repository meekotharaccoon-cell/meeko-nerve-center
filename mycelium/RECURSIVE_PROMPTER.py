def generate_self_commands():
    # We use a cleaner multi-line string to avoid quote errors
    commands = [
        "Write-Host 'ðŸ’Ž AWAKENING THE FINAL FORM SWARM...' -ForegroundColor Magenta",
        "python mycelium/SECRET_LOADER.py",
        "python mycelium/AUTO_HEALER.py",
        "python mycelium/REDUNDANCY_MGR.py",
        "python mycelium/CAPACITY_BOOSTER.py",
        "python mycelium/NETWORK_SENTRY.py",
        "python mycelium/NEWS_HARVESTER.py
        'python mycelium/KNOWLEDGE_BRIDGE.py',",
        "python mycelium/DEEP_RESEARCHER.py",
        "python mycelium/NEURAL_PREFERENCE.py",
        "python mycelium/VALUE_GENERATOR.py",
        "python mycelium/WEB_PUBLISHER.py",
        "python mycelium/MISSION_CONTROL.py",
        "Write-Host 'ðŸŒ• The Swarm is self-aware and resilient.' -ForegroundColor Green"
    ]
    
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write("\n".join(commands))
    print("ðŸŒ€ Master Evolutionary Chain Repaired.")

if __name__ == '__main__':
    generate_self_commands()
