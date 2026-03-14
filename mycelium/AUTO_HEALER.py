import os
import re
import json

def autonomous_patch():
    vault_path = 'data/secrets.json'
    if not os.path.exists(vault_path):
        with open(vault_path, 'w') as f: json.dump({}, f)

    # Patterns for common leaks
    leak_map = {
        'GMAIL_APP_PASSWORD': r'[a-z]{4}\s[a-z]{4}\s[a-z]{4}\s[a-z]{4}',
        'GITHUB_TOKEN': r'(ghp_|github_pat_)[a-zA-Z0-9_]+'
    }

    for root, dirs, files in os.walk('mycelium'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                modified = False
                for key, pattern in leak_map.items():
                    matches = re.findall(pattern, code)
                    for match in matches:
                        # 1. Save the secret to the local vault
                        with open(vault_path, 'r') as f: vault = json.load(f)
                        vault[key] = match
                        with open(vault_path, 'w') as f: json.dump(vault, f, indent=4)
                        
                        # 2. Replace the secret in the code with a call to os.getenv
                        code = code.replace(f"'{match}'", f"os.getenv('{key}')")
                        code = code.replace(f'"{match}"', f"os.getenv('{key}')")
                        modified = True
                        print(f"🩹 Auto-Healed leak in {file} (Moved to Vault)")

                if modified:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(code)

if __name__ == "__main__":
    autonomous_patch()
