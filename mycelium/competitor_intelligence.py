#!/usr/bin/env python3
"""
Competitor Intelligence Engine
================================
The system is unique but not alone. There are other projects
tracking congressional trades, other AI tools for activism,
other open source accountability systems.

Knowing what they're doing means:
  1. Avoid duplicating work — build what DOESN'T exist
  2. Find gaps they haven't filled — build those first
  3. Identify where to position (what makes this different)
  4. Learn what's working in adjacent projects
  5. Find merger/collaboration opportunities
  6. Be first to cover stories they break (congressional trades)

Projects monitored:
  Congressional trades:
    - Capitol Trades (capitoltrades.com)
    - Quiver Quantitative (quiverquant.com)
    - TechCongress (congressional tech fellowship)

  Open source accountability:
    - OpenSecrets API usage
    - CREW (Citizens for Responsibility)

  Palestinian solidarity tech:
    - Tech for Palestine directory
    - BDS movement tech tools

  Autonomous AI / civic tech:
    - AutoGPT equivalents
    - Hugging Face Spaces with civic purpose

Output:
  - data/competitor_intel.json
  - Weekly digest email: what they did, what gaps exist
  - Idea injection: gaps become ideas for this system
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

MONITOR_TARGETS = [
    {
        'id': 'capitol_trades',
        'name': 'Capitol Trades',
        'url': 'https://capitoltrades.com',
        'rss': 'https://capitoltrades.com/trades.rss',
        'type': 'congressional_trades',
        'monitor': 'new_trades',
    },
    {
        'id': 'quiver_quant',
        'name': 'Quiver Quantitative',
        'url': 'https://www.quiverquant.com',
        'api': 'https://api.quiverquant.com/beta/live/congresstrading',
        'type': 'congressional_trades',
        'monitor': 'api_activity',
    },
    {
        'id': 'tech4palestine',
        'name': 'Tech for Palestine',
        'url': 'https://techforpalestine.org',
        'type': 'solidarity_tech',
        'monitor': 'new_projects',
    },
    {
        'id': 'crew',
        'name': 'CREW (Citizens for Responsibility)',
        'url': 'https://www.citizensforethics.org',
        'rss': 'https://www.citizensforethics.org/feed/',
        'type': 'accountability',
        'monitor': 'new_reports',
    },
]

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def fetch(url, timeout=15):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-intel/1.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'[intel] Fetch error {url[:50]}: {e}')
        return None

def check_site_activity(target):
    """Basic check: is the site up and recently updated?"""
    html = fetch(target['url'])
    if not html:
        return {'target': target['id'], 'status': 'unreachable', 'activity': []}

    # Look for date patterns indicating recent updates
    import re
    dates = re.findall(r'202[4-9]-\d{2}-\d{2}', html)
    recent = [d for d in set(dates) if d >= (datetime.date.today() - datetime.timedelta(days=7)).isoformat()]

    return {
        'target':        target['id'],
        'name':          target['name'],
        'status':        'active',
        'recent_dates':  sorted(set(recent), reverse=True)[:5],
        'is_active':     len(recent) > 0,
        'checked':       TODAY,
    }

def identify_gaps(intel_data, stats):
    """Ask LLM: what are these competitors NOT doing that we could?"""
    if not HF_TOKEN: return []
    summary = json.dumps(intel_data, indent=2)[:2000]
    prompt = f"""Analyze these competitor projects and identify gaps.

Competitors:
{summary}

Our project (Meeko Nerve Center) capabilities:
  - Self-evolving autonomous AI
  - Congressional STOCK Act tracking
  - Palestinian solidarity art generation
  - Grant writing and submission
  - Press outreach automation
  - Crypto signals
  - $0/month infrastructure
  - AGPL-3.0 open source

Identify 3-5 specific gaps: things the competitors aren't doing that we COULD do
that would be valuable, differentiated, and aligned with our mission.

Return JSON:
{{
  "gaps": [
    {{
      "gap": "what's missing",
      "opportunity": "how we could fill it",
      "priority": 1-10,
      "effort": "low|medium|high"
    }}
  ]
}}"""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 500,
            'messages': [
                {'role': 'system', 'content': 'You identify strategic gaps in competitive landscapes. JSON only.'},
                {'role': 'user', 'content': prompt}
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
        result = json.loads(text[s:e])
        return result.get('gaps', [])
    except Exception as e:
        print(f'[intel] Gap analysis error: {e}')
        return []

def inject_gaps_as_ideas(gaps):
    """Turn identified gaps into ideas for the idea engine."""
    import hashlib
    ledger_path = DATA / 'idea_ledger.json'
    ledger = load(ledger_path, {'ideas': {}})
    ideas  = ledger.get('ideas', {})
    for gap in gaps:
        text = gap.get('opportunity', gap.get('gap', ''))
        iid  = hashlib.md5(text.encode()).hexdigest()[:8]
        if iid not in ideas:
            ideas[iid] = {
                'id': iid, 'title': text[:80],
                'source': 'competitor_intelligence',
                'priority': gap.get('priority', 5),
                'status': 'pending', 'date': TODAY,
            }
    ledger['ideas'] = ideas
    try: ledger_path.write_text(json.dumps(ledger, indent=2))
    except: pass
    print(f'[intel] Injected {len(gaps)} gap ideas')

def send_weekly_digest(intel_data, gaps):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    if WEEKDAY != 4: return  # Fridays only

    lines = [f'Competitor Intelligence Digest — {TODAY}', '']
    lines.append('COMPETITOR ACTIVITY:')
    for item in intel_data:
        active = '✅ Active' if item.get('is_active') else '😴 Quiet'
        lines.append(f'  {active} {item.get("name",item.get("target",""))}')
        if item.get('recent_dates'):
            lines.append(f'         Last seen: {item["recent_dates"][0]}')
    lines.append('')
    if gaps:
        lines.append('GAPS IDENTIFIED (injected as ideas):')
        for g in gaps:
            lines.append(f'  [{g.get("priority",5)}/10] {g.get("gap","")}')
            lines.append(f'       Opportunity: {g.get("opportunity","")[:100]}')
            lines.append(f'       Effort: {g.get("effort","?")}')
            lines.append('')
    lines += ['', f'All gap ideas added to idea ledger for next evolution cycle.']

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🔍 Intel digest: {len(gaps)} gaps identified | {TODAY}'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[intel] Digest emailed')
    except Exception as e:
        print(f'[intel] Email error: {e}')

def run():
    print(f'\n[intel] Competitor Intelligence Engine — {TODAY}')

    intel_data = []
    for target in MONITOR_TARGETS:
        print(f'[intel] Checking {target["name"]}...')
        result = check_site_activity(target)
        intel_data.append(result)

    # Gap analysis once per week
    gaps = []
    if WEEKDAY == 4:  # Fridays
        stats = {'engines': len(list((ROOT / 'mycelium').glob('*.py')))}
        gaps = identify_gaps(intel_data, stats)
        if gaps:
            inject_gaps_as_ideas(gaps)

    report = {'date': TODAY, 'targets': intel_data, 'gaps': gaps}
    try: (DATA / 'competitor_intel.json').write_text(json.dumps(report, indent=2))
    except: pass

    send_weekly_digest(intel_data, gaps)

    active = sum(1 for i in intel_data if i.get('is_active'))
    print(f'[intel] Active competitors: {active}/{len(intel_data)} | Gaps found: {len(gaps)}')
    print('[intel] Done.')

if __name__ == '__main__':
    run()
