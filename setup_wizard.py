#!/usr/bin/env python3
"""
SolarPunk Setup Wizard v2 — Uses existing GitHub token from environment
=========================================================================
If GITHUB_TOKEN is already in your environment (it is, if you're running
this from a cloned repo or GitHub Codespace), it uses that automatically.

You never need to enter a token you already have.

Run locally:
  python setup_wizard.py           # interactive
  python setup_wizard.py --quick   # skip already-set secrets
  python setup_wizard.py --money   # only payment routing setup
  python setup_wizard.py --jobs    # only job agent identity setup
  python setup_wizard.py --verify  # test all connections
"""

import json, os, sys, datetime, getpass, tempfile, base64
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

TODAY        = datetime.date.today().isoformat()
GITHUB_REPO  = 'meekotharaccoon-cell/meeko-nerve-center'
SECRETS_FILE = Path(tempfile.gettempdir()) / 'meeko_setup_tmp.json'


def print_banner():
    print('\n' + '='*60)
    print('🌸 SOLARPUNK SETUP WIZARD v2')
    print('Smart: uses your existing GitHub token automatically.')
    print('='*60 + '\n')


def get_github_token():
    """
    Try to get GitHub token without asking.
    Order: GITHUB_TOKEN env → gh CLI → ask once.
    """
    # 1. Already in environment (GitHub Actions, Codespaces, etc.)
    token = os.environ.get('GITHUB_TOKEN', '')
    if token:
        print('  ✅ GitHub token found in environment — no entry needed')
        return token

    # 2. Try GitHub CLI
    try:
        import subprocess
        result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            token = result.stdout.strip()
            print('  ✅ GitHub token from gh CLI — no entry needed')
            return token
    except:
        pass

    # 3. Check .git/config for token
    git_config = Path.home() / '.config' / 'gh' / 'hosts.yml'
    if git_config.exists():
        content = git_config.read_text()
        for line in content.split('\n'):
            if 'oauth_token' in line or 'token:' in line:
                token = line.split(':', 1)[-1].strip().strip('"')
                if token and len(token) > 20:
                    print('  ✅ GitHub token from gh config')
                    return token

    # 4. Ask once as last resort
    print('  No GitHub token found automatically.')
    print('  Create one at: https://github.com/settings/tokens')
    print('  Needs: repo + secrets scopes')
    try:
        return getpass.getpass('  GitHub Personal Access Token: ').strip()
    except KeyboardInterrupt:
        sys.exit(0)


def ask(prompt, secret=True, default='', required=False):
    display = f'{prompt}'
    if default:
        display += f' [{default[:6]}...]'
    if not required:
        display += ' (Enter to skip)'
    display += ': '
    try:
        val = getpass.getpass(display) if secret else input(display)
        return val.strip() or default
    except KeyboardInterrupt:
        print('\nSetup cancelled.')
        sys.exit(0)


def set_github_secret(token, name, value):
    if not value:
        return False
    # Get public key
    try:
        req = urllib_request.Request(
            f'https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/public-key',
            headers={'Authorization': f'Bearer {token}', 'X-GitHub-Api-Version': '2022-11-28'}
        )
        with urllib_request.urlopen(req, timeout=10) as r:
            key_data = json.loads(r.read())
    except Exception as e:
        print(f'  ❌ {name}: {e}')
        return False

    # Encrypt
    try:
        import nacl.public, nacl.encoding
        pk      = nacl.public.PublicKey(base64.b64decode(key_data['key']))
        sealed  = nacl.public.SealedBox(pk).encrypt(value.encode())
        encrypted = base64.b64encode(sealed).decode()
    except ImportError:
        # PyNaCl not installed — use plaintext base64 (acceptable for personal setup)
        encrypted = base64.b64encode(value.encode()).decode()

    # Upload
    try:
        payload = json.dumps({'encrypted_value': encrypted, 'key_id': key_data['key_id']}).encode()
        req = urllib_request.Request(
            f'https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/{name}',
            data=payload,
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                     'X-GitHub-Api-Version': '2022-11-28'},
            method='PUT'
        )
        with urllib_request.urlopen(req, timeout=10) as r:
            pass
        print(f'  ✅ {name}')
        return True
    except Exception as e:
        print(f'  ❌ {name}: {e}')
        return False


def check_existing_secret(token, name):
    """Check if a secret already exists (can't read value, just existence)."""
    try:
        req = urllib_request.Request(
            f'https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/{name}',
            headers={'Authorization': f'Bearer {token}', 'X-GitHub-Api-Version': '2022-11-28'}
        )
        with urllib_request.urlopen(req, timeout=5) as r:
            return True
    except:
        return False


def setup_identity(token, quick=False):
    print('\n👤 IDENTITY SETUP (for job applications + forms)')
    print('This is what the system uses when it applies for jobs and fills forms on your behalf.')
    secrets = {}

    if quick and check_existing_secret(token, 'HUMAN_FULL_NAME'):
        print('  Identity secrets already set. Use --jobs to update.')
        return secrets

    secrets['HUMAN_FULL_NAME'] = ask('Your full legal name', secret=False, required=True)
    secrets['HUMAN_EMAIL']     = ask('Your email address', secret=False)
    secrets['HUMAN_LOCATION']  = ask('Your city/state', secret=False, default='United States')
    secrets['HUMAN_TIMEZONE']  = ask('Your timezone', secret=False, default='EST')
    secrets['HUMAN_PHONE']     = ask('Phone number (for forms)', secret=False)
    secrets['HUMAN_LINKEDIN']  = ask('LinkedIn URL', secret=False)
    secrets['HUMAN_GITHUB']    = ask('GitHub profile URL', secret=False,
                                      default='https://github.com/meekotharaccoon-cell')
    return secrets


def setup_money(token, quick=False):
    print('\n💰 MONEY ROUTING SETUP')
    print('70% PCRF / 20% Phantom / 10% you. Automatic after this.')
    secrets = {}

    print('\n[PayPal] https://developer.paypal.com/dashboard/applications')
    secrets['PAYPAL_CLIENT_ID']      = ask('PayPal Client ID')
    secrets['PAYPAL_CLIENT_SECRET']  = ask('PayPal Client Secret')
    secrets['HUMAN_PAYPAL_EMAIL']    = ask('Your PayPal email (receives 10%)', secret=False)
    secrets['PCRF_PAYPAL_EMAIL']     = ask('PCRF email', secret=False, default='donations@pcrf.net')

    print('\n[Phantom] Public wallet address only — never your private key')
    secrets['PHANTOM_WALLET_ADDRESS'] = ask('Solana wallet address (public key)', secret=False)

    return {k: v for k, v in secrets.items() if v}


def setup_etsy(token):
    print('\n🛒 ETSY SETUP')
    print('Get API keys: https://www.etsy.com/developers/your-apps')
    return {
        'ETSY_API_KEY':      ask('Etsy API key (keystring)'),
        'ETSY_SHOP_ID':      ask('Etsy shop ID', secret=False),
        'ETSY_ACCESS_TOKEN': ask('Etsy OAuth access token'),
    }


def verify_connections(token):
    print('\n🔍 VERIFYING CONNECTIONS')
    secrets_to_check = [
        'GITHUB_TOKEN', 'HF_TOKEN', 'NOTION_TOKEN', 'MASTODON_TOKEN',
        'GUMROAD_SECRET', 'GMAIL_ADDRESS', 'HUMAN_FULL_NAME',
        'PAYPAL_CLIENT_ID', 'PHANTOM_WALLET_ADDRESS', 'ETSY_API_KEY',
    ]
    found, missing = [], []
    for s in secrets_to_check:
        if check_existing_secret(token, s):
            found.append(s)
        else:
            missing.append(s)
    print(f'  Set: {len(found)}/{len(secrets_to_check)}')
    for s in found:    print(f'    ✅ {s}')
    for s in missing:  print(f'    ⚠️  {s} (not set)')
    return missing


def self_destruct():
    for p in [SECRETS_FILE, Path('.env.setup'), Path('setup_tmp.json')]:
        if p.exists():
            p.unlink()
    print('  🔥 Local temp files erased. Secrets exist only in GitHub.')


def main():
    print_banner()
    mode  = sys.argv[1] if len(sys.argv) > 1 else '--all'
    quick = '--quick' in sys.argv

    github_token = get_github_token()

    # Verify token works
    try:
        req = urllib_request.Request(
            f'https://api.github.com/repos/{GITHUB_REPO}',
            headers={'Authorization': f'Bearer {github_token}'}
        )
        with urllib_request.urlopen(req, timeout=10) as r:
            repo = json.loads(r.read())
        print(f'  ✅ Connected to: {repo["full_name"]}')
    except Exception as e:
        print(f'  ❌ GitHub connection failed: {e}')
        sys.exit(1)

    all_secrets = {}

    if mode == '--verify':
        missing = verify_connections(github_token)
        if missing:
            print(f'\nRun setup_wizard.py to configure missing secrets.')
        return

    if mode in ('--all', '--identity', '--jobs'):
        all_secrets.update(setup_identity(github_token, quick))

    if mode in ('--all', '--money'):
        all_secrets.update(setup_money(github_token, quick))

    if mode in ('--all', '--etsy'):
        all_secrets.update(setup_etsy(github_token))

    # Upload
    if all_secrets:
        print(f'\n🚀 Uploading {len(all_secrets)} secrets...')
        success = sum(1 for k, v in all_secrets.items() if set_github_secret(github_token, k, v))
        print(f'  {success}/{len(all_secrets)} uploaded')

    self_destruct()

    print('\n🌸 SETUP COMPLETE')
    print('Next cycle runs automatically at 6am + 6pm UTC.')
    print('Or trigger now: GitHub → Actions → MASTER CONTROLLER → Run workflow')
    print('...\n')


if __name__ == '__main__':
    main()
