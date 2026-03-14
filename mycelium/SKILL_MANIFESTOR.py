import os
import re

def scavenge_logic(func_name):
    # Look through processed files for any mention of this function
    processed_dir = 'knowledge_ingest/processed'
    if not os.path.exists(processed_dir): return None
    
    for root, dirs, files in os.walk(processed_dir):
        for file in files:
            if file.endswith('.py') or file.endswith('.txt'):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Look for a function definition block
                        pattern = rf"def {func_name}\(.*?\):.*?(?=\ndef|\nif __name__|$)"
                        match = re.search(pattern, content, re.DOTALL)
                        if match:
                            print(f"🕵️ Scavenger: Found logic for {func_name} in {file}")
                            return match.group(0)
                except: continue
    return None

def manifest_scavenged_skills():
    main_path = 'projects/Active_Synthesis/main.py'
    output_skills_path = 'mycelium/GENERATED_SKILLS.py'
    
    if not os.path.exists(main_path): return
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()

    calls = re.findall(r'try: (\w+)\(\)', content)
    
    existing_skills = ""
    if os.path.exists(output_skills_path):
        with open(output_skills_path, 'r', encoding='utf-8') as f:
            existing_skills = f.read()

    new_code = ""
    for func in calls:
        if func not in existing_skills and func != "execute":
            # TRY TO SCAVENGE FIRST
            logic = scavenge_logic(func)
            if logic:
                new_code += f"\n# Scavenged from legacy knowledge\n{logic}\n"
            else:
                # Fallback to placeholder
                new_code += f"\ndef {func}():\n    print('⚡ Skill {func} manifested (Placeholder).')\n    return True\n"

    if new_code:
        with open(output_skills_path, 'a', encoding='utf-8') as f:
            f.write(new_code)
        print("🧬 GENERATED_SKILLS.py has been evolved with scavenged logic.")

if __name__ == "__main__":
    manifest_scavenged_skills()
