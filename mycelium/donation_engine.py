#!/usr/bin/env python3
"""
Donation Engine
================
Wires together ALL donation channels into one unified system.

Channels:
  - Ko-fi         (KOFI_TOKEN)         — fiat, most common
  - Solana        (SOLANA_WALLET)       — crypto, fast + cheap fees
  - Ethereum      (ETHEREUM_WALLET)     — crypto, wide adoption
  - Bitcoin/Lightning                   — via Strike (manual)
  - Exchange rates (EXCHANGE_RATE_API)  — show real-time value context

What this does:
  1. Generates donation context: "$10 = X shekels today"
  2. Builds donation widget HTML for solarpunk.html + consent.html
  3. Tracks Ko-fi webhook events (when someone donates)
  4. Generates thank-you content when donations come in
  5. Shows wallet addresses for crypto donations
  6. Updates public/donate.json for the website to use

Outputs:
  - public/donate.json          live donation data for website
  - public/donation_widget.html embeddable widget
  - data/donation_context.json  exchange rate context
  - data/kofi_events.json       Ko-fi donation history
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
PUBLIC = ROOT / 'public'
PUBLIC.mkdir(exist_ok=True)

TODAY = datetime.date.today().isoformat()

# Secrets
EXCHANGE_API_KEY  = os.environ.get('EXCHANGE_RATE_API', '')
SOLANA_WALLET     = os.environ.get('SOLANA_WALLET', '')
ETHEREUM_WALLET   = os.environ.get('ETHEREUM_WALLET', '')
KOFI_TOKEN        = os.environ.get('KOFI_TOKEN', '')

# Currencies relevant to your donor base + Gaza context
KEY_CURRENCIES = ['EUR', 'GBP', 'ILS', 'JOD', 'EGP', 'TRY', 'CAD', 'AUD', 'SAR', 'AED']

def fetch_exchange_rates():
    """Get live exchange rates. Uses premium key if available, falls back to free."""
    print('[donate] Fetching exchange rates...')
    
    if EXCHANGE_API_KEY:
        # Premium ExchangeRate-API (higher limits, more currencies)
        url = f'https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/USD'
    else:
        # Free fallback
        url = 'https://open.er-api.com/v6/latest/USD'
    
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            rates = data.get('rates', data.get('conversion_rates', {}))
            result = {c: rates[c] for c in KEY_CURRENCIES if c in rates}
            print(f'[donate] Got {len(result)} exchange rates')
            return result
    except Exception as e:
        print(f'[donate] Exchange rate error: {e}')
        return {}

def build_donation_context(rates):
    """Build human-readable donation context messages."""
    messages = []
    
    if 'ILS' in rates:
        ils = rates['ILS']
        messages += [
            f"$5 = {round(5*ils)} Israeli Shekels",
            f"$10 = {round(10*ils)} Israeli Shekels",
            f"$25 = {round(25*ils)} Shekels \u2014 roughly a week of groceries in Gaza",
        ]
    if 'EGP' in rates:
        egp = rates['EGP']
        messages.append(f"$10 = {round(10*egp)} Egyptian Pounds")
    if 'EUR' in rates:
        messages.append(f"$10 = \u20ac{round(10*rates['EUR'], 2)}")
    if 'GBP' in rates:
        messages.append(f"$10 = \u00a3{round(10*rates['GBP'], 2)}")
    
    return messages

def fetch_kofi_recent():
    """Check Ko-fi for recent donations via their API."""
    if not KOFI_TOKEN:
        print('[donate] No KOFI_TOKEN — skipping Ko-fi check')
        return []
    
    # Ko-fi uses webhooks rather than a polling API.
    # When someone donates, Ko-fi POSTs to your webhook URL.
    # For now we track via a local events file that the webhook populates.
    events_path = DATA / 'kofi_events.json'
    if events_path.exists():
        try:
            return json.loads(events_path.read_text()).get('events', [])
        except:
            pass
    return []

def build_donate_json(rates, context_messages):
    """Build the public donate.json used by the website."""
    donate = {
        'date':              TODAY,
        'exchange_rates':    rates,
        'context_messages':  context_messages,
        'channels': {
            'kofi': {
                'url':     'https://ko-fi.com/',  # update with your Ko-fi username
                'label':   'Support on Ko-fi',
                'accepts': ['USD', 'EUR', 'GBP', 'card'],
                'note':    'Most accessible for most people',
            },
            'solana': {
                'address': SOLANA_WALLET,
                'label':   'Donate in SOL',
                'network': 'Solana',
                'note':    'Fast, cheap fees',
                'qr_url':  f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=solana:{SOLANA_WALLET}' if SOLANA_WALLET else '',
            },
            'ethereum': {
                'address': ETHEREUM_WALLET,
                'label':   'Donate in ETH/USDC',
                'network': 'Ethereum',
                'note':    'Widely supported',
                'qr_url':  f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=ethereum:{ETHEREUM_WALLET}' if ETHEREUM_WALLET else '',
            },
            'gumroad': {
                'url':     'https://gumroad.com/',  # update with your Gumroad link
                'label':   'Buy Gaza Rose Art',
                'note':    '70% goes directly to PCRF',
            },
        },
        'pcrf_note': '70% of Gaza Rose proceeds go to the Palestinian Children\'s Relief Fund (PCRF). See pcrf.net',
    }
    
    (PUBLIC / 'donate.json').write_text(json.dumps(donate, indent=2))
    print('[donate] public/donate.json updated')
    return donate

def build_donation_widget(donate_data):
    """Build an embeddable donation widget for the website."""
    channels = donate_data.get('channels', {})
    sol = channels.get('solana', {})
    eth = channels.get('ethereum', {})
    context = donate_data.get('context_messages', [])
    
    context_html = ''.join(f'<li>{m}</li>' for m in context[:3])
    
    sol_block = ''
    if sol.get('address'):
        sol_block = f'''
      <div class="wallet">
        <div class="wallet-label">SOL (Solana)</div>
        <div class="wallet-addr">{sol["address"][:20]}...</div>
        <img src="{sol["qr_url"]}" alt="Solana QR" class="wallet-qr">
        <button onclick="copyAddr(\'{sol["address"]}\')">Copy Address</button>
      </div>'''
    
    eth_block = ''
    if eth.get('address'):
        eth_block = f'''
      <div class="wallet">
        <div class="wallet-label">ETH / USDC (Ethereum)</div>
        <div class="wallet-addr">{eth["address"][:20]}...</div>
        <img src="{eth["qr_url"]}" alt="Ethereum QR" class="wallet-qr">
        <button onclick="copyAddr(\'{eth["address"]}\')">Copy Address</button>
      </div>'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Support the Mission</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Georgia', serif;
      background: #1a2a1a;
      color: #e8e0d0;
      padding: 2rem 1rem;
    }}
    h1 {{ font-size: 1.6rem; color: #9ed89e; margin-bottom: 0.5rem; }}
    .sub {{ color: #8a9a7a; margin-bottom: 1.5rem; font-size: 0.95rem; }}
    .pcrf-note {{
      background: #2a3a2a;
      border-left: 3px solid #7eb87e;
      padding: 0.8rem 1rem;
      margin-bottom: 1.5rem;
      font-size: 0.9rem;
      color: #b8d0b0;
    }}
    .context-rates {{
      font-size: 0.85rem;
      color: #6a8a6a;
      margin-bottom: 1.5rem;
    }}
    .context-rates ul {{ list-style: none; line-height: 2; }}
    .channels {{ display: grid; gap: 1rem; }}
    .channel {{
      background: #243024;
      border-radius: 10px;
      padding: 1.2rem;
      border: 1px solid #3a5a3a;
    }}
    .channel h3 {{ font-size: 1rem; color: #9ed89e; margin-bottom: 0.5rem; }}
    .channel .note {{ font-size: 0.8rem; color: #6a8a6a; margin-bottom: 0.8rem; }}
    .channel a, .channel button {{
      display: inline-block;
      background: #3a6a3a;
      color: #c8e8c8;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      text-decoration: none;
      font-size: 0.9rem;
      border: none;
      cursor: pointer;
      font-family: inherit;
    }}
    .wallet-addr {{
      font-family: monospace;
      font-size: 0.8rem;
      color: #8aaa8a;
      margin: 0.5rem 0;
      word-break: break-all;
    }}
    .wallet-qr {{ display: block; margin: 0.5rem 0; border-radius: 6px; }}
    .copied {{ color: #7eb87e !important; }}
  </style>
</head>
<body>
  <h1>\U0001f33f Support the Mission</h1>
  <div class="sub">Every contribution funds Palestinian children and open source liberation tools.</div>
  
  <div class="pcrf-note">
    \U0001f3f5 <strong>Gaza Rose Art:</strong> 70% of every sale goes directly to PCRF (Palestinian Children\'s Relief Fund).<br>
    <a href="https://pcrf.net" target="_blank" style="color:#9ed89e">pcrf.net</a>
  </div>
  
  <div class="context-rates">
    <strong>Your donation today:</strong>
    <ul>{context_html}</ul>
  </div>
  
  <div class="channels">
    <div class="channel">
      <h3>\U0001f48c Ko-fi — Easiest</h3>
      <div class="note">Card, PayPal, one-time or monthly. Most accessible.</div>
      <a href="https://ko-fi.com" target="_blank">Support on Ko-fi \u2192</a>
    </div>
    
    <div class="channel">
      <h3>\U0001f3fa Gaza Rose Art — 70% to PCRF</h3>
      <div class="note">Buy art. Fund Palestinian children directly.</div>
      <a href="https://gumroad.com" target="_blank">See Gaza Rose Gallery \u2192</a>
    </div>
    {sol_block}
    {eth_block}
  </div>
  
  <script>
    function copyAddr(addr) {{
      navigator.clipboard.writeText(addr).then(() => {{
        event.target.textContent = '\u2713 Copied!';
        event.target.classList.add('copied');
        setTimeout(() => {{
          event.target.textContent = 'Copy Address';
          event.target.classList.remove('copied');
        }}, 2000);
      }});
    }}
  </script>
</body>
</html>'''
    
    (PUBLIC / 'donate.html').write_text(html)
    print('[donate] public/donate.html built')

def generate_thank_you_content(events):
    """Generate thank-you posts when donations come in."""
    if not events:
        return
    
    recent = [e for e in events if e.get('date', '') >= TODAY]
    if not recent:
        return
    
    total = sum(float(e.get('amount', 0)) for e in recent)
    count = len(recent)
    
    post = f"""Today {count} person{'s' if count > 1 else ''} chose to support Palestinian children.\n
Total: ${total:.0f} \u2014 {round(total * 0.7):.0f} of that goes directly to PCRF.\n\nEvery single one of you: thank you for being YOU.\n\nGaza Rose gallery \u2192 link in bio\n#GazaRose #PCRF #Palestine #Solidarity"""
    
    (ROOT / 'content' / 'queue' / f'thankyou_{TODAY}.json').write_text(
        json.dumps([{'platform': 'mastodon', 'type': 'thankyou', 'text': post}], indent=2)
    )
    print(f'[donate] Thank-you post generated for {count} donations')

def run():
    print(f'[donate] Donation Engine \u2014 {TODAY}')
    
    rates    = fetch_exchange_rates()
    context  = build_donation_context(rates)
    donate   = build_donate_json(rates, context)
    build_donation_widget(donate)
    
    events   = fetch_kofi_recent()
    generate_thank_you_content(events)
    
    # Save context for other scripts to use
    (DATA / 'donation_context.json').write_text(json.dumps({
        'date':     TODAY,
        'rates':    rates,
        'messages': context,
        'wallets': {
            'solana':   SOLANA_WALLET,
            'ethereum': ETHEREUM_WALLET,
        }
    }, indent=2))
    
    print(f'[donate] Done. Rates: {len(rates)} currencies. Channels: Ko-fi + SOL + ETH + Gumroad.')
    if rates.get('ILS'):
        print(f'[donate] $10 = {round(10*rates["ILS"])} ILS today')
    
    return donate

if __name__ == '__main__':
    run()
