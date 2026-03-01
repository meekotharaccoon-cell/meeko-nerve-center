#!/usr/bin/env python3
"""
Long-Term Memory Engine — v2: Now reads from Notion
====================================================
Every LLM call in every engine starts from zero.
No engine remembers what worked last week.
This is the biggest invisible bottleneck in the whole system.

v1: stored patterns in data/long_term_memory.json (good start, blind spot)
v2: NOW pulls from three sources simultaneously:
  1. data/ JSON files (existing — system-generated metrics)
  2. Notion workspace (NEW — human-annotated knowledge, your observations)
  3. HuggingFace dataset log (NEW — performance data over time)

Then synthesizes EVERYTHING into engine-specific context strings
that get prepended to every LLM prompt.

Result: every engine gets smarter every day. Not just from its own data —
from YOUR observations in Notion and from the performance record in HF.

Used by other engines:
  from mycelium.long_term_memory import get_context, get_directives_context
  context = get_context('grant_engine')
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import HTTPError

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN       = os.environ.get('HF_TOKEN', '')
NOTION_TOKEN   = os.environ.get('NOTION_TOKEN', '')
NOTION_VERSION = '2022-06-28'
NOTION_API     = 'https://api.notion.com/v1'
HF_USERNAME    = os.environ.get('HF_USERNAME', 'meekotharaccoon')

MEMORY_PATH = DATA / 'long_term_memory.json'

BASE_SCHEMA = {
    'version':   2,
    'updated':   TODAY,
    'contexts':  {},
    'patterns':  [],
    'failures':  [],
    'wins':      [],
    'signals_accuracy':    {},
    'content_patterns':    {},
    'donor_patterns':      {},
    'press_patterns':      {},
    'grant_patterns':      {},
    'world_patterns':      [],
    'notion_observations': [],  # NEW: human-written notes from Notion
    'hf_performance':      {},  # NEW: performance data from HF dataset
    'directives_history':  [],  # NEW: what the human has prioritized over time
    'meta': {
        'total_ideas_processed': 0,
        'total_signals_generated': 0,
        'total_art_generated': 0,
        'total_dataset_records': 0,
        'system_age_days': 0,
        'last_evolution_date': '',
        'strongest_engines': [],
        'weakest_engines': [],
    }
}


# ── Utilities ─────────────────────────────────────────────────────────────────
def load(path, default=None):
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text())
    except:
        pass
    return default if default is not None else {}

def notion_req(method, path, body=None):
    if not NOTION_TOKEN:
        return None
    url = NOTION_API + path
    data = json.dumps(body).encode() if body else None
    req = urllib_request.Request(url, data=data, method=method, headers={
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Notion-Version': NOTION_VERSION,
        'Content-Type': 'application/json',
    })
    try:
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except:
        return None

def hf_infer(prompt, max_tokens=600):
    if not HF_TOKEN:
        return None
    payload = json.dumps({
        'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
        'max_tokens': max_tokens,
        'messages': [
            {'role': 'system', 'content': 'You are the long-term memory synthesizer for an autonomous AI system. Generate compact, useful context strings. Return only valid JSON.'},
            {'role': 'user', 'content': prompt}
        ]
    }).encode()
    try:
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=45) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        s = text.find('{')
        e = text.rfind('}') + 1
        if s >= 0 and e > s:
            return json.loads(text[s:e])
    except Exception as e:
        print(f'[memory] HF error: {e}')
    return None


# ── Source 1: data/ JSON files (original) ────────────────────────────────────
def harvest_data_files(mem):
    print('[memory] Harvesting data/ files')

    # Content performance
    perf = load(DATA / 'content_performance.json')
    if perf:
        for platform in ('mastodon', 'bluesky'):
            pd = perf.get(platform, {})
            top = pd.get('top_posts', [])
            if top:
                avg_len = sum(len(p.get('text','')) for p in top) // max(len(top), 1)
                mem.setdefault('content_patterns', {})[platform] = {
                    'avg_top_length': avg_len,
                    'sample_top': top[0].get('text','')[:100],
                    'updated': TODAY,
                }

    # Signal accuracy
    report = load(DATA / 'validation_report.json')
    for r in report.get('results', []):
        if r.get('check') == 'signal_accuracy':
            mem['signals_accuracy']['overall_accuracy'] = r.get('accuracy', 0)
            mem['signals_accuracy']['updated'] = TODAY

    # Press patterns
    fu_log = load(DATA / 'press_followup_log.json').get('contacts', {})
    replied = sum(1 for v in fu_log.values() if v.get('status') == 'replied')
    total   = len(fu_log)
    if total > 0:
        mem['press_patterns']['overall_reply_rate'] = round(replied/total*100)
        mem['press_patterns']['total_contacted']    = total
        mem['press_patterns']['updated']            = TODAY

    # Grant patterns
    submitted = load(DATA / 'grant_submissions.json').get('submitted', [])
    mem['grant_patterns']['total_submitted'] = len(submitted)
    mem['grant_patterns']['recent'] = [
        {'name': s.get('grant_name',''), 'date': s.get('date','')}
        for s in submitted[-5:]
    ]

    # Meta
    ledger = load(DATA / 'idea_ledger.json')
    ideas  = ledger.get('ideas', {})
    il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
    mem['meta']['total_ideas_processed'] = len(il)

    history = load(DATA / 'crypto_signals_history.json', [])
    mem['meta']['total_signals_generated'] = len(history)

    arts = load(DATA / 'generated_art.json')
    al   = arts if isinstance(arts, list) else arts.get('art', [])
    mem['meta']['total_art_generated'] = len(al)

    try:
        start = datetime.date(2026, 2, 1)
        mem['meta']['system_age_days'] = (datetime.date.today() - start).days
    except:
        pass


# ── Source 2: Notion workspace (NEW) ─────────────────────────────────────────
def harvest_notion(mem):
    """Pull human observations from Notion pages."""
    if not NOTION_TOKEN:
        print('[memory] No NOTION_TOKEN — skipping Notion harvest')
        return

    print('[memory] Harvesting Notion workspace')
    observations = []

    # Pages to harvest from
    pages_to_read = [
        '3D Brain State Log',
        'Claude Sessions — Build Log',
        'Revenue & Products Dashboard',
        'DIRECTIVES',
    ]

    for page_title in pages_to_read:
        result = notion_req('POST', '/search', {
            'query': page_title,
            'filter': {'value': 'page', 'property': 'object'},
            'page_size': 3
        })
        if not result:
            continue
        for r in result.get('results', []):
            if r.get('object') != 'page':
                continue
            page_id = r['id']
            # Read blocks
            blocks_result = notion_req('GET', f'/blocks/{page_id}/children?page_size=50')
            if not blocks_result:
                continue
            page_text = []
            for block in blocks_result.get('results', []):
                btype = block.get('type', '')
                rich  = block.get(btype, {}).get('rich_text', [])
                text  = ''.join(t.get('plain_text', '') for t in rich)
                if text.strip():
                    page_text.append(text.strip())
            if page_text:
                observations.append({
                    'source': page_title,
                    'date': TODAY,
                    'content': ' | '.join(page_text[:10])[:1000],
                })
                print(f'[memory] Read Notion page: {page_title} ({len(page_text)} blocks)')

    # Harvest directives history
    directives = load(DATA / 'directives.json')
    if directives and directives.get('raw'):
        mem.setdefault('directives_history', []).append({
            'date': directives.get('date', TODAY),
            'message': directives.get('human_message', ''),
            'priority': directives.get('priority', []),
            'pause': directives.get('pause', []),
        })
        # Keep last 30 days
        mem['directives_history'] = mem['directives_history'][-30:]

    mem['notion_observations'] = observations[-20:]  # Keep last 20 observations
    print(f'[memory] Harvested {len(observations)} Notion observations')


# ── Source 3: HuggingFace dataset performance (NEW) ──────────────────────────
def harvest_hf_performance(mem):
    """Read performance data from local HF dataset log."""
    print('[memory] Harvesting HF dataset performance')
    log_path = DATA / 'hf_dataset_log.jsonl'
    if not log_path.exists():
        print('[memory] No HF dataset log yet')
        return

    records = []
    try:
        with open(log_path) as f:
            for line in f.readlines()[-500:]:  # last 500 records
                if line.strip():
                    records.append(json.loads(line))
    except Exception as e:
        print(f'[memory] HF log read error: {e}')
        return

    mem['meta']['total_dataset_records'] = len(records)

    # Analyze performance by engine
    by_engine = {}
    for r in records:
        engine = r.get('engine', 'unknown')
        perf   = r.get('performance', {})
        engagement = sum([
            perf.get('likes', 0),
            perf.get('boosts', 0),
            perf.get('replies', 0),
        ])
        by_engine.setdefault(engine, {'count': 0, 'total_engagement': 0})
        by_engine[engine]['count'] += 1
        by_engine[engine]['total_engagement'] += engagement

    # Find best/worst performers
    sorted_engines = sorted(
        by_engine.items(),
        key=lambda x: x[1]['total_engagement'] / max(x[1]['count'], 1),
        reverse=True
    )
    mem['meta']['strongest_engines'] = [e for e, _ in sorted_engines[:3]]
    mem['meta']['weakest_engines']   = [e for e, _ in sorted_engines[-3:]]

    # Find best-performing content patterns
    social_posts = [r for r in records if r.get('type') == 'social_post']
    if social_posts:
        top_posts = sorted(
            social_posts,
            key=lambda r: sum(r.get('performance', {}).values()),
            reverse=True
        )[:5]
        mem['hf_performance']['top_post_patterns'] = [
            {
                'content_snippet': r.get('content','')[:150],
                'platform': r.get('platform',''),
                'engagement': sum(r.get('performance', {}).values()),
            }
            for r in top_posts
        ]

    print(f'[memory] Analyzed {len(records)} HF dataset records')
    print(f'[memory] Strongest: {mem["meta"]["strongest_engines"]}')


# ── Synthesize into engine contexts ──────────────────────────────────────────
def synthesize_contexts(mem):
    """Use HF LLM to synthesize all sources into engine-specific context strings."""
    if not HF_TOKEN:
        print('[memory] No HF_TOKEN — using rule-based contexts')
        _rule_based_contexts(mem)
        return

    # Build rich summary from all three sources
    notion_summary = ' // '.join([
        obs.get('content', '')[:200]
        for obs in mem.get('notion_observations', [])[:5]
    ])

    directives_summary = ' // '.join([
        f"{d.get('date')}: priority={d.get('priority',[])}, message={d.get('message','')}"
        for d in mem.get('directives_history', [])[-5:]
    ])

    hf_perf_summary = json.dumps(
        mem.get('hf_performance', {}).get('top_post_patterns', [])[:3], indent=2
    ) if mem.get('hf_performance') else 'No performance data yet'

    summary = {
        'system_age_days':    mem['meta'].get('system_age_days', 0),
        'total_ideas':        mem['meta'].get('total_ideas_processed', 0),
        'signal_accuracy':    mem['signals_accuracy'].get('overall_accuracy', 'unknown'),
        'press_reply_rate':   mem['press_patterns'].get('overall_reply_rate', 'unknown'),
        'grants_submitted':   mem['grant_patterns'].get('total_submitted', 0),
        'strongest_engines':  mem['meta'].get('strongest_engines', []),
        'total_dataset_records': mem['meta'].get('total_dataset_records', 0),
    }

    parsed = hf_infer(f"""You synthesize an autonomous AI system's long-term memory into engine context strings.
These strings will be prepended to every LLM prompt to make engines smarter.

System metrics:
{json.dumps(summary, indent=2)}

Human's recent directives from Notion:
{directives_summary if directives_summary else 'No directives yet'}

Human's observations from Notion:
{notion_summary if notion_summary else 'No observations yet'}

Top performing content:
{hf_perf_summary}

Generate COMPACT (1-2 sentences each) context strings for each engine:
{{
  "crypto_signals":  "context about signal performance",
  "content_engine":  "context about content that performs best + human's tone preferences",
  "press_outreach":  "context about press response patterns",
  "grant_engine":    "context about grant patterns + what human has prioritized",
  "idea_engine":     "context about idea types that get implemented",
  "art_engine":      "context about art generation + cause alignment",
  "social_poster":   "context about best posting strategy from performance data",
  "email_engine":    "context about email patterns that work",
  "general":         "2-3 sentence overall context: system state, human intent, strategic focus"
}}""", max_tokens=800)

    if parsed:
        mem['contexts'] = parsed
        mem['contexts']['updated'] = TODAY
        mem['contexts']['synthesized_from'] = ['data_files', 'notion', 'hf_dataset']
        print('[memory] Contexts synthesized from all 3 sources')
    else:
        _rule_based_contexts(mem)

def _rule_based_contexts(mem):
    """Fallback: rule-based contexts when LLM unavailable."""
    directives = load(DATA / 'directives.json')
    priority = directives.get('priority', []) if directives else []
    human_msg = directives.get('human_message', '') if directives else ''

    base = f"System age: {mem['meta'].get('system_age_days', 0)} days. "
    if priority:
        base += f"Human priority today: {', '.join(priority)}. "
    if human_msg:
        base += f"Human says: {human_msg}. "

    mem['contexts'] = {
        'general':       base + 'Focus on mission: ethical AI products, 70% PCRF, open source.',
        'grant_engine':  base + f"Grants submitted: {mem['grant_patterns'].get('total_submitted', 0)}.",
        'content_engine': base + 'Optimize for engagement and mission alignment.',
        'crypto_signals': 'Focus on accuracy over volume.',
        'updated': TODAY,
        'synthesized_from': ['data_files'],
    }


# ── Public API ────────────────────────────────────────────────────────────────
def load_memory():
    if MEMORY_PATH.exists():
        try:
            return json.loads(MEMORY_PATH.read_text())
        except:
            pass
    return dict(BASE_SCHEMA)

def save_memory(mem):
    mem['updated'] = TODAY
    DATA.mkdir(parents=True, exist_ok=True)
    try:
        MEMORY_PATH.write_text(json.dumps(mem, indent=2))
    except Exception as e:
        print(f'[memory] Save error: {e}')

def get_context(engine_name):
    """Called by other engines: prepend this to LLM prompts."""
    mem = load_memory()
    ctx = mem.get('contexts', {})
    # Check if today's context exists
    if ctx.get('updated') == TODAY:
        return ctx.get(engine_name, '') or ctx.get('general', '')
    # Context stale — return general directive
    directives = load(DATA / 'directives.json')
    if directives and directives.get('human_message'):
        return f"Human directive: {directives['human_message']}"
    return ''

def get_directives_context():
    """Get a context string from today's human directives."""
    directives = load(DATA / 'directives.json')
    if not directives or directives.get('date') != TODAY:
        return ''
    parts = []
    if directives.get('human_message'):
        parts.append(f"Human says: {directives['human_message']}")
    if directives.get('priority'):
        parts.append(f"Priority today: {', '.join(directives['priority'])}")
    if directives.get('pause'):
        parts.append(f"PAUSED: {', '.join(directives['pause'])}")
    if directives.get('build_next'):
        parts.append(f"Build next: {directives['build_next']}")
    return ' | '.join(parts)


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print(f'\n[memory] Long-Term Memory Engine v2 — {TODAY}')
    print('[memory] Sources: data/ files + Notion + HuggingFace dataset')

    mem = load_memory()

    # Harvest from all three sources
    harvest_data_files(mem)
    harvest_notion(mem)
    harvest_hf_performance(mem)

    # Synthesize only if contexts are stale
    if mem.get('contexts', {}).get('updated') != TODAY:
        synthesize_contexts(mem)
    else:
        print('[memory] Contexts already synthesized today')

    save_memory(mem)

    print(f'\n[memory] Summary:')
    print(f'  Age: {mem["meta"]["system_age_days"]} days')
    print(f'  Ideas processed: {mem["meta"]["total_ideas_processed"]}')
    print(f'  Dataset records: {mem["meta"]["total_dataset_records"]}')
    print(f'  Notion observations: {len(mem.get("notion_observations", []))}')
    print(f'  Directives history: {len(mem.get("directives_history", []))} days')
    print(f'  Contexts synthesized from: {mem.get("contexts", {}).get("synthesized_from", [])}')
    print('[memory] Done.')


if __name__ == '__main__':
    run()
