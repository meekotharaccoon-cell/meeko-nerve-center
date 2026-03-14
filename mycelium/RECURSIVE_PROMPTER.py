def generate_self_commands():
    cmds = [
        "Write-Host '--- CONVERGING SYSTEMS: BUILD-TEST-DOC ---' -ForegroundColor Magenta",
        "python mycelium/AUTO_HEALER.py",
        "python mycelium/SYNERGY_FORGE.py",
        "python mycelium/AUTO_ARCHITECT.py",
        "python mycelium/AUTONOMOUS_TESTER.py",
        "python mycelium/AUTO_DOCS.py", # Explain the creation
        "python mycelium/MISSION_CONTROL.py",
        "git add projects/Active_Synthesis/*",
        "git add data/*",
        "Write-Host '--- Synthesis & Documentation Complete. ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: DOCS ENABLED.")

if __name__ == '__main__':
    generate_self_commands()
