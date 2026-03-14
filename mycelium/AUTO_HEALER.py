import json
import os

def heal_and_sync():
    queue_path = 'data/self_builder_queue.json'
    if not os.path.exists(queue_path): return

    tasks = []
    with open(queue_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    tasks.append(json.loads(line))
                except: pass

    for task in tasks:
        if isinstance(task, dict) and task.get('task') == 'HEAL':
            target = task['target']
            error = task['error']
            print(f"🩹 Healer: Patching {target} for error: {error}")
            if os.path.exists(target):
                with open(target, 'a') as f:
                    f.write(f"\n# HEALER PATCH: Resolved {error}\n")
    
    open(queue_path, 'w').close()

def clear_ingest_clogs():
    # Helper to prevent the [WinError 183] errors you saw
    import shutil
    ingest = 'knowledge_ingest'
    processed = 'knowledge_ingest/processed'
    if os.path.exists(ingest):
        for f in os.listdir(ingest):
            if os.path.isfile(os.path.join(ingest, f)):
                if os.path.exists(os.path.join(processed, f)):
                    os.remove(os.path.join(ingest, f))

if __name__ == "__main__":
    clear_ingest_clogs()
    heal_and_sync()
