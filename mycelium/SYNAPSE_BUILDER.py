# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

﻿import json
import os
import re

def build_synapses():
    bank_path = 'data/knowledge_bank.txt'
    graph_path = 'data/knowledge_graph.json'
    
    if not os.path.exists(bank_path):
        return

    with open(bank_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Simple keyword extraction to build connections
    graph = {"nodes": [], "edges": []}
    for line in lines:
        # Extract keywords (words starting with capital letters or specific tech terms)
        keywords = re.findall(r'\b[A-Z][a-z]+|SolarPunk|Gmail|GitHub|PowerShell\b', line)
        if keywords:
            node = {"info": line.strip(), "tags": list(set(keywords))}
            graph["nodes"].append(node)
            
    with open(graph_path, 'w') as f:
        json.dump(graph, f, indent=4)
    print(f"🧠 Synapse Builder: Linked {len(graph['nodes'])} knowledge nodes.")

if __name__ == "__main__":
    build_synapses()
