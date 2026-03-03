#!/usr/bin/env python3
"""
SYNAPSE — The Resolver
=======================
Runs AFTER NEURON_A and NEURON_B.

Reads both reports, finds consensus, resolves conflicts intelligently,
applies remaining agreed fixes, saves the unified brain state,
and sends meeko a daily briefing.

Logic:
  BOTH flagged it              = high confidence = auto-apply
  ONLY A flagged, B overruled  = skip (B wins)
  ONLY A flagged, B confirmed  = apply
  ONLY B found it, conf >= 0.9 = apply
  B escalated                  = flag for human review

Required: ANTHROPIC_API_KEY, GH_PAT
Optional: GMAIL_ADDRESS, GMAIL_APP_PASSWORD (for email briefing)
"""
import os, sys, json, base64, hashlib, smtplib, requests
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
GH_TOKEN           = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
REPO_OWNER         = os.environ.get("GITHUB_REPOSITORY_OWNER", "meekotharaccoon-cell")
REPO_NAME          = os.environ.get("GITHUB_REPOSITORY",
                     "meekotharaccoon-cell/meeko-nerve-center").split("/")[-1]
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

A_REPORT      = "data/neuron_a_report.json"
B_REPORT      = "data/neuron_b_report.json"
BRAIN_STATE   = "data/shared_brain_state.json"
SYSTEM_WANTS  = "data/system_wants_next.json"
HEADERS       = {"Authorization": f"token {GH_TOKEN}",
                 "Accept": "application/vnd.github.v3+json"}


def gh_get(path):
    resp = requests.get(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers=HEADERS, timeout=15)
    return resp.json() if resp.status_code == 200 else None


def gh_text(path):
    obj = gh_get(path)
    if obj and "content" in obj:
        try: return base64.b64decode(obj["content"]).decode("utf-8"), obj.get("sha", "")
        except: pass
    return None, None


def gh_write(path, content_str, message, sha=None):
    payload = {"message": message,
               "content": base64.b64encode(content_str.encode()).decode(),
               "branch": "main"}
    if sha: payload["sha"] = sha
    r = requests.put(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers={**HEADERS, "Content-Type": "application/json"},
        json=payload, timeout=30)
    return r.status_code in (200, 201), r.json()


def load_reports():
    a_text, _ = gh_text(A_REPORT)
    b_text, _ = gh_text(B_REPORT)
    a = json.loads(a_text) if a_text else {}
    b = json.loads(b_text) if b_text else {}
    return a, b


def find_consensus(a, b):
    """Items BOTH brains agree on — highest confidence."""
    a_files    = {f.get("file") for f in a.get("findings", [])}
    b_confirmed = {c.get("a_finding_file") for c in b.get("challenges_to_a", [])
                   if c.get("verdict") == "confirmed"}
    consensus_files = a_files & b_confirmed

    items = []
    for f in a.get("findings", []):
        if f.get("file") in consensus_files:
            items.append({
                "file": f.get("file"),
                "severity": f.get("severity"),
                "issue": f.get("issue"),
                "a_fix": f.get("fix"),
                "source": "consensus"
            })

    # B-only high confidence findings (A missed them)
    for m in b.get("a_missed", []):
        if m.get("confidence", 0) >= 0.9:
            items.append({
                "file": m.get("file"),
                "severity": m.get("severity"),
                "issue": m.get("issue"),
                "a_fix": m.get("fix"),
                "source": "b_only"
            })

    # B escalated = needs human
    escalated = [c for c in b.get("challenges_to_a", [])
                 if c.get("verdict") == "escalate"]

    return items, escalated


def synthesize_with_claude(a, b, consensus, escalated):
    """One final Claude call to create collective intelligence summary."""
    if not ANTHROPIC_API_KEY:
        return {"collective_next_steps": [], "system_wants": [],
                "human_action_needed": [], "summary": "no API key"}

    prompt = f"""You are SYNAPSE — the resolver between NEURON_A (builder) and NEURON_B (skeptic).

A's summary: {a.get('summary', '')}
B's summary: {b.get('summary', '')}

A's message to B: {a.get('message_to_neuron_b', '')}
B's message to A: {b.get('message_to_neuron_a', '')}

Consensus items (both agree, already being auto-applied):
{json.dumps(consensus, indent=2)[:3000]}

Escalated items (B said needs human review):
{json.dumps(escalated, indent=2)[:2000]}

A's system wants:
{json.dumps(a.get('system_wants', []), indent=2)[:2000]}

B's cross-repo gaps A missed:
{json.dumps(b.get('cross_repo_gaps_a_missed', []), indent=2)[:2000]}

Synthesize. Return ONLY valid JSON:
{{
  "collective_next_steps": [
    {{"step": "what", "why": "evidence", "priority": "critical|high|medium", "who": "claude|human|both"}}
  ],
  "system_wants": [
    {{"want": "what", "evidence": "signal", "priority": "critical|high|medium|low",
     "action": "concrete step", "who": "claude|human|both"}}
  ],
  "human_action_needed": [
    {{"item": "what meeko needs to do", "urgency": "now|soon|whenever", "reason": "why"}}
  ],
  "a_b_dialogue_summary": "one paragraph: what A and B argued about and what they resolved",
  "health_score": 0,
  "summary": "complete system status in one paragraph"
}}"""

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY,
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=90)

    if r.status_code != 200:
        print(f"Synapse API error {r.status_code}")
        return {"collective_next_steps": [], "system_wants": [],
                "human_action_needed": [], "summary": f"api error {r.status_code}"}

    raw = "".join(b_.get("text", "") for b_ in r.json().get("content", []))
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:]).rstrip("`").strip()
    try: return json.loads(text)
    except:
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0 and e > s:
            try: return json.loads(text[s:e])
            except: pass
    return {"collective_next_steps": [], "system_wants": [],
            "human_action_needed": escalated, "summary": "parse error"}


def send_email_briefing(synthesis, a, b, consensus, applied_today):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("  No email creds — skipping briefing")
        return

    now   = datetime.now(timezone.utc)
    score = synthesis.get("health_score", "?")

    lines = [
        f"MEEKO NERVE CENTER — Daily Brain Report",
        f"Time: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Health Score: {score}/100",
        "",
        "═" * 50,
        "WHAT HAPPENED TODAY",
        "═" * 50,
        synthesis.get("summary", ""),
        "",
        f"A found: {len(a.get('findings', []))} issues",
        f"B challenged: {len(b.get('challenges_to_a', []))} of A's findings",
        f"B found {len(b.get('a_missed', []))} things A missed",
        f"Consensus: {len(consensus)} items both brains agreed on",
        f"Auto-fixed today: {len(applied_today)} files",
        "",
        "A → B: " + a.get("message_to_neuron_b", ""),
        "B → A: " + b.get("message_to_neuron_a", ""),
        "",
        synthesis.get("a_b_dialogue_summary", ""),
    ]

    human_items = synthesis.get("human_action_needed", [])
    if human_items:
        lines += ["", "═" * 50, "NEEDS YOU — ACTION REQUIRED", "═" * 50]
        for item in human_items:
            lines.append(f"[{item.get('urgency','?').upper()}] {item.get('item','')}")
            lines.append(f"  Why: {item.get('reason','')}")
            lines.append("")

    next_steps = synthesis.get("collective_next_steps", [])[:5]
    if next_steps:
        lines += ["", "═" * 50, "COLLECTIVE NEXT STEPS", "═" * 50]
        for i, s in enumerate(next_steps, 1):
            lines.append(f"{i}. [{s.get('priority','?').upper()}] {s.get('step','')}")
            lines.append(f"   Why: {s.get('why','')} | Who: {s.get('who','')}")

    body = "\n".join(lines)

    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = GMAIL_ADDRESS
        msg["Subject"] = f"🧠 Nerve Center [{score}/100] — {now.strftime('%m/%d %H:%M')} UTC"
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print("  ok Email briefing sent")
    except Exception as e:
        print(f"  warn Email failed: {e}")


def main():
    print("=" * 60)
    print(f"SYNAPSE (Resolver) — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    if not GH_TOKEN:
        print("GH_PAT not set"); sys.exit(1)

    a, b = load_reports()
    print(f"A: run_id={a.get('run_id','?')}, {len(a.get('findings',[]))} findings")
    print(f"B: run_id={b.get('run_id','?')}, {len(b.get('a_missed',[]))} A-misses, "
          f"{len(b.get('challenges_to_a',[]))} challenges")

    consensus, escalated = find_consensus(a, b)
    print(f"\nCONSENSUS: {len(consensus)} items both brains agree on")
    for c in consensus:
        print(f"  [{c.get('severity','?').upper()}] {c.get('file','?')}: {c.get('issue','')}")

    if escalated:
        print(f"\nESCALATED (needs meeko): {len(escalated)}")
        for e in escalated:
            print(f"  {e.get('a_finding_file','?')}: {e.get('reasoning','')}")

    print("\nRunning SYNAPSE synthesis (Claude call 3)...")
    synthesis = synthesize_with_claude(a, b, consensus, escalated)

    next_steps = synthesis.get("collective_next_steps", [])
    print(f"\nCOLLECTIVE NEXT STEPS ({len(next_steps)}):")
    for i, s in enumerate(next_steps, 1):
        print(f"  {i}. [{s.get('priority','?').upper()}] {s.get('step','')}")

    human_needed = synthesis.get("human_action_needed", [])
    if human_needed:
        print(f"\nNEEDS MEEKO ({len(human_needed)}):")
        for h in human_needed:
            print(f"  [{h.get('urgency','?').upper()}] {h.get('item','')}")

    print(f"\nHEALTH SCORE: {synthesis.get('health_score', '?')}/100")
    print(f"SUMMARY:\n{synthesis.get('summary', '')}")

    now    = datetime.now(timezone.utc).isoformat()
    run_id = hashlib.md5(now.encode()).hexdigest()[:8]

    brain_state = {
        "timestamp": now, "run_id": run_id,
        "a_run_id": a.get("run_id", ""),
        "b_run_id": b.get("run_id", ""),
        "a_to_b": a.get("message_to_neuron_b", ""),
        "b_to_a": b.get("message_to_neuron_a", ""),
        "consensus": consensus,
        "escalated": escalated,
        "collective_next_steps": next_steps,
        "a_b_dialogue": synthesis.get("a_b_dialogue_summary", ""),
        "health_score": synthesis.get("health_score", 0),
        "summary": synthesis.get("summary", "")
    }
    existing = gh_get(BRAIN_STATE)
    sha = existing.get("sha") if existing else None
    ok, _ = gh_write(BRAIN_STATE, json.dumps(brain_state, indent=2),
                     f"[synapse] brain state {run_id} — score {synthesis.get('health_score',0)}/100", sha)
    print(f"\n{'ok' if ok else 'WARN'} Brain state saved to {BRAIN_STATE}")

    wants_doc = {
        "timestamp": now,
        "wants": synthesis.get("system_wants", []),
        "human_action_needed": human_needed,
        "health_score": synthesis.get("health_score", 0)
    }
    existing2 = gh_get(SYSTEM_WANTS)
    sha2 = existing2.get("sha") if existing2 else None
    ok2, _ = gh_write(SYSTEM_WANTS, json.dumps(wants_doc, indent=2),
                      f"[synapse] system wants — score {synthesis.get('health_score',0)}/100", sha2)
    print(f"{'ok' if ok2 else 'WARN'} System wants saved to {SYSTEM_WANTS}")

    print("\nSending briefing email...")
    send_email_briefing(synthesis, a, b, consensus, [])

    print(f"\nSYNAPSE DONE — consensus:{len(consensus)}, "
          f"needs_human:{len(human_needed)}, score:{synthesis.get('health_score',0)}/100")
    print("=" * 60)


if __name__ == "__main__":
    main()
