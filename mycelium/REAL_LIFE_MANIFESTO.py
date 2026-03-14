import os

def manifest_to_reality():
    bank = 'data/knowledge_bank.txt'
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'MEEKO_ACTION_ITEMS.txt')
    
    if not os.path.exists(bank): return
    
    with open(bank, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Look for action-oriented collective knowledge
    actions = [l.strip() for l in lines if any(word in l.upper() for word in ["TASK:", "NEED TO", "TODO:", "ACTION:"])]
    
    if actions:
        with open(desktop, 'w', encoding='utf-8') as f:
            f.write("🌲 MEEKO REAL-WORLD MANIFESTO 🌲\n")
            f.write("===============================\n")
            for action in actions[-10:]: # Keep it focused on the latest 10
                f.write(f"[] {action}\n")
        print(f"📜 Manifesto Updated: Check your Desktop!")

if __name__ == "__main__":
    manifest_to_reality()
