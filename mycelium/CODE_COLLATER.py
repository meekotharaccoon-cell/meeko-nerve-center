import os
import re

def collate_legacy_logic():
    mycelium_dir = 'mycelium'
    toolbox_path = 'mycelium/SWARM_TOOLBOX.py'
    
    legacy_files = [f for f in os.listdir(mycelium_dir) if f.startswith('LEGACY_')]
    
    if not legacy_files:
        print("🧬 Code Collater: No legacy logic found to synthesize yet.")
        return

    combined_logic = "# --- SWARM TOOLBOX: SYNTHESIZED LEGACY LOGIC ---\nimport os\n\n"
    
    for file in legacy_files:
        path = os.path.join(mycelium_dir, file)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Extract functions (def ...) and classes
            logic = re.findall(r'(def\s+.*?\(.*?\):(?:\n\s+.*)+|class\s+.*?:\n(?:\s+.*)+)', content)
            if logic:
                combined_logic += f"\n# From: {file}\n" + "\n".join(logic) + "\n"

    with open(toolbox_path, 'w', encoding='utf-8') as f:
        f.write(combined_logic)
    print(f"🔧 Synthesizer: Created {toolbox_path} with {len(legacy_files)} legacy modules.")

if __name__ == "__main__":
    collate_legacy_logic()
