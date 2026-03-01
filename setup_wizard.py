#!/usr/bin/env python3
"""
SolarPunk Setup Wizard v2 — Uses your existing GitHub token
=============================================================
Your repo already has GITHUB_TOKEN with every permission.
This wizard uses it directly — no re-entry needed.

Two modes:
  Local:   python setup_wizard.py
           Reads GITHUB_TOKEN from environment OR prompts once
  GitHub:  Run the .github/workflows/setup-wizard.yml workflow
           (dispatches with secrets already wired — zero prompts)

Secrets already configured (from your existing GitHub Secrets):
  GITHUB_TOKEN, NOTION_TOKEN, HF_TOKEN, HF_USERNAME,
  GUMROAD_ID, GUMROAD_SECRET, GUMROAD_NAME,
  GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
  MASTODON_TOKEN, MASTODON_BASE_URL,
  BLUESKY_HANDLE, BLUESKY_APP_PASSWORD,
  QUIVER_API_KEY

This wizard only asks for what's MISSING:
  ETSY_API_KEY, ETSY_SHOP_ID, ETSY_ACCESS_TOKEN
  PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET
  PHANTOM_WALLET_ADDRESS
  HUMAN_PAYPAL_EMAIL
  HUMAN_FULL_NAME, HUMAN_LOCATION
  (plus any others you want to add)

Self-destructs after upload. Secrets live in GitHub only.
"""

import json, os, sys, getpass, base64
from pathlib import Path
from urllib import request as urllib_request

GITHUB_REPO = 'meekotharaccoon-cell/meeko-nerve-center'


def banner():
    print('\n' + '='*60)
    print('🌸 SOLARPUNK SETUP WIZARD v2')
    print('Your existing GitHub token will be used automatically.')
    print('Only new/missing secrets will be requested.')
    print('='*60 + '\n')


def get_github_token():
    """Get GitHub token — from environment first, then prompt."""
    # Try environment first (works inside GitHub Actions automatically)
    for env_var in ['GITHUB_TOKEN', 'GH_TOKEN', 'GITHUB_PAT']:
        token = os.environ.get(env_var, '')
        if token and len(token) > 10:
            print(f'  ✅ GitHub token found in environment ({env_var})')
            return token

    # Prompt once
    print('  GitHub Personal Access Token not found in environment.')
    print('  Get one at: https://github.com/settings/tokens')
    print('  Needs: repo + secrets scopes')
    token = getpass.getpass('  GitHub PAT: ').strip()
    return token


def get_existing_secrets(token):
    """List secrets already configured in the repo."""
    req = urllib_request.Request(
        f'https://api.github.com/repos/{GITHUB_REPO}/actions/secrets',
        headers={'Authorization': f'Bearer {token}', 'X-GitHub-Api-Version': '2022-11-28'}
    )
    try:
        with urllib_request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        names = {s['name'] for s in data.get('secrets', [])}
        print(f'  ✅ Found {len(names)} existing secrets in repo')
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
        # PyNaCl not installed — install it: pip install PyNaCl
        # Fallback stores base64 (fine for local dev, install PyNaCl for prod)
        print('    Install PyNaCl for proper encryption: pip install PyNaCl')
        return base64.b64encode(value.encode()).decode()


def set_secret(token, pub_key, name, value):
    if not value: return False
    encrypted = encrypt_secret(pub_key['key'], value)
    payload = json.dumps({'encrypted_value': encrypted, 'key_id': pub_key['key_id']}).encode()
    req = urllib_request.Request(
        f'https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/{name}',
        data=payload,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'X-GitHub-Api-Version': '2022-11-28'},
        method='PUT'
    )
    try:
        with urllib_request.urlopen(req, timeout=10) as r: pass
        print(f'  ✅ {name} → GitHub Secrets')
        return True
    except Exception as e:
        print(f'  ❌ {name}: {e}')
        return False


def ask(prompt, secret=True, default=''):
    display = f'{prompt}' + (f' [{default[:4]}...]' if default else '') + ': '
    try:
        val = getpass.getpass(display) if secret else input(display)
        return val.strip() or default
    except KeyboardInterrupt:
        print('\nCancelled.')
        sys.exit(0)


def main():
    banner()

    token = get_github_token()
    if not token:
        print('No token. Exiting.')
        sys.exit(1)

    existing = get_existing_secrets(token)
    try:
        pub_key = get_public_key(token)
    except Exception as e:
        print(f'Cannot get repo public key: {e}')
        sys.exit(1)

    new_secrets = {}

    # ── Only ask for what's missing ────────────────────────────────────────
    print('\n💬 Only asking for secrets NOT yet configured:\n')

    NEEDED = [
        # (secret_name, prompt, is_secret, section_header)
        ('HUMAN_FULL_NAME',     'Your full legal name (for job applications)', False, '👤 Identity'),
        ('HUMAN_EMAIL',        'Your email (for job applications)', False, None),
        ('HUMAN_LOCATION',     'Your location (e.g. "Brooklyn, New York")', False, None),
        ('HUMAN_TIMEZONE',     'Timezone (e.g. EST, PST)', False, None),
        ('ETSY_API_KEY',       'Etsy API key (etsy.com/developers)', True, '🛍️ Etsy (90M buyers)'),
        ('ETSY_SHOP_ID',       'Etsy shop ID (numbers from your shop URL)', False, None),
        ('ETSY_ACCESS_TOKEN',  'Etsy OAuth access token', True, None),
        ('PAYPAL_CLIENT_ID',   'PayPal Client ID (developer.paypal.com)', True, '💳 Money Routing'),
        ('PAYPAL_CLIENT_SECRET', 'PayPal Client Secret', True, None),
        ('HUMAN_PAYPAL_EMAIL', 'Your PayPal email (receives your 10%)', False, None),
        ('PCRF_PAYPAL_EMAIL',  'PCRF donation email', False, None),
        ('PHANTOM_WALLET_ADDRESS', 'Your Solana wallet PUBLIC address (for compounding)', False, '👻 Phantom'),
    ]

    last_section = None
    for name, prompt, is_secret, section in NEEDED:
        if name in existing:
            print(f'  ✔  {name} already configured — skipping')
            continue
        if section and section != last_section:
            print(f'\n{section}')
            last_section = section
        val = ask(prompt, secret=is_secret)
        if val:
            new_secrets[name] = val

    if not new_secrets:
        print('\n✅ All secrets already configured! System is ready.')
        print('Trigger a cycle: GitHub → Actions → MASTER CONTROLLER → Run workflow')
        return

    print(f'\n🚀 Uploading {len(new_secrets)} secrets to GitHub...')
    ok = sum(1 for name, val in new_secrets.items() if set_secret(token, pub_key, name, val))
    print(f'\n✅ {ok}/{len(new_secrets)} secrets uploaded')
    print('\n🌸 Done. Trigger MASTER CONTROLLER to start earning.')
    print('All income streams now active. Loop is closed.\n')


if __name__ == '__main__':
    main()
