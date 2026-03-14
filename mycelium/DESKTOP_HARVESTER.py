# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

﻿import os
import shutil
import time
from datetime import datetime

# CONFIGURATION
SEARCH_PATH = os.path.expanduser("~/Desktop")
TARGET_DIR = "data/harvested_knowledge"
STALE_DAYS = 7

def harvest():
    if not os.path.exists(TARGET_DIR): os.makedirs(TARGET_DIR)
    
    now = time.time()
    count = 0

    for root, dirs, files in os.walk(SEARCH_PATH):
        for file in files:
            # Only target knowledge files
            if file.endswith(('.py', '.txt', '.md', '.json')):
                file_path = os.path.join(root, file)
                last_mod = os.path.getmtime(file_path)
                
                # If file is older than STALE_DAYS
                if (now - last_mod) > (STALE_DAYS * 86400):
                    print(f"📦 Harvesting stale knowledge: {file}")
                    # Move to Mycelium repo for backup/upload
                    shutil.move(file_path, os.path.join(TARGET_DIR, file))
                    count += 1

    print(f"✨ Harvested {count} items to the Mycelium. Desktop space reclaimed.")

if __name__ == "__main__":
    harvest()
