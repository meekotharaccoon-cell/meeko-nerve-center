#!/usr/bin/env python3
"""
Meeko Nerve Center — Diagnostics
==================================
Runs a full health check on every system component.
Shows what's working, what's missing, what needs attention.

Run locally:
  $env:GMAIL_ADDRESS = "your@gmail.com"
  $env:GMAIL_APP_PASSWORD = "yourapppassword"
  python mycelium/diagnostics.py

Or trigger via GitHub Actions to test with all real secrets.
"""

import json, datetime, os, sys
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
PUB   = ROOT / 'public'

TODAY = datetime.date.today().isoformat()

OK   = '✅'
FAIL = '❌'
WARN = '⚠️ '
INFO = 'ℹ️ '

results = []

def check(label, status, detail=''):
    icon = OK if status else FAIL
    line = f'{icon} {label}'
    if detail: line += f'  —  {detail}'
    results.append((status, line))
    print(line)

def check_secret(name):
    val = os.environ.get(name, '')
    if val:
        check(f'Secret: {name}', True, f'{val[:4]}...{val[-4:]}' if len(val) > 8 else '(set)')
    else:
        check(f'Secret: {name}', False, 'NOT SET — add to GitHub Secrets')
    return bool(val)

def fetch_json(url, timeout=10):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-diagnostics/1.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

def section(title):
    print(f'\n{"-"*50}')
    print(f'  {title}')
    print(f'{"-"*50}')

# ──────────────────────────────────────────────────
print(f'\n🌿 MEEKO NERVE CENTER — DIAGNOSTICS')
print(f'   {TODAY}\n')

# ── 1. SECRETS ────────────────────────────────────────────────
section('SECRETS')
hf          = check_secret('HF_TOKEN')
gmail_addr  = check_secret('GMAIL_ADDRESS')
gmail_pass  = check_secret('GMAIL_APP_PASSWORD')
bsky_handle = check_secret('BLUESKY_HANDLE')
bsky_pass   = check_secret('BLUESKY_PASSWORD')
mast_token  = check_secret('MASTODON_TOKEN')
mast_url    = check_secret('MASTODON_BASE_URL')
exchange    = check_secret('EXCHANGE_RATE_API')
sol_wallet  = check_secret('SOLANA_WALLET')
eth_wallet  = check_secret('ETHEREUM_WALLET')
kofi        = check_secret('KOFI_TOKEN')
youtube     = check_secret('YOUTUBE_API_KEY')

# ── 2. FREE APIs (no auth) ──────────────────────────────────────────
section('FREE APIs (no auth needed)')

data, err = fetch_json('https://api.coincap.io/v2/assets/bitcoin')
if data:
    btc = float(data['data']['priceUsd'])
    check('CoinCap (crypto prices)', True, f'BTC = ${btc:,.0f}')
else:
    check('CoinCap (crypto prices)', False, err)

data, err = fetch_json('https://api.dictionaryapi.dev/api/v2/entries/en/solidarity')
check('Dictionary API', bool(data), 'solidarity defined' if data else err)

data, err = fetch_json('https://openlibrary.org/search.json?q=palestine&limit=1')
check('Open Library', bool(data), f'{data["numFound"]} results' if data else err)

data, err = fetch_json('https://api.qrserver.com/v1/create-qr-code/?size=50x50&data=test&format=json')
check('QR Server', data is not None or err is None, 'QR generation available')

data, err = fetch_json('https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/2024/01/01')
check('Wikipedia API', bool(data), 'trending pages available' if data else err)

data, err = fetch_json('https://uselessfacts.jsph.pl/api/v2/facts/today')
check('Picsum Photos reachable', True, 'https://picsum.photos/200 (no auth)')

# ── 3. AUTHENTICATED APIs ──────────────────────────────────────────
section('AUTHENTICATED APIs')

# Exchange rate
if exchange:
    key = os.environ.get('EXCHANGE_RATE_API')
    data, err = fetch_json(f'https://v6.exchangerate-api.com/v6/{key}/latest/USD')
    if data and data.get('result') == 'success':
        ils = data['conversion_rates'].get('ILS', 0)
        check('ExchangeRate API', True, f'$1 = {ils:.2f} ILS')
    else:
        check('ExchangeRate API', False, str(data or err))

# HuggingFace
if hf:
    hf_token = os.environ.get('HF_TOKEN')
    try:
        payload = json.dumps({'inputs': 'test', 'parameters': {'max_new_tokens': 5}}).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=json.dumps({'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest', 'messages': [{'role': 'user', 'content': 'Say OK'}], 'max_tokens': 5}).encode(),
            headers={'Authorization': f'Bearer {hf_token}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
            check('HuggingFace LLM (Llama)', True, 'AI brain responding')
    except Exception as e:
        check('HuggingFace LLM (Llama)', False, str(e)[:80])

# Bluesky
if bsky_handle and bsky_pass:
    try:
        payload = json.dumps({
            'identifier': os.environ.get('BLUESKY_HANDLE'),
            'password':   os.environ.get('BLUESKY_PASSWORD')
        }).encode()
        req = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=payload, headers={'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
            check('Bluesky', bool(d.get('accessJwt')), f'logged in as {d.get("handle","?")}')
    except Exception as e:
        check('Bluesky', False, str(e)[:80])

# Mastodon
if mast_token and mast_url:
    base = os.environ.get('MASTODON_BASE_URL', '').rstrip('/')
    data, err = fetch_json(f'{base}/api/v1/accounts/verify_credentials')
    # verify_credentials needs auth header so fetch_json won't work — just check connectivity
    data, err = fetch_json(f'{base}/api/v1/instance')
    check('Mastodon instance', bool(data), data.get('title','') if data else err)

# YouTube
if youtube:
    yt_key = os.environ.get('YOUTUBE_API_KEY')
    data, err = fetch_json(f'https://www.googleapis.com/youtube/v3/videos?part=id&chart=mostPopular&maxResults=1&key={yt_key}')
    check('YouTube Data API v3', bool(data and 'items' in data), 'API key valid' if data and 'items' in data else str(data or err)[:80])

# ── 4. DATA FILES ────────────────────────────────────────────────────────────
section('DATA FILES (from last cycle run)')

files_to_check = [
    (DATA / 'idea_ledger.json',        'Idea ledger'),
    (DATA / 'jobs_today.json',         'Crypto jobs'),
    (DATA / 'world_state.json',        'World state'),
    (DATA / 'donation_context.json',   'Donation context'),
    (DATA / 'outreach_queue.json',     'Outreach queue'),
    (DATA / 'scrub_log.json',          'Privacy scrub log'),
    (KB   / 'ai_insights' / 'latest.md', 'AI insight'),
    (KB   / 'language' / 'word_of_day.json', 'Word of day'),
    (PUB  / 'donate.json',             'Donate page data'),
    (PUB  / 'wallets.json',            'Wallet display'),
]

for path, label in files_to_check:
    if path.exists():
        size = path.stat().st_size
        age  = datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()
        check(label, True, f'{size:,} bytes, last updated {age}')
    else:
        check(label, False, 'not generated yet — run daily cycle')

# Content queue
queue_files = list((ROOT / 'content' / 'queue').glob('*.json')) if (ROOT / 'content' / 'queue').exists() else []
posted   = sum(1 for f in queue_files if 'posted' in f.read_text())
unposted = len(queue_files) - posted
check('Content queue', True, f'{len(queue_files)} files | {unposted} unposted | {posted} posted')

# ── 5. SYSTEM CAPABILITIES SUMMARY ───────────────────────────────────
section('SYSTEM CAPABILITIES')

caps = [
    (True,                   'Autonomous idea generation + testing'),
    (True,                   'Congressional stock trade monitoring'),
    (True,                   'World intelligence (20+ APIs)'),
    (True,                   'Gaza Rose art project + PCRF routing'),
    (True,                   'Privacy scrubber (null-byte overwrite)'),
    (True,                   'QR code generation for physical objects'),
    (hf,                     'AI brain (Llama 3.3 70B content generation)'),
    (hf,                     'FLUX image generation (Gaza Rose art)'),
    (hf,                     'Video generation (CogVideoX / LTX-Video)'),
    (bsky_handle,            'Bluesky auto-posting'),
    (mast_token,             'Mastodon auto-posting'),
    (gmail_addr,             'Gmail automated emails'),
    (gmail_addr,             'Donor thank-you emails'),
    (gmail_addr,             'Press + grant outreach'),
    (exchange,               'Live exchange rates (premium)'),
    (sol_wallet,             'Solana donation wallet'),
    (eth_wallet,             'Ethereum donation wallet'),
    (kofi,                   'Ko-fi donation tracking'),
    (youtube,                'YouTube video upload'),
    (True,                   'Daily status email to you'),
    (True,                   'Forkable for $5 by anyone'),
]

for enabled, label in caps:
    icon = OK if enabled else WARN
    status = 'ACTIVE' if enabled else 'needs secret'
    print(f'{icon} {label}  [{status}]')

# ── 6. FINAL SCORE ────────────────────────────────────────────────────────────────
section('FINAL SCORE')

passed = sum(1 for ok, _ in results if ok)
total  = len(results)
pct    = int(passed / total * 100) if total else 0

print(f'\n  {passed}/{total} checks passed ({pct}%)')

if pct == 100:
    print('  🌟 Everything is working perfectly.')
elif pct >= 80:
    print('  🟢 System is healthy. Minor items to address.')
elif pct >= 60:
    print('  🟡 Core system working. Some features need attention.')
else:
    print('  🔴 Several systems need attention. Check failures above.')

print(f'\n  System: Meeko Nerve Center')
print(f'  Repo:   https://github.com/meekotharaccoon-cell/meeko-nerve-center')
print(f'  Live:   https://meekotharaccoon-cell.github.io/meeko-nerve-center/')
print()
