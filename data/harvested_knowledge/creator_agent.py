class RepoCreatorAgent:
    def __init__(self, github_api):
        self.github = github_api
        self.created_repos = []
    
    def create_from_template(self, name, description, template_files):
        repo = self.github.create_repo(name, description)
        repo_path = Path(f'../{name}')
        subprocess.run(['git', 'clone', repo['clone_url'], str(repo_path)])
        
        for file_path, content in template_files.items():
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        os.chdir(repo_path)
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'Initial commit from template'])
        subprocess.run(['git', 'push'])
        os.chdir('..')
        
        self.created_repos.append(name)
        return repo
    
    def create_missing_repos(self, required_repos):
        existing = [d.name for d in Path('..').iterdir() if d.is_dir() and (d/'.git').exists()]
        for name, config in required_repos.items():
            if name not in existing:
                self.create_from_template(name, config['description'], config['files'])
