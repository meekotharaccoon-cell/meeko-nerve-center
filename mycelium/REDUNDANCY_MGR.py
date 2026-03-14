import os
import shutil

def create_offline_redundancy():
    # Back up the current best-performing scripts to a 'Stable' folder
    if not os.path.exists('mycelium/stable_core'):
        os.makedirs('mycelium/stable_core')
    
    core_files = ['AUTO_HEALER.py', 'SECRET_LOADER.py', 'GUARD.ps1']
    for f in core_files:
        if os.path.exists(f):
            shutil.copy(f, f'mycelium/stable_core/{f}')
    print("🛡️ Redundancy Manager: Stable Core backed up for offline resilience.")

if __name__ == "__main__":
    create_offline_redundancy()
