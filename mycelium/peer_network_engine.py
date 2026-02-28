#!/usr/bin/env python3
"""
Peer Network Engine
====================
The system is an island. It monitors itself, posts about itself,
and evolves itself — but it has zero relationships with other
open source projects doing adjacent or complementary work.

This engine builds those relationships.

What it finds:
  1. GitHub repos with similar tags: autonomous-ai, open-source,
     humanitarian, accountability, solarpunk, self-evolving
  2. Active maintainers of those repos
  3. Opportunities to cross-promote, collaborate, or cite
  4. Open issues where this system's capabilities could help
  5. Projects that could become nodes in the network

What it does:
  1. Stars interesting repos (builds goodwill, gets noticed)
  2. Drafts outreach to maintainers (emails you the draft)
  3. Opens thoughtful issues on repos where relevant
  4. Adds to COLLABORATORS.md in the repo
  5. Generates a weekly digest of the peer landscape

Why this matters:
  One repo = invisible. A network of repos citing each other
  = Google juice, GitHub trending, community, cross-pollination.
  The system needs peers to become more than a solo project.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

OWN_REPO = 'meekotharaccoon-cell/meeko-nerve-center'
OWN_URL  = f'https://github.com/{OWN_REPO}'

SEARCH_QUERIES = [
    'topic:autonomous-ai stars:>10',
    'topic:solarpunk topic:open-source stars:>5',
    'topic:accountability topic:congress stars:>10',
    'topic:humanitarian topic:ai stars:>20',
    'topic:self-evolving stars:>5',
    'github-actions autonomous bot humanitarian stars:>10',
    'topic:palestine topic:open-source stars:>5',
]

def gh_get(path, params=''):
    if not GITHUB_TOKEN: return None
    url = f'https://api.github.com/{path}?{params}'
    try:
        req = urllib_request.Request(
            url,
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github+json',
            }
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[peers] GH error {path[:40]}: {e}')
        return None

def search_repos(query):
    from urllib.parse import quote
    data = gh_get(f'search/repositories', f'q={quote(query)}&sort=updated&per_page=5')
    if not data: return []
    return [{
        'full_name':    r.get('full_name'),
        'description':  r.get('description', '')[:100],
        'stars':        r.get('stargazers_count', 0),
        'url':          r.get('html_url'),
        'owner_email':  '',  # fetched separately
        'topics':       r.get('topics', []),
        'updated':      r.get('updated_at', '')[:10],
    } for r in data.get('items', [])]

def star_repo(full_name):
    if not GITHUB_TOKEN: return False
    try:
        req = urllib_request.Request(
            f'https://api.github.com/user/starred/{full_name}',
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github+json',
            },
            method='PUT'
        )
        req.add_header('Content-Length', '0')
        with urllib_request.urlopen(req, timeout=10) as r:
            return r.status in (204, 201)
    except:
        return False

def already_starred(full_name):
    log = load_peer_log()
    return full_name in log.get('starred', [])

def load_peer_log():
    p = DATA / 'peer_network_log.json'
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {'starred': [], 'outreach_sent': [], 'repos_found': [], 'last_run': ''}

def save_peer_log(log):
    try: (DATA / 'peer_network_log.json').write_text(json.dumps(log, indent=2))
    except: pass

def generate_outreach(repo):
    if not HF_TOKEN: return None
    prompt = f"""Write a genuine GitHub outreach message to the maintainer of this repo.

Their repo: {repo['full_name']}
Description: {repo['description']}
Topics: {repo['topics']}

Our repo: {OWN_URL}
What we do: Autonomous AI for Palestinian solidarity and congressional accountability.
Self-evolving, runs on GitHub Actions free tier, AGPL-3.0.

Write a short, genuine message (NOT a form letter) that:
- References something specific about their project
- Explains the connection/overlap honestly
- Proposes one concrete thing: cross-link, collaboration, or just mutual awareness
- Is under 150 words
- Sounds like a real person, not a bot

Just the message body. No subject line."""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 250,
            'messages': [
                {'role': 'system', 'content': 'You write genuine, specific outreach. Never generic.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except:
        return None

def update_collaborators_md(new_repos):
    collab_path = ROOT / 'COLLABORATORS.md'
    existing = collab_path.read_text() if collab_path.exists() else '# Peer Network\n\n'
    additions = ''
    for r in new_repos:
        line = f'- [{r["full_name"]}]({r["url"]}) — {r["description"][:80]}\n'
        if r['url'] not in existing:
            additions += line
    if additions:
        try:
            collab_path.write_text(existing.rstrip() + '\n\n' + additions)
            print(f'[peers] Added {len(new_repos)} repos to COLLABORATORS.md')
        except: pass

def send_peer_digest(new_repos, outreach_drafts):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    if not new_repos and not outreach_drafts: return
    lines = [f'Peer Network Digest — {TODAY}', '']
    if new_repos:
        lines.append(f'NEW PEERS FOUND ({len(new_repos)}):')
        for r in new_repos:
            lines.append(f'  ⭐ {r["full_name"]} ({r["stars"]} stars)')
            lines.append(f'     {r["description"][:80]}')
            lines.append(f'     {r["url"]}')
            lines.append('')
    if outreach_drafts:
        lines.append(f'OUTREACH DRAFTS:')
        for repo, draft in outreach_drafts:
            lines.append(f'  To: {repo["full_name"]} maintainer')
            lines.append(f'  Open an issue at: {repo["url"]}/issues/new')
            lines.append(f'  --- draft ---')
            lines.append(draft)
            lines.append('')
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🌐 Peer network: {len(new_repos)} new repos found'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[peers] Digest emailed')
    except Exception as e:
        print(f'[peers] Email error: {e}')

def run():
    print(f'\n[peers] Peer Network Engine — {TODAY}')

    log = load_peer_log()
    known = set(log.get('repos_found', []))

    all_repos = []
    for query in SEARCH_QUERIES[:3]:  # 3 queries per run to avoid rate limits
        repos = search_repos(query)
        for r in repos:
            if r['full_name'] != OWN_REPO and r['full_name'] not in known:
                all_repos.append(r)
                known.add(r['full_name'])

    print(f'[peers] Found {len(all_repos)} new peer repos')

    new_starred = []
    outreach_drafts = []

    for repo in all_repos[:5]:  # Process top 5 per run
        # Star the repo
        if not already_starred(repo['full_name']):
            ok = star_repo(repo['full_name'])
            if ok:
                log.setdefault('starred', []).append(repo['full_name'])
                new_starred.append(repo)
                print(f'[peers] ⭐ Starred {repo["full_name"]}')

        # Generate outreach draft (weekly, not daily)
        if WEEKDAY == 2 and repo['stars'] > 50:  # Wednesday, popular repos
            draft = generate_outreach(repo)
            if draft:
                outreach_drafts.append((repo, draft))
                log.setdefault('outreach_sent', []).append({
                    'repo': repo['full_name'], 'date': TODAY
                })

    log['repos_found'] = list(known)
    log['last_run']    = TODAY
    save_peer_log(log)

    update_collaborators_md(new_starred)
    send_peer_digest(new_starred, outreach_drafts)

    print(f'[peers] Done. Starred: {len(new_starred)} | Outreach: {len(outreach_drafts)}')

if __name__ == '__main__':
    run()
