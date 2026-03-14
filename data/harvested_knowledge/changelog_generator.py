#!/usr/bin/env python3
"""
CHANGELOG GENERATOR
====================
Reads git log. Writes CHANGELOG.md.
The system knows its own history.

No APIs. No tokens. Pure git.

Runs on every push via GitHub Actions.
Outputs: CHANGELOG.md (human-readable), data/changelog.json (machine-readable)

Groups commits by:
  - Week (recent activity visible at a glance)
  - Category (auto-detected from commit message emoji/keywords)

Categories detected:
  📚 lessons / knowledge / learn
  🤝 mutual aid / community
  📧 email / outreach
  📡 social / posting / cross-poster
  📊 data / tracking / signals
  ⚖️ legal / rights
  🌹 gallery / art
  🔍 SEO / search / discovery
  ⚙️ system / workflow / automation
  📝 docs / readme / guide
  🚹 fix / bug / patch
"""
import subprocess, json, re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path('data')
OUT_MD   = Path('CHANGELOG.md')
OUT_JSON = DATA_DIR / 'changelog.json'

CATEGORY_RULES = [
    ('lesson',   ['lesson', 'learn', 'knowledge', '📚', 'guide', 'tutorial', 'rights', 'tcpa', 'fdcpa']),
    ('mutual',   ['mutual aid', 'community', '🤝', 'board', 'grant']),
    ('email',    ['email', 'outreach', '📧', 'emailer', 'mailer']),
    ('social',   ['social', 'post', '📡', 'cross-poster', 'mastodon', 'bluesky', 'discord']),
    ('signal',   ['signal', 'track', '📊', 'analytic', 'metric', 'what works']),
    ('legal',    ['legal', '⚖️', 'law', 'rights', 'dispute']),
    ('art',      ['gallery', 'art', '🌹', 'flower', 'gumroad', 'shop']),
    ('seo',      ['seo', '🔍', 'search', 'sitemap', 'index', 'discovery']),
    ('fix',      ['fix', '🚹', 'bug', 'patch', 'correct', 'repair']),
    ('docs',     ['doc', '📝', 'readme', 'changelog', 'guide']),
    ('system',   ['⚙️', 'workflow', 'action', 'system', 'auto', 'spawn', 'fork', 'deploy']),
]

CATEGORY_LABELS = {
    'lesson':  '📚 Knowledge',
    'mutual':  '🤝 Community',
    'email':   '📧 Outreach',
    'social':  '📡 Social',
    'signal':  '📊 Signals',
    'legal':   '⚖️ Legal',
    'art':     '🌹 Art & Gallery',
    'seo':     '🔍 Discovery',
    'fix':     '🚹 Fixes',
    'docs':    '📝 Documentation',
    'system':  '⚙️ System',
    'other':   '• Other',
}

def get_commits():
    result = subprocess.run(
        ['git', 'log', '--format=%H|%ai|%s|%an', '--no-merges', '-n', '200'],
        capture_output=True, text=True
    )
    commits = []
    for line in result.stdout.strip().split('\n'):
        if not line.strip(): continue
        parts = line.split('|', 3)
        if len(parts) < 4: continue
        sha, date_str, subject, author = parts
        try:
            dt = datetime.fromisoformat(date_str.strip())
        except:
            continue
        commits.append({
            'sha': sha[:8],
            'date': dt.isoformat(),
            'week': dt.strftime('%Y-W%V'),
            'subject': subject.strip(),
            'author': author.strip(),
        })
    return commits

def categorize(subject):
    sl = subject.lower()
    for cat, keywords in CATEGORY_RULES:
        if any(kw in sl for kw in keywords):
            return cat
    return 'other'

def group_by_week(commits):
    weeks = defaultdict(list)
    for c in commits:
        weeks[c['week']].append(c)
    return dict(sorted(weeks.items(), reverse=True))

def week_label(week_str):
    try:
        year, w = week_str.split('-W')
        # Find first day of that ISO week
        from datetime import date
        d = date.fromisocalendar(int(year), int(w), 1)
        return d.strftime('Week of %B %-d, %Y')
    except:
        return week_str

def build_markdown(commits, by_week):
    total = len(commits)
    now   = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    lines = [
        '# CHANGELOG',
        '',
        '> Auto-generated from git history by `mycelium/changelog_generator.py`  ',
        f'> Last updated: {now}  ',
        f'> Total commits tracked: {total}',
        '',
        '---',
        '',
    ]

    for week, week_commits in list(by_week.items())[:16]:  # Last 16 weeks
        lines.append(f'## {week_label(week)}')
        lines.append('')

        # Group by category within week
        by_cat = defaultdict(list)
        for c in week_commits:
            by_cat[categorize(c['subject'])].append(c)

        for cat, label in CATEGORY_LABELS.items():
            if cat not in by_cat: continue
            lines.append(f'**{label}**')
            for c in by_cat[cat]:
                lines.append(f'- `{c["sha"]}` {c["subject"]}')
            lines.append('')

        lines.append('---')
        lines.append('')

    lines += [
        '## About This File',
        '',
        'This file is generated automatically on every push.',
        'It reads the git log and groups commits by week and category.',
        'No human writes it. The system documents itself.',
        '',
        '`mycelium/changelog_generator.py` — MIT License — fork freely',
    ]

    return '\n'.join(lines)

def run():
    print('\n' + '='*48)
    print('  CHANGELOG GENERATOR')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*48)

    commits = get_commits()
    print(f'  Commits found: {len(commits)}')

    if not commits:
        print('  No commits found. Are you in a git repo?')
        return

    by_week = group_by_week(commits)
    print(f'  Weeks covered: {len(by_week)}')

    # Write markdown
    md = build_markdown(commits, by_week)
    OUT_MD.write_text(md)
    print(f'  Written: {OUT_MD}')

    # Write JSON
    DATA_DIR.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps({
        'generated': datetime.now(timezone.utc).isoformat(),
        'total_commits': len(commits),
        'weeks': len(by_week),
        'commits': commits[:50],  # Last 50 in JSON
    }, indent=2))
    print(f'  Written: {OUT_JSON}')
    print('  System knows its own history. ✓')

if __name__ == '__main__':
    run()
