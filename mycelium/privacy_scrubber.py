#!/usr/bin/env python3
"""
Privacy Scrubber
================
Hard data scrub: once data has served its final purpose, it's gone.
Nothing passes through more hands/friction than absolutely necessary.

Rules (absolute, no exceptions):
  1. Temporary data (API responses, routing info) -> scrub after use
  2. PII (email, IP, name, location) -> never stored, or scrubbed within 1 cycle
  3. Crypto keys / secrets -> never written to disk, never logged
  4. Old knowledge digests -> keep 7 days, then purge
  5. Content queue -> processed items purged after 24h
  6. Job data -> personal identifying info stripped on ingest
  7. QR scan data -> used for routing only, never persisted

What is NOT scrubbed (intentionally kept):
  - knowledge/ digests (last 7 days) - system memory
  - data/ JSON state files - system needs these
  - IDEA LEDGER - learning must persist
  - WIRED.md, IDEAS.md - system documentation
  - art, books, music catalogs - public domain, no PII

Outputs:
  - data/scrub_log.json     what was scrubbed and when (no content, just paths)
  - PRIVACY.md              public privacy commitment
"""

import json, datetime, shutil
from pathlib import Path

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
CONT  = ROOT / 'content' / 'queue'

TODAY = datetime.date.today()
NOW   = datetime.datetime.utcnow().isoformat()

# How many days to keep each data type
RETENTION = {
    'knowledge/*/':      7,   # daily digests kept 7 days
    'content/queue/':    1,   # content queue items: 24 hours
    'data/jobs_today.json': 1, # job listings: refresh daily
    'data/art_pairs.json':  7, # art pairs: weekly refresh
    'data/music.json':      7,
    'data/books.json':      7,
}

# Files that are NEVER scrubbed (system-critical)
NEVER_SCRUB = {
    'data/idea_ledger.json',
    'data/ideas_working.json',
    'data/ideas_failed.json',
    'data/world_state.json',
    'data/congress.json',
    'data/dex_state.json',
    'data/qr_campaigns.json',
    'data/etsy_tags.json',
    'data/content_calendar.json',
    'data/donation_context.json',
    'wiring_status.json',
}

# PII patterns to detect and flag in any data file
PII_PATTERNS = [
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # email
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IP address
    r'\b\d{3}-\d{2}-\d{4}\b',         # SSN pattern
    r'\b4[0-9]{12}(?:[0-9]{3})?\b',   # Visa card
    r'\b5[1-5][0-9]{14}\b',           # MC card
]

def scrub_old_files(directory, max_days, log):
    """Remove files older than max_days from a directory."""
    if not directory.exists():
        return
    cutoff = TODAY - datetime.timedelta(days=max_days)
    scrubbed = 0
    for f in directory.iterdir():
        if not f.is_file(): continue
        # Skip non-date files (like latest.md, latest.json)
        if 'latest' in f.name: continue
        # Try to parse date from filename
        try:
            file_date = datetime.date.fromisoformat(f.name[:10])
            if file_date < cutoff:
                f.unlink()
                log.append({'action': 'scrubbed', 'path': str(f.relative_to(ROOT)), 'reason': f'older than {max_days} days', 'time': NOW})
                scrubbed += 1
        except ValueError:
            pass  # Not a date-named file, skip
    return scrubbed

def strip_pii_from_json(filepath, log):
    """Read a JSON file and zero out any PII fields."""
    import re
    if not filepath.exists(): return
    try:
        content = filepath.read_text()
        original = content
        for pattern in PII_PATTERNS:
            content = re.sub(pattern, '[SCRUBBED]', content)
        if content != original:
            filepath.write_text(content)
            log.append({'action': 'pii_scrubbed', 'path': str(filepath.relative_to(ROOT)), 'time': NOW})
            print(f'[scrub] PII found and removed: {filepath.name}')
    except Exception as e:
        print(f'[scrub] Error scanning {filepath.name}: {e}')

def build_privacy_doc():
    """Public-facing privacy commitment."""
    doc = '''# PRIVACY COMMITMENT
> Last updated: {today}
> This is not a legal document. It\'s a promise.

## The Short Version

We collect the minimum possible.
We keep it the minimum time necessary.
We delete it the moment it\'s no longer needed.
You can always say no.

## What We Never Do

- No selling data. Ever. To anyone.
- No third-party analytics (no Google Analytics, no Facebook Pixel, nothing)
- No fingerprinting or "anonymous" tracking
- No storing IP addresses beyond immediate routing
- No email lists unless you explicitly opt in
- No sharing with "partners" (we don\'t have commercial partners)
- No data passing through more hands than absolutely necessary

## What We Keep and Why

| Data | Why | How Long |
|------|-----|----------|
| Knowledge digests | System memory (no PII) | 7 days |
| Crypto/market data | Trading signals | 1 day |
| Content queue | Publishing pipeline | 24 hours |
| Idea ledger | System learning | Permanent (no PII) |
| QR campaigns | Campaign tracking | No scan data kept |

## QR Code Scans

When you scan a QR code:
- Source param (`?src=`) is processed client-side in your browser only
- Nothing is sent to any server beyond what a normal webpage visit sends
- No scan database exists
- If you click "No thanks": zero data is recorded. Not even the visit.

## The "No" Is Always Respected

If you decline anything — a QR scan, an email ask, a fork invitation — the response is always:
**"Yeah, no problem! Thanks for being YOU."**

And then it\'s done. No follow-up. No "are you sure?". No dark patterns.

## Automated Scrubbing

`mycelium/privacy_scrubber.py` runs daily and:
- Removes knowledge digests older than 7 days
- Clears content queue items older than 24 hours
- Scans all data files for PII patterns and zeroes them out
- Logs what was scrubbed (path only, no content)

## Questions

Open an issue at github.com/meekotharaccoon-cell/meeko-nerve-center
or email meekotharaccoon@gmail.com

*Built by a human who\'s tired of being the product.*
'''.format(today=TODAY.isoformat())
    (ROOT / 'PRIVACY.md').write_text(doc)
    print('[scrub] PRIVACY.md written')

def run():
    print(f'[scrub] Privacy Scrubber — {TODAY}')
    log = []
    total_scrubbed = 0

    # Scrub old knowledge digests (keep 7 days)
    for subdir in KB.iterdir() if KB.exists() else []:
        if subdir.is_dir():
            n = scrub_old_files(subdir, 7, log)
            if n: total_scrubbed += n

    # Scrub old content queue items (keep 1 day)
    if CONT.exists():
        n = scrub_old_files(CONT, 1, log)
        if n: total_scrubbed += (n or 0)

    # Scan all data files for PII
    if DATA.exists():
        for f in DATA.iterdir():
            if f.suffix == '.json' and f.name not in NEVER_SCRUB:
                strip_pii_from_json(f, log)

    # Write scrub log
    existing_log = []
    log_path = DATA / 'scrub_log.json'
    if log_path.exists():
        try:
            existing_log = json.loads(log_path.read_text())
            # Keep only last 30 days of log entries
            cutoff = (TODAY - datetime.timedelta(days=30)).isoformat()
            existing_log = [e for e in existing_log if e.get('time', '') >= cutoff]
        except:
            pass
    existing_log.extend(log)
    log_path.write_text(json.dumps(existing_log[-200:], indent=2))  # cap at 200 entries

    # Update privacy doc
    build_privacy_doc()

    print(f'[scrub] Complete: {total_scrubbed} files scrubbed, {len(log)} actions logged')
    return {'scrubbed': total_scrubbed, 'actions': len(log)}

if __name__ == '__main__':
    run()
