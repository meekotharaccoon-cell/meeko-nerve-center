"""
AI SYSTEM GRAPH VISUALIZER
One file. No dependencies beyond standard Python + pip install networkx matplotlib.
Shows your entire Ethical AI Impact System as a living graph.
"""

import json
import os
import subprocess
from pathlib import Path

# ==============================================
# STEP 1: AUTO-GENERATE THE LATEST SYSTEM MAP
# ==============================================
def generate_system_map():
    """PowerShell command to scan your system right now"""
    ps_command = '''
    $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
    $ollamaModels = "API not responding"
    if ($ollamaCommand) {
        try {
            $apiResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/models" -ErrorAction Stop
            $ollamaModels = $apiResponse.name -join ", "
        } catch {}
    }

    $pyFiles = Get-ChildItem -Path "$env:USERPROFILE\\Desktop" -Recurse -Include *.py
    $scriptDeps = @()
    foreach ($file in $pyFiles) {
        $usesOllama = (Select-String -Path $file.FullName -Pattern "ollama").Count -gt 0
        $usesFastAPI = (Select-String -Path $file.FullName -Pattern "FastAPI").Count -gt 0
        $readsJSON = (Select-String -Path $file.FullName -Pattern ".json").Count -gt 0
        if ($usesOllama -or $usesFastAPI -or $readsJSON) {
            $scriptDeps += [PSCustomObject]@{
                Script = $file.Name
                Path = $file.FullName
                Ollama = $usesOllama
                FastAPI = $usesFastAPI
                JSONQueue = $readsJSON
            }
        }
    }

    $jsonFiles = Get-ChildItem -Path "$env:USERPROFILE\\Desktop" -Recurse -Include *.json | Select-Object Name, FullName

    @{
        Ollama = @{
            Installed = ($ollamaCommand -ne $null)
            Models = $ollamaModels
        }
        Scripts = $scriptDeps
        JSONQueues = $jsonFiles
    } | ConvertTo-Json -Depth 5
    '''
    
    result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
    return json.loads(result.stdout)

# ==============================================
# STEP 2: VISUALIZE AS GRAPH
# ==============================================
def visualize_graph(system_data):
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("📦 Installing required packages...")
        subprocess.run(["pip", "install", "networkx", "matplotlib"])
        import networkx as nx
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

    G = nx.DiGraph()
    
    # Color scheme
    colors = {
        "ollama": "#10a37f",      # Green - running AI
        "model": "#4285f4",       # Blue - AI models
        "script": "#fbbc05",      # Yellow - Python scripts
        "queue": "#ea4335",       # Red - JSON queues
        "api": "#34a853"          # Light green - API bridge
    }
    
    # Add Ollama node
    if system_data["Ollama"]["Installed"]:
        G.add_node("Ollama", type="ollama", label="🦙 Ollama")
        
        # Add models
        models = system_data["Ollama"]["Models"]
        if models and models != "API not responding":
            for model in models.split(", "):
                model = model.strip()
                if model:
                    G.add_node(model, type="model", label=f"📦 {model}")
                    G.add_edge("Ollama", model, label="runs")
    
    # Add scripts
    for script in system_data["Scripts"]:
        script_name = script["Script"]
        G.add_node(script_name, type="script", label=f"📜 {script_name}")
        
        if script["Ollama"]:
            G.add_edge(script_name, "Ollama", label="calls")
        if script["FastAPI"]:
            G.add_node("FastAPI", type="api", label="⚡ FastAPI")
            G.add_edge(script_name, "FastAPI", label="uses")
    
    # Add JSON queues
    for queue in system_data["JSONQueues"]:
        queue_name = queue["Name"]
        G.add_node(queue_name, type="queue", label=f"📋 {queue_name}")
        
        # Connect scripts that read this queue
        for script in system_data["Scripts"]:
            if script["JSONQueue"]:
                # Check if script actually references this specific queue
                script_path = Path(script["Path"])
                if script_path.exists():
                    try:
                        content = script_path.read_text()
                        if queue_name in content:
                            G.add_edge(script_name, queue_name, label="writes/reads")
                    except:
                        pass
    
    # ==========================================
    # DRAW THE GRAPH
    # ==========================================
    plt.figure(figsize=(16, 10))
    
    # Position nodes
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Draw nodes by type
    node_types = nx.get_node_attributes(G, 'type')
    for node_type, color in colors.items():
        node_list = [n for n in G.nodes() if node_types.get(n) == node_type]
        nx.draw_networkx_nodes(G, pos, nodelist=node_list, node_color=color, node_size=2000, alpha=0.9)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowsize=20, width=1.5, alpha=0.6)
    
    # Draw labels
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight="bold")
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=colors["ollama"], label='🦙 Ollama (Local LLM)'),
        mpatches.Patch(color=colors["model"], label='📦 AI Models'),
        mpatches.Patch(color=colors["script"], label='📜 Python Scripts'),
        mpatches.Patch(color=colors["queue"], label='📋 JSON Queues'),
        mpatches.Patch(color=colors["api"], label='⚡ API Bridge'),
    ]
    plt.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    plt.title("🤖 ETHICAL AI IMPACT SYSTEM - LIVING ARCHITECTURE", fontsize=16, fontweight="bold", pad=20)
    plt.axis('off')
    
    # Save
    output_path = Path.home() / "Desktop" / "AI_System_Graph.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Graph saved to: {output_path}")
    
    plt.show()
    
    return G

# ==============================================
# STEP 3: SYSTEM REPORT
# ==============================================
def print_report(system_data):
    print("\n" + "="*60)
    print("🤖 ETHICAL AI IMPACT SYSTEM - LIVE STATUS")
    print("="*60)
    
    # Ollama status
    print(f"\n🦙 OLLAMA: {'✅ RUNNING' if system_data['Ollama']['Installed'] else '❌ NOT FOUND'}")
    if system_data['Ollama']['Models'] != "API not responding":
        print(f"   Models: {system_data['Ollama']['Models']}")
    else:
        print(f"   ⚠️  API not responding - run 'ollama serve'")
    
    # Scripts
    print(f"\n📜 PYTHON SCRIPTS: {len(system_data['Scripts'])}")
    for script in system_data['Scripts']:
        deps = []
        if script['Ollama']: deps.append("🦙")
        if script['FastAPI']: deps.append("⚡")
        if script['JSONQueue']: deps.append("📋")
        print(f"   {script['Script']:<30} {' '.join(deps)}")
    
    # JSON queues
    print(f"\n📋 JSON QUEUES: {len(system_data['JSONQueues'])}")
    for queue in system_data['JSONQueues']:
        print(f"   {queue['Name']}")
    
    print("\n" + "="*60)
    print("✅ SYSTEM MAP COMPLETE")
    print("📊 Graph saved to Desktop/AI_System_Graph.png")
    print("="*60)

# ==============================================
# MAIN
# ==============================================
if __name__ == "__main__":
    print("🔍 Scanning your AI ecosystem...")
    system_data = generate_system_map()
    
    print_report(system_data)
    
    print("\n🔄 Generating visual graph...")
    G = visualize_graph(system_data)
    
    print("\n🚀 Frictionless AI System Map complete!")