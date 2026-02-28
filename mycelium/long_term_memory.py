#!/usr/bin/env python3
"""
Long-Term Memory Engine
========================
Every LLM call in every engine starts from zero.
No engine remembers what worked last week.
This is the biggest invisible bottleneck in the whole system.

This engine builds and maintains a persistent knowledge layer
that every other engine reads before making LLM calls.

What it stores:
  1. What content performed best (tone, length, topics)
  2. Which grant applications got responses
  3. Which press contacts replied
  4. Which crypto signals were accurate
  5. Which ideas the system built vs rejected and why
  6. What the system tried that failed
  7. Recurring patterns in world events
  8. Donor preferences and response patterns
  9. What the LLM generates well vs poorly
  10. Compounding insights — things that connect across domains

Format: data/long_term_memory.json
Each engine prepends: memory = load_memory(); context = memory.get_context('engine_name')
Result: every engine gets smarter every day instead of
starting fresh every single time.
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN = os.environ.get('HF_TOKEN', '')

MEMORY_PATH = DATA / 'long_term_memory.json'

MEMORY_SCHEMA = {
    'version':   1,
    'updated':   TODAY,
    'contexts':  {},   # engine_name -> context string
    'patterns':  [],   # recurring insights
    'failures':  [],   # what didn't work
    'wins':      [],   # what worked well
    'signals_accuracy': {},   # coin_id -> hit_rate
    'content_patterns': {},   # platform -> {best_tone, best_length, best_topics}
    'donor_patterns':   {},   # segment -> response_rate
    'press_patterns':   {},   # outlet_type -> response_rate
    'grant_patterns':   {},   # grant_type -> success_signals
    'world_patterns':   [],   # recurring event types
    'meta': {
        'total_ideas_processed': 0,
        'total_signals_generated': 0,
        'total_art_generated': 0,
        'system_age_days': 0,
        'last_evolution_date': '',
        'strongest_engines': [],
        'weakest_engines': [],
    }
}

def load_memory():
    if MEMORY_PATH.exists():
        try: return json.loads(MEMORY_PATH.read_text())
        except: pass
    return dict(MEMORY_SCHEMA)

def save_memory(mem):
    mem['updated'] = TODAY
    try: MEMORY_PATH.write_text(json.dumps(mem, indent=2))
    except Exception as e:
        print(f'[memory] Save error: {e}')

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

# ── Data harvesters ───────────────────────────────────────────────────────────

def harvest_content_patterns(mem):
    perf = load(DATA / 'content_performance.json')
    if not perf: return
    for platform in ('mastodon', 'bluesky'):
        platform_data = perf.get(platform, {})
        top_posts = platform_data.get('top_posts', [])
        if not top_posts: continue
        # Find common patterns in top posts
        lengths = [len(p.get('text','')) for p in top_posts]
        avg_len = sum(lengths)//max(len(lengths),1)
        mem.setdefault('content_patterns', {})[platform] = {
            'avg_top_length': avg_len,
            'sample_top':     top_posts[0].get('text','')[:100] if top_posts else '',
            'updated':        TODAY,
        }

def harvest_signal_accuracy(mem):
    report = load(DATA / 'validation_report.json')
    for r in report.get('results', []):
        if r.get('check') == 'signal_accuracy':
            mem['signals_accuracy']['overall_accuracy'] = r.get('accuracy', 0)
            mem['signals_accuracy']['updated'] = TODAY

def harvest_press_patterns(mem):
    fu_log = load(DATA / 'press_followup_log.json').get('contacts', {})
    replied  = sum(1 for v in fu_log.values() if v.get('status') == 'replied')
    total    = len(fu_log)
    if total > 0:
        mem['press_patterns']['overall_reply_rate'] = round(replied/total*100)
        mem['press_patterns']['total_contacted'] = total
        mem['press_patterns']['updated'] = TODAY

def harvest_grant_patterns(mem):
    submitted = load(DATA / 'grant_submissions.json').get('submitted', [])
    mem['grant_patterns']['total_submitted'] = len(submitted)
    mem['grant_patterns']['grants'] = [
        {'name': s.get('grant_name',''), 'date': s.get('date',''), 'method': s.get('method','')}
        for s in submitted[-5:]
    ]
    mem['grant_patterns']['updated'] = TODAY

def harvest_meta(mem):
    # Ideas
    ledger = load(DATA / 'idea_ledger.json')
    ideas  = ledger.get('ideas', {})
    il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
    mem['meta']['total_ideas_processed'] = len(il)

    # Signals
    history = load(DATA / 'crypto_signals_history.json', [])
    mem['meta']['total_signals_generated'] = len(history)

    # Art
    arts = load(DATA / 'generated_art.json')
    al   = arts if isinstance(arts, list) else arts.get('art', [])
    mem['meta']['total_art_generated'] = len(al)

    # Age
    try:
        start = datetime.date(2026, 2, 1)
        mem['meta']['system_age_days'] = (datetime.date.today() - start).days
    except: pass

    # Engine health
    confidence = load(DATA / 'engine_confidence.json', {})
    if confidence:
        sorted_engines = sorted(confidence.items(), key=lambda x: x[1], reverse=True)
        mem['meta']['strongest_engines'] = [e for e, _ in sorted_engines[:3]]
        mem['meta']['weakest_engines']   = [e for e, _ in sorted_engines[-3:]]

def synthesize_insights(mem):
    """Ask LLM to find cross-domain patterns and compress into engine contexts."""
    if not HF_TOKEN: return

    summary = {
        'age_days':         mem['meta'].get('system_age_days', 0),
        'total_ideas':      mem['meta'].get('total_ideas_processed', 0),
        'total_signals':    mem['meta'].get('total_signals_generated', 0),
        'signal_accuracy':  mem['signals_accuracy'].get('overall_accuracy', 'unknown'),
        'press_reply_rate': mem['press_patterns'].get('overall_reply_rate', 'unknown'),
        'grants_submitted': mem['grant_patterns'].get('total_submitted', 0),
        'strongest':        mem['meta'].get('strongest_engines', []),
        'weakest':          mem['meta'].get('weakest_engines', []),
    }

    prompt = f"""You are the long-term memory of an autonomous AI system.
Analyze these performance metrics and generate compact context strings
for each engine to use at the start of its LLM prompts.

System stats:
{json.dumps(summary, indent=2)}

Generate context for these engines in JSON:
{{
  "crypto_signals":   "1-2 sentence context about signal performance and what to focus on",
  "content_engine":   "1-2 sentence context about what content performs best",
  "press_outreach":   "1-2 sentence context about press response patterns",
  "grant_engine":     "1-2 sentence context about grant application patterns",
  "idea_engine":      "1-2 sentence context about which idea types get implemented",
  "art_engine":       "1-2 sentence context about art generation patterns",
  "general":          "2-3 sentence overall system context for any engine"
}}

Be specific and useful. These strings get prepended to every LLM prompt."""

    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 500,
            'messages': [
                {'role': 'system', 'content': 'Generate compact, useful context strings. JSON only.'},
                {'role': 'user',   'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        s = text.find('{')
        e = text.rfind('}') + 1
        contexts = json.loads(text[s:e])
        mem['contexts'] = contexts
        mem['contexts']['updated'] = TODAY
        print('[memory] Contexts synthesized')
    except Exception as e:
        print(f'[memory] Synthesis error: {e}')

def get_context(engine_name):
    """Helper for other engines to call: prepend to their LLM prompts."""
    mem = load_memory()
    ctx = mem.get('contexts', {})
    return ctx.get(engine_name, '') or ctx.get('general', '')

def run():
    print(f'\n[memory] Long-Term Memory Engine — {TODAY}')

    mem = load_memory()

    harvest_content_patterns(mem)
    harvest_signal_accuracy(mem)
    harvest_press_patterns(mem)
    harvest_grant_patterns(mem)
    harvest_meta(mem)

    # Only synthesize LLM contexts once per day
    if mem.get('contexts', {}).get('updated') != TODAY:
        synthesize_insights(mem)

    save_memory(mem)

    print(f'[memory] Memory updated:')
    print(f'  Ideas: {mem["meta"]["total_ideas_processed"]} | Signals: {mem["meta"]["total_signals_generated"]}')
    print(f'  Signal accuracy: {mem["signals_accuracy"].get("overall_accuracy","?")}')
    print(f'  Press reply rate: {mem["press_patterns"].get("overall_reply_rate","?")}%')
    print(f'  Strongest engines: {mem["meta"]["strongest_engines"]}')
    print('[memory] Done.')

if __name__ == '__main__':
    run()
