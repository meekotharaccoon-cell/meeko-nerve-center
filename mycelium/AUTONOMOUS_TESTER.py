import subprocess
import os

def test_manifestation():
    target = 'projects/Active_Synthesis/main.py'
    if not os.path.exists(target): return

    print(f"🧪 Tester: Executing {target}...")
    result = subprocess.run(['python', target], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Test Failed: {result.stderr}")
        with open('data/self_builder_queue.json', 'a') as q:
            import json
            q.write(json.dumps({"task": "HEAL", "target": target, "error": result.stderr}) + "\n")
    else:
        print(f"✅ Test Passed: {result.stdout}")

if __name__ == "__main__":
    test_manifestation()
