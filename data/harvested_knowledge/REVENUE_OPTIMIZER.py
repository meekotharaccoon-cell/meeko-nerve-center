#!/usr/bin/env python3
"""
REVENUE_OPTIMIZER.py — Claude-powered revenue maximizer
=========================================================
Every cycle: reads all revenue/product data, asks Claude for concrete
actions, rewrites product descriptions, emails digest to Meeko.
Uses ONLY existing channels: Ko-fi, GitHub Sponsors, GitHub Pages, Gmail.
Zero new secrets needed.
"""
import os, json, smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
sys.path.insert(0, str(Path(__file__).parent))
from AI_CLIENT import ask_json, ask_json_list, ai_available

DATA  = Path("data");  DATA.mkdir(exist_ok=True)
DOCS  = Path("docs");  DOCS.mkdir(exist_ok=True)
STATE = DATA / "revenue_optimizer_state.json"

GMAIL_ADDR = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "")


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"cycles": 0, "emails_sent": 0, "last_email_day": "", "actions_taken": []}


def get_context():
    ctx = {}
    for f in ["revenue_inbox.json", "flywheel_summary.json", "gumroad_listings.json",
              "kofi_state.json", "free_api_state.json", "business_factory_state.json",
              "brain_state.json", "secrets_checker_state.json", "architect_plan.json"]:
        fp = DATA / f
        if fp.exists():
            try:
                ctx[f] = json.loads(fp.read_text())
            except Exception:
                pass
    return ctx


def generate_actions(ctx):
    """Claude returns 5 concrete revenue actions executable today."""
    if not ai_available():
        return []
    prompt = f"""SolarPunk autonomous revenue system. Available channels:
- Ko-fi shop (active, 0 sales)
- GitHub Sponsors (active, 0 sponsors)  
- GitHub Pages (10 landing pages live)
- Gmail (can send outreach emails)
- Gumroad (6 products queued, no API token yet)
- Claude API (working)

CURRENT DATA:
{json.dumps(ctx, default=str)[:2500]}

Generate 5 CONCRETE actions to generate first revenue using ONLY the above.
No new accounts. No social media. Focus on: SEO improvements, product copy,
email outreach to warm leads in email_brain data, Ko-fi page optimization,
GitHub Sponsors profile, landing page improvements.

Return JSON array of:
{{"action": "...", "channel": "...", "expected_usd": 0, "steps": ["step1", "step2"]}}"""
    return ask_json_list(prompt, max_tokens=1500) or []


def optimize_one_product(ctx):
    """Rewrite one product listing per cycle."""
    if not ai_available():
        return {}
    listings = ctx.get("gumroad_listings.json", {})
    products = listings.get("products", []) if isinstance(listings, dict) else []
    if not isinstance(products, list) or not products:
        return {}
    # Rotate through products
    state = load_state()
    idx = state.get("cycles", 0) % max(len(products), 1)
    product = products[idx] if idx < len(products) else products[0]
    prompt = f"""Rewrite this product for maximum conversion on Ko-fi / Gumroad.
Product: {json.dumps(product, default=str)[:500]}

Return JSON:
{{"headline": "15 words max", "description": "100 words, emotional hook + concrete value",
  "bullets": ["benefit 1", "benefit 2", "benefit 3", "benefit 4", "benefit 5"],
  "cta": "call to action", "tags": ["tag1","tag2","tag3","tag4","tag5"]}}"""
    return ask_json(prompt, max_tokens=700) or {}


def send_digest(actions, product_opt):
    if not GMAIL_ADDR or not GMAIL_PASS:
        return False
    try:
        action_html = ""
        for i, a in enumerate(actions[:5], 1):
            if not isinstance(a, dict):
                continue
            steps = "".join(f"<li>{s}</li>" for s in (a.get("steps") or []))
            action_html += f"""<div style='border-left:3px solid #0a0;padding:8px 12px;margin:8px 0'>
<b>{i}. {a.get('action','')}</b><br>
Channel: {a.get('channel','')} | Est: ${a.get('expected_usd',0)}/mo
<ol>{steps}</ol></div>"""

        prod_html = ""
        if product_opt:
            prod_html = f"""<h2>📝 Product Rewrite</h2>
<p><b>{product_opt.get('headline','')}</b></p>
<p>{product_opt.get('description','')}</p>
<ul>{''.join(f"<li>{b}</li>" for b in product_opt.get('bullets',[]))}</ul>
<p><b>CTA:</b> {product_opt.get('cta','')}</p>
<p><b>Tags:</b> {', '.join(product_opt.get('tags',[]))}</p>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"💰 SolarPunk Revenue Actions — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        msg["From"] = GMAIL_ADDR
        msg["To"]   = GMAIL_ADDR
        html = f"""<html><body style='font-family:Arial;max-width:640px;margin:auto'>
<h1>🌱 Revenue Optimizer</h1>
<h2>🎯 {len(actions)} Actions Ready</h2>
{action_html}
{prod_html}
<hr><p style='color:#888;font-size:12px'>SolarPunk Autonomous System — {datetime.now(timezone.utc).isoformat()}</p>
</body></html>"""
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_ADDR, GMAIL_PASS)
            s.sendmail(GMAIL_ADDR, GMAIL_ADDR, msg.as_string())
        return True
    except Exception as e:
        print(f"  Email error: {e}")
        return False


def build_page(state, actions, product_opt):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    action_html = ""
    for a in (actions or []):
        if not isinstance(a, dict):
            continue
        steps = "".join(f"<li>{s}</li>" for s in (a.get("steps") or []))
        action_html += f"""<div style='border:1px solid #1a3;padding:10px;margin:8px 0'>
<b>{a.get('action','')}</b> | {a.get('channel','')} | ${a.get('expected_usd',0)}/mo
<ol>{steps}</ol></div>"""
    prod_html = f"<pre style='background:#111;padding:10px'>{json.dumps(product_opt, indent=2)[:800]}</pre>" if product_opt else "<p>none</p>"
    html = f"""<!DOCTYPE html><html><head><title>Revenue Optimizer</title>
<meta charset=utf-8>
<style>body{{font-family:monospace;background:#0a0a0a;color:#0f0;padding:20px}}
h1,h2{{color:#0f0}}pre{{overflow-x:auto;white-space:pre-wrap}}</style>
</head><body>
<h1>💰 REVENUE OPTIMIZER — {ts}</h1>
<p>Cycles: {state['cycles']} | Emails sent: {state['emails_sent']}</p>
<h2>Actions This Cycle ({len(actions) if actions else 0})</h2>
{action_html}
<h2>Product Copy Optimized</h2>{prod_html}
</body></html>"""
    (DOCS / "optimizer.html").write_text(html)


def run():
    print("REVENUE_OPTIMIZER — maximizing revenue from existing channels...")
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1

    ctx         = get_context()
    actions     = generate_actions(ctx)
    product_opt = optimize_one_product(ctx)

    if product_opt:
        opt_log = DATA / "product_optimizations.json"
        history = json.loads(opt_log.read_text()) if opt_log.exists() else []
        history.append({"ts": datetime.now(timezone.utc).isoformat(), "opt": product_opt})
        opt_log.write_text(json.dumps(history[-100:], indent=2))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if actions and state.get("last_email_day") != today:
        sent = send_digest(actions, product_opt)
        if sent:
            state["emails_sent"] = state.get("emails_sent", 0) + 1
            state["last_email_day"] = today
            print(f"  📧 Revenue digest sent")

    build_page(state, actions, product_opt)
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(state, indent=2))
    print(f"  Actions: {len(actions) if actions else 0} | Product opt: {'yes' if product_opt else 'no'}")
    print("REVENUE_OPTIMIZER done")


if __name__ == "__main__":
    run()
