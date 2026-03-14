import os
import subprocess

def run_organ_pulse():
    organs = ['REVENUE_MONITOR.py', 'SCAVENGER_WEB.py', 'TELEGRAM_BRIDGE.py']
    print("🌀 SOVEREIGN CORE: Pulsing external sensors...")
    
    for organ in organs:
        path = f'mycelium/{organ}'
        if os.path.exists(path):
            try:
                subprocess.run(['python', path], check=True)
            except Exception as e:
                print(f"⚠️ Organ {organ} failed: {e}")

if __name__ == "__main__":
    run_organ_pulse()
