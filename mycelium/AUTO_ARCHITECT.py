import os
import re

def build_entirety():
    mutation_path = 'data/synergy_mutations.txt'
    project_dir = os.path.join('projects', 'Active_Synthesis')
    if not os.path.exists(project_dir): os.makedirs(project_dir)

    try:
        if not os.path.exists(mutation_path): return
        with open(mutation_path, 'r', encoding='utf-8') as f:
            content = f.read().split('--- NEW SYNERGY MUTATION ---')
            mutation = [m for m in content if m.strip()][-1]

        skills = re.findall(r'\[SKILL\]: def (\w+)', mutation)
        
        exec_lines = []
        for s in skills:
            exec_lines.append(f"    try:\n        {s}()\n    except Exception as e:\n        print(f'Skill {s} failed: {{e}}')")
        
        exec_block = "\n".join(exec_lines) if exec_lines else "    pass"

        main_code = f"""# -*- coding: utf-8 -*-
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
{exec_block}

if __name__ == "__main__":
    execute()
"""
        with open(os.path.join(project_dir, 'main.py'), 'w', encoding='utf-8') as f:
            f.write(main_code)
        print("🏗️ Architect: Emojis purged, UTF-8 wrapper injected.")

    except Exception as err:
        print(f"🏗️ Architect Failure: {err}")

if __name__ == "__main__":
    build_entirety()
