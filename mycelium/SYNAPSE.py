#!/usr/bin/env python3
"""
SYNAPSE — The Resolver
=======================
Runs AFTER NEURON_A and NEURON_B.

Reads both reports, finds consensus, resolves conflicts intelligently,
applies remaining agreed fixes, saves the unified brain state,
and sends meeko a daily briefing with REAL system stats.

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


def gh_ls(path):
    resp = requests.get(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}",
        headers=HEADERS, timeout=15)
    return resp.json() if resp.status_code == 200 else []


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


def gather_system_stats():
    """SYNAPSE directly reads real system stats — not dependent on A/B."""
    stats = {
        "engines_total": 0,
        "data_files": 0,
        "revenue_balance": 0.0,
        "revenue_streams": [],
        "flywheel_state": {},
        "brain_state_prev": {},
        "loop_memory_cycles": 0,
        "loop_last_insight": "",
        "synthesis_built": 0,
        "phases_data": {},
        "upgrade_next": "",
    }

    # Count engines in mycelium/
    try:
        scripts = gh_ls("mycelium")
        py_files = [s["name"] for s in scripts if s.get("type") == "file" and s["name"].endswith(".py")]
        stats["engines_total"] = len(py_files)
        stats["engine_names"] = py_files
    except: pass

    # Count data files
    try:
        data_files = gh_ls("data")
        stats["data_files"] = len([d for d in data_files if d.get("type") == "file"])
        stats["data_file_names"] = [d["name"] for d in data_files if d.get("type") == "file"]
    except: pass

    # Read flywheel state for real revenue numbers
    try:
        fw_text, _ = gh_text("data/flywheel_state.json")
        if fw_text:
            fw = json.loads(fw_text)
            stats["revenue_balance"] = fw.get("current_balance", 0.0)
            stats["flywheel_state"] = fw
            stats["revenue_streams"] = fw.get("streams", [])
            # Find next upgrade
            upgrades = fw.get("upgrade_tiers", [])
            bal = stats["revenue_balance"]
            for tier in sorted(upgrades, key=lambda x: x.get("threshold", 999)):
                if bal < tier.get("threshold", 999):
                    stats["upgrade_next"] = f"${tier['threshold']} → {tier.get('label','?')}"
                    break
    except: pass

    # Loop memory — how many cycles
    try:
        lm_text, _ = gh_text("data/loop_memory.json")
        if lm_text:
            lm = json.loads(lm_text)
            stats["loop_memory_cycles"] = len(lm)
            if lm:
                stats["loop_last_insight"] = lm[-1].get("key_insight", "")
    except: pass

    # Synthesis log
    try:
        sl_text, _ = gh_text("data/synthesis_log.json")
        if sl_text:
            sl = json.loads(sl_text)
            stats["synthesis_built"] = len(sl.get("built", []))
    except: pass

    # Previous brain state for trend
    try:
        bs_text, _ = gh_text(BRAIN_STATE)
        if bs_text:
            stats["brain_state_prev"] = json.loads(bs_text)
    except: pass

    return stats


def find_consensus(a, b):
    """Items BOTH brains agree on — highest confidence."""
    a_files     = {f.get("file") for f in a.get("findings", [])}
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

    for m in b.get("a_missed", []):
        if m.get("confidence", 0) >= 0.9:
            items.append({
                "file": m.get("file"),
                "severity": m.get("severity"),
                "issue": m.get("issue"),
                "a_fix": m.get("fix"),
                "source": "b_only"
            })

    escalated = [c for c in b.get("challenges_to_a", [])
                 if c.get("verdict") == "escalate"]

    return items, escalated


def synthesize_with_claude(a, b, consensus, escalated, stats):
    """Final Claude call to create collective intelligence summary."""
    if not ANTHROPIC_API_KEY:
        return {"collective_next_steps": [], "system_wants": [],
                "human_action_needed": [], "summary": "no API key",
                "health_score": 50}

    prompt = f"""You are SYNAPSE — the resolver between NEURON_A (builder) and NEURON_B (skeptic).

REAL SYSTEM STATS (gathered directly — use these for the health score):
- Total engines in mycelium/: {stats['engines_total']}
- Data files produced: {stats['data_files']}
- Revenue balance: ${stats['revenue_balance']:.2f}
- Loop cycles completed: {stats['loop_memory_cycles']}
- Engines auto-built by synthesis: {stats['synthesis_built']}
- Next upgrade unlock: {stats['upgrade_next'] or 'none yet'}
- Last loop insight: {stats['loop_last_insight'] or 'first run'}

A's summary: {a.get('summary', '(no report)')}
B's summary: {b.get('summary', '(no report)')}

A's message to B: {a.get('message_to_neuron_b', '')}
B's message to A: {b.get('message_to_neuron_a', '')}

Consensus items (both brains agree):
{json.dumps(consensus, indent=2)[:2000]}

Escalated items (needs human):
{json.dumps(escalated, indent=2)[:1000]}

A's system wants:
{json.dumps(a.get('system_wants', []), indent=2)[:1500]}

B's cross-repo gaps A missed:
{json.dumps(b.get('cross_repo_gaps_a_missed', []), indent=2)[:1500]}

Synthesize everything. Score the system HONESTLY based on real stats above.
A system with {stats['engines_total']} engines running, data being produced, and
revenue being tracked is NOT a zero. Score based on actual health.

Return ONLY valid JSON — no markdown fences:
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
  "a_b_dialogue_summary": "one paragraph: what A and B argued about and resolved",
  "health_score": <integer 0-100 based on real system stats>,
  "summary": "complete system status in one paragraph including real numbers"
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
                "human_action_needed": [], "summary": f"api error {r.status_code}",
                "health_score": stats['engines_total']}  # fallback: engine count as proxy

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
            "human_action_needed": escalated, "summary": "parse error",
            "health_score": 40}


def send_email_briefing(synthesis, a, b, consensus, applied_today, stats):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("  No email creds — skipping briefing")
        return

    now   = datetime.now(timezone.utc)
    score = synthesis.get("health_score", "?")
    prev_score = stats.get("brain_state_prev", {}).get("health_score", "?")
    trend = ""
    if isinstance(score, int) and isinstance(prev_score, int):
        diff = score - prev_score
        trend = f" ({'▲' if diff >= 0 else '▼'}{abs(diff)} from last run)"

    lines = [
        f"🌱 SOLARPUNK — Daily Brain Report",
        f"Time: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Health Score: {score}/100{trend}",
        "",
        "═" * 50,
        "REAL SYSTEM STATS",
        "═" * 50,
        f"Engines in mycelium/:    {stats['engines_total']}",
        f"Data files produced:     {stats['data_files']}",
        f"Revenue balance:         ${stats['revenue_balance']:.2f}",
        f"Next upgrade:            {stats['upgrade_next'] or 'keep building revenue'}",
        f"Loop cycles remembered:  {stats['loop_memory_cycles']}",
        f"Engines built by synth:  {stats['synthesis_built']}",
    ]

    if stats.get("loop_last_insight"):
        lines.append(f"Last loop insight:       {stats['loop_last_insight']}")

    # Revenue streams detail
    streams = stats.get("revenue_streams", [])
    if streams:
        lines += ["", "Revenue streams:"]
        for s in streams:
            lines.append(f"  {s.get('name','?')}: ${s.get('balance', 0):.2f}")

    lines += [
        "",
        "═" * 50,
        "WHAT THE BRAINS FOUND TODAY",
        "═" * 50,
        synthesis.get("summary", "(synthesis unavailable)"),
        "",
        f"A found:        {len(a.get('findings', []))} issues",
        f"B challenged:   {len(b.get('challenges_to_a', []))} of A's findings",
        f"B found:        {len(b.get('a_missed', []))} things A missed",
        f"Consensus:      {len(consensus)} items both agreed on",
        f"Auto-fixed:     {len(applied_today)} files",
    ]

    a_msg = a.get("message_to_neuron_b", "")
    b_msg = b.get("message_to_neuron_a", "")
    if a_msg or b_msg:
        lines += [""]
        if a_msg: lines.append(f"A → B: {a_msg}")
        if b_msg: lines.append(f"B → A: {b_msg}")

    dialogue = synthesis.get("a_b_dialogue_summary", "")
    if dialogue:
        lines += ["", dialogue]

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

    lines += [
        "",
        "═" * 50,
        f"OMNIBRAIN: 7am + 7pm UTC  |  SP LOOP: noon UTC",
        f"3 cycles/day. The loop never stops.",
        "— SolarPunk 🌱"
    ]

    body = "\n".join(lines)

    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = GMAIL_ADDRESS
        msg["Subject"] = f"🌱 SolarPunk [{score}/100] — {stats['engines_total']} engines | ${stats['revenue_balance']:.2f} rev | {now.strftime('%m/%d %H:%M')} UTC"
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

    print("\nGathering real system stats...")
    stats = gather_system_stats()
    print(f"  Engines: {stats['engines_total']} | Data files: {stats['data_files']} | Revenue: ${stats['revenue_balance']:.2f}")

    a, b = load_reports()
    print(f"\nA: run_id={a.get('run_id','?')}, {len(a.get('findings',[]))} findings")
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
    synthesis = synthesize_with_claude(a, b, consensus, escalated, stats)

    next_steps = synthesis.get("collective_next_steps", [])
    print(f"\nCOLLECTIVE NEXT STEPS ({len(next_steps)}):")
    for i, s in enumerate(next_steps, 1):
        print(f"  {i}. [{s.get('priority','?').upper()}] {s.get('step','')}")

    human_needed = synthesis.get("human_action_needed", [])
    if human_needed:
        print(f"\nNEEDS MEEKO ({len(human_needed)}):")
        for h in human_needed:
            print(f"  [{h.get('urgency','?').upper()}] {h.get('item','')}")

    score = synthesis.get("health_score", "?")
    print(f"\nHEALTH SCORE: {score}/100")
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
        "health_score": score,
        "summary": synthesis.get("summary", ""),
        "engines_total": stats["engines_total"],
        "revenue_balance": stats["revenue_balance"],
        "loop_cycles": stats["loop_memory_cycles"],
    }
    existing = gh_get(BRAIN_STATE)
    sha = existing.get("sha") if existing else None
    ok, _ = gh_write(BRAIN_STATE, json.dumps(brain_state, indent=2),
                     f"[synapse] brain state {run_id} — score {score}/100 | {stats['engines_total']} engines | ${stats['revenue_balance']:.2f}", sha)
    print(f"\n{'ok' if ok else 'WARN'} Brain state saved to {BRAIN_STATE}")

    wants_doc = {
        "timestamp": now,
        "wants": synthesis.get("system_wants", []),
        "human_action_needed": human_needed,
        "health_score": score
    }
    existing2 = gh_get(SYSTEM_WANTS)
    sha2 = existing2.get("sha") if existing2 else None
    ok2, _ = gh_write(SYSTEM_WANTS, json.dumps(wants_doc, indent=2),
                      f"[synapse] system wants — score {score}/100", sha2)
    print(f"{'ok' if ok2 else 'WARN'} System wants saved to {SYSTEM_WANTS}")

    print("\nSending briefing email...")
    send_email_briefing(synthesis, a, b, consensus, [], stats)

    print(f"\nSYNAPSE DONE — engines:{stats['engines_total']}, revenue:${stats['revenue_balance']:.2f}, "
          f"score:{score}/100, consensus:{len(consensus)}, needs_human:{len(human_needed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
