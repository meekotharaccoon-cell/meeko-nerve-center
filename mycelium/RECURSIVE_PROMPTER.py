def generate_self_commands():
    cmds = [
        "Write-Host '--- CONVERGING SYSTEMS: BUILD-TEST-SENTRY ---' -ForegroundColor Magenta",
        "python mycelium/EXTERNAL_SENTRY.py", # Look outside
        "python mycelium/AUTO_HEALER.py",
        "python mycelium/SYNERGY_FORGE.py",
        "python mycelium/AUTO_ARCHITECT.py",
        "python mycelium/AUTONOMOUS_TESTER.py",
        "python mycelium/AUTO_DOCS.py",
        "python mycelium/MISSION_CONTROL.py",
        "git add projects/Active_Synthesis/*",
        "git add data/*",
        "Write-Host '--- Convergence Cycle Complete. ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: SENTRY ENGAGED.")

if __name__ == '__main__':
    generate_self_commands()
