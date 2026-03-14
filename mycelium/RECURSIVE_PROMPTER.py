def generate_self_commands():
    cmds = [
        "Write-Host '--- INITIATING TOTAL SYSTEM SYNTHESIS ---' -ForegroundColor Cyan",
        "python mycelium/SYSTEM_SIFTER.py",
        "python mycelium/DUPLICATE_DELETER.py",
        "python mycelium/KNOWLEDGE_BRIDGE.py",
        "python mycelium/LEGACY_INTEGRATOR.py",
        "python mycelium/CODE_COLLATER.py",
        "python mycelium/SYNERGY_FORGE.py",
        "python mycelium/AUTO_ARCHITECT.py", # Build the future
        "python mycelium/VALUE_GENERATOR.py",
        "python mycelium/MISSION_CONTROL.py",
        "git add data/*.txt",
        "git add projects/*",
        "git add mycelium/*.py",
        "Write-Host '--- Swarm has synthesized and built new blueprints. ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Master Architect: CALIBRATED.")

if __name__ == '__main__':
    generate_self_commands()
