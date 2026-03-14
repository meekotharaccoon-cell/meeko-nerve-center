class CrossRepoSyncAgent:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.sync_history = []
    
    def sync_all(self):
        for repo in self.orchestrator.repositories:
            self.create_symlinks(repo)
        self.sync_history.append(datetime.now())
    
    def create_symlinks(self, repo):
        claude_dir = repo.path / '.claude'
        claude_dir.mkdir(exist_ok=True)
        
        symlinks = [
            ('agents/global', 'agents/global'),
            ('commands', 'commands'),
            ('guidelines/global', 'guidelines/global'),
            ('hooks', 'hooks'),
            ('skills/global', 'skills/global')
        ]
        
        for src, dst in symlinks:
            source = self.orchestrator.shared_path / src
            target = claude_dir / dst
            if target.exists():
                target.unlink()
            os.symlink(source, target, target_is_directory=True)
    
    def run_forever(self):
        while True:
            self.sync_all()
            time.sleep(21600)  # Every 6 hours
