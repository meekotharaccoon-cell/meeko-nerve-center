# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

﻿import json
import os

def plan_expansion():
    graph_path = 'data/knowledge_graph.json'
    queue_path = 'data/self_builder_queue.json'
    
    if not os.path.exists(graph_path):
        return

    with open(graph_path, 'r') as f:
        graph = json.load(f)

    # If we have a lot of knowledge about 'Gmail' but no 'Gmail_Notifier', suggest it.
    all_tags = [tag for node in graph['nodes'] for tag in node['tags']]
    
    new_tasks = []
    if "Gmail" in all_tags and "Status" not in all_tags:
        new_tasks.append({"topic": "Build Gmail Status Notifier", "type": "FIX"})
    
    if len(graph['nodes']) > 5:
        new_tasks.append({"topic": "Optimize Knowledge Graph", "type": "MAINTENANCE"})

    with open(queue_path, 'w') as f:
        json.dump(new_tasks, f, indent=4)
    print(f"🏗️ Auto-Architect: Queued {len(new_tasks)} expansion tasks.")

if __name__ == "__main__":
    plan_expansion()
