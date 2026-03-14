import os

def build_blueprint():
    mutation_path = 'data/synergy_mutations.txt'
    if not os.path.exists(mutation_path): return

    with open(mutation_path, 'r', encoding='utf-8') as f:
        mutations = f.read().split('--- NEW SYNERGY MUTATION ---')
        last_mutation = mutations[-1] if mutations[-1].strip() else mutations[-2]

    # Create a project name based on the mutation
    project_name = "Mutation_Alpha"
    project_dir = os.path.join('projects', project_name)
    
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
        
    with open(os.path.join(project_dir, 'manifesto.md'), 'w', encoding='utf-8') as f:
        f.write(f"# Project Manifested via Synergy\n\n{last_mutation}")
        
    print(f"🏗️ Auto-Architect: New project structure manifested at /projects/{project_name}")

if __name__ == "__main__":
    build_blueprint()
