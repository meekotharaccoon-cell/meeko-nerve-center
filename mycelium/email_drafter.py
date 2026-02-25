#!/usr/bin/env python3
"""
Email Drafter
=============
Every morning, drafts ready-to-send emails for:
  1. Fix requests (anything in FIXES_NEEDED.md that needs a human)
  2. Grant outreach (based on what the knowledge harvester found)
  3. Tech press / blog outreach (journalists + communities)
  4. Charity partnerships (PCRF, IRC, UNHCR)
  5. Community outreach (Mastodon, HN, Dev.to)

Output: DRAFT_EMAILS.md (repo root) — human opens, reviews, sends.
Each email includes: To, Subject, Body — ready to copy-paste.

Also writes data/draft_emails.json for the dashboard widget.
"""

import json, datetime, re
from pathlib import Path

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
DATA.mkdir(exist_ok=True)

# ── Load context ───────────────────────────────────────────────────────────
fixes_text = ''
fixes_path = ROOT / 'FIXES_NEEDED.md'
if fixes_path.exists():
    fixes_text = fixes_path.read_text(encoding='utf-8')

heal_report = {}
heal_path = DATA / 'heal_report.json'
if heal_path.exists():
    try: heal_report = json.loads(heal_path.read_text())
    except: pass

strategy = {}
strat_path = DATA / 'strategy.json'
if strat_path.exists():
    try: strategy = json.loads(strat_path.read_text())
    except: pass

# ── Counts for subject lines ────────────────────────────────────────────
open_issues  = heal_report.get('needs_human', 0)
healed_total = heal_report.get('total_healed', 0)
primary      = strategy.get('primary_crisis', 'Gaza')

# ── Email templates ────────────────────────────────────────────────────

EMAILS = []

# — 1. PCRF Partnership ————————————————————————————————————————
EMAILS.append({
    'category': 'charity_partnership',
    'priority': 'high',
    'to': 'info@pcrf.net',
    'subject': 'Autonomous open-source art platform donating 70% to PCRF — partnership inquiry',
    'body': """\
Hello PCRF team,

I’m reaching out because I’ve built an open-source autonomous AI system
that generates and sells original digital art, with 70% of every sale going
directly to PCRF.

The gallery is live at:
https://meekotharaccoon-cell.github.io/gaza-rose-gallery

The system is built on GitHub Actions and GitHub Pages at zero cost, and the
entire source code is public under AGPL-3.0:
https://github.com/meekotharaccoon-cell/meeko-nerve-center

I wanted to reach out directly for a few reasons:
1. To make sure you’re aware the platform exists and is actively directing
   sales revenue to PCRF
2. To ask whether PCRF would be willing to mention or link to the gallery
   as a fundraising resource
3. To explore any formal partnership or verification that would help donors
   feel confident

I’m committed to this mission long-term. The system is designed to be
self-sustaining and to grow its reach over time.

Thank you for the work you do.

Best,
Meeko
https://github.com/meekotharaccoon-cell/meeko-nerve-center
"""
})

# — 2. NLnet Foundation grant ————————————————————————————————————
EMAILS.append({
    'category': 'grant',
    'priority': 'high',
    'to': 'foundation@nlnet.nl',
    'subject': 'NGI0 grant inquiry — autonomous humanitarian AI, AGPL, zero-cost infrastructure',
    'body': """\
Hello NLnet Foundation,

I’m writing to inquire about NGI0 funding for an open-source autonomous AI
system I’ve built for humanitarian purposes.

Project: Meeko Nerve Center
URL: https://github.com/meekotharaccoon-cell/meeko-nerve-center
License: AGPL-3.0

What it does:
• Harvests knowledge daily from public APIs (GitHub, Wikipedia, arXiv,
  HackerNews, NASA) with zero proprietary dependencies
• Runs a local LLM strategy brain (Ollama) that adapts content based on
  real engagement signals
• Self-heals broken workflows — diagnoses errors, applies fixes, writes
  plain-English instructions for anything requiring human intervention
• Raises funds for Gaza, Sudan, and Congo through art sales and digital
  products, with 70% going to verified charities
• Runs at $0/month on GitHub infrastructure
• Designed to be forked by anyone for any humanitarian cause

The system embodies several NGI values: decentralized infrastructure,
transparency (every commit is public), open standards, and humanitarian
benefit.

I’d welcome the chance to discuss whether this project fits your current
funding priorities.

Best regards,
Meeko
https://github.com/meekotharaccoon-cell/meeko-nerve-center
"""
})

# — 3. Mozilla Foundation ———————————————————————————————————————
EMAILS.append({
    'category': 'grant',
    'priority': 'medium',
    'to': 'awards@mozillafoundation.org',
    'subject': 'Mozilla Technology Fund inquiry — open-source autonomous humanitarian AI',
    'body': """\
Hello Mozilla Foundation team,

I’m writing to inquire about the Mozilla Technology Fund for a project that
aligns with Mozilla’s mission of trustworthy, beneficial AI.

Project: Meeko Nerve Center
https://github.com/meekotharaccoon-cell/meeko-nerve-center

This is a fully open-source autonomous AI system (AGPL-3.0) that:
• Runs on 100% free, public infrastructure (GitHub Actions + Pages)
• Uses only local AI models (Ollama) — no data sent to commercial AI APIs
• Self-monitors and self-heals its own errors
• Raises funds for humanitarian crises through transparent, verifiable
  mechanisms (70% of revenue to PCRF, a 4-star Charity Navigator org)
• Is designed to be forkable by anyone for any cause

The project demonstrates that AI can be:
- Genuinely autonomous without being opaque
- Beneficial without being extractive
- Powerful without requiring corporate infrastructure

I believe this fits the Responsible Computer Science Challenge and
Technology Fund priorities.

Thank you for your consideration.

Meeko
https://github.com/meekotharaccoon-cell/meeko-nerve-center
"""
})

# — 4. Tech press ————————————————————————————————————————————
for outlet, email, editor in [
    ('404 Media',    'tips@404media.co',       '404 Media team'),
    ('Wired',        'wired@condenast.com',    'Wired editorial team'),
    ('Rest of World','tips@restofworld.org',   'Rest of World team'),
]:
    EMAILS.append({
        'category': 'press',
        'priority': 'medium',
        'to': email,
        'subject': f'Story tip: Self-healing autonomous AI raises money for Gaza at $0/month',
        'body': f"""\
Hello {editor},

I wanted to flag a project that might make an interesting story for {outlet}.

I’ve built a fully autonomous AI system that:
• Runs at zero cost (GitHub Actions + GitHub Pages, no servers)
• Teaches itself daily from public internet sources
• Repairs its own broken code when it encounters errors
• Raises money for Gaza, Sudan, and Congo

The whole thing is open source, every decision is logged publicly, and
anyone can fork it and aim it at any cause.

Repo: https://github.com/meekotharaccoon-cell/meeko-nerve-center
Live gallery: https://meekotharaccoon-cell.github.io/gaza-rose-gallery
System dashboard: https://meekotharaccoon-cell.github.io/meeko-nerve-center/dashboard.html

I think the combination of zero-cost autonomous AI + humanitarian mission +
self-healing architecture is genuinely novel. Happy to do an interview or
provide more technical detail.

Best,
Meeko
"""
    })

# — 5. Self-hosted community post (for forum/Discord outreach) ————————
EMAILS.append({
    'category': 'community',
    'priority': 'medium',
    'to': '[paste your community link / Discord / forum post]',
    'subject': 'Built a self-healing autonomous AI system at $0/month — full source on GitHub',
    'body': """\
Hey everyone,

I wanted to share something I’ve been building. It’s an autonomous AI
system that runs entirely on GitHub Actions + GitHub Pages at zero cost.

What makes it interesting architecturally:
• Daily knowledge harvesting from GitHub API, Wikipedia, arXiv, HackerNews
• A strategy brain that reads engagement signals and adjusts what it does
  next (uses local Ollama when available, rule-based fallback in the cloud)
• Self-healing: a workflow monitors all other workflows, diagnoses failures,
  applies fixes automatically, and writes plain-English repair instructions
  for anything it can’t fix itself
• Everything is plain Python stdlib + requests — no frameworks

The mission is humanitarian — it raises funds for Gaza, Congo, and Sudan.
But the architecture is fully generic and forkable for any cause.

Full source (AGPL-3.0): https://github.com/meekotharaccoon-cell/meeko-nerve-center

Happy to answer questions about how any of it works.
"""
})

# — 6. Fix-specific emails (if open issues exist) —————————————————
if open_issues > 0:
    needs_human = heal_report.get('needs_human_list', [])
    for issue in needs_human[:3]:
        cat  = issue.get('category', 'unknown')
        diag = issue.get('diagnosis', '?')
        fix  = issue.get('fallback', '?')
        wf   = issue.get('workflow', '?')
        url  = issue.get('url', 'https://github.com/meekotharaccoon-cell/meeko-nerve-center/actions')

        if cat == 'secret':
            # These don’t need emails, just the GitHub Secrets page
            EMAILS.append({
                'category': 'self_fix',
                'priority': 'high',
                'to': '[no email needed — this is a self-action]',
                'subject': f'ACTION NEEDED: Add missing secret to unlock {wf}',
                'body': f"""\
This is not an email to send — it’s a reminder for you:

ISSUE: {diag}
WORKFLOW: {wf}

FIX:
{fix}

Go to: https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions

Once added, trigger the workflow manually from:
{url}

No email needed. Just the GitHub Secrets page.
"""
            })

# ── Write DRAFT_EMAILS.md ────────────────────────────────────────────────────
lines = [
    f'# ✉️ Draft Emails — {TODAY}',
    f'*Auto-generated by email_drafter.py · {len(EMAILS)} emails ready*',
    '',
    '**Instructions:** Copy each email, open your email client, paste, review, send.',
    'Each one is ready to go. Edit anything you want first.',
    '',
    f'> **System today:** Primary crisis = {primary} | '
    f'Auto-healed = {healed_total} | Open issues = {open_issues}',
    '',
    '---',
    '',
]

priority_order = {'high': 0, 'medium': 1, 'low': 2}
for i, email in enumerate(sorted(EMAILS, key=lambda x: priority_order.get(x['priority'], 9)), 1):
    cat   = email['category'].replace('_', ' ').upper()
    pri   = email['priority'].upper()
    lines += [
        f'## Email {i} — [{cat}] [{pri} PRIORITY]',
        '',
        f'**To:** `{email["to"]}`',
        f'**Subject:** `{email["subject"]}`',
        '',
        '**Body:**',
        '```',
        email['body'].strip(),
        '```',
        '',
        '---',
        '',
    ]

lines += [
    f'*{len(EMAILS)} emails drafted. Send the HIGH PRIORITY ones first.*',
    f'*Regenerated daily. Next update tomorrow morning.*',
]

(ROOT / 'DRAFT_EMAILS.md').write_text('\n'.join(lines), encoding='utf-8')

# ── Write JSON for dashboard ───────────────────────────────────────────────────
(DATA / 'draft_emails.json').write_text(
    json.dumps({'generated': TODAY, 'count': len(EMAILS),
                'emails': [{k: v for k, v in e.items() if k != 'body'}
                           for e in EMAILS]}, indent=2),
    encoding='utf-8'
)

print(f'\u2713 {len(EMAILS)} draft emails written to DRAFT_EMAILS.md')
for e in EMAILS:
    print(f'  [{e["priority"].upper()}] {e["category"]} → {e["to"][:45]}')
