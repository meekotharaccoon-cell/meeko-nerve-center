# NEURAL_LINK: Wisdom
# Part of the Meeko SolarPunk Swarm.

import json
import os
import re

def build_synapses():
    bank_path = 'data/knowledge_bank.txt'
    graph_path = 'data/knowledge_graph.json'
    if not os.path.exists(bank_path): return
    with open(bank_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    graph = {'nodes': [], 'edges': []}
    for line in lines:
        keywords = re.findall(r'\b[A-Z][a-z]+|SolarPunk|Gmail|GitHub|PowerShell\b', line)
        if keywords:
            graph['nodes'].append({'info': line.strip(), 'tags': list(set(keywords))})
    with open(graph_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=4)
    print(f"🧠 Linked {len(graph['nodes'])} nodes.")

if __name__ == '__main__':
    build_synapses()
