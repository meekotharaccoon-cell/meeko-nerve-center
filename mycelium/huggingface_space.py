#!/usr/bin/env python3
"""
Hugging Face Space Engine
===========================
Deploys a live interactive demo of the system to Hugging Face Spaces.
Anyone can visit the Space and interact with the system's intelligence.

The Space shows:
  - Live system stats pulled from the repo
  - The latest Gaza Rose art
  - Congressional trade lookup
  - Ask-the-system interface (powered by the same LLM)
  - Fork button + mission explanation

Hugging Face Spaces = free hosting, massive discoverability,
the exact audience (ML researchers, developers, open source people)
who would fork this, fund it, or write about it.

Creates/updates: meekotharaccoon/meeko-nerve-center Space
Uses HF Hub API to push app.py + requirements.txt
"""

import json, datetime, os, base64
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN   = os.environ.get('HF_TOKEN', '')
HF_USERNAME = os.environ.get('HF_USERNAME', 'meekotharaccoon')
SPACE_NAME  = 'meeko-nerve-center'
REPO_URL    = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

SPACE_ID = f'{HF_USERNAME}/{SPACE_NAME}'

def hf_api(method, path, body=None, timeout=30):
    if not HF_TOKEN: return None
    url = f'https://huggingface.co/api/{path}'
    headers = {
        'Authorization': f'Bearer {HF_TOKEN}',
        'Content-Type':  'application/json',
    }
    try:
        req = urllib_request.Request(url, headers=headers, method=method)
        if body: req.data = json.dumps(body).encode()
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[hf_space] API error {path[:50]}: {e}')
        return None

def push_file_to_space(filepath_in_space, content):
    """Push a file to the HF Space repo via the Hub API."""
    if not HF_TOKEN: return False
    encoded = base64.b64encode(content.encode()).decode()
    url = f'https://huggingface.co/api/spaces/{SPACE_ID}/upload/{filepath_in_space}'
    try:
        req = urllib_request.Request(
            url,
            data=json.dumps({'content': encoded, 'encoding': 'base64'}).encode(),
            headers={
                'Authorization': f'Bearer {HF_TOKEN}',
                'Content-Type': 'application/json',
            },
            method='POST'
        )
        with urllib_request.urlopen(req, timeout=30) as r:
            return r.status in (200, 201)
    except Exception as e:
        # Try alternative: direct git push via HF dataset API
        print(f'[hf_space] Upload error: {e}')
        return False

def load_stats():
    stats = {
        'health': 100, 'engines': 0, 'self_built': 0,
        'ideas': 0, 'passed': 0, 'trades': 0,
        'art': 0, 'pcrf': 0.0, 'uptime': 0,
    }
    try:
        h = json.loads((DATA / 'health_report.json').read_text())
        stats['health'] = h.get('score', 100)
    except: pass
    try:
        stats['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try:
        evo = json.loads((DATA / 'evolution_log.json').read_text())
        stats['self_built'] = len(evo.get('built', []))
    except: pass
    try:
        ledger = json.loads((DATA / 'idea_ledger.json').read_text())
        ideas  = ledger.get('ideas', {})
        il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
        stats['ideas']  = len(il)
        stats['passed'] = sum(1 for i in il if i.get('status') in ('passed','wired'))
    except: pass
    try:
        congress = json.loads((DATA / 'congress.json').read_text())
        trades   = congress if isinstance(congress, list) else congress.get('trades', [])
        stats['trades'] = len(trades)
    except: pass
    try:
        arts = json.loads((DATA / 'generated_art.json').read_text())
        al   = arts if isinstance(arts, list) else arts.get('art', [])
        stats['art'] = len(al)
    except: pass
    try:
        kofi = json.loads((DATA / 'kofi_events.json').read_text())
        ev   = kofi if isinstance(kofi, list) else kofi.get('events', [])
        total = sum(float(e.get('amount', 0)) for e in ev if e.get('type') in ('donation','Donation'))
        stats['pcrf'] = round(total * 0.70, 2)
    except: pass
    try:
        stats['uptime'] = (datetime.date.today() - datetime.date(2026, 2, 1)).days
    except: pass
    return stats

def generate_app_py(stats):
    return f'''import gradio as gr
import urllib.request, json, datetime

STATS = {json.dumps(stats)}
REPO  = "{REPO_URL}"
UPDATED = "{TODAY}"

def get_status():
    lines = [
        f"🌹 Meeko Nerve Center — Live Dashboard",
        f"Updated: {{UPDATED}} | Uptime: {{STATS.get('uptime',0)}} days\\n",
        f"🧠 System Health:     {{STATS.get('health',100)}}/100",
        f"⚡ Engines running:   {{STATS.get('engines',0)}}",
        f"🔧 Self-built:        {{STATS.get('self_built',0)}}",
        f"💡 Ideas tested:      {{STATS.get('ideas',0)}}",
        f"✅ Ideas implemented: {{STATS.get('passed',0)}}",
        f"⚠️  Trades flagged:   {{STATS.get('trades',0)}}",
        f"🎨 Gaza Rose art:     {{STATS.get('art',0)}} pieces",
        f"💚 To PCRF:           ${{STATS.get('pcrf',0):.2f}}",
        f"\\nFork it free: {{REPO}}",
    ]
    return "\\n".join(lines)

def ask_system(question):
    if not question.strip():
        return "Ask me anything about the system, the mission, or Palestinian solidarity tech."
    try:
        payload = json.dumps({{
            "model": "meta-llama/Llama-3.3-70B-Instruct:fastest",
            "max_tokens": 400,
            "messages": [
                {{"role": "system", "content": """You are Meeko Nerve Center, an autonomous AI
built for Palestinian solidarity and congressional accountability. You run on GitHub Actions
for free. You self-evolve. You fund Palestinian children\'s medical relief via art sales.
Answer questions about yourself, your mission, and how people can fork/use you.
GitHub: {REPO_URL}"""}},
                {{"role": "user", "content": question}}
            ]
        }}).encode()
        req = urllib.request.Request(
            "https://router.huggingface.co/v1/chat/completions",
            data=payload,
            headers={{"Content-Type": "application/json"}}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e:
        return f"System is processing. Try again in a moment. ({{e}})"

with gr.Blocks(
    title="Meeko Nerve Center",
    theme=gr.themes.Base(),
    css="body{{background:#0d0d0d;color:#f0f0f0}} .gradio-container{{max-width:800px;margin:auto}}"
) as demo:
    gr.Markdown("""# 🌹 Meeko Nerve Center\n> A self-evolving autonomous AI for accountability + Palestinian solidarity. $0/month. Open source. Running right now.""")

    with gr.Row():
        with gr.Column():
            gr.Markdown("## Live System Status")
            status_box = gr.Textbox(value=get_status, every=300, lines=12, label="", interactive=False)

    with gr.Row():
        with gr.Column():
            gr.Markdown("## Ask the System")
            question = gr.Textbox(placeholder="What does this system do? How do I fork it? What is PCRF?", label="Your question")
            answer   = gr.Textbox(label="Response", lines=6, interactive=False)
            ask_btn  = gr.Button("Ask", variant="primary")
            ask_btn.click(ask_system, inputs=question, outputs=answer)

    gr.Markdown(f"""---\n**[Fork this system free]({REPO_URL}/fork)** | [GitHub]({REPO_URL}) | [Ko-fi](https://ko-fi.com/meekotharaccoon) | [PCRF](https://www.pcrf.net) | AGPL-3.0""")

if __name__ == "__main__":
    demo.launch()
'''

def generate_readme():
    return f"""---
title: Meeko Nerve Center
emoji: 🌹
colorFrom: red
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: true
license: agpl-3.0
short_description: Self-evolving autonomous AI for accountability + Palestinian solidarity
tags:
  - autonomous-ai
  - open-source
  - palestine
  - accountability
  - self-evolving
  - github-actions
  - solarpunk
---

# 🌹 Meeko Nerve Center

A self-evolving autonomous AI that:
- Tracks congressional trades under the STOCK Act
- Generates Palestinian solidarity art (Gaza Rose series)
- Funds Palestinian children's medical relief (70% to PCRF)
- Writes its own code daily
- Heals its own bugs
- Applies for grants autonomously
- Runs for **$0/month** on GitHub Actions

**[Fork it free on GitHub]({REPO_URL})**

AGPL-3.0 — fork freely, improvements stay open source.
"""

def create_space_if_needed():
    """Create the HF Space if it doesn't exist."""
    if not HF_TOKEN: return False
    # Check if space exists
    url = f'https://huggingface.co/api/spaces/{SPACE_ID}'
    try:
        req = urllib_request.Request(url, headers={'Authorization': f'Bearer {HF_TOKEN}'})
        with urllib_request.urlopen(req, timeout=10) as r:
            if r.status == 200:
                print(f'[hf_space] Space exists: {SPACE_ID}')
                return True
    except:
        pass

    # Create it
    result = hf_api('POST', 'repos/create', {
        'type':    'space',
        'name':    SPACE_NAME,
        'private': False,
        'sdk':     'gradio',
    })
    if result:
        print(f'[hf_space] Created space: {SPACE_ID}')
        return True
    print(f'[hf_space] Could not create space (may need to create manually at huggingface.co/new-space)')
    return False

def run():
    print(f'\n[hf_space] Hugging Face Space Engine — {TODAY}')

    if not HF_TOKEN:
        print('[hf_space] No HF_TOKEN. Skipping.')
        return

    stats = load_stats()
    app_code = generate_app_py(stats)
    readme   = generate_readme()
    reqs     = 'gradio>=4.44.0\n'

    # Save locally first
    space_dir = ROOT / 'hf_space'
    space_dir.mkdir(exist_ok=True)
    try:
        (space_dir / 'app.py').write_text(app_code)
        (space_dir / 'README.md').write_text(readme)
        (space_dir / 'requirements.txt').write_text(reqs)
        print(f'[hf_space] Space files written to hf_space/')
    except Exception as e:
        print(f'[hf_space] Local write error: {e}')

    # Try to push to HF
    created = create_space_if_needed()
    if created:
        for fname, content in [('app.py', app_code), ('README.md', readme), ('requirements.txt', reqs)]:
            ok = push_file_to_space(fname, content)
            print(f'[hf_space] Push {fname}: {"ok" if ok else "failed (push manually from hf_space/ dir)"}')
    else:
        print(f'[hf_space] Files ready in hf_space/ — push manually:')
        print(f'[hf_space] huggingface-cli upload {SPACE_ID} hf_space/ . --repo-type space')

    print(f'[hf_space] Space URL: https://huggingface.co/spaces/{SPACE_ID}')

if __name__ == '__main__':
    run()
