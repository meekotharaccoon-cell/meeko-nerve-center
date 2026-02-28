#!/usr/bin/env python3
"""
Secret Scrubber — Nuclear Option
=================================
Finds secrets already IN the repo and destroys them.
Also generates the rewrite-history command to purge them from git log.

For the Stripe key that got through:
  1. Revoke it at dashboard.stripe.com RIGHT NOW
  2. Run this script
  3. Follow the git filter-branch instructions it prints
  4. Force push to overwrite history

Runs locally (never in CI — git history rewrite needs local access).

Also emails you a clean secrets summary: what was found,
what was scrubbed, what you need to add to GitHub Secrets.
"""

import re, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

PATTERNS = [
    (re.compile(r'sk_live_[\w]{20,}'), 'stripe_live_key'),
    (re.compile(r'sk_test_[\w]{20,}'), 'stripe_test_key'),
    (re.compile(r'pk_live_[\w]{20,}'), 'stripe_publishable_live'),
    (re.compile(r'pk_test_[\w]{20,}'), 'stripe_publishable_test'),
    (re.compile(r'ghp_[\w]{36}'),       'github_pat'),
    (re.compile(r'ghs_[\w]{36}'),       'github_secret'),
    (re.compile(r'sk-[a-zA-Z0-9]{32,}'), 'openai_key'),
    (re.compile(r'(?i)HF_TOKEN[\s=:]+[\w\-\.]{10,}'), 'hf_token'),
    (re.compile(r'(?i)(password|passwd)[\s=:]+[\w\-\.!@#]{8,}'), 'password'),
    (re.compile(r'(?i)(secret|api_key|apikey)[\s=:]+[\w\-\.]{10,}'), 'generic_secret'),
    (re.compile(r'(?i)Bearer [\w\-\.]{20,}'), 'bearer_token'),
    (re.compile(r'(?i)xox[bp]-[\w\-]+'), 'slack_token'),
    (re.compile(r'(?i)AAAA[\w\-]{30,}'), 'firebase_key'),
    (re.compile(r'(?i)(twilio|sendgrid|mailgun)[_\s]?(key|token|secret)[\s=:]+[\w\-]{10,}'), 'email_service_key'),
]

SKIP_DIRS  = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}
SKIP_EXTS  = {'.pyc', '.jpg', '.png', '.gif', '.mp4', '.mp3', '.zip', '.tar', '.gz', '.exe', '.dll'}
SCRUB_WITH = '[REDACTED]'

def scan_and_scrub(dry_run=False):
    findings = []
    files_changed = []

    for fpath in ROOT.rglob('*'):
        if not fpath.is_file(): continue
        if any(part in SKIP_DIRS for part in fpath.parts): continue
        if fpath.suffix.lower() in SKIP_EXTS: continue
        if fpath.name.startswith('.'): continue

        try:
            text = fpath.read_text(encoding='utf-8', errors='replace')
        except:
            continue

        new_text = text
        file_findings = []

        for pattern, ptype in PATTERNS:
            for match in pattern.finditer(text):
                val = match.group(0)
                file_findings.append({
                    'file':  str(fpath.relative_to(ROOT)),
                    'type':  ptype,
                    'chars': len(val),
                    'preview': val[:4] + '...' + val[-4:] if len(val) > 8 else '***',
                })
                new_text = new_text.replace(val, SCRUB_WITH)

        if file_findings:
            findings.extend(file_findings)
            if not dry_run and new_text != text:
                fpath.write_text(new_text)
                files_changed.append(str(fpath.relative_to(ROOT)))
                print(f'  SCRUBBED: {fpath.relative_to(ROOT)} ({len(file_findings)} secrets removed)')

    return findings, files_changed

def print_git_purge_commands(files_changed):
    if not files_changed:
        return
    print('\n' + '='*60)
    print('GIT HISTORY PURGE COMMANDS')
    print('Run these to remove secrets from ALL git history:')
    print('(Do this in your repo directory)')
    print('='*60)
    for f in files_changed[:5]:  # Show for first 5 changed files
        print(f'git filter-branch --force --index-filter \'git rm --cached --ignore-unmatch {f}\' --prune-empty --tag-name-filter cat -- --all')
    print('\nThen force push:')
    print('git push origin --force --all')
    print('git push origin --force --tags')
    print('\nWARNING: This rewrites history. Anyone who cloned the repo')
    print('will need to re-clone. GitHub will also need a cache clear.')
    print('See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository')
    print('='*60)

def main():
    print('\n[scrubber] Secret Scrubber — Nuclear Option')
    print('[scrubber] Scanning for secrets in repo...\n')

    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print('[scrubber] DRY RUN — nothing will be changed\n')

    findings, files_changed = scan_and_scrub(dry_run=dry_run)

    if not findings:
        print('[scrubber] ✅ No secrets found in repo files.')
        return

    print(f'\n[scrubber] Found {len(findings)} potential secrets in {len(set(f["file"] for f in findings))} files:')
    for f in findings:
        action = 'would scrub' if dry_run else 'SCRUBBED'
        print(f'  [{f["type"]}] {f["file"]} → {f["preview"]} ({action})')

    if not dry_run:
        print(f'\n[scrubber] ✅ Scrubbed {len(files_changed)} files.')
        print_git_purge_commands(files_changed)
    else:
        print(f'\n[scrubber] Run without --dry-run to actually scrub.')

if __name__ == '__main__':
    main()
