import json
import os

def generate_self_commands():
    queue_path = 'data/self_builder_queue.json'
    if not os.path.exists(queue_path): return
    with open(queue_path, 'r', encoding='utf-8') as f:
        queue = json.load(f)
    if queue and isinstance(queue, list):
        topic = queue[0].get('topic', 'Evolution')
        cmd = f"Write-Host 'Executing: {topic}' -ForegroundColor Cyan\npython mycelium/NEURAL_WEAVER.py\npython mycelium/GMAIL_NOTIFIER.py\npython mycelium/DUPLICATE_STRIKER.py\npython mycelium/CAPABILITY_SCANNER.py"
        with open('AUTO_EXEC.ps1', 'w', encoding='utf-8') as f:
            f.write(cmd)
        print(f"🤖 Generated: {topic}")

if __name__ == '__main__':
    generate_self_commands()
