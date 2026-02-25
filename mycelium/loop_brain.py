#!/usr/bin/env python3
"""
Loop Brain — the strategy layer.

Reads:
  data/what_works.json     (signal_tracker output)
  data/signals.json        (raw signal history)
  knowledge/LATEST_DIGEST.md (today's harvested knowledge)
  content/queue/latest.json  (what was posted recently)

Thinks:
  If Ollama is running locally (port 11434), asks it for strategy.
  If running in GitHub Actions (cloud), uses rule-based logic.
  Either way produces the same output format.

Writes:
  data/strategy.json  — what to do next, consumed by humanitarian_content.py

The strategy output controls:
  - Which crisis to emphasize today
  - Which post templates to use more vs. less
  - What time-of-day angle to lean on
  - Whether to push gallery, fork guide, Ko-fi, or direct donation
  - What knowledge topics to weave into posts
"""

import os, json, datetime, urllib.request, urllib.error
from pathlib import Path

ROOT     = Path(__file__).parent.parent
DATA     = ROOT / 'data'
KB       = ROOT / 'knowledge'
CONTENT  = ROOT / 'content'
TODAY    = datetime.date.today().isoformat()
DAY_NUM  = datetime.date.today().toordinal()  # for deterministic rotation

DATA.mkdir(exist_ok=True)

def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return default if default is not None else {}


# ── Load all inputs ────────────────────────────────────────────────────────
what_works = load_json(DATA / 'what_works.json')
signals    = load_json(DATA / 'signals.json')

digest_text = ''
digest_path = KB / 'LATEST_DIGEST.md'
if digest_path.exists():
    digest_text = digest_path.read_text(encoding='utf-8')[:3000]

recent_posts = load_json(CONTENT / 'queue' / 'latest.json', default=[])


# ── Rule-based strategy (runs anywhere, no Ollama needed) ──────────────────
def rule_based_strategy():
    """
    Deterministic strategy built from signal data.
    Runs in GitHub Actions (no Ollama). Produces same schema as Ollama path.
    """
    summary    = what_works.get('summary', {})
    traffic    = what_works.get('traffic', {})
    top_posts  = what_works.get('top_posts', [])
    recs       = what_works.get('recommendations', [])

    total_views  = summary.get('total_14d_views', 0)
    total_unique = summary.get('total_14d_unique', 0)
    top_repo     = traffic.get('winner', 'meeko-nerve-center')
    top_engage   = summary.get('top_mastodon_engagement', 0)

    # Crisis rotation — cycle through all 3, but weight toward one
    # If gallery (Gaza) is the traffic winner → emphasise Gaza
    # Otherwise rotate daily: Gaza Mon/Thu, Congo Tue/Fri, Sudan Wed/Sat, all Sun
    crises = ['Gaza', 'Congo (DRC)', 'Sudan']
    if 'gaza' in (top_repo or '').lower():
        primary_crisis = 'Gaza'
    else:
        primary_crisis = crises[DAY_NUM % 3]

    # Post template weighting based on engagement
    # Templates: 'awareness', 'gallery', 'fork', 'info', 'punchy'
    # Default weights
    weights = {'awareness': 2, 'gallery': 3, 'fork': 2, 'info': 1, 'punchy': 2}

    # If gallery traffic is high → push gallery more
    gallery_views = (traffic.get('by_repo', {})
                     .get('gaza-rose-gallery', {})
                     .get('views', 0))
    if gallery_views > 50:
        weights['gallery'] += 2
        weights['punchy']  += 1

    # If Mastodon engagement is low → switch to punchier content
    if top_engage < 3:
        weights['punchy']  += 2
        weights['awareness'] = max(1, weights['awareness'] - 1)

    # If zero traffic everywhere → fork/spread the network
    if total_views < 10:
        weights['fork'] += 3

    # Revenue channel to push today
    # Rotate: gallery → ko-fi → fork-guide → sponsor
    channels = ['gallery', 'kofi', 'fork_guide', 'sponsor']
    push_channel = channels[DAY_NUM % len(channels)]

    # Pull a relevant knowledge snippet to weave into posts
    knowledge_hook = ''
    if digest_text:
        lines = [l.strip() for l in digest_text.split('\n')
                 if l.strip() and l.startswith('-') and len(l) > 30]
        if lines:
            knowledge_hook = lines[DAY_NUM % len(lines)].lstrip('- ').strip()

    return {
        'generated':      TODAY,
        'method':         'rule-based',
        'primary_crisis': primary_crisis,
        'all_crises':     crises,
        'post_weights':   weights,
        'push_channel':   push_channel,
        'knowledge_hook': knowledge_hook,
        'signals_summary': {
            'total_14d_views':   total_views,
            'total_14d_unique':  total_unique,
            'top_repo':          top_repo,
            'top_engagement':    top_engage,
        },
        'recommendations': recs,
        'reasoning': (
            f"Primary crisis: {primary_crisis} (day rotation + traffic signals). "
            f"Push channel: {push_channel}. "
            f"Post weights favor: {max(weights, key=weights.get)}. "
            f"Knowledge hook: '{knowledge_hook[:60]}'"
        ),
    }


# ── Ollama strategy (runs locally when Ollama is available) ────────────────
def ollama_strategy():
    """
    Ask local Ollama for a richer strategy.
    Falls back to rule_based_strategy() if Ollama is not running.
    """
    try:
        # Check if Ollama is running
        urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2)
    except Exception:
        print('  [brain] Ollama not running — using rule-based strategy')
        return rule_based_strategy()

    context = f"""
You are the strategy brain for an autonomous humanitarian AI system.
Mission: raise money for Gaza, Congo, and Sudan through art sales, digital products, and donations.
All revenue is split 70% to verified charities, 30% operational.

Today is {TODAY}.

Signal data (what's working):
{json.dumps(what_works.get('summary', {}), indent=2)}

Top performing content:
{json.dumps(what_works.get('top_posts', [])[:3], indent=2)}

Traffic by page:
{json.dumps(what_works.get('traffic', {}).get('by_repo', {}), indent=2)}

Latest knowledge digest snippet:
{digest_text[:800]}

Recent posts sent:
{json.dumps([p.get('text','')[:80] for p in recent_posts[:5]], indent=2)}

Based on this data, respond ONLY with a JSON object (no markdown, no explanation) with these exact keys:
{{
  "primary_crisis": "Gaza" or "Congo (DRC)" or "Sudan",
  "post_weights": {{"awareness": 1-5, "gallery": 1-5, "fork": 1-5, "info": 1-5, "punchy": 1-5}},
  "push_channel": "gallery" or "kofi" or "fork_guide" or "sponsor",
  "knowledge_hook": "one sentence from today's knowledge to weave into posts",
  "reasoning": "2 sentences explaining the strategy"
}}
"""

    try:
        payload = json.dumps({
            'model': 'mistral',
            'prompt': context,
            'stream': False,
            'options': {'temperature': 0.3, 'num_predict': 400}
        }).encode()

        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())

        raw = resp.get('response', '').strip()
        # Strip markdown fences if present
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        raw = raw.strip()

        ollama_result = json.loads(raw)
        ollama_result['generated'] = TODAY
        ollama_result['method']    = 'ollama'
        ollama_result['all_crises'] = ['Gaza', 'Congo (DRC)', 'Sudan']
        ollama_result['signals_summary'] = what_works.get('summary', {})
        ollama_result['recommendations'] = what_works.get('recommendations', [])
        print(f'  [brain] Ollama strategy: {ollama_result["reasoning"][:80]}')
        return ollama_result

    except Exception as e:
        print(f'  [brain] Ollama parse error: {e} — falling back to rule-based')
        return rule_based_strategy()


# ── Run ────────────────────────────────────────────────────────────────────
print('\n' + '='*52)
print('  LOOP BRAIN — Building Strategy')
print(f'  {TODAY}')
print('='*52)

# Try Ollama first, fall back to rules
strategy = ollama_strategy()

# Save
strategy_path = DATA / 'strategy.json'
strategy_path.write_text(json.dumps(strategy, indent=2), encoding='utf-8')

print(f'\n  Primary crisis today: {strategy["primary_crisis"]}')
print(f'  Push channel: {strategy["push_channel"]}')
print(f'  Method: {strategy["method"]}')
print(f'  Reasoning: {strategy.get("reasoning","")[:100]}')
print(f'\n  Strategy saved to data/strategy.json')
print('='*52)
