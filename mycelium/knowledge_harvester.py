#!/usr/bin/env python3
"""
Knowledge Harvester — pulls from free, open, zero-auth public sources daily.
Outputs structured markdown files into knowledge/ for the system to use.
"""

import os, json, datetime, time, textwrap, re
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

ROOT       = Path(__file__).parent.parent
KNOWLEDGE  = ROOT / 'knowledge'
TODAY      = datetime.date.today().isoformat()
EXTRA      = os.environ.get('EXTRA_TOPIC', '').strip()

def mkdir(p): p.mkdir(parents=True, exist_ok=True); return p

mkdir(KNOWLEDGE)
for d in ['github','wikipedia','arxiv','hackernews','nasa','repos','digest']:
    mkdir(KNOWLEDGE / d)

S = requests.Session()
S.headers.update({'User-Agent': 'meeko-nerve-center/1.0 (github.com/meekotharaccoon-cell)'})

def get(url, **kw):
    try:
        r = S.get(url, timeout=20, **kw)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f'  ✗ {url[:70]} — {e}')
        return None

def save(path, content):
    path.write_text(content, encoding='utf-8')
    print(f'  ✓ {path.relative_to(ROOT)}')

def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')[:60]

# ─────────────────────────────────────────────────────────────────────────────
# 1. GITHUB — Trending repos across key topics
# ─────────────────────────────────────────────────────────────────────────────
print('\n🐙 GitHub repos...')

GH_TOPICS = [
    'autonomous-agents',
    'self-replicating',
    'solarpunk',
    'mutual-aid',
    'free-software',
    'agpl',
    'humanitarian',
    'decentralized',
    'open-source-ai',
    'local-llm',
    'ollama',
    'github-actions-automation',
    'no-code-automation',
    'passive-income',
    'digital-products',
]

if EXTRA:
    GH_TOPICS.append(slug(EXTRA))

gh_rows = []
for topic in GH_TOPICS:
    r = get(f'https://api.github.com/search/repositories'
            f'?q=topic:{topic}&sort=stars&order=desc&per_page=5')
    if not r: continue
    items = r.json().get('items', [])
    for repo in items:
        gh_rows.append({
            'name':        repo['full_name'],
            'url':         repo['html_url'],
            'description': repo.get('description') or '',
            'stars':       repo['stargazers_count'],
            'language':    repo.get('language') or 'unknown',
            'topic':       topic,
            'updated':     repo['updated_at'][:10],
        })
    time.sleep(0.4)

# dedupe by name, keep highest stars
seen = {}
for row in gh_rows:
    n = row['name']
    if n not in seen or row['stars'] > seen[n]['stars']:
        seen[n] = row
gh_rows = sorted(seen.values(), key=lambda x: x['stars'], reverse=True)

lines = [f'# GitHub Knowledge — {TODAY}', '',
         f'*{len(gh_rows)} repos across {len(GH_TOPICS)} topics.*', '',
         '| Repo | Stars | Language | Topic |',
         '|------|-------|----------|-------|']
for r in gh_rows[:80]:
    desc = r['description'][:80].replace('|','‖') if r['description'] else '—'
    lines.append(f"| [{r['name']}]({r['url']}) | ⭐{r['stars']:,} | {r['language']} | {r['topic']} |")

lines += ['', '## Full Details', '']
for r in gh_rows[:40]:
    lines += [
        f"### [{r['name']}]({r['url']})",
        f"**Stars:** {r['stars']:,} · **Language:** {r['language']} · **Topic:** {r['topic']}",
        f"> {r['description'][:200]}" if r['description'] else '',
        f'Updated: {r["updated"]}', ''
    ]

save(KNOWLEDGE/'github'/f'{TODAY}.md', '\n'.join(lines))

# Write a latest symlink-equivalent (just overwrite)
save(KNOWLEDGE/'github'/'latest.md', '\n'.join(lines))

# Also save machine-readable JSON for other scripts to consume
(KNOWLEDGE/'github'/'latest.json').write_text(
    json.dumps(gh_rows[:80], indent=2), encoding='utf-8')
print(f'  → {len(gh_rows)} repos harvested')

# ─────────────────────────────────────────────────────────────────────────────
# 2. WIKIPEDIA — Key topics as reference knowledge
# ─────────────────────────────────────────────────────────────────────────────
print('\n📖 Wikipedia...')

WIKI_TOPICS = [
    'Solarpunk',
    'Mutual aid (organization theory)',
    'Free and open-source software',
    'Autonomous agent',
    'Self-replication',
    'Decentralization',
    'Commons-based peer production',
    'Digital commons',
    'AGPL',
    'GitHub Actions',
    'Palestinian Children\'s Relief Fund',
    'Humanitarian aid',
]

if EXTRA:
    WIKI_TOPICS.append(EXTRA)

wiki_summaries = []
for topic in WIKI_TOPICS:
    r = get('https://en.wikipedia.org/api/rest_v1/page/summary/' +
            requests.utils.quote(topic))
    if not r: continue
    d = r.json()
    if d.get('type') == 'disambiguation': continue
    wiki_summaries.append({
        'title':   d.get('title',''),
        'url':     d.get('content_urls',{}).get('desktop',{}).get('page',''),
        'extract': d.get('extract',''),
    })
    time.sleep(0.3)

lines = [f'# Wikipedia Knowledge — {TODAY}', '']
for w in wiki_summaries:
    lines += [
        f"## {w['title']}",
        f"[Wikipedia]({w['url']})",
        '',
        w['extract'],
        ''
    ]

save(KNOWLEDGE/'wikipedia'/f'{TODAY}.md', '\n'.join(lines))
save(KNOWLEDGE/'wikipedia'/'latest.md',  '\n'.join(lines))
print(f'  → {len(wiki_summaries)} articles')

# ─────────────────────────────────────────────────────────────────────────────
# 3. ARXIV — AI + autonomous systems papers
# ─────────────────────────────────────────────────────────────────────────────
print('\n📄 arXiv papers...')

ARXIV_QUERIES = [
    'autonomous+agents+open+source',
    'self+replicating+systems',
    'decentralized+AI',
    'local+language+models+deployment',
    'humanitarian+AI+applications',
    'mutual+aid+networks+technology',
]

papers = []
for q in ARXIV_QUERIES:
    r = get(f'https://export.arxiv.org/api/query?search_query=all:{q}'
            f'&start=0&max_results=3&sortBy=lastUpdatedDate&sortOrder=descending')
    if not r: continue
    # parse Atom XML minimally
    entries = re.findall(r'<entry>(.*?)</entry>', r.text, re.DOTALL)
    for entry in entries:
        title   = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
        summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
        link    = re.search(r'<id>(.*?)</id>', entry)
        authors = re.findall(r'<name>(.*?)</name>', entry)
        if title and summary:
            papers.append({
                'title':   title.group(1).strip().replace('\n',' '),
                'summary': summary.group(1).strip()[:600],
                'url':     link.group(1).strip() if link else '',
                'authors': authors[:3],
                'query':   q.replace('+',' '),
            })
    time.sleep(0.5)

lines = [f'# arXiv Papers — {TODAY}', '',
         f'*{len(papers)} papers across {len(ARXIV_QUERIES)} queries.*', '']
for p in papers:
    lines += [
        f"## {p['title']}",
        f"**Authors:** {', '.join(p['authors'])}  ",
        f"**Query:** {p['query']}  ",
        f"**URL:** {p['url']}",
        '',
        textwrap.fill(p['summary'], 100),
        ''
    ]

save(KNOWLEDGE/'arxiv'/f'{TODAY}.md', '\n'.join(lines))
save(KNOWLEDGE/'arxiv'/'latest.md',  '\n'.join(lines))
print(f'  → {len(papers)} papers')

# ─────────────────────────────────────────────────────────────────────────────
# 4. HACKERNEWS — Top stories + Show HN (builders sharing projects)
# ─────────────────────────────────────────────────────────────────────────────
print('\n🔶 HackerNews...')

hn_top = get('https://hacker-news.firebaseio.com/v0/topstories.json')
hn_show= get('https://hacker-news.firebaseio.com/v0/showstories.json')

hn_stories = []
for story_id in ((hn_top.json() if hn_top else [])[:15] +
                 (hn_show.json() if hn_show else [])[:10]):
    r = get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
    if not r: continue
    d = r.json()
    if not d or not d.get('title'): continue
    hn_stories.append({
        'title': d['title'],
        'url':   d.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
        'score': d.get('score', 0),
        'by':    d.get('by',''),
        'type':  'show' if story_id in (hn_show.json() if hn_show else []) else 'top',
    })
    time.sleep(0.1)

lines = [f'# HackerNews — {TODAY}', '',
         '## Top Stories', '']
for s in [x for x in hn_stories if x['type']=='top']:
    lines.append(f"- [{s['title']}]({s['url']}) *(▲{s['score']} by {s['by']})*")

lines += ['', '## Show HN (builders)', '']
for s in [x for x in hn_stories if x['type']=='show']:
    lines.append(f"- [{s['title']}]({s['url']}) *(▲{s['score']} by {s['by']})*")

save(KNOWLEDGE/'hackernews'/f'{TODAY}.md', '\n'.join(lines))
save(KNOWLEDGE/'hackernews'/'latest.md',  '\n'.join(lines))
print(f'  → {len(hn_stories)} stories')

# ─────────────────────────────────────────────────────────────────────────────
# 5. NASA — free endpoints, no key required
# ─────────────────────────────────────────────────────────────────────────────
print('\n🚀 NASA...')

nasa_lines = [f'# NASA Data — {TODAY}', '']

# ISS position
r = get('http://api.open-notify.org/iss-now.json')
if r:
    d = r.json()['iss_position']
    nasa_lines += [
        '## ISS Position', '',
        f"Latitude: {d['latitude']}",
        f"Longitude: {d['longitude']}",
        f"Captured: {TODAY}", ''
    ]

# People in space
r = get('http://api.open-notify.org/astros.json')
if r:
    d = r.json()
    nasa_lines += ['## People in Space', '']
    for p in d['people']:
        nasa_lines.append(f"- {p['name']} ({p['craft']})")
    nasa_lines.append('')

# NASA APOD (demo key = 100 req/day)
r = get('https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY')
if r:
    d = r.json()
    nasa_lines += [
        '## Astronomy Picture of the Day', '',
        f"**{d.get('title','')}** ({d.get('date','')})",
        '',
        d.get('explanation','')[:800],
        '',
        f"Image: {d.get('url','')}", ''
    ]

# Near Earth Objects — 7-day window
from datetime import date, timedelta
end = date.today() + timedelta(days=7)
r = get(f'https://api.nasa.gov/neo/rest/v1/feed'
        f'?start_date={TODAY}&end_date={end}&api_key=DEMO_KEY')
if r:
    neo = r.json()
    total = neo.get('element_count', 0)
    nasa_lines += ['## Near Earth Objects (next 7 days)', '',
                   f'Total: {total}', '']
    for day_data in list(neo.get('near_earth_objects',{}).values())[:3]:
        for obj in day_data[:2]:
            name = obj['name']
            diam = obj['estimated_diameter']['meters']
            haz  = '⚠️ HAZARDOUS' if obj['is_potentially_hazardous_asteroid'] else 'safe'
            nasa_lines.append(
                f"- **{name}** — {diam['estimated_diameter_min']:.0f}–"
                f"{diam['estimated_diameter_max']:.0f}m — {haz}"
            )
    nasa_lines.append('')

save(KNOWLEDGE/'nasa'/f'{TODAY}.md', '\n'.join(nasa_lines))
save(KNOWLEDGE/'nasa'/'latest.md',  '\n'.join(nasa_lines))
print('  → NASA data captured')

# ─────────────────────────────────────────────────────────────────────────────
# 6. REPOS — Deep-read specific high-value open source repos
#    Fetches README + key files from repos directly relevant to this system
# ─────────────────────────────────────────────────────────────────────────────
print('\n📦 Deep-reading key repos...')

REPOS_TO_READ = [
    # autonomous systems / self-hosting
    ('n8n-io/n8n',               'automation'),
    ('Significant-Gravitas/AutoGPT', 'autonomous-ai'),
    ('microsoft/autogen',        'multi-agent'),
    ('crewAIInc/crewAI',         'multi-agent'),
    ('ollama/ollama',            'local-llm'),
    # solarpunk / mutual aid tech
    ('publiclab/plots2',         'humanitarian'),
    ('hotosm/tasking-manager',   'humanitarian'),
    # revenue / digital products
    ('gumroad/gumroad',          'revenue'),   # may be private, will skip
    # github actions
    ('sdras/awesome-actions',    'automation'),
    ('nickvdyck/github-actions-awesome', 'automation'),
]

for full_name, category in REPOS_TO_READ:
    r = get(f'https://api.github.com/repos/{full_name}')
    if not r: continue
    meta = r.json()
    if 'message' in meta: continue  # 404 or private

    # fetch README
    readme_r = get(f'https://api.github.com/repos/{full_name}/readme')
    readme_text = ''
    if readme_r:
        import base64
        try:
            readme_text = base64.b64decode(
                readme_r.json().get('content','')
            ).decode('utf-8', errors='replace')[:3000]
        except Exception:
            pass

    lines = [
        f"# {full_name}",
        f"*Category: {category} · Harvested: {TODAY}*",
        '',
        f"**Stars:** {meta['stargazers_count']:,}  ",
        f"**Language:** {meta.get('language','?')}  ",
        f"**License:** {(meta.get('license') or {}).get('spdx_id','?')}  ",
        f"**URL:** {meta['html_url']}",
        '',
        f"> {meta.get('description','')}",
        '',
        '## README (first 3000 chars)',
        '',
        readme_text,
    ]
    fname = slug(full_name.replace('/', '_'))
    save(KNOWLEDGE/'repos'/f'{fname}.md', '\n'.join(lines))
    time.sleep(0.5)

print('  → Repo snapshots saved')

# ─────────────────────────────────────────────────────────────────────────────
# 7. DAILY DIGEST — single file combining everything, ready for the system
# ─────────────────────────────────────────────────────────────────────────────
print('\n📋 Writing daily digest...')

digest = [
    f'# 🧠 Daily Knowledge Digest — {TODAY}',
    f'*Auto-generated by knowledge_harvester.py*',
    '',
    '## Summary',
    '',
    f'- **GitHub repos harvested:** {len(gh_rows)}',
    f'- **Wikipedia articles:** {len(wiki_summaries)}',
    f'- **arXiv papers:** {len(papers)}',
    f'- **HackerNews stories:** {len(hn_stories)}',
    f'- **Sources:** GitHub API, Wikipedia, arXiv, HackerNews, NASA, public repos',
    '',
    '## Top GitHub Repos Today',
    '',
]
for row in gh_rows[:10]:
    digest.append(f"- [{row['name']}]({row['url']}) ⭐{row['stars']:,} — {row['description'][:80]}")

digest += [
    '',
    '## Today in HackerNews',
    '',
]
for s in hn_stories[:8]:
    digest.append(f"- [{s['title']}]({s['url']})")

digest += [
    '',
    '## New Papers',
    '',
]
for p in papers[:5]:
    digest.append(f"- [{p['title']}]({p['url']})")

digest += [
    '',
    '---',
    f'*Files: knowledge/github/ · knowledge/wikipedia/ · knowledge/arxiv/ · knowledge/hackernews/ · knowledge/nasa/ · knowledge/repos/*',
    f'*Next update: tomorrow 5am UTC via knowledge-harvester.yml*'
]

save(KNOWLEDGE/'digest'/f'{TODAY}.md',   '\n'.join(digest))
save(KNOWLEDGE/'digest'/'latest.md',     '\n'.join(digest))
save(KNOWLEDGE/'LATEST_DIGEST.md',       '\n'.join(digest))

# ─────────────────────────────────────────────────────────────────────────────
# 8. INDEX — master index of all knowledge files
# ─────────────────────────────────────────────────────────────────────────────
all_files = sorted(KNOWLEDGE.rglob('*.md'))
index_lines = [
    '# 🧠 Knowledge Base Index',
    '',
    f'*{len(all_files)} files · Last updated: {TODAY}*',
    '',
    'Auto-built daily by knowledge_harvester.py from:',
    '- GitHub API (trending repos by topic)',
    '- Wikipedia REST API',
    '- arXiv API (research papers)',
    '- HackerNews Firebase API',
    '- NASA Open APIs (DEMO_KEY)',
    '- Direct repo README harvesting',
    '',
    '## Files',
    '',
]
for f in all_files:
    rel = f.relative_to(KNOWLEDGE)
    index_lines.append(f'- `{rel}`')

save(KNOWLEDGE/'INDEX.md', '\n'.join(index_lines))

print(f'\n✅ Harvest complete. {len(all_files)} total knowledge files.')
