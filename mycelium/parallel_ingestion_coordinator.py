#!/usr/bin/env python3
"""
Parallel Ingestion Coordinator
================================
Splits the 192k file ingestion across 8 simultaneous agents.
77 days → ~10 days. With more workers, faster.

How it works:
  - Coordinator splits all files into N shards
  - Each shard gets a GitHub Actions job (matrix strategy)
  - All jobs run in parallel
  - Each writes results to data/ingestion_shard_{N}.json
  - Coordinator merges results after all shards complete
  - Triggers next wave automatically

Triggered by: .github/workflows/parallel-ingest.yml
Shard count: 8 (GitHub Actions free tier = 20 concurrent jobs)
"""

import json, datetime, os, hashlib, shutil
from pathlib import Path

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
KB     = ROOT / 'knowledge'
TODAY  = datetime.date.today().isoformat()

SHARD_COUNT  = 8
BATCH_PER_SHARD = 300  # files per shard per run = 2400 files/cycle
# At 5 cycles/day = 12,000 files/day = 192k done in ~16 days
# With 8 parallel workers each doing 300 = effectively 8x faster

SHARD_ID   = int(os.environ.get('SHARD_ID', '0'))
TOTAL_SHARDS = int(os.environ.get('TOTAL_SHARDS', str(SHARD_COUNT)))

HF_TOKEN = os.environ.get('HF_TOKEN', '')

INTAKE_DIRS = [ROOT / 'solarpunk', ROOT / 'intake']

SENSITIVE_EXTS  = {'.env', '.pem', '.key', '.secret', '.p12', '.pfx', '.crt', '.ps1'}
IMAGE_EXTS      = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
CODE_EXTS       = {'.py', '.js', '.ts', '.sh', '.rb', '.go', '.html', '.css'}
DATA_EXTS       = {'.json', '.csv', '.yaml', '.yml', '.toml', '.ini'}
DOC_EXTS        = {'.md', '.txt', '.rst', '.docx'}
SKIP_EXTS       = {'.exe', '.dll', '.so', '.bin', '.mp3', '.mp4', '.zip',
                   '.tar', '.gz', '.rar', '.db', '.sqlite', '.pyc'}

import re
SENSITIVE_RE = re.compile(
    r'(?i)(stripe[_\s]?(sk|pk|rk)_(?:live|test)_[\w]{20,}'
    r'|api[_\s-]?key[\s:=]+[\w\-]{16,}'
    r'|password[\s:=]+[\w\-\.]{8,}'
    r'|secret[\s:=]+[\w\-\.]{8,}'
    r'|token[\s:=]+[\w\-\.]{16,}'
    r'|ghp_[\w]{36}'
    r'|sk-[a-zA-Z0-9]{32,})',
    re.MULTILINE
)

def file_id(f):
    return hashlib.md5(str(f).encode()).hexdigest()[:12]

def load_global_progress():
    p = DATA / 'ingestion_progress.json'
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {'processed': [], 'total_found': 0}

def save_global_progress(prog):
    try: (DATA / 'ingestion_progress.json').write_text(json.dumps(prog, indent=2))
    except: pass

def get_all_pending_files():
    prog     = load_global_progress()
    done_ids = set(prog.get('processed', []))
    all_files = []
    for d in INTAKE_DIRS:
        if d.exists():
            all_files.extend(f for f in d.rglob('*') if f.is_file() and not f.name.startswith('.'))
    prog['total_found'] = len(all_files)
    save_global_progress(prog)
    return [f for f in all_files if file_id(f) not in done_ids], prog

def get_shard_files(pending, shard_id, total_shards, batch_size):
    """Deterministically assign files to this shard."""
    # Sort for determinism, then take every Nth file for this shard
    sorted_files = sorted(pending, key=lambda f: f.suffix.lower() + str(f))
    shard_files  = sorted_files[shard_id::total_shards]
    return shard_files[:batch_size]

def process_file_fast(filepath):
    """Lightweight processing — no LLM per file (batched later)."""
    ext  = filepath.suffix.lower()
    fid  = file_id(filepath)
    result = {'id': fid, 'name': filepath.name, 'ext': ext,
              'type': 'unknown', 'sensitive': False, 'date': TODAY}

    if ext in SKIP_EXTS:
        result['type'] = 'skip'
        return result

    if ext in SENSITIVE_EXTS:
        result['type']      = 'sensitive'
        result['sensitive'] = True
        return result

    if ext in IMAGE_EXTS:
        dest = ROOT / 'public' / 'images' / 'ingested'
        dest.mkdir(parents=True, exist_ok=True)
        try: shutil.copy2(filepath, dest / filepath.name)
        except: pass
        result['type'] = 'image'
        return result

    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')[:5000]
    except:
        result['type'] = 'binary'
        return result

    if SENSITIVE_RE.search(text):
        result['type']      = 'sensitive'
        result['sensitive'] = True
        # Log key name only
        log_sensitive(filepath.name, filepath.suffix)
        return result

    if ext in DATA_EXTS:  result['type'] = 'data'
    elif ext in CODE_EXTS: result['type'] = 'code'
    elif ext in DOC_EXTS:  result['type'] = 'doc'
    else:                  result['type'] = 'text'

    # Archive everything to knowledge base
    kb = KB / 'ingested' / ext.lstrip('.')
    kb.mkdir(parents=True, exist_ok=True)
    dest = kb / f'{filepath.stem[:30]}_{fid}.txt'
    if not dest.exists():
        try: dest.write_text(text)
        except: pass

    result['preview'] = text[:200]
    return result

def log_sensitive(filename, ext):
    p = DATA / 'ingestion_secrets_log.json'
    log = {'found': []}
    if p.exists():
        try: log = json.loads(p.read_text())
        except: pass
    log['found'].append({'file': filename, 'ext': ext, 'date': TODAY, 'action': 'flagged_not_ingested'})
    try: p.write_text(json.dumps(log, indent=2))
    except: pass

def batch_llm_summarize(doc_files):
    """One LLM call to summarize up to 15 docs and extract ideas."""
    if not HF_TOKEN or not doc_files: return
    snippets = '\n---\n'.join(
        f'FILE: {r["name"]}\n{r.get("preview","")}'
        for r in doc_files[:15]
    )
    prompt = f"""Extract ideas and facts from these files for an autonomous AI focused on
Palestinian solidarity, accountability, SolarPunk tech, and humanitarian innovation.

Files:
{snippets[:4000]}

Return JSON: {{"ideas": ["idea 1", ...], "facts": ["fact 1", ...]}}
Only include genuinely useful insights. Skip noise."""
    try:
        import urllib.request
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 600,
            'messages': [
                {'role': 'system', 'content': 'Extract structured knowledge. Respond only with valid JSON.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib.request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        s = text.find('{')
        e = text.rfind('}') + 1
        data = json.loads(text[s:e])

        # Inject ideas
        ledger_path = DATA / 'idea_ledger.json'
        ledger = {'ideas': {}}
        if ledger_path.exists():
            try: ledger = json.loads(ledger_path.read_text())
            except: pass
        for idea in data.get('ideas', []):
            iid = hashlib.md5(idea.encode()).hexdigest()[:8]
            if iid not in ledger.get('ideas', {}):
                ledger.setdefault('ideas', {})[iid] = {
                    'id': iid, 'title': idea[:80],
                    'source': 'parallel_ingestion', 'status': 'pending', 'date': TODAY
                }
        ledger_path.write_text(json.dumps(ledger, indent=2))

        # Save facts
        facts = data.get('facts', [])
        if facts:
            (KB / 'ingested').mkdir(parents=True, exist_ok=True)
            fact_path = KB / 'ingested' / f'facts_shard{SHARD_ID}_{TODAY}.json'
            fact_path.write_text(json.dumps({'date': TODAY, 'shard': SHARD_ID, 'facts': facts}, indent=2))
    except Exception as e:
        print(f'[ingest_shard{SHARD_ID}] LLM error: {e}')

def run():
    print(f'\n[ingest_shard{SHARD_ID}/{TOTAL_SHARDS}] Starting — {TODAY}')

    pending, prog = get_all_pending_files()
    total = len(pending)
    print(f'[ingest_shard{SHARD_ID}] {total} files pending across all shards')

    if not pending:
        print(f'[ingest_shard{SHARD_ID}] All done!')
        return

    my_files = get_shard_files(pending, SHARD_ID, TOTAL_SHARDS, BATCH_PER_SHARD)
    print(f'[ingest_shard{SHARD_ID}] My batch: {len(my_files)} files')

    results = []
    doc_results = []
    for f in my_files:
        try:
            r = process_file_fast(f)
            results.append(r)
            if r['type'] in ('doc', 'text', 'code'):
                doc_results.append(r)
        except Exception as e:
            results.append({'id': file_id(f), 'name': f.name, 'type': 'error', 'error': str(e)})

    # Batch LLM for docs
    if doc_results:
        print(f'[ingest_shard{SHARD_ID}] LLM summarizing {len(doc_results)} docs...')
        batch_llm_summarize(doc_results)

    # Mark processed
    done_ids = set(prog.get('processed', []))
    for r in results:
        done_ids.add(r['id'])
    prog['processed'] = list(done_ids)
    save_global_progress(prog)

    # Save shard results
    shard_path = DATA / f'ingestion_shard_{SHARD_ID}.json'
    shard_path.write_text(json.dumps(results, indent=2))

    sensitive = sum(1 for r in results if r.get('sensitive'))
    images    = sum(1 for r in results if r.get('type') == 'image')
    pct       = round(len(done_ids) / max(prog['total_found'], 1) * 100, 1)
    print(f'[ingest_shard{SHARD_ID}] Done: {len(results)} files | sensitive={sensitive} | images={images} | overall={pct}%')

if __name__ == '__main__':
    run()
