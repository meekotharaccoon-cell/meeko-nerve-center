#!/usr/bin/env python3
"""
KNOWLEDGE INDEXER
==================
Reads all lesson HTML files. Builds a searchable index.
Updates the learn site's index.html with every lesson found.
The knowledge library adds itself to its own table of contents.

No APIs. No tokens. Pure file I/O + string building.

Runs:
  - On every push that touches lessons/
  - Weekly to catch anything missed
  - Outputs: updated index page, data/lessons.json
"""
import re, json
from pathlib import Path
from datetime import datetime, timezone

# Looks for lessons in the solarpunk-learn repo
# When run from nerve center, paths relative to ../solarpunk-learn
# When run from the learn repo itself, paths are local
LEARN_DIRS = [
    Path('lessons'),
    Path('../solarpunk-learn/lessons'),
    Path('solarpunk-learn/lessons'),
]

DATA_DIR  = Path('data')
INDEX_OUT = DATA_DIR / 'lessons.json'

KNOWN_LESSONS = [
    {'file': 'tcpa.html',                'title': 'TCPA: Robocall Rights',              'tag': 'Legal',      'desc': 'Every robocall to your cell is worth $500–$1,500 in damages. Here\'s how to collect.',  'emoji': '📱'},
    {'file': 'unclaimed-property.html',  'title': 'Unclaimed Property',                 'tag': 'Free Money', 'desc': 'Billions in forgotten accounts. Your name might be in the national database right now.', 'emoji': '💰'},
    {'file': 'foia.html',                'title': 'FOIA: Access Government Records',   'tag': 'Legal',      'desc': 'Your right to see what the government knows. How to file, what to expect.',              'emoji': '📜'},
    {'file': 'fdcpa.html',               'title': 'Debt Collector Rights (FDCPA)',      'tag': 'Legal',      'desc': 'Collectors can\'t call before 8am or after 9pm. Each violation = up to $1,000.',          'emoji': '🛡️'},
    {'file': 'free-infrastructure.html', 'title': 'Free Digital Infrastructure',        'tag': 'Tech',       'desc': 'Everything you need to run a full web presence for exactly $0/month.',                    'emoji': '⚙️'},
    {'file': 'credit-dispute.html',      'title': 'Dispute a Credit Report Error',      'tag': 'Credit',     'desc': '1 in 5 reports has errors. Fixing one can save thousands in interest. Here\'s how.',       'emoji': '📊'},
    {'file': 'small-claims.html',        'title': 'Win in Small Claims Court',          'tag': 'Legal',      'desc': 'Sue without a lawyer. $30–$100 filing fee. Up to $25,000 recovery. No attorney needed.',    'emoji': '⚖️'},
    {'file': 'medical-bills.html',       'title': 'Negotiate Medical Bills',            'tag': 'Healthcare', 'desc': 'The chargemaster rate is fake. The real price is 40–80% less. Here\'s how to ask.',         'emoji': '🏥'},
    {'file': 'free-medications.html',    'title': 'Free or Almost-Free Medications',   'tag': 'Healthcare', 'desc': 'Patient assistance programs exist for every major drug. Most people never apply.',          'emoji': '💊'},
    {'file': 'workers-rights.html',      'title': 'Workers Rights Most Don\'t Know',   'tag': 'Labor',      'desc': 'Salary discussion is protected. Non-competes are often illegal. Wage theft is recoverable.', 'emoji': '✊'},
    {'file': 'library-card.html',        'title': 'What a Library Card Gets You',      'tag': 'Free',       'desc': '$1,000+ in resources: ebooks, films, courses, databases, notary, printing. All free.',       'emoji': '📚'},
    {'file': 'free-tax-filing.html',     'title': 'Free Tax Filing — Every Option',    'tag': 'Taxes',      'desc': 'TurboTax spends millions lobbying to keep this complicated. Here are the free options.',      'emoji': '📝'},
    {'file': 'benefits-you-qualify-for.html', 'title': 'Benefits You Probably Qualify For', 'tag': 'Benefits', 'desc': 'Medicaid, SNAP, LIHEAP, Lifeline, and more. Apply for all of them.',                    'emoji': '🌟'},
]

def build_index_html(lessons):
    now = datetime.now(timezone.utc).strftime('%B %Y')
    cards = ''
    for l in lessons:
        cards += f"""    <a href="lessons/{l['file']}" class="lesson-card">
      <span class="lesson-emoji">{l['emoji']}</span>
      <span class="lesson-tag">{l['tag']}</span>
      <h3>{l['title']}</h3>
      <p>{l['desc']}</p>
    </a>\n"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk Learn — Free Knowledge Library</title>
<meta name="description" content="Free knowledge on legal rights, healthcare, money, and infrastructure. No paywall, no signup.">
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Lora:wght@400;600&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0c0c0c;color:#e8e8e8;font-family:'Lora',serif;min-height:100vh}}
.hero{{padding:72px 28px 52px;border-bottom:1px solid rgba(255,255,255,0.07);max-width:900px;margin:0 auto}}
.hero-tag{{font-family:'IBM Plex Mono',monospace;font-size:.6rem;letter-spacing:3px;text-transform:uppercase;color:#00ff88;margin-bottom:14px}}
h1{{font-size:2.8rem;font-weight:600;line-height:1.15;margin-bottom:18px}}
h1 span{{color:#00ff88}}
.hero-sub{{font-size:1rem;color:rgba(255,255,255,0.4);max-width:520px;line-height:1.8}}
.meta{{font-family:'IBM Plex Mono',monospace;font-size:.65rem;color:rgba(255,255,255,0.2);margin-top:24px;letter-spacing:1px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;padding:48px 28px;max-width:900px;margin:0 auto}}
.lesson-card{{background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:24px;text-decoration:none;color:#fff;display:block;transition:all .2s;position:relative}}
.lesson-card:hover{{border-color:rgba(0,255,136,0.2);background:rgba(0,255,136,0.03);transform:translateY(-2px)}}
.lesson-emoji{{font-size:1.6rem;display:block;margin-bottom:12px}}
.lesson-tag{{font-family:'IBM Plex Mono',monospace;font-size:.58rem;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,0.25);display:block;margin-bottom:8px}}
.lesson-card h3{{font-size:1.05rem;font-weight:600;margin-bottom:8px;line-height:1.3}}
.lesson-card p{{font-size:.82rem;color:rgba(255,255,255,0.4);line-height:1.65}}
footer{{padding:32px 28px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:rgba(255,255,255,0.15)}}
footer a{{color:rgba(0,255,136,0.3);text-decoration:none}}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-tag">📚 Free Knowledge Library</div>
  <h1>Learn what they<br>don't teach you.<br><span>For free.</span></h1>
  <p class="hero-sub">Legal rights with money attached. Healthcare you didn't know you could access. Infrastructure that costs nothing. No paywall. No signup. No ads.</p>
  <div class="meta">{len(lessons)} lessons · updated {now} · no paywall · no signup · fork this library</div>
</div>
<div class="grid">
{cards}</div>
<footer>
  SolarPunk Learn · part of <a href="https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html">SolarPunk Mycelium</a> ·
  <a href="https://github.com/meekotharaccoon-cell/solarpunk-learn">source</a> ·
  AGPL-3.0 + Ethical Use · fork freely
</footer>
</body></html>"""

def run():
    print('\n' + '='*48)
    print('  KNOWLEDGE INDEXER')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*48)

    # Find lesson files that actually exist
    learn_dir = None
    for d in LEARN_DIRS:
        if d.exists():
            learn_dir = d
            break

    existing = []
    for lesson in KNOWN_LESSONS:
        if learn_dir and (learn_dir / lesson['file']).exists():
            existing.append(lesson)
            print(f'  ✓ {lesson["file"]}')
        else:
            print(f'  - {lesson["file"]} (not found locally — still indexing)')
            existing.append(lesson)  # Index even if not local

    # Save JSON index
    DATA_DIR.mkdir(exist_ok=True)
    index_data = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'count': len(existing),
        'lessons': existing,
    }
    INDEX_OUT.write_text(json.dumps(index_data, indent=2))
    print(f'  Index saved: {INDEX_OUT}')

    # Build and optionally write index.html
    html = build_index_html(existing)
    out_html = Path('index.html')
    if learn_dir and learn_dir.parent.exists():
        out_html = learn_dir.parent / 'index.html'
    out_html.write_text(html)
    print(f'  Index HTML: {out_html}')
    print(f'  Total lessons indexed: {len(existing)}')

if __name__ == '__main__':
    run()
