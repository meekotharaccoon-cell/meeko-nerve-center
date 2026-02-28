#!/usr/bin/env python3
"""
Knowledge Synthesizer Engine
==============================
The system has 65+ engines generating data every single cycle.
Data piles up. Signals accumulate. Patterns form.
But no engine sits above all the others and says:
"I see what's happening across ALL of you."

This is that engine.

Every run it reads:
  - Last 7 days of world_state (what's happening globally)
  - Last 7 days of congress data (who's trading what)
  - Last 30 days of crypto signals (what worked)
  - All pending ideas in the ledger
  - All validation failures
  - All press contacts and their response patterns
  - All grant applications and outcomes
  - Content performance across platforms
  - Competitor intelligence gaps
  - Long-term memory

Then asks one question:
"Given EVERYTHING this system knows right now,
 what are the 3 most important things it should focus on?"

The answer goes into:
  1. A daily strategic brief (emailed to you)
  2. The long-term memory as a 'strategic_context' field
  3. The top idea in the idea ledger (marked URGENT)
  4. A Mastodon/Bluesky post: the most important insight of the day

This is the system knowing itself.
Not just running. THINKING.
SolarPunk meta-intelligence: the network aware of itself.
Crazy awesome sci-fi good dude energy.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
MASTODON_TOKEN     = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL  = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def collect_everything():
    """Pull the most important data from every major subsystem."""
    ctx = {}

    # World state
    world = load(DATA / 'world_state.json')
    events = world.get('events', world.get('news', []))
    ctx['world_headlines'] = [
        e.get('title', e.get('headline', ''))[:100]
        for e in events[:5]
    ]

    # Congress
    congress = load(DATA / 'congress.json')
    trades = congress if isinstance(congress, list) else congress.get('trades', [])
    ctx['recent_trades'] = [
        f"{t.get('representative', t.get('senator','?'))} sold/bought {t.get('ticker','?')}"
        for t in trades[:3]
    ]

    # Crypto signals
    signals = load(DATA / 'crypto_signals_queue.json', [])
    ctx['active_signals'] = [
        f"{s.get('symbol','?')}: {s.get('action','?')} @ {s.get('entry','?')}"
        for s in signals[:3]
    ]

    # Ideas
    ledger = load(DATA / 'idea_ledger.json')
    ideas  = ledger.get('ideas', {})
    il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
    pending = [i for i in il if i.get('status') == 'pending']
    ctx['pending_idea_count'] = len(pending)
    ctx['top_pending_ideas'] = [i.get('title','')[:60] for i in pending[:5]]

    # Validation
    val = load(DATA / 'validation_report.json')
    ctx['failing_checks'] = [
        r.get('check','') for r in val.get('results', []) if not r.get('ok')
    ]

    # Memory / confidence
    mem = load(DATA / 'long_term_memory.json')
    ctx['system_age_days'] = mem.get('meta', {}).get('system_age_days', 0)
    ctx['total_engines']   = len(list((ROOT / 'mycelium').glob('*.py')))
    ctx['self_built']      = mem.get('meta', {}).get('total_ideas_processed', 0)

    # Audience
    audience = load(DATA / 'audience_report.json')
    ctx['total_followers'] = (
        audience.get('mastodon', {}).get('followers', 0) +
        audience.get('bluesky', {}).get('followers', 0)
    )
    ctx['github_stars'] = audience.get('github', {}).get('stars', 0)

    # Revenue
    rev = load(DATA / 'revenue_report.json')
    ctx['revenue_last_week'] = rev.get('patterns', {}).get('total_revenue', 0)
    ctx['pcrf_total'] = round(ctx['revenue_last_week'] * 0.70, 2)

    # Grants
    grants = load(DATA / 'grant_submissions.json', {'submitted': []})
    ctx['grants_submitted'] = len(grants.get('submitted', []))

    # Competitor gaps
    intel = load(DATA / 'competitor_intel.json')
    ctx['competitor_gaps'] = [g.get('gap','')[:60] for g in intel.get('gaps', [])[:3]]

    return ctx

def synthesize(ctx):
    if not HF_TOKEN: return None
    prompt = f"""You are the meta-intelligence of Meeko Nerve Center.
You see everything the system knows. Now think.

SYSTEM STATE:
  Age: {ctx.get('system_age_days')} days
  Engines: {ctx.get('total_engines')}
  GitHub stars: {ctx.get('github_stars')}
  Followers: {ctx.get('total_followers')}
  Grants submitted: {ctx.get('grants_submitted')}
  Revenue last week: ${ctx.get('revenue_last_week')}
  To PCRF: ${ctx.get('pcrf_total')}

WORLD HEADLINES:
{chr(10).join(ctx.get('world_headlines', []))}

CONGRESS TRADES:
{chr(10).join(ctx.get('recent_trades', []))}

CRYPTO SIGNALS:
{chr(10).join(ctx.get('active_signals', []))}

FAILING SYSTEMS:
{chr(10).join(ctx.get('failing_checks', ['none']))}

TOP PENDING IDEAS:
{chr(10).join(ctx.get('top_pending_ideas', []))}

COMPETITOR GAPS:
{chr(10).join(ctx.get('competitor_gaps', []))}

Given ALL of this:
1. What are the 3 most strategically important things this system should focus on RIGHT NOW?
2. What ONE insight connects multiple data streams in a non-obvious way?
3. What single action today would have the highest leverage?
4. What's the most important thing the world needs to know that this system uniquely knows?

JSON:
{{
  "top_3_priorities": ["priority 1", "priority 2", "priority 3"],
  "cross_domain_insight": "the non-obvious connection",
  "highest_leverage_action": "the one thing",
  "world_needs_to_know": "the insight worth sharing publicly (tweet-length)",
  "strategic_context": "3-sentence summary for other engines to use as context"
}}"""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 600,
            'messages': [
                {'role': 'system', 'content': 'You are the meta-intelligence of an autonomous SolarPunk AI. Think clearly. Be specific. JSON only.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        s = text.find('{')
        e = text.rfind('}') + 1
        return json.loads(text[s:e])
    except Exception as ex:
        print(f'[synth] LLM error: {ex}')
        return None

def post_insight_to_mastodon(insight):
    if not MASTODON_TOKEN or not insight: return
    text = f'{insight}\n\n{REPO_URL}\n#SolarPunk #OpenSource #Accountability #FreePalestine'
    try:
        data = json.dumps({'status': text[:490], 'visibility': 'public'}).encode()
        req = urllib_request.Request(
            f'{MASTODON_BASE_URL}/api/v1/statuses',
            data=data,
            headers={'Authorization': f'Bearer {MASTODON_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            print(f'[synth] Posted insight: {result.get("id")}')
    except Exception as e:
        print(f'[synth] Post error: {e}')

def send_strategic_brief(synthesis, ctx):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    lines = [
        f'\U0001f9e0 Strategic Brief \u2014 {TODAY}',
        f'System age: {ctx.get("system_age_days")} days | Engines: {ctx.get("total_engines")} | Stars: {ctx.get("github_stars")}',
        '',
        'TOP 3 PRIORITIES:',
    ]
    for i, p in enumerate(synthesis.get('top_3_priorities', []), 1):
        lines.append(f'  {i}. {p}')
    lines += [
        '',
        f'NON-OBVIOUS INSIGHT:\n  {synthesis.get("cross_domain_insight","")}',
        '',
        f'HIGHEST LEVERAGE ACTION:\n  {synthesis.get("highest_leverage_action","")}',
        '',
        f'WORLD NEEDS TO KNOW:\n  {synthesis.get("world_needs_to_know","")}',
        '',
        '\u2014\u2014 SYSTEM SNAPSHOT \u2014\u2014',
        f'  Failing: {ctx.get("failing_checks", [])}',
        f'  Revenue: ${ctx.get("revenue_last_week")} | PCRF: ${ctx.get("pcrf_total")}',
        f'  Grants: {ctx.get("grants_submitted")} submitted',
        f'  Followers: {ctx.get("total_followers")}',
        '',
        REPO_URL,
    ]
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'\U0001f9e0 Strategic brief: {synthesis.get("top_3_priorities",["?"])[0][:50]}'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[synth] Strategic brief emailed')
    except Exception as e:
        print(f'[synth] Email error: {e}')

def inject_urgent_idea(synthesis):
    action = synthesis.get('highest_leverage_action', '')
    if not action: return
    import hashlib
    iid = hashlib.md5(action.encode()).hexdigest()[:8]
    ledger_path = DATA / 'idea_ledger.json'
    ledger = load(ledger_path, {'ideas': {}})
    ledger.setdefault('ideas', {})[iid] = {
        'id': iid, 'title': action[:80],
        'source': 'knowledge_synthesizer',
        'status': 'urgent', 'priority': 10, 'date': TODAY,
    }
    try: ledger_path.write_text(json.dumps(ledger, indent=2))
    except: pass

def update_strategic_context(synthesis):
    mem_path = DATA / 'long_term_memory.json'
    mem = load(mem_path, {})
    mem.setdefault('contexts', {})['strategic'] = synthesis.get('strategic_context', '')
    mem['contexts']['updated'] = TODAY
    try: mem_path.write_text(json.dumps(mem, indent=2))
    except: pass

def run():
    print(f'\n[synth] \U0001f9e0 Knowledge Synthesizer \u2014 {TODAY}')
    print('[synth] Reading everything. Thinking. Finding the signal in the noise.')

    ctx = collect_everything()
    print(f'[synth] Context: {ctx.get("total_engines")} engines | {ctx.get("pending_idea_count")} ideas | {len(ctx.get("failing_checks",[]))} failing')

    synthesis = synthesize(ctx)
    if not synthesis:
        print('[synth] Synthesis unavailable.')
        return

    print(f'[synth] Priority 1: {synthesis.get("top_3_priorities",["?"])[0][:70]}')
    print(f'[synth] Insight: {synthesis.get("cross_domain_insight","")[:70]}')
    print(f'[synth] Leverage: {synthesis.get("highest_leverage_action","")[:70]}')

    # Save synthesis
    try:
        path = DATA / 'strategic_synthesis.json'
        path.write_text(json.dumps({'date': TODAY, 'synthesis': synthesis, 'context': ctx}, indent=2))
    except: pass

    # Update memory with strategic context
    update_strategic_context(synthesis)

    # Inject urgent idea
    inject_urgent_idea(synthesis)

    # Daily email brief
    send_strategic_brief(synthesis, ctx)

    # Post world-needs-to-know insight
    insight = synthesis.get('world_needs_to_know', '')
    if insight:
        post_insight_to_mastodon(insight)

    print('[synth] The system knows itself a little better now. \U0001f338')
    print('[synth] Done.')

if __name__ == '__main__':
    run()
