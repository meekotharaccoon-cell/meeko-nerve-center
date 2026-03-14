import os
import re
import json

def process_and_plug():
    ingest_dir = 'knowledge_ingest'
    vault_path = 'data/secrets.json'
    bank_path = 'data/knowledge_bank.txt'
    
    # Common Patterns for hidden secrets
    secret_patterns = {
        "API_KEY": r'[A-Za-z0-9]{32,}',
        "GENERIC_TOKEN": r'sk-[a-zA-Z0-9]{20,}'
    }

    if not os.path.exists(ingest_dir): return
    files = [f for f in os.listdir(ingest_dir) if os.path.isfile(os.path.join(ingest_dir, f))]

    for file in files:
        path = os.path.join(ingest_dir, file)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 1. Look for Secrets to PLUG
            with open(vault_path, 'r') as f: vault = json.load(f)
            found_any = False
            for key_type, pattern in secret_patterns.items():
                matches = re.findall(pattern, content)
                for match in matches:
                    if match not in vault.values():
                        vault[f"EXTRACTED_{key_type}_{file[:5]}"] = match
                        content = content.replace(match, "[REDACTED_AND_VAULTED]")
                        found_any = True
            
            if found_any:
                with open(vault_path, 'w') as f: json.dump(vault, f, indent=4)
                print(f"🔌 Plugged new potential secrets from {file}")

            # 2. Commit the scrubbed knowledge to the Bank
            with open(bank_path, 'a', encoding='utf-8') as f:
                f.write(f"\n--- RECLAIMED FROM {file} ---\n{content}\n")
            
            # 3. Move to processed
            if not os.path.exists('knowledge_ingest/processed'): os.makedirs('knowledge_ingest/processed')
            os.rename(path, f"knowledge_ingest/processed/{file}")
            
        except Exception as e:
            print(f"❌ Failed to process {file}: {e}")

if __name__ == "__main__":
    process_and_plug()
