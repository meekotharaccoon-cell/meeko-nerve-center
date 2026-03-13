#!/usr/bin/env python3
"""
OMNIBUS v24 — NANOSHOPS + PASSIVE INCOME ARCHITECT + DIGEST FIXED
=================================================================
New in v24:
  NANOSHOP_ENGINE        (L4) — generates embeddable 1-click purchase widgets
                                 docs/nanoshop.js + docs/ns/{id}.html + embed.html
  PASSIVE_INCOME_ARCHITECT(L6)— invents new income streams using real capabilities
                                 asks Groq, scores ideas, queues top 3 for SELF_BUILDER
  NIGHTLY_DIGEST v2      (L7) — 1 email/day max, real revenue only, delta diffs,
                                 [ESTIMATE] labels, alerts section

v23: PROOF_LEDGER, STOREFRONT_BUILDER, Gaza Rose 7-pack
v22: PDF_GENERATOR, GITHUB_RELEASES_PUBLISHER, GUMROAD_PRODUCT_PUBLISHER, PRODUCT_DELIVERY_ENGINE
v21: BLUESKY_ENGINE, MASTODON_ENGINE, AUTONOMOUS_PUBLISHER, FIRST_SALE_NOTIFIER
v20: NARRATOR, PLUGIN_REGISTRY
v19: NEWSLETTER_ENGINE, ANALYTICS_ENGINE, RSS_PUBLISHER, FORK_SCANNER
v18: REPO_SPIDER, RESONANCE_CONVERTER, @claude GitHub Issues
v17: DESKTOP_DAEMON, CLAUDE_BRIDGE

The loop: build -> speak -> listen -> remember -> watch -> respond -> grow -> tell -> prove -> expand

L0  CYCLE_MEMORY . GUARDIAN . ENGINE_INTEGRITY . SECRETS_CHECKER . BOTTLENECK_SCANNER
    AUTO_HEALER . CAPABILITY_SCANNER . AGENT_LINK_VERIFIER . PLUGIN_REGISTRY . REVENUE_AUDIT
L1  EMAIL_BRAIN . SCAM_SHIELD . CALENDAR_BRAIN . CONTENT_HARVESTER .
    AI_WATCHER . CRYPTO_WATCHER . FREE_API_ENGINE .
    RESONANCE_ENGINE . ANALYTICS_ENGINE . REPO_SPIDER . FORK_SCANNER . FIRST_CONTACT .
    NEURON_A . NEURON_B
L2  GRANT_HUNTER . ETSY_SEO_ENGINE . INCOME_ARCHITECT . REVENUE_FLYWHEEL .
    GUMROAD_AUTO_QUEUE . QUICK_REVENUE . BUSINESS_FACTORY
L3  LANDING_DEPLOYER . ART_CATALOG . REVENUE_LOOP . ART_GENERATOR .
    EMAIL_AGENT_EXCHANGE . GRANT_APPLICANT . HEALTH_BOOSTER .
    AGENT_GUMROAD_BUILDER . PDF_GENERATOR . GITHUB_RELEASES_PUBLISHER
L4  SOCIAL_PROMOTER . BLUESKY_ENGINE . MASTODON_ENGINE .
    AUTONOMOUS_PUBLISHER . SUBSTACK_ENGINE . LINK_PAGE . GITHUB_POSTER .
    SOCIAL_DASHBOARD . CONNECTION_FORGE . HUMAN_CONNECTOR . AFFILIATE_MAXIMIZER .
    STORE_BUILDER . BRIDGE_BUILDER . EMAIL_OUTREACH . VIRALITY_ENGINE .
    DEV_TO_PUBLISHER . AGENT_TWEET_WRITER . RESONANCE_CONVERTER . NEWSLETTER_ENGINE .
    NANOSHOP_ENGINE [v24]
L5  KOFI_ENGINE . GUMROAD_ENGINE . GUMROAD_PRODUCT_PUBLISHER . GITHUB_SPONSORS_ENGINE .
    KOFI_PAYMENT_TRACKER . DISPATCH_HANDLER . HUMAN_PAYOUT .
    CONTRIBUTOR_REGISTRY . PAYPAL_PAYOUT . FIRST_SALE_NOTIFIER .
    PRODUCT_DELIVERY_ENGINE . PROOF_LEDGER . STOREFRONT_BUILDER
L6  SYNAPSE . SYNTHESIS_FACTORY . ARCHITECT . SELF_BUILDER .
    KNOWLEDGE_BRIDGE . KNOWLEDGE_WEAVER . REVENUE_OPTIMIZER . BIG_BRAIN_ORACLE .
    SWARM_COORDINATOR .
    PASSIVE_INCOME_ARCHITECT [v24]
L7  MEMORY_PALACE . README_GENERATOR . BRIEFING_ENGINE . NIGHTLY_DIGEST .
    ISSUE_SYNC . SOLARPUNK_LEGAL . BRAND_LEGAL . TASK_ATOMIZER .
    AUTONOMY_PROOF . CLAUDE_ENGINE . SELF_PORTRAIT . RSS_PUBLISHER .
    NARRATOR
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
        "run_id":           os.environ.get("GITHUB_RUN_ID", f"local-{int(time.time())}"),
        "ts":               datetime.now(timezone.utc).isoformat(),
        "prev_health":      rj("brain_state.json").get("health_score", 40),
        "memory":           rj("memory_palace.json"),
        "cycle_delta":      rj("cycle_delta.json"),
        "neuron_a":         rj("neuron_a_report.json"),
        "neuron_b":         rj("neuron_b_report.json"),
        "flywheel":         rj("flywheel_summary.json"),
        "content":          rj("content_harvest.json"),
        "free_apis":        rj("free_api_state.json"),
        "grants":           rj("grants_found.json"),
        "loop_result":      rj("revenue_loop_last.json"),
        "exchange":         rj("email_exchange_state.json"),
        "biz_factory":      rj("business_factory_state.json"),
        "secrets":          rj("secrets_checker_state.json"),
        "bottlenecks":      rj("bottleneck_report.json"),
        "architect_plan":   rj("architect_plan.json"),
        "weaver":           rj("knowledge_weaver_state.json"),
        "optimizer":        rj("revenue_optimizer_state.json"),
        "revenue_inbox":    rj("revenue_inbox.json"),
        "capabilities":     rj("capability_map.json"),
        "outreach":         rj("outreach_state.json"),
        "resonance":        rj("resonance_state.json"),
        "quick_revenue":    rj("quick_revenue.json"),
        "first_contact":    rj("first_contact.json"),
        "link_verifier":    rj("agent_link_verifier_state.json"),
        "daemon_state":     rj("desktop_daemon_state.json"),
        "repo_spider":      rj("repo_spider_state.json"),
        "converter":        rj("resonance_converter_state.json"),
        "asks_queue":       rj("asks_queue.json"),
        "analytics":        rj("analytics_state.json"),
        "fork_scanner":     rj("fork_scanner_state.json"),
        "newsletter":       rj("newsletter_state.json"),
        "plugin_registry":  rj("plugin_registry.json"),
        "narrator":         rj("narrator_state.json"),
        "bluesky":          rj("bluesky_engine_state.json"),
        "mastodon":         rj("mastodon_state.json"),
        "publisher":        rj("autonomous_publisher_state.json"),
        "first_sale":       rj("first_sale_state.json"),
        "pdf_generator":    rj("pdf_generator_state.json"),
        "product_registry": rj("product_registry.json"),
        "delivery":         rj("delivery_engine_state.json"),
        "revenue_audit":    rj("revenue_audit.json"),
        "swarm":            rj("swarm_state.json"),
        "proof_ledger":     rj("proof_ledger.json"),
        "storefront":       rj("storefront_builder_state.json"),
        "nanoshop":         rj("nanoshop_state.json"),           # v24
        "passive_income":   rj("passive_income_state.json"),     # v24
        "engines_ok":       results["ok"][:],
        "engines_failed":   results["failed"][:],
    }


def save_ctx():
    (DATA / "ctx.json").write_text(json.dumps(ctx(), indent=2, default=str))


def _queue_daemon_task(prompt, source="OMNIBUS", priority=5):
    try:
        qfile = DATA / "claude_tasks_queue.json"
        queue = json.loads(qfile.read_text()) if qfile.exists() else []
        if not isinstance(queue, list): queue = []
        queue.append({"id": f"omnibus_{int(time.time())}", "prompt": prompt,
                      "priority": priority, "source": source, "status": "pending",
                      "queued_at": datetime.now(timezone.utc).isoformat()})
        qfile.write_text(json.dumps(queue, indent=2))
    except: pass


def L0():
    print("\n--- L0: REMEMBER + HEALTH + INTEGRITY ---")
    eng("CYCLE_MEMORY",       timeout=30)
    eng("GUARDIAN",           timeout=60)
    eng("ENGINE_INTEGRITY",   timeout=60)
    eng("SECRETS_CHECKER",    timeout=60)
    eng("BOTTLENECK_SCANNER", timeout=60)
    eng("AUTO_HEALER",        timeout=90)
    eng("CAPABILITY_SCANNER", timeout=30)
    eng("AGENT_LINK_VERIFIER",timeout=60)
    eng("PLUGIN_REGISTRY",    timeout=60)
    eng("REVENUE_AUDIT",      timeout=60)
    save_ctx()


def L1():
    print("\n--- L1: INTEL + LISTEN + WATCH ---")
    eng("EMAIL_BRAIN",        timeout=90)
    eng("SCAM_SHIELD",        timeout=60)
    eng("CALENDAR_BRAIN",     timeout=30)
    eng("CONTENT_HARVESTER",  timeout=90)
    eng("AI_WATCHER",         timeout=60)
    eng("CRYPTO_WATCHER",     timeout=60)
    eng("FREE_API_ENGINE",    timeout=60)
    eng("RESONANCE_ENGINE",   timeout=60)
    eng("ANALYTICS_ENGINE",   timeout=60)
    eng("REPO_SPIDER",        timeout=120)
    eng("FORK_SCANNER",       timeout=60)
    eng("FIRST_CONTACT",      timeout=30)
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
    print("\n--- L3: DEPLOY + LOOP + GENERATE PRODUCTS ---")
    eng("LANDING_DEPLOYER",         timeout=90)
    eng("ART_CATALOG",              timeout=60)
    eng("AGENT_GUMROAD_BUILDER",    timeout=60)
    save_ctx()
    eng("REVENUE_LOOP",             timeout=240)
    eng("ART_GENERATOR",            timeout=120)
    eng("EMAIL_AGENT_EXCHANGE",     timeout=120)
    eng("GRANT_APPLICANT",          timeout=90)
    eng("HEALTH_BOOSTER",           timeout=60)
    save_ctx()
    eng("PDF_GENERATOR",            timeout=600)
    save_ctx()
    eng("GITHUB_RELEASES_PUBLISHER",timeout=120)
    save_ctx()


def L4():
    print("\n--- L4: DISTRIBUTE + PUBLISH + BROADCAST + NANOSHOPS ---")
    eng("SOCIAL_PROMOTER",     timeout=90)
    eng("BLUESKY_ENGINE",      timeout=60)
    eng("MASTODON_ENGINE",     timeout=60)
    eng("AUTONOMOUS_PUBLISHER",timeout=90)
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
    eng("AGENT_TWEET_WRITER",  timeout=60)
    eng("RESONANCE_CONVERTER", timeout=90)
    eng("NEWSLETTER_ENGINE",   timeout=90)
    eng("NANOSHOP_ENGINE",     timeout=90)   # v24: builds embeddable micro-shops
    save_ctx()


def L5():
    print("\n--- L5: COLLECT + PUBLISH + DELIVER + PROVE ---")
    eng("KOFI_ENGINE",               timeout=60)
    eng("GUMROAD_ENGINE",            timeout=60)
    eng("GUMROAD_PRODUCT_PUBLISHER", timeout=90)
    eng("GITHUB_SPONSORS_ENGINE",    timeout=60)
    eng("KOFI_PAYMENT_TRACKER",      timeout=60)
    eng("DISPATCH_HANDLER",          timeout=60)
    eng("HUMAN_PAYOUT",              timeout=60)
    eng("CONTRIBUTOR_REGISTRY",      timeout=60)
    eng("PAYPAL_PAYOUT",             timeout=90)
    eng("FIRST_SALE_NOTIFIER",       timeout=30)
    eng("PRODUCT_DELIVERY_ENGINE",   timeout=90)
    eng("PROOF_LEDGER",              timeout=60)
    eng("STOREFRONT_BUILDER",        timeout=90)
    save_ctx()


def L6():
    print("\n--- L6: THINK + SELF-EXPAND + INVENT ---")
    save_ctx()
    eng("SYNAPSE",                  timeout=120); save_ctx()
    eng("SYNTHESIS_FACTORY",        timeout=120); save_ctx()
    eng("ARCHITECT",                timeout=120); save_ctx()
    eng("SELF_BUILDER",             timeout=240); save_ctx()
    eng("KNOWLEDGE_BRIDGE",         timeout=60)
    eng("KNOWLEDGE_WEAVER",         timeout=180); save_ctx()
    eng("REVENUE_OPTIMIZER",        timeout=120); save_ctx()
    eng("BIG_BRAIN_ORACLE",         timeout=90)
    eng("SWARM_COORDINATOR",        timeout=120); save_ctx()
    eng("PASSIVE_INCOME_ARCHITECT", timeout=120); save_ctx()  # v24: invents new streams

    health   = rj("brain_state.json").get("health_score", 0)
    cycle    = rj("cycle_delta.json").get("cycle_number", "?")
    registry = rj("product_registry.json")
    ledger   = rj("proof_ledger.json")
    bsky     = rj("bluesky_engine_state.json")
    pub      = rj("autonomous_publisher_state.json")
    pia      = rj("passive_income_state.json")
    nanoshop = rj("nanoshop_state.json")
    products_live = sum(1 for p in registry.get("products", {}).values()
                        if p.get("gumroad_url") or p.get("download_url"))
    _queue_daemon_task(
        f"Cycle {cycle} done. Health: {health}/100. "
        f"Products live: {products_live}. "
        f"Gaza fund: ${ledger.get('total_to_gaza', 0):.2f} | PCRF transferred: ${ledger.get('total_transferred', 0):.2f}. "
        f"Nanoshop pages: {nanoshop.get('pages_generated', 0)}. "
        f"Passive income ideas queued: {len(pia.get('queued_for_build', []))}. "
        f"Bluesky: {bsky.get('posted', 0)} | Published: {pub.get('total_sent', 0)}. "
        f"Shop: {BASE}/shop.html | Embed: {BASE}/embed.html",
        source="OMNIBUS_L6", priority=2
    )


def L7():
    print("\n--- L7: REPORT + PROOF + VOICE ---")
    eng("MEMORY_PALACE",    timeout=60)
    eng("README_GENERATOR", timeout=60)
    eng("BRIEFING_ENGINE",  timeout=60)
    eng("NIGHTLY_DIGEST",   timeout=120)  # v24: fixed — 1 email/day, real revenue, delta
    eng("ISSUE_SYNC",       timeout=90)
    eng("SOLARPUNK_LEGAL",  timeout=60)
    eng("BRAND_LEGAL",      timeout=60)
    eng("TASK_ATOMIZER",    timeout=120)
    eng("AUTONOMY_PROOF",   timeout=60)
    eng("CLAUDE_ENGINE",    timeout=60)
    eng("SELF_PORTRAIT",    timeout=60)
    eng("RSS_PUBLISHER",    timeout=30)
    eng("NARRATOR",         timeout=60)
    save_ctx()


def run_bonus_engines():
    weaver = rj("knowledge_weaver_state.json")
    built  = weaver.get("engines_built", [])
    # Also check passive_income_architect queued engines
    pia    = rj("passive_income_state.json")
    pia_queued = [q.get("engine_name","") for q in
                  rj("self_builder_queue.json", []) if isinstance(rj("self_builder_queue.json",[]),list)]
    known  = set(results["ok"] + results["failed"] + results["skipped"])
    for name in list(set(built)):
        if name not in known and (MYCELIUM / f"{name}.py").exists():
            print(f"\n--- BONUS: {name} (auto-built) ---")
            eng(name, timeout=120)
            save_ctx()


def run():
    t0     = time.time()
    run_id = os.environ.get("GITHUB_RUN_ID", f"local-{int(t0)}")
    ts     = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print(f"\nOMNIBUS v24 -- {ts}")
    print(f"   Run: {run_id}")
    print(f"   build -> speak -> listen -> remember -> watch -> respond -> grow -> tell -> prove -> expand")
    print(f"   NEW: NANOSHOP_ENGINE + PASSIVE_INCOME_ARCHITECT + NIGHTLY_DIGEST fixed")
    print(f"   Embed: {BASE}/embed.html | Shop: {BASE}/shop.html")
    print("=" * 60)

    for layer in [L0, L1, L2, L3, L4, L5, L6, L7]:
        try: layer()
        except Exception as e: print(f"  LAYER ERROR: {e}")

    run_bonus_engines()

    elapsed    = round(time.time() - t0)
    total      = len(results["ok"]) + len(results["failed"])
    secrets    = rj("secrets_checker_state.json")
    revenue    = rj("revenue_inbox.json")
    payouts    = rj("payout_ledger.json")
    legal      = rj("brand_legal_state.json")
    bottleneck = rj("bottleneck_report.json")
    weaver     = rj("knowledge_weaver_state.json")
    outreach   = rj("outreach_state.json")
    resonance  = rj("resonance_state.json")
    cycle_mem  = rj("cycle_delta.json")
    fc         = rj("first_contact.json")
    daemon     = rj("desktop_daemon_state.json")
    spider     = rj("repo_spider_state.json")
    analytics  = rj("analytics_state.json")
    fork_sc    = rj("fork_scanner_state.json")
    newsletter = rj("newsletter_state.json")
    narrator   = rj("narrator_state.json")
    plugins    = rj("plugin_registry.json")
    bsky       = rj("bluesky_engine_state.json")
    mast       = rj("mastodon_state.json")
    pub        = rj("autonomous_publisher_state.json")
    first_sale = rj("first_sale_state.json")
    registry   = rj("product_registry.json")
    delivery   = rj("delivery_engine_state.json")
    ledger     = rj("proof_ledger.json")
    nanoshop   = rj("nanoshop_state.json")    # v24
    pia        = rj("passive_income_state.json")  # v24
    asks       = rj("asks_queue.json") if isinstance(rj("asks_queue.json"), list) else []

    rev_total   = revenue.get("total_received", 0) if isinstance(revenue, dict) else 0
    gaza_total  = ledger.get("total_to_gaza", 0) or (revenue.get("total_to_gaza", 0) if isinstance(revenue, dict) else 0)
    health_now  = rj("brain_state.json").get("health_score", 0)
    emails_out  = len([e for e in outreach.get("sent", []) if e.get("sent")])
    fc_happened = fc.get("happened", False) if isinstance(fc, dict) else False
    fs_happened = first_sale.get("happened", False) if isinstance(first_sale, dict) else False
    products_ready = sum(1 for p in registry.get("products", {}).values() if p.get("content_ready"))
    products_live  = sum(1 for p in registry.get("products", {}).values()
                         if p.get("gumroad_url") or p.get("download_url"))

    manifest = {
        "version":                  "v24",
        "run_id":                   run_id,
        "completed":                datetime.now(timezone.utc).isoformat(),
        "elapsed_s":                elapsed,
        "health_before":            rj("brain_state.json").get("health_score", 40),
        "health_after":             health_now,
        "health_trend":             cycle_mem.get("health_trend", "unknown"),
        "cycle_number":             cycle_mem.get("cycle_number", 0),
        "products_content_ready":   products_ready,
        "products_with_live_urls":  products_live,
        "deliveries_sent":          delivery.get("total_delivered", 0),
        "total_to_gaza":            gaza_total,
        "total_transferred_pcrf":   ledger.get("total_transferred", 0),
        "pending_transfer":         ledger.get("pending_transfer", 0),
        "nanoshop_pages":           nanoshop.get("pages_generated", 0),     # v24
        "nanoshop_indexed":         nanoshop.get("products_indexed", 0),    # v24
        "passive_income_ideas":     len(pia.get("all_ideas", {})),          # v24
        "passive_income_queued":    len(pia.get("queued_for_build", [])),   # v24
        "shop_url":                 f"{BASE}/shop.html",
        "proof_url":                f"{BASE}/proof.html",
        "embed_url":                f"{BASE}/embed.html",                   # v24
        "nanoshop_widget":          f"{BASE}/nanoshop.js",                  # v24
        "businesses_built":         len(list(DATA.glob("business_*.json"))),
        "live_url":                 rj("revenue_loop_last.json").get("live_url"),
        "total_revenue":            rev_total,
        "first_sale_happened":      fs_happened,
        "first_sale_amount":        first_sale.get("amount", 0) if isinstance(first_sale, dict) else 0,
        "first_contact_happened":   fc_happened,
        "first_contact_who":        fc.get("stranger") if fc_happened else None,
        "legal_fund":               legal.get("upto_fund_collected", 0),
        "total_paid_out":           payouts.get("total_paid_usd", 0) if isinstance(payouts, dict) else 0,
        "secrets_configured":       secrets.get("configured", 0),
        "critical_missing":         secrets.get("critical_missing", []),
        "bottleneck_count":         bottleneck.get("summary", {}).get("total_bottlenecks", 0),
        "engines_auto_built":       weaver.get("engines_built", []),
        "outreach_sent":            emails_out,
        "resonance_score":          resonance.get("resonance_score", 0),
        "resonance_label":          resonance.get("resonance_label", "SILENT"),
        "github_stars":             resonance.get("github", {}).get("stars", 0),
        "persistent_blockers":      len(cycle_mem.get("persistent", [])),
        "daemon_status":            daemon.get("status", "not_started"),
        "repos_forked":             len(spider.get("forked", [])),
        "asks_pending":             len([a for a in asks if a.get("status") == "pending"]),
        "views_14d":                analytics.get("views_14d_total", 0),
        "view_trend":               analytics.get("trend", "unknown"),
        "new_forkers":              len(fork_sc.get("forkers", [])),
        "newsletter_sent_total":    newsletter.get("total_sent", 0),
        "stories_told":             narrator.get("stories_told", 0),
        "plugins_registered":       plugins.get("total_registered", 0),
        "bluesky_posted":           bsky.get("posted", 0),
        "mastodon_posted":          mast.get("posted", 0),
        "total_published":          pub.get("total_sent", 0),
        "channels_active":          pub.get("by_channel", {}),
        "rss_feed_url":             f"{BASE}/feed.xml",
        "engines_ok":               results["ok"],
        "engines_failed":           results["failed"],
        "engines_skipped":          results["skipped"],
        "log":                      results["log"],
    }

    (DATA / "omnibus_last.json").write_text(json.dumps(manifest, indent=2))
    hf   = DATA / "omnibus_history.json"
    hist = json.loads(hf.read_text()) if hf.exists() else []
    hist.append({k: v for k, v in manifest.items() if k != "log"})
    hf.write_text(json.dumps(hist[-200:], indent=2))

    print(f"\n{'='*60}")
    print(f"OMNIBUS v24 done -- {elapsed}s")
    print(f"   {len(results['ok'])}/{total} OK | {len(results['skipped'])} skipped")
    if results["failed"]:
        print(f"   FAILED: {', '.join(results['failed'])}")
    print(f"   Health: {manifest['health_before']} -> {manifest['health_after']}")
    print(f"   Revenue: ${rev_total:.2f} | Gaza: ${gaza_total:.2f} | PCRF: ${manifest['total_transferred_pcrf']:.2f}")
    print(f"   First sale: {'$' + str(manifest['first_sale_amount']) if fs_happened else 'waiting'}")
    print(f"   Products: {products_ready} ready | {products_live} live | {manifest['deliveries_sent']} delivered")
    print(f"   Nanoshop: {manifest['nanoshop_pages']} pages | {manifest['nanoshop_indexed']} indexed")
    print(f"   Passive income: {manifest['passive_income_ideas']} ideas | {manifest['passive_income_queued']} queued to build")
    print(f"   Shop: {manifest['shop_url']}")
    print(f"   Embed: {manifest['embed_url']}")
    print(f"   Resonance: {manifest['resonance_score']}/100 | Stars: {manifest['github_stars']}")
    print(f"   Published: {manifest['total_published']} | Bluesky: {manifest['bluesky_posted']}")
    if fc_happened:
        print(f"   *** FIRST CONTACT: {fc.get('stranger')} ***")
    if manifest["engines_auto_built"]:
        print(f"   Auto-built: {', '.join(manifest['engines_auto_built'])}")
    if manifest["critical_missing"]:
        print(f"   MISSING SECRETS: {', '.join(manifest['critical_missing'])}")
    return manifest


if __name__ == "__main__":
    run()
