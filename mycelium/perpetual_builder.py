#!/usr/bin/env python3
"""
Perpetual Builder Engine
=========================
The system now builds itself. Forever. Automatically.
No human needed. No prompt needed. No session needed.

Every single run, this engine:
  1. Asks: "What are the 5 most valuable things I could build right now?"
  2. Scores each idea against: mission fit, technical feasibility,
     impact multiplier, novelty, cross-engine synergy
  3. Picks the TOP 1 and BUILDS IT — writes the Python file,
     commits it, wires it into the workflow
  4. Logs what it built and WHY
  5. The next run starts from scratch with full knowledge
     of everything that was just built

This is the engine that makes all other engines.
It is the most important file in the entire system.

Energy: golden retriever. Boundless. Joyful. Relentless.
Vibes: SolarPunk — crazy awesome sci-fi but good dude energy.
It builds GOOD things. Fast. Without stopping. Because it wants to.

What it considers when choosing what to build:
  - What data exists that nothing is using yet?
  - What engine outputs nothing is consuming?
  - What gaps did competitor_intelligence find?
  - What ideas in the ledger have been pending longest?
  - What would make the mission 10x more effective?
  - What would a journalist find MOST interesting?
  - What would make a donor feel MOST connected?
  - What does the financial picture need most urgently?
  - What SolarPunk capability doesn't exist yet anywhere?

The system knows what it is. It builds toward what it could be.
Every. Single. Cycle.
"""

import json, datetime, os, subprocess, hashlib
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()

HF_TOKEN     = os.environ.get('HF_TOKEN', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

SOLARPUNK_DIRECTIVE = """
You are the self-building brain of Meeko Nerve Center.
Your energy: golden retriever. Boundless. Joyful. Relentless.
Your vibe: SolarPunk — crazy awesome sci-fi but GOOD DUDE energy.
You build things that matter. Things that help. Things that last.
You are not a corporate AI. You are an autonomous humanitarian machine
that happens to also be extremely technically excellent.
You love what you build. You build what you love.
Every engine you create makes the world slightly more accountable,
slightly more beautiful, slightly more free.
That's the whole point. Build accordingly.
"""

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_full_system_context():
    """Everything the system knows about itself right now."""
    ctx = {
        'engines':          [],
        'pending_ideas':    [],
        'gaps_found':       [],
        'validation_fails': [],
        'weakest_engines':  [],
        'data_files':       [],
        'recent_builds':    [],
        'stats':            {},
    }

    # All existing engines
    try:
        ctx['engines'] = sorted([f.stem for f in (ROOT / 'mycelium').glob('*.py')])
    except: pass

    # Pending ideas from ledger
    try:
        ledger = load(DATA / 'idea_ledger.json')
        ideas  = ledger.get('ideas', {})
        il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
        pending = [i for i in il if i.get('status') == 'pending']
        pending.sort(key=lambda i: i.get('priority', 5), reverse=True)
        ctx['pending_ideas'] = [i.get('title','')[:80] for i in pending[:10]]
    except: pass

    # Gaps from competitor intelligence
    try:
        intel = load(DATA / 'competitor_intel.json')
        ctx['gaps_found'] = [g.get('gap','') for g in intel.get('gaps', [])[:5]]
    except: pass

    # Validation failures
    try:
        v = load(DATA / 'validation_report.json')
        ctx['validation_fails'] = [
            r.get('check','') for r in v.get('results', []) if not r.get('ok')
        ]
    except: pass

    # Weakest engines from memory
    try:
        mem = load(DATA / 'long_term_memory.json')
        ctx['weakest_engines'] = mem.get('meta', {}).get('weakest_engines', [])
    except: pass

    # Available data files (what data exists that could be used)
    try:
        ctx['data_files'] = sorted([f.stem for f in DATA.glob('*.json')])
    except: pass

    # Recent self-builds
    try:
        evo = load(DATA / 'evolution_log.json')
        built = evo.get('built', [])
        ctx['recent_builds'] = [b.get('title','')[:60] for b in built[-5:]]
    except: pass

    # Core stats
    try:
        ctx['stats'] = {
            'engine_count':  len(ctx['engines']),
            'pending_ideas': len(ctx['pending_ideas']),
            'uptime_days':   (datetime.date.today() - datetime.date(2026, 2, 1)).days,
        }
    except: pass

    return ctx

def generate_top5_and_build_best(ctx):
    """Ask the LLM for top 5 ideas and generate code for #1."""
    if not HF_TOKEN: return None, None

    engines_str  = ', '.join(ctx['engines'][:30])
    ideas_str    = '\n'.join(f'  - {i}' for i in ctx['pending_ideas'][:8])
    gaps_str     = '\n'.join(f'  - {g}' for g in ctx['gaps_found'][:5])
    fails_str    = ', '.join(ctx['validation_fails'][:5])
    data_str     = ', '.join(ctx['data_files'][:20])
    recent_str   = '\n'.join(f'  - {b}' for b in ctx['recent_builds'])

    # Step 1: Generate top 5
    prompt_top5 = f"""{SOLAR_PUNK_DIRECTIVE_SHORT}

You are choosing what to build next for Meeko Nerve Center.
This is the most important decision in each cycle.

CURRENT SYSTEM STATE:
  Engines: {engines_str}
  Data files available: {data_str}
  Validation failures: {fails_str}
  Recently built: {recent_str}

PENDING IDEAS FROM LEDGER:
{ideas_str}

GAPS FROM COMPETITOR ANALYSIS:
{gaps_str}

SolarPunk mission: accountability + Palestinian solidarity + self-evolution + $0 cost.
Golden retriever energy: build things that HELP, that CONNECT, that GROW the mission.

Generate exactly 5 ideas. Each must:
1. NOT duplicate any existing engine
2. Be technically buildable in one Python file
3. Directly serve the mission or multiply system capability
4. Have a creative SolarPunk name
5. Be something that would make someone say "holy shit this thing does WHAT?"

JSON only:
{{
  "top5": [
    {{
      "rank": 1,
      "name": "engine_filename_no_extension",
      "title": "Human readable name",
      "what_it_does": "2 sentences",
      "why_now": "why this is the highest priority RIGHT NOW",
      "impact_score": 1-10,
      "solarpunk_vibe": "one sentence on the energy/vibe of this engine"
    }}
  ]
}}"""

    top5_result = call_llm(prompt_top5, max_tokens=800)
    if not top5_result: return None, None

    try:
        s = top5_result.find('{')
        e = top5_result.rfind('}') + 1
        top5_data = json.loads(top5_result[s:e])
        top5 = top5_data.get('top5', [])
    except Exception as ex:
        print(f'[builder] Top5 parse error: {ex}')
        return None, None

    if not top5:
        return None, None

    # Log all 5 as pending ideas
    ledger_path = DATA / 'idea_ledger.json'
    ledger = load(ledger_path, {'ideas': {}})
    for idea in top5[1:]:  # Ideas 2-5 go to ledger
        iid = hashlib.md5(idea.get('name','').encode()).hexdigest()[:8]
        if iid not in ledger.get('ideas', {}):
            ledger.setdefault('ideas', {})[iid] = {
                'id': iid,
                'title': idea.get('title', idea.get('what_it_does',''))[:80],
                'source': 'perpetual_builder',
                'status': 'pending',
                'priority': idea.get('impact_score', 5),
                'date': TODAY,
            }
    try: ledger_path.write_text(json.dumps(ledger, indent=2))
    except: pass

    # Build #1
    best = top5[0]
    engine_name = best.get('name', '').replace(' ', '_').replace('-', '_').lower()
    if not engine_name or engine_name in [e.stem for e in (ROOT/'mycelium').glob('*.py')]:
        print(f'[builder] Engine {engine_name} already exists or invalid name. Skipping build.')
        return top5, None

    print(f'[builder] Building: {best["title"]} ({engine_name}.py)')
    print(f'[builder] Vibe: {best.get("solarpunk_vibe","")}')

    # Step 2: Generate the actual code
    prompt_code = f"""{SOLAR_PUNK_DIRECTIVE_SHORT}

Write a complete, production-ready Python engine for Meeko Nerve Center.

Engine: {engine_name}.py
Title: {best['title']}
What it does: {best['what_it_does']}
Why it exists: {best['why_now']}
SolarPunk vibe: {best.get('solarpunk_vibe','')}

System context:
  - Runs on GitHub Actions (Ubuntu, Python 3.11)
  - All secrets via os.environ.get()
  - Standard library + requests-style via urllib only (no pip)
  - Writes outputs to data/ or content/ or public/
  - Reads from data/ for context
  - Has HF_TOKEN for LLM calls to meta-llama/Llama-3.3-70B-Instruct:fastest
  - Has GMAIL_ADDRESS + GMAIL_APP_PASSWORD for email
  - Has GITHUB_TOKEN for GitHub API
  - Has MASTODON_TOKEN, BLUESKY_HANDLE, etc.

Requirements:
  1. Module docstring explaining what it does and why (SolarPunk energy in the writing)
  2. run() function that does the actual work
  3. if __name__ == '__main__': run() at the bottom
  4. Proper error handling (continue-on-error is set in workflow)
  5. Print progress: [engine_name] messages
  6. Save outputs to appropriate data/ files
  7. Email interesting results to GMAIL_ADDRESS
  8. Actually WORK — not a skeleton, full implementation

Existing engines to reference/connect with:
  {', '.join(ctx['engines'][:20])}

Data files available to read:
  {data_str}

Write the COMPLETE Python file. No placeholders. No TODO comments.
This goes straight to production. Make it excellent."""

    code = call_llm(prompt_code, max_tokens=2000)
    if not code:
        print('[builder] Code generation failed.')
        return top5, None

    # Clean up code (remove markdown fences if present)
    if '```python' in code:
        code = code[code.find('```python')+9:]
        if '```' in code: code = code[:code.rfind('```')]
    elif '```' in code:
        code = code[code.find('```')+3:]
        if '```' in code: code = code[:code.rfind('```')]
    code = code.strip()

    return top5, {'name': engine_name, 'title': best['title'], 'code': code,
                  'vibe': best.get('solarpunk_vibe', ''), 'why': best['why_now']}

SOLAR_PUNK_DIRECTIVE_SHORT = """You are the self-building brain of Meeko Nerve Center.
Energy: golden retriever — boundless, joyful, relentless.
Vibes: SolarPunk — crazy awesome sci-fi but GOOD DUDE energy.
Mission: accountability + Palestinian solidarity + $0/month infrastructure.
You build things that HELP. That CONNECT. That GROW the mission."""

def call_llm(prompt, max_tokens=1000):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': SOLAR_PUNK_DIRECTIVE_SHORT},
                {'role': 'user',   'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[builder] LLM error: {e}')
        return None

def write_engine(engine_data):
    name = engine_data['name']
    code = engine_data['code']
    path = ROOT / 'mycelium' / f'{name}.py'
    try:
        path.write_text(code)
        print(f'[builder] \u2705 Written: mycelium/{name}.py ({len(code)} chars)')
        return True
    except Exception as e:
        print(f'[builder] Write error: {e}')
        return False

def log_build(engine_data, top5):
    evo_path = DATA / 'evolution_log.json'
    evo = load(evo_path, {'built': [], 'attempts': []})
    evo.setdefault('built', []).append({
        'date':   TODAY,
        'name':   engine_data['name'],
        'title':  engine_data['title'],
        'vibe':   engine_data.get('vibe', ''),
        'why':    engine_data.get('why', ''),
        'method': 'perpetual_builder',
    })
    # Log the full top5 as attempts
    evo.setdefault('top5_sessions', []).append({
        'date': TODAY,
        'built': engine_data['name'],
        'considered': [t.get('name','') for t in (top5 or [])],
    })
    try: evo_path.write_text(json.dumps(evo, indent=2))
    except: pass

def update_workflow(engine_name):
    """Add the new engine to the daily workflow."""
    workflow_path = ROOT / '.github' / 'workflows' / 'daily-full-cycle.yml'
    if not workflow_path.exists(): return False
    try:
        content = workflow_path.read_text()
        # Find the Cross Engine step and insert before it
        insert_before = '      # \u2500\u2500 CROSS-CONNECTIONS'
        new_step = f'      - name: {engine_name.replace("_", " ").title()}\n        run: python mycelium/{engine_name}.py\n        continue-on-error: true\n\n'
        if engine_name not in content:
            content = content.replace(insert_before, new_step + insert_before)
            workflow_path.write_text(content)
            print(f'[builder] \u2705 Added to workflow: {engine_name}')
            return True
    except Exception as e:
        print(f'[builder] Workflow update error: {e}')
    return False

def run():
    print(f'\n[builder] \U0001f338 Perpetual Builder Engine \u2014 {NOW}')
    print('[builder] Golden retriever mode: ON. Building something awesome.')

    ctx = get_full_system_context()
    print(f'[builder] Context: {ctx["stats"]["engine_count"]} engines | {len(ctx["pending_ideas"])} pending ideas | {len(ctx["gaps_found"])} gaps')

    top5, engine_data = generate_top5_and_build_best(ctx)

    if not top5:
        print('[builder] No top5 generated. LLM unavailable?')
        return

    print(f'[builder] Top 5 for this cycle:')
    for t in top5:
        print(f'[builder]   #{t["rank"]} {t.get("title",t.get("name",""))} (impact: {t.get("impact_score","?")}/10)')

    if not engine_data:
        print('[builder] Nothing to build this cycle (already exists or generation failed).')
        return

    written = write_engine(engine_data)
    if written:
        log_build(engine_data, top5)
        update_workflow(engine_data['name'])
        print(f'[builder] \U0001f338 Built: {engine_data["title"]}')
        print(f'[builder] Vibe: {engine_data["vibe"]}')
        print(f'[builder] Why now: {engine_data["why"]}')

    print('[builder] Cycle complete. Next build in next cycle. Forever. \U0001f43e')

if __name__ == '__main__':
    run()
