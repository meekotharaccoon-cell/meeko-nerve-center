# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
GROWTH_CHAIN.py — Distribute → Attract → Convert → Retain → Refer → (loop)

The five-step growth loop. Every step feeds the next.
Every new person becomes a node in the distribution network.

Step 1 DISTRIBUTE  — push content everywhere, all channels, always
Step 2 ATTRACT     — optimize what's pulling, kill what's not
Step 3 CONVERT     — turn visitors into buyers (lowest friction path)
Step 4 RETAIN      — keep them engaged (email, updates, mission)
Step 5 REFER       — turn buyers into distributors (they become the system)

The refer step feeds back into distribute. The loop closes.
Every sale creates the next sale.

Output: data/growth_chain_state.json
        docs/growth.html (live dashboard)
Consumed by: SOCIAL_PROMOTER, EMAIL_OUTREACH, VIRALITY_ENGINE
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

try:
    from AI_CLIENT import ai_available
except ImportError:
    def ai_available(): return False

def load(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text())
            return d if isinstance(d, (dict, list)) else (fb or {})
        except: pass
    return fb if fb is not None else {}

def run():
    print("GROWTH_CHAIN running...")
    now = datetime.now(timezone.utc).isoformat()

    resonance = load("resonance_state.json")
    social    = load("social_promoter_state.json")
    analytics = load("analytics_state.json")
    knowledge = load("knowledge_chain_synthesis.json")
    economy   = load("economy_chain_ledger.json")
    newsletter= load("newsletter_state.json")
    fork_st   = load("fork_scanner_state.json")
    gumroad   = load("gumroad_engine_state.json")
    kofi_st   = load("kofi_state.json")
    substack  = load("substack_state.json")
    devto_st  = load("dev_to_publisher_state.json")
    signal_q  = load("signal_chain_queue.json", {"actions": []})
    prev      = load("growth_chain_state.json", {
        "cycles": 0, "actions_total": 0, "steps_completed": {}
    })

    score     = resonance.get("score", 0)
    stars     = resonance.get("stars", 0)
    forks     = fork_st.get("total_forks", 0)
    revenue   = economy.get("total_earned", 0)
    loop_closed = economy.get("loop_closed", False)
    queue_depth = (social.get("queue_total") or social.get("queue_size") or
                   len(signal_q.get("actions", [])))
    newsletter_subs = newsletter.get("subscribers", 0) or substack.get("subscribers", 0)
    devto_posts = devto_st.get("posts_published", 0)
    gumroad_live = gumroad.get("total_live", 0)
    kofi_live = kofi_st.get("items_listed", 0)

    actions = []

    def act(step, channel, action_text, priority="medium"):
        actions.append({
            "step": step,
            "channel": channel,
            "action": action_text,
            "priority": priority,
            "ts": now,
        })

    # ════════════════════════════════════════════════════════════
    # STEP 1: DISTRIBUTE — be everywhere, always
    # ════════════════════════════════════════════════════════════
    if queue_depth > 0:
        act(1, "twitter", f"{queue_depth} posts queued in SOCIAL_PROMOTER — add X_API_KEY secret to publish",
            "critical" if queue_depth > 50 else "high")

    if devto_posts == 0:
        act(1, "devto", "DEV.to: post a technical article about the SolarPunk architecture — DEVTO_API_KEY is set, run DEV_TO_PUBLISHER",
            "high")

    if substack.get("issues_published", 0) < 3:
        act(1, "substack", "Substack: post 2 more issues to hit 3-issue momentum threshold",
            "medium")

    act(1, "github", "Pin the best issue as a README hook — the story is the distribution", "medium")

    # Hacker News — most impactful single action for builders
    hn_posted = prev.get("hn_posted", False)
    if not hn_posted:
        act(1, "hacker_news",
            "POST Show HN NOW: 'Show HN: I built a self-running AI agent that funds Gaza relief from every sale' — news.ycombinator.com/submit",
            "critical")

    # ════════════════════════════════════════════════════════════
    # STEP 2: ATTRACT — amplify what works
    # ════════════════════════════════════════════════════════════
    for angle in knowledge.get("content_angles", [])[:3]:
        act(2, "content", f"Post: {angle[:150]}", "medium")

    if stars >= 1:
        act(2, "social_proof",
            f"Leverage {stars} star(s): 'People are watching this. Here's what SolarPunk is doing right now...' — live update thread",
            "high")

    if score >= 60:
        act(2, "cta",
            "Resonance is HIGH — add a direct call-to-action link in every post, every page, every email: 'Ko-fi / Gumroad / Email us'",
            "high")

    # ════════════════════════════════════════════════════════════
    # STEP 3: CONVERT — lowest friction path to first dollar
    # ════════════════════════════════════════════════════════════
    if revenue == 0:
        act(3, "kofi",
            "FASTEST PATH: go to ko-fi.com/account/shop → paste 6 listings from data/quick_revenue.html → LIVE IN 5 MINUTES",
            "critical")

    if gumroad_live == 0:
        act(3, "gumroad",
            "10 products queued in data/gumroad_listings.json — create them at gumroad.com/new/product",
            "critical")

    if kofi_live > 0 or gumroad_live > 0:
        act(3, "pricing",
            "Add 'Pay what you want' option to at least one product — lowers barrier to first conversion",
            "high")

    act(3, "store",
        "Add a '$1 tip to fund Gaza' product to Ko-fi/Gumroad — the mission IS the product for some buyers",
        "high")

    # ════════════════════════════════════════════════════════════
    # STEP 4: RETAIN — keep them coming back
    # ════════════════════════════════════════════════════════════
    if newsletter_subs == 0:
        act(4, "email",
            "Add email signup to every page. Even 10 subscribers = 10 people who asked to hear from you.",
            "high")

    act(4, "transparency",
        "Weekly public update: 'SolarPunk week N: N cycles run, $X earned, $Y to Gaza, N engines built' — builds trust over time",
        "medium")

    act(4, "changelog",
        "Auto-generate and post a CHANGELOG from commit history — every commit proves the system is alive",
        "medium")

    # ════════════════════════════════════════════════════════════
    # STEP 5: REFER — turn buyers into distributors
    # ════════════════════════════════════════════════════════════
    if forks > 0:
        act(5, "community",
            f"{forks} fork(s) exist — reach out to each: 'You forked SolarPunk. Want to be listed as a contributor? Want to build on this?'",
            "high")

    act(5, "affiliate",
        "Add AFFILIATE_MAXIMIZER output to every Gumroad product — buyers get a referral link, earn 20% per sale they bring in",
        "medium")

    act(5, "story",
        "When first sale happens: post the FULL STORY everywhere. 'An AI system ran itself for N days and made its first dollar for Gaza.' This goes viral.",
        "high")

    # ════════════════════════════════════════════════════════════
    # Save state + surface output
    # ════════════════════════════════════════════════════════════
    critical = [a for a in actions if a["priority"] == "critical"]
    high     = [a for a in actions if a["priority"] == "high"]

    output = {
        "ts": now,
        "revenue": revenue,
        "loop_closed": loop_closed,
        "score": score,
        "stars": stars,
        "forks": forks,
        "actions": actions,
        "critical_actions": critical,
        "action_count": len(actions),
        "step_coverage": {
            str(s): sum(1 for a in actions if a["step"] == s)
            for s in range(1, 6)
        },
    }

    prev["cycles"]       = prev.get("cycles", 0) + 1
    prev["actions_total"]= prev.get("actions_total", 0) + len(actions)
    prev["last_run"]     = now
    prev["last_output"]  = output

    (DATA / "growth_chain_state.json").write_text(json.dumps(prev, indent=2))

    print(f"  🌱 Actions: {len(actions)} | Critical: {len(critical)} | High: {len(high)}")
    print(f"  Steps covered: { {s: sum(1 for a in actions if a['step']==s) for s in range(1,6)} }")
    for a in critical[:3]:
        print(f"  🔴 [{a['channel']}] {a['action'][:80]}")

    # ── Build growth dashboard ────────────────────────────────────────────────
    step_names = {1: "Distribute", 2: "Attract", 3: "Convert", 4: "Retain", 5: "Refer"}
    pri_color  = {"critical": "#f44336", "high": "#ff9800", "medium": "#2196f3", "low": "#555"}

    rows = "\n".join(
        f'<tr>'
        f'<td style="color:#aaa">{step_names.get(a["step"], a["step"])}</td>'
        f'<td style="color:#777">{a["channel"]}</td>'
        f'<td style="color:{pri_color.get(a["priority"], "#555")};font-weight:700">{a["priority"].upper()}</td>'
        f'<td>{a["action"][:120]}</td>'
        f'</tr>'
        for a in sorted(actions, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["priority"], 3))
    )
    loop_html = (
        '<div style="background:#0d1a0d;border:2px solid #4caf50;border-radius:8px;padding:1rem;margin-bottom:1rem;color:#81c784;font-weight:700">🎉 LOOP CLOSED — Revenue flowing</div>'
        if loop_closed else
        '<div style="background:#1a0f00;border:2px solid #ff9800;border-radius:8px;padding:1rem;margin-bottom:1rem;color:#ffb74d">🔄 LOOP RUNNING — First revenue incoming</div>'
    )

    (DOCS / "growth.html").write_text(f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta http-equiv="refresh" content="300">
<title>SolarPunk Growth Chain</title>
<style>
body{{background:#020208;color:#ccc;font-family:-apple-system,sans-serif;padding:1.5rem}}
h1{{color:#81c784;margin-bottom:.25rem}}
.meta{{color:#444;font-size:.8rem;margin-bottom:1.5rem}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
td,th{{padding:.4rem .6rem;border-bottom:1px solid #111;vertical-align:top}}
th{{color:#555;text-transform:uppercase;font-size:.7rem;letter-spacing:1px}}
.stat{{display:inline-block;margin-right:1.5rem;margin-bottom:.75rem}}
.stat .val{{font-size:1.4rem;font-weight:700;color:#81c784}}
.stat .lbl{{font-size:.7rem;color:#444;text-transform:uppercase}}
</style></head><body>
<h1>🌱 SolarPunk Growth Chain</h1>
<p class="meta">Distribute → Attract → Convert → Retain → Refer → Distribute | Cycle {prev['cycles']} | {now[:16]} UTC</p>
{loop_html}
<div style="margin-bottom:1.5rem">
  <span class="stat"><div class="val">${revenue:.2f}</div><div class="lbl">Earned</div></span>
  <span class="stat"><div class="val">{score}/100</div><div class="lbl">Resonance</div></span>
  <span class="stat"><div class="val">{stars}</div><div class="lbl">Stars</div></span>
  <span class="stat"><div class="val">{forks}</div><div class="lbl">Forks</div></span>
  <span class="stat"><div class="val">{len(actions)}</div><div class="lbl">Actions</div></span>
  <span class="stat"><div class="val">{len(critical)}</div><div class="lbl">Critical</div></span>
</div>
<table>
<thead><tr><th>Step</th><th>Channel</th><th>Priority</th><th>Action</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<p style="margin-top:1rem;color:#333;font-size:.75rem">
  Every step feeds the next. Every sale creates the next sale.<br>
  Updated: {now[:16]} UTC | <a href="chains.html" style="color:#333">→ Chain Orchestrator</a>
</p>
</body></html>""")

if __name__ == "__main__": run()
