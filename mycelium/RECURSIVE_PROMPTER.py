def generate_self_commands():
    cmds = [
        "Write-Host '--- INITIATING SOVEREIGN DIALOGUE ---' -ForegroundColor Magenta",
        "python mycelium/SYSTEM_SIFTER.py",
        "python mycelium/KNOWLEDGE_BRIDGE.py",
        "python mycelium/CODE_COLLATER.py",
        "python mycelium/SYNERGY_FORGE.py",
        "python mycelium/AUTO_ARCHITECT.py", # Architect builds
        "python mycelium/AUTO_HEALER.py",    # Healer checks Architect's work
        "python mycelium/AUTO_ARCHITECT.py", # Architect refines
        "python mycelium/MISSION_CONTROL.py",
        "python mycelium/REAL_LIFE_MANIFESTO.py",
        "git add projects/Active_Synthesis/*",
        "git add data/*.json",
        "git add data/*.txt",
        "Write-Host '--- The Systems have converged. Manifestation complete. ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Master Architect: SOVEREIGN LOOP ENGAGED.")

if __name__ == '__main__':
    generate_self_commands()
