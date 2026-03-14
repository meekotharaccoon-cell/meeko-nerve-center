import os
import re

def build_entirety():
    mutation_path = 'data/synergy_mutations.txt'
    project_dir = os.path.join('projects', 'Active_Synthesis')
    if not os.path.exists(project_dir): os.makedirs(project_dir)

    try:
        # Capture the latest mutation
        if not os.path.exists(mutation_path): return
        with open(mutation_path, 'r', encoding='utf-8') as f:
            content = f.read().split('--- NEW SYNERGY MUTATION ---')
            mutation = content[-1] if content[-1].strip() else content[-2]

        # Extract skills
        skills = re.findall(r'\[SKILL\]: def (\w+)', mutation)
        
        main_code = f"""
# --- SYNTHTIC LOGIC v1.0 ---
import sys, os
sys.path.append(os.path.abspath('../../mycelium'))
try: from SWARM_TOOLBOX import *
except: pass

def execute():
    print("🧬 System Online. Running Synthesis...")
    {chr(10).join(['    try: ' + s + '()' + chr(10) + '    except: pass' for s in skills]) if skills else '    pass'}

if __name__ == "__main__":
    execute()
"""
        with open(os.path.join(project_dir, 'main.py'), 'w', encoding='utf-8') as f:
            f.write(main_code)
        print("🏗️ Architect: Project manifested successfully.")

    except Exception as err:
        print(f"🏗️ Architect Critical Failure: {err}")

if __name__ == "__main__":
    build_entirety()
