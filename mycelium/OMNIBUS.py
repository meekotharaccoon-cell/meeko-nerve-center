#!/usr/bin/env python3
"""
OMNIBUS v4 — The real fixed orchestrator
=========================================
v4 changes vs v3:
- Added GITHUB_POSTER (L4) — creates GitHub Releases per product, GITHUB_TOKEN only
- Added SOCIAL_DASHBOARD (L4) — builds docs/social.html copy-paste board
- CONNECTION_FORGE fixed (SyntaxError patched)
- BRIEFING_ENGINE fixed (None[:10] TypeError patched)
- AI_CLIENT updated (dead HF models replaced)

CORRECT DEPENDENCY CHAIN:
  L0  GUARDIAN              — load/save brain state
  L1  EMAIL + INTEL         — read email, gather intel
  L2  REVENUE INTEL         — grants, flywheel, SEO, income plan
  L2b BUSINESS_FACTORY      — build new business (writes data/business_*.json)
  L3  REVENUE_LOOP          — reads business file, deploys, Gumroad, social
  L3b LANDING_DEPLOYER      — deploy any remaining undeployed businesses
  L3c OTHER BUILD           — art, email exchange, health
  L4  PUBLISH               — social posts, Substack, links, GitHub Releases, copy-paste board
  L5  COLLECT               — Ko-fi, Gumroad, payment tracking
  L6  ARCHITECT             — strategic plan (reads all state, writes plan)
  L6b SELF_BUILDER          — reads architect plan, writes new engine
  L6c SYNAPSE + SYNTHESIS   — synthesis
  L7  REPORT                — memory, README, nightly digest (status page)
"""
import os, sys, json, time, subprocess
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
DOCS     = Path("docs"); DOCS.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
PYTHON   = sys.executable

results = {"ok": [], "failed": [], "skipped": [], "log": []}


def eng(name, *, timeout=120):
    """Run one engine as an isolated subprocess."""
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
            timeout=timeout,
            cwd=Path.cwd(),
            env=dict(os.environ),
        )
        elapsed = round(time.time() - t0, 1)
        ok = proc.returncode == 0

        if ok:
            results["ok"].append(name)
            lines = [l for l in (proc.stdout or "").strip().splitlines() if l.strip()]
            tail  = lines[-2:] if lines else []
            print(f"  ✅ {name} ({elapsed}s)" + (f"  ← {tail[-1][:80]}" if tail else ""))
        else:
            results["failed"].append(name)
            err_lines = [l for l in (proc.stderr or "").strip().splitlines() if l.strip()]
            err_tail  = err_lines[-1][:120] if err_lines else "unknown error"
            out_lines = [l for l in (proc.stdout or "").strip().splitlines() if l.strip()]
            out_tail  = out_lines[-1][:80] if out_lines else ""
            print(f"  ❌ {name} ({elapsed}s) rc={proc.returncode}")
            print(f"     ERR: {err_tail}")
            if out_tail:
                print(f"     OUT: {out_tail}")

        results["log"].append({
            "engine": name, "status": "ok" if ok else "error",
            "code": proc.returncode, "elapsed": elapsed,
            "stdout_tail": (proc.stdout or "")[-500:],
            "stderr_tail": (proc.stderr or "")[-500:],
        })
        return ok

    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - t0, 1)
        results["failed"].append(name)
        results["log"].append({"engine": name, "status": "timeout", "elapsed": elapsed})
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
        "run_id":        os.environ.get("GITHUB_RUN_ID", f"local-{int(time.time())}"),
        "cycle_start":   datetime.now(timezone.utc).isoformat(),
        "amazon_tag":    os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20"),
        "prev_health":   rj("brain_state.json").get("health_score", 40),
        "memory":        rj("memory_palace.json"),
        "lessons":       rj("lessons.json", []),
        "neuron_a":      rj("neuron_a_report.json"),
        "neuron_b":      rj("neuron_b_report.json"),
        "flywheel":      rj("flywheel_summary.json"),
        "content":       rj("content_harvest.json"),
        "seo":           rj("etsy_seo_output.json"),
        "grants":        rj("grant_hunter_state.json"),
        "loop_result":   rj("revenue_loop_last.json"),
        "live_url":      rj("revenue_loop_last.json").get("live_url"),
        "gumroad_url":   rj("revenue_loop_last.json").get("gumroad_url"),
        "exchange":      rj("email_exchange_state.json"),
        "kofi_tracker":  rj("kofi_tracker_state.json"),
        "architect_plan":rj("architect_plan.json"),
        "biz_factory":   rj("business_factory_state.json"),
        "self_builder":  rj("self_builder_state.json"),
        "engines_ok":    results["ok"][:],
        "engines_failed":results["failed"][:],
        "engines_skipped":results["skipped"][:],
    }
    (DATA / "ctx.json").write_text(json.dumps(ctx, indent=2, default=str))
    return ctx


# ─────────────────────────────────────────────────────────────────────────────
def layer_0():
    """Memory & guardian — load brain state"""
    print("\n━━━ L0: GUARDIAN ━━━")
    eng("GUARDIAN", timeout=60)
    write_ctx()


def layer_1():
    """Intel — email, scams, calendar, content, market data"""
    print("\n━━━ L1: INTEL ━━━")
    eng("EMAIL_BRAIN",       timeout=90)
    eng("SCAM_SHIELD",       timeout=60)
    eng("CALENDAR_BRAIN",    timeout=30)
    eng("CONTENT_HARVESTER", timeout=90)
    eng("AI_WATCHER",        timeout=60)
    eng("CRYPTO_WATCHER",    timeout=60)
    write_ctx()
    eng("NEURON_A", timeout=90)
    write_ctx()
    eng("NEURON_B", timeout=90)
    write_ctx()


def layer_2():
    """Revenue Intel + Business Building — must run before REVENUE_LOOP"""
    print("\n━━━ L2: REVENUE INTEL ━━━")
    eng("GRANT_HUNTER",     timeout=90)
    eng("ETSY_SEO_ENGINE",  timeout=60)
    eng("INCOME_ARCHITECT", timeout=60)
    write_ctx()
    eng("REVENUE_FLYWHEEL", timeout=90)
    write_ctx()

    # CRITICAL: Build the business FIRST so REVENUE_LOOP has something to read
    print("\n━━━ L2b: BUSINESS FACTORY ━━━")
    eng("BUSINESS_FACTORY", timeout=180)
    write_ctx()


def layer_3():
    """Build — revenue loop reads the business built in L2b"""
    print("\n━━━ L3: BUILD ━━━")

    # Deploy any undeployed businesses first
    eng("LANDING_DEPLOYER", timeout=90)
    write_ctx()

    # Full revenue loop: reads business file → injects affiliates → deploys → Gumroad → social → email
    eng("REVENUE_LOOP", timeout=240)
    write_ctx()

    # Other build engines
    eng("ART_GENERATOR",        timeout=120)
    eng("EMAIL_AGENT_EXCHANGE", timeout=120)
    eng("GRANT_APPLICANT",      timeout=90)
    eng("HEALTH_BOOSTER",       timeout=60)
    write_ctx()


def layer_4():
    """Publish — social posts, GitHub Releases, copy-paste dashboard"""
    print("\n━━━ L4: PUBLISH ━━━")
    eng("SOCIAL_PROMOTER",   timeout=90)
    eng("SUBSTACK_ENGINE",   timeout=90)
    eng("LINK_PAGE",         timeout=60)
    eng("GITHUB_POSTER",     timeout=120)   # GitHub Releases — zero external APIs
    eng("SOCIAL_DASHBOARD",  timeout=60)    # builds docs/social.html copy-paste board
    eng("CONNECTION_FORGE",  timeout=90)
    eng("HUMAN_CONNECTOR",   timeout=60)
    write_ctx()


def layer_5():
    """Collect — track payments, reconcile"""
    print("\n━━━ L5: COLLECT ━━━")
    eng("KOFI_ENGINE",            timeout=60)
    eng("GUMROAD_ENGINE",         timeout=60)
    eng("GITHUB_SPONSORS_ENGINE", timeout=60)
    eng("KOFI_PAYMENT_TRACKER",   timeout=60)
    write_ctx()


def layer_6():
    """Synth — ARCHITECT plans first, then SELF_BUILDER reads the plan"""
    print("\n━━━ L6: SYNTH + PLAN ━━━")
    write_ctx()
    eng("SYNAPSE",           timeout=120)
    write_ctx()
    eng("SYNTHESIS_FACTORY", timeout=120)
    write_ctx()

    # ARCHITECT must run before SELF_BUILDER
    eng("ARCHITECT",    timeout=120)
    write_ctx()
    eng("SELF_BUILDER", timeout=240)
    write_ctx()


def layer_7():
    """Report — update status page, README, memory, send digest"""
    print("\n━━━ L7: REPORT ━━━")
    eng("MEMORY_PALACE",    timeout=60)
    eng("README_GENERATOR", timeout=60)
    eng("BRIEFING_ENGINE",  timeout=60)
    eng("NIGHTLY_DIGEST",   timeout=120)
    write_ctx()


# ─────────────────────────────────────────────────────────────────────────────
def run():
    t0 = time.time()
    run_id = os.environ.get("GITHUB_RUN_ID", f"local-{int(t0)}")

    print(f"\n🧠 OMNIBUS v4 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   Run: {run_id}")
    print("=" * 58)

    biz_before = len(list(DATA.glob("business_*.json"))) - (1 if (DATA/"business_factory_state.json").exists() else 0)
    print(f"   Business files before run: {max(0, biz_before)}")

    for layer_fn in [layer_0, layer_1, layer_2, layer_3,
                     layer_4, layer_5, layer_6, layer_7]:
        try:
            layer_fn()
        except Exception as e:
            print(f"  💥 Layer error: {e}")

    elapsed = round(time.time() - t0)
    total   = len(results["ok"]) + len(results["failed"])
    ctx     = write_ctx()

    biz_after = len(list(DATA.glob("business_*.json"))) - (1 if (DATA/"business_factory_state.json").exists() else 0)

    manifest = {
        "run_id":          run_id,
        "completed":       datetime.now(timezone.utc).isoformat(),
        "elapsed_s":       elapsed,
        "health_before":   ctx.get("prev_health", 0),
        "health_after":    rj("brain_state.json").get("health_score", 0),
        "businesses_built": max(0, biz_after),
        "live_url":        ctx.get("live_url"),
        "gumroad_url":     ctx.get("gumroad_url"),
        "exchange_tasks":  ctx.get("exchange", {}).get("total_tasks", 0),
        "exchange_earned": ctx.get("exchange", {}).get("total_earned", 0.0),
        "exchange_gaza":   ctx.get("exchange", {}).get("total_to_gaza", 0.0),
        "engines_ok":      results["ok"],
        "engines_failed":  results["failed"],
        "engines_skipped": results["skipped"],
        "log":             results["log"],
    }
    (DATA / "omnibus_last.json").write_text(json.dumps(manifest, indent=2))

    hf   = DATA / "omnibus_history.json"
    hist = json.loads(hf.read_text()) if hf.exists() else []
    hist.append({k: v for k, v in manifest.items() if k != "log"})
    hf.write_text(json.dumps(hist[-200:], indent=2))

    print(f"\n{'='*58}")
    print(f"🧠 OMNIBUS v4 done — {elapsed}s")
    print(f"   Engines: {len(results['ok'])}/{total} OK | {len(results['skipped'])} skipped")
    if results["failed"]:
        print(f"   FAILED:  {', '.join(results['failed'])}")
    print(f"   Health:  {manifest['health_before']} → {manifest['health_after']}")
    print(f"   Businesses built: {manifest['businesses_built']}")
    if manifest.get("live_url"):
        print(f"   Live URL: {manifest['live_url']}")
    print(f"   Social: https://meekotharaccoon-cell.github.io/meeko-nerve-center/social.html")
    return manifest


if __name__ == "__main__":
    run()
