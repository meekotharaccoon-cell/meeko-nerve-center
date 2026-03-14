import json
import os

def generate_evolution_report():
    failure_log = 'data/self_builder_queue.json'
    mutation_path = 'data/synergy_mutations.txt'
    report_path = 'docs/evolution.html'
    
    failures = {}
    if os.path.exists(failure_log):
        with open(failure_log, 'r') as f:
            for line in f:
                try:
                    task = json.loads(line)
                    target = task.get('target', 'Unknown')
                    failures[target] = failures.get(target, 0) + 1
                except: pass

    html_content = f"""
    <html>
    <head><title>Mycelium Evolution Tracker</title>
    <style>
        body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 20px; }}
        .skill-card {{ background: #1e1e1e; border: 1px solid #333; padding: 10px; margin: 10px; border-radius: 5px; }}
        .success {{ color: #4caf50; }}
        .failure {{ color: #f44336; }}
    </style>
    </head>
    <body>
        <h1>🧬 Evolution Dashboard</h1>
        <div class="skill-card">
            <h2>Current State</h2>
            <p>Active Synthesis Failures: <span class="failure">{failures.get('projects/Active_Synthesis/main.py', 0)}</span></p>
        </div>
    </body>
    </html>
    """
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("📊 Evolution Viewer: Dashboard updated at docs/evolution.html")

if __name__ == "__main__":
    generate_evolution_report()
