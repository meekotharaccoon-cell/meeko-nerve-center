import os
import json
import re

def forge_smart_mutation():
    toolbox_path = 'mycelium/SWARM_TOOLBOX.py'
    failure_log = 'data/self_builder_queue.json'
    
    # Load failure counts
    failure_counts = {}
    if os.path.exists(failure_log):
        with open(failure_log, 'r') as f:
            for line in f:
                try:
                    task = json.loads(line)
                    err = task.get('error', '')
                    # Extract function name from error if possible
                    match = re.search(r"name '(\w+)' is not defined", err)
                    if match:
                        func = match.group(1)
                        failure_counts[func] = failure_counts.get(func, 0) + 1
                except: pass

    # Read available skills
    with open(toolbox_path, 'r', encoding='utf-8') as f:
        all_skills = re.findall(r'def (\w+)\(', f.read())

    # Filter out skills that fail too often (Threshold: 3 failures)
    viable_skills = [s for s in all_skills if failure_counts.get(s, 0) < 3]

    mutation = f"""
--- NEW SYNERGY MUTATION ---
[STRATEGY]: Optimized Synthesis v2
[CONFIDENCE]: High
[REASONING]: Filtering {len(all_skills) - len(viable_skills)} unstable legacy functions.
"""
    for skill in viable_skills[:5]: # Take top 5 viable skills
        mutation += f"[SKILL]: def {skill}\n"

    with open('data/synergy_mutations.txt', 'a', encoding='utf-8') as f:
        f.write(mutation)
    print(f"🧠 Forge: Forged a smarter mutation using {len(viable_skills)} stable skills.")

if __name__ == "__main__":
    forge_smart_mutation()
