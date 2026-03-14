import os
import random
import json

def forge_synergy():
    bank_path = 'data/knowledge_bank.txt'
    news_path = 'data/news_feed.json'
    toolbox_path = 'mycelium/SWARM_TOOLBOX.py'
    output_path = 'data/synergy_mutations.txt'

    # 1. Grab Wisdom (Resilient encoding)
    wisdom = "No wisdom found."
    if os.path.exists(bank_path):
        with open(bank_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if lines: wisdom = random.choice(lines).strip()

    # 2. Grab Trends
    trend = "No trends found."
    if os.path.exists(news_path):
        try:
            with open(news_path, 'r', encoding='utf-8') as f:
                news = json.load(f)
                if news: trend = random.choice(list(news.values()))
        except: pass

    # 3. Grab Skill (Added UTF-8 and Error handling)
    skill = "No legacy skills found."
    if os.path.exists(toolbox_path):
        with open(toolbox_path, 'r', encoding='utf-8', errors='ignore') as f:
            skills = [line for line in f.readlines() if 'def ' in line]
            if skills: skill = random.choice(skills).strip()

    # 4. Forge the Mutation
    mutation = f"""
--- NEW SYNERGY MUTATION ---
[WISDOM]: {wisdom}
[TREND]: {str(trend)[:200]}...
[SKILL]: {skill}
[HYPOTHESIS]: Bridge the logic of '{skill.split('(')[0] if '(' in skill else 'Legacy Logic'}' with the trend of '{str(trend)[:50]}' using your core philosophy: '{wisdom}'.
"""
    
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(mutation + "\n")
    
    print("🧬 Synergy Forge: Mutation successfully forged despite legacy noise.")

if __name__ == "__main__":
    forge_synergy()
