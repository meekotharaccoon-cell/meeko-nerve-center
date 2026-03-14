import json
import os

def visualize_swarm():
    graph_path = 'data/knowledge_graph.json'
    if not os.path.exists(graph_path):
        print("No connections found yet.")
        return

    with open(graph_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)

    print("\n🌲 MEEKO NERVE CENTER: KNOWLEDGE TREE")
    print("====================================")
    for node in graph['nodes']:
        tags = " + ".join(node['tags'])
        print(f" ● [{tags}] -> {node['info'][:50]}...")
    print("====================================\n")

if __name__ == "__main__":
    visualize_swarm()
