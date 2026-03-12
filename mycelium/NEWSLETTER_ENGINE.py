#!/usr/bin/env python3
"""
NEWSLETTER_ENGINE — auto-generate and send email newsletter from data/

Every cycle:
  1. Pull top signals: resonance, flywheel, spider, asks
  2. Use Claude to write a punchy 200-word newsletter
  3. Send via Gmail (GMAIL_APP_PASSWORD) to data/newsletter_subscribers.json
  4. Archive to data/newsletter_archive.json
  5. Max 1 send per 24h
"""
import os, json, time, urllib.request, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime, timezone

DATA    = Path("data"); DATA.mkdir(exist_ok=True)
STATE   = DATA / "newsletter_state.json"
ARCHIVE = DATA / "newsletter_archive.json"
SUBS    = DATA / "newsletter_subscribers.json"

API_KEY    = os.environ.get("ANTHROPIC_API_KEY", "").strip()
GMAIL_USER = os.environ.get("GMAIL_USER", "meekotharaccoon@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
MODEL      = "claude-haiku-4-5-20251001"
MIN_HOURS  = 24

SYSTEM = """You write short punchy newsletters for SolarPunk — Meeko's autonomous AI system.
Tone: builder energy, genuine. Not marketing. Max 200 words.
15% of revenue goes to Palestinian relief (PCRF) — mention naturally.
End with one specific ask (buy link, star repo, reply).
Output ONLY JSON: {"subject": "...", "body": "..."}"""


def rj(path, fb=None):
    try: return json.loads(Path(path).read_text())
    except: return fb or {}


def call_claude(prompt):
    if not API_KEY: return None
    try:
        payload = json.dumps({"model": MODEL, "max_tokens": 512, "system": SYSTEM,
            "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
            headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = json.loads(r.read())["content"][0]["text"].strip()
            return json.loads(raw.replace("```json","").replace("```","").strip())
    except Exception as e:
        print(f"  Claude error: {e}"); return None


def should_send(state):
    last = state.get("last_sent")
    if not last: return True
    try:
        from datetime import timedelta
        delta = datetime.now(timezone.utc) - datetime.fromisoformat(last)
        return delta.total_seconds() > MIN_HOURS * 3600
    except: return True


def send_email(to_list, subject, body):
    if not GMAIL_PASS or not to_list:
        print(f"  SKIP send: {'no password' if not GMAIL_PASS else 'no subscribers'}")
        return 0
    sent = 0
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        for addr in to_list:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"]    = f"SolarPunk <{GMAIL_USER}>"
                msg["To"]      = addr
                msg.attach(MIMEText(body, "plain"))
                server.sendmail(GMAIL_USER, addr, msg.as_string())
                sent += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"  Failed {addr}: {e}")
        server.quit()
    except Exception as e:
        print(f"  SMTP error: {e}")
    return sent


def run():
    print("NEWSLETTER_ENGINE starting...")
    state = rj(STATE, {"cycles": 0, "total_sent": 0, "last_sent": None})
    subs  = rj(SUBS, [])
    if isinstance(subs, dict): subs = subs.get("emails", [])

    if not should_send(state):
        print(f"  SKIP: last sent {str(state.get('last_sent',''))[:16]} — waiting {MIN_HOURS}h")
        state["cycles"] = state.get("cycles", 0) + 1
        STATE.write_text(json.dumps(state, indent=2))
        return

    resonance = rj(DATA / "resonance_state.json")
    omnibus   = rj(DATA / "omnibus_last.json")
    flywheel  = rj(DATA / "flywheel_state.json")
    spider    = rj(DATA / "repo_spider_state.json")
    asks_raw  = rj(DATA / "asks_queue.json")
    asks      = asks_raw if isinstance(asks_raw, list) else []
    best_ask  = next((a for a in asks if a.get("status") == "pending"), None)

    prompt = f"""SolarPunk state:
- Resonance: {resonance.get('resonance_score', 0)}/100 ({resonance.get('resonance_label', 'SILENT')})
- Stars: {resonance.get('github', {}).get('stars', 0)}
- Health: {omnibus.get('health_after', 0)}/100
- Revenue: ${flywheel.get('total_routed_usd', 0):.2f}
- Repos forked: {len(spider.get('forked', []))}
- Subscribers: {len(subs)}
- Best pending ask: {best_ask.get('content', 'none')[:80] if best_ask else 'none'}
Store: https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html
Write this week's newsletter."""

    result = call_claude(prompt)
    if not result:
        print("  Failed to generate"); return

    subject = result.get("subject", "SolarPunk update")
    body    = result.get("body", "")
    print(f"  Subject: {subject}")

    archive = rj(ARCHIVE, [])
    if not isinstance(archive, list): archive = []
    archive.append({"ts": datetime.now(timezone.utc).isoformat(),
                    "subject": subject, "body": body, "sent_to": len(subs)})
    ARCHIVE.write_text(json.dumps(archive[-52:], indent=2))

    sent = send_email(subs, subject, body)
    print(f"  Sent to {sent}/{len(subs)} subscribers")

    state["cycles"]       = state.get("cycles", 0) + 1
    state["total_sent"]   = state.get("total_sent", 0) + sent
    state["last_sent"]    = datetime.now(timezone.utc).isoformat()
    state["last_subject"] = subject
    STATE.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    run()
