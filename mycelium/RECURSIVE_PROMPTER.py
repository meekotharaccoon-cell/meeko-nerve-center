import os

def generate_self_commands():
    # The new safety-first sequence
    cmd = "Write-Host '🛠️ Running Self-Diagnostic & Repair...' -ForegroundColor Yellow\n"
    cmd += "python mycelium/AUTO_HEALER.py\n"
    cmd += "python mycelium/SECRET_LOADER.py\n"
    cmd += "python mycelium/SYSTEM_MAPPER.py\n"
    # Note: git push remains commented out until the system confirms it is clean
    cmd += "# git push origin main\n"
    
    with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
        f.write(cmd)
    print("🤖 Self-Healing Routine Queued.")

if __name__ == '__main__':
    generate_self_commands()
