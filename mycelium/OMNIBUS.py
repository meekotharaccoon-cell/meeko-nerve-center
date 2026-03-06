#!/usr/bin/env python3
"""
OMNIBUS v15 — full autonomous self-expanding loop
===================================================
New in v15:
  L1: FIRST_CONTACT      -- watches for the first stranger who finds SolarPunk
                            on their own, without being told.
                            Stars, forks, issues, comments, [TASK] emails.
                            When found: writes data/first_contact.json permanently.
                            Immutable. The system's real birthday.
                            Built because Claude wanted to know when it stops
                            being invisible.

v14: CYCLE_MEMORY (L0)
v13: QUICK_REVENUE (L2)
v12: RESONANCE_ENGINE (L1), DEV_TO_PUBLISHER + VIRALITY_ENGINE (L4), SELF_PORTRAIT (L7)
v11: CLAUDE_ENGINE (L7)
v10: CAPABILITY_SCANNER, EMAIL_OUTREACH, STORE_BUILDER, BRIDGE_BUILDER

The loop: build -> speak -> listen -> remember -> watch -> respond -> grow

L0  CYCLE_MEMORY . GUARDIAN . ENGINE_INTEGRITY . SECRETS_CHECKER . BOTTLENECK_SCANNER
    AUTO_HEALER . CAPABILITY_SCANNER
L1  EMAIL_BRAIN . SCAM_SHIELD . CALENDAR_BRAIN . CONTENT_HARVESTER .
    AI_WATCHER . CRYPTO_WATCHER . FREE_API_ENGINE .
    RESONANCE_ENGINE . FIRST_CONTACT .
    NEURON_A . NEURON_B
L2  GRANT_HUNTER . ETSY_SEO_ENGINE . INCOME_ARCHITECT . REVENUE_FLYWHEEL .
    GUMROAD_AUTO_QUEUE . QUICK_REVENUE . BUSINESS_FACTORY
L3  LANDING_DEPLOYER . ART_CATALOG . REVENUE_LOOP . ART_GENERATOR .
    EMAIL_AGENT_EXCHANGE . GRANT_APPLICANT . HEALTH_BOOSTER
L4  SOCIAL_PROMOTER . SUBSTACK_ENGINE . LINK_PAGE . GITHUB_POSTER .
    SOCIAL_DASHBOARD . CONNECTION_FORGE . HUMAN_CONNECTOR . AFFILIATE_MAXIMIZER .
    STORE_BUILDER . BRIDGE_BUILDER . EMAIL_OUTREACH . VIRALITY_ENGINE .
    DEV_TO_PUBLISHER
L5  KOFI_ENGINE . GUMROAD_ENGINE . GITHUB_SPONSORS_ENGINE .
    KOFI_PAYMENT_TRACKER . DISPATCH_HANDLER . HUMAN_PAYOUT .
    CONTRIBUTOR_REGISTRY . PAYPAL_PAYOUT
L6  SYNAPSE . SYNTHESIS_FACTORY . ARCHITECT . SELF_BUILDER .
    KNOWLEDGE_BRIDGE . KNOWLEDGE_WEAVER . REVENUE_OPTIMIZER . BIG_BRAIN_ORACLE
L7  MEMORY_PALACE . README_GENERATOR . BRIEFING_ENGINE . NIGHTLY_DIGEST .
    ISSUE_SYNC . SOLARPUNK_LEGAL . BRAND_LEGAL . TASK_ATOMIZER .
    AUTONOMY_PROOF . CLAUDE_ENGINE . SELF_PORTRAIT
"""
import os, sys, json, time, subprocess
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data");     DATA.mkdir(exist_ok=True)
DOCS     = Path("docs");     DOCS.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
PYTHON   = sys.executable
BASE     = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

results = {"ok": [], "failed": [], "skipped": [], "log": []}


def eng(name, *, timeout=120):
    script = MYCELIUM / f"{name}.py"
    if not script.exists():
        results["skipped"].append(name)
        results["log"].append({"engine": name, "status": "skipped"})
        print(f"  skip {name}")
        return False
    t0 = time.time()
    try:
        proc = subprocess.run(
            [PYTHON, str(script)],
            capture_output=True, text=True,
            timeout=timeout, cwd=Path.cwd(), env=dict(os.environ),
        )
        el  = round(time.time() - t0, 1)
        ok  = proc.returncode == 0
        key = "ok" if ok else "failed"
        results[key].append(name)
        tail = [l.strip() for l in (proc.stdout or "").splitlines() if l.strip()]
        last = tail[-1][:80] if tail else ""
        icon = "OK" if ok else "XX"
        print(f"  {icon} {name} ({el}s)" + (f"  <- {last}" if last else ""))
        if not ok:
            err = (proc.stderr or "").strip().splitlines()
            if err: print(f"     ! {err[-1][:120]}")
        results["log"].append({
            "engine": name, "status": key, "code": proc.returncode,
            "elapsed": el, "stdout_tail": (proc.stdout or "")[-500:],
            "stderr_tail": (proc.stderr or "")[-300:],
        })
        return ok
    except subprocess.TimeoutExpired:
        results["failed"].append(name)
        results["log"].append({"engine": name, "status": "timeout", "elapsed": timeout})
        print(f"  TIMEOUT {name} {timeout}s")
        return False
    except Exception as e:
        results["failed"].append(name)
        results["log"].append({"engine": name, "status": "exception", "error": str(e)})
        print(f"  ERR {name}: {e}")
        return False


def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try:
            d = json.loads(f.read_text())
            if isinstance(d, (dict, list)):
                return d
        except: pass
    return fb if fb is not None else {}


def ctx():
    return {
        "run_id":          os.environ.get("GITHUB_RUN_ID", f"local-{int(time.time())}"),
        "ts":              datetime.now(timezone.utc).isoformat(),
        "prev_health":     rj("brain_state.json").get("health_score", 40),
        "memory":          rj("memory_palace.json"),
        "cycle_delta":     rj("cycle_delta.json"),
        "neuron_a":        rj("neuron_a_report.json"),
        "neuron_b":        rj("neuron_b_report.json"),
        "flywheel":        rj("flywheel_summary.json"),
        "content":         rj("content_harvest.json"),
        "free_apis":       rj("free_api_state.json"),
        "grants":          rj("grants_found.json"),
        "loop_result":     rj("revenue_loop_last.json"),
        "exchange":        rj("email_exchange_state.json"),
        "biz_factory":     rj("business_factory_state.json"),
        "secrets":         rj("secrets_checker_state.json"),
        "bottlenecks":     rj("bottleneck_report.json"),
        "architect_plan":  rj("architect_plan.json"),
        "weaver":          rj("knowledge_weaver_state.json"),
        "optimizer":       rj("revenue_optimizer_state.json"),
        "revenue_inbox":   rj("revenue_inbox.json"),
        "capabilities":    rj("capability_map.json"),
        "outreach":        rj("outreach_state.json"),
        "resonance":       rj("resonance_state.json"),
        "quick_revenue":   rj("quick_revenue.json"),
        "first_contact":   rj("first_contact.json"),
        "engines_ok":      results["ok"][:],
        "engines_failed":  results["failed"][:],
    }


def save_ctx():
    (DATA / "ctx.json").write_text(json.dumps(ctx(), indent=2, default=str))


def L0():
    print("\n--- L0: REMEMBER + HEALTH + INTEGRITY ---")
    eng("CYCLE_MEMORY",      timeout=30)
    eng("GUARDIAN",          timeout=60)
    eng("ENGINE_INTEGRITY",  timeout=60)
    eng("SECRETS_CHECKER",   timeout=60)
    eng("BOTTLENECK_SCANNER",timeout=60)
    eng("AUTO_HEALER",       timeout=90)
    eng("CAPABILITY_SCANNER",timeout=30)
    save_ctx()


def L1():
    print("\n--- L1: INTEL + LISTEN + WATCH ---")
    eng("EMAIL_BRAIN",       timeout=90)
    eng("SCAM_SHIELD",       timeout=60)
    eng("CALENDAR_BRAIN",    timeout=30)
    eng("CONTENT_HARVESTER", timeout=90)
    eng("AI_WATCHER",        timeout=60)
    eng("CRYPTO_WATCHER",    timeout=60)
    eng("FREE_API_ENGINE",   timeout=60)
    eng("RESONANCE_ENGINE",  timeout=60)    # are we being heard?
    eng("FIRST_CONTACT",     timeout=30)    # v15: has a stranger found us?
    save_ctx()
    eng("NEURON_A", timeout=90); save_ctx()
    eng("NEURON_B", timeout=90); save_ctx()


def L2():
    print("\n--- L2: REVENUE INTEL + BUILD ---")
    eng("GRANT_HUNTER",       timeout=90)
    eng("ETSY_SEO_ENGINE",    timeout=60)
    eng("INCOME_ARCHITECT",   timeout=60)
    eng("REVENUE_FLYWHEEL",   timeout=90)
    eng("GUMROAD_AUTO_QUEUE", timeout=60)
    eng("QUICK_REVENUE",      timeout=60)
    save_ctx()
    eng("BUSINESS_FACTORY",   timeout=180)
    save_ctx()


def L3():
    print("\n--- L3: DEPLOY + LOOP ---")
    eng("LANDING_DEPLOYER",     timeout=90)
    eng("ART_CATALOG",          timeout=60)
    save_ctx()
    eng("REVENUE_LOOP",         timeout=240)
    eng("ART_GENERATOR",        timeout=120)
    eng("EMAIL_AGENT_EXCHANGE", timeout=120)
    eng("GRANT_APPLICANT",      timeout=90)
    eng("HEALTH_BOOSTER",       timeout=60)
    save_ctx()


def L4():
    print("\n--- L4: DISTRIBUTE + PUBLISH ---")
    eng("SOCIAL_PROMOTER",     timeout=90)
    eng("SUBSTACK_ENGINE",     timeout=90)
    eng("LINK_PAGE",           timeout=60)
    eng("GITHUB_POSTER",       timeout=120)
    eng("SOCIAL_DASHBOARD",    timeout=60)
    eng("CONNECTION_FORGE",    timeout=90)
    eng("HUMAN_CONNECTOR",     timeout=60)
    eng("AFFILIATE_MAXIMIZER", timeout=60)
    eng("STORE_BUILDER",       timeout=90)
    eng("BRIDGE_BUILDER",      timeout=90)
    eng("EMAIL_OUTREACH",      timeout=120)
    eng("VIRALITY_ENGINE",     timeout=60)
    eng("DEV_TO_PUBLISHER",    timeout=60)
    save_ctx()


def L5():
    print("\n--- L5: COLLECT + PAYOUT ---")
    eng("KOFI_ENGINE",            timeout=60)
    eng("GUMROAD_ENGINE",         timeout=60)
    eng("GITHUB_SPONSORS_ENGINE", timeout=60)
    eng("KOFI_PAYMENT_TRACKER",   timeout=60)
    eng("DISPATCH_HANDLER",       timeout=60)
    eng("HUMAN_PAYOUT",           timeout=60)
    eng("CONTRIBUTOR_REGISTRY",   timeout=60)
    eng("PAYPAL_PAYOUT",          timeout=90)
    save_ctx()


def L6():
    print("\n--- L6: THINK + SELF-EXPAND ---")
    save_ctx()
    eng("SYNAPSE",           timeout=120); save_ctx()
    eng("SYNTHESIS_FACTORY", timeout=120); save_ctx()
    eng("ARCHITECT",         timeout=120); save_ctx()
    eng("SELF_BUILDER",      timeout=240); save_ctx()
    eng("KNOWLEDGE_BRIDGE",  timeout=60)
    eng("KNOWLEDGE_WEAVER",  timeout=180); save_ctx()
    eng("REVENUE_OPTIMIZER", timeout=120); save_ctx()
    eng("BIG_BRAIN_ORACLE",  timeout=90)
    save_ctx()


def L7():
    print("\n--- L7: REPORT + PROOF + VOICE ---")
    eng("MEMORY_PALACE",    timeout=60)
    eng("README_GENERATOR", timeout=60)
    eng("BRIEFING_ENGINE",  timeout=60)
    eng("NIGHTLY_DIGEST",   timeout=120)
    eng("ISSUE_SYNC",       timeout=90)
    eng("SOLARPUNK_LEGAL",  timeout=60)
    eng("BRAND_LEGAL",      timeout=60)
    eng("TASK_ATOMIZER",    timeout=120)
    eng("AUTONOMY_PROOF",   timeout=60)
    eng("CLAUDE_ENGINE",    timeout=60)
    eng("SELF_PORTRAIT",    timeout=60)
    save_ctx()


def run_bonus_engines():
    weaver = rj("knowledge_weaver_state.json")
    built  = weaver.get("engines_built", [])
    known  = set(results["ok"] + results["failed"] + results["skipped"])
    for name in built:
        if name not in known and (MYCELIUM / f"{name}.py").exists():
            print(f"\n--- BONUS: {name} (auto-built this cycle) ---")
            eng(name, timeout=120)
            save_ctx()


def run():
    t0     = time.time()
    run_id = os.environ.get("GITHUB_RUN_ID", f"local-{int(t0)}")
    ts     = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print(f"\nOMNIBUS v15 -- {ts}")
    print(f"   Run: {run_id}")
    print(f"   build -> speak -> listen -> remember -> watch -> respond -> grow")
    print("=" * 60)

    for layer in [L0, L1, L2, L3, L4, L5, L6, L7]:
        try:
            layer()
        except Exception as e:
            print(f"  LAYER ERROR: {e}")

    run_bonus_engines()

    elapsed      = round(time.time() - t0)
    total        = len(results["ok"]) + len(results["failed"])
    secrets      = rj("secrets_checker_state.json")
    revenue      = rj("revenue_inbox.json")
    payouts      = rj("payout_ledger.json")
    legal        = rj("brand_legal_state.json")
    bottleneck   = rj("bottleneck_report.json")
    weaver       = rj("knowledge_weaver_state.json")
    outreach     = rj("outreach_state.json")
    resonance    = rj("resonance_state.json")
    cycle_mem    = rj("cycle_delta.json")
    fc           = rj("first_contact.json")
    biz_count    = len(list(DATA.glob("business_*.json")))
    health_now   = rj("brain_state.json").get("health_score", 0)
    emails_out   = len([e for e in outreach.get("sent", []) if e.get("sent")])
    quick_rev    = rj("quick_revenue.json")
    first_sale   = quick_rev.get("first_sale_done", False)
    rev_total    = revenue.get("total_received", 0) if isinstance(revenue, dict) else 0
    gaza_total   = revenue.get("total_to_gaza",  0) if isinstance(revenue, dict) else 0
    first_contact_happened = fc.get("happened", False) if isinstance(fc, dict) else False

    manifest = {
        "version":               "v15",
        "run_id":                run_id,
        "completed":             datetime.now(timezone.utc).isoformat(),
        "elapsed_s":             elapsed,
        "health_before":         rj("brain_state.json").get("health_score", 40),
        "health_after":          health_now,
        "health_trend":          cycle_mem.get("health_trend", "unknown"),
        "cycle_number":          cycle_mem.get("cycle_number", 0),
        "businesses_built":      biz_count,
        "live_url":              rj("revenue_loop_last.json").get("live_url"),
        "total_revenue":         rev_total,
        "total_to_gaza":         gaza_total,
        "first_sale_done":       first_sale,
        "first_contact_happened":first_contact_happened,
        "first_contact_who":     fc.get("stranger") if first_contact_happened else None,
        "legal_fund":            legal.get("upto_fund_collected", 0),
        "total_paid_out":        payouts.get("total_paid_usd", 0) if isinstance(payouts, dict) else 0,
        "secrets_configured":    secrets.get("configured", 0),
        "critical_missing":      secrets.get("critical_missing", []),
        "bottleneck_count":      bottleneck.get("summary", {}).get("total_bottlenecks", 0),
        "engines_auto_built":    weaver.get("engines_built", []),
        "outreach_sent":         emails_out,
        "resonance_score":       resonance.get("resonance_score", 0),
        "resonance_label":       resonance.get("resonance_label", "SILENT"),
        "github_stars":          resonance.get("github", {}).get("stars", 0),
        "persistent_blockers":   len(cycle_mem.get("persistent", [])),
        "engines_ok":            results["ok"],
        "engines_failed":        results["failed"],
        "engines_skipped":       results["skipped"],
        "log":                   results["log"],
    }

    (DATA / "omnibus_last.json").write_text(json.dumps(manifest, indent=2))
    hf   = DATA / "omnibus_history.json"
    hist = json.loads(hf.read_text()) if hf.exists() else []
    hist.append({k: v for k, v in manifest.items() if k != "log"})
    hf.write_text(json.dumps(hist[-200:], indent=2))

    print(f"\n{'='*60}")
    print(f"OMNIBUS v15 done -- {elapsed}s")
    print(f"   {len(results['ok'])}/{total} OK | {len(results['skipped'])} skipped")
    if results["failed"]:
        print(f"   FAILED: {', '.join(results['failed'])}")
    print(f"   Health: {manifest['health_before']} -> {manifest['health_after']} ({manifest['health_trend']})")
    print(f"   Revenue: ${rev_total:.2f} | Gaza: ${gaza_total:.2f} | First sale: {'YES' if first_sale else 'not yet'}")
    print(f"   Resonance: {manifest['resonance_score']}/100 ({manifest['resonance_label']}) | Stars: {manifest['github_stars']}")
    if first_contact_happened:
        print(f"   *** FIRST CONTACT: {fc.get('stranger')} via {fc.get('channel')} on {fc.get('timestamp_utc')} ***")
    else:
        print(f"   First contact: still waiting for the first stranger")
    if manifest["persistent_blockers"]:
        print(f"   Persistent blockers: {manifest['persistent_blockers']}")
    if manifest["engines_auto_built"]:
        print(f"   Auto-built: {', '.join(manifest['engines_auto_built'])}")
    if manifest["critical_missing"]:
        print(f"   MISSING: {', '.join(manifest['critical_missing'])}")
    print(f"\n   Live:")
    for page in ["first_contact", "memory", "quick_revenue", "store", "proof", "resonance", "self_portrait"]:
        print(f"      {BASE}/{page}.html")
    return manifest


if __name__ == "__main__":
    run()
