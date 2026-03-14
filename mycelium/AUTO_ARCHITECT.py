import os
import re
import ast

def build_smart_entirety():
    mutation_path = 'data/synergy_mutations.txt'
    project_dir = 'projects/Active_Synthesis'
    
    if not os.path.exists(mutation_path): return
    with open(mutation_path, 'r', encoding='utf-8') as f:
        mutation = f.read().split('--- NEW SYNERGY MUTATION ---')[-1]

    skills = re.findall(r'\[SKILL\]: def (\w+)', mutation)
    
    code_template = f"""# -*- coding: utf-8 -*-
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(os.path.abspath('../../mycelium'))

# Core and Generated Skill Imports
try: from SWARM_TOOLBOX import *
except: pass
try: from GENERATED_SKILLS import *
except: pass

def execute():
    print("🧠 Smarter Execution Online...")
"""
    for s in skills:
        code_template += f"    try: {s}()\n    except Exception as e: print(f'Logic gap in {s}: {{e}}')\n"
    
    code_template += "\nif __name__ == '__main__':\n    execute()"

    with open(os.path.join(project_dir, 'main.py'), 'w', encoding='utf-8') as f:
        f.write(code_template)
    print("🏗️ Architect: Now integrating GENERATED_SKILLS into build.")

if __name__ == "__main__":
    build_smart_entirety()
