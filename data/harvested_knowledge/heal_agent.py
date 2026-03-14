class SelfHealingAgent:
    def __init__(self):
        self.heal_log = []
        self.max_attempts = 3
    
    def detect_failures(self, repo_path):
        failures = []
        result = subprocess.run(['python', '-m', 'py_compile'] + 
                               list(Path(repo_path).rglob('*.py')),
                               capture_output=True, text=True)
        if result.returncode != 0:
            failures.append({
                'type': 'build_error',
                'output': result.stderr,
                'files': self.extract_files_with_errors(result.stderr)
            })
        return failures
    
    def diagnose_error(self, failure):
        output = failure['output'].lower()
        if 'syntaxerror' in output:
            return {'root_cause': 'syntax_error', 'fix_strategy': 'fix_syntax', 'confidence': 0.9}
        elif 'indentationerror' in output:
            return {'root_cause': 'indentation_error', 'fix_strategy': 'fix_indentation', 'confidence': 0.85}
        elif 'importerror' in output:
            return {'root_cause': 'missing_import', 'fix_strategy': 'add_import', 'confidence': 0.8}
        return {'root_cause': 'unknown', 'fix_strategy': None, 'confidence': 0.0}
    
    def generate_fix(self, file_path, diagnosis):
        with open(file_path, 'r') as f:
            content = f.read()
        if diagnosis['fix_strategy'] == 'fix_syntax':
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if re.match(r'^\s*(if|for|while|def|class)\s+.*[^:]$', line):
                    lines[i] = line + ':'
            return '\n'.join(lines)
        return None
    
    def apply_fix(self, file_path, fixed_content):
        backup = file_path + '.bak'
        os.rename(file_path, backup)
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        return backup
    
    def verify_fix(self, file_path):
        result = subprocess.run(['python', '-m', 'py_compile', file_path],
                               capture_output=True)
        return result.returncode == 0
    
    def heal_repository(self, repo_path):
        failures = self.detect_failures(repo_path)
        for failure in failures:
            diagnosis = self.diagnose_error(failure)
            if diagnosis['fix_strategy'] and diagnosis['confidence'] > 0.5:
                for file_path in failure.get('files', []):
                    full_path = os.path.join(repo_path, file_path)
                    fixed = self.generate_fix(full_path, diagnosis)
                    if fixed:
                        backup = self.apply_fix(full_path, fixed)
                        if self.verify_fix(full_path):
                            self.heal_log.append({'success': True, 'file': file_path})
                        else:
                            os.replace(backup, full_path)
    
    def run_forever(self):
        while True:
            for repo in Path('..').iterdir():
                if repo.is_dir() and (repo / '.git').exists():
                    self.heal_repository(str(repo))
            time.sleep(3600)
