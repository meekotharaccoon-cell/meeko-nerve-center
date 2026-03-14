import os
import hashlib

# MEEKO_NANOBOT: DUPLICATE_STRIKER
# Purpose: Delete local files if a copy exists in the Mycelium.

HARVEST_DIR = "data/harvested_knowledge"
DESKTOP = os.path.expanduser("~/Desktop")

def get_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def strike():
    # Map all harvested files by their hash
    harvested_hashes = {}
    if os.path.exists(HARVEST_DIR):
        for f in os.listdir(HARVEST_DIR):
            path = os.path.join(HARVEST_DIR, f)
            if os.path.isfile(path):
                harvested_hashes[get_hash(path)] = f

    # Check Desktop for matches
    freed_space = 0
    for f in os.listdir(DESKTOP):
        path = os.path.join(DESKTOP, f)
        if os.path.isfile(path) and f.endswith(('.py', '.txt', '.md')):
            h = get_hash(path)
            if h in harvested_hashes:
                size = os.path.getsize(path)
                os.remove(path)
                freed_space += size
                print(f"🔥 Striking duplicate: {f} (Preserved in Mycelium)")

    print(f"✅ Striker finished. Reclaimed {freed_space / 1024:.2f} KB.")

if __name__ == "__main__":
    strike()
