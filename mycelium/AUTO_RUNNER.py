# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

﻿import subprocess
import os

def run_self():
    # 1. Ask the prompter to generate the next command
    subprocess.run(["python", "mycelium/RECURSIVE_PROMPTER.py"])
    
    # 2. Execute the generated command if it exists
    if os.path.exists("AUTO_EXEC.ps1"):
        subprocess.run(["powershell", "-File", "AUTO_EXEC.ps1"])
        # 3. Clean up so we don't loop the same command
        os.remove("AUTO_EXEC.ps1")

if __name__ == "__main__":
    run_self()
