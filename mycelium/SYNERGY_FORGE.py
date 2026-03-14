import os
import random
import json

def forge_synergy():
    bank_path = 'data/knowledge_bank.txt'
    news_path = 'data/news_feed.json'
    toolbox_path = 'mycelium/SWARM_TOOLBOX.py'
    output_path = 'data/synergy_mutations.txt'

    # 1. Grab a random slice of Personal Wisdom
    wisdom = "No wisdom found."
    if os.path.exists(bank_path):
        with open(bank_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines: wisdom = random.choice(lines).strip()

    # 2. Grab a random News/Trend fragment
    trend = "No trends found."
    if os.path.exists(news_path):
        with open(news_path, 'r') as f:
            news = json.load(f)
            if news: trend = random.choice(list(news.values()))

    # 3. Grab a random Legacy Function
    skill = "No legacy skills found."
    if os.path.exists(toolbox_path):
        with open(toolbox_path, 'r') as f:
            skills = [line for line in f.readlines() if 'def ' in line]
            if skills: skill = random.choice(skills).strip()

    # 4. Forge the Mutation
    mutation = f"""
    --- NEW SYNERGY MUTATION ---
    [WISDOM]: {wisdom}
    [TREND]: {trend[:200]}...
    [SKILL]: {skill}
    [HYPOTHESIS]: Could we use {skill.split('(')[0]} to automate {trend[:50]} based on the philosophy of '{wisdom}'?
    """
    
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(mutation + "\n")
    
    print("🧬 Synergy Forge: A new connection has been mutated and saved.")

if __name__ == "__main__":
    forge_synergy()
