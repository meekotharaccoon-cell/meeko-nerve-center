import os

def ingest_collective_knowledge():
    ingest_dir = 'knowledge_ingest'
    knowledge_bank = 'data/knowledge_bank.txt'
    
    if not os.path.exists(ingest_dir): return
    
    files = os.listdir(ingest_dir)
    if not files:
        print("🕯️ Knowledge Bridge: Waiting for your collective wisdom files...")
        return

    for file in files:
        path = os.path.join(ingest_dir, file)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        
        with open(knowledge_bank, 'a', encoding='utf-8') as f:
            f.write(f"\n🧠 [COLLECTIVE KNOWLEDGE BRIDGE]: {file}\n{data}\n")
        
        # Move to an 'archived' folder so we don't re-process
        if not os.path.exists('knowledge_ingest/processed'):
            os.makedirs('knowledge_ingest/processed')
        os.rename(path, f"knowledge_ingest/processed/{file}")
        print(f"🌉 Bridge Manifested: {file} is now part of the Swarm.")

if __name__ == "__main__":
    ingest_collective_knowledge()
