#!/usr/bin/env python3
"""
OMNIBUS v2 — Subprocess-isolated execution with shared ctx
===========================================================
FIX from v1: import conflicts and mixed run()/main() entry points
caused cascading failures. v2 runs every engine as its own subprocess —
complete isolation, no import pollution, any engine can crash without
taking down the rest.

SHARED CONTEXT: data/ctx.json — written before each layer, read by
engines that support it. All engines still write their own data/ files
as before. OMNIBUS reads those files to build ctx progressively.

DEPENDENCY ORDER (same 7 layers, now subprocess-safe):
  L0: MEMORY     — Guardian, (memory loaded from disk)
  L1: INTEL      — Email, Scam, Calendar, Content, AI/Crypto, Neurons A+B
  L2: REV INTEL  — Grants, Flywheel, Income Architect, SEO
  L3: BUILD      — Revenue Loop, Art, Exchange, Grant Applicant
  L4: PUBLISH    — Social, Substack, Links, Connection, Human
  L5: COLLECT    — Ko-fi, Gumroad, Sponsors
  L6: SYNTH      — Synapse, Synthesis, Self Builder
  L7: REPORT     — Memory Palace, README, Nightly Digest
"""
import os, sys, json, time, subprocess
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
PYTHON   = sys.executable

# ── result tracking ──────────────────────────────────────────────────────────
results = {"ok": [], "failed": [], "skipped": [], "log": []}


def eng(name, *, required=False, timeout=120):
    """
    Run mycelium/{name}.py as a subprocess.
    Captures stdout/stderr. Updates results dict.
    Writes ctx.json before each call so engines can optionally read it.
    """
    script = MYCELIUM / f"{name}.py"
    if not script.exists():
        results["skipped"].append(name)
        results["log"].append({"engine": name, "status": "skipped", "reason": "file not found"})
        print(f"  ⏭  {name} (not found)")
        return False

    t0 = time.time()
    try:
        proc = subprocess.run(
            [PYTHON, str(script)],
            capture_output=True, text=True,
            timeout=timeout,
            cwd=Path.cwd(),
            env=os.environ.copy(),
        )
        elapsed = round(time.time() - t0, 1)
        ok = proc.returncode == 0

        entry = {
            "engine": name,
            "status": "ok" if ok else "error",
            "code": proc.returncode,
            "elapsed": elapsed,
            "stdout_tail": proc.stdout[-400:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-400:] if proc.stderr else "",
        }
        results["log"].append(entry)

        if ok:
            results["ok"].append(name)
            print(f"  ✅ {name} ({elapsed}s)")
        else:
            results["failed"].append(name)
            print(f"  ❌ {name} ({elapsed}s) rc={proc.returncode}")
            if proc.stderr:
                # Show last error line only
                last_err = [l for l in proc.stderr.strip().splitlines() if l]
                print(f"     {last_err[-1][:120]}" if last_err else "")

        return ok

    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - t0, 1)
        results["failed"].append(name)
        results["log"].append({"engine": name, "status": "timeout", "elapsed": elapsed})
        print(f"  ⏱  {name} timeout after {timeout}s")
        if required:
            raise
        return False
    except Exception as e:
        results["failed"].append(name)
        results["log"].append({"engine": name, "status": "exception", "error": str(e)})
        print(f"  💥 {name}: {e}")
        return False


def rj(fname, fallback=None):
    """Read a JSON file from data/, return fallback on any error."""
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fallback if fallback is not None else {}


def write_ctx(extra=None):
    """Write accumulated context to data/ctx.json for engines to consume."""
    ctx = {
        "run_id":      os.environ.get("GITHUB_RUN_ID", f"local-{int(time.time())}"),
        "cycle_start": datetime.now(timezone.utc).isoformat(),
        "amazon_tag":  os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20"),
        "prev_health": rj("brain_state.json").get("health_score", 40),
        "memory":      rj("memory_palace.json"),
        "lessons":     rj("lessons.json", []),
        "neuron_a":    rj("neuron_a_report.json"),
        "neuron_b":    rj("neuron_b_report.json"),
        "opportunities": rj("neuron_b_report.json").get("vetted_opportunities",
                          rj("neuron_a_report.json").get("opportunities", [])),
        "flywheel":    rj("flywheel_summary.json"),
        "content":     rj("content_harvest.json"),
        "seo":         rj("etsy_seo_output.json"),
        "grants":      rj("grant_hunter_state.json"),
        "loop_result": rj("revenue_loop_last.json"),
        "live_url":    rj("revenue_loop_last.json").get("live_url"),
        "gumroad_url": rj("revenue_loop_last.json").get("gumroad_url"),
        "engines_ok":    results["ok"][:],
        "engines_failed":results["failed"][:],
    }
    if extra:
        ctx.update(extra)
    (DATA / "ctx.json").write_text(json.dumps(ctx, indent=2, default=str))
    return ctx


# ─────────────────────────────────────────────────────────────────────────────
# LAYERS
# ─────────────────────────────────────────────────────────────────────────────

def layer_0():
    print("\n━━━ L0: MEMORY ━━━")
    eng("GUARDIAN")
    write_ctx()

def layer_1():
    print("\n━━━ L1: INTEL ━━━")
    eng("EMAIL_BRAIN",    timeout=60)
    eng("SCAM_SHIELD",    timeout=60)
    eng("CALENDAR_BRAIN", timeout=30)
    eng("CONTENT_HARVESTER", timeout=60)
    eng("AI_WATCHER",    timeout=60)
    eng("CRYPTO_WATCHER",timeout=60)
    write_ctx()
    eng("NEURON_A",      timeout=90)
    write_ctx()          # B sees A's output
    eng("NEURON_B",      timeout=90)
    write_ctx()

def layer_2():
    print("\n━━━ L2: REVENUE INTEL ━━━")
    eng("GRANT_HUNTER",    timeout=90)
    eng("ETSY_SEO_ENGINE", timeout=60)
    eng("INCOME_ARCHITECT",timeout=60)
    write_ctx()
    eng("REVENUE_FLYWHEEL",timeout=90)
    write_ctx()

def layer_3():
    print("\n━━━ L3: BUILD ━━━")
    eng("REVENUE_LOOP",    timeout=180)  # build+deploy+gumroad
    write_ctx()
    eng("ART_GENERATOR",   timeout=120)
    eng("EMAIL_AGENT_EXCHANGE", timeout=90)
    eng("GRANT_APPLICANT", timeout=90)
    eng("HEALTH_BOOSTER",  timeout=60)
    write_ctx()

def layer_4():
    print("\n━━━ L4: PUBLISH ━━━")
    eng("SOCIAL_PROMOTER",  timeout=90)
    eng("SUBSTACK_ENGINE",  timeout=90)
    eng("LINK_PAGE",        timeout=60)
    eng("CONNECTION_FORGE", timeout=90)
    eng("HUMAN_CONNECTOR",  timeout=60)
    write_ctx()

def layer_5():
    print("\n━━━ L5: COLLECT ━━━")
    eng("KOFI_ENGINE",           timeout=60)
    eng("GUMROAD_ENGINE",        timeout=60)
    eng("GITHUB_SPONSORS_ENGINE",timeout=60)
    write_ctx()

def layer_6():
    print("\n━━━ L6: SYNTH ━━━")
    write_ctx()          # flush everything before synthesis
    eng("SYNAPSE",          timeout=120)
    write_ctx()
    eng("SYNTHESIS_FACTORY",timeout=120)
    eng("SELF_BUILDER",     timeout=180)
    # ARCHITECT: what new engines/capabilities should be built?
    eng("ARCHITECT",        timeout=120)
    write_ctx()

def layer_7():
    print("\n━━━ L7: REPORT ━━━")
    eng("MEMORY_PALACE",  timeout=60)
    eng("README_GENERATOR",timeout=60)
    eng("BRIEFING_ENGINE", timeout=60)
    eng("NIGHTLY_DIGEST",  timeout=120)  # comprehensive nightly + system self-improvement
    write_ctx()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run():
    t0 = time.time()
    run_id = os.environ.get("GITHUB_RUN_ID", f"local-{int(t0)}")
    print(f"\n🧠 OMNIBUS v2 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   Run: {run_id}")
    print("=" * 55)

    for layer_fn in [layer_0, layer_1, layer_2, layer_3,
                     layer_4, layer_5, layer_6, layer_7]:
        layer_fn()

    elapsed = round(time.time() - t0)
    total   = len(results["ok"]) + len(results["failed"])

    # Final manifest
    ctx = write_ctx()
    manifest = {
        "run_id":     run_id,
        "completed":  datetime.now(timezone.utc).isoformat(),
        "elapsed_s":  elapsed,
        "health_before": ctx.get("prev_health", 0),
        "health_after":  rj("brain_state.json").get("health_score", 0),
        "live_url":   ctx.get("live_url"),
        "engines_ok":    results["ok"],
        "engines_failed":results["failed"],
        "engines_skipped":results["skipped"],
        "log":        results["log"],
    }
    (DATA / "omnibus_last.json").write_text(json.dumps(manifest, indent=2))

    # History (last 100 cycles)
    hf = DATA / "omnibus_history.json"
    hist = json.loads(hf.read_text()) if hf.exists() else []
    hist.append({k: v for k, v in manifest.items() if k != "log"})
    hf.write_text(json.dumps(hist[-100:], indent=2))

    print(f"\n{'='*55}")
    print(f"🧠 OMNIBUS done — {elapsed}s | {len(results['ok'])}/{total} engines OK")
    if results["failed"]:
        print(f"   Failed: {', '.join(results['failed'])}")
    if results["skipped"]:
        print(f"   Skipped: {', '.join(results['skipped'])}")
    health_after = manifest["health_after"]
    print(f"   Health: {manifest['health_before']} → {health_after}")
    if ctx.get("live_url"):
        print(f"   Live: {ctx['live_url']}")
    return manifest


if __name__ == "__main__":
    run()
