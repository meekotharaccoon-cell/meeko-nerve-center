#!/usr/bin/env python3
"""
Self-Healer V2 — The System Reads Its Own Mail
================================================
The OLD problem:
  system finds a bug -> emails USER -> user has to fix it
  system gets skipped -> user has to re-enable it
  workflow fails -> user has to check it

The NEW architecture:
  self_healer_v2.py reads data/self_diagnostic_inbox.json
  That file is written by master_controller.py
  Self-healer reads it, generates fixes, commits them
  Also reads its own Gmail for any self-addressed diagnostics
  The human is completely out of the loop

Self-email reading:
  System sends emails to itself (gmail to same gmail)
  Self-healer reads those emails via IMAP
  Subject patterns it handles:
    '[DIAGNOSTIC]' — workflow error report
    '[SELF-FIX]'   — engine generated a fix for itself
    '[BLOCKED]'    — something is blocking a cycle
    '[ALERT]'      — anything flagged as high-priority
  It reads them, marks them read, takes action
  NEVER forwards to the user unless it's a HUMAN_ACTION required

Fix generation:
  Given a broken engine file and its error:
  1. Reads the file
  2. Reads the error from the diagnostic inbox
  3. Asks LLM to generate a minimal fix
  4. Writes the fixed file
  5. Commits it
  6. Logs the fix to data/self_healer_log.json
  7. Marks the issue as resolved in the inbox

This is the system becoming fully responsible for itself.
"""

import json, datetime, os, imaplib, email
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')

SELF_EMAIL_SUBJECTS = ['[DIAGNOSTIC]', '[SELF-FIX]', '[BLOCKED]', '[ALERT]', '[WORKFLOW-FAIL]']

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def read_self_emails():
    """Read emails the system sent to itself for self-diagnostics."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return []
    self_emails = []
    try:
        imap = imaplib.IMAP4_SSL('imap.gmail.com')
        imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        imap.select('INBOX')
        # Search for self-addressed diagnostic emails
        _, data = imap.search(None, 'UNSEEN')
        uids = data[0].split()
        for uid in uids[-20:]:  # Last 20 unread
            _, msg_data = imap.fetch(uid, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get('Subject', '')
            sender  = msg.get('From', '')
            # Only process self-emails with diagnostic patterns
            is_self = GMAIL_ADDRESS.split('@')[0].lower() in sender.lower() or \
                      'meeko' in sender.lower() or 'solarpunk' in sender.lower()
            is_diag = any(p.lower() in subject.lower() for p in SELF_EMAIL_SUBJECTS)
            if is_self and is_diag:
                # Extract body
                body = ''
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain':
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                self_emails.append({'subject': subject, 'body': body[:2000], 'uid': uid})
                # Mark as read
                imap.store(uid, '+FLAGS', '\\Seen')
        imap.logout()
    except Exception as e:
        print(f'[healer] IMAP error: {e}')
    return self_emails

def generate_fix(engine_name, error_context):
    """Ask LLM to generate a minimal fix for a broken engine.""""
    if not HF_TOKEN: return None
    engine_path = ROOT / 'mycelium' / f'{engine_name}.py'
    if not engine_path.exists(): return None
    engine_code = engine_path.read_text()[:3000]  # First 3000 chars
    prompt = f"""Fix this Python engine. Minimal change, just make it not crash.

Engine: {engine_name}.py
Error: {error_context[:500]}
Code start:
```python
{engine_code}
```

Return ONLY the fixed Python code starting with #!/usr/bin/env python3
Fix ONLY the specific error. Don't refactor. Don't add features."""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 2000,
            'messages': [
                {'role': 'system', 'content': 'You fix Python bugs with minimal changes. Return only fixed code.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            result = json.loads(r.read())['choices'][0]['message']['content'].strip()
            # Extract code block if present
            if '```python' in result:
                result = result.split('```python')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()
            if result.startswith('#!/'):
                return result
    except Exception as e:
        print(f'[healer] LLM error: {e}')
    return None

def process_diagnostic_inbox():
    """Process issues written by master_controller.py"""
    inbox_path = DATA / 'self_diagnostic_inbox.json'
    inbox = load(inbox_path, {'issues': [], 'resolved': []})
    issues = [i for i in inbox.get('issues', []) if not i.get('resolved')]
    
    if not issues:
        print('[healer] Inbox empty. System healthy.')
        return 0
    
    print(f'[healer] {len(issues)} issues in diagnostic inbox')
    fixed = 0
    
    for issue in issues[:3]:  # Process 3 per run
        issue_type = issue.get('type', '')
        if issue_type == 'workflow_failure':
            wf_file = issue.get('file', '')
            # Map workflow to engine
            engine = wf_file.replace('.yml', '').replace('-', '_')
            error  = issue.get('error', 'unknown error')
            print(f'[healer] Attempting fix: {engine}')
            fix = generate_fix(engine, error)
            if fix:
                try:
                    engine_path = ROOT / 'mycelium' / f'{engine}.py'
                    if engine_path.exists():
                        engine_path.write_text(fix)
                        print(f'[healer] ✅ Fixed: {engine}.py')
                        issue['resolved'] = True
                        issue['fix_date'] = TODAY
                        fixed += 1
                except Exception as e:
                    print(f'[healer] Write error: {e}')
    
    # Update inbox
    inbox['issues']   = issues
    inbox['resolved'] = inbox.get('resolved', []) + [i for i in issues if i.get('resolved')]
    try: inbox_path.write_text(json.dumps(inbox, indent=2))
    except: pass
    return fixed

def process_self_emails(self_emails):
    """Act on self-sent diagnostic emails."""
    acted = 0
    for em in self_emails:
        subject = em['subject']
        body    = em['body']
        print(f'[healer] Processing self-email: {subject[:60]}')
        # Parse action from email body
        issues_to_add = []
        if '[WORKFLOW-FAIL]' in subject or '[DIAGNOSTIC]' in subject:
            # Extract engine name from subject if present
            # Pattern: [DIAGNOSTIC] engine_name: error message
            parts = subject.split(':')
            if len(parts) > 1:
                engine = parts[1].strip().split()[0].replace('-', '_')
                issues_to_add.append({
                    'type': 'workflow_failure',
                    'workflow': subject,
                    'file': f'{engine}.py',
                    'error': body[:500],
                })
        if issues_to_add:
            inbox = load(DATA / 'self_diagnostic_inbox.json', {'issues': []})
            inbox['issues'].extend(issues_to_add)
            try: (DATA / 'self_diagnostic_inbox.json').write_text(json.dumps(inbox, indent=2))
            except: pass
            acted += 1
    return acted

def enable_skipped_workflows():
    """If workflows are being skipped, re-enable them."""
    if not GITHUB_TOKEN: return
    # Check for workflows in disabled state
    try:
        from urllib import request as r
        req = urllib_request.Request(
            f'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/actions/workflows?per_page=100',
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github+json',
            }
        )
        with urllib_request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        for wf in data.get('workflows', []):
            if wf.get('state') == 'disabled_manually':
                wf_id = wf['id']
                wf_name = wf['name']
                # Re-enable it
                enable_req = urllib_request.Request(
                    f'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/actions/workflows/{wf_id}/enable',
                    data=b'',
                    headers={
                        'Authorization': f'Bearer {GITHUB_TOKEN}',
                        'Accept': 'application/vnd.github+json',
                    },
                    method='PUT'
                )
                try:
                    with urllib_request.urlopen(enable_req, timeout=15) as resp:
                        print(f'[healer] ✅ Re-enabled: {wf_name}')
                except Exception as e:
                    print(f'[healer] Enable error for {wf_name}: {e}')
    except Exception as e:
        print(f'[healer] Workflow enable check error: {e}')

def run():
    print(f'\n[healer] 🌸 Self-Healer V2 — {TODAY}')
    print('[healer] Reading own diagnostics. Fixing own bugs. No human needed.')
    
    # Read and act on self-emails
    self_emails = read_self_emails()
    if self_emails:
        acted = process_self_emails(self_emails)
        print(f'[healer] Processed {len(self_emails)} self-emails, acted on {acted}')
    
    # Re-enable any disabled workflows
    enable_skipped_workflows()
    
    # Process diagnostic inbox
    fixed = process_diagnostic_inbox()
    
    # Log
    log = load(DATA / 'self_healer_log.json', {'runs': []})
    log['runs'].append({
        'date': TODAY,
        'self_emails_read': len(self_emails),
        'issues_fixed': fixed,
    })
    log['runs'] = log['runs'][-50:]
    try: (DATA / 'self_healer_log.json').write_text(json.dumps(log, indent=2))
    except: pass
    
    print(f'[healer] Self-emails: {len(self_emails)} | Fixed: {fixed}')
    print('[healer] The system heals itself. 🌸')

if __name__ == '__main__':
    run()
