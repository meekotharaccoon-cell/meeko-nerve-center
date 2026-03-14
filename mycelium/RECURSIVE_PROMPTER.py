def generate_self_commands():
    cmds = [
        "Write-Host '--- CONVERGING SYSTEMS: BUILD-TEST-HEAL ---' -ForegroundColor Magenta",
        "python mycelium/AUTO_HEALER.py",     # Clear clogs first
        "python mycelium/KNOWLEDGE_BRIDGE.py",
        "python mycelium/SYNERGY_FORGE.py",
        "python mycelium/AUTO_ARCHITECT.py",  # Architect Builds
        "python mycelium/AUTONOMOUS_TESTER.py", # Tester Runs
        "python mycelium/AUTO_HEALER.py",     # Healer Fixes if Tester failed
        "python mycelium/AUTONOMOUS_TESTER.py", # Final Test
        "python mycelium/MISSION_CONTROL.py",
        "git add projects/Active_Synthesis/*",
        "git add data/*",
        "Write-Host '--- Convergence Cycle Complete. ---' -ForegroundColor Green"
    ]
    ps_content = "$cmds = " + str(cmds).replace("[", "@(").replace("]", ")") + "\nforeach ($c in $cmds) { iex $c }"
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print("🌀 Sovereign Architect: LOOP RE-CALIBRATED.")

if __name__ == '__main__':
    generate_self_commands()
