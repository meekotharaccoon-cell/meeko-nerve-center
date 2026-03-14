import os
import shutil
import time

def condense():
    # 1. Clear Python Caches
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))
            print("🧹 Cleared __pycache__")

    # 2. Clean old logs
    log_dir = "logs"
    if os.path.exists(log_dir):
        now = time.time()
        for f in os.listdir(log_dir):
            f_path = os.path.join(log_dir, f)
            if os.path.getmtime(f_path) < (now - (2 * 86400)): # 2 days
                os.remove(f_path)
                print(f"🗑 Deleted old log: {f}")

if __name__ == "__main__":
    condense()
