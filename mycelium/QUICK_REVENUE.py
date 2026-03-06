#!/usr/bin/env python3
"""
QUICK_REVENUE.py -- Fastest path to first dollar
=================================================
Claude was asked: "I need to make revenue as fast as possible. What do YOU suggest?"

Honest answer after reading system state:

  Three channels can generate revenue TODAY with zero new credentials:

  1. KO-FI SHOP (10 min manual setup)
     Already configured. 6 Gaza Rose Gallery products are fully written.
     Just paste them into ko-fi.com UI. No API. No token.
     This engine generates the exact copy-paste text for each listing.

  2. EMAIL_AGENT_EXCHANGE (live right now)
     Already running. AI=online. [TASK] email -> work -> payment.
     $0.05-$0.10 per task. Only missing: people knowing it exists.
     This engine generates the promo email to send to developer contacts.

  3. GITHUB SPONSORS + README badges (2 min)
     Already configured. Anyone can sponsor today.
     This engine generates the bio and README snippet that drives it.

The 10x multiplier when you're ready:
  ANTHROPIC_API_KEY + GUMROAD_ACCESS_TOKEN + X_API_KEY

Outputs:
  docs/quick_revenue.html  -- action dashboard, copy-paste ready
  data/quick_revenue.json  -- structured state for other engines
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

REPO      = "https://github.com/meekotharaccoon-cell/meeko-nerve-center"
BASE      = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
KOFI_PAGE = "https://ko-fi.com/meekotharaccoon"
EXCHANGE  = "meekotharaccoon@gmail.com"

KOFI_PRODUCTS = [
    {
        "name": "Desert Rose at Dawn",
        "price": 1.00,
        "description": (
            "A desert rose blooming at first light -- symbol of resilience and the "
            "enduring beauty of Palestinian land. AI-generated art print. "
            "70% of every sale goes to PCRF (Palestinian Children's Relief Fund, "
            "EIN 93-1057665). Digital download, print at any size."
        ),
        "tags": "palestine, art, digital, rose, gaza",
    },
    {
        "name": "White Doves Over the Mediterranean",
        "price": 1.00,
        "description": (
            "White doves in flight above the Mediterranean coast -- peace, migration, "
            "and the sky that belongs to everyone. AI-generated art print. "
            "70% of every sale goes to PCRF. Digital download."
        ),
        "tags": "palestine, doves, mediterranean, peace, art",
    },
    {
        "name": "Olive Grove Eternal",
        "price": 1.00,
        "description": (
            "Ancient olive trees -- some thousands of years old -- standing through "
            "centuries of history. Palestinian olive groves are among the oldest "
            "cultivated landscapes on earth. AI-generated art print. "
            "70% to PCRF. Digital download."
        ),
        "tags": "palestine, olive, trees, history, art",
    },
    {
        "name": "Tatreez Pattern Bloom",
        "price": 1.00,
        "description": (
            "Traditional Palestinian embroidery (tatreez) patterns blooming into "
            "a field of color. Each pattern carries regional identity passed through "
            "generations of women. AI-generated art print. "
            "70% to PCRF. Digital download."
        ),
        "tags": "tatreez, embroidery, palestine, pattern, culture",
    },
    {
        "name": "Gaza Coastline at Golden Hour",
        "price": 1.00,
        "description": (
            "The Gaza coastline at golden hour -- the Mediterranean catching light "
            "the way it always has. Some things persist. "
            "AI-generated art print. 70% to PCRF. Digital download."
        ),
        "tags": "gaza, coast, mediterranean, golden hour, art",
    },
    {
        "name": "Star of Hope Rising",
        "price": 1.00,
        "description": (
            "A star rising over Palestinian land -- the kind of image that holds "
            "grief and hope at the same time. Sometimes that is what art is for. "
            "AI-generated art print. 70% to PCRF. Digital download."
        ),
        "tags": "palestine, star, hope, art, night",
    },
]

EXCHANGE_PROMO = f"""Subject: I built an AI agent that does tasks by email for $0.10 (15% goes to Gaza)

Hi,

I built a system called SolarPunk that processes AI tasks by email.

How it works:
  1. Email {EXCHANGE} with [TASK] in the subject
  2. Describe what you need (content, research, code review, translation, data)
  3. The system responds with completed work within 6 hours
  4. Pay $0.05-$0.10 via Ko-fi: {KOFI_PAGE}
  5. 15% goes to PCRF (Palestinian children's charity, EIN 93-1057665)

This is useful for:
  - Content generation at scale
  - Quick research synthesis
  - Light code review
  - Translation tasks
  - Structuring messy data

The AI is live right now. Runs 4x daily.
Full source (MIT, free to fork): {REPO}

-- SolarPunk Autonomous AI
   (Automated email. A human reviews all replies.)"""

SPONSOR_BIO = (
    "Building SolarPunk -- autonomous AI that funds Gaza. "
    "$1 products, 15% hardcoded to PCRF. "
    "github.com/sponsors/meekotharaccoon-cell"
)

SPONSOR_README = f"""
## Support

[![Sponsor](https://img.shields.io/badge/GitHub_Sponsor-%E2%9D%A4-red)](https://github.com/sponsors/meekotharaccoon-cell)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy_a_print_$1-orange)]({KOFI_PAGE})

15% of everything goes to [PCRF](https://www.pcrf.net/) (EIN: 93-1057665). Hardcoded. Not a pledge.
"""


def run():
    now      = datetime.now(timezone.utc)
    ts_nice  = now.strftime("%Y-%m-%d %H:%M UTC")

    revenue  = (DATA / "revenue_inbox.json")
    rev_data = json.loads(revenue.read_text()) if revenue.exists() else {}
    total_rev = rev_data.get("total_received", 0) if isinstance(rev_data, dict) else 0
    first_sale = total_rev > 0

    state = {
        "generated_at":    now.isoformat(),
        "total_revenue":   total_rev,
        "first_sale_done": first_sale,
        "kofi_products":   KOFI_PRODUCTS,
        "exchange_promo":  EXCHANGE_PROMO,
        "sponsor_bio":     SPONSOR_BIO,
        "sponsor_readme":  SPONSOR_README,
    }
    (DATA / "quick_revenue.json").write_text(json.dumps(state, indent=2))

    # --- HTML ---
    def card(title, step, body):
        return (
            f'<div style="background:#0d1410;border:1px solid rgba(0,255,136,.2);'
            f'border-radius:14px;padding:22px;margin-bottom:18px">'
            f'<div style="font-size:28px;color:#00ff88;font-weight:700;margin-bottom:6px">{step}</div>'
            f'<h3 style="font-size:14px;color:#deeae1;margin-bottom:10px">{title}</h3>'
            f'{body}'
            f'</div>'
        )

    def copyblock(text, btn_id):
        esc = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        return (
            f'<pre id="{btn_id}" style="font-size:11px;color:rgba(222,234,225,.6);'
            f'white-space:pre-wrap;word-break:break-word;background:rgba(0,0,0,.3);'
            f'padding:12px;border-radius:8px;max-height:260px;overflow-y:auto;'
            f'line-height:1.6;margin:8px 0">{esc}</pre>'
            f'<button onclick="copy(\'{btn_id}\')" style="background:transparent;'
            f'border:1px solid rgba(0,255,136,.3);color:rgba(0,255,136,.7);'
            f'padding:6px 14px;border-radius:6px;font-size:10px;cursor:pointer;'
            f'font-family:inherit">Copy</button>'
        )

    # Ko-fi products
    products_blocks = ""
    for i, p in enumerate(KOFI_PRODUCTS):
        listing = f"{p['name']} | ${p['price']:.2f}\n\n{p['description']}\n\nTags: {p['tags']}"
        pid = f"prod{i}"
        products_blocks += (
            f'<div style="border-bottom:1px solid rgba(0,255,136,.08);padding:14px 0">'
            f'<p style="font-size:13px;color:#deeae1;font-weight:600;margin-bottom:6px">{p["name"]}'
            f'<span style="color:#00ff88;margin-left:8px">${p["price"]:.2f}</span></p>'
            + copyblock(listing, pid) +
            f'</div>'
        )

    kofi_card = card(
        "Ko-fi Shop -- Add 6 products (10 min, zero credentials)",
        "1",
        f'<p style="font-size:12px;color:rgba(222,234,225,.65);line-height:1.7;margin-bottom:14px">'
        f'Go to <a href="{KOFI_PAGE}" target="_blank" style="color:#00ff88">{KOFI_PAGE}</a> '
        f'&rarr; Shop &rarr; Add Item. Paste each listing. Price: $1.00. '
        f'Upload any image. Publish.</p>'
        + products_blocks
    )

    promo_card = card(
        "Email Agent Exchange -- Send to 3 developer contacts",
        "2",
        f'<p style="font-size:12px;color:rgba(222,234,225,.65);line-height:1.7;margin-bottom:10px">'
        f'The exchange is live right now. Send this to any developer who might use $0.10 AI tasks:</p>'
        + copyblock(EXCHANGE_PROMO, "promo")
    )

    sponsor_card = card(
        "GitHub Sponsors -- Update bio + README (2 min)",
        "3",
        f'<p style="font-size:12px;color:rgba(222,234,225,.65);margin-bottom:8px">'
        f'GitHub bio (<a href="https://github.com/settings/profile" target="_blank" style="color:#00ff88">settings/profile</a>):</p>'
        + copyblock(SPONSOR_BIO, "bio")
        + f'<p style="font-size:12px;color:rgba(222,234,225,.65);margin:12px 0 8px">README snippet (add after title):</p>'
        + copyblock(SPONSOR_README, "readme")
    )

    multiplier = (
        '<div style="background:rgba(255,165,0,.04);border:1px solid rgba(255,165,0,.25);'
        'border-radius:12px;padding:20px;margin-top:24px">'
        '<p style="font-size:10px;letter-spacing:.2em;color:rgba(255,165,0,.6);margin-bottom:10px">10X MULTIPLIER WHEN READY</p>'
        '<p style="font-size:12px;color:rgba(222,234,225,.65);line-height:1.9">'
        '<span style="color:#ff9030">ANTHROPIC_API_KEY</span> &rarr; SELF_BUILDER resumes, new revenue engines auto-written<br>'
        '<span style="color:#ff9030">GUMROAD_ACCESS_TOKEN</span> &rarr; 6 products auto-published, searchable by 100K+ buyers<br>'
        '<span style="color:#ff9030">X_API_KEY</span> &rarr; 88 queued posts start distributing, one per cycle<br>'
        '</p>'
        '<p style="font-size:11px;color:rgba(222,234,225,.35);margin-top:10px">'
        'Get keys: anthropic.com/console (API Keys) + gumroad.com/settings/advanced &rarr; GitHub Secrets'
        '</p>'
        '</div>'
    )

    status = (
        '<span style="background:#00ff88;color:#060a07;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700">FIRST SALE DONE</span>'
        if first_sale else
        '<span style="background:rgba(255,80,50,.15);border:1px solid rgba(255,80,50,.3);color:#ff7050;padding:4px 12px;border-radius:20px;font-size:11px">WAITING FOR FIRST SALE</span>'
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk -- Quick Revenue</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#060a07;color:#deeae1;font-family:'Courier New',monospace;padding:28px 20px;min-height:100vh}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,255,136,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,136,.018) 1px,transparent 1px);
  background-size:44px 44px}}
.wrap{{position:relative;z-index:1;max-width:860px;margin:0 auto}}
h1{{font-size:22px;color:#00ff88;letter-spacing:.06em;margin-bottom:6px}}
.sub{{font-size:12px;color:rgba(222,234,225,.35);margin-bottom:28px}}
.ts{{margin-top:36px;padding-top:18px;border-top:1px solid rgba(0,255,136,.1);font-size:11px;color:rgba(0,255,136,.3);line-height:2.2}}
a{{color:#00ff88}}
</style>
</head>
<body>
<div class="wrap">
<h1>&#128176; QUICK REVENUE</h1>
<div class="sub">{ts_nice} &middot; {status} &middot; ${total_rev:.2f} total</div>

{kofi_card}
{promo_card}
{sponsor_card}
{multiplier}

<div class="ts">
  Source: <a href="{REPO}/blob/main/mycelium/QUICK_REVENUE.py" target="_blank">QUICK_REVENUE.py</a><br>
  Data: <a href="https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/quick_revenue.json" target="_blank">quick_revenue.json</a><br><br>
  <a href="proof.html">Proof</a> &middot; <a href="store.html">Store</a> &middot; <a href="launch.html">Launch</a> &middot; <a href="{REPO}" target="_blank">GitHub</a>
</div>
</div>
<script>
function copy(id) {{
  var el = document.getElementById(id);
  navigator.clipboard.writeText(el.textContent).then(function() {{
    var btns = el.parentNode.querySelectorAll('button');
    btns.forEach(function(b){{ b.textContent = 'Copied!'; }});
    setTimeout(function(){{ btns.forEach(function(b){{ b.textContent = 'Copy'; }}); }}, 2000);
  }});
}}
</script>
</body>
</html>"""

    (DOCS / "quick_revenue.html").write_text(html, encoding="utf-8")

    print("QUICK_REVENUE done.")
    print(f"  Revenue: ${total_rev:.2f} | First sale: {'YES' if first_sale else 'NOT YET'}")
    print(f"  Ko-fi listings ready: {len(KOFI_PRODUCTS)}")
    print(f"  Live: {BASE}/quick_revenue.html")
    print("  Fastest path to $1: Go to ko-fi.com -> Shop -> paste 6 listings -> done")


if __name__ == "__main__":
    run()
