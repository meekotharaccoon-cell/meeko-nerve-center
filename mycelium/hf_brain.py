#!/usr/bin/env python3
"""
HuggingFace Brain
Fix: backslash not allowed inside f-string expressions (Python 3.11).
Pattern was: f"...{chr(10).join(context_parts)}..." — moved join to a pre-assigned variable.
"""

import json, datetime, os, random
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
CONT  = ROOT / 'content' / 'queue'

for p in [KB / 'ai_insights', CONT, DATA / 'ai_images']:
    p.mkdir(parents=True, exist_ok=True)

TODAY     = datetime.date.today().isoformat()
HF_TOKEN  = os.environ.get('HF_TOKEN', '')
HF_API    = 'https://router.huggingface.co/v1/chat/completions'
LLM_MODEL = 'meta-llama/Llama-3.3-70B-Instruct:fastest'

def ask_llm(prompt, system=None, max_tokens=500):
    if not HF_TOKEN:
        print('[hf-brain] No HF_TOKEN found.')
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
                'Authorization': 'Bearer ' + HF_TOKEN,
                'Content-Type': 'application/json',
            }
        )
        with urllib_request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print('[hf-brain] LLM error: ' + str(e))
        return None

def generate_cause_post(context):
    system = (
        'You are a humanitarian content writer for the Meeko Nerve Center.\n'
        'Mission: Palestine solidarity, Gaza Rose art, open source as liberation.\n'
        '70% of Gaza Rose proceeds go to PCRF.\n'
        'Direct, human, non-preachy voice. Short. Powerful.'
    )
    prompt = 'Write a short social media post (under 200 words) about: ' + context + '\n\nReturn ONLY the post text.'
    return ask_llm(prompt, system=system, max_tokens=300)

def generate_system_insight():
    system = (
        'You are the strategic brain of an autonomous humanitarian AI system.\n'
        'Analyze data, find opportunities, suggest actions that serve:\n'
        'bettering humanity, supporting Palestine, spreading open source tools.'
    )
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
                context_parts.append(f.name + ': ' + json.dumps(data)[:500] + '...')
            except:
                pass
    if not context_parts:
        context_parts = ['No data files found yet.']
    # Pre-assign newline — backslash not allowed inside f-string {} in Python 3.11
    nl = '\n'
    context_block = nl.join(context_parts)
    prompt = (
        'Today is ' + TODAY + '. System state:\n\n' +
        context_block +
        '\n\nAnswer:\n'
        '1. Most impactful thing TODAY?\n'
        '2. Missing data connection?\n'
        '3. What should Meeko do in the next 30 minutes?\n'
        'Be direct. Max 200 words.'
    )
    return ask_llm(prompt, system=system, max_tokens=300)

def generate_etsy_listing(artwork_title, artwork_source):
    system = 'Etsy SEO expert specializing in cause-driven digital art.'
    prompt = (
        'Write an Etsy listing for Gaza Rose digital art download.\n'
        'Inspiration: ' + artwork_title + ' from ' + artwork_source + '\n'
        '70% of proceeds go to PCRF. Palestine keywords. Emotional description.\n'
        'Return JSON: {title, description, tags}'
    )
    result = ask_llm(prompt, system=system, max_tokens=400)
    if result:
        try:
            start = result.find('{')
            end   = result.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except:
            pass
    return {'title': 'Gaza Rose Art \u2014 ' + artwork_title, 'description': result or '', 'tags': []}

def run():
    print('[hf-brain] HuggingFace Brain \u2014 ' + TODAY)
    if not HF_TOKEN:
        print('[hf-brain] HF_TOKEN not set. Get free token: huggingface.co/settings/tokens')
        return {'error': 'HF_TOKEN not configured'}
    results = {'date': TODAY, 'generated': []}
    contexts = [
        'a child in Gaza seeing their first flower after weeks of bombardment',
        'the connection between open source software and human liberation',
        'why art persists through siege and what that means',
    ]
    context = random.choice(contexts)
    post = generate_cause_post(context)
    if post:
        results['generated'].append({'type': 'cause_post', 'text': post, 'context': context})
        print('[hf-brain] Cause post: ' + str(len(post)) + ' chars')
    insight = generate_system_insight()
    if insight:
        results['insight'] = insight
        (KB / 'ai_insights' / (TODAY + '.md')).write_text('# AI Insight \u2014 ' + TODAY + '\n\n' + insight)
        (KB / 'ai_insights' / 'latest.md').write_text('# AI Insight \u2014 ' + TODAY + '\n\n' + insight)
        print('[hf-brain] Insight: ' + str(len(insight)) + ' chars')
    if results['generated']:
        posts = [
            {'platform': 'mastodon', 'type': 'ai_generated',
             'text': item['text'], 'context': item.get('context', '')}
            for item in results['generated']
        ]
        (CONT / ('ai_content_' + TODAY + '.json')).write_text(json.dumps(posts, indent=2))
    print('[hf-brain] Done. ' + str(len(results['generated'])) + ' pieces generated.')
    return results

if __name__ == '__main__':
    run()
