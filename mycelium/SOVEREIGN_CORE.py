import subprocess
import os

def run_singularity_pulse():
    # Priority Order for Total Autonomy
    priority_tasks = [
        'REVENUE_ENGINE.py',   # Make Money
        'SCAVENGER_WEB.py',    # Find New Money Methods
        'SKILL_MANIFESTOR.py', # Fix Gaps in Revenue Code
        'AUTO_ARCHITECT.py'    # Build the Updated System
    ]
    
    for task in priority_tasks:
        path = f'mycelium/{task}'
        if os.path.exists(path):
            try:
                print(f"🌀 Singularity: Running {task}...")
                subprocess.run(['python', path], check=True)
            except Exception as e:
                print(f"⚠️ Task {task} stalled: {e}")

if __name__ == "__main__":
    run_singularity_pulse()
