#!/usr/bin/env python3
"""
LOCAL-GITHUB BRIDGE
====================
Connects your local Ollama AI stack to the GitHub organism.
Runs daily - supplements the GitHub Actions workflows with local AI power.

What it does:
- Uses local Mistral (free, private) for analysis instead of OpenRouter (costs tokens)
- Syncs local AI knowledge to GitHub brain repo
- Monitors investment systems and reports to morning briefing
- Runs more compute-heavy tasks that don't fit in GitHub's 6-hour limit

Run: python LOCAL_GITHUB_BRIDGE.py
Or add to Windows Task Scheduler for daily automation.
"""
import os, json, requests, subprocess
from datetime import datetime, timezone
from pathlib import Path

DESKTOP    = Path(r"C:\Users\meeko\Desktop")
GH_TOKEN   = os.environ.get('CONDUCTOR_TOKEN', '')  # set after running GRAND_SETUP_WIZARD
OR_KEY     = os.environ.get('OPENROUTER_KEY', '')
BRAIN_REPO = 'meekotharaccoon-cell/meeko-brain'
KNOWLEDGE  = DESKTOP / 'MYCELIUM_KNOWLEDGE_BASE.json'

def ask_local_ollama(prompt, model='mistral'):
    """Use LOCAL Mistral - no API cost, no token limit, private."""
    try:
        r = requests.post('http://localhost:11434/api/generate',
            json={'model': model, 'prompt': prompt, 'stream': False},
            timeout=60)
        return r.json().get('response', '')
    except Exception as e:
        return f"Ollama unavailable: {e}"

def ask_openrouter(prompt):
    """Fallback to OpenRouter if Ollama is down."""
    if not OR_KEY: return "No OpenRouter key"
    try:
        r = requests.post('https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OR_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'openai/gpt-4o-mini', 'messages': [{'role':'user','content':prompt}], 'max_tokens': 500},
            timeout=20)
        return r.json()['choices'][0]['message']['content']
    except: return "AI unavailable"

def sync_to_brain():
    """Push local knowledge to GitHub brain repo."""
    if not GH_TOKEN: 
        print("[Bridge] No CONDUCTOR_TOKEN - run GRAND_SETUP_WIZARD first")
        return False
    try:
        with open(KNOWLEDGE) as f:
            knowledge = json.load(f)
        # Add local AI status
        knowledge['local_ai_sync'] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ollama_status': check_ollama(),
            'local_stack': 'running'
        }
        # Push to brain repo via GitHub API
        import base64
        content = base64.b64encode(json.dumps(knowledge, indent=2).encode()).decode()
        # Get current SHA
        r = requests.get(
            f'https://api.github.com/repos/{BRAIN_REPO}/contents/organism_knowledge.json',
            headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github+json'},
            timeout=15)
        sha = r.json().get('sha', '') if r.status_code == 200 else ''
        payload = {
            'message': f'local bridge sync {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")}',
            'content': content
        }
        if sha: payload['sha'] = sha
        r2 = requests.put(
            f'https://api.github.com/repos/{BRAIN_REPO}/contents/organism_knowledge.json',
            headers={'Authorization': f'token {GH_TOKEN}', 'Content-Type': 'application/json'},
            json=payload, timeout=15)
        if r2.status_code in (200, 201):
            print("[Bridge] Knowledge synced to GitHub brain")
            return True
        else:
            print(f"[Bridge] Brain sync failed: {r2.status_code}")
            return False
    except Exception as e:
        print(f"[Bridge] Sync error: {e}")
        return False

def check_ollama():
    """Check if Ollama is running."""
    try:
        r = requests.get('http://localhost:11434/api/tags', timeout=5)
        models = [m['name'] for m in r.json().get('models', [])]
        return {'running': True, 'models': models}
    except:
        return {'running': False, 'models': []}

def run_local_analysis():
    """Run analysis with local AI, save results for morning briefing."""
    print("[Bridge] Running local AI analysis...")
    
    prompt = """You are Meeko's AI system analyst. Analyze the current state of the Gaza Rose Gallery system.
    
Current state:
- Gallery: 56 artworks at $1 each, 70% to PCRF
- Revenue: $0 (no sales yet - distribution problem not product problem)  
- Emails sent: PCRF, Open Collective, Mozilla, Tech4Palestine, Cloudinary, Strike, Awesome Foundation, Fractured Atlas, Creative Capital, Wikimedia, Harvestworks
- New page: Art + Guides + Rights + Fork all on one page, no friction
- 8 GitHub repos active with daily autonomous workflows
- Missing: GMAIL_APP_PASSWORD (unlocks all automation)

Give 3 specific, actionable insights Meeko should know this morning. Be direct, honest, brief."""

    response = ask_local_ollama(prompt)
    if 'unavailable' in response.lower():
        response = ask_openrouter(prompt)
    
    result = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'model': 'mistral (local)',
        'analysis': response
    }
    
    with open(DESKTOP / 'local_analysis.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[Bridge] Analysis complete")
    print(f"  {response[:200]}...")
    return response

def run():
    print(f"\n{'='*50}")
    print("  LOCAL-GITHUB BRIDGE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    ollama_status = check_ollama()
    print(f"[Bridge] Ollama: {'RUNNING' if ollama_status['running'] else 'OFFLINE'}")
    if ollama_status['running']:
        print(f"  Models: {', '.join(ollama_status['models'])}")
    
    run_local_analysis()
    sync_to_brain()
    
    print("\n[Bridge] Complete. Run again tomorrow or add to Task Scheduler.")
    print(f"{'='*50}\n")

if __name__ == '__main__':
    run()
