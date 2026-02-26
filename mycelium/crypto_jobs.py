#!/usr/bin/env python3
"""
Crypto Jobs Engine
==================
Jobicy API -> finds remote jobs globally.
Flags which ones mention crypto/Web3/blockchain pay.
Also pulls from other free job sources.

Outputs:
  - data/jobs_today.json        raw job data
  - content/queue/jobs_*.md     ready-to-post content
  - knowledge/jobs/latest.md    digest for the brain

Use case for YOU:
  - Find remote work that pays in crypto
  - Surface humanitarian/nonprofit/open source jobs
  - Content: 'Remote jobs hiring today that pay in BTC/ETH/SOL'

Use case for SYSTEM:
  - Revenue stream research
  - Audience targeting (people who want crypto jobs = your audience)
  - Grant/funding opportunity detection in job listings
"""

import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
CONT  = ROOT / 'content' / 'queue'

for d in [DATA, KB / 'jobs', CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

CRYPTO_KEYWORDS = [
    'crypto', 'bitcoin', 'ethereum', 'solana', 'web3', 'blockchain',
    'defi', 'nft', 'dao', 'token', 'wallet', 'lightning', 'layer 2',
    'smart contract', 'dex', 'protocol', 'on-chain',
]

MISSION_KEYWORDS = [
    'humanitarian', 'nonprofit', 'open source', 'climate', 'environment',
    'social impact', 'charity', 'ngo', 'education', 'health', 'community',
    'human rights', 'transparency', 'civic', 'public interest',
]

HIGH_VALUE_KEYWORDS = [
    'remote', 'senior', 'lead', 'principal', 'staff', 'architect',
    'python', 'rust', 'go', 'typescript', 'react', 'node',
    'machine learning', 'ai', 'data engineer', 'devops', 'security',
]

def fetch_json(url, timeout=15):
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[jobs] fetch error: {e}')
        return None

def fetch_jobicy():
    """Jobicy free API - no auth needed."""
    print('[jobs] Fetching Jobicy...')
    results = []
    
    # Multiple category pulls
    endpoints = [
        'https://jobicy.com/api/v2/remote-jobs?count=50&industry=engineering',
        'https://jobicy.com/api/v2/remote-jobs?count=50&industry=design',
        'https://jobicy.com/api/v2/remote-jobs?count=50&industry=marketing',
        'https://jobicy.com/api/v2/remote-jobs?count=50&tag=crypto',
        'https://jobicy.com/api/v2/remote-jobs?count=50&tag=blockchain',
        'https://jobicy.com/api/v2/remote-jobs?count=50&tag=python',
        'https://jobicy.com/api/v2/remote-jobs?count=50&tag=ai',
    ]
    
    seen = set()
    for url in endpoints:
        data = fetch_json(url)
        if not data: continue
        jobs = data.get('jobs', [])
        for job in jobs:
            jid = job.get('id', job.get('url', ''))
            if jid in seen: continue
            seen.add(jid)
            results.append({
                'id':       jid,
                'title':    job.get('jobTitle', ''),
                'company':  job.get('companyName', ''),
                'location': job.get('jobGeo', 'Remote'),
                'type':     job.get('jobType', ''),
                'industry': job.get('jobIndustry', ''),
                'salary':   job.get('annualSalaryMin', ''),
                'url':      job.get('url', ''),
                'excerpt':  job.get('jobExcerpt', '')[:300],
                'tags':     job.get('jobTag', []),
                'date':     job.get('pubDate', TODAY),
            })
    
    print(f'[jobs] Got {len(results)} unique jobs from Jobicy')
    return results

def fetch_remotive():
    """Remotive.com - free remote job API."""
    print('[jobs] Fetching Remotive...')
    data = fetch_json('https://remotive.com/api/remote-jobs?limit=100')
    if not data: return []
    
    results = []
    for job in data.get('jobs', []):
        results.append({
            'id':       str(job.get('id', '')),
            'title':    job.get('title', ''),
            'company':  job.get('company_name', ''),
            'location': 'Remote',
            'type':     job.get('job_type', ''),
            'industry': job.get('category', ''),
            'salary':   job.get('salary', ''),
            'url':      job.get('url', ''),
            'excerpt':  job.get('description', '')[:300],
            'tags':     job.get('tags', []),
            'date':     job.get('publication_date', TODAY)[:10],
            'source':   'remotive',
        })
    
    print(f'[jobs] Got {len(results)} jobs from Remotive')
    return results

def score_job(job):
    text = (job.get('title','') + ' ' + job.get('excerpt','') + ' ' + 
            ' '.join(job.get('tags', []) if isinstance(job.get('tags'), list) else [])).lower()
    
    scores = {'crypto': 0, 'mission': 0, 'value': 0, 'total': 0}
    
    for kw in CRYPTO_KEYWORDS:
        if kw in text: scores['crypto'] += 3
    for kw in MISSION_KEYWORDS:
        if kw in text: scores['mission'] += 3
    for kw in HIGH_VALUE_KEYWORDS:
        if kw in text: scores['value'] += 1
    
    if job.get('salary'): scores['value'] += 2
    scores['total'] = scores['crypto'] + scores['mission'] + scores['value']
    return scores

def build_content(jobs):
    """Generate social posts from job data."""
    posts = []
    
    crypto_jobs = [j for j in jobs if j['scores']['crypto'] > 0]
    mission_jobs = [j for j in jobs if j['scores']['mission'] > 0]
    
    if crypto_jobs:
        top = crypto_jobs[:3]
        lines = ['Remote jobs paying in crypto / Web3 hiring today:\n']
        for j in top:
            lines.append(f"\u2022 {j['title']} @ {j['company']}")
            if j.get('url'): lines.append(f"  {j['url']}")
        lines.append('\nFull list: meekotharaccoon-cell.github.io/meeko-nerve-center')
        lines.append('\n#RemoteWork #Crypto #Web3 #Jobs #GetPaid')
        posts.append({
            'type': 'crypto_jobs',
            'platform': 'mastodon',
            'text': '\n'.join(lines),
            'job_count': len(crypto_jobs),
        })
    
    if mission_jobs:
        top = mission_jobs[:3]
        lines = ['Remote jobs at mission-driven orgs:\n']
        for j in top:
            lines.append(f"\u2022 {j['title']} @ {j['company']}")
            if j.get('url'): lines.append(f"  {j['url']}")
        lines.append('\n#NonProfit #SocialImpact #RemoteWork #Jobs')
        posts.append({
            'type': 'mission_jobs',
            'platform': 'mastodon', 
            'text': '\n'.join(lines),
            'job_count': len(mission_jobs),
        })
    
    return posts

def run():
    print(f'[jobs] Starting job harvest \u2014 {TODAY}')
    
    all_jobs = []
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_remotive())
    
    # Deduplicate
    seen_titles = set()
    unique = []
    for j in all_jobs:
        key = (j.get('title','').lower(), j.get('company','').lower())
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(j)
    
    print(f'[jobs] {len(unique)} unique jobs after dedup')
    
    # Score each
    for job in unique:
        job['scores'] = score_job(job)
    
    # Sort by total score
    unique.sort(key=lambda j: j['scores']['total'], reverse=True)
    
    crypto = [j for j in unique if j['scores']['crypto'] > 0]
    mission = [j for j in unique if j['scores']['mission'] > 0]
    
    print(f'[jobs] {len(crypto)} crypto/Web3 jobs, {len(mission)} mission-aligned jobs')
    
    # Save data
    output = {
        'date': TODAY,
        'total': len(unique),
        'crypto_jobs': crypto[:20],
        'mission_jobs': mission[:20],
        'top_50': unique[:50],
    }
    (DATA / 'jobs_today.json').write_text(json.dumps(output, indent=2))
    
    # Build content posts
    posts = build_content(unique)
    
    # Save knowledge digest
    lines = [f'# Remote Jobs Digest \u2014 {TODAY}', '',
             f'Total: {len(unique)} | Crypto/Web3: {len(crypto)} | Mission: {len(mission)}', '']
    
    if crypto:
        lines += ['## Top Crypto/Web3 Jobs', '']
        for j in crypto[:5]:
            lines.append(f"- **{j['title']}** @ {j['company']} | {j.get('url','')}")
        lines.append('')
    
    if mission:
        lines += ['## Top Mission-Aligned Jobs', '']
        for j in mission[:5]:
            lines.append(f"- **{j['title']}** @ {j['company']} | {j.get('url','')}")
        lines.append('')
    
    digest = '\n'.join(lines)
    (KB / 'jobs' / f'{TODAY}.md').write_text(digest)
    (KB / 'jobs' / 'latest.md').write_text(digest)
    
    # Save content
    if posts:
        post_file = CONT / f'jobs_{TODAY}.json'
        post_file.write_text(json.dumps(posts, indent=2))
        print(f'[jobs] {len(posts)} content posts generated')
    
    print(f'[jobs] Done.')
    if crypto:
        print(f'[jobs] Top crypto job: {crypto[0]["title"]} @ {crypto[0]["company"]}')
    
    return output

if __name__ == '__main__':
    run()
