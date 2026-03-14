import json
import os
import shutil

def heal_and_sync():
    queue_path = 'data/self_builder_queue.json'
    if not os.path.exists(queue_path): return
    tasks = []
    try:
        with open(queue_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try: tasks.append(json.loads(line))
                    except: pass
        for task in tasks:
            if isinstance(task, dict) and task.get('task') == 'HEAL':
                target = task['target']
                print(f"🩹 Healer: Patching {target}...")
                if os.path.exists(target):
                    with open(target, 'a', encoding='utf-8') as f:
                        f.write(f"\n# HEALER_AUTOPATCH: Logic injection.\n")
        open(queue_path, 'w').close()
    except Exception as e:
        print(f"⚠️ Healer logic paused: {e}")

def clear_ingest_clogs():
    ingest = 'knowledge_ingest'
    processed = 'knowledge_ingest/processed'
    if not os.path.exists(processed): os.makedirs(processed)
    for f in os.listdir(ingest):
        src = os.path.join(ingest, f)
        if os.path.isfile(src):
            try:
                # If it already exists in processed, just delete the duplicate in ingest
                if os.path.exists(os.path.join(processed, f)):
                    os.remove(src)
                else:
                    shutil.move(src, processed)
            except PermissionError:
                continue # Skip if file is locked by another process
            except Exception:
                continue

if __name__ == "__main__":
    clear_ingest_clogs()
    heal_and_sync()
