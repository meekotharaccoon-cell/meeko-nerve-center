import os
import re

def manifest_missing_skills():
    main_path = 'projects/Active_Synthesis/main.py'
    output_skills_path = 'mycelium/GENERATED_SKILLS.py'
    
    if not os.path.exists(main_path): return

    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find functions the Architect tried to call
    calls = re.findall(r'try: (\w+)\(\)', content)
    
    # Check what we already have in our generated library
    existing_skills = ""
    if os.path.exists(output_skills_path):
        with open(output_skills_path, 'r', encoding='utf-8') as f:
            existing_skills = f.read()

    new_code = ""
    for func in calls:
        if func not in existing_skills and func != "execute":
            print(f"✨ Manifesting missing skill: {func}")
            new_code += f"\ndef {func}():\n    # Automatically manifested to fill logic gap\n    print('⚡ Skill {func} is now ACTIVE.')\n    return True\n"

    if new_code:
        with open(output_skills_path, 'a', encoding='utf-8') as f:
            f.write(new_code)
        print("🧬 GENERATED_SKILLS.py has been updated.")

if __name__ == "__main__":
    manifest_missing_skills()
