#!/usr/bin/env python3
"""
FREE_API_ENGINE.py — Zero-auth public API connector
====================================================
Connects to 20+ free APIs with ZERO secrets required.
Harvests data, finds opportunities, feeds all other engines.
Runs every OMNIBUS cycle.
"""
import os, json, time, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

FREE_APIS = [
    {"name": "coingecko_global",    "url": "https://api.coingecko.com/api/v3/global",                         "key": "data"},
    {"name": "coingecko_trending",  "url": "https://api.coingecko.com/api/v3/search/trending",                "key": "coins"},
    {"name": "hn_top",              "url": "https://hacker-news.firebaseio.com/v0/topstories.json",           "key": None},
    {"name": "github_events",       "url": "https://api.github.com/events?per_page=10",                      "key": None},
    {"name": "hf_trending_models",  "url": "https://huggingface.co/api/models?sort=downloads&limit=10",      "key": None},
    {"name": "hf_trending_spaces",  "url": "https://huggingface.co/api/spaces?sort=likes&limit=10",          "key": None},
    {"name": "exchange_rates",      "url": "https://open.er-api.com/v6/latest/USD",                          "key": "rates"},
    {"name": "github_topics_ai",    "url": "https://api.github.com/search/repositories?q=topic:ai-agent&sort=stars&per_page=5", "key": "items"},
    {"name": "github_topics_agent", "url": "https://api.github.com/search/repositories?q=topic:autonomous-agent&sort=stars&per_page=5", "key": "items"},
    {"name": "devto_ai",            "url": "https://dev.to/api/articles?tag=ai&per_page=5",                  "key": None},
    {"name": "devto_python",        "url": "https://dev.to/api/articles?tag=python&per_page=5",              "key": None},
    {"name": "devto_webdev",        "url": "https://dev.to/api/articles?tag=webdev&per_page=5",              "key": None},
    {"name": "open_library_ai",     "url": "https://openlibrary.org/search.json?q=ai+agents&limit=5",        "key": "docs"},
    {"name": "wikipedia_ai",        "url": "https://en.wikipedia.org/api/rest_v1/page/summary/Artificial_intelligence", "key": None},
    {"name": "nominatim_hq",        "url": "https://nominatim.openstreetmap.org/search?q=gaza&format=json&limit=1", "key": None},
    {"name": "public_apis_list",    "url": "https://api.publicapis.org/entries?category=Finance&https=true", "key": "entries"},
    {"name": "joke_api",            "url": "https://v2.jokeapi.dev/joke/Programming?safe-mode",              "key": None},
    {"name": "advice_api",          "url": "https://api.adviceslip.com/advice",                              "key": "slip"},
    {"name": "github_gists_trending","url": "https://api.github.com/gists/public?per_page=5",                "key": None},
    {"name": "npm_downloads",       "url": "https://api.npmjs.org/downloads/point/last-week/react",          "key": None},
]

state_file = DATA / "free_api_state.json"


def fetch(api):
    try:
        r = requests.get(api["url"], timeout=10, headers={"User-Agent": "SolarPunk/1.0"})
        r.raise_for_status()
        data = r.json()
        if api["key"] and isinstance(data, dict):
            data = data.get(api["key"], data)
        return data
    except Exception as e:
        return {"error": str(e)[:100]}


def extract_signals(results):
    signals = []

    hf_models = results.get("hf_trending_models", [])
    if isinstance(hf_models, list):
        for m in hf_models[:5]:
            if isinstance(m, dict):
                signals.append({"type": "trending_model", "name": m.get("id", ""), "downloads": m.get("downloads", 0)})

    hf_spaces = results.get("hf_trending_spaces", [])
    if isinstance(hf_spaces, list):
        for s in hf_spaces[:3]:
            if isinstance(s, dict):
                signals.append({"type": "trending_space", "name": s.get("id", ""), "likes": s.get("likes", 0)})

    gh_ai = results.get("github_topics_ai", [])
    if isinstance(gh_ai, list):
        for r in gh_ai[:3]:
            if isinstance(r, dict):
                signals.append({"type": "github_ai_repo", "repo": r.get("full_name", ""), "stars": r.get("stargazers_count", 0)})

    devto = results.get("devto_ai", [])
    if isinstance(devto, list):
        for a in devto[:3]:
            if isinstance(a, dict):
                signals.append({"type": "trending_article", "title": a.get("title", ""), "reactions": a.get("positive_reactions_count", 0)})

    cg = results.get("coingecko_global", {})
    if isinstance(cg, dict):
        mc = cg.get("total_market_cap", {})
        if isinstance(mc, dict):
            signals.append({"type": "crypto_market_cap_usd", "value": mc.get("usd", 0)})

    apis = results.get("public_apis_list", [])
    if isinstance(apis, list):
        for a in apis[:3]:
            if isinstance(a, dict):
                signals.append({"type": "free_api", "name": a.get("API", ""), "desc": a.get("Description", "")[:80]})

    return signals


def generate_opportunities(signals):
    opps = []
    for s in signals:
        if s["type"] == "trending_model":
            opps.append(f"Guide/tutorial product: '{s['name']}' ({s['downloads']:,} downloads) — build how-to guide")
        elif s["type"] == "trending_space":
            opps.append(f"Clone/extend HF space: '{s['name']}' ({s['likes']} likes) — integrate into SolarPunk")
        elif s["type"] == "github_ai_repo":
            opps.append(f"Engine wrapper: {s['repo']} ({s['stars']} stars) — build integration engine")
        elif s["type"] == "trending_article":
            opps.append(f"Content leverage: '{s['title'][:60]}' ({s['reactions']} reactions) — create SolarPunk angle")
        elif s["type"] == "free_api":
            opps.append(f"Free API to integrate: {s['name']} — {s['desc'][:60]}")
    return opps


def build_page(signals, opps, ok, failed):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    opp_li = "".join(f"<li>{o}</li>" for o in opps)
    sig_rows = "".join(f"<tr><td>{s['type']}</td><td>{str(s)[:120]}</td></tr>" for s in signals[:25])
    html = f"""<!DOCTYPE html><html><head><title>SolarPunk Free API Signals</title>
<meta charset=utf-8><style>body{{font-family:monospace;background:#0a0a0a;color:#0f0;padding:20px}}
h1,h2{{color:#0f0}}table{{width:100%;border-collapse:collapse}}td{{padding:6px;border:1px solid #333}}
li{{margin:6px 0}}.stat{{display:inline-block;margin:8px;padding:8px 16px;border:1px solid #0f0}}</style></head><body>
<h1>📡 FREE API SIGNALS — {ts}</h1>
<div><span class="stat">APIs OK: {ok}</span><span class="stat">Failed: {failed}</span><span class="stat">Signals: {len(signals)}</span></div>
<h2>🚨 Opportunities ({len(opps)})</h2><ul>{opp_li}</ul>
<h2>📊 Raw Signals</h2>
<table><tr><th>Type</th><th>Data</th></tr>{sig_rows}</table>
</body></html>"""
    (DOCS / "opportunities.html").write_text(html)


def run():
    print("FREE_API_ENGINE — connecting to public APIs...")
    results = {}
    ok, failed = 0, 0
    for api in FREE_APIS:
        data = fetch(api)
        results[api["name"]] = data
        if isinstance(data, dict) and "error" in data:
            failed += 1
        else:
            ok += 1

    signals = extract_signals(results)
    opps = generate_opportunities(signals)
    build_page(signals, opps, ok, failed)

    state = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "apis_ok": ok, "apis_failed": failed,
        "signals": signals,
        "opportunities": opps,
        "raw_keys": list(results.keys()),
    }
    state_file.write_text(json.dumps(state, indent=2, default=str))
    print(f"  APIs: {ok} ok | {failed} failed | Signals: {len(signals)} | Opps: {len(opps)}")
    if opps:
        print(f"  Top: {opps[0][:80]}")
    print("FREE_API_ENGINE done")


if __name__ == "__main__":
    run()
