# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

???import os
import sys

def check_intent():
    if not os.path.exists('AUTO_EXEC.ps1'):
        return
    with open('AUTO_EXEC.ps1', 'r') as f:
        cmd_content = f.read()
    loop_triggers = ['EVOLVE.ps1', 'AUTO_RUNNER', 'while(true)']
    if any(trigger in cmd_content for trigger in loop_triggers):
        print("\n?????? LOOP DETECTED!")
        sys.exit(1)
    print("??? Command Vetted.")

if __name__ == "__main__":
    check_intent()
