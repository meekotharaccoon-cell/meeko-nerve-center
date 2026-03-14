import json
import os

def rebuild_mission_control():
    # Gather data from the swarm
    with open('data/knowledge_graph.json', 'r') as f: graph = json.load(f)
    
    html = f"""
    <html>
    <head><style>
        body {{ background: #0a0e14; color: #00ffcc; font-family: 'Courier New', monospace; padding: 50px; }}
        .node {{ border-left: 3px solid #00ffcc; padding-left: 20px; margin-bottom: 20px; }}
        h1 {{ text-transform: uppercase; letter-spacing: 5px; }}
    </style></head>
    <body>
        <h1>🌿 Meeko Nerve Center: Mission Control</h1>
        <div id="stats">Active Nodes: {len(graph['nodes'])}</div>
        <hr>
        <h2>Latest Insights</h2>
        {"".join([f"<div class='node'>{n['info']}</div>" for n in graph['nodes'][-5:]])}
    </body>
    </html>
    """
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("🖥️ Mission Control Updated: docs/index.html")

if __name__ == "__main__":
    rebuild_mission_control()
