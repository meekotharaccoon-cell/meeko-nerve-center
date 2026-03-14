import json
import os
import requests

def process_locally():
    bank_path = 'data/knowledge_bank.txt'
    if not os.path.exists(bank_path): return

    with open(bank_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # We target a local OLLAMA instance (No API Key Required)
    # This assumes you have Ollama running on localhost:11434
    try:
        print("🧠 Local Brain: Analyzing harvested seeds...")
        response = requests.post('http://localhost:11434/api/generate', 
            json={
                "model": "mistral",
                "prompt": f"Based on these tech updates, suggest 1 SolarPunk automation project: {content[-1000:]}",
                "stream": False
            })
        
        if response.status_code == 200:
            idea = response.json().get('response')
            with open('data/self_builder_queue.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"topic": "Local Brain Idea", "info": idea}) + "\n")
            print("💡 Local Brain: New project queued.")
    except:
        print("⚠️ Local Brain: Offline. (Ensure Ollama is running for local processing)")

if __name__ == "__main__":
    process_locally()
