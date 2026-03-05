#!/usr/bin/env python3
"""
OMNIBUS v7 — full bridge network
=================================
v7 changes vs v6:
- Added GUMROAD_AUTO_QUEUE (L2) — auto-populates gumroad_listings.json with real products
- Added CONTRIBUTOR_REGISTRY (L5) — tracks human revenue splits, credits contributors
- Added PAYPAL_PAYOUT (L5) — sends real PayPal payments to contributors
- Added KNOWLEDGE_BRIDGE (L6) — maps all engine connections, finds gaps
- Added BIG_BRAIN_ORACLE (L6) — asks Claude strategic questions, seeds next cycle
- All workflows now pass PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET

FULL DEPENDENCY CHAIN:
  L0  GUARDIAN + ENGINE_INTEGRITY + SECRETS_CHECKER
  L1  EMAIL + INTEL
  L2  REVENUE INTEL + GUMROAD_AUTO_QUEUE + BUSINESS_FACTORY
  L3  BUILD + ART_CATALOG
  L4  PUBLISH (social, releases, dashboard)
  L5  COLLECT + PAYOUT (Ko-fi, Gumroad, PayPal, CONTRIBUTOR_REGISTRY, PAYPAL_PAYOUT)
  L6  SYNTH + PLAN + KNOWLEDGE_BRIDGE + BIG_BRAIN_ORACLE
  L7  REPORT + LEGAL (memory, readme, briefing, digest, issue sync, legal)
"""
import os, sys, json, time, subprocess
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
DOCS     = Path("docs"); DOCS.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
PYTHON   = sys.executable

results = {"ok": [], "failed": [], "skipped": [], "log": []}
BASE_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"


def eng(name, *, timeout=120):
    script = MYCELIUM / f"{name}.py"
    if not script.exists():
        results["skipped"].append(name)
        results["log"].append({"engine": name, "status": "skipped", "reason": "file not found"})
        print(f"  ⏭  {name} — NOT FOUND")
        return False

    t0 = time.time()
    try:
        proc = subprocess.run(
            [PYTHON, str(script)],
            capture_output=True, text=True,
            timeout=timeout, cwd=Path.cwd(), env=dict(os.environ),
        )
        elapsed = round(time.time() - t0, 1)
        ok = proc.returncode == 0

        if ok:
            results["ok"].append(name)
            lines = [l for l in (proc.stdout or "").strip().splitlines() if l.strip()]
            tail = lines[-1][:80] if lines else ""
            print(f"  ✅ {name} ({elapsed}s)" + (f"  ← {tail}" if tail else ""))
        else:
            results["failed"].append(name)
            err = (proc.stderr or "")[-200:].strip().splitlines()
            print(f"  ❌ {name} ({elapsed}s) rc={proc.returncode}")
            if err: print(f"     {err[-1][:120]}")

        results["log"].append({
            "engine": name, "status": "ok" if ok else "error",
            "code": proc.returncode, "elapsed": elapsed,
            "stdout_tail": (proc.stdout or "")[-500:],
            "stderr_tail": (proc.stderr or "")[-500:],
        })
        return ok

    except subprocess.TimeoutExpired:
        results["failed"].append(name)
        results["log"].append({"engine": name, "status": "timeout", "elapsed": timeout})
        print(f"  ⏱  {name} TIMEOUT after {timeout}s")
        return False
    except Exception as e:
        results["failed"].append(name)
        results["log"].append({"engine": name, "status": "exception", "error": str(e)})
        print(f"  💥 {name}: {e}")
        return False


def rj(fname, fallback=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fallback if fallback is not None else {}


def write_ctx():
    ctx = {
        "run_id":         os.environ.get("GITHUB_RUN_ID", f"local-{int(time.time())}"),
        "cycle_start":    datetime.now(timezone.utc).isoformat(),
        "prev_health":    rj("brain_state.json").get("health_score", 40),
        "memory":         rj("memory_palace.json"),
        "lessons":        rj("lessons.json", []),
        "neuron_a":       rj("neuron_a_report.json"),
        "neuron_b":       rj("neuron_b_report.json"),
        "flywheel":       rj("flywheel_summary.json"),
        "content":        rj("content_harvest.json"),
        "seo":            rj("etsy_seo_output.json"),
        "grants":         rj("grant_hunter_state.json"),
        "loop_result":    rj("revenue_loop_last.json"),
        "live_url":       rj("revenue_loop_last.json").get("live_url"),
        "gumroad_url":    rj("revenue_loop_last.json").get("gumroad_url"),
        "exchange":       rj("email_exchange_state.json"),
        "kofi_tracker":   rj("kofi_tracker_state.json"),
        "architect_plan": rj("architect_plan.json"),
        "biz_factory":    rj("business_factory_state.json"),
        "self_builder":   rj("self_builder_state.json"),
        "integrity":      rj("engine_sha_registry.json"),
        "revenue_inbox":  rj("revenue_inbox.json"),
        "secrets":        rj("secrets_checker_state.json"),
        "legal":          rj("brand_legal_state.json"),
        "payouts":        rj("payout_ledger.json"),
        "art_catalog":    rj("art_catalog.json"),
        "oracle":         rj("oracle_state.json"),
        "knowledge_gaps": rj("knowledge_gaps.json"),
        "contributor_reg":rj("contributor_registry.json"),
        "engines_ok":     results["ok"][:],
        "engines_failed": results["failed"][:],
        "engines_skipped":results["skipped"][:],
    }
    (DATA / "ctx.json").write_text(json.dumps(ctx, indent=2, default=str))
    return ctx


# ─────────────────────────────────────────────────────────────────────────────
def layer_0():
    print("\n━━━ L0: GUARDIAN + INTEGRITY + SECRETS ━━━")
    eng("GUARDIAN",         timeout=60)
    eng("ENGINE_INTEGRITY", timeout=60)
    eng("SECRETS_CHECKER",  timeout=60)
    write_ctx()


def layer_1():
    print("\n━━━ L1: INTEL ━━━")
    eng("EMAIL_BRAIN",       timeout=90)
    eng("SCAM_SHIELD",       timeout=60)
    eng("CALENDAR_BRAIN",    timeout=30)
    eng("CONTENT_HARVESTER", timeout=90)
    eng("AI_WATCHER",        timeout=60)
    eng("CRYPTO_WATCHER",    timeout=60)
    write_ctx()
    eng("NEURON_A", timeout=90); write_ctx()
    eng("NEURON_B", timeout=90); write_ctx()


def layer_2():
    print("\n━━━ L2: REVENUE INTEL ━━━")
    eng("GRANT_HUNTER",       timeout=90)
    eng("ETSY_SEO_ENGINE",    timeout=60)
    eng("INCOME_ARCHITECT",   timeout=60)
    eng("REVENUE_FLYWHEEL",   timeout=90)
    eng("GUMROAD_AUTO_QUEUE", timeout=60)   # ← v7: builds gumroad listings
    write_ctx()
    print("\n━━━ L2b: BUSINESS FACTORY ━━━")
    eng("BUSINESS_FACTORY", timeout=180)
    write_ctx()


def layer_3():
    print("\n━━━ L3: BUILD + ART ━━━")
    eng("LANDING_DEPLOYER",     timeout=90)
    eng("ART_CATALOG",          timeout=60)
    write_ctx()
    eng("REVENUE_LOOP",         timeout=240)
    eng("ART_GENERATOR",        timeout=120)
    eng("EMAIL_AGENT_EXCHANGE", timeout=120)
    eng("GRANT_APPLICANT",      timeout=90)
    eng("HEALTH_BOOSTER",       timeout=60)
    write_ctx()


def layer_4():
    print("\n━━━ L4: PUBLISH ━━━")
    eng("SOCIAL_PROMOTER",  timeout=90)
    eng("SUBSTACK_ENGINE",  timeout=90)
    eng("LINK_PAGE",        timeout=60)
    eng("GITHUB_POSTER",    timeout=120)
    eng("SOCIAL_DASHBOARD", timeout=60)
    eng("CONNECTION_FORGE", timeout=90)
    eng("HUMAN_CONNECTOR",  timeout=60)
    write_ctx()


def layer_5():
    print("\n━━━ L5: COLLECT + PAYOUT ━━━")
    eng("KOFI_ENGINE",            timeout=60)
    eng("GUMROAD_ENGINE",         timeout=60)
    eng("GITHUB_SPONSORS_ENGINE", timeout=60)
    eng("KOFI_PAYMENT_TRACKER",   timeout=60)
    eng("HUMAN_PAYOUT",           timeout=60)
    eng("CONTRIBUTOR_REGISTRY",   timeout=60)   # ← v7: credits contributors from revenue
    eng("PAYPAL_PAYOUT",          timeout=90)   # ← v7: auto-sends PayPal payments
    write_ctx()


def layer_6():
    print("\n━━━ L6: SYNTH + PLAN + ORACLE ━━━")
    write_ctx()
    eng("SYNAPSE",           timeout=120); write_ctx()
    eng("SYNTHESIS_FACTORY", timeout=120); write_ctx()
    eng("ARCHITECT",         timeout=120); write_ctx()
    eng("SELF_BUILDER",      timeout=240); write_ctx()
    eng("KNOWLEDGE_BRIDGE",  timeout=60)   # ← v7: maps engine connections, finds gaps
    eng("BIG_BRAIN_ORACLE",  timeout=90)   # ← v7: asks strategic questions, seeds next cycle
    write_ctx()


def layer_7():
    print("\n━━━ L7: REPORT + LEGAL ━━━")
    eng("MEMORY_PALACE",    timeout=60)
    eng("README_GENERATOR", timeout=60)
    eng("BRIEFING_ENGINE",  timeout=60)
    eng("NIGHTLY_DIGEST",   timeout=120)
    eng("ISSUE_SYNC",       timeout=90)
    eng("SOLARPUNK_LEGAL",  timeout=60)
    eng("BRAND_LEGAL",      timeout=60)   # ← v7: SolarPunk™ trademark + legal fund
    write_ctx()


# ─────────────────────────────────────────────────────────────────────────────
def run():
    t0 = time.time()
    run_id = os.environ.get("GITHUB_RUN_ID", f"local-{int(t0)}")

    print(f"\n🧠 OMNIBUS v7 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   Run: {run_id}")
    print("=" * 58)

    for layer_fn in [layer_0, layer_1, layer_2, layer_3,
                     layer_4, layer_5, layer_6, layer_7]:
        try:
            layer_fn()
        except Exception as e:
            print(f"  💥 Layer error: {e}")

    elapsed = round(time.time() - t0)
    total   = len(results["ok"]) + len(results["failed"])
    ctx     = write_ctx()

    biz_after = len(list(DATA.glob("business_*.json")))
    revenue = rj("revenue_inbox.json")
    legal   = rj("brand_legal_state.json")
    secrets = rj("secrets_checker_state.json")
    payouts = rj("payout_ledger.json")

    manifest = {
        "version":           "v7",
        "run_id":            run_id,
        "completed":         datetime.now(timezone.utc).isoformat(),
        "elapsed_s":         elapsed,
        "health_before":     ctx.get("prev_health", 0),
        "health_after":      rj("brain_state.json").get("health_score", 0),
        "businesses_built":  biz_after,
        "live_url":          ctx.get("live_url"),
        "gumroad_url":       ctx.get("gumroad_url"),
        "total_revenue":     revenue.get("total_received", 0),
        "total_to_gaza":     revenue.get("total_to_gaza", 0),
        "legal_fund":        legal.get("upto_fund_collected", 0),
        "total_paid_out":    payouts.get("total_paid_usd", 0),
        "secrets_configured":secrets.get("configured", 0),
        "secrets_total":     secrets.get("total", 0),
        "critical_missing":  secrets.get("critical_missing", []),
        "engines_ok":        results["ok"],
        "engines_failed":    results["failed"],
        "engines_skipped":   results["skipped"],
        "log":               results["log"],
    }
    (DATA / "omnibus_last.json").write_text(json.dumps(manifest, indent=2))

    hf = DATA / "omnibus_history.json"
    hist = json.loads(hf.read_text()) if hf.exists() else []
    hist.append({k: v for k, v in manifest.items() if k != "log"})
    hf.write_text(json.dumps(hist[-200:], indent=2))

    print(f"\n{'='*58}")
    print(f"🧠 OMNIBUS v7 done — {elapsed}s")
    print(f"   Engines: {len(results['ok'])}/{total} OK | {len(results['skipped'])} skipped")
    if results["failed"]:
        print(f"   FAILED:  {', '.join(results['failed'])}")
    print(f"   Health:  {manifest['health_before']} → {manifest['health_after']}")
    print(f"   Revenue: ${manifest['total_revenue']:.2f} | → Gaza: ${manifest['total_to_gaza']:.2f}")
    print(f"   Paid out: ${manifest['total_paid_out']:.2f} to contributors")
    print(f"   Legal fund: ${manifest['legal_fund']:.2f} / $1,200 full USPTO target")
    print(f"   Secrets: {manifest['secrets_configured']}/{manifest['secrets_total']} configured")
    if manifest["critical_missing"]:
        print(f"   🔴 CRITICAL missing: {', '.join(manifest['critical_missing'])}")
    print(f"\n   🌐 LIVE URLS:")
    print(f"   Home:      {BASE_URL}/index.html")
    print(f"   Store:     {BASE_URL}/store.html")
    print(f"   Art:       {BASE_URL}/art.html")
    print(f"   Social:    {BASE_URL}/social.html")
    print(f"   Dashboard: {BASE_URL}/dashboard.html")
    print(f"   Setup:     {BASE_URL}/setup.html")
    print(f"   Legal:     {BASE_URL}/legal.html")
    print(f"   Payouts:   {BASE_URL}/payouts.html")
    print(f"   Knowledge: {BASE_URL}/knowledge_map.html")
    return manifest


if __name__ == "__main__":
    run()
