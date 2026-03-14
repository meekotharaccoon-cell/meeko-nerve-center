# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
ANALYTICS_ENGINE — track GitHub Pages views, referrers, popular paths

Sources: GitHub Traffic API (requires admin scope on GITHUB_TOKEN)
Outputs: data/analytics_state.json, data/analytics_history.json
"""
import os, json, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA    = Path("data"); DATA.mkdir(exist_ok=True)
STATE   = DATA / "analytics_state.json"
HISTORY = DATA / "analytics_history.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "meekotharaccoon-cell"
REPO  = "meeko-nerve-center"
API   = f"https://api.github.com/repos/{OWNER}/{REPO}"


def gh(path):
    if not GITHUB_TOKEN: return None
    try:
        req = urllib.request.Request(f"{API}{path}")
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-Analytics/1.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 403: print(f"  403 on {path} — need repo admin scope")
        return None
    except Exception as e:
        print(f"  Error {path}: {e}"); return None


def run():
    print("ANALYTICS_ENGINE starting...")
    if not GITHUB_TOKEN:
        print("  SKIP: GITHUB_TOKEN not set"); return

    views     = gh("/traffic/views") or {}
    clones    = gh("/traffic/clones") or {}
    referrers = gh("/traffic/referrers") or []
    paths     = gh("/traffic/popular/paths") or []
    repo_info = gh("") or {}

    stars    = repo_info.get("stargazers_count", 0)
    forks    = repo_info.get("forks_count", 0)
    watchers = repo_info.get("subscribers_count", 0)

    total_views  = views.get("count", 0)
    unique_views = views.get("uniques", 0)
    view_data    = views.get("views", [])
    total_clones  = clones.get("count", 0)
    unique_clones = clones.get("uniques", 0)

    top_refs  = sorted(referrers, key=lambda x: x.get("count", 0), reverse=True)[:5]
    top_paths = sorted(paths, key=lambda x: x.get("count", 0), reverse=True)[:5]

    def week_sum(data, offset=0):
        if not data: return 0
        days = sorted(data, key=lambda x: x.get("timestamp", ""))
        chunk = days[-(14 - offset*7):(len(days) - offset*7) or None]
        return sum(d.get("count", 0) for d in chunk)

    this_week = week_sum(view_data, 0)
    last_week = week_sum(view_data, 1)
    trend     = "up" if this_week > last_week else "down" if this_week < last_week else "flat"
    trend_pct = round((this_week - last_week) / max(last_week, 1) * 100)

    state = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stars": stars, "forks": forks, "watchers": watchers,
        "views_14d_total": total_views, "views_14d_unique": unique_views,
        "clones_14d_total": total_clones, "clones_14d_unique": unique_clones,
        "this_week_views": this_week, "last_week_views": last_week,
        "trend": trend, "trend_pct": trend_pct,
        "top_referrers": top_refs, "top_paths": top_paths,
        "view_data": view_data[-14:],
    }
    STATE.write_text(json.dumps(state, indent=2))

    hist = []
    if HISTORY.exists():
        try: hist = json.loads(HISTORY.read_text())
        except: pass
    hist.append({"ts": state["ts"], "stars": stars, "views": total_views,
                 "unique": unique_views, "trend": trend, "trend_pct": trend_pct})
    HISTORY.write_text(json.dumps(hist[-90:], indent=2))

    print(f"  Stars: {stars} | Forks: {forks} | Watchers: {watchers}")
    print(f"  Views 14d: {total_views} ({unique_views} unique) | Trend: {trend} {trend_pct:+}%")
    if top_refs: print(f"  Top referrer: {top_refs[0].get('referrer','?')} ({top_refs[0].get('count',0)})")
    if top_paths: print(f"  Top page: {top_paths[0].get('path','?')} ({top_paths[0].get('count',0)})")


if __name__ == "__main__":
    run()
