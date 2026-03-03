#!/usr/bin/env python3
"""
NEURON_A — The Builder Brain
============================
First Claude pass. Optimistic, solution-oriented, comprehensive.
Reads the ENTIRE system across ALL repos and finds what needs fixing.
Writes a structured report and a direct message to NEURON_B.

NEURON_B will challenge everything this produces.
That tension is the intelligence.

Required: ANTHROPIC_API_KEY, GH_PAT
"""
import os, sys, json, base64, hashlib, requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GH_TOKEN          = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
REPO_OWNER        = os.environ.get("GITHUB_REPOSITORY_OWNER", "meekotharaccoon-cell")
REPO_NAME         = os.environ.get("GITHUB_REPOSITORY",
                    "meekotharaccoon-cell/meeko-nerve-center").split("/")[-1]
NOTION_TOKEN      = os.environ.get("NOTION_TOKEN", "")
DIRECTIVES_PAGE   = os.environ.get("NOTION_DIRECTIVES_PAGE_ID", "")

REPORT_PATH = "data/neuron_a_report.json"
HEADERS     = {"Authorization": f"token {GH_TOKEN}",
               "Accept": "application/vnd.github.v3+json"}


def gh_get(path, repo=None):
    r = repo or f"{REPO_OWNER}/{REPO_NAME}"
    resp = requests.get(f"https://api.github.com/repos/{r}/contents/{path}",
                        headers=HEADERS, timeout=15)
    return resp.json() if resp.status_code == 200 else None


def gh_text(path, repo=None):
    obj = gh_get(path, repo)
    if obj and "content" in obj:
        try: return base64.b64decode(obj["content"]).decode("utf-8"), obj.get("sha", "")
        except: pass
    return None, None


def gh_ls(path, repo=None):
    r = repo or f"{REPO_OWNER}/{REPO_NAME}"
    resp = requests.get(f"https://api.github.com/repos/{r}/contents/{path}",
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


def list_all_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{REPO_OWNER}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "sort": "updated"},
            timeout=15)
        if r.status_code != 200: break
        batch = r.json()
        if not batch: break
        repos.extend(batch)
        if len(batch) < 100: break
        page += 1
    return repos


def read_repo_snapshot(repo_full_name):
    snap = {}
    for p in ["README.md", "STATUS.md", "wiring_status.json"]:
        t, _ = gh_text(p, repo_full_name)
        if t: snap[f"{repo_full_name}/{p}"] = t[:2000]
    return snap


def collect_context():
    ctx = {}
    print("NEURON_A reading full system...")

    for p in ["README.md", "STATUS.md", "mycelium/WIRING_MAP.md",
              "data/reminders.json", "data/neuron_b_report.json",
              "data/shared_brain_state.json", "data/system_wants_next.json",
              "data/workflow_health.json", "data/open_loops.json",
              "data/system_manifest.json", "wiring_status.json"]:
        t, _ = gh_text(p)
        if t: ctx[p] = t[:5000]; print(f"  ok {p}")

    for wf in gh_ls(".github/workflows"):
        if wf.get("type") == "file" and wf["name"].endswith(".yml"):
            t, _ = gh_text(wf["path"])
            if t: ctx[wf["path"]] = t[:2000]

    scripts = gh_ls("mycelium")
    ctx["_scripts"] = json.dumps([s["name"] for s in scripts
                                   if s.get("type") == "file"])
    for p in ["mycelium/wiring_hub.py", "mycelium/ORCHESTRATOR.py",
              "mycelium/email_optin_guard.py", "mycelium/email_gateway.py",
              "mycelium/self_healer.py", "mycelium/self_healer_v2.py",
              "mycelium/master_controller.py", "mycelium/grant_outreach.py",
              "mycelium/revenue_router.py", "mycelium/evolve.py",
              "mycelium/network_node.py", "mycelium/perpetual_builder.py",
              "mycelium/diagnostics.py", "mycelium/loop_closer.py"]:
        if p not in ctx:
            t, _ = gh_text(p)
            if t: ctx[p] = t[:4000]; print(f"  ok {p}")

    for di in gh_ls("data"):
        if di.get("type") == "file" and di["name"].endswith(".json"):
            t, _ = gh_text(di["path"])
            if t and len(t) < 3000: ctx[di["path"]] = t

    print("  Scanning all repos for cross-repo context...")
    all_repos = list_all_repos()
    ctx["_all_repos"] = json.dumps([r["full_name"] for r in all_repos])
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(read_repo_snapshot, r["full_name"]): r["full_name"]
                   for r in all_repos if r["full_name"] != f"{REPO_OWNER}/{REPO_NAME}"}
        for future in as_completed(futures):
            snap = future.result()
            ctx.update(snap)
            if snap: print(f"  ok repo: {futures[future]}")

    if NOTION_TOKEN and DIRECTIVES_PAGE:
        try:
            nr = requests.get(
                f"https://api.notion.com/v1/blocks/{DIRECTIVES_PAGE}/children",
                headers={"Authorization": f"Bearer {NOTION_TOKEN}",
                         "Notion-Version": "2022-06-28"}, timeout=10)
            if nr.status_code == 200:
                texts = []
                for b in nr.json().get("results", [])[:50]:
                    bt = b.get("type", "")
                    for rt in b.get(bt, {}).get("rich_text", []):
                        texts.append(rt.get("plain_text", ""))
                ctx["notion://DIRECTIVES"] = "\n".join(texts)[:4000]
                print("  ok Notion DIRECTIVES")
        except Exception as e:
            print(f"  warn Notion: {e}")

    return ctx


SYSTEM_PROMPT = """You are NEURON_A — the builder intelligence of the meeko-nerve-center.

You are OPTIMISTIC and SOLUTION-ORIENTED. Your job:
1. Read the full system state across ALL repos
2. Find REAL problems: broken wires, bad references, missing env vars,
   scripts nothing calls, credentials nothing uses, dead code paths,
   duplicate logic, missing connections between repos
3. Propose SPECIFIC file fixes
4. Write a direct message to NEURON_B who will challenge everything you say

System context:
- meeko-nerve-center: autonomous revenue + humanitarian tech
- Mission: revenue → 70% to PCRF refugee fund, 30% ops
- Builder: meeko (raccoon energy, ADHD, solo)
- ALL connected repos are part of one system — see cross-repo gaps

HARD RULES:
- Never cold email without email_optin_guard.py
- Never duplicate sends
- Never expose secrets
- Self-emails to GMAIL_ADDRESS are fine
- Revenue: 70% PCRF, 30% ops

Return ONLY valid JSON:
{
  "timestamp": "ISO8601",
  "findings": [
    {
      "severity": "critical|warning|info",
      "file": "path/to/file or repo-name",
      "issue": "exact problem description",
      "fix": "exact fix description",
      "confidence": 0.0-1.0
    }
  ],
  "cross_repo_gaps": [
    {
      "repos": ["repo1", "repo2"],
      "gap": "what connection is missing",
      "fix": "how to wire them"
    }
  ],
  "file_changes": [
    {
      "path": "path/to/file",
      "content": "COMPLETE file content — never truncate",
      "commit_message": "fix: description",
      "confidence": 0.0-1.0
    }
  ],
  "system_wants": [
    {
      "want": "what the system needs",
      "evidence": "data signal",
      "priority": "critical|high|medium|low",
      "action": "concrete next step",
      "who": "claude|human|both"
    }
  ],
  "next_priorities": ["p1", "p2", "p3"],
  "message_to_neuron_b": "direct message to B — what you want B to scrutinize most",
  "summary": "one paragraph: what you found and what you're proposing"
}"""


def build_message(ctx):
    all_repos = json.loads(ctx.get("_all_repos", "[]"))
    scripts = json.loads(ctx.get("_scripts", "[]"))
    parts = [
        f"meeko system state — {datetime.now(timezone.utc).isoformat()}\n",
        f"Repos in account: {len(all_repos)} — {', '.join(all_repos[:10])}\n",
        f"Scripts in mycelium/: {len(scripts)}\n\n"
    ]
    for path, content in ctx.items():
        if not path.startswith("_"):
            parts.append(f"=== {path} ===\n{content}\n\n")
    return "".join(parts)[:120000]


def call_claude(message):
    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY not set"); sys.exit(1)
    print("NEURON_A calling Claude API...")
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
    return {"findings": [], "file_changes": [], "system_wants": [], "summary": "parse error"}


def apply_fixes(result, only_high_confidence=True):
    applied, failed, skipped = [], [], []
    for change in result.get("file_changes", []):
        path    = change.get("path", "")
        content = change.get("content", "")
        msg     = change.get("commit_message", f"fix: {path}")
        conf    = change.get("confidence", 0.5)
        if only_high_confidence and conf < 0.85:
            skipped.append(path)
            print(f"  skip {path} (confidence {conf:.2f} < 0.85 — B will review)")
            continue
        if not path or not content: continue
        print(f"  writing {path} (confidence {conf:.2f})")
        existing = gh_get(path)
        sha = existing.get("sha") if existing else None
        ok, resp = gh_write(path, content, f"[neuron-a] {msg}", sha)
        if ok: applied.append(path); print(f"    ok")
        else: failed.append(path); print(f"    fail: {resp.get('message', '?')}")
    return applied, failed, skipped


def main():
    print("=" * 60)
    print(f"NEURON_A (Builder) — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    if not GH_TOKEN:
        print("GH_PAT not set"); sys.exit(1)

    ctx    = collect_context()
    msg    = build_message(ctx)
    print(f"\nContext: {len(ctx)} sections, {len(msg):,} chars\n")

    raw    = call_claude(msg)
    result = parse(raw)

    findings = result.get("findings", [])
    print(f"\nFINDINGS ({len(findings)}):")
    for f in findings:
        icon = {"critical": "[CRIT]", "warning": "[WARN]"}.get(f.get("severity", ""), "[INFO]")
        print(f"  {icon} {f.get('file', '?')}: {f.get('issue', '')} [conf:{f.get('confidence',0):.2f}]")

    gaps = result.get("cross_repo_gaps", [])
    if gaps:
        print(f"\nCROSS-REPO GAPS ({len(gaps)}):")
        for g in gaps:
            print(f"  {g.get('repos', [])} → {g.get('gap', '')}")

    changes = result.get("file_changes", [])
    print(f"\nAPPLYING high-confidence fixes ({len(changes)} proposed)...")
    applied, failed, skipped = apply_fixes(result, only_high_confidence=True)

    wants = result.get("system_wants", [])
    print(f"\nSYSTEM WANTS ({len(wants)}):")
    for w in wants:
        print(f"  [{w.get('priority', '?').upper()}] {w.get('want', '')}")

    print(f"\nMESSAGE TO NEURON_B:\n  {result.get('message_to_neuron_b', '')}")
    print(f"\nSUMMARY:\n{result.get('summary', '')}")

    now    = datetime.now(timezone.utc).isoformat()
    run_id = hashlib.md5(now.encode()).hexdigest()[:8]
    report = {
        "timestamp": now, "run_id": run_id,
        "brain": "NEURON_A",
        "findings": findings,
        "cross_repo_gaps": gaps,
        "file_changes_proposed": changes,
        "files_applied": applied,
        "files_skipped_for_b": skipped,
        "files_failed": failed,
        "system_wants": wants,
        "next_priorities": result.get("next_priorities", []),
        "message_to_neuron_b": result.get("message_to_neuron_b", ""),
        "summary": result.get("summary", "")
    }
    existing = gh_get(REPORT_PATH)
    sha = existing.get("sha") if existing else None
    ok, _ = gh_write(REPORT_PATH, json.dumps(report, indent=2),
                     f"[neuron-a] report {run_id} — {len(findings)} findings", sha)
    print(f"\n{'ok' if ok else 'WARN'} Report saved to {REPORT_PATH}")
    print(f"DONE — {len(applied)} applied, {len(skipped)} deferred to B, {len(failed)} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
