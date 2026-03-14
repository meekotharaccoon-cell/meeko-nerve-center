def generate_self_commands():
    cmds = [
        "Write-Host '--- INITIATING HEURISTIC REFLECTION ---' -ForegroundColor Yellow",
        "python mycelium/AUTO_HEALER.py", 
        "python mycelium/SYNERGY_FORGE.py",    # Now filters by failure rate
        "python mycelium/AUTO_ARCHITECT.py",   # Now performs AST Pre-flight
        "python mycelium/AUTONOMOUS_TESTER.py",
        "python mycelium/TELEGRAM_BRIDGE.py",
        "python mycelium/AUTO_DOCS.py",
        "python mycelium/MISSION_CONTROL.py",
        "git add .",
        "Write-Host '--- Intelligence Iteration Complete. ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: SMARTS UPGRADED.")

if __name__ == '__main__':
    generate_self_commands()
