#!/usr/bin/env python3
"""
Newsletter Writer
=================
Generates a weekly newsletter from the knowledge harvest + system activity.
Compatible with: Substack (free), Beehiiv (free), Ghost (free self-hosted).

Substack pays through:
  - Paid subscriptions (you set the price)
  - Substack Recommendations (free readers → discover you)

Output: content/newsletter/YYYY-WNN.md (weekly)
        content/newsletter/latest.md
"""

import json, datetime
from pathlib import Path

ROOT  = Path(__file__).parent.parent
KB    = ROOT / 'knowledge'
DATA  = ROOT / 'data'
OUT   = ROOT / 'content' / 'newsletter'
OUT.mkdir(parents=True, exist_ok=True)

TODAY   = datetime.date.today()
WEEK    = TODAY.strftime('%Y-W%W')
DATE_HR = TODAY.strftime('%B %d, %Y')

# Load what we have
digest = ''
dp = KB / 'LATEST_DIGEST.md'
if dp.exists():
    digest = dp.read_text(encoding='utf-8')[:1500]

what_works = {}
wp = DATA / 'what_works.json'
if wp.exists():
    try: what_works = json.loads(wp.read_text())
    except: pass

strategy = {}
sp = DATA / 'strategy.json'
if sp.exists():
    try: strategy = json.loads(sp.read_text())
    except: pass

total_views = what_works.get('summary', {}).get('total_14d_views', 0)
primary     = strategy.get('primary_crisis', 'Gaza')
recs        = strategy.get('recommendations', [])

newsletter = f"""# The Mycelium — Week of {DATE_HR}

*The weekly dispatch from an autonomous AI system built for humanitarian causes.*
*Free forever. Forward it. [Read online](https://meekotharaccoon-cell.github.io/meeko-nerve-center)*

---

## This week: {primary}

The system’s focus this week is {primary}. Here’s why that matters and what you can do.

**Gaza:** Over 40,000 killed. 2 million displaced. The [Palestine Children’s Relief Fund](https://www.pcrf.net) (4-star Charity Navigator) is one of the most effective ways to help. You can also [buy a $1 piece of original art](https://meekotharaccoon-cell.github.io/gaza-rose-gallery) — 70% goes directly to PCRF.

**Congo:** 7+ million displaced in Eastern DRC. Ongoing for 25 years. The [International Rescue Committee](https://www.rescue.org) is on the ground.

**Sudan:** 8+ million displaced — the largest displacement crisis in the world right now. [UNHCR Sudan](https://www.unhcr.org/sudan) needs support.

---

## What the system learned this week

Every day this system wakes up at 5am UTC and reads the open internet.
Here’s a sample of what it found:

{chr(10).join(['> ' + l.strip().lstrip('- ') for l in digest.split(chr(10)) if l.strip().startswith('-')][:6])}

---

## How the system works (for the curious)

This newsletter is written by an autonomous AI system that:
- Costs $0/month to run (GitHub Actions + GitHub Pages)
- Teaches itself daily from free public APIs
- Fixes its own broken code when errors occur
- Adjusts its strategy based on what’s actually working

Everything is open source: [github.com/meekotharaccoon-cell/meeko-nerve-center](https://github.com/meekotharaccoon-cell/meeko-nerve-center)

Fork it. Aim it at your cause.

---

## One action you can take right now

🎨 **Buy a $1 piece of original art.** 70% goes to PCRF for Gaza.
[meekotharaccoon-cell.github.io/gaza-rose-gallery](https://meekotharaccoon-cell.github.io/gaza-rose-gallery)

🔗 **Share this newsletter.** Every new reader = more reach = more impact.

🌱 **Fork the system.** Build your own autonomous AI for your cause:
[Fork guide — $5](https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/products/fork-guide.md)

---

*Built in public. Every commit visible.*
*[Unsubscribe](mailto:meekotharaccoon@gmail.com?subject=unsubscribe) anytime.*
"""

(OUT / f'{WEEK}.md').write_text(newsletter, encoding='utf-8')
(OUT / 'latest.md').write_text(newsletter, encoding='utf-8')
print(f'✓ Newsletter written to content/newsletter/latest.md')
print(f'  Post this to Substack (free): substack.com')
print(f'  Or Beehiiv (free): beehiiv.com')
