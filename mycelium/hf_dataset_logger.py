#!/usr/bin/env python3
"""
HuggingFace Dataset Logger — The system's training data flywheel
================================================================
Every output the system generates is potentially training data.
This engine collects ALL outputs, tags them with performance signals,
and uploads to a private HuggingFace dataset.

Over time this dataset becomes:
  1. The foundation for fine-tuning a model that sounds like Meeko
  2. A performance record the system can analyze
  3. A searchable memory of everything the system ever said or did
  4. Evidence for grant applications ("we generated X outputs")
  5. The raw material for the long_term_memory engine

What gets logged:
  - Every social post (with engagement if available)
  - Every Gumroad product description
  - Every grant application draft
  - Every email draft
  - Every art prompt and generated image URL
  - Every 3D brain decision
  - Every directive and how the system responded
  - Every idea the system considered (accepted or rejected)

Dataset format: JSONL, one record per output
Dataset name: meekotharaccoon/meeko-outputs (private)

Each record:
{
  "timestamp": "2026-03-01T11:00:00",
  "engine": "cross_poster",
  "type": "social_post",
  "platform": "mastodon",
  "content": "...",
  "metadata": {"topic": "grants", "tone": "informational"},
  "performance": {"likes": 0, "boosts": 0, "replies": 0},  // filled in later
  "directive_context": "...",  // what the human said that day
  "outcome": null  // filled in by performance tracker
}
"""

import json, os, datetime, glob
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import HTTPError

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

HF_TOKEN    = os.environ.get('HF_TOKEN', '')
HF_USERNAME = os.environ.get('HF_USERNAME', 'meekotharaccoon')
DATASET_NAME = 'meeko-outputs'
DATASET_ID   = f'{HF_USERNAME}/{DATASET_NAME}'

LOCAL_LOG = DATA / 'hf_dataset_log.jsonl'
QUEUE_LOG = DATA / 'hf_upload_queue.jsonl'  # buffered if upload fails


# ── HuggingFace API ───────────────────────────────────────────────────────────
def hf_req(method, path, body=None, raw_data=None):
    if not HF_TOKEN:
        return None
    url = f'https://huggingface.co/api/{path}'
    headers = {'Authorization': f'Bearer {HF_TOKEN}'}
    if body:
        raw_data = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib_request.Request(url, data=raw_data, method=method, headers=headers)
    try:
        with urllib_request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except HTTPError as e:
        print(f'[hf_dataset] HF {e.code}: {e.read().decode()[:200]}')
        return None
    except Exception as e:
        print(f'[hf_dataset] HF error: {e}')
        return None

def ensure_dataset_exists():
    """Create private dataset repo if it doesn't exist."""
    # Check
    check = hf_req('GET', f'datasets/{DATASET_ID}')
    if check and not check.get('error'):
        return True
    # Create
    result = hf_req('POST', 'repos/create', {
        'type': 'dataset',
        'name': DATASET_NAME,
        'private': True,
    })
    if result:
        print(f'[hf_dataset] Created dataset: {DATASET_ID}')
        return True
    print(f'[hf_dataset] Could not create dataset — will queue locally')
    return False

def upload_jsonl_to_hf(records):
    """Upload a batch of records to the HF dataset as a JSONL file."""
    if not HF_TOKEN or not records:
        return False
    filename = f'outputs/{TODAY}.jsonl'
    content = '\n'.join(json.dumps(r) for r in records)

    import base64
    encoded = base64.b64encode(content.encode()).decode()

    # Use HF Hub commit API
    result = hf_req('POST', f'datasets/{DATASET_ID}/commit/main', {
        'commit_message': f'auto: {len(records)} outputs logged {TODAY}',
        'operations': [{
            'operation': 'addOrUpdate',
            'path': filename,
            'content': encoded,
            'encoding': 'base64'
        }]
    })
    if result and not result.get('error'):
        print(f'[hf_dataset] Uploaded {len(records)} records to {DATASET_ID}/{filename}')
        return True
    return False


# ── Data collectors — harvest outputs from the system ─────────────────────────
def load_json(path, default=None):
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text())
    except:
        pass
    return default if default is not None else {}

def collect_social_posts():
    """Collect recent social posts from cross_engine output."""
    records = []
    for path in [
        DATA / 'cross_posts.json',
        DATA / 'social_posts.json',
        DATA / 'posted_today.json',
    ]:
        data = load_json(path, [])
        posts = data if isinstance(data, list) else data.get('posts', [])
        for post in posts[-20:]:  # last 20
            records.append({
                'timestamp': post.get('timestamp', NOW),
                'engine': 'cross_poster',
                'type': 'social_post',
                'platform': post.get('platform', 'unknown'),
                'content': post.get('text', post.get('content', str(post)))[:2000],
                'metadata': {
                    'topic': post.get('topic', ''),
                    'tone': post.get('tone', ''),
                    'tags': post.get('tags', []),
                },
                'performance': {
                    'likes': post.get('likes', 0),
                    'boosts': post.get('boosts', post.get('reposts', 0)),
                    'replies': post.get('replies', 0),
                },
                'source_file': str(path.name),
            })
    return records

def collect_grant_drafts():
    """Collect grant application drafts."""
    records = []
    grant_dir = DATA / 'grants'
    if not grant_dir.exists():
        return records
    for f in list(grant_dir.glob('*.json'))[-10:]:
        data = load_json(f)
        if not data:
            continue
        records.append({
            'timestamp': data.get('date', TODAY) + 'T00:00:00',
            'engine': 'grant_intelligence',
            'type': 'grant_draft',
            'platform': 'grants.gov',
            'content': data.get('draft', data.get('application', str(data)))[:3000],
            'metadata': {
                'grant_name': data.get('grant_name', data.get('name', '')),
                'amount': data.get('amount', ''),
                'deadline': data.get('deadline', ''),
            },
            'performance': {
                'submitted': data.get('submitted', False),
                'response': data.get('response', None),
            },
            'source_file': f.name,
        })
    return records

def collect_gumroad_products():
    """Collect Gumroad product descriptions."""
    records = []
    products_dir = ROOT / 'products'
    if not products_dir.exists():
        return records
    for f in sorted(products_dir.glob('[0-9]*.md')):
        content = f.read_text()[:3000]
        records.append({
            'timestamp': TODAY + 'T00:00:00',
            'engine': 'product_catalog',
            'type': 'product_description',
            'platform': 'gumroad',
            'content': content,
            'metadata': {
                'filename': f.name,
                'price': '$1.00',
                'pcrf_split': '70%',
            },
            'performance': {},
            'source_file': f.name,
        })
    return records

def collect_brain_decisions():
    """Collect 3D brain decisions."""
    brain = load_json(DATA / 'three_d_brain.json')
    if not brain:
        return []
    synthesis = brain.get('synthesis', {})
    return [{
        'timestamp': brain.get('timestamp', NOW),
        'engine': 'three_d_brain',
        'type': 'strategic_decision',
        'platform': 'internal',
        'content': json.dumps(synthesis.get('decisions', []))[:2000],
        'metadata': {
            'insights': synthesis.get('insights', []),
            'revenue_total': brain.get('revenue', {}).get('grand_total', 0),
            'impact_score': brain.get('impact', {}).get('impact_score', 0),
            'viral_potential': brain.get('reach', {}).get('viral_potential', ''),
        },
        'performance': {},
        'source_file': 'three_d_brain.json',
    }]

def collect_directives():
    """Collect human directives — what you told the system."""
    directives = load_json(DATA / 'directives.json')
    if not directives or not directives.get('raw'):
        return []
    return [{
        'timestamp': directives.get('date', TODAY) + 'T00:00:00',
        'engine': 'human',
        'type': 'directive',
        'platform': 'notion',
        'content': directives.get('raw', '')[:2000],
        'metadata': {
            'parsed_by': directives.get('parsed_by', 'keyword'),
            'pause': directives.get('pause', []),
            'priority': directives.get('priority', []),
            'amplify': directives.get('amplify', []),
            'message': directives.get('human_message', ''),
        },
        'performance': {},
        'source_file': 'directives.json',
    }]

def collect_art_outputs():
    """Collect generated art prompts and URLs."""
    records = []
    art_data = load_json(DATA / 'generated_art.json')
    arts = art_data if isinstance(art_data, list) else art_data.get('art', [])
    for art in arts[-20:]:
        records.append({
            'timestamp': art.get('timestamp', art.get('date', TODAY) + 'T00:00:00'),
            'engine': 'art_cause_generator',
            'type': 'art_output',
            'platform': 'huggingface',
            'content': art.get('prompt', '')[:1000],
            'metadata': {
                'url': art.get('url', ''),
                'model': art.get('model', ''),
                'theme': art.get('theme', 'Gaza Rose'),
            },
            'performance': {
                'shared': art.get('shared', False),
                'platform': art.get('posted_to', []),
            },
            'source_file': 'generated_art.json',
        })
    return records

def collect_email_drafts():
    """Collect draft emails."""
    records = []
    email_path = ROOT / 'DRAFT_EMAILS.md'
    if not email_path.exists():
        return records
    content = email_path.read_text()[:5000]
    if content.strip():
        records.append({
            'timestamp': NOW,
            'engine': 'email_drafter',
            'type': 'email_draft',
            'platform': 'gmail',
            'content': content,
            'metadata': {},
            'performance': {},
            'source_file': 'DRAFT_EMAILS.md',
        })
    return records


# ── Deduplication ─────────────────────────────────────────────────────────────
def load_seen_hashes():
    seen_path = DATA / 'hf_seen_hashes.json'
    if seen_path.exists():
        try:
            return set(json.loads(seen_path.read_text()))
        except:
            pass
    return set()

def save_seen_hashes(hashes):
    (DATA / 'hf_seen_hashes.json').write_text(json.dumps(list(hashes)[-5000:]))

def record_hash(record):
    import hashlib
    key = f"{record.get('engine')}{record.get('type')}{record.get('content','')[:100]}"
    return hashlib.md5(key.encode()).hexdigest()


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print(f'\n[hf_dataset] HuggingFace Dataset Logger — {TODAY}')
    DATA.mkdir(parents=True, exist_ok=True)

    # Collect all outputs
    all_records = []
    collectors = [
        ('social posts',   collect_social_posts),
        ('grant drafts',   collect_grant_drafts),
        ('gumroad prods',  collect_gumroad_products),
        ('brain decisions',collect_brain_decisions),
        ('directives',     collect_directives),
        ('art outputs',    collect_art_outputs),
        ('email drafts',   collect_email_drafts),
    ]
    for name, fn in collectors:
        try:
            records = fn()
            print(f'[hf_dataset] {name}: {len(records)} records')
            all_records.extend(records)
        except Exception as e:
            print(f'[hf_dataset] Error collecting {name}: {e}')

    # Deduplicate
    seen = load_seen_hashes()
    new_records = []
    for r in all_records:
        h = record_hash(r)
        if h not in seen:
            seen.add(h)
            new_records.append(r)
    save_seen_hashes(seen)
    print(f'[hf_dataset] New records: {len(new_records)} (of {len(all_records)} total)')

    if not new_records:
        print('[hf_dataset] Nothing new to log')
        return

    # Append to local JSONL log (always)
    with open(LOCAL_LOG, 'a') as f:
        for r in new_records:
            f.write(json.dumps(r) + '\n')
    print(f'[hf_dataset] Appended {len(new_records)} records to {LOCAL_LOG}')

    # Upload to HuggingFace
    if not HF_TOKEN:
        print('[hf_dataset] No HF_TOKEN — logged locally only')
        return

    dataset_ready = ensure_dataset_exists()
    if dataset_ready:
        ok = upload_jsonl_to_hf(new_records)
        if not ok:
            # Queue for retry
            with open(QUEUE_LOG, 'a') as f:
                for r in new_records:
                    f.write(json.dumps(r) + '\n')
            print(f'[hf_dataset] Upload failed — queued {len(new_records)} records for retry')
    else:
        with open(QUEUE_LOG, 'a') as f:
            for r in new_records:
                f.write(json.dumps(r) + '\n')
        print(f'[hf_dataset] Queued {len(new_records)} records (dataset not ready yet)')

    # Try to flush queue
    if QUEUE_LOG.exists():
        try:
            queued = [json.loads(l) for l in QUEUE_LOG.read_text().strip().split('\n') if l.strip()]
            if queued and upload_jsonl_to_hf(queued):
                QUEUE_LOG.unlink()
                print(f'[hf_dataset] Flushed {len(queued)} queued records')
        except Exception as e:
            print(f'[hf_dataset] Queue flush error: {e}')

    # Update stats
    total_lines = sum(1 for _ in open(LOCAL_LOG)) if LOCAL_LOG.exists() else 0
    print(f'[hf_dataset] Total records in local log: {total_lines}')
    print(f'[hf_dataset] Dataset: https://huggingface.co/datasets/{DATASET_ID}')
    print('[hf_dataset] Done.')


if __name__ == '__main__':
    run()
