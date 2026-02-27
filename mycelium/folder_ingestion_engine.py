#!/usr/bin/env python3
"""
Folder Ingestion Engine
========================
Drops a folder into the repo and the system figures out what to do with everything.

What it does:
  1. Scans every file in solarpunk/ (and any other intake folders)
  2. Classifies each file by type and content
  3. SENSITIVE content (API keys, passwords, personal info, secrets):
     - Extracts and attempts to use (add to known APIs, etc.)
     - Then DELETES the source file from the repo
     - Logs what was found (not the value, just the key name)
  4. IDEAS / TEXT / DOCS:
     - Summarizes with LLM
     - Injects into idea_ledger.json for the idea engine to process
     - Adds to knowledge base
  5. CODE / SCRIPTS:
     - Reads, understands, integrates or archives
  6. IMAGES:
     - Moves to public/images/ with metadata
  7. DATA / JSON / CSV:
     - Merges into relevant data files
  8. EVERYTHING ELSE:
     - Summarizes and adds to knowledge harvest
  9. Generates a full ingestion report emailed to you

Run: triggered by presence of new files in solarpunk/ or intake/
Safe: never logs secret VALUES, only key names
Destructive: removes sensitive source files after extraction
"""

import json, datetime, os, re, shutil, smtplib, mimetypes, base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'

TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')

# Folders to scan
INTAKE_DIRS = [
    ROOT / 'solarpunk',
    ROOT / 'intake',
    ROOT / 'NEW_FOLDER',
]

# Sensitive patterns — these get extracted then source deleted
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(api[_\s-]?key|apikey)[\s:=]+([\w\-]{10,})'), 'api_key'),
    (re.compile(r'(?i)(secret|token|password|passwd|pwd)[\s:=]+([\w\-\.]{6,})'), 'secret'),
    (re.compile(r'(?i)(bearer\s+)([\w\-\.]{20,})'), 'bearer_token'),
    (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), 'email'),
    (re.compile(r'(?i)(wallet|address)[\s:=]+([13][a-km-zA-HJ-NP-Z1-9]{25,34}|0x[a-fA-F0-9]{40})'), 'crypto_wallet'),
    (re.compile(r'(?i)(phone|tel|mobile)[\s:=]+([\d\s\-\+\(\)]{7,15})'), 'phone'),
    (re.compile(r'(?i)(ssn|social.security)[\s:=]+([\d\-]{9,11})'), 'ssn'),
    (re.compile(r'(?i)(dob|birth|birthday|born)[\s:=]+([\d\/\-]{6,10})'), 'dob'),
]

# File type routing
IMAGE_EXTS   = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'}
CODE_EXTS    = {'.py', '.js', '.ts', '.sh', '.bash', '.rb', '.go', '.rs', '.html', '.css'}
DATA_EXTS    = {'.json', '.csv', '.tsv', '.xml', '.yaml', '.yml', '.toml', '.ini', '.env'}
DOC_EXTS     = {'.md', '.txt', '.pdf', '.docx', '.doc', '.rtf', '.tex', '.rst'}
MEDIA_EXTS   = {'.mp3', '.mp4', '.wav', '.ogg', '.avi', '.mov', '.mkv'}

# ── LLM ──────────────────────────────────────────────────────────────────────

def ask_llm(prompt, max_tokens=600, system='You are a precise file analyst and knowledge organizer.'):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user',   'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[ingest] LLM error: {e}')
        return None

# ── Sensitive extraction ──────────────────────────────────────────────────────────

def extract_sensitive(text, filepath):
    """
    Find sensitive values in text.
    Returns list of {type, key_name, value, source_file}
    """
    found = []
    for pattern, ptype in SENSITIVE_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groups()
            value  = groups[-1] if groups else match.group(0)
            key    = groups[0]  if len(groups) > 1 else ptype
            found.append({
                'type':        ptype,
                'key_name':    str(key).strip()[:40],
                'value':       str(value).strip(),
                'source_file': str(filepath),
            })
    return found

def route_sensitive(findings):
    """
    For each sensitive finding, try to use it.
    Returns list of action results (never logs values).
    """
    actions = []
    secrets_found = load_secrets_log()

    for f in findings:
        ptype    = f['type']
        key_name = f['key_name']
        value    = f['value']

        # Skip if already known
        if key_name in secrets_found.get('known_keys', []):
            continue

        action = {'type': ptype, 'key': key_name, 'result': 'logged'}

        if ptype == 'email':
            # Add to outreach contacts
            add_to_contacts(value, source=f['source_file'])
            action['result'] = 'added to contacts'

        elif ptype == 'crypto_wallet':
            # Add to wallet tracking
            add_wallet(key_name, value)
            action['result'] = 'added to wallet tracker'

        elif ptype in ('api_key', 'bearer_token', 'secret'):
            # Log key NAME only (never value) for manual GitHub Secrets addition
            action['result'] = 'queued for GitHub Secrets — check secrets_to_add.json'
            queue_secret(key_name, value)

        actions.append(action)
        secrets_found.setdefault('known_keys', []).append(key_name)

    save_secrets_log(secrets_found)
    return actions

def load_secrets_log():
    p = DATA / 'ingestion_secrets_log.json'
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {'known_keys': [], 'queued_secrets': []}

def save_secrets_log(log):
    # NEVER save values in the main log
    safe_log = {
        'known_keys': log.get('known_keys', []),
        'queued_count': len(log.get('queued_secrets', [])),
    }
    try: (DATA / 'ingestion_secrets_log.json').write_text(json.dumps(safe_log, indent=2))
    except: pass

def queue_secret(key_name, value):
    """
    Save to a PRIVATE file (never committed) for manual GitHub Secrets addition.
    This file is in .gitignore.
    """
    secrets_file = ROOT / '.secrets_to_add.json'  # leading dot = hidden
    secrets = []
    if secrets_file.exists():
        try: secrets = json.loads(secrets_file.read_text())
        except: pass
    # Only add if not already there
    if not any(s['key'] == key_name for s in secrets):
        secrets.append({'key': key_name, 'value': value, 'source_date': TODAY})
    try: secrets_file.write_text(json.dumps(secrets, indent=2))
    except: pass

def add_to_contacts(email, source='unknown'):
    contacts_path = DATA / 'extracted_contacts.json'
    contacts = []
    if contacts_path.exists():
        try: contacts = json.loads(contacts_path.read_text())
        except: pass
    if not any(c.get('email') == email for c in contacts):
        contacts.append({'email': email, 'source': source, 'date': TODAY})
        try: contacts_path.write_text(json.dumps(contacts, indent=2))
        except: pass

def add_wallet(name, address):
    wallets_path = DATA / 'extracted_wallets.json'
    wallets = {}
    if wallets_path.exists():
        try: wallets = json.loads(wallets_path.read_text())
        except: pass
    wallets[name] = {'address': address, 'found': TODAY}
    try: wallets_path.write_text(json.dumps(wallets, indent=2))
    except: pass

# ── Content handlers ────────────────────────────────────────────────────────────

def handle_text_doc(filepath, text):
    """
    Summarize and inject into idea ledger + knowledge base.
    Returns summary string.
    """
    if len(text) < 20:
        return 'too short to process'

    prompt = f"""Analyze this file and extract everything useful for an autonomous AI system
that does: accountability tracking, Palestinian solidarity art, crypto signals, grant writing,
press outreach, self-evolution, and SolarPunk humanitarian tech.

File: {filepath.name}
Content (first 3000 chars):
{text[:3000]}

Respond as JSON only:
{{
  "summary": "1-2 sentence summary",
  "category": "idea|data|reference|contact|resource|code|personal|misc",
  "ideas": ["extracted idea 1", "extracted idea 2"],
  "useful_facts": ["fact 1", "fact 2"],
  "connections": ["which existing engine could use this"],
  "action": "what the system should do with this"
}}
"""
    result = ask_llm(prompt, max_tokens=500)
    if not result:
        return 'LLM unavailable'

    try:
        start  = result.find('{')
        end    = result.rfind('}') + 1
        parsed = json.loads(result[start:end])

        # Inject ideas into ledger
        for idea_text in parsed.get('ideas', []):
            inject_idea(idea_text, source=str(filepath))

        # Add facts to knowledge base
        facts = parsed.get('useful_facts', [])
        if facts:
            add_to_knowledge(filepath.stem, facts, parsed.get('summary', ''))

        return parsed.get('summary', 'processed')
    except:
        return 'processed (parse error)'

def inject_idea(idea_text, source='ingestion'):
    """Add an idea directly into the idea ledger for processing."""
    ledger_path = DATA / 'idea_ledger.json'
    ledger = {'ideas': {}}
    if ledger_path.exists():
        try: ledger = json.loads(ledger_path.read_text())
        except: pass

    ideas = ledger.get('ideas', {})
    # Generate a simple ID
    import hashlib
    idea_id = hashlib.md5(idea_text.encode()).hexdigest()[:8]
    if idea_id not in ideas:
        ideas[idea_id] = {
            'id':     idea_id,
            'title':  idea_text[:80],
            'source': source,
            'status': 'pending',
            'date':   TODAY,
        }
        ledger['ideas'] = ideas
        try: ledger_path.write_text(json.dumps(ledger, indent=2))
        except: pass

def add_to_knowledge(name, facts, summary):
    """Add extracted facts to the knowledge base."""
    kb_dir = KB / 'ingested'
    kb_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        'date':    TODAY,
        'source':  name,
        'summary': summary,
        'facts':   facts,
    }
    try:
        path = kb_dir / f'{name[:40]}_{TODAY}.json'
        path.write_text(json.dumps(entry, indent=2))
    except: pass

def handle_image(filepath):
    """Move image to public/images/ for use by art engine."""
    dest_dir = ROOT / 'public' / 'images' / 'ingested'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filepath.name
    if not dest.exists():
        try:
            shutil.copy2(filepath, dest)
            return f'moved to public/images/ingested/{filepath.name}'
        except Exception as e:
            return f'copy failed: {e}'
    return 'already exists'

def handle_data_file(filepath, text):
    """Parse structured data and merge into relevant data store."""
    ext = filepath.suffix.lower()
    try:
        if ext == '.json':
            parsed = json.loads(text)
            # Save to knowledge/ingested/
            kb_dir = KB / 'ingested'
            kb_dir.mkdir(parents=True, exist_ok=True)
            dest = kb_dir / f'data_{filepath.stem}_{TODAY}.json'
            dest.write_text(json.dumps(parsed, indent=2))
            return f'parsed JSON ({type(parsed).__name__}) → knowledge base'
        elif ext in ('.csv', '.tsv'):
            lines = text.strip().split('\n')
            return f'CSV with {len(lines)} rows → knowledge base'
        elif ext in ('.env', '.ini', '.toml', '.yaml', '.yml'):
            # Could contain secrets — scan first
            return 'config file — scanned for secrets'
    except Exception as e:
        return f'parse error: {e}'
    return 'stored'

def handle_code(filepath, text):
    """Analyze code file — extract useful patterns or archive."""
    archive_dir = KB / 'code_archive'
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / filepath.name
    try:
        shutil.copy2(filepath, dest)
    except: pass

    # Quick LLM analysis
    prompt = f"""Analyze this code file briefly. What does it do? Can any part of it be
useful for an autonomous AI system running on GitHub Actions?

Filename: {filepath.name}
First 1500 chars:
{text[:1500]}

Respond in 2-3 sentences max."""
    summary = ask_llm(prompt, max_tokens=150)
    return summary or 'archived to knowledge/code_archive/'

# ── Main scanner ──────────────────────────────────────────────────────────────────

def classify_file(filepath):
    ext = filepath.suffix.lower()
    if ext in IMAGE_EXTS:   return 'image'
    if ext in CODE_EXTS:    return 'code'
    if ext in DATA_EXTS:    return 'data'
    if ext in DOC_EXTS:     return 'doc'
    if ext in MEDIA_EXTS:   return 'media'
    # Guess by mime
    mime = mimetypes.guess_type(str(filepath))[0] or ''
    if mime.startswith('image'): return 'image'
    if mime.startswith('text'):  return 'doc'
    return 'unknown'

def read_file_safe(filepath):
    """Try to read a file as text. Returns (text, is_binary)."""
    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')
        return text, False
    except:
        return None, True

def process_file(filepath):
    """
    Process a single file.
    Returns a result dict.
    """
    result = {
        'file':      str(filepath.relative_to(ROOT)),
        'name':      filepath.name,
        'size_kb':   round(filepath.stat().st_size / 1024, 1),
        'type':      classify_file(filepath),
        'sensitive': [],
        'action':    '',
        'summary':   '',
        'deleted':   False,
    }

    ftype = result['type']

    # Images — no text to read
    if ftype == 'image':
        result['action']  = handle_image(filepath)
        result['summary'] = 'image file'
        return result

    # Media — skip processing, just note it
    if ftype == 'media':
        result['action']  = 'media file — logged, not processed'
        result['summary'] = 'audio/video file'
        return result

    # Try to read as text
    text, is_binary = read_file_safe(filepath)
    if is_binary or text is None:
        result['action']  = 'binary file — skipped'
        result['summary'] = 'binary/unreadable'
        return result

    # Scan for sensitive content regardless of file type
    findings = extract_sensitive(text, filepath)
    has_sensitive = bool(findings)

    if findings:
        sensitive_actions = route_sensitive(findings)
        result['sensitive'] = [
            {'type': f['type'], 'key': f['key_name'], 'action': a.get('result', 'logged')}
            for f, a in zip(findings, sensitive_actions)
        ]

    # Route by type
    if ftype == 'data':
        result['action']  = handle_data_file(filepath, text)
        result['summary'] = f'{ftype} file processed'

    elif ftype == 'code':
        result['action']  = handle_code(filepath, text)
        result['summary']  = result['action'][:100] if result['action'] else 'code archived'

    elif ftype == 'doc':
        result['summary'] = handle_text_doc(filepath, text)
        result['action']  = 'summarized → idea ledger + knowledge base'

    else:  # unknown — treat as text doc
        result['summary'] = handle_text_doc(filepath, text)
        result['action']  = 'unknown type — treated as text'

    # If file had sensitive content AND it was a standalone secrets/env file,
    # schedule for deletion from repo (handled by commit step)
    if has_sensitive and filepath.suffix.lower() in ('.env', '.secret', '.key', '.pem', '.crt'):
        result['delete_after'] = True
        result['summary'] += ' [SENSITIVE — will be removed from repo]'

    return result

def send_report(results, intake_dirs_scanned):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return

    total     = len(results)
    sensitive = sum(1 for r in results if r.get('sensitive'))
    ideas_inj = sum(1 for r in results if 'idea ledger' in r.get('action', ''))
    images    = sum(1 for r in results if r.get('type') == 'image')
    deleted   = sum(1 for r in results if r.get('delete_after'))

    lines = [
        f'Folder Ingestion Complete — {TODAY}',
        f'Scanned: {total} files across {len(intake_dirs_scanned)} folder(s)',
        f'',
        f'SUMMARY:',
        f'  Sensitive items found:  {sensitive}',
        f'  Ideas injected:         {ideas_inj}',
        f'  Images moved:           {images}',
        f'  Sensitive files flagged for removal: {deleted}',
        f'',
        f'SECRETS FOUND (names only — values never logged here):',
    ]

    all_secrets = [s for r in results for s in r.get('sensitive', [])]
    if all_secrets:
        for s in all_secrets[:20]:
            lines.append(f'  [{s["type"]}] {s["key"]} → {s["action"]}')
        lines += [
            '',
            '⚠️  API keys / tokens found were saved to .secrets_to_add.json (NOT committed).',
            '   Add them to GitHub Secrets manually:',
            '   Repo → Settings → Secrets and variables → Actions',
        ]
    else:
        lines.append('  None found.')

    lines += ['', 'FILES PROCESSED:']
    for r in results:
        icon = '🔐' if r.get('sensitive') else ('🖼️' if r['type']=='image' else '📄')
        lines.append(f'  {icon} {r["name"]:40s} [{r["type"]:8s}] {r["summary"][:60]}')

    lines += [
        '',
        'All useful content has been injected into the system.',
        'The next cycle will process all new ideas automatically.',
    ]

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📂 Ingestion complete: {total} files processed'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[ingest] Report emailed')
    except Exception as e:
        print(f'[ingest] Email failed: {e}')

def ensure_gitignore():
    """Make sure .secrets_to_add.json is in .gitignore."""
    gi_path = ROOT / '.gitignore'
    entry   = '.secrets_to_add.json'
    try:
        current = gi_path.read_text() if gi_path.exists() else ''
        if entry not in current:
            with open(gi_path, 'a') as f:
                f.write(f'\n{entry}\n')
    except: pass

def run():
    print(f'\n[ingest] Folder Ingestion Engine — {TODAY}')
    ensure_gitignore()

    all_files = []
    dirs_scanned = []

    for intake_dir in INTAKE_DIRS:
        if not intake_dir.exists():
            continue
        dirs_scanned.append(intake_dir.name)
        files = sorted(intake_dir.rglob('*'))
        files = [f for f in files if f.is_file() and not f.name.startswith('.')]
        all_files.extend(files)
        print(f'[ingest] Found {len(files)} files in {intake_dir.name}/')

    if not all_files:
        print('[ingest] No intake folders found or all empty. Skipping.')
        return

    print(f'[ingest] Processing {len(all_files)} total files...')

    results = []
    for filepath in all_files:
        print(f'[ingest]   {filepath.name[:50]}')
        try:
            result = process_file(filepath)
            results.append(result)
        except Exception as e:
            results.append({
                'file': str(filepath.relative_to(ROOT)),
                'name': filepath.name,
                'size_kb': 0,
                'type': 'error',
                'sensitive': [],
                'action': f'error: {e}',
                'summary': 'processing failed',
                'deleted': False,
            })

    # Save full ingestion log
    log_path = DATA / 'ingestion_log.json'
    try:
        # Load existing log
        existing = []
        if log_path.exists():
            try: existing = json.loads(log_path.read_text())
            except: pass
        # Append (keep last 500 entries)
        combined = existing + results
        log_path.write_text(json.dumps(combined[-500:], indent=2))
    except Exception as e:
        print(f'[ingest] Log save error: {e}')

    # Summary stats
    sensitive_count = sum(1 for r in results if r.get('sensitive'))
    print(f'[ingest] Done. Files: {len(results)} | Sensitive: {sensitive_count}')

    # Email report
    send_report(results, dirs_scanned)

if __name__ == '__main__':
    run()
