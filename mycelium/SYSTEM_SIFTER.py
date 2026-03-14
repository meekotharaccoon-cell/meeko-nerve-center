import os
import shutil

def deep_sift():
    target_dirs = [
        os.path.join(os.environ['USERPROFILE'], 'Documents'),
        os.path.join(os.environ['USERPROFILE'], 'Downloads'),
        os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Temp') # Hidden logs often hide here
    ]
    
    ingest_dir = 'knowledge_ingest'
    # Extensions that usually contain "Wisdom" or "Tokens"
    wisdom_exts = ('.py', '.ps1', '.json', '.txt', '.md', '.log', '.env', '.yaml', '.conf')

    print("⛏️ Deep Sifter: Descending into the system strata...")
    
    for root_dir in target_dirs:
        if not os.path.exists(root_dir): continue
        for root, dirs, files in os.walk(root_dir):
            # Skip heavy folders to keep the system fast
            if any(x in root for x in ['node_modules', '.git', 'venv', 'AppData\\Local\\Microsoft']):
                continue
                
            for file in files:
                if file.endswith(wisdom_exts):
                    src_path = os.path.join(root, file)
                    # Only grab files smaller than 1MB to avoid massive log dumps
                    if os.path.getsize(src_path) < 1024 * 1024:
                        dest_path = os.path.join(ingest_dir, f"SIFTED_{file}")
                        try:
                            shutil.copy2(src_path, dest_path)
                        except:
                            continue

if __name__ == "__main__":
    deep_sift()
