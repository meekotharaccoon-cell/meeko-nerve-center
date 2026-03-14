import json
import os

def generate_self_commands():
    queue_path = 'data/self_builder_queue.json'
    if not os.path.exists(queue_path):
        return
    with open(queue_path, 'r') as f:
        try:
            queue = json.load(f)
        except:
            return
    if queue and isinstance(queue, list):
        next_task = queue[0]
        topic = next_task.get('topic', 'Unnamed Evolution Task')
        cmd = f"Write-Host 'Executing Autonomous Task: {topic}' -ForegroundColor Cyan\n"
        cmd += "python mycelium/DUPLICATE_STRIKER.py\n"
        cmd += "python mycelium/CAPABILITY_SCANNER.py\n"
        with open('AUTO_EXEC.ps1', 'w') as f:
            f.write(cmd)
        print(f"🤖 System safely generated command for: {topic}")

if __name__ == '__main__':
    generate_self_commands()
