#!/usr/bin/env python3
"""
HuggingFace Brain
==================
Connects the system to real AI inference via HuggingFace Inference Providers.
Free tier. OpenAI-compatible API. Hundreds of models.

What this unlocks:
  - System can now THINK, not just template
  - Generate original content with actual LLMs (DeepSeek, Llama, Mistral)
  - Generate images with FLUX (text-to-image, free tier)
  - Analyze data and produce insights, not just summaries
  - Write better cause content than any template
  - Summarize knowledge digests intelligently
  - Generate Etsy descriptions, YouTube scripts, social posts from actual AI

Requires:
  - HF_TOKEN secret in GitHub Actions (get free at huggingface.co/settings/tokens)
  - Fine-grained token with 'Make calls to Inference Providers' permission

Models used (all free tier):
  - meta-llama/Llama-3.3-70B-Instruct  (powerful, free, fast)
  - black-forest-labs/FLUX.1-schnell   (text-to-image, fast + free)

Outputs:
  - content/queue/ai_content_*.json    AI-generated posts ready to use
  - knowledge/ai_insights/latest.md    AI analysis of current system state
  - data/ai_images/                    Generated images (URLs)
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
CONT  = ROOT / 'content' / 'queue'

for d in [KB / 'ai_insights', CONT, DATA / 'ai_images']:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()
HF_TOKEN = os.environ.get('HF_TOKEN', '')

HF_API = 'https://router.huggingface.co/v1/chat/completions'
LLM_MODEL = 'meta-llama/Llama-3.3-70B-Instruct:fastest'

def ask_llm(prompt, system=None, max_tokens=500):
    """Ask HuggingFace LLM a question. Returns text response."""
    if not HF_TOKEN:
        print('[hf-brain] No HF_TOKEN found. Set it in GitHub Secrets.')
        return None
    
    messages = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt})
    
    payload = json.dumps({
        'model': LLM_MODEL,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': 0.7,
    }).encode()
    
    try:
        req = urllib_request.Request(
            HF_API,
            data=payload,
            headers={
                'Authorization': f'Bearer {HF_TOKEN}',
                'Content-Type': 'application/json',
            }
        )
        with urllib_request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[hf-brain] LLM error: {e}')
        return None

def generate_cause_post(context):
    """Generate an original Gaza Rose / humanitarian post."""
    system = """You are a humanitarian content writer for the Meeko Nerve Center.
Your mission: Palestine solidarity, Gaza Rose art project, open source technology as liberation.
70% of Gaza Rose proceeds go to PCRF (Palestinian Children's Relief Fund).
Write in a direct, human, non-preachy voice. Short. Powerful. Never manipulative.
Always end with something that gives people agency (a link, an action, or just hope)."""
    
    prompt = f"""Write a short social media post (under 200 words) about: {context}

Use these facts if relevant:
- Gaza Rose digital art: 70% to PCRF
- System is open source: github.com/meekotharaccoon-cell/meeko-nerve-center  
- SolarPunk dashboard: meekotharaccoon-cell.github.io/meeko-nerve-center/solarpunk.html
- Ko-fi for donations: include if appropriate

Return ONLY the post text. No explanation. No quotes around it."""
    
    return ask_llm(prompt, system=system, max_tokens=300)

def generate_system_insight():
    """Ask the AI to analyze the current system state and suggest next moves."""
    system = """You are the strategic brain of an autonomous humanitarian AI system.
You analyze data, find opportunities, and suggest actions that serve the mission:
bettering humanity, supporting Palestine, spreading open source tools.
Be specific. Be honest. Prioritize impact per effort."""
    
    # Read current system state
    state_files = [
        DATA / 'world_state.json',
        DATA / 'congress.json',
        DATA / 'jobs_today.json',
    ]
    
    context_parts = []
    for f in state_files:
        if f.exists():
            try:
                data = json.loads(f.read_text())
                # Give AI a summary, not the full file
                context_parts.append(f'{f.name}: {json.dumps(data, indent=None)[:500]}...')
            except:
                pass
    
    if not context_parts:
        context_parts = ['No data files found yet. System is in early state.']
    
    prompt = f"""Today is {TODAY}. Here is the current state of the Meeko Nerve Center:

{'\n'.join(context_parts)}

Based on this, answer:
1. What is the single most impactful thing the system should do TODAY?
2. What connection between these data sources is the system missing?
3. What should Meeko (the human) do in the next 30 minutes that would have the biggest effect?

Be direct. Be specific. Max 200 words total."""
    
    return ask_llm(prompt, system=system, max_tokens=300)

def generate_etsy_listing(artwork_title, artwork_source):
    """Generate an optimized Etsy listing description."""
    system = "Etsy SEO expert specializing in cause-driven digital art. Write for both humans and search."
    
    prompt = f"""Write an Etsy listing description for a Gaza Rose digital art download.
The inspiration artwork is: {artwork_title} from {artwork_source}.

Requirements:
- Title: SEO-optimized (include: Palestine, Gaza Rose, digital download, art print)
- Description: 100-150 words, emotional but not manipulative
- Mention: 70% of proceeds go to PCRF
- Tags: list 13 comma-separated Etsy tags
- Return as JSON: {{title, description, tags}}"""
    
    result = ask_llm(prompt, system=system, max_tokens=400)
    if result:
        try:
            # Try to parse JSON from response
            start = result.find('{')
            end   = result.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
    return {'title': f'Gaza Rose Art — {artwork_title}', 'description': result or '', 'tags': []}

def run():
    print(f'[hf-brain] HuggingFace Brain — {TODAY}')
    
    if not HF_TOKEN:
        print('[hf-brain] HF_TOKEN not set. Add it to GitHub Secrets.')
        print('[hf-brain] Get one free at: huggingface.co/settings/tokens')
        print('[hf-brain] Permission needed: Make calls to Inference Providers')
        return {'error': 'HF_TOKEN not configured'}
    
    results = {'date': TODAY, 'generated': []}
    
    # 1. Generate daily cause post
    print('[hf-brain] Generating cause post...')
    contexts = [
        'a child in Gaza seeing their first flower after weeks of bombardment',
        'the connection between open source software and human liberation',
        'why art persists through siege and what that means',
    ]
    import random
    context = random.choice(contexts)
    post = generate_cause_post(context)
    if post:
        results['generated'].append({'type': 'cause_post', 'text': post, 'context': context})
        print(f'[hf-brain] Cause post generated ({len(post)} chars)')
    
    # 2. Generate system insight
    print('[hf-brain] Generating system insight...')
    insight = generate_system_insight()
    if insight:
        results['insight'] = insight
        (KB / 'ai_insights' / f'{TODAY}.md').write_text(f'# AI System Insight — {TODAY}\n\n{insight}')
        (KB / 'ai_insights' / 'latest.md').write_text(f'# AI System Insight — {TODAY}\n\n{insight}')
        print(f'[hf-brain] Insight generated')
    
    # 3. Save content queue
    if results['generated']:
        posts = [{
            'platform': 'mastodon',
            'type': 'ai_generated',
            'text': r['text'],
            'context': r.get('context', ''),
        } for r in results['generated']]
        (CONT / f'ai_content_{TODAY}.json').write_text(json.dumps(posts, indent=2))
    
    print(f'[hf-brain] Done. {len(results["generated"])} pieces of content generated.')
    return results

if __name__ == '__main__':
    run()
