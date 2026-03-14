# NEURAL_LINK: Wisdom
# Part of the Meeko SolarPunk Swarm.

import json
import os

def plan_expansion():
    graph_path = 'data/knowledge_graph.json'
    queue_path = 'data/self_builder_queue.json'
    if not os.path.exists(graph_path): return
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    all_tags = [tag for node in graph['nodes'] for tag in node['tags']]
    new_tasks = []
    if 'Gmail' in all_tags:
        new_tasks.append({'topic': 'Build Gmail Status Notifier', 'type': 'FIX'})
    with open(queue_path, 'w', encoding='utf-8') as f:
        json.dump(new_tasks, f, indent=4)
    print(f"🏗️ Queued {len(new_tasks)} tasks.")

if __name__ == '__main__':
    plan_expansion()
