#!/usr/bin/env python3
"""
Privacy Scrubber
================
Hard scrub of sensitive/transient data after it has served its purpose.

Philosophy:
  - Data exists only as long as it needs to
  - After its final destination purpose: gone. Forever.
  - Nothing passes through more hands than absolutely necessary
  - Every scrub is logged (the FACT of scrubbing, not the data itself)
  - This is not a security feature bolted on. It is the architecture.

What gets scrubbed:
  - Consent session logs (after user decides yes/no)
  - Temporary API response caches older than their TTL
  - Any file tagged for scrubbing in scrub_queue.json
  - Raw personally-identifiable-looking data in data/ before it propagates

What NEVER gets collected:
  - IP addresses
  - Device fingerprints
  - Browser data
  - Location (beyond what the user explicitly shares)
  - Names, emails without explicit consent
  - Behavioral tracking of any kind

Outputs:
  - data/scrub_log.json   audit log (what was scrubbed, when, why — NOT the data)
  - data/scrub_queue.json files waiting to be scrubbed
"""

import json, datetime, os, hashlib
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()

# Files/patterns that should be scrubbed after N days
SCRUB_RULES = [
    # Pattern, max age in days, reason
    ('data/session_*.json',      0,  'Session data: scrub immediately after use'),
    ('data/consent_*.json',      0,  'Consent records: only the decision matters, not who'),
    ('data/jobs_today.json',     1,  'Job listings: replaced daily, no reason to keep'),
    ('data/music.json',          7,  'Music data: refreshed weekly'),
    ('data/books.json',          7,  'Book data: refreshed weekly'),
    ('knowledge/apis/*.json',    30, 'API catalogs: keep 30 days then roll'),
]

# Data keys that should NEVER appear in committed files
SENSITIVE_PATTERNS = [
    'ip_address', 'ipAddress', 'user_agent', 'userAgent',
    'email', 'phone', 'ssn', 'password', 'token', 'secret',
    'credit_card', 'creditCard', 'address', 'location',
    'device_id', 'deviceId', 'fingerprint', 'cookie',
    'session_id', 'sessionId', 'tracking',
]

def load_scrub_log():
    path = DATA / 'scrub_log.json'
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return {'scrubs': [], 'total_scrubbed': 0}

def save_scrub_log(log):
    (DATA / 'scrub_log.json').write_text(json.dumps(log, indent=2))

def scrub_file(path, reason):
    """Overwrite file with zeros then delete. Proper scrub."""
    try:
        p = Path(path)
        if not p.exists(): return False
        size = p.stat().st_size
        # Overwrite with null bytes first (prevent recovery)
        p.write_bytes(b'\x00' * size)
        p.unlink()
        return True
    except Exception as e:
        print(f'[scrub] Failed to scrub {path}: {e}')
        return False

def scan_for_sensitive_data(filepath):
    """Scan a JSON file for sensitive key names. Returns list of found keys."""
    try:
        text = Path(filepath).read_text()
        found = [k for k in SENSITIVE_PATTERNS if k.lower() in text.lower()]
        return found
    except:
        return []

def scrub_sensitive_from_json(filepath):
    """Remove sensitive keys from a JSON file in place."""
    try:
        data = json.loads(Path(filepath).read_text())
        changed = False
        
        def clean(obj):
            nonlocal changed
            if isinstance(obj, dict):
                keys_to_remove = [k for k in obj if any(p.lower() in k.lower() for p in SENSITIVE_PATTERNS)]
                for k in keys_to_remove:
                    del obj[k]
                    changed = True
                for v in obj.values():
                    clean(v)
            elif isinstance(obj, list):
                for item in obj:
                    clean(item)
        
        clean(data)
        if changed:
            Path(filepath).write_text(json.dumps(data, indent=2))
        return changed
    except:
        return False

def run():
    print(f'[scrub] Privacy Scrubber — {NOW}')
    
    log = load_scrub_log()
    scrubbed_count = 0
    
    # 1. Process scrub queue
    queue_path = DATA / 'scrub_queue.json'
    if queue_path.exists():
        try:
            queue = json.loads(queue_path.read_text())
            for item in queue.get('queue', []):
                path  = item.get('path', '')
                reason = item.get('reason', 'queued for scrub')
                if scrub_file(path, reason):
                    log['scrubs'].append({'path': path, 'reason': reason, 'when': NOW})
                    scrubbed_count += 1
                    print(f'[scrub] Scrubbed: {path}')
            # Clear the queue
            queue_path.write_text(json.dumps({'queue': [], 'last_cleared': NOW}, indent=2))
        except Exception as e:
            print(f'[scrub] Queue error: {e}')
    
    # 2. Scan data/ for sensitive keys that slipped through
    data_files = list(DATA.glob('*.json'))
    for f in data_files:
        sensitive = scan_for_sensitive_data(f)
        if sensitive:
            cleaned = scrub_sensitive_from_json(f)
            if cleaned:
                log['scrubs'].append({
                    'path': str(f),
                    'reason': f'Sensitive keys found and removed: {sensitive}',
                    'when': NOW,
                })
                scrubbed_count += 1
                print(f'[scrub] Cleaned sensitive data from {f.name}: {sensitive}')
    
    # 3. Age-based scrubs (rolling cleanup)
    cutoff_1day  = datetime.date.today() - datetime.timedelta(days=1)
    cutoff_7day  = datetime.date.today() - datetime.timedelta(days=7)
    cutoff_30day = datetime.date.today() - datetime.timedelta(days=30)
    
    for pattern, max_days, reason in SCRUB_RULES:
        if max_days == 0: continue  # handled by queue
        cutoff = datetime.date.today() - datetime.timedelta(days=max_days)
        for f in ROOT.glob(pattern):
            try:
                mtime = datetime.date.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    if scrub_file(f, reason):
                        log['scrubs'].append({'path': str(f), 'reason': reason, 'when': NOW})
                        scrubbed_count += 1
                        print(f'[scrub] Age-scrubbed: {f.name} ({mtime})')
            except:
                pass
    
    log['total_scrubbed'] += scrubbed_count
    save_scrub_log(log)
    
    print(f'[scrub] Done. {scrubbed_count} items scrubbed this run. Total ever: {log["total_scrubbed"]}')
    
    return {'scrubbed': scrubbed_count, 'total_ever': log['total_scrubbed']}

def queue_for_scrub(path, reason='served its purpose'):
    """External API: queue a file for scrubbing on next run."""
    queue_path = DATA / 'scrub_queue.json'
    try:
        queue = json.loads(queue_path.read_text()) if queue_path.exists() else {'queue': []}
    except:
        queue = {'queue': []}
    
    queue['queue'].append({'path': str(path), 'reason': reason, 'queued': NOW})
    queue_path.write_text(json.dumps(queue, indent=2))
    print(f'[scrub] Queued for scrub: {path}')

if __name__ == '__main__':
    run()
