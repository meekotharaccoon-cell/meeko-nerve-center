# --- SYNTHETIC LOGIC v1.1 ---
import sys, os
sys.path.append(os.path.abspath('../../mycelium'))
try:
    from SWARM_TOOLBOX import *
except:
    pass

def execute():
    print("🧬 System Online. Running Synthesis...")
    try:
        setup_convertkit()
    except Exception as e:
        print(f'Skill setup_convertkit failed: {e}')

if __name__ == "__main__":
    execute()
