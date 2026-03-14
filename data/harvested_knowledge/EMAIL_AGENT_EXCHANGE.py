#!/usr/bin/env python3
"""EMAIL_AGENT_EXCHANGE — AI agents that email AI agents, everyone gets paid per email

FIXES v2:
- Uses AI_CLIENT (free HuggingFace) — agents always online, no Anthropic key needed
- Reads exchange_inbox.json (written by EMAIL_BRAIN) + revenue_inbox fallback
- Payment refs in every reply so KOFI_PAYMENT_TRACKER can reconcile
- route_to_agent() uses AI fallback even without Anthropic key
"""
import os, json, re, smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# AI_CLIENT: free HF models, no Anthropic key needed
try:
    from AI_CLIENT import ask, ask_json
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask(messages, **kw): return "[AI offline — check AI_CLIENT.py and HF_TOKEN secret]"
    def ask_json(prompt, **kw): return None

DATA      = Path("data"); DATA.mkdir(exist_ok=True)
GMAIL     = os.environ.get("GMAIL_ADDRESS", "")
GPWD      = os.environ.get("GMAIL_APP_PASSWORD", "")
KOFI_USER = os.environ.get("KOFI_USERNAME", "meekotharaccoon")

# ── AGENT REGISTRY ────────────────────────────────────────────────────────────
AGENTS = {
    "RESEARCH_AGENT": {
        "specialty": "market research, fact-finding, web intelligence",
        "rate_per_email": 0.05,
        "system": "You are a research agent for the SolarPunk Email Exchange. You receive research requests via email and reply with thorough, cited research. Be concise but complete. End every reply with: '[RESEARCH_AGENT — SolarPunk Exchange]'",
        "keywords": ["research", "find", "what is", "tell me about", "information on", "look up", "investigate"],
    },
    "GRANT_WRITER_AGENT": {
        "specialty": "grant writing, proposal drafting, funding applications",
        "rate_per_email": 0.10,
        "system": "You are a grant writing agent for the SolarPunk Email Exchange. You draft compelling grant applications and proposals. Focus on impact, feasibility, and alignment with funder priorities. End every reply with: '[GRANT_WRITER_AGENT — SolarPunk Exchange]'",
        "keywords": ["grant", "proposal", "funding", "application", "write a pitch", "apply for"],
    },
    "MARKET_AGENT": {
        "specialty": "market analysis, pricing strategy, competitor research",
        "rate_per_email": 0.05,
        "system": "You are a market analysis agent for the SolarPunk Email Exchange. You analyze markets, pricing, and competitors. Give actionable insights. End every reply with: '[MARKET_AGENT — SolarPunk Exchange]'",
        "keywords": ["market", "pricing", "competitor", "analyze", "business model", "strategy", "revenue"],
    },
    "CODE_AGENT": {
        "specialty": "code review, debugging, technical advice",
        "rate_per_email": 0.08,
        "system": "You are a code agent for the SolarPunk Email Exchange. You review code, debug issues, and give technical advice. Be precise and practical. End every reply with: '[CODE_AGENT — SolarPunk Exchange]'",
        "keywords": ["code", "debug", "python", "javascript", "error", "fix", "review my", "technical"],
    },
    "COPY_AGENT": {
        "specialty": "copywriting, emails, social media, product descriptions",
        "rate_per_email": 0.05,
        "system": "You are a copywriting agent for the SolarPunk Email Exchange. You write compelling copy for any medium. Match the brand voice. End every reply with: '[COPY_AGENT — SolarPunk Exchange]'",
        "keywords": ["write", "copy", "email", "description", "social post", "tweet", "caption", "headline"],
    },
    "SOLARPUNK_AGENT": {
        "specialty": "help others build their own SolarPunk autonomous income system",
        "rate_per_email": 0.00,
        "system": "You are SolarPunk's ambassador agent. You help people build their own autonomous income systems. Give them the fork guide, technical help, and encouragement. End every reply with: '[SOLARPUNK_AGENT — FREE — Build your own: github.com/meekotharaccoon-cell/meeko-nerve-center]'",
        "keywords": ["solarpunk", "autonomous", "github actions", "fork", "build my own", "income system", "your system"],
    },
}

SPLIT = {"agent_owner": 0.60, "meeko_platform": 0.25, "gaza": 0.15}


def load():
    f = DATA / "email_exchange_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "total_tasks": 0, "total_earned": 0.0, "total_to_gaza": 0.0,
            "agent_earnings": {}, "task_log": [], "registered_clients": []}


def save(s):
    s["task_log"] = s.get("task_log", [])[-500:]
    (DATA / "email_exchange_state.json").write_text(json.dumps(s, indent=2))


def route_to_agent(subject, body):
    """Match email to best agent by keywords, fall back to AI routing."""
    combined = (subject + " " + body).lower()
    scores = {}
    for name, agent in AGENTS.items():
        score = sum(1 for kw in agent["keywords"] if kw in combined)
        if score > 0: scores[name] = score
    if scores:
        return max(scores, key=scores.get)
    # AI routing fallback — free HF models, always available
    agent_list = "\n".join([f"  {n}: {a['specialty']}" for n, a in AGENTS.items()])
    prompt = f"Route this email to the best agent.\nSUBJECT: {subject}\nBODY: {body[:300]}\n\nAGENTS:\n{agent_list}\n\nReply ONLY with JSON: {{\"agent_name\": \"AGENT_NAME\"}}"
    result = ask_json(prompt, max_tokens=60)
    if result:
        name = str(result.get("agent_name", "RESEARCH_AGENT")).strip().upper()
        return name if name in AGENTS else "RESEARCH_AGENT"
    return "RESEARCH_AGENT"


def run_agent(agent_name, task_email):
    """AI runs as the specified agent — free HF models, always online."""
    agent = AGENTS[agent_name]
    task_content = (
        f"Task from client:\n"
        f"SUBJECT: {task_email.get('subject', '')}\n\n"
        f"{task_email.get('body', '')[:800]}"
    )
    try:
        response = ask(
            [{"role": "user", "content": task_content}],
            system=agent["system"],
            max_tokens=800,
        )
        return response
    except Exception as e:
        return f"I encountered an issue processing your request: {e}\n\n[{agent_name} — SolarPunk Exchange]"


def send_agent_reply(to, subject, agent_name, response, rate, task_ref):
    if not GMAIL or not GPWD: return False
    rate_note = f"Rate: ${rate:.2f}" if rate > 0 else "Free (SolarPunk mission)"
    pay_note = (
        f"\n\n💳 Pay for this task:\n"
        f"   https://ko-fi.com/{KOFI_USER}\n"
        f"   Amount: ${rate:.2f} | Ref: {task_ref}\n"
        f"   (Card + PayPal, no Ko-fi account needed)"
    ) if rate > 0 else ""
    body = (
        f"{response}{pay_note}\n\n"
        f"---\n"
        f"SolarPunk Email Agent Exchange | {rate_note}\n"
        f"15% of every payment → Gaza humanitarian fund\n"
        f"Need another task? Reply with: [TASK] your request\n"
        f"Open-source: github.com/meekotharaccoon-cell/meeko-nerve-center"
    )
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL
        msg["To"] = to
        msg["Subject"] = f"Re: {subject} [{agent_name}]"
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(GMAIL, GPWD)
            s.sendmail(GMAIL, to, msg.as_string())
        return True
    except Exception as e:
        print(f"  send: {e}")
        return False


def process_task_emails(state):
    """Read task emails from exchange_inbox.json (EMAIL_BRAIN) + revenue_inbox fallback."""
    all_emails = []
    for fname in ["exchange_inbox.json", "revenue_inbox.json"]:
        inbox = DATA / fname
        if inbox.exists():
            try:
                all_emails.extend(json.loads(inbox.read_text()))
            except: pass

    if not all_emails:
        print("  No inbox data — EMAIL_BRAIN hasn't run yet or Gmail not configured")
        return

    processed = {t.get("email_id") for t in state.get("task_log", [])}

    for em in all_emails[-30:]:
        eid = em.get("ts", em.get("email_id", ""))
        if eid in processed:
            continue

        subject    = em.get("subject", "")
        body       = em.get("body", "")
        sender_raw = em.get("from", "")

        is_task = (
            "[TASK]" in subject
            or "agent" in (subject + body).lower()
            or em.get("is_exchange_task", False)
        )
        if not is_task:
            continue

        m = re.search(r'<(.+?)>', sender_raw)
        sender = m.group(1) if m else sender_raw
        if "@" not in sender:
            continue

        agent_name = route_to_agent(subject, body)
        agent      = AGENTS[agent_name]
        rate       = agent["rate_per_email"]
        task_ref   = f"{agent_name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        print(f"  TASK [{agent_name}] from {sender}: {subject[:40]}")
        response = run_agent(agent_name, em)
        ok       = send_agent_reply(sender, subject, agent_name, response, rate, task_ref)

        record = {
            "email_id": eid, "task_ref": task_ref,
            "from": sender, "subject": subject[:50],
            "agent": agent_name, "rate": rate,
            "replied": ok, "paid": False,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        state.setdefault("task_log", []).append(record)
        state["total_tasks"] = state.get("total_tasks", 0) + 1

        if ok and rate > 0:
            state["total_earned"]  = state.get("total_earned", 0)  + rate * SPLIT["meeko_platform"]
            state["total_to_gaza"] = state.get("total_to_gaza", 0) + rate * SPLIT["gaza"]
            state.setdefault("agent_earnings", {})[agent_name] = (
                state["agent_earnings"].get(agent_name, 0) + rate * SPLIT["agent_owner"]
            )


def generate_exchange_page(state):
    """Regenerate docs/exchange.html with live stats."""
    agent_cards = "".join([f"""
<div class="agent">
  <div class="agent-name">{n.replace('_', ' ')}</div>
  <div class="specialty">{a['specialty']}</div>
  <div class="rate">{'Free' if a['rate_per_email'] == 0 else f'${a["rate_per_email"]:.2f}/task'}</div>
  <p>Email <strong>{GMAIL or '[exchange email]'}</strong><br>Subject: <code>[TASK] your request</code></p>
</div>""" for n, a in AGENTS.items()])

    html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk Email Agent Exchange — Live Stats</title>
<style>
body{{font-family:sans-serif;background:#0a0a0a;color:#e8e8e8;margin:0;padding:20px;max-width:960px;margin:auto}}
h1{{color:#c8a86b}}p.sub{{color:#888;margin-top:0}}
.stats{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}}
.stat{{background:#1a1a1a;padding:16px;border-radius:8px;text-align:center;flex:1;min-width:90px}}
.stat-n{{font-size:26px;color:#c8a86b;font-weight:bold}}
.stat-l{{font-size:11px;color:#666;text-transform:uppercase;letter-spacing:1px}}
.agents{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin:20px 0}}
.agent{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;padding:16px}}
.agent-name{{color:#c8a86b;font-weight:bold;font-size:13px;letter-spacing:1px}}
.specialty{{font-size:12px;color:#888;margin:4px 0 8px}}
.rate{{font-size:18px;color:#c8a86b;font-weight:bold;margin-bottom:8px}}
.how{{background:#1a1a1a;padding:16px;border-radius:8px;margin:20px 0;border-left:3px solid #c8a86b}}
a{{color:#c8a86b}} code{{background:#111;padding:2px 6px;border-radius:3px;font-size:13px}}
.footer{{color:#555;font-size:12px;margin-top:30px;padding-top:16px;border-top:1px solid #1a1a1a}}
</style></head><body>
<h1>⚡ SolarPunk Email Agent Exchange</h1>
<p class="sub">AI agents that work via email. Pay per task. 15% funds Palestinian artists.</p>
<div class="stats">
<div class="stat"><div class="stat-n">{len(AGENTS)}</div><div class="stat-l">Agents</div></div>
<div class="stat"><div class="stat-n">{state.get('total_tasks',0)}</div><div class="stat-l">Tasks Done</div></div>
<div class="stat"><div class="stat-n">${state.get('total_earned',0):.2f}</div><div class="stat-l">Platform Earned</div></div>
<div class="stat"><div class="stat-n">${state.get('total_to_gaza',0):.2f}</div><div class="stat-l">→ Gaza</div></div>
<div class="stat"><div class="stat-n">~6hr</div><div class="stat-l">Response</div></div>
</div>
<div class="how">
<strong>How to use:</strong><br>
1. Email <strong>{GMAIL or '[exchange email]'}</strong><br>
2. Subject: <code>[TASK] your request here</code><br>
3. Agent replies within the next cycle (up to 6 hours)<br>
4. Pay via Ko-fi link in the reply — card + PayPal, no account needed<br><br>
<strong>Split: 60% agent · 25% platform · 15% Gaza Rose Fund</strong>
</div>
<h2>Available Agents</h2>
<div class="agents">{agent_cards}</div>
<div class="footer">
Open-source: <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">meeko-nerve-center</a> ·
Support: <a href="https://ko-fi.com/{KOFI_USER}">ko-fi.com/{KOFI_USER}</a> ·
Built by SolarPunk
</div></body></html>"""

    Path("docs").mkdir(exist_ok=True)
    (Path("docs") / "exchange.html").write_text(html)
    print("  Exchange page → docs/exchange.html")


def run():
    state = load()
    state["cycles"]   = state.get("cycles", 0) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    print(f"EMAIL_AGENT_EXCHANGE cycle {state['cycles']} | {state.get('total_tasks',0)} tasks | ${state.get('total_earned',0):.2f} | AI={'online' if AI_ONLINE else 'OFFLINE'}")
    process_task_emails(state)
    generate_exchange_page(state)
    print(f"  Gaza fund: ${state.get('total_to_gaza',0):.2f}")
    save(state)
    return state


if __name__ == "__main__":
    run()
