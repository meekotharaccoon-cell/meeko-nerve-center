# debugger.py
import json
import os
import subprocess
import sys
from pathlib import Path

class SolarPunkDebugger:
    def __init__(self, knowledge_base_path=None):
        if knowledge_base_path is None:
            knowledge_base_path = Path(__file__).parent / 'knowledge_base' / 'debug.json'
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base = self.load_knowledge_base()
        
    def load_knowledge_base(self):
        if self.knowledge_base_path.exists():
            with open(self.knowledge_base_path, 'r') as f:
                return json.load(f)
        return {
            "issues": [],
            "version": "1.0"
        }
    
    def save_knowledge_base(self):
        self.knowledge_base_path.parent.mkdir(exist_ok=True)
        with open(self.knowledge_base_path, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)
    
    def check_system(self):
        """Run system checks and return list of issues found."""
        issues = []
        
        # Check 1: Is the web server running?
        if not self.is_webserver_running():
            issues.append({
                "type": "webserver_down",
                "message": "Web server is not running on port 5000",
                "severity": "critical"
            })
        
        # Check 2: Are there recent error logs?
        log_issues = self.check_error_logs()
        issues.extend(log_issues)
        
        # Check 3: Disk space
        disk_issue = self.check_disk_space()
        if disk_issue:
            issues.append(disk_issue)
        
        return issues
    
    def is_webserver_running(self, port=5000):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def check_error_logs(self, log_path=None, recent_minutes=10):
        if log_path is None:
            log_path = Path('logs')
        issues = []
        
        if not log_path.exists():
            return issues
        
        import time
        cutoff = time.time() - (recent_minutes * 60)
        
        for log_file in log_path.glob('*.log'):
            # Simple check: if file has grown recently and contains "ERROR"
            # In production, we'd use more sophisticated log parsing
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if 'ERROR' in line or 'Exception' in line:
                            # Check if the line is recent (by file modification time for now)
                            # In a real system, we'd parse timestamps in the log
                            issues.append({
                                "type": "log_error",
                                "message": f"Error found in {log_file.name}: {line.strip()}",
                                "severity": "warning",
                                "log_file": str(log_file)
                            })
            except:
                pass
        
        return issues
    
    def check_disk_space(self, threshold_gb=1):
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        if free_gb < threshold_gb:
            return {
                "type": "low_disk_space",
                "message": f"Low disk space: {free_gb}GB free",
                "severity": "warning"
            }
        return None
    
    def diagnose_and_fix(self, issue):
        """Try to find a fix for the issue and apply it."""
        # Look for matching issue in knowledge base
        for known_issue in self.knowledge_base.get("issues", []):
            if known_issue["type"] == issue["type"]:
                # Found a known issue, try to apply the fix
                if self.apply_fix(known_issue.get("fix")):
                    return True
        return False
    
    def apply_fix(self, fix):
        """Apply a fix if it's safe."""
        if not fix:
            return False
        
        # Check if the fix is marked as safe
        if fix.get("safety") != "safe":
            print(f"Fix not marked as safe: {fix.get('description')}")
            return False
        
        # Execute the fix script or commands
        try:
            if "command" in fix:
                result = subprocess.run(fix["command"], shell=True, check=True, capture_output=True)
                print(f"Fix applied: {fix.get('description')}")
                return True
            elif "script" in fix:
                # Run a script
                script_path = Path(fix["script"])
                if script_path.exists():
                    subprocess.run([sys.executable, str(script_path)], check=True)
                    print(f"Fix applied via script: {fix.get('description')}")
                    return True
        except subprocess.CalledProcessError as e:
            print(f"Fix failed: {e}")
        
        return False
    
    def run(self):
        """Main debugger loop."""
        print("🔍 SolarPunk Debugger starting...")
        issues = self.check_system()
        
        if not issues:
            print("✅ No issues found.")
            return True
        
        print(f"⚠️  Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"   - {issue['message']} (severity: {issue['severity']})")
        
        # Try to fix each issue
        fixed = []
        for issue in issues:
            if self.diagnose_and_fix(issue):
                fixed.append(issue)
        
        # Report
        if fixed:
            print(f"✅ Fixed {len(fixed)} issue(s).")
            # Re-check system
            remaining_issues = self.check_system()
            if remaining_issues:
                print(f"⚠️  {len(remaining_issues)} issue(s) remain.")
                return False
            else:
                print("✅ All issues resolved.")
                return True
        else:
            print("❌ Could not automatically fix issues.")
            return False

if __name__ == "__main__":
    debugger = SolarPunkDebugger()
    success = debugger.run()
    sys.exit(0 if success else 1)
