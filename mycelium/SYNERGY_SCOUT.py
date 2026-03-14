import json
import os

def identify_synergies():
    # Load all existing data
    synergies = []
    if os.path.exists('data/knowledge_graph.json'):
        with open('data/knowledge_graph.json', 'r') as f:
            graph = json.load(f)
        
        # Look for cross-pollination opportunities
        tags = [node['tags'] for node in graph['nodes']]
        if any('Security' in t for t in tags) and any('Tech-Evolution' in t for t in tags):
            synergies.append("Action: Combine Network Sentry data with Tech Trends for a 'Privacy First' blog post.")

    if synergies:
        with open('data/self_builder_queue.json', 'a', encoding='utf-8') as f:
            for s in synergies:
                f.write(json.dumps({"topic": "Synergy Found", "info": s}) + "\n")
        print(f"🧬 Synergy Scout: Found {len(synergies)} new cross-connections.")

if __name__ == "__main__":
    identify_synergies()
