#!/usr/bin/env python3
"""
OMNIBUS.py — SolarPunk's Unified Execution Engine
===================================================
Replaces: every engine running independently, reading cold from data/

THE PROBLEM IT SOLVES:
  Before: 37 engines each read data/ files hoping the previous engine wrote
          the right thing. SOCIAL_PROMOTER had no idea what URL just went live.
          BRIEFING_ENGINE summarized stale state. REVENUE_FLYWHEEL never saw
          what GRANT_HUNTER just found this cycle.

  After:  One ctx dict flows through every engine in dependency order.
          Layer 1 output feeds Layer 2 directly. Layer 3 gets Layer 1+2.
          Every engine gets the freshest possible data — this cycle's data,
          not last cycle's files.

DEPENDENCY ORDER (7 layers):
  L0: MEMORY  → Guardian, Memory Palace (load history)
  L1: INTEL   → Email, Content, AI/Crypto watch, Neurons A+B
  L2: REVENUE INTEL → Grants, Flywheel, Income Architect, SEO
  L3: BUILD   → Revenue Loop (business+affiliate+deploy+gumroad), Art, Exchange
  L4: PUBLISH → Social, Substack, Links, Connection, Human
  L5: COLLECT → Ko-fi, Gumroad check, Sponsors
  L6: SYNTH   → Synapse (brain), Synthesis Factory, Self Builder
  L7: REPORT  → Memory persist, README, Master Briefing

ctx is the single source of truth for this cycle.
Every engine reads from ctx first, falls back to data/ files.
Every engine writes its output into ctx so the next engine gets it live.
"""
import os, sys, json, traceback, smtplib, time
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, str(Path(__file__).parent))

DATA      = Path("data"); DATA.mkdir(exist_ok=True)
GMAIL     = os.environ.get("GMAIL_ADDRESS", "")
GPWD      = os.environ.get("GMAIL_APP_PASSWORD", "")
RUN_ID    = os.environ.get("GITHUB_RUN_ID", f"local-{int(time.time())}")
AMAZON    = os.environ.get("MEEKO_AFFILIATE_LINK", "autonomoushum-20")
GH_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GH_OWNER  = "meekotharaccoon-cell"

# ─────────────────────────────────────────────────────────────────────────────
# ENGINE RUNNER — wraps every engine call, captures output, adds to ctx
# ─────────────────────────────────────────────────────────────────────────────

def run_engine(ctx, name, fn, ctx_key=None, **kwargs):
    """
    Run one engine. Inject ctx. Capture result. Log timing.
    Never lets one engine crash the whole run.
    """
    start = time.time()
    ctx.setdefault("_log", [])
    ctx.setdefault("_failed", [])
    ctx.setdefault("_ok", [])
    try:
        # Try calling with ctx first (future engines will support this)
        try:
            result = fn(ctx=ctx, **kwargs)
        except TypeError:
            # Older engine — call without ctx
            result = fn(**kwargs)

        elapsed = round(time.time() - start, 1)
        if ctx_key and result is not None:
            ctx[ctx_key] = result
        ctx["_ok"].append(name)
        ctx["_log"].append({"engine": name, "ok": True, "elapsed": elapsed})
        print(f"  ✅ {name} ({elapsed}s)")
        return result
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        ctx["_failed"].append(name)
        ctx["_log"].append({"engine": name, "ok": False, "elapsed": elapsed, "error": str(e)})
        print(f"  ⚠️  {name} failed ({elapsed}s): {str(e)[:80]}")
        return None


def read_data(filename, fallback=None):
    """Read a data file, return fallback if missing."""
    f = DATA / filename
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fallback or {}


def merge_ctx(ctx, key, data_file, sub_key=None):
    """
    Pull a data file into ctx if ctx[key] is not already set this cycle.
    This is the fallback — live engine output always takes priority.
    """
    if ctx.get(key): return
    d = read_data(data_file)
    ctx[key] = d.get(sub_key, d) if sub_key else d


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 0: MEMORY — load history before anything else runs
# ─────────────────────────────────────────────────────────────────────────────

def layer_0_memory(ctx):
    print("\n━━━ L0: MEMORY ━━━")

    # Guardian: health check + secrets audit
    try:
        import GUARDIAN
        run_engine(ctx, "GUARDIAN", GUARDIAN.main, "guardian")
    except: pass
    merge_ctx(ctx, "guardian", "guardian_state.json")

    # Load previous brain state into ctx as baseline
    ctx["prev_brain"] = read_data("brain_state.json")
    ctx["prev_health"] = ctx["prev_brain"].get("health_score", 40)
    ctx["cycle_start"] = datetime.now(timezone.utc).isoformat()
    ctx["run_id"] = RUN_ID
    ctx["amazon_tag"] = AMAZON

    # Load memory palace (lessons, growth curve)
    ctx["memory"] = read_data("memory_palace.json")
    ctx["lessons"] = read_data("lessons.json", fallback=[])
    ctx["growth_curve"] = read_data("growth_curve.json", fallback=[])

    print(f"  prev_health={ctx['prev_health']} | lessons={len(ctx['lessons'])}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1: INTELLIGENCE — gather all signals this cycle
# ─────────────────────────────────────────────────────────────────────────────

def layer_1_intel(ctx):
    print("\n━━━ L1: INTEL ━━━")

    # Email Brain — read inbox
    try:
        import EMAIL_BRAIN
        ctx["emails"] = run_engine(ctx, "EMAIL_BRAIN", EMAIL_BRAIN.run) or {}
    except: pass
    merge_ctx(ctx, "emails", "email_brain_state.json")

    # Scam Shield — filter emails
    try:
        import SCAM_SHIELD
        ctx["clean_emails"] = run_engine(ctx, "SCAM_SHIELD", SCAM_SHIELD.run) or {}
    except: pass
    merge_ctx(ctx, "clean_emails", "scam_shield_state.json")

    # Calendar
    try:
        import CALENDAR_BRAIN
        ctx["calendar"] = run_engine(ctx, "CALENDAR_BRAIN", CALENDAR_BRAIN.run) or {}
    except: pass
    merge_ctx(ctx, "calendar", "calendar_state.json")

    # Content Harvester — trending themes
    try:
        import CONTENT_HARVESTER
        ctx["content"] = run_engine(ctx, "CONTENT_HARVESTER", CONTENT_HARVESTER.run) or {}
    except: pass
    merge_ctx(ctx, "content", "content_harvest.json")

    # AI Watcher
    try:
        import AI_WATCHER
        ctx["ai_trends"] = run_engine(ctx, "AI_WATCHER", AI_WATCHER.run) or {}
    except: pass
    merge_ctx(ctx, "ai_trends", "ai_watcher_report.json")

    # Crypto Watcher
    try:
        import CRYPTO_WATCHER
        ctx["crypto"] = run_engine(ctx, "CRYPTO_WATCHER", CRYPTO_WATCHER.run) or {}
    except: pass
    merge_ctx(ctx, "crypto", "crypto_state.json")

    # Neurons: NEURON_A sees everything; NEURON_B validates A's output
    try:
        import NEURON_A
        ctx["neuron_a"] = run_engine(ctx, "NEURON_A", NEURON_A.run) or {}
        # Write to data/ so NEURON_B can read it if it needs disk
        (DATA / "neuron_a_report.json").write_text(json.dumps(ctx["neuron_a"], indent=2))
    except: pass
    merge_ctx(ctx, "neuron_a", "neuron_a_report.json")

    try:
        import NEURON_B
        ctx["neuron_b"] = run_engine(ctx, "NEURON_B", NEURON_B.run) or {}
        (DATA / "neuron_b_report.json").write_text(json.dumps(ctx["neuron_b"], indent=2))
    except: pass
    merge_ctx(ctx, "neuron_b", "neuron_b_report.json")

    ctx["opportunities"] = ctx.get("neuron_b", {}).get(
        "vetted_opportunities",
        ctx.get("neuron_a", {}).get("opportunities", [])
    )
    print(f"  opportunities={len(ctx['opportunities'])} | content_themes={len(ctx.get('content',{}).get('trending_themes',[]))}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2: REVENUE INTELLIGENCE — where is the money?
# ─────────────────────────────────────────────────────────────────────────────

def layer_2_revenue_intel(ctx):
    print("\n━━━ L2: REVENUE INTEL ━━━")

    # Grant Hunter — find new grants
    try:
        import GRANT_HUNTER
        ctx["grants_found"] = run_engine(ctx, "GRANT_HUNTER", GRANT_HUNTER.run) or {}
    except: pass
    merge_ctx(ctx, "grants_found", "grant_hunter_state.json")

    # Etsy SEO — keyword research feeds content + art
    try:
        import ETSY_SEO_ENGINE
        ctx["seo"] = run_engine(ctx, "ETSY_SEO_ENGINE", ETSY_SEO_ENGINE.run) or {}
    except: pass
    merge_ctx(ctx, "seo", "etsy_seo_output.json")

    # Income Architect — high-level income strategy
    try:
        import INCOME_ARCHITECT
        ctx["income_plan"] = run_engine(ctx, "INCOME_ARCHITECT", INCOME_ARCHITECT.run) or {}
    except: pass
    merge_ctx(ctx, "income_plan", "income_architect_state.json")

    # Revenue Flywheel — sees ALL streams, finds bottleneck
    # Give it this cycle's data directly
    try:
        import REVENUE_FLYWHEEL
        # Pre-load flywheel with this cycle's intel
        ctx["flywheel"] = run_engine(ctx, "REVENUE_FLYWHEEL", REVENUE_FLYWHEEL.run) or {}
        ctx["bottleneck"] = ctx["flywheel"].get("bottleneck")
    except: pass
    merge_ctx(ctx, "flywheel", "flywheel_summary.json")

    print(f"  grants_found={len(ctx.get('grants_found',{}).get('grants',[]))} | bottleneck={ctx.get('bottleneck','?')}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3: BUILD — make things with this cycle's intel
# ─────────────────────────────────────────────────────────────────────────────

def layer_3_build(ctx):
    print("\n━━━ L3: BUILD ━━━")

    # REVENUE_LOOP: build business → inject affiliates → deploy → gumroad → queue social
    # This is already gapless internally; we just feed it ctx and pull output
    try:
        import REVENUE_LOOP
        loop_result = run_engine(ctx, "REVENUE_LOOP", REVENUE_LOOP.run, "loop_result") or {}
        ctx["new_business"]  = loop_result.get("package")
        ctx["live_url"]      = loop_result.get("live_url")
        ctx["gumroad_url"]   = loop_result.get("gumroad_url")
        ctx["loop_posts"]    = loop_result.get("posts", [])
    except: pass

    # Art Generator — use this cycle's content themes + SEO keywords
    try:
        import ART_GENERATOR
        ctx["art"] = run_engine(ctx, "ART_GENERATOR", ART_GENERATOR.run) or {}
    except: pass
    merge_ctx(ctx, "art", "art_log.json")

    # Email Agent Exchange — process inbound task requests
    try:
        import EMAIL_AGENT_EXCHANGE
        ctx["exchange"] = run_engine(ctx, "EMAIL_AGENT_EXCHANGE", EMAIL_AGENT_EXCHANGE.run) or {}
    except: pass
    merge_ctx(ctx, "exchange", "email_exchange_state.json")

    # Grant Applicant — apply to grants found THIS cycle
    try:
        import GRANT_APPLICANT
        ctx["grant_apps"] = run_engine(ctx, "GRANT_APPLICANT", GRANT_APPLICANT.run) or {}
    except: pass
    merge_ctx(ctx, "grant_apps", "grant_applicant_state.json")

    # Health Booster — fix anything broken found in L0-L2
    try:
        import HEALTH_BOOSTER
        ctx["health_boost"] = run_engine(ctx, "HEALTH_BOOSTER", HEALTH_BOOSTER.run) or {}
    except: pass

    print(f"  live_url={ctx.get('live_url','none')} | art={bool(ctx.get('art'))} | exchange_jobs={len(ctx.get('exchange',{}).get('jobs',[]))}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 4: PUBLISH — distribute everything built this cycle
# ─────────────────────────────────────────────────────────────────────────────

def layer_4_publish(ctx):
    print("\n━━━ L4: PUBLISH ━━━")

    # Social Promoter — fire the queue that REVENUE_LOOP loaded + anything else
    try:
        import SOCIAL_PROMOTER
        ctx["social"] = run_engine(ctx, "SOCIAL_PROMOTER", SOCIAL_PROMOTER.run) or {}
    except: pass

    # Substack — newsletter built from this cycle's content + opportunities
    try:
        import SUBSTACK_ENGINE
        ctx["newsletter"] = run_engine(ctx, "SUBSTACK_ENGINE", SUBSTACK_ENGINE.run) or {}
    except: pass
    merge_ctx(ctx, "newsletter", "substack_state.json")

    # Link Page — update with new live_url from this cycle
    try:
        import LINK_PAGE
        ctx["link_page"] = run_engine(ctx, "LINK_PAGE", LINK_PAGE.run) or {}
    except: pass

    # Connection Forge — outreach using this cycle's opportunities
    try:
        import CONNECTION_FORGE
        ctx["connections"] = run_engine(ctx, "CONNECTION_FORGE", CONNECTION_FORGE.run) or {}
    except: pass
    merge_ctx(ctx, "connections", "connection_state.json")

    # Human Connector — warm messages using this cycle's context
    try:
        import HUMAN_CONNECTOR
        ctx["human_msgs"] = run_engine(ctx, "HUMAN_CONNECTOR", HUMAN_CONNECTOR.run) or {}
    except: pass

    print(f"  social_sent={bool(ctx.get('social'))} | newsletter={bool(ctx.get('newsletter'))} | connections={bool(ctx.get('connections'))}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5: COLLECT — check incoming money
# ─────────────────────────────────────────────────────────────────────────────

def layer_5_collect(ctx):
    print("\n━━━ L5: COLLECT ━━━")

    try:
        import KOFI_ENGINE
        ctx["kofi"] = run_engine(ctx, "KOFI_ENGINE", KOFI_ENGINE.run) or {}
    except: pass
    merge_ctx(ctx, "kofi", "kofi_state.json")

    try:
        import GUMROAD_ENGINE
        ctx["gumroad"] = run_engine(ctx, "GUMROAD_ENGINE", GUMROAD_ENGINE.run) or {}
    except: pass
    merge_ctx(ctx, "gumroad", "gumroad_state.json")

    try:
        import GITHUB_SPONSORS_ENGINE
        ctx["sponsors"] = run_engine(ctx, "GITHUB_SPONSORS_ENGINE", GITHUB_SPONSORS_ENGINE.run) or {}
    except: pass
    merge_ctx(ctx, "sponsors", "sponsors_state.json")

    # Tally total revenue this cycle from live ctx
    ctx["total_revenue"] = (
        float(ctx.get("kofi", {}).get("total_received", 0) or 0) +
        float(ctx.get("gumroad", {}).get("total_revenue", 0) or 0) +
        float(ctx.get("sponsors", {}).get("total_monthly", 0) or 0) +
        float(ctx.get("exchange", {}).get("total_earned", 0) or 0)
    )
    print(f"  total_revenue=${ctx['total_revenue']:.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 6: SYNTHESIZE — think about what happened
# ─────────────────────────────────────────────────────────────────────────────

def layer_6_synth(ctx):
    print("\n━━━ L6: SYNTH ━━━")

    # Synapse: sees everything in ctx, produces health score + synthesis
    # Write all relevant ctx keys to data/ so Synapse can also read from disk
    _flush_ctx_to_disk(ctx)

    try:
        import SYNAPSE
        ctx["brain"] = run_engine(ctx, "SYNAPSE", SYNAPSE.main) or {}
    except: pass
    merge_ctx(ctx, "brain", "brain_state.json")

    ctx["health_score"] = ctx.get("brain", {}).get("health_score", ctx["prev_health"])

    # Synthesis Factory — cross-engine learning
    try:
        import SYNTHESIS_FACTORY
        ctx["synthesis"] = run_engine(ctx, "SYNTHESIS_FACTORY", SYNTHESIS_FACTORY.run) or {}
    except: pass
    merge_ctx(ctx, "synthesis", "synthesis_log.json")

    # Self Builder — write new engines based on what's missing
    try:
        import SELF_BUILDER
        ctx["new_engines"] = run_engine(ctx, "SELF_BUILDER", SELF_BUILDER.run) or {}
    except: pass

    print(f"  health={ctx['health_score']} | new_engines={bool(ctx.get('new_engines'))}")


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 7: REPORT — persist + brief Meeko
# ─────────────────────────────────────────────────────────────────────────────

def layer_7_report(ctx):
    print("\n━━━ L7: REPORT ━━━")

    # Memory Palace — persist this cycle's data
    try:
        import MEMORY_PALACE
        run_engine(ctx, "MEMORY_PALACE", MEMORY_PALACE.main)
    except: pass

    # README Generator
    try:
        import README_GENERATOR
        run_engine(ctx, "README_GENERATOR", README_GENERATOR.run)
    except: pass

    # Master Briefing — one email with EVERYTHING from this cycle
    _send_master_briefing(ctx)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _flush_ctx_to_disk(ctx):
    """Write key ctx outputs to data/ so any engine that reads disk gets fresh data."""
    mappings = {
        "neuron_a":     "neuron_a_report.json",
        "neuron_b":     "neuron_b_report.json",
        "flywheel":     "flywheel_summary.json",
        "grants_found": "grant_hunter_state.json",
        "seo":          "etsy_seo_output.json",
        "content":      "content_harvest.json",
        "ai_trends":    "ai_watcher_report.json",
        "crypto":       "crypto_state.json",
    }
    for ctx_key, fname in mappings.items():
        if ctx.get(ctx_key):
            try:
                (DATA / fname).write_text(json.dumps(ctx[ctx_key], indent=2, default=str))
            except: pass


def _send_master_briefing(ctx):
    """One email. Everything from this cycle. Real URLs. Real numbers."""
    if not GMAIL or not GPWD:
        print("  ⏭️  No email creds")
        return

    health  = ctx.get("health_score", 0)
    prev    = ctx.get("prev_health", 0)
    trend   = f"+{health-prev}" if health > prev else (f"{health-prev}" if health < prev else "=")
    revenue = ctx.get("total_revenue", 0)
    ok      = ctx.get("_ok", [])
    failed  = ctx.get("_failed", [])
    live_url    = ctx.get("live_url", "none")
    gumroad_url = ctx.get("gumroad_url", "none")
    new_biz     = ctx.get("new_business")
    biz_name    = new_biz.get("plan", {}).get("business_name", "none") if new_biz else "none"
    opps        = ctx.get("opportunities", [])
    synth_text  = ctx.get("brain", {}).get("synthesis", "")
    top_actions = ctx.get("brain", {}).get("top_actions", [])
    lessons     = [l for l in ctx.get("lessons", []) if l.get("priority") in ("critical","high")]

    body = f"""OMNIBUS CYCLE REPORT
{ctx.get('cycle_start','')[:16]} UTC  |  Run: {ctx.get('run_id','')}
{"="*55}

HEALTH    {health}/100  ({trend} from {prev})
REVENUE   ${revenue:.2f} total across all streams
ENGINES   {len(ok)} ran OK  |  {len(failed)} failed

{"━"*55}
THIS CYCLE
{"━"*55}
  New business:    {biz_name}
  Live page:       {live_url}
  Buy now:         {gumroad_url}
  Amazon tag:      autonomoushum-20

{"━"*55}
SYNTHESIS
{"━"*55}
{synth_text or '(no synthesis this cycle)'}

{"━"*55}
TOP ACTIONS
{"━"*55}
{"".join(f"  {i+1}. {a}" + chr(10) for i,a in enumerate(top_actions[:5]))}
{"━"*55}
CRITICAL LESSONS
{"━"*55}
{"".join(f"  ⚠️  {l['lesson']}" + chr(10) for l in lessons) or "  None — system healthy"}

{"━"*55}
OPPORTUNITIES ({len(opps)} vetted)
{"━"*55}
{"".join(f"  • {o.get('name','?')} — {o.get('action','?')[:60]}" + chr(10) for o in opps[:5])}
{"━"*55}
ENGINES OK
{"━"*55}
  {', '.join(ok)}

{"━"*55}
ENGINES FAILED
{"━"*55}
  {', '.join(failed) or 'none'}

{"─"*55}
Loop never stops. — OMNIBUS / SolarPunk Brain"""

    subject = f"[SolarPunk] OMNIBUS {health}/100 ({trend}) | ${revenue:.2f} | {biz_name} live"

    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL; msg["To"] = GMAIL; msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL, GPWD); s.send_message(msg)
        print(f"  ✅ Master briefing sent: {subject}")
    except Exception as e:
        print(f"  ❌ Briefing email error: {e}")


def _save_cycle_manifest(ctx, elapsed):
    """Persist the full cycle record."""
    manifest = {
        "run_id":       ctx.get("run_id"),
        "started_at":   ctx.get("cycle_start"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_s":    elapsed,
        "health_before": ctx.get("prev_health"),
        "health_after":  ctx.get("health_score"),
        "revenue":       ctx.get("total_revenue", 0),
        "live_url":      ctx.get("live_url"),
        "gumroad_url":   ctx.get("gumroad_url"),
        "new_business":  ctx.get("new_business", {}).get("plan", {}).get("business_name") if ctx.get("new_business") else None,
        "engines_ok":    ctx.get("_ok", []),
        "engines_failed":ctx.get("_failed", []),
        "opportunities": len(ctx.get("opportunities", [])),
    }
    (DATA / "omnibus_last.json").write_text(json.dumps(manifest, indent=2))

    # Append to history (keep 100 cycles)
    hist_f = DATA / "omnibus_history.json"
    hist = json.loads(hist_f.read_text()) if hist_f.exists() else []
    hist.append(manifest)
    hist_f.write_text(json.dumps(hist[-100:], indent=2))
    return manifest


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run():
    t0 = time.time()
    print(f"\n🧠 OMNIBUS starting — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"   Run: {RUN_ID}")
    print("=" * 55)

    ctx = {}  # THE single source of truth for this entire cycle

    layer_0_memory(ctx)
    layer_1_intel(ctx)
    layer_2_revenue_intel(ctx)
    layer_3_build(ctx)
    layer_4_publish(ctx)
    layer_5_collect(ctx)
    layer_6_synth(ctx)
    layer_7_report(ctx)

    elapsed = round(time.time() - t0)
    manifest = _save_cycle_manifest(ctx, elapsed)

    ok_count     = len(ctx.get("_ok", []))
    failed_count = len(ctx.get("_failed", []))
    total        = ok_count + failed_count

    print(f"\n{'='*55}")
    print(f"🧠 OMNIBUS done — {elapsed}s")
    print(f"   Engines: {ok_count}/{total} OK")
    print(f"   Health:  {ctx.get('prev_health')} → {ctx.get('health_score')}")
    print(f"   Revenue: ${ctx.get('total_revenue', 0):.2f}")
    if ctx.get("live_url"):
        print(f"   Live:    {ctx['live_url']}")
    if failed_count:
        print(f"   Failed:  {', '.join(ctx['_failed'])}")

    return manifest


if __name__ == "__main__":
    run()
