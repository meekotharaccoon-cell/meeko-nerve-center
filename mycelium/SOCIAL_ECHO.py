import os
import json

def generate_echo():
    insight_path = 'docs/public_insight.html'
    if not os.path.exists(insight_path): return

    # Extract the latest insight
    with open(insight_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate a social-friendly "hook"
    hook = f"🌱 SolarPunk Swarm Update: {content[-200:].strip()}... #BuildInPublic #SolarPunk"
    
    with open('data/SOCIAL_QUEUE.txt', 'a', encoding='utf-8') as f:
        f.write(f"\n[QUEUE] {hook}")
    
    print("📢 Social Echo: New broadcast snippet queued in data/SOCIAL_QUEUE.txt.")

if __name__ == "__main__":
    generate_echo()
