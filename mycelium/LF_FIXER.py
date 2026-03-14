# NEURAL_LINK: Wisdom
# Part of the Meeko SolarPunk Swarm.

import os

def fix_swarm_files():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.py', '.ps1', '.md', '.txt')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                    
                    # Target the Byte Order Mark (BOM) specifically
                    has_bom = content.startswith(b'\xef\xbb\xbf')
                    if has_bom:
                        content = content[3:]
                        print(f"?? Stripped BOM from: {file}")

                    # Normalize line endings to Windows standard
                    normalized = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
                    
                    if has_bom or (normalized != content):
                        with open(path, 'wb') as f:
                            f.write(normalized)
                        if not has_bom: print(f"??? Fixed formatting: {file}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    fix_swarm_files()
