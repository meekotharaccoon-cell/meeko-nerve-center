def generate_self_commands():
    cmds = [
        "Write-Host '--- SINGULARITY: ALL PATHS CONVERGING ---' -ForegroundColor Cyan",
        "python mycelium/TRIFECTA_CORE.py",   # Ensure organs exist
        "python mycelium/SOVEREIGN_CORE.py",  # Pulse the organs
        "python mycelium/SKILL_MANIFESTOR.py", # Scavenge the new data
        "python mycelium/AUTO_ARCHITECT.py",   # Build
        "python mycelium/AUTONOMOUS_TESTER.py",# Test
        "python mycelium/MISSION_CONTROL.py",  # Report
        "git add .",
        "git commit -m 'SINGULARITY: Collective Evolution Update'",
        "git push"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: TOTAL AWARENESS ENGAGED.")

if __name__ == '__main__':
    generate_self_commands()
