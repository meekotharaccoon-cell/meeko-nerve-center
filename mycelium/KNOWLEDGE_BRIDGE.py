import json
import os
from datetime import datetime

# MEEKO_ENGINE: KNOWLEDGE_BRIDGE (SolarPunk Edition)
# Purpose: Interweave emailed intelligence into the core architecture.

CAPABILITY_MAP = "data/capability_map.json"
MANIFESTO = "solarpunk_legal_declaration.txt"

def interweave(new_engine_name, engine_purpose):
    # 1. Update the Capability Map
    if os.path.exists(CAPABILITY_MAP):
        with open(CAPABILITY_MAP, 'r') as f:
            cmap = json.load(f)
    else:
        cmap = {"engines": []}

    new_entry = {
        "name": new_engine_name,
        "purpose": engine_purpose,
        "integrated_at": datetime.now().isoformat(),
        "status": "active",
        "philosophy": "SolarPunk / Decentralized Knowledge"
    }
    
    cmap["engines"].append(new_entry)
    
    with open(CAPABILITY_MAP, 'w') as f:
        json.dump(cmap, f, indent=4)

    # 2. Log to the Solarpunk Manifesto
    with open(MANIFESTO, "a") as f:
        f.write(f"\n[{datetime.now().date()}] New knowledge bridge established: {new_engine_name}. Swarm complexity increasing.")

    print(f"Interweave Complete: {new_engine_name} is now part of the Mycelium.")

if __name__ == "__main__":
    # This is called by GMAIL_INTAKE when new code arrives
    print("Bridge ready for incoming spores.")
