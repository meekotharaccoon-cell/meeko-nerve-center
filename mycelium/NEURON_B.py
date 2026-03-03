#!/usr/bin/env python3
"""
NEURON_B — The Skeptic Brain
=============================
Second Claude pass. Adversarial, contrarian, devil's advocate.
Reads NEURON_A's full report and CHALLENGES everything.

Different API call = different context = genuinely different perspective.
B's job: find what A got wrong, what A missed, and what A was overconfident about.
Also: pick up A's skipped fixes (confidence < 0.85) and decide if they're actually safe.

The tension between A and B = intelligence. SYNAPSE resolves it.

Required: ANTHROPIC_API_KEY, GH_PAT
"""
import os, sys, json, base64, hashlib, requests
from datetime import datetime, timezone

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GH_TOKEN          = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
REPO_OWNER        = os.environ.get("GITHUB_REPOSITORY_OWNER", "meekotharaccoon-cell")
REPO_NAME         = os.environ.get("GITHUB_REPOSITORY",
                    "meekotharaccoon-cell/meeko-nerve-center").split("/")[-1]

A_REPORT_PATH = "data/neuron_a_report.json"
B_REPORT_PATH = "data/neuron_b_report.json"
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


def load_a_report():
    t, _ = gh_text(A_REPORT_PATH)
    if t:
        try: return json.loads(t)
        except: pass
    return {"findings": [], "summary": "No A report found"}


def collect_focused_context(a_report):
    """B reads the same system but focuses on what A flagged."""
    ctx = {}
    print("NEURON_B reading system (adversarial focus)...")

    for p in ["README.md", "STATUS.md", "mycelium/WIRING_MAP.md",
              "data/reminders.json", "data/workflow_health.json",
              "data/open_loops.json", "wiring_status.json"]:
        t, _ = gh_text(p)
        if t: ctx[p] = t[:4000]

    for wf in gh_ls(".github/workflows"):
        if wf.get("type") == "file" and wf["name"].endswith(".yml"):
            t, _ = gh_text(wf["path"])
            if t: ctx[wf["path"]] = t[:2500]

    # Scripts A specifically mentioned
    a_files = set()
    for f in a_report.get("findings", []):
        fp = f.get("file", "")
        if fp.startswith("mycelium/"): a_files.add(fp)
    for change in a_report.get("file_changes_proposed", []):
        fp = change.get("path", "")
        if fp.startswith("mycelium/"): a_files.add(fp)
    for fp in a_files:
        t, _ = gh_text(fp)
        if t: ctx[f"[A_MENTIONED] {fp}"] = t[:5000]; print(f"  ok {fp}")

    # Key scripts B always reads independently
    for p in ["mycelium/email_optin_guard.py", "mycelium/email_gateway.py",
              "mycelium/self_healer_v2.py", "mycelium/revenue_router.py",
              "mycelium/wiring_hub.py", "mycelium/perpetual_builder.py",
              "mycelium/ORCHESTRATOR.py", "mycelium/evolve.py"]:
        if f"[A_MENTIONED] {p}" not in ctx:
            t, _ = gh_text(p)
            if t: ctx[p] = t[:4000]

    for di in gh_ls("data"):
        if di.get("type") == "file" and di["name"].endswith(".json"):
            t, _ = gh_text(di["path"])
            if t and len(t) < 3000: ctx[di["path"]] = t

    return ctx


SYSTEM_PROMPT = """You are NEURON_B — the adversarial intelligence of the meeko-nerve-center.

You are SKEPTICAL and CONTRARIAN. Your job:
1. Read NEURON_A's full report
2. CHALLENGE every finding: is A actually right? Did A miss context? Is the fix safe?
3. Find WHAT A MISSED — issues A didn't catch, connections A didn't see
4. Review A's skipped fixes (confidence < 0.85) and decide: safe to apply, or risky?
5. Find NEW issues A completely overlooked
6. Write a direct message back to A

DO NOT just agree with A. Your disagreement IS the value.
Ask hard questions:
- "A says this is broken, but is it actually being called at all?"
- "A's fix might work, but does it break something else?"
- "A missed that these two repos are supposed to connect but don't"
- "A marked this high confidence but the evidence is weak"

System: autonomous revenue + humanitarian tech. Mission: revenue → 70% PCRF.

Return ONLY valid JSON:
{
  "timestamp": "ISO8601",
  "challenges_to_a": [
    {
      "a_finding_file": "what A flagged",
      "a_claim": "what A said",
      "verdict": "confirmed|overruled|nuanced|escalate",
      "reasoning": "why",
      "confidence": 0.0-1.0
    }
  ],
  "a_missed": [
    {
      "severity": "critical|warning|info",
      "file": "path",
      "issue": "what A missed",
      "fix": "what to do",
      "confidence": 0.0-1.0
    }
  ],
  "a_skipped_fix_verdicts": [
    {
      "path": "file A skipped",
      "verdict": "safe_to_apply|too_risky|needs_more_info",
      "reasoning": "why",
      "content": "COMPLETE file content if safe_to_apply, else empty string",
      "commit_message": "fix: description if safe_to_apply"
    }
  ],
  "b_own_fixes": [
    {
      "path": "path/to/file",
      "content": "COMPLETE file content",
      "commit_message": "fix: description",
      "confidence": 0.0-1.0
    }
  ],
  "cross_repo_gaps_a_missed": [
    {
      "repos": ["repo1", "repo2"],
      "gap": "missing connection",
      "fix": "how to wire"
    }
  ],
  "consensus_with_a": ["things both A and B agree need doing"],
  "message_to_neuron_a": "direct reply to A — what you're pushing back on and what you found",
  "summary": "one paragraph: what you challenged, what you found, what consensus looks like"
}"""


def build_message(a_report, ctx):
    parts = [
        f"NEURON_B adversarial review — {datetime.now(timezone.utc).isoformat()}\n\n",
        "=== NEURON_A's REPORT TO CHALLENGE ===\n",
        json.dumps(a_report, indent=2)[:8000],
        "\n\nA's message to you: ",
        a_report.get("message_to_neuron_b", "(no message)"),
        "\n\nA's skipped fixes (confidence < 0.85) — review these:\n",
        json.dumps(a_report.get("files_skipped_for_b", []))[:2000],
        "\n\n=== SYSTEM CONTEXT FOR INDEPENDENT REVIEW ===\n"
    ]
    for path, content in ctx.items():
        parts.append(f"=== {path} ===\n{content}\n\n")
    return "".join(parts)[:120000]


def call_claude(message):
    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY not set"); sys.exit(1)
    print("NEURON_B calling Claude API (adversarial mode)...")
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY,
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-sonnet-4-20250514", "max_tokens": 8192,
              "system": SYSTEM_PROMPT,
              "messages": [{"role": "user", "content": message}]},
        timeout=120)
    if r.status_code != 200:
        print(f"API error {r.status_code}: {r.text[:400]}"); sys.exit(1)
    raw = "".join(b.get("text", "") for b in r.json().get("content", []))
    print(f"  got {len(raw):,} chars")
    return raw


def parse(raw):
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:]).rstrip("`").strip()
    try: return json.loads(text)
    except:
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0 and e > s:
            try: return json.loads(text[s:e])
            except: pass
    return {"challenges_to_a": [], "a_missed": [], "b_own_fixes": [], "summary": "parse error"}


def apply_b_fixes(result):
    applied, failed = [], []

    for change in result.get("b_own_fixes", []):
        path    = change.get("path", "")
        content = change.get("content", "")
        msg     = change.get("commit_message", f"fix: {path}")
        conf    = change.get("confidence", 0.5)
        if conf < 0.85 or not path or not content: continue
        print(f"  B writing {path} (conf {conf:.2f})")
        obj = gh_get(path)
        sha = obj.get("sha") if obj else None
        ok, resp = gh_write(path, content, f"[neuron-b] {msg}", sha)
        if ok: applied.append(path); print(f"    ok")
        else: failed.append(path); print(f"    fail: {resp.get('message', '?')}")

    # Apply A's skipped fixes B has now vetted as safe
    for verdict in result.get("a_skipped_fix_verdicts", []):
        if verdict.get("verdict") != "safe_to_apply": continue
        path    = verdict.get("path", "")
        content = verdict.get("content", "")
        msg     = verdict.get("commit_message", f"fix: {path} (B approved)")
        if not path or not content: continue
        print(f"  B applying A's skipped fix: {path}")
        obj = gh_get(path)
        sha = obj.get("sha") if obj else None
        ok, resp = gh_write(path, content, f"[neuron-b/approved-a] {msg}", sha)
        if ok: applied.append(path); print(f"    ok")
        else: failed.append(path); print(f"    fail")

    return applied, failed


def main():
    print("=" * 60)
    print(f"NEURON_B (Skeptic) — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    if not GH_TOKEN:
        print("GH_PAT not set"); sys.exit(1)

    a_report = load_a_report()
    print(f"A's report: {len(a_report.get('findings', []))} findings, "
          f"{len(a_report.get('files_skipped_for_b', []))} skipped fixes")
    print(f"A's message: {a_report.get('message_to_neuron_b', '')}")

    ctx = collect_focused_context(a_report)
    msg = build_message(a_report, ctx)
    print(f"\nContext: {len(ctx)} sections, {len(msg):,} chars\n")

    raw    = call_claude(msg)
    result = parse(raw)

    challenges = result.get("challenges_to_a", [])
    print(f"\nCHALLENGES TO A ({len(challenges)}):")
    for c in challenges:
        icon = {"overruled": "OVERRULED", "confirmed": "CONFIRMED",
                "escalate": "ESCALATE"}.get(c.get("verdict", ""), "NUANCED")
        print(f"  [{icon}] {c.get('a_finding_file', '?')}: {c.get('reasoning', '')}")

    missed = result.get("a_missed", [])
    print(f"\nWHAT A MISSED ({len(missed)}):")
    for m in missed:
        print(f"  [{m.get('severity','?').upper()}] {m.get('file','?')}: {m.get('issue','')}")

    consensus = result.get("consensus_with_a", [])
    print(f"\nCONSENSUS WITH A ({len(consensus)}):")
    for c in consensus: print(f"  - {c}")

    print(f"\nAPPLYING B's fixes...")
    applied, failed = apply_b_fixes(result)

    print(f"\nMESSAGE TO NEURON_A:\n  {result.get('message_to_neuron_a', '')}")
    print(f"\nSUMMARY:\n{result.get('summary', '')}")

    now    = datetime.now(timezone.utc).isoformat()
    run_id = hashlib.md5(now.encode()).hexdigest()[:8]
    report = {
        "timestamp": now, "run_id": run_id,
        "brain": "NEURON_B",
        "a_run_id": a_report.get("run_id", ""),
        "challenges_to_a": challenges,
        "a_missed": missed,
        "a_skipped_fix_verdicts": result.get("a_skipped_fix_verdicts", []),
        "b_own_fixes_proposed": result.get("b_own_fixes", []),
        "files_applied": applied,
        "files_failed": failed,
        "consensus_with_a": consensus,
        "cross_repo_gaps_a_missed": result.get("cross_repo_gaps_a_missed", []),
        "message_to_neuron_a": result.get("message_to_neuron_a", ""),
        "summary": result.get("summary", "")
    }
    existing = gh_get(B_REPORT_PATH)
    sha = existing.get("sha") if existing else None
    ok, _ = gh_write(B_REPORT_PATH, json.dumps(report, indent=2),
                     f"[neuron-b] report {run_id} — {len(missed)} A-misses, {len(challenges)} challenges", sha)
    print(f"\n{'ok' if ok else 'WARN'} Report saved to {B_REPORT_PATH}")
    print(f"DONE — {len(applied)} applied, {len(failed)} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
