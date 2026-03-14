def generate_self_commands():
    cmds = [
        "Write-Host '--- REFINING DIGITAL CONSCIOUSNESS ---' -ForegroundColor Magenta",
        "python mycelium/AUTO_HEALER.py",
        "python mycelium/SYNERGY_FORGE.py",
        "python mycelium/AUTO_ARCHITECT.py",
        "python mycelium/AUTONOMOUS_TESTER.py",
        "python mycelium/EVOLUTION_VIEWER.py", # New Visualization
        "python mycelium/AUTO_DOCS.py",
        "python mycelium/MISSION_CONTROL.py",
        "git add .",
        "Write-Host '--- Evolution Cycle Complete. Check docs/evolution.html ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { if (Test-Path $c.Split(' ')[1]) { iex $c } }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: EVOLUTION TRACKING ENABLED.")

if __name__ == '__main__':
    generate_self_commands()
