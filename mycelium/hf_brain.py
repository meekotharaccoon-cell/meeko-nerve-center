#!/usr/bin/env python3
"""
HuggingFace Brain
==================
Free AI inference via HuggingFace Inference Providers.
This upgrades the entire system from template-based to actually intelligent.

What this unlocks:
  - Generate real content with LLMs (DeepSeek, Llama, Qwen)
  - Generate images with FLUX (Gaza Rose art variations, visual content)
  - Summarize knowledge digests intelligently
  - Write better YouTube scripts than templates
  - Analyze congress trades with reasoning
  - Generate captions for art+cause posts

Requires: HF_TOKEN in GitHub Secrets (free tier available)
Get token: huggingface.co/settings/tokens

Models used (all free tier friendly):
  - Text: meta-llama/Llama-3.2-3B-Instruct (fast, free)
  - Text: Qwen/Qwen2.5-7B-Instruct (better quality)
  - Image: black-forest-labs/FLUX.1-schnell (fast image gen)

Outputs:
  - content/queue/ai_content_*.json   AI-generated posts
  - knowledge/brain/latest.md         AI analysis of current state
  - data/hf_status.json               Model availability check
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import HTTPError

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
CONT  = ROOT / 'content' / 'queue'

for d in [KB / 'brain', CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()
HF_TOKEN = os.environ.get('HF_TOKEN', '')

HF_BASE = 'https://router.huggingface.co/v1'

# Models - ordered by preference (fallback if one is unavailable)
TEXT_MODELS = [
    'meta-llama/Llama-3.2-3B-Instruct',  # fast, free tier
    'Qwen/Qwen2.5-7B-Instruct',           # better quality
    'mistralai/Mistral-7B-Instruct-v0.3', # reliable fallback
]

IMAGE_MODELS = [
    'black-forest-labs/FLUX.1-schnell',   # fast
    'stabilityai/stable-diffusion-xl-base-1.0',  # fallback
]

def hf_chat(prompt, system=None, model=None, max_tokens=500):
    """Call HuggingFace chat completion. Returns text or None."""
    if not HF_TOKEN:
        print('[hf] No HF_TOKEN found — add to GitHub Secrets')
        return None

    models_to_try = [model] if model else TEXT_MODELS

    messages = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt})

    for m in models_to_try:
        try:
            payload = json.dumps({
                'model':      m,
                'messages':   messages,
                'max_tokens': max_tokens,
                'temperature': 0.7,
            }).encode()

            req = urllib_request.Request(
                f'{HF_BASE}/chat/completions',
                data=payload,
                headers={
                    'Authorization': f'Bearer {HF_TOKEN}',
                    'Content-Type':  'application/json',
                    'User-Agent':    'meeko-nerve-center/2.0',
                },
                method='POST'
            )
            with urllib_request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
                text = data['choices'][0]['message']['content'].strip()
                print(f'[hf] ✅ {m}: {len(text)} chars')
                return text
        except HTTPError as e:
            print(f'[hf] {m} HTTP {e.code}: {e.reason}')
        except Exception as e:
            print(f'[hf] {m} error: {e}')

    return None

def generate_youtube_script(topic, context=''):
    """Generate a YouTube Short script using actual AI."""
    system = """You write 60-second YouTube Short scripts for a humanitarian tech creator.
Tone: honest, direct, not preachy. End with one specific action.
Format: Hook (5s) | Context (20s) | The point (25s) | Action (10s)
No hashtags in script. Under 150 words total."""

    prompt = f"Write a YouTube Short script about: {topic}\n\nContext: {context}" if context else f"Write a YouTube Short script about: {topic}"
    return hf_chat(prompt, system=system, max_tokens=300)

def analyze_congress_trades(trades_summary):
    """AI analysis of congress trading data."""
    system = """You analyze congressional stock trades for suspicious patterns.
Be factual. Note conflicts of interest. Keep it under 100 words.
Don't speculate beyond the data. Flag what's notable."""
    return hf_chat(f'Analyze these recent congressional trades: {trades_summary}', system=system, max_tokens=200)

def generate_art_caption(artwork_title, artwork_artist, cause_context):
    """Generate caption pairing museum art with Gaza Rose mission."""
    system = """You write social media captions pairing museum art with humanitarian causes.
Tone: poetic but grounded. Not sappy. Under 80 words.
Always end with a concrete action (donate link, fork link, etc)."""
    prompt = f'Art: "{artwork_title}" by {artwork_artist}\nCause context: {cause_context}'
    return hf_chat(prompt, system=system, max_tokens=150)

def summarize_daily_digest():
    """Read today\'s world intelligence and generate a human-readable briefing."""
    system = """You summarize daily intelligence briefings for a humanitarian technologist.
Focus on: what matters for the mission, what needs action, what\'s hopeful.
Under 200 words. Bullet points. No filler."""

    # Try to read latest world digest
    world_path = KB / 'world' / 'latest.md'
    digest_path = KB / f'{datetime.date.today().isoformat()}_v2.md'

    context = ''
    if world_path.exists():
        context += world_path.read_text()[:1500]
    if digest_path.exists():
        context += digest_path.read_text()[:1000]

    if not context:
        return None

    return hf_chat(f'Summarize this intelligence for today\'s briefing:\n\n{context}', system=system, max_tokens=300)

def generate_solarpunk_post():
    """Generate a SolarPunk-themed social post about today\'s data."""
    system = """You write SolarPunk social media posts: hopeful, grounded, specific.
SolarPunk = technology + ecology + community + mutual aid.
Avoid: vague optimism, corporate greenwashing, doom.
Include: one specific fact from the data. Under 200 chars for Mastodon."""

    # Pull today\'s carbon/space/earthquake context
    context_parts = []
    carbon_path = KB / 'carbon' / 'latest.md'
    space_path  = KB / 'spaceflight' / 'latest.md'
    if carbon_path.exists(): context_parts.append(carbon_path.read_text()[:300])
    if space_path.exists():  context_parts.append(space_path.read_text()[:300])

    context = '\n'.join(context_parts) if context_parts else 'Focus on: the ISS crew, or clean energy, or open source technology'
    return hf_chat(f'Write a SolarPunk post using this data:\n{context}', system=system, max_tokens=150)

def run():
    print(f'[hf] HuggingFace Brain — {TODAY}')

    if not HF_TOKEN:
        print('[hf] HF_TOKEN not set. Add to GitHub Secrets to enable AI generation.')
        print('[hf] Get token: https://huggingface.co/settings/tokens')
        (DATA / 'hf_status.json').write_text(json.dumps({
            'date':   TODAY,
            'status': 'no_token',
            'note':   'Add HF_TOKEN to GitHub Secrets to enable AI generation',
        }))
        return

    results = {'date': TODAY, 'generated': []}
    posts = []

    # 1. Daily briefing
    print('[hf] Generating daily briefing...')
    briefing = summarize_daily_digest()
    if briefing:
        (KB / 'brain' / f'{TODAY}_briefing.md').write_text(f'# AI Briefing — {TODAY}\n\n{briefing}')
        (KB / 'brain' / 'latest.md').write_text(f'# AI Briefing — {TODAY}\n\n{briefing}')
        results['generated'].append('daily_briefing')
        print(f'[hf] Briefing: {briefing[:100]}...')

    # 2. YouTube script
    print('[hf] Generating YouTube script...')
    # Pull today\'s most interesting topic from available data
    congress_path = DATA / 'congress.json'
    topic = 'how open source tools are changing humanitarian aid'
    if congress_path.exists():
        try:
            congress = json.loads(congress_path.read_text())
            flagged = congress.get('flagged', [])
            if flagged:
                ticker = flagged[0].get('ticker', 'defense stocks')
                topic = f'your representative traded {ticker} and here\'s what that means'
        except: pass

    script = generate_youtube_script(topic)
    if script:
        scripts_path = ROOT / 'content' / 'youtube'
        scripts_path.mkdir(parents=True, exist_ok=True)
        (scripts_path / f'{TODAY}_ai_script.md').write_text(f'# YouTube Short Script — {TODAY}\n\n{script}')
        (scripts_path / 'latest_ai.md').write_text(f'# YouTube Short Script — {TODAY}\n\n{script}')
        results['generated'].append('youtube_script')

    # 3. SolarPunk post
    print('[hf] Generating SolarPunk post...')
    sp_post = generate_solarpunk_post()
    if sp_post:
        posts.append({'platform': 'mastodon', 'type': 'solarpunk_ai', 'text': sp_post})
        results['generated'].append('solarpunk_post')

    # Save content
    if posts:
        (CONT / f'hf_ai_{TODAY}.json').write_text(json.dumps(posts, indent=2))

    (DATA / 'hf_status.json').write_text(json.dumps({
        'date':      TODAY,
        'status':    'active',
        'generated': results['generated'],
    }, indent=2))

    print(f'[hf] Done. Generated: {results["generated"]}')
    return results

if __name__ == '__main__':
    run()
