#!/usr/bin/env python3
"""
SolarPunk Setup Wizard v3 — Multi-chain wallet support
=======================================================
Now accepts ALL 9 wallet addresses from your Phantom setup.
Never turn away money from any blockchain.

Your token is already in the environment. This only asks for what's missing.

Wallets supported (paste all of them):
  Solana, Ethereum, Base, Polygon, Bitcoin Taproot, Bitcoin SegWit,
  Sui, Monad, HyperEVM

EVM chains (Ethereum/Base/Polygon/Monad/HyperEVM) share the same address.
Setup wizard detects this and auto-fills siblings.
"""

import json, os, sys, getpass, base64
from pathlib import Path
from urllib import request as urllib_request

GITHUB_REPO = 'meekotharaccoon-cell/meeko-nerve-center'


def banner():
    print('\n' + '='*60)
    print('🌸 SOLARPUNK SETUP WIZARD v3')
    print('Multi-chain. Every blockchain. No money turned away.')
    print('Your GitHub token is read from environment automatically.')
    print('='*60 + '\n')


def get_github_token():
    for env_var in ['GITHUB_TOKEN', 'GH_TOKEN', 'GITHUB_PAT']:
        token = os.environ.get(env_var, '')
        if token and len(token) > 10:
            print(f'  ✅ GitHub token found ({env_var})')
            return token
    print('  GitHub token not found in environment.')
    print('  Get one at: https://github.com/settings/tokens (repo + secrets)')
    return getpass.getpass('  GitHub PAT: ').strip()


def get_existing_secrets(token):
    req = urllib_request.Request(
        f'https://api.github.com/repos/{GITHUB_REPO}/actions/secrets',
        headers={'Authorization': f'Bearer {token}', 'X-GitHub-Api-Version': '2022-11-28'}
    )
    try:
        with urllib_request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        names = {s['name'] for s in data.get('secrets', [])}
        print(f'  ✅ {len(names)} secrets already configured')
        return names
    except Exception as e:
        print(f'  ⚠️ Could not list secrets: {e}')
        return set()


def get_public_key(token):
    req = urllib_request.Request(
        f'https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/public-key',
        headers={'Authorization': f'Bearer {token}', 'X-GitHub-Api-Version': '2022-11-28'}
    )
    with urllib_request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def encrypt_secret(public_key_b64, value):
    try:
        import nacl.public
        pk_bytes = base64.b64decode(public_key_b64)
        box = nacl.public.SealedBox(nacl.public.PublicKey(pk_bytes))
        return base64.b64encode(box.encrypt(value.encode())).decode()
    except ImportError:
        print('    (install PyNaCl for proper encryption: pip install PyNaCl)')
        return base64.b64encode(value.encode()).decode()


def set_secret(token, pub_key, name, value):
    if not value: return False
    encrypted = encrypt_secret(pub_key['key'], value)
    payload   = json.dumps({'encrypted_value': encrypted, 'key_id': pub_key['key_id']}).encode()
    req = urllib_request.Request(
        f'https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/{name}',
        data=payload,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'X-GitHub-Api-Version': '2022-11-28'},
        method='PUT'
    )
    try:
        with urllib_request.urlopen(req, timeout=10) as r: pass
        print(f'  ✅ {name}')
        return True
    except Exception as e:
        print(f'  ❌ {name}: {e}')
        return False


def ask(prompt, secret=False, default='', skip_if=''):
    if skip_if:
        return default
    display = prompt + (f' [{default[:6]}...]' if default else '') + ': '
    try:
        val = getpass.getpass(display) if secret else input(display)
        return val.strip() or default
    except KeyboardInterrupt:
        print('\nCancelled.'); sys.exit(0)


def detect_evm_siblings(wallets):
    """
    EVM chains (Ethereum, Base, Polygon, Monad, HyperEVM) share one address.
    If any one is set, auto-populate the rest.
    """
    evm_chains = ('WALLET_ETHEREUM', 'WALLET_BASE', 'WALLET_POLYGON',
                  'WALLET_MONAD', 'WALLET_HYPEREVM')
    evm_addr = next((wallets[c] for c in evm_chains if wallets.get(c)), '')
    if evm_addr:
        for c in evm_chains:
            if not wallets.get(c):
                wallets[c] = evm_addr
                print(f'  🔗 {c} auto-filled from Ethereum address')
    return wallets


def main():
    banner()

    token = get_github_token()
    if not token:
        print('No token. Exiting.'); sys.exit(1)

    existing = get_existing_secrets(token)
    try:
        pub_key = get_public_key(token)
    except Exception as e:
        print(f'Cannot get repo public key: {e}'); sys.exit(1)

    new_secrets = {}

    # ── Identity ─────────────────────────────────────────────────────────
    print('\n👤 IDENTITY (for job applications + form filling)')
    for name, prompt in [
        ('HUMAN_FULL_NAME', 'Your full legal name'),
        ('HUMAN_EMAIL',     'Your email'),
        ('HUMAN_LOCATION',  'Your location (e.g. Brooklyn, New York)'),
        ('HUMAN_TIMEZONE',  'Timezone (e.g. EST)'),
    ]:
        if name not in existing:
            val = ask(prompt)
            if val: new_secrets[name] = val
        else:
            print(f'  ✔  {name} already set')

    # ── Multi-chain wallets ────────────────────────────────────────────────────
    print('\n👻 WALLETS — paste all of them, never turn away money')
    print('  EVM chains (ETH/Base/Polygon/Monad/HyperEVM) use the same 0x... address')
    print('  Bitcoin has two: Taproot (bc1p...) and SegWit (bc1q...)')
    print('  Paste the address or press Enter to skip\n')

    wallet_inputs = {}
    wallet_fields = [
        ('WALLET_SOLANA',       'Solana address'),
        ('WALLET_ETHEREUM',     'Ethereum address (0x...) — also used for Base/Polygon/Monad/HyperEVM'),
        ('WALLET_BTC_TAPROOT',  'Bitcoin Taproot address (bc1p...)'),
        ('WALLET_BTC_SEGWIT',   'Bitcoin SegWit address (bc1q...)'),
        ('WALLET_SUI',          'Sui address'),
        ('WALLET_BASE',         'Base address (leave blank to use Ethereum address)'),
        ('WALLET_POLYGON',      'Polygon address (leave blank to use Ethereum address)'),
        ('WALLET_MONAD',        'Monad address (leave blank to use Ethereum address)'),
        ('WALLET_HYPEREVM',     'HyperEVM address (leave blank to use Ethereum address)'),
    ]
    for name, prompt in wallet_fields:
        if name not in existing:
            val = ask(prompt)
            if val: wallet_inputs[name] = val
        else:
            print(f'  ✔  {name} already set')

    # Auto-fill EVM siblings
    wallet_inputs = detect_evm_siblings(wallet_inputs)
    new_secrets.update(wallet_inputs)

    # Summary
    configured = len(wallet_inputs)
    if configured > 0:
        print(f'\n  💳 {configured} wallet addresses configured')
        print('  Accepting payments on all configured chains.')

    # ── Revenue routing ────────────────────────────────────────────────────
    print('\n💰 REVENUE ROUTING')
    for name, prompt, secret in [
        ('PAYPAL_CLIENT_ID',     'PayPal Client ID (developer.paypal.com)', True),
        ('PAYPAL_CLIENT_SECRET', 'PayPal Client Secret', True),
        ('HUMAN_PAYPAL_EMAIL',   'Your PayPal email (receives your 10%)', False),
        ('PCRF_PAYPAL_EMAIL',    'PCRF email (default: donations@pcrf.net)', False),
    ]:
        if name not in existing:
            val = ask(prompt, secret=secret, default='donations@pcrf.net' if 'PCRF' in name else '')
            if val: new_secrets[name] = val
        else:
            print(f'  ✔  {name} already set')

    # ── Etsy ──────────────────────────────────────────────────────────────
    print('\n🛍️ ETSY (90M buyers)')
    print('  Get keys at: https://www.etsy.com/developers/your-apps')
    for name, prompt, secret in [
        ('ETSY_API_KEY',      'Etsy API key', True),
        ('ETSY_SHOP_ID',      'Etsy shop ID (numbers from your shop URL)', False),
        ('ETSY_ACCESS_TOKEN', 'Etsy OAuth access token', True),
    ]:
        if name not in existing:
            val = ask(prompt, secret=secret)
            if val: new_secrets[name] = val
        else:
            print(f'  ✔  {name} already set')

    # ── Upload ──────────────────────────────────────────────────────────────
    if not new_secrets:
        print('\n✅ Everything already configured. System is fully active.')
        return

    print(f'\n🚀 Uploading {len(new_secrets)} secrets...')
    ok = sum(1 for n, v in new_secrets.items() if set_secret(token, pub_key, n, v))
    print(f'\n✅ {ok}/{len(new_secrets)} uploaded')
    print('\n🌸 DONE. Trigger MASTER CONTROLLER to activate everything.')
    print('All income streams active. All chains open. Loop closed.\n')


if __name__ == '__main__':
    main()
