import os
import shutil

def link_discovered_code():
    processed_dir = 'knowledge_ingest/processed'
    mycelium_dir = 'mycelium'
    
    if not os.path.exists(processed_dir): return
    
    # Scan processed files for anything that looks like a Python or PowerShell script
    for file in os.listdir(processed_dir):
        if file.endswith(('.py', '.ps1')) and file not in os.listdir(mycelium_dir):
            print(f"🔗 Integration: Found legacy logic in {file}. Linking to Swarm...")
            # Copy discovered scripts into the mycelium folder to be vetted by the Guard
            shutil.copy(os.path.join(processed_dir, file), os.path.join(mycelium_dir, f"LEGACY_{file}"))

if __name__ == "__main__":
    link_discovered_code()
