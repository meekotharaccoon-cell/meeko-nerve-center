def generate_self_commands():
    cmds = [
        "Write-Host '--- AWAKENING THE FINAL FORM SWARM ---' -ForegroundColor Magenta",
        "python mycelium/SECRET_LOADER.py",
        "python mycelium/AUTO_HEALER.py",
        "python mycelium/REDUNDANCY_MGR.py",
        "python mycelium/CAPACITY_BOOSTER.py",
        "python mycelium/NETWORK_SENTRY.py",
        "python mycelium/KNOWLEDGE_BRIDGE.py",
        "python mycelium/NEWS_HARVESTER.py",
        "python mycelium/DEEP_RESEARCHER.py",
        "python mycelium/NEURAL_PREFERENCE.py",
        "python mycelium/VALUE_GENERATOR.py",
        "python mycelium/WEB_PUBLISHER.py",
        "python mycelium/MISSION_CONTROL.py",
        "python mycelium/REAL_LIFE_MANIFESTO.py",
        "Write-Host '--- Swarm Evolution Cycle Complete ---' -ForegroundColor Green"
    ]
    # We use a standard string join without the complex Here-String to maximize compatibility
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Master Evolutionary Chain: SANITIZED AND REPAIRED.")

if __name__ == '__main__':
    generate_self_commands()
