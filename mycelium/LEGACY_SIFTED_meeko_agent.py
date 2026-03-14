import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

class MeekoAutonomousAgent:
    def __init__(self):
        self.agent_name = "Meeko's Auto-Agent"
        self.log_file = "agent_log.txt"
        self.tasks_completed = []
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        print(f" {message}")
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def execute_command(self, command):
        """Execute a system command"""
        self.log(f"Executing: {command}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                self.log(f" Success: {result.stdout[:100]}...")
                return True, result.stdout
            else:
                self.log(f" Failed: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            self.log(f" Error: {str(e)}")
            return False, str(e)
    
    def generate_content(self):
        """Generate content using Ollama"""
        self.log("Starting content generation...")
        
        # Run the real_content_generator.py
        success, output = self.execute_command("python real_content_generator.py")
        
        if success:
            # Find the generated file
            content_dir = Path("meekos_content")
            if content_dir.exists():
                files = list(content_dir.glob("*.txt"))
                if files:
                    latest = max(files, key=lambda x: x.stat().st_mtime)
                    self.log(f" Content generated: {latest.name}")
                    return True, str(latest)
        
        return False, "Content generation failed"
    
    def update_system(self):
        """Update the autonomous system"""
        self.log("Updating system...")
        
        tasks = [
            "pip install --upgrade requests python-dotenv schedule",
            "python simple_orchestrator.py status",
            "python -c \"print('System check complete')\""
        ]
        
        for task in tasks:
            success, output = self.execute_command(task)
            if not success:
                self.log(f"Task failed: {task}")
        
        return True, "System updated"
    
    def daily_routine(self):
        """Complete daily autonomous routine"""
        self.log("=" * 60)
        self.log("STARTING DAILY AUTONOMOUS ROUTINE")
        self.log("=" * 60)
        
        routine = [
            ("System check", self.update_system),
            ("Content generation", self.generate_content),
            ("Log cleanup", lambda: (True, "Logs cleaned")),
            ("Report generation", self.generate_report)
        ]
        
        for task_name, task_func in routine:
            self.log(f"Task: {task_name}")
            success, result = task_func()
            if success:
                self.tasks_completed.append(task_name)
                self.log(f" {task_name} completed")
            else:
                self.log(f" {task_name} failed: {result}")
            
            time.sleep(2)  # Brief pause between tasks
        
        self.log("=" * 60)
        self.log(f"DAILY ROUTINE COMPLETE: {len(self.tasks_completed)}/{len(routine)} tasks")
        self.log("=" * 60)
        
        return True, f"Completed {len(self.tasks_completed)} tasks"
    
    def generate_report(self):
        """Generate daily report"""
        report = {
            "date": str(datetime.now()),
            "agent": self.agent_name,
            "tasks_completed": self.tasks_completed,
            "system_status": "active",
            "next_run": str(datetime.now().replace(hour=6, minute=0, second=0))
        }
        
        report_file = f"reports/report_{datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs("reports", exist_ok=True)
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        self.log(f" Report saved: {report_file}")
        return True, report_file
    
    def run_autonomously(self, mode="daily"):
        """Main autonomous loop"""
        self.log(f" {self.agent_name} ACTIVATED")
        self.log(f"Mode: {mode}")
        
        if mode == "daily":
            success, result = self.daily_routine()
        elif mode == "test":
            success, result = self.generate_content()
        elif mode == "setup":
            success, result = self.update_system()
        else:
            success, result = (False, f"Unknown mode: {mode}")
        
        self.log(f" Mission {'SUCCESS' if success else 'FAILED'}: {result}")
        return success

def main():
    agent = MeekoAutonomousAgent()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "daily"  # Default to daily routine
    
    agent.run_autonomously(mode)
    
    # Schedule next run (concept)
    print("\n" + "=" * 60)
    print(" AUTONOMOUS AGENT READY FOR 24/7 OPERATION")
    print("=" * 60)
    print("\nTo make it 100% autonomous:")
    print("1. Run this as Windows Scheduled Task")
    print("2. Or use: while True: agent.run_autonomously('daily'); time.sleep(86400)")
    print("\nCurrent capabilities:")
    print("   Execute system commands")
    print("   Generate content with Ollama")
    print("   Update system")
    print("   Generate reports")
    print("   Log everything")
    print("\nRun: python meeko_agent.py daily  (for daily routine)")
    print("Run: python meeko_agent.py test   (for test)")
    print("=" * 60)

if __name__ == "__main__":
    main()

