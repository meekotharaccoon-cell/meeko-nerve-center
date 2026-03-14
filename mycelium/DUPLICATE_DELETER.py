import os
import hashlib

def get_file_hash(path):
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def purge_duplicates():
    ingest_dir = 'knowledge_ingest'
    if not os.path.exists(ingest_dir): return
    
    seen_hashes = {}
    duplicates_removed = 0

    print("🧹 Duplicate Deleter: Scanning for digital clones...")
    
    for root, dirs, files in os.walk(ingest_dir):
        for file in files:
            path = os.path.join(root, file)
            f_hash = get_file_hash(path)
            
            if f_hash in seen_hashes:
                # Duplicate found! Remove the older or redundant copy
                os.remove(path)
                duplicates_removed += 1
            else:
                seen_hashes[f_hash] = path

    if duplicates_removed:
        print(f"✅ Cleanup Complete: Pruned {duplicates_removed} redundant files.")
    else:
        print("✨ No duplicates found. The Knowledge Stream is pure.")

if __name__ == "__main__":
    purge_duplicates()
