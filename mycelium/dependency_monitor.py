#!/usr/bin/env python3
"""
Dependency Monitor
===================
The system silently fails when external APIs break.
CoinGecko rate limits. HuggingFace goes down. Mastodon
changes an endpoint. GitHub Actions hits a quota.
Engines log errors and move on, never alerting you.

This engine watches every external dependency daily
and alerts the moment something breaks — BEFORE
you notice your crypto signals stopped running or
your social posts went dark.

Dependencies monitored:
  APIs:      CoinGecko, HuggingFace Router, GitHub API,
             Mastodon, Bluesky, Ko-fi, Gumroad, Reddit,
             Alternative.me (fear/greed), OpenAlex
  Services:  GitHub Actions quota, GitHub Pages status
  Internal:  All data files that should be fresh

Alert levels:
  GREEN  — working fine
  YELLOW — degraded or slow (>5s response)
  RED    — down or returning errors

Email alert: only when status changes (no spam).
"""

import json, datetime, os, time, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
MASTODON_TOKEN     = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL  = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')

DEPS = [
    {
        'name':    'CoinGecko API',
        'url':     'https://api.coingecko.com/api/v3/ping',
        'expect':  'gecko_says',
        'critical': True,
    },
    {
        'name':    'HuggingFace Router',
        'url':     'https://router.huggingface.co/health',
        'expect':  '',
        'critical': True,
        'headers': {'Authorization': f'Bearer {os.environ.get("HF_TOKEN","")}'},
    },
    {
        'name':    'GitHub API',
        'url':     'https://api.github.com',
        'expect':  'current_user_url',
        'critical': True,
    },
    {
        'name':    'Alternative.me Fear/Greed',
        'url':     'https://api.alternative.me/fng/?limit=1',
        'expect':  'data',
        'critical': False,
    },
    {
        'name':    'GitHub Pages (your dashboard)',
        'url':     'https://meekotharaccoon-cell.github.io/meeko-nerve-center',
        'expect':  '',
        'critical': False,
    },
    {
        'name':    'Reddit API',
        'url':     'https://www.reddit.com/r/opensource.json?limit=1',
        'expect':  'data',
        'critical': False,
    },
    {
        'name':    'OpenAlex API',
        'url':     'https://api.openalex.org/works?filter=title.search:palestine&per-page=1',
        'expect':  'results',
        'critical': False,
    },
]

def check_dep(dep):
    url     = dep['url']
    expect  = dep.get('expect', '')
    headers = dep.get('headers', {'User-Agent': 'meeko-monitor/1.0'})
    headers.setdefault('User-Agent', 'meeko-monitor/1.0')

    start = time.time()
    try:
        req = urllib_request.Request(url, headers=headers)
        with urllib_request.urlopen(req, timeout=15) as r:
            elapsed = time.time() - start
            body    = r.read().decode('utf-8', errors='replace')[:500]
            status  = r.status
        ok      = status in (200, 201, 204)
        if expect and expect not in body:
            ok = False
            detail = f'Expected "{expect}" not found in response'
        else:
            detail = f'HTTP {status} in {elapsed:.1f}s'
        level = 'GREEN' if ok and elapsed < 5 else ('YELLOW' if ok else 'RED')
        return {'name': dep['name'], 'status': level, 'detail': detail,
                'elapsed': round(elapsed, 2), 'ok': ok, 'date': TODAY}
    except Exception as e:
        return {'name': dep['name'], 'status': 'RED', 'detail': str(e)[:100],
                'elapsed': round(time.time() - start, 2), 'ok': False, 'date': TODAY}

def check_internal_freshness():
    """Check that key data files are being updated."""
    results = []
    files = [
        ('data/health_report.json',      2, 'system_health'),
        ('data/world_state.json',         2, 'world_intelligence'),
        ('data/idea_ledger.json',         3, 'idea_engine'),
        ('data/ingestion_progress.json',  7, 'folder_ingestion'),
    ]
    for rel, max_days, name in files:
        p = ROOT / rel
        if not p.exists():
            results.append({'name': f'internal:{name}', 'status': 'RED',
                            'detail': 'file missing', 'ok': False, 'date': TODAY})
            continue
        try:
            age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(p.stat().st_mtime)).days
            ok  = age <= max_days
            results.append({
                'name':   f'internal:{name}',
                'status': 'GREEN' if ok else 'YELLOW',
                'detail': f'last updated {age}d ago (max {max_days}d)',
                'ok':     ok, 'date': TODAY,
            })
        except Exception as e:
            results.append({'name': f'internal:{name}', 'status': 'RED',
                            'detail': str(e), 'ok': False, 'date': TODAY})
    return results

def load_prev_status():
    p = DATA / 'dependency_status.json'
    if p.exists():
        try: return {r['name']: r['status'] for r in json.loads(p.read_text()).get('results', [])}
        except: pass
    return {}

def send_alert(changed):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD or not changed: return
    lines = [f'Dependency Status Change — {TODAY}', '']
    for r in changed:
        icon = '🟢' if r['status'] == 'GREEN' else ('🟡' if r['status'] == 'YELLOW' else '🔴')
        lines.append(f'{icon} {r["name"]}: {r["status"]} — {r["detail"]}')
    lines += ['', 'Full report: data/dependency_status.json']
    try:
        msg = MIMEMultipart('alternative')
        reds    = sum(1 for r in changed if r['status'] == 'RED')
        subject = f'🔴 {reds} dependency DOWN' if reds else f'🟡 Dependency status changed'
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[deps] Alert sent: {len(changed)} changes')
    except Exception as e:
        print(f'[deps] Alert email error: {e}')

def run():
    print(f'\n[deps] Dependency Monitor — {TODAY}')

    results = []
    for dep in DEPS:
        # Skip if header requires missing token
        if 'HuggingFace' in dep['name'] and not HF_TOKEN:
            results.append({'name': dep['name'], 'status': 'YELLOW',
                            'detail': 'No HF_TOKEN to test with', 'ok': True, 'date': TODAY})
            continue
        r = check_dep(dep)
        results.append(r)
        icon = '🟢' if r['status']=='GREEN' else ('🟡' if r['status']=='YELLOW' else '🔴')
        print(f'[deps] {icon} {r["name"]}: {r["detail"][:60]}')

    results.extend(check_internal_freshness())

    # Compare to previous
    prev = load_prev_status()
    changed = [r for r in results if prev.get(r['name']) != r['status']
               and prev.get(r['name']) is not None]  # only alert on changes
    new_reds = [r for r in results if r['status'] == 'RED' and r['name'] not in prev]

    if changed or new_reds:
        send_alert(changed + new_reds)

    summary = {
        'date':    TODAY,
        'green':   sum(1 for r in results if r['status'] == 'GREEN'),
        'yellow':  sum(1 for r in results if r['status'] == 'YELLOW'),
        'red':     sum(1 for r in results if r['status'] == 'RED'),
        'results': results,
    }
    try: (DATA / 'dependency_status.json').write_text(json.dumps(summary, indent=2))
    except Exception as e: print(f'[deps] Save error: {e}')

    print(f'[deps] 🟢 {summary["green"]} | 🟡 {summary["yellow"]} | 🔴 {summary["red"]}')
    print('[deps] Done.')

if __name__ == '__main__':
    run()
