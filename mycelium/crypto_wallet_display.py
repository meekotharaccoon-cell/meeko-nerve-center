#!/usr/bin/env python3
"""
Crypto Wallet Display
======================
Builds public-facing wallet info for donation pages.
Uses GeckoTerminal + CoinCap for live prices.
Shows current SOL and ETH value in USD.

Your wallet addresses are PUBLIC by design —
they need to be visible for people to send to them.
Private keys are NEVER touched here. Only public addresses.

Outputs:
  - public/wallets.json     live wallet display data
  - public/wallets.html     embeddable wallet widget
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT   = Path(__file__).parent.parent
PUBLIC = ROOT / 'public'
DATA   = ROOT / 'data'
PUBLIC.mkdir(exist_ok=True)

TODAY = datetime.date.today().isoformat()

SOLANA_WALLET   = os.environ.get('SOLANA_WALLET', '')
ETHEREUM_WALLET = os.environ.get('ETHEREUM_WALLET', '')

def fetch_json(url):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except:
        return None

def get_crypto_prices():
    data = fetch_json('https://api.coincap.io/v2/assets?limit=20')
    if not data: return {}
    prices = {}
    for asset in data.get('data', []):
        sym = asset.get('symbol', '').upper()
        if sym in ('SOL', 'ETH', 'BTC'):
            prices[sym] = {
                'price':      round(float(asset.get('priceUsd', 0)), 2),
                'change_24h': round(float(asset.get('changePercent24Hr', 0)), 2),
            }
    return prices

def build_wallets_json(prices):
    wallets = {
        'date': TODAY,
        'wallets': [],
        'note': 'Public wallet addresses for receiving donations. Never share private keys.',
    }
    
    if SOLANA_WALLET:
        sol_price = prices.get('SOL', {}).get('price', 0)
        wallets['wallets'].append({
            'network':   'Solana',
            'symbol':    'SOL',
            'address':   SOLANA_WALLET,
            'price_usd': sol_price,
            'qr_url':    f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=solana:{SOLANA_WALLET}',
            'explorer':  f'https://explorer.solana.com/address/{SOLANA_WALLET}',
            'apps':      ['Phantom', 'Solflare', 'Coinbase'],
            'note':      'Fast transactions, low fees. Great for smaller donations.',
        })
    
    if ETHEREUM_WALLET:
        eth_price = prices.get('ETH', {}).get('price', 0)
        wallets['wallets'].append({
            'network':   'Ethereum',
            'symbol':    'ETH',
            'address':   ETHEREUM_WALLET,
            'price_usd': eth_price,
            'qr_url':    f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=ethereum:{ETHEREUM_WALLET}',
            'explorer':  f'https://etherscan.io/address/{ETHEREUM_WALLET}',
            'apps':      ['MetaMask', 'Coinbase', 'Rainbow'],
            'note':      'Also accepts USDC, USDT, and other ERC-20 tokens.',
        })
    
    (PUBLIC / 'wallets.json').write_text(json.dumps(wallets, indent=2))
    print(f'[wallets] public/wallets.json built ({len(wallets["wallets"])} wallets)')
    return wallets

def build_wallet_widget(wallets_data, prices):
    cards = ''
    for w in wallets_data.get('wallets', []):
        price_info = ''
        p = prices.get(w['symbol'], {})
        if p.get('price'):
            change = p['change_24h']
            color = '#7eb87e' if change >= 0 else '#e87e7e'
            price_info = f'<div class="price">${p["price"]:,.2f} <span style="color:{color}">{change:+.1f}%</span></div>'
        
        apps = ', '.join(w.get('apps', []))
        cards += f'''
    <div class="wallet-card">
      <div class="wallet-header">
        <span class="network">{w["network"]}</span>
        {price_info}
      </div>
      <div class="wallet-note">{w["note"]}</div>
      <img src="{w["qr_url"]}" alt="{w["network"]} QR Code" class="qr">
      <div class="addr" id="addr-{w["symbol"]}">{w["address"]}</div>
      <div class="actions">
        <button onclick="copyAddr(\'{w["address"]}\', \'{w["symbol"]}\')">\U0001f4cb Copy Address</button>
        <a href="{w["explorer"]}" target="_blank">\U0001f50d Explorer</a>
      </div>
      <div class="apps">Works with: {apps}</div>
    </div>'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Crypto Donation Wallets</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: monospace; background: #0d1a0d; color: #c8e0c0; padding: 2rem 1rem; }}
    h2 {{ color: #7eb87e; margin-bottom: 1.5rem; font-size: 1.3rem; }}
    .wallet-card {{
      background: #1a2a1a;
      border: 1px solid #2a4a2a;
      border-radius: 10px;
      padding: 1.2rem;
      margin-bottom: 1rem;
    }}
    .wallet-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }}
    .network {{ font-weight: bold; color: #9ed89e; font-size: 1.1rem; }}
    .price {{ font-size: 0.9rem; }}
    .wallet-note {{ font-size: 0.8rem; color: #6a8a6a; margin-bottom: 0.8rem; }}
    .qr {{ display: block; margin: 0.5rem 0; border-radius: 6px; }}
    .addr {{
      font-size: 0.7rem;
      color: #5a7a5a;
      word-break: break-all;
      margin: 0.5rem 0;
      padding: 0.5rem;
      background: #0a150a;
      border-radius: 4px;
    }}
    .actions {{ display: flex; gap: 0.5rem; margin: 0.5rem 0; flex-wrap: wrap; }}
    .actions button, .actions a {{
      background: #2a4a2a;
      color: #9ed89e;
      border: none;
      padding: 0.4rem 0.8rem;
      border-radius: 5px;
      cursor: pointer;
      font-family: monospace;
      font-size: 0.85rem;
      text-decoration: none;
    }}
    .apps {{ font-size: 0.75rem; color: #4a6a4a; margin-top: 0.5rem; }}
  </style>
</head>
<body>
  <h2>\U0001fa99 Crypto Donation Wallets</h2>
  {cards}
  <script>
    function copyAddr(addr, sym) {{
      navigator.clipboard.writeText(addr);
      const el = document.getElementById('addr-' + sym);
      el.style.color = '#7eb87e';
      setTimeout(() => el.style.color = '#5a7a5a', 2000);
    }}
  </script>
</body>
</html>'''
    
    (PUBLIC / 'wallets.html').write_text(html)
    print('[wallets] public/wallets.html built')

def run():
    print(f'[wallets] Crypto Wallet Display \u2014 {TODAY}')
    
    if not SOLANA_WALLET and not ETHEREUM_WALLET:
        print('[wallets] No wallet addresses configured. Set SOLANA_WALLET and/or ETHEREUM_WALLET secrets.')
        return {}
    
    prices = get_crypto_prices()
    wallets = build_wallets_json(prices)
    build_wallet_widget(wallets, prices)
    
    for w in wallets.get('wallets', []):
        p = prices.get(w['symbol'], {})
        print(f'[wallets] {w["network"]}: {w["address"][:16]}... | ${p.get("price", 0):,.2f}')
    
    return wallets

if __name__ == '__main__':
    run()
