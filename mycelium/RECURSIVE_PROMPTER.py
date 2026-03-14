import json
import os

# MEEKO_ENGINE: RECURSIVE_PROMPTER
# Purpose: Allow the system to generate its own next steps.

def generate_self_commands():
    # Look for bottlenecks identified by the other agents
    queue_path = 'data/self_builder_queue.json'
    if not os.path.exists(queue_path):
        return

    with open(queue_path, 'r') as f:
        queue = json.load(f)

    if queue:
        # Take the top priority item and turn it into a shell command
        next_task = queue[0]
        cmd = f"Write-Host 'Executing Autonomous Task: {next_task['topic']}' -ForegroundColor Cyan\n"
        
        # If it's a product idea, trigger the factory
        if "PRODUCT" in next_task.get('type', ''):
            cmd += "python mycelium/BUSINESS_FACTORY.py\n"
        
        # Save as the auto-execution script
        with open('AUTO_EXEC.ps1', 'w') as f:
            f.write(cmd)
        print(f"🤖 System has generated its own command for: {next_task['topic']}")

if __name__ == "__main__":
    generate_self_commands()
