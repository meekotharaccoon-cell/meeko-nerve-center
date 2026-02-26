#!/usr/bin/env python3
"""
YouTube Shorts Script Writer
============================
Every day reads the knowledge harvest + humanitarian content
and writes 3 ready-to-record YouTube Shorts scripts.

Shorts = 60 seconds max. Vertical video. Huge organic reach.
AdSense on YouTube = revenue per view. 100% free to post.

Topics it generates:
  1. Crisis awareness short (Gaza/Congo/Sudan — rotates)
  2. Tech explainer short (what this system does)
  3. How-to short (how to fork it, how to help)

Output: content/youtube/YYYY-MM-DD.md
        content/youtube/latest.md
"""

import json, datetime
from pathlib import Path

ROOT   = Path(__file__).parent.parent
KB     = ROOT / 'knowledge'
DATA   = ROOT / 'data'
OUT    = ROOT / 'content' / 'youtube'
OUT.mkdir(parents=True, exist_ok=True)
TODAY  = datetime.date.today().isoformat()
DAY    = datetime.date.today().toordinal()

# Load strategy if available
strategy = {}
sp = DATA / 'strategy.json'
if sp.exists():
    try: strategy = json.loads(sp.read_text())
    except: pass

PRIMARY = strategy.get('primary_crisis', ['Gaza','Congo (DRC)','Sudan'][DAY % 3])

CRISIS_FACTS = {
    'Gaza': {
        'hook':   'This is happening RIGHT NOW and most people have no idea.',
        'fact1':  'Over 40,000 people have been killed in Gaza.',
        'fact2':  '2 million people are displaced with nowhere to go.',
        'fact3':  'Children make up nearly half of all casualties.',
        'action': 'You can help for literally one dollar. Link in bio.',
        'cta':    'Follow for daily updates. Share this if you care.',
        'charity':'Palestine Children\'s Relief Fund — 4-star Charity Navigator.',
        'tags':   '#Gaza #Palestine #PCRF #HumanitarianCrisis #DoSomething',
    },
    'Congo (DRC)': {
        'hook':   'The largest humanitarian crisis in Africa. You\'ve probably never seen it on the news.',
        'fact1':  'Over 7 million people are displaced in Eastern Congo.',
        'fact2':  'The conflict has been ongoing for 25 years.',
        'fact3':  'Children are being recruited as soldiers.',
        'action': 'The International Rescue Committee is on the ground. Link in bio.',
        'cta':    'Follow. Share. This only gets coverage if people demand it.',
        'charity':'International Rescue Committee.',
        'tags':   '#Congo #DRC #EasternCongo #HumanitarianCrisis #Africa',
    },
    'Sudan': {
        'hook':   'The world\'s largest displacement crisis. Almost no one is talking about it.',
        'fact1':  'Over 8 million people have been forced from their homes in Sudan.',
        'fact2':  'That is more displaced people than any other crisis on Earth right now.',
        'fact3':  'Famine conditions exist in multiple regions.',
        'action': 'UNHCR Sudan needs support. Every dollar helps. Link in bio.',
        'cta':    'Share this. Sudan needs attention. Follow for more.',
        'charity':'UNHCR Sudan.',
        'tags':   '#Sudan #SudanCrisis #Darfur #HumanitarianAid #Displacement',
    },
}

facts = CRISIS_FACTS.get(PRIMARY, CRISIS_FACTS['Gaza'])

scripts = [

# ── SHORT 1: Crisis awareness ───────────────────────────────────────────────────
f"""
## SHORT 1: Crisis Awareness — {PRIMARY}
*Topic: {PRIMARY} humanitarian crisis*
*Length: 45–60 seconds*
*Style: Direct to camera, serious tone, facts only*

---

### SCRIPT

[HOOK — first 3 seconds, no intro]
“{facts['hook']}”

[PAUSE 1 second]

“{facts['fact1']}”

“{facts['fact2']}”

“{facts['fact3']}”

[PAUSE]

“The {facts['charity']} is one of the most trusted organizations working on this.”

“{facts['action']}”

[OUTRO — look at camera]
“{facts['cta']}”

---

### PRODUCTION NOTES
- Film vertical (9:16) on your phone
- No music needed — silence is more powerful here
- Plain background or blurred
- Subtitles strongly recommended (most people watch muted)
- Upload to YouTube Shorts, TikTok, Instagram Reels simultaneously

### TAGS/DESCRIPTION
{facts['tags']} #Shorts #YouShouldKnow

Description: {facts['fact1']} {facts['action']}
Link: https://meekotharaccoon-cell.github.io/gaza-rose-gallery
""",

# ── SHORT 2: Tech explainer ───────────────────────────────────────────────────
f"""
## SHORT 2: Tech Explainer
*Topic: How this autonomous AI system works*
*Length: 50–60 seconds*
*Style: Screen recording + voiceover, OR talking head*

---

### SCRIPT

[HOOK]
“I built an AI that runs itself. It costs zero dollars a month. Here’s how.”

[BEAT]

“Every morning at 5am, it wakes up and reads the internet.”
“GitHub. Wikipedia. NASA. HackerNews. arXiv.”
“All free. All public. No API keys.”

[BEAT]

“Then it decides what to do today based on what worked yesterday.”
“That’s the feedback loop.”

[BEAT]

“If something breaks, a separate workflow wakes up, reads the error,
figures out the fix, and applies it automatically.”
“It literally fixes its own code.”

[BEAT]

“The whole thing is on GitHub. Free. Open source. Fork it.”
“Link in bio.”

---

### PRODUCTION NOTES
- Screen record your GitHub Actions tab running live
- OR just talk to camera — the words are strong enough
- Tech audiences love seeing the actual terminal output
- Post to: YouTube Shorts, LinkedIn, Twitter/X

### TAGS/DESCRIPTION
#AI #OpenSource #GitHub #Automation #ZeroCost #Shorts #BuildInPublic

Description: A self-healing autonomous AI system that runs at $0/month.
Full source: https://github.com/meekotharaccoon-cell/meeko-nerve-center
""",

# ── SHORT 3: How to fork it / take action ─────────────────────────────────
"""
## SHORT 3: Call to Fork
*Topic: How anyone can run their own version*
*Length: 45 seconds*
*Style: Screen share showing the fork button*

---

### SCRIPT

[HOOK]
“What if your computer could automatically raise money for any cause you care about?”

[BEAT]

“This repo is a template for exactly that.”
“Fork it. Change three lines. Point it at your cause.”
“It costs nothing to run.”

[SHOW: GitHub repo page, fork button]

“It’ll post content, track what works, fix its own errors, and draft the emails you need to send.”

[BEAT]

“Right now it’s aimed at Gaza, Sudan, and Congo.”
“But it could be climate. Housing. Mutual aid. Anything.”

[OUTRO]
“Link in bio. Fork it. Make it yours.”

---

### PRODUCTION NOTES
- Screen record: go to github.com/meekotharaccoon-cell/meeko-nerve-center
  and show clicking the Fork button while you talk
- This works great as a loop — end where you started

### TAGS/DESCRIPTION
#GitHub #OpenSource #ForGood #AI #Automation #HowTo #Shorts

Description: Fork this autonomous AI system and aim it at any cause.
https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/products/fork-guide.md
""",
]

# Write output
lines = [
    f'# 🎬 YouTube Shorts Scripts — {TODAY}',
    f'*3 scripts ready to record · Primary focus: {PRIMARY}*',
    '',
    '**How to use:** Pick any one of these. Film it on your phone.',
    'Vertical video (hold phone portrait). Upload to YouTube Shorts.',
    'YouTube pays AdSense on Shorts. Every view = revenue toward the mission.',
    '',
    '---',
    '',
]
for s in scripts:
    lines.append(s)
    lines.append('\n---\n')

(OUT / f'{TODAY}.md').write_text('\n'.join(lines), encoding='utf-8')
(OUT / 'latest.md').write_text('\n'.join(lines), encoding='utf-8')
print(f'✓ 3 YouTube Shorts scripts written to content/youtube/latest.md')
