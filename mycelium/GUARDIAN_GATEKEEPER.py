# NEURAL_LINK: Wisdom
# Part of the Meeko SolarPunk Swarm.

import os
import sys

def check_intent():
    if not os.path.exists('AUTO_EXEC.ps1'): return
    with open('AUTO_EXEC.ps1', 'r', encoding='utf-8') as f:
        content = f.read()
    if 'while(true)' in content:
        sys.exit(1)
    print('✅ Command Vetted.')

if __name__ == '__main__':
    check_intent()
