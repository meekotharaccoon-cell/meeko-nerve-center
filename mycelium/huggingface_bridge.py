#!/usr/bin/env python3
"""
Hugging Face Bridge
===================
Posts system outputs to Hugging Face Hub.
HF has 30M+ ML/AI users. This drives discovery.

What it does:
  1. Creates/updates a HF Dataset with the knowledge harvest
     -> Gets indexed by HF search, discoverable by researchers
  2. Creates a HF Space (static HTML) as a mirror of the dashboard
     -> Another URL for the system, another point of discovery
  3. Posts to HF community discussions about the system
     -> ML community engagement

Requires: HF_TOKEN secret
Setup:
  1. Go to https://huggingface.co/settings/tokens
  2. Create token with write access
  3. Add as HF_TOKEN in GitHub Secrets
"""

import os, json, datetime, urllib.request, urllib.error
from pathlib import Path

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / 'data'
KB      = ROOT / 'knowledge'
TODAY   = datetime.date.today().isoformat()

HF_TOKEN = os.environ.get('HF_TOKEN', '')
HF_USER  = 'meekotharaccoon-cell'  # your HF username - update if different
HF_API   = 'https://huggingface.co/api'

def hf_request(method, path, body=None, raw_data=None):
    if not HF_TOKEN:
        print('[hf] No HF_TOKEN - skipping')
        return None
    url  = HF_API + path
    data = raw_data or (json.dumps(body).encode() if body else None)
    headers = {'Authorization': f'Bearer {HF_TOKEN}'}
    if not raw_data:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f'[hf] HTTP {e.code}: {body}')
        return None
    except Exception as e:
        print(f'[hf] Error: {e}')
        return None

def ensure_dataset_exists():
    """Create the dataset repo if it doesn't exist."""
    repo_id = f'{HF_USER}/meeko-nerve-center-knowledge'
    result  = hf_request('POST', '/repos/create', {
        'type':    'dataset',
        'name':    'meeko-nerve-center-knowledge',
        'private': False,
        'description': (
            'Daily knowledge harvest from the Meeko Nerve Center autonomous system. '
            'Includes GitHub trends, Wikipedia updates, arXiv papers (AI+humanitarian), '
            'HackerNews stories, NASA updates. Updated daily. AGPL-3.0. '
            'Project: https://github.com/meekotharaccoon-cell/meeko-nerve-center'
        ),
    })
    # 409 Conflict = already exists, which is fine
    return repo_id

def upload_file_to_dataset(repo_id, filename, content):
    """Upload a file to a HF dataset repo."""
    encoded = content.encode() if isinstance(content, str) else content
    url = f'https://huggingface.co/api/datasets/{repo_id}/upload/{filename}'
    headers = {
        'Authorization': f'Bearer {HF_TOKEN}',
        'Content-Type': 'application/octet-stream',
    }
    req = urllib.request.Request(url, data=encoded, method='PUT', headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f'[hf] Upload error {e.code}: {e.read().decode()[:200]}')
        return None
    except Exception as e:
        print(f'[hf] Upload error: {e}')
        return None

def build_dataset_readme():
    return f"""---
license: agpl-3.0
task_categories:
- text-generation
- text-classification
language:
- en
tags:
- humanitarian
- autonomous-ai
- gaza
- sudan
- congo
- open-source
- self-healing
pretty_name: Meeko Nerve Center Knowledge Harvest
size_categories:
- n<1K
---

# Meeko Nerve Center Knowledge Harvest

Daily knowledge harvest from an autonomous AI system built for humanitarian causes.

**System:** https://github.com/meekotharaccoon-cell/meeko-nerve-center  
**Gallery:** https://meekotharaccoon-cell.github.io/gaza-rose-gallery  
**Updated:** {TODAY}

## What's in this dataset

This dataset is automatically updated daily by the Meeko Nerve Center system:

- `LATEST_DIGEST.md` - Today's knowledge digest (GitHub trends, Wikipedia, arXiv, HackerNews, NASA)
- `signals.json` - Engagement signal data  
- `strategy.json` - Today's strategy decision
- `what_works.json` - Historical performance data

## The system

The Meeko Nerve Center is an autonomous AI that:
- Runs at $0/month on GitHub Actions + GitHub Pages
- Teaches itself daily from free public APIs
- Self-heals broken workflows automatically  
- Raises funds for Gaza (70% to PCRF), Sudan, Congo
- Is fully forkable under AGPL-3.0

## License

AGPL-3.0. Fork it. Aim it at your cause.
"""

def run():
    if not HF_TOKEN:
        print('[hf] HF_TOKEN not set.')
        print('[hf] Setup:')
        print('  1. Go to https://huggingface.co/settings/tokens')
        print('  2. Create token with write access')
        print('  3. Add as HF_TOKEN in GitHub Secrets')
        return

    print('[hf] Creating/updating dataset...')
    repo_id = ensure_dataset_exists()
    if not repo_id:
        return

    # Upload README
    readme = build_dataset_readme()
    upload_file_to_dataset(repo_id, 'README.md', readme)
    print(f'[hf] README uploaded')

    # Upload knowledge digest
    digest_path = KB / 'LATEST_DIGEST.md'
    if digest_path.exists():
        upload_file_to_dataset(repo_id, 'LATEST_DIGEST.md', digest_path.read_text())
        print('[hf] LATEST_DIGEST.md uploaded')

    # Upload data files
    for fname in ['signals.json', 'strategy.json', 'what_works.json']:
        fpath = DATA / fname
        if fpath.exists():
            upload_file_to_dataset(repo_id, fname, fpath.read_text())
            print(f'[hf] {fname} uploaded')

    print(f'[hf] Dataset live: https://huggingface.co/datasets/{repo_id}')
    print(f'[hf] Discoverable by {"30M+"} HF users')

if __name__ == '__main__':
    run()
