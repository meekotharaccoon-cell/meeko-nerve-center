# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
SOLARPUNK_CLI — terminal dashboard showing live system state

Run: python mycelium/SOLARPUNK_CLI.py

Reads entirely from data/*.json — no API calls, instant.
Refreshes every 30s. Ctrl+C to exit.
"""
import json, time, os
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data")


def rj(path, fb=None):
    try: return json.loads((DATA / path).read_text())
    except: return fb or {}


def bar(val, max_val=100, width=28, fill="█", empty="░"):
    filled = int(width * val / max(max_val, 1))
    return fill * filled + empty * (width - filled)


def c(text, code): return f"\033[{code}m{text}\033[0m"


def render():
    os.system("cls" if os.name == "nt" else "clear")

    omnibus   = rj("omnibus_last.json")
    resonance = rj("resonance_state.json")
    flywheel  = rj("flywheel_state.json")
    daemon    = rj("desktop_daemon_state.json")
    spider    = rj("repo_spider_state.json")
    analytics = rj("analytics_state.json")
    secrets   = rj("secrets_checker_state.json")
    asks_raw  = rj("asks_queue.json")
    asks      = asks_raw if isinstance(asks_raw, list) else []
    quick_rev = rj("quick_revenue.json")
    fc        = rj("first_contact.json")

    health     = omnibus.get("health_after", 0)
    res_score  = resonance.get("resonance_score", 0)
    res_label  = resonance.get("resonance_label", "SILENT")
    stars      = resonance.get("github", {}).get("stars", 0)
    rev_total  = flywheel.get("total_routed_usd", 0)
    gaza_total = flywheel.get("total_to_gaza_usd", 0)
    cycle_num  = omnibus.get("cycle_number", 0)
    version    = omnibus.get("version", "?")
    ok_count   = len(omnibus.get("engines_ok", []))
    fail_count = len(omnibus.get("engines_failed", []))
    skip_count = len(omnibus.get("engines_skipped", []))
    last_run   = omnibus.get("completed", "")[:16].replace("T", " ")
    daemon_st  = daemon.get("status", "unknown")
    daemon_tasks = daemon.get("tasks_completed", 0)
    repos_forked = len(spider.get("forked", []))
    views_14d  = analytics.get("views_14d_total", 0)
    trend      = analytics.get("trend", "?")
    trend_pct  = analytics.get("trend_pct", 0)
    missing    = secrets.get("critical_missing", [])
    pending_asks = [a for a in asks if a.get("status") == "pending"]
    first_sale = quick_rev.get("first_sale_done", False)
    first_contact = fc.get("happened", False)

    ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    health_col = "92" if health >= 70 else "93" if health >= 40 else "91"

    print(c("╔══════════════════════════════════════════════════════════╗", "36"))
    print(c("║        🌱 SOLARPUNK NERVE CENTER — LIVE STATUS           ║", "36"))
    print(c("╚══════════════════════════════════════════════════════════╝", "36"))
    print(f"  {c(ts_now,'90')}  |  {version}  |  Cycle #{cycle_num}")
    print(f"  Last run: {last_run} UTC\n")

    h_col = "92" if health >= 70 else "93" if health >= 40 else "91"
    r_col = "92" if res_score >= 60 else "93" if res_score >= 30 else "90"
    print(f"  Health    [{bar(health)}] {c(str(health)+'/100', h_col)}")
    print(f"  Resonance [{bar(res_score)}] {c(str(res_score)+'/100', r_col)}  {c(res_label,'93')}\n")

    print(f"  Revenue:  ${rev_total:.4f}   {'🎉 FIRST SALE!' if first_sale else c('(no sales yet)','90')}")
    print(f"  → Gaza:   ${gaza_total:.4f}   {c('15% to PCRF — hardcoded','92')}")
    print(f"  Stars: {stars}  |  Views 14d: {views_14d}  |  Trend: {trend} {trend_pct:+}%")
    print(f"  Repos forked: {repos_forked}  |  Asks pending: {len(pending_asks)}\n")

    print(f"  Engines:  {c(str(ok_count)+' OK','92')}  |  "
          f"{c(str(fail_count)+' failed','91') if fail_count else c('0 failed','90')}  |  "
          f"{skip_count} skipped")
    failed = omnibus.get("engines_failed", [])
    if failed:
        print(f"  Failed:   {c(', '.join(failed[:6]),'91')}")

    daemon_col = "92" if daemon_st == "running" else "91"
    print(f"\n  Daemon:   {c(daemon_st, daemon_col)}  |  Tasks done: {daemon_tasks}")

    if first_contact:
        print(c(f"\n  *** FIRST CONTACT: {fc.get('stranger','?')} ***", "95"))

    if pending_asks:
        print(f"\n  {c('PENDING ASKS:','93')}")
        for ask in pending_asks[:3]:
            print(f"    [{ask.get('channel','?'):8s}] {ask.get('content','')[:65]}...")

    if missing:
        print(f"\n  {c('MISSING SECRETS:','91')} {', '.join(missing)}")

    print(f"\n  {c('https://meekotharaccoon-cell.github.io/meeko-nerve-center','34')}")
    print(f"  {c('Press Ctrl+C to exit | Refreshes every 30s','90')}")


def main():
    try:
        while True:
            render()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\n  SolarPunk CLI closed.")


if __name__ == "__main__":
    main()
