import json
import os

def atomize_tasks():
    queue_path = 'data/self_builder_queue.json'
    if not os.path.exists(queue_path): return

    with open(queue_path, 'r') as f:
        tasks = f.readlines()

    if len(tasks) > 10:
        print(f"⚛️ Atomizing {len(tasks)} tasks into manageable shards...")
        # Keeps only the first 5 to run now, saves the rest for later
        with open(queue_path, 'w') as f:
            f.writelines(tasks[5:])
        print("✅ Sharding complete. CPU pressure reduced.")

if __name__ == "__main__":
    atomize_tasks()
