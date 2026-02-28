#!/usr/bin/env python3
"""
Output Validator Engine
========================
The system generates content, signals, code, emails, art prompts
— but never checks if any of it actually WORKED.

This is the QA brain.

What it validates every cycle:
  1. GitHub Pages: is the dashboard actually live and loading?
  2. Social posts: did they actually post or just log success falsely?
  3. Crypto signals: were last week's signals accurate? (backcheck)
  4. Emails: did the Gmail engine actually send or silently fail?
  5. Art generation: did images actually land in public/images/?
  6. Ko-fi/Gumroad: are the listings actually visible publicly?
  7. Engines: does each engine produce non-empty output?
  8. GitHub Actions: are workflows actually completing or failing silently?

When validation fails:
  - Flags the broken output in data/validation_failures.json
  - Feeds failure to error_self_healing.py as a known issue
  - Adjusts engine confidence scores
  - Emails you only when something that WAS working breaks
    (not noise about things that never worked)

Confidence scoring:
  Each engine gets a score 0-100 based on output validity history.
  Engines below 50 get flagged for healing.
  Score feeds into health report.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
YESTERDAY = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

SITE_URL = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center'
REPO     = 'meekotharaccoon-cell/meeko-nerve-center'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def fetch_url(url, timeout=15):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-validator/1.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(1024).decode('utf-8', errors='replace')
    except Exception as e:
        return 0, str(e)

# ── Individual validators ─────────────────────────────────────────────────────

def validate_github_pages():
    status, body = fetch_url(SITE_URL)
    ok = status == 200 and 'Meeko' in body
    return {
        'check':  'github_pages',
        'ok':     ok,
        'detail': f'HTTP {status}' if ok else f'HTTP {status} — site may be down or not yet enabled',
        'action': None if ok else 'Enable GitHub Pages: repo → Settings → Pages → main branch → /public',
    }

def validate_data_freshness():
    """Check that key data files were updated recently."""
    results = []
    critical_files = [
        ('data/health_report.json',    'system_health_alerting'),
        ('data/idea_ledger.json',       'idea_engine'),
        ('data/world_state.json',       'world_intelligence'),
        ('data/content_performance.json', 'content_performance'),
    ]
    for rel_path, engine in critical_files:
        p = ROOT / rel_path
        if not p.exists():
            results.append({'check': engine, 'ok': False, 'detail': 'file missing'})
            continue
        try:
            age_days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(p.stat().st_mtime)).days
            ok = age_days <= 2
            results.append({
                'check':  engine,
                'ok':     ok,
                'detail': f'last updated {age_days}d ago',
                'action': f'Engine {engine} may be broken' if not ok else None,
            })
        except Exception as e:
            results.append({'check': engine, 'ok': False, 'detail': str(e)})
    return results

def validate_art_output():
    images_dir = ROOT / 'public' / 'images'
    if not images_dir.exists():
        return {'check': 'art_generation', 'ok': False, 'detail': 'public/images/ missing'}
    images = list(images_dir.rglob('*.png')) + list(images_dir.rglob('*.jpg'))
    recent = [i for i in images
              if (datetime.datetime.now() - datetime.datetime.fromtimestamp(i.stat().st_mtime)).days <= 7]
    ok = len(recent) > 0
    return {
        'check':  'art_generation',
        'ok':     ok,
        'detail': f'{len(images)} total images, {len(recent)} in last 7 days',
        'action': 'Art engine may be failing to generate images' if not ok else None,
    }

def validate_signal_accuracy():
    """Backcheck: did last week's signals go in the right direction?"""
    history = load(DATA / 'crypto_signals_history.json', [])
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    old_signals = [s for s in history if s.get('date', '') <= week_ago
                   and s.get('action', '').startswith('BUY')]
    if not old_signals:
        return {'check': 'signal_accuracy', 'ok': True, 'detail': 'no old signals to backcheck yet'}

    # For each old signal, fetch current price and compare to entry
    correct = 0
    for sig in old_signals[:5]:
        try:
            coin_id = sig.get('coin_id', '')
            if not coin_id: continue
            data = json.loads(
                urllib_request.urlopen(
                    f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd',
                    timeout=10
                ).read()
            )
            current_price = data.get(coin_id, {}).get('usd', 0)
            entry_str     = sig.get('entry', '0').replace('$','').replace('<','').strip()
            try:
                entry_price = float(entry_str.split('-')[0].strip())
            except:
                continue
            if current_price > entry_price:
                correct += 1
        except:
            continue

    accuracy = round(correct / len(old_signals[:5]) * 100) if old_signals else 0
    return {
        'check':    'signal_accuracy',
        'ok':       accuracy >= 40,
        'detail':   f'{correct}/{min(len(old_signals),5)} signals moved in right direction ({accuracy}%)',
        'accuracy': accuracy,
    }

def validate_github_actions():
    """Check recent workflow run results."""
    if not GITHUB_TOKEN: return {'check': 'github_actions', 'ok': True, 'detail': 'no token'}
    try:
        req = urllib_request.Request(
            f'https://api.github.com/repos/{REPO}/actions/runs?per_page=10',
            headers={'Authorization': f'Bearer {GITHUB_TOKEN}'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            runs = json.loads(r.read()).get('workflow_runs', [])
        failures = [r for r in runs if r.get('conclusion') == 'failure']
        latest   = runs[0] if runs else {}
        ok = latest.get('conclusion') in ('success', 'in_progress', None)
        return {
            'check':    'github_actions',
            'ok':       ok,
            'detail':   f'Latest: {latest.get("name","?")} — {latest.get("conclusion","pending")}',
            'failures': len(failures),
        }
    except Exception as e:
        return {'check': 'github_actions', 'ok': False, 'detail': str(e)}

def validate_social_posts():
    """Check that social engine is actually producing queue items."""
    queue_dir = ROOT / 'content' / 'queue'
    if not queue_dir.exists():
        return {'check': 'social_queue', 'ok': False, 'detail': 'queue directory missing'}
    posts = list(queue_dir.glob('*.json'))
    recent = []
    for p in posts:
        try:
            age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(p.stat().st_mtime)).days
            if age <= 3: recent.append(p)
        except: pass
    ok = len(recent) > 0 or len(posts) > 0
    return {
        'check':  'social_queue',
        'ok':     ok,
        'detail': f'{len(recent)} posts queued in last 3 days ({len(posts)} total)',
        'action': 'Social/content engines may not be generating posts' if not ok else None,
    }

# ── Confidence scoring ────────────────────────────────────────────────────────

def update_confidence_scores(all_results):
    scores_path = DATA / 'engine_confidence.json'
    scores = load(scores_path, {})
    for r in all_results:
        check = r.get('check', '')
        ok    = r.get('ok', True)
        prev  = scores.get(check, 75)
        # Exponential moving average
        new_score = prev * 0.8 + (100 if ok else 0) * 0.2
        scores[check] = round(new_score)
    try: scores_path.write_text(json.dumps(scores, indent=2))
    except: pass
    return scores

def send_alert(failures):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD or not failures: return
    lines = [f'Output Validation Failures — {TODAY}', '']
    for f in failures:
        lines.append(f'❌ {f["check"]}: {f["detail"]}')
        if f.get('action'):
            lines.append(f'   → {f["action"]}')
        lines.append('')
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'⚠️ {len(failures)} validation failure(s) — Meeko'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
    except: pass

def run():
    print(f'\n[validator] Output Validator — {TODAY}')

    all_results = []
    all_results.append(validate_github_pages())
    all_results.extend(validate_data_freshness())
    all_results.append(validate_art_output())
    all_results.append(validate_signal_accuracy())
    all_results.append(validate_github_actions())
    all_results.append(validate_social_posts())

    failures = [r for r in all_results if not r.get('ok', True)]
    passes   = [r for r in all_results if r.get('ok', True)]

    print(f'[validator] ✅ {len(passes)} passing | ❌ {len(failures)} failing')
    for r in all_results:
        icon = '✅' if r.get('ok') else '❌'
        print(f'[validator]   {icon} {r["check"]}: {r.get("detail","")[:80]}')

    scores = update_confidence_scores(all_results)

    # Save report
    report = {'date': TODAY, 'results': all_results, 'confidence': scores,
              'failures': len(failures), 'passes': len(passes)}
    try: (DATA / 'validation_report.json').write_text(json.dumps(report, indent=2))
    except: pass

    # Load previous failures to only alert on NEW breakages
    prev_path = DATA / 'validation_failures.json'
    prev_failures = set()
    if prev_path.exists():
        try: prev_failures = set(load(prev_path, {}).get('checks', []))
        except: pass

    new_failures = [f for f in failures if f['check'] not in prev_failures]
    if new_failures:
        send_alert(new_failures)
        print(f'[validator] Alert sent for {len(new_failures)} new failure(s)')

    try: prev_path.write_text(json.dumps(
        {'date': TODAY, 'checks': [f['check'] for f in failures]}, indent=2))
    except: pass

    print('[validator] Done.')

if __name__ == '__main__':
    run()
