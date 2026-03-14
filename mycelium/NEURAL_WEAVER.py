import os
import json

def weave_knowledge():
    graph_path = 'data/knowledge_graph.json'
    if not os.path.exists(graph_path): return
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)
        
    summary = " | ".join([node['tags'][0] for node in graph['nodes'] if node['tags']])
    header = f"# NEURAL_LINK: {summary}\n# Part of the Meeko SolarPunk Swarm.\n\n"

    for root, dirs, files in os.walk('mycelium'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                # Use utf-8 encoding and ignore errors to stay robust
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if "NEURAL_LINK" not in content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(header + content)
                    print(f"🕸️ Interwove {file}")

if __name__ == "__main__":
    weave_knowledge()
