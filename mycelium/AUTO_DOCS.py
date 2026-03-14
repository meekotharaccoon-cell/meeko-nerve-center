import os

def document_progress():
    project_dir = 'projects/Active_Synthesis'
    mutation_path = 'data/synergy_mutations.txt'
    doc_path = os.path.join(project_dir, 'README.md')

    if not os.path.exists(project_dir): return

    try:
        with open(mutation_path, 'r', encoding='utf-8') as f:
            mutation = f.read().split('--- NEW SYNERGY MUTATION ---')[-1]

        summary = f"""# Project: Active Synthesis
## Origin Mutation
{mutation}

## System Status
- **Last Built:** {os.path.getmtime(os.path.join(project_dir, 'main.py'))}
- **Autonomous Testing:** Active
- **Self-Healing:** Enabled

This project was automatically manifested by the Mycelium Architect using legacy skills and modern trends.
"""
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print("📝 Auto-Docs: Project documentation manifested.")
    except:
        pass

if __name__ == "__main__":
    document_progress()
