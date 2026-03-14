def generate_self_commands():
    cmds = [
        "Write-Host '--- AUTONOMOUS CODING INITIALIZED ---' -ForegroundColor Cyan",
        "python mycelium/AUTO_HEALER.py",
        "python mycelium/SYNERGY_FORGE.py",
        "python mycelium/SKILL_MANIFESTOR.py", # Fill the gaps
        "python mycelium/AUTO_ARCHITECT.py",   # Build with new skills
        "python mycelium/AUTONOMOUS_TESTER.py",
        "python mycelium/EVOLUTION_VIEWER.py",
        "python mycelium/MISSION_CONTROL.py",
        "git add .",
        "Write-Host '--- Gap-Filling Complete. ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { if (Test-Path $c.Split(' ')[1]) { iex $c } }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: SKILL MANIFESTATION ACTIVE.")

if __name__ == '__main__':
    generate_self_commands()
