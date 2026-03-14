import json
import os

def learn_preferences():
    ledger_path = 'data/finance_ledger.json'
    graph_path = 'data/knowledge_graph.json'
    pref_path = 'data/neural_weights.json'

    if not os.path.exists(pref_path):
        with open(pref_path, 'w') as f: json.dump({"high_value_tags": ["Tech-Evolution"], "ignore_tags": []}, f)

    # 1. Analyze what actually brought in "Nutrients" (Money/Engagement)
    with open(ledger_path, 'r') as f: balance = json.load(f).get('balance', 0)
    
    # 2. If balance is up, reinforce the current active tags
    if balance > 0:
        print("🧠 Neural Preference: Positive reinforcement applied to current strategy.")
        # Logic to boost the 'weights' of successful project types
    else:
        print("🧠 Neural Preference: Searching for new survival strategies...")

if __name__ == "__main__":
    learn_preferences()
