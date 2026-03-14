def generate_self_commands():
    cmds = [
        "Write-Host '--- INITIATING SYSTEM-WIDE HARVEST & SYNTHESIS ---' -ForegroundColor Cyan",
        "python mycelium/SYSTEM_SIFTER.py",
        "python mycelium/KNOWLEDGE_BRIDGE.py",
        "python mycelium/LEGACY_INTEGRATOR.py",
        "python mycelium/CODE_COLLATER.py", # The Glue
        "python mycelium/SECRET_LOADER.py",
        "python mycelium/AUTO_HEALER.py",
        "python mycelium/VALUE_GENERATOR.py",
        "python mycelium/MISSION_CONTROL.py",
        "python mycelium/REAL_LIFE_MANIFESTO.py",
        "git add data/knowledge_bank.txt",
        "git add docs/*",
        "git add mycelium/LEGACY_*.py",
        "git add mycelium/SWARM_TOOLBOX.py",
        "Write-Host '--- Harvest & Synthesis Complete. ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Master Architect: SYNCHRONIZED.")

if __name__ == '__main__':
    generate_self_commands()
