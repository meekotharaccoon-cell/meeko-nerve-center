# -*- coding: utf-8 -*-
# --- SYNTHETIC LOGIC v1.2 ---
import sys, os
import io

# Force UTF-8 for console output to prevent charmap errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.path.abspath('../../mycelium'))
try:
    from SWARM_TOOLBOX import *
except:
    pass

def execute():
    print("SYSTEM ONLINE: Running Synthesis Loop...")
    try:
        run_daily_cycle()
    except Exception as e:
        print(f'Skill run_daily_cycle failed: {e}')

if __name__ == "__main__":
    execute()
