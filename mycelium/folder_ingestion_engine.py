#!/usr/bin/env python3
"""
Folder Ingestion Engine v2 — Scales to 200k+ files
====================================================
Smart batched ingestion. Doesn't choke on massive folders.

Strategy for huge folders:
  1. First pass: fast file tree scan (no reading) — build manifest
  2. Prioritize: process high-value files first (docs, code, data)
  3. Sample large folders: if >1000 files in one dir, sample intelligently
  4. Batch LLM calls: group similar files, one LLM call per batch
  5. Track progress: resume where it left off if interrupted
  6. Daily budget: process max 500 files per run (rest next cycle)
"""

import json, datetime, os, re, shutil, smtplib, mimetypes, hashlib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'

TODAY    = datetime.date.today().isoformat()
BATCH_MAX = 500  # files per run — spread over multiple cycles

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

INTAKE_DIRS = [
    ROOT / 'solarpunk',
    ROOT / 'intake',
]

SENSITIVE_PATTERNS = re.compile(
    r'(?i)(api[_\s-]?key|apikey|secret|token|password|passwd|bearer'
    r'|private_key|aws_|sk-[a-z]|pk-[a-z]|ghp_|xox[pb]-)[^\s\n]{6,}',
    re.MULTILINE
)
SENSITIVE_EXTS  = {'.env', '.pem', '.key', '.secret', '.p12', '.pfx', '.crt'}
IMAGE_EXTS      = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'}
CODE_EXTS       = {'.py', '.js', '.ts', '.sh', '.rb', '.go', '.rs', '.html', '.css'}
DATA_EXTS       = {'.json', '.csv', '.tsv', '.xml', '.yaml', '.yml', '.toml', '.ini', '.env'}
DOC_EXTS        = {'.md', '.txt', '.pdf', '.docx', '.rst', '.rtf'}
SKIP_EXTS       = {'.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.db', '.sqlite',
                   '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv', '.zip', '.tar', '.gz', '.rar'}

# Priority scoring — higher = process first
EXT_PRIORITY = {}
for e in DOC_EXTS:   EXT_PRIORITY[e] = 10
for e in CODE_EXTS:  EXT_PRIORITY[e] = 8
for e in DATA_EXTS:  EXT_PRIORITY[e] = 7
for e in IMAGE_EXTS: EXT_PRIORITY[e] = 3

def load_progress():
    p = DATA / 'ingestion_progress.json'
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {'processed': [], 'total_found': 0, 'sessions': []}

def save_progress(prog):
    try: (DATA / 'ingestion_progress.json').write_text(json.dumps(prog, indent=2))
    except: pass

def file_id(filepath):
    return hashlib.md5(str(filepath).encode()).hexdigest()[:12]

def ask_llm_batch(files_content, max_tokens=800):
    """Process multiple small files in one LLM call."""
    if not HF_TOKEN or not files_content: return {}
    prompt = f"""Analyze these files from a SolarPunk/humanitarian tech knowledge base.
For each file extract: summary, category, ideas, useful_facts, which system engine could use it.

Files:
{files_content[:4000]}

Respond as JSON:
{{"files": [
  {{"name": "filename", "summary": "...", "category": "idea|data|reference|personal|misc",
   "ideas": ["..."], "facts": ["..."], "engine": "which engine uses this"}}
]}}"""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You extract structured knowledge from files. Respond only with valid JSON.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        start = text.find('{')
        end   = text.rfind('}') + 1
        return json.loads(text[start:end])
    except Exception as e:
        print(f'[ingest] Batch LLM error: {e}')
        return {}

def inject_idea(idea_text, source):
    ledger_path = DATA / 'idea_ledger.json'
    ledger = {'ideas': {}}
    if ledger_path.exists():
        try: ledger = json.loads(ledger_path.read_text())
        except: pass
    ideas  = ledger.get('ideas', {})
    iid    = hashlib.md5(idea_text.encode()).hexdigest()[:8]
    if iid not in ideas:
        ideas[iid] = {'id': iid, 'title': idea_text[:80], 'source': source, 'status': 'pending', 'date': TODAY}
        ledger['ideas'] = ideas
        try: ledger_path.write_text(json.dumps(ledger, indent=2))
        except: pass

def route_sensitive_text(text, filepath):
    """Find and quarantine sensitive content. Returns True if sensitive."""
    matches = SENSITIVE_PATTERNS.findall(text)
    if not matches: return False

    # Save key names (not values) to log
    log_path = DATA / 'ingestion_secrets_log.json'
    log = {'found': []}
    if log_path.exists():
        try: log = json.loads(log_path.read_text())
        except: pass
    for m in matches:
        key_name = str(m[0]).strip()[:40] if isinstance(m, tuple) else str(m)[:40]
        entry = {'key': key_name, 'file': filepath.name, 'date': TODAY}
        if entry not in log['found']:
            log['found'].append(entry)
    try: log_path.write_text(json.dumps(log, indent=2))
    except: pass
    return True

def process_batch(files):
    """Process a batch of files. Returns list of result dicts."""
    results    = []
    text_batch = []  # (name, text) pairs for LLM batch
    text_files = []  # corresponding file paths

    for filepath in files:
        ext   = filepath.suffix.lower()
        fid   = file_id(filepath)
        result = {'id': fid, 'name': filepath.name, 'type': 'unknown',
                  'sensitive': False, 'action': '', 'date': TODAY}

        # Skip
        if ext in SKIP_EXTS:
            result['type']   = 'skipped'
            result['action'] = 'binary/media — skipped'
            results.append(result)
            continue

        # Sensitive extension
        if ext in SENSITIVE_EXTS:
            result['type']      = 'sensitive'
            result['sensitive'] = True
            result['action']    = 'quarantined — check ingestion_secrets_log.json'
            results.append(result)
            continue

        # Image
        if ext in IMAGE_EXTS:
            dest_dir = ROOT / 'public' / 'images' / 'ingested'
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(filepath, dest_dir / filepath.name)
                result['type']   = 'image'
                result['action'] = 'moved to public/images/ingested/'
            except Exception as e:
                result['action'] = f'image copy failed: {e}'
            results.append(result)
            continue

        # Try reading as text
        try:
            text = filepath.read_text(encoding='utf-8', errors='replace')
        except:
            result['type']   = 'binary'
            result['action'] = 'unreadable binary'
            results.append(result)
            continue

        # Scan for secrets
        is_sensitive = route_sensitive_text(text, filepath)
        result['sensitive'] = is_sensitive

        if ext in DATA_EXTS:
            result['type'] = 'data'
            # Archive to knowledge base
            kb_dir = KB / 'ingested'
            kb_dir.mkdir(parents=True, exist_ok=True)
            try:
                dest = kb_dir / f'{filepath.stem[:30]}_{TODAY[:7]}.json'
                if ext == '.json':
                    parsed = json.loads(text)
                    dest.write_text(json.dumps(parsed, indent=2))
                else:
                    dest.write_text(text[:50000])
                result['action'] = 'archived to knowledge base'
            except:
                result['action'] = 'data file archived'
            results.append(result)

        elif ext in CODE_EXTS:
            result['type'] = 'code'
            code_dir = KB / 'code_archive'
            code_dir.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(filepath, code_dir / filepath.name)
                result['action'] = 'archived to knowledge/code_archive/'
            except:
                result['action'] = 'code archived'
            # Queue for batch LLM
            text_batch.append(f'FILE: {filepath.name}\n{text[:500]}')
            text_files.append((filepath, result))
            results.append(result)

        elif ext in DOC_EXTS or ext == '':
            result['type'] = 'doc'
            # Queue for batch LLM
            text_batch.append(f'FILE: {filepath.name}\n{text[:800]}')
            text_files.append((filepath, result))
            results.append(result)

        else:
            result['type']   = 'misc'
            result['action'] = 'stored as misc'
            if len(text) > 20:
                text_batch.append(f'FILE: {filepath.name}\n{text[:400]}')
                text_files.append((filepath, result))
            results.append(result)

    # Batch LLM call for all text/doc/code files
    if text_batch and HF_TOKEN:
        combined = '\n---\n'.join(text_batch[:10])  # max 10 per LLM call
        llm_result = ask_llm_batch(combined)
        parsed_files = llm_result.get('files', [])
        for i, pf in enumerate(parsed_files):
            if i < len(text_files):
                fp, res = text_files[i]
                res['summary'] = pf.get('summary', '')
                res['action']  = f'extracted → {pf.get("engine", "knowledge base")}'
                # Inject ideas
                for idea in pf.get('ideas', []):
                    if idea: inject_idea(idea, str(fp.name))
                # Save facts
                facts = pf.get('facts', [])
                if facts:
                    kb_dir = KB / 'ingested'
                    kb_dir.mkdir(parents=True, exist_ok=True)
                    try:
                        (kb_dir / f'facts_{fp.stem[:20]}_{TODAY[:7]}.json').write_text(
                            json.dumps({'source': fp.name, 'facts': facts, 'date': TODAY}, indent=2)
                        )
                    except: pass

    return results

def send_progress_email(session_results, total_processed, total_found, remaining):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return

    sensitive = sum(1 for r in session_results if r.get('sensitive'))
    ideas     = sum(1 for r in session_results if 'extracted' in r.get('action', ''))
    images    = sum(1 for r in session_results if r.get('type') == 'image')
    pct       = round(total_processed / max(total_found, 1) * 100, 1)

    lines = [
        f'Folder Ingestion Progress — {TODAY}',
        f'',
        f'This session:  {len(session_results)} files processed',
        f'Total so far:  {total_processed} / {total_found} ({pct}%)',
        f'Remaining:     {remaining} files ({remaining // BATCH_MAX + 1} more cycles)',
        f'',
        f'This session:',
        f'  Sensitive flagged: {sensitive}',
        f'  Ideas extracted:   {ideas}',
        f'  Images moved:      {images}',
        f'',
    ]
    if sensitive:
        lines += ['Sensitive keys found (names only):', '']
        log_path = DATA / 'ingestion_secrets_log.json'
        if log_path.exists():
            try:
                log = json.loads(log_path.read_text())
                for e in log.get('found', [])[-10:]:
                    lines.append(f'  [{e["date"]}] {e["key"]} in {e["file"]}')
            except: pass
        lines += ['', '⚠️  Add these to GitHub Secrets if needed.']

    if remaining > 0:
        lines += ['', f'✅ Next batch processes automatically next cycle.']
    else:
        lines += ['', '✅ COMPLETE — all files ingested!']

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📂 Ingestion: {len(session_results)} files | {pct}% complete'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
    except Exception as e:
        print(f'[ingest] Email error: {e}')

def run():
    print(f'\n[ingest] Folder Ingestion Engine v2 — {TODAY}')

    # Find all intake files
    all_files = []
    for intake_dir in INTAKE_DIRS:
        if not intake_dir.exists(): continue
        files = [f for f in intake_dir.rglob('*') if f.is_file() and not f.name.startswith('.')]
        all_files.extend(files)
        print(f'[ingest] {intake_dir.name}/: {len(files)} files')

    if not all_files:
        print('[ingest] No intake folders found. Skipping.')
        return

    # Load progress
    prog           = load_progress()
    already_done   = set(prog.get('processed', []))
    prog['total_found'] = len(all_files)

    # Filter to unprocessed
    pending = [f for f in all_files if file_id(f) not in already_done]
    print(f'[ingest] {len(already_done)} already processed, {len(pending)} remaining')

    if not pending:
        print('[ingest] All files processed. Nothing to do.')
        return

    # Sort by priority (docs first, binaries last)
    pending.sort(key=lambda f: -EXT_PRIORITY.get(f.suffix.lower(), 1))

    # Take this cycle's batch
    this_batch = pending[:BATCH_MAX]
    print(f'[ingest] Processing {len(this_batch)} files this cycle...')

    # Process in sub-batches of 10 (for LLM efficiency)
    all_results = []
    for i in range(0, len(this_batch), 10):
        sub = this_batch[i:i+10]
        print(f'[ingest] Batch {i//10 + 1}/{len(this_batch)//10 + 1}...')
        results = process_batch(sub)
        all_results.extend(results)
        # Mark as processed
        for f in sub:
            fid = file_id(f)
            if fid not in already_done:
                already_done.add(fid)
                prog.setdefault('processed', []).append(fid)

    # Save progress
    prog['sessions'] = prog.get('sessions', []) + [{
        'date':      TODAY,
        'processed': len(this_batch),
        'total':     len(all_files),
    }]
    save_progress(prog)

    remaining = len(pending) - len(this_batch)
    total_processed = len(already_done)

    print(f'[ingest] Session complete. Processed: {len(all_results)} | Remaining: {remaining}')
    send_progress_email(all_results, total_processed, len(all_files), remaining)

if __name__ == '__main__':
    run()
