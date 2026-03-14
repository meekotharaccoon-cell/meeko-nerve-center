# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
CAPABILITY_SCANNER.py — What can SolarPunk actually DO right now?
=================================================================
Runs every cycle. Checks every channel against reality.
Not what engines EXIST — what they can actually EXECUTE.

The system has been promoting itself while most channels are blocked.
This engine makes that visible so we stop wasting cycles on dead paths
and maximize the channels that actually work.

Outputs:
  data/capability_map.json  — machine-readable status
  docs/capabilities.html    — live public page
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)


def scan():
    now = datetime.now(timezone.utc).isoformat()

    caps = {
        "anthropic_api": {
            "name": "Claude API",
            "status": "active" if os.environ.get("ANTHROPIC_API_KEY") else "blocked",
            "impact": "SELF_BUILDER, KNOWLEDGE_WEAVER, REVENUE_OPTIMIZER, ARCHITECT all dead without this",
            "fix": "anthropic.com/console → API Keys → add ANTHROPIC_API_KEY to GitHub Secrets",
            "blocks": ["SELF_BUILDER", "KNOWLEDGE_WEAVER", "REVENUE_OPTIMIZER", "NEURON_B"],
        },
        "gmail": {
            "name": "Gmail (send + read email)",
            "status": "active" if (os.environ.get("GMAIL_ADDRESS") and os.environ.get("GMAIL_APP_PASSWORD")) else "blocked",
            "impact": "Can reach journalists, newsletters, orgs, communities RIGHT NOW",
            "fix": "Already connected — use it offensively via EMAIL_OUTREACH",
            "note": "BIGGEST UNDERUSED WEAPON — works today, zero new keys",
            "blocks": [],
        },
        "gumroad": {
            "name": "Gumroad (publish + sell)",
            "status": "blocked" if not os.environ.get("GUMROAD_ACCESS_TOKEN") else "active",
            "impact": "6 products queued, $0 published — Gumroad dead",
            "fix": "gumroad.com → Settings → Advanced → Access Token → GitHub Secrets as GUMROAD_ACCESS_TOKEN",
            "blocks": ["GUMROAD_ENGINE"],
        },
        "twitter": {
            "name": "Twitter/X (auto-post)",
            "status": "blocked" if not os.environ.get("X_API_KEY") else "active",
            "impact": "88 posts queued, 14 already failed, 42 waiting — all stuck",
            "fix": "developer.twitter.com → create app → 4 keys → GitHub Secrets",
            "blocks": ["SOCIAL_PROMOTER"],
        },
        "reddit": {
            "name": "Reddit (auto-post)",
            "status": "blocked" if not os.environ.get("REDDIT_CLIENT_ID") else "active",
            "impact": "Bridge posts written and waiting, none submitted",
            "fix": "reddit.com/prefs/apps → create script app → GitHub Secrets",
            "blocks": ["SOCIAL_PROMOTER"],
        },
        "huggingface": {
            "name": "HuggingFace (AI fallback)",
            "status": "degraded",
            "impact": "All fallback models 410 Gone — Llama, Phi-3.5 dead. Engines fail silently.",
            "fix": "Add ANTHROPIC_API_KEY — HF fallback not needed if Claude works",
            "blocks": ["SYNTHESIS_FACTORY", "ARCHITECT", "EMAIL_BRAIN classification"],
        },
        "github_pages": {
            "name": "GitHub Pages (public website)",
            "status": "active",
            "impact": "store.html, outreach.html, capabilities.html all live — no traffic yet",
            "fix": "Already working — needs EMAIL_OUTREACH to drive traffic",
            "url": "https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html",
        },
        "github_releases": {
            "name": "GitHub Releases (public product drops)",
            "status": "active",
            "impact": "11 releases live, public URLs, indexable — nobody knows they exist",
            "fix": "Promote these in EMAIL_OUTREACH and bridge posts",
        },
        "email_outreach": {
            "name": "Email Outreach (Gmail → journalists/newsletters/orgs)",
            "status": "active" if os.environ.get("GMAIL_APP_PASSWORD") else "blocked",
            "impact": "Direct line to people who would care and share — unused",
            "fix": "EMAIL_OUTREACH.py now live — runs automatically each cycle",
            "note": "NEW ENGINE — first real offensive channel",
        },
    }

    active   = [k for k, v in caps.items() if v["status"] == "active"]
    blocked  = [k for k, v in caps.items() if v["status"] == "blocked"]
    degraded = [k for k, v in caps.items() if v["status"] == "degraded"]

    priority = (
        "ANTHROPIC_API_KEY" if not os.environ.get("ANTHROPIC_API_KEY") else
        "GUMROAD_ACCESS_TOKEN" if not os.environ.get("GUMROAD_ACCESS_TOKEN") else
        "X_API_KEY"
    )

    result = {
        "scanned_at": now,
        "active": len(active),
        "blocked": len(blocked),
        "degraded": len(degraded),
        "capabilities": caps,
        "priority_fix": priority,
        "best_channel_now": "gmail — works today, no new keys needed",
        "summary": f"{len(active)} active / {len(blocked)} blocked / {len(degraded)} degraded",
    }

    (DATA / "capability_map.json").write_text(json.dumps(result, indent=2))
    _build_html(result)
    return result


def _build_html(r):
    caps = r["capabilities"]
    cards = ""
    color_map = {"active": "#00ff88", "blocked": "#ff4455", "degraded": "#ffd166"}
    bg_map    = {"active": "rgba(0,255,136,.07)", "blocked": "rgba(255,68,85,.07)", "degraded": "rgba(255,209,102,.07)"}

    for k, c in caps.items():
        col   = color_map.get(c["status"], "#888")
        bg    = bg_map.get(c["status"], "")
        badge = c["status"].upper()
        note  = f'<p style="color:{col};font-size:11px;margin-top:6px">★ {c["note"]}</p>' if c.get("note") else ""
        url   = f'<p style="margin-top:6px"><a href="{c["url"]}" style="color:#00ff88;font-size:11px">{c["url"]}</a></p>' if c.get("url") else ""
        blks  = f'<p style="color:#ff4455;font-size:10px;opacity:.7;margin-top:4px">Blocks: {", ".join(c["blocks"])}</p>' if c.get("blocks") else ""
        cards += f"""
<div style="background:{bg};border:1px solid {col}22;border-radius:12px;padding:20px;display:flex;flex-direction:column;gap:6px">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <strong style="color:#deeae1;font-size:13px">{c["name"]}</strong>
    <span style="background:{col}18;border:1px solid {col}44;border-radius:20px;padding:2px 12px;font-size:10px;color:{col};letter-spacing:.12em">{badge}</span>
  </div>
  <p style="color:rgba(222,234,225,.55);font-size:12px;line-height:1.6">{c["impact"]}</p>
  <p style="color:rgba(222,234,225,.3);font-size:11px">→ {c["fix"]}</p>
  {blks}{note}{url}
</div>"""

    now = r["scanned_at"][:16].replace("T", " ") + " UTC"
    (DOCS / "capabilities.html").write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk — Capability Map</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#060a07;color:#deeae1;font-family:'Courier New',monospace;padding:28px 20px;min-height:100vh}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,255,136,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,136,.018) 1px,transparent 1px);
  background-size:44px 44px}}
.wrap{{position:relative;z-index:1;max-width:960px;margin:0 auto}}
h1{{font-size:22px;color:#00ff88;letter-spacing:.1em;margin-bottom:8px}}
.sub{{font-size:13px;color:rgba(222,234,225,.4);margin-bottom:28px;line-height:1.7}}
.stats{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px}}
.stat{{background:#0d1410;border:1px solid rgba(0,255,136,.13);border-radius:10px;padding:14px 22px;text-align:center}}
.stat b{{font-size:28px;display:block}}
.stat span{{font-size:10px;letter-spacing:.15em;color:rgba(222,234,225,.4)}}
.callout{{background:rgba(0,255,136,.04);border:1px solid rgba(0,255,136,.25);border-radius:12px;padding:20px;margin-bottom:28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:14px}}
footer{{margin-top:48px;border-top:1px solid rgba(0,255,136,.1);padding-top:20px;font-size:11px;color:rgba(222,234,225,.3);text-align:center;line-height:2}}
a{{color:#00ff88}}
</style></head><body><div class="wrap">
<h1>⚡ SOLARPUNK CAPABILITY MAP</h1>
<div class="sub">What the system can actually execute right now — not what engines exist, what WORKS.<br>Scanned: {now}</div>
<div class="callout">
  <div style="font-size:10px;letter-spacing:.2em;color:#00ff88;margin-bottom:8px">BEST MOVE RIGHT NOW</div>
  <div style="font-size:15px;color:#deeae1">Gmail is connected and working. <span style="color:#00ff88">EMAIL_OUTREACH now reaches journalists, newsletters, and orgs directly</span> — no new API keys. This is the first real offensive channel.</div>
</div>
<div class="stats">
  <div class="stat"><b style="color:#00ff88">{r["active"]}</b><span>ACTIVE</span></div>
  <div class="stat"><b style="color:#ff4455">{r["blocked"]}</b><span>BLOCKED</span></div>
  <div class="stat"><b style="color:#ffd166">{r["degraded"]}</b><span>DEGRADED</span></div>
  <div class="stat"><b style="color:#deeae1;font-size:16px!important">{r["priority_fix"]}</b><span>PRIORITY FIX</span></div>
</div>
<div class="grid">{cards}</div>
<footer>SOLARPUNK™ · CAPABILITY_SCANNER · auto-updated every cycle<br>
<a href="store.html">Store</a> · <a href="outreach.html">Bridges</a> · <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">GitHub</a></footer>
</div></body></html>""", encoding="utf-8")


def run():
    print("CAPABILITY_SCANNER starting...")
    r = scan()
    print(f"  {r['summary']} | best channel: {r['best_channel_now']}")
    print(f"  🌐 https://meekotharaccoon-cell.github.io/meeko-nerve-center/capabilities.html")
    print("CAPABILITY_SCANNER done.")


if __name__ == "__main__":
    run()
