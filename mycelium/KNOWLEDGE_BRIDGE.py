#!/usr/bin/env python3
"""
KNOWLEDGE_BRIDGE.py — Maps all engine connections. Finds gaps. Suggests bridges.

Every engine reads and writes JSON files in data/.
This engine reads ALL engine source code and:
  1. Maps what each engine READS from data/
  2. Maps what each engine WRITES to data/
  3. Finds GAPS: files written but not read, files read but not written
  4. Suggests bridge engines to fill gaps
  5. Builds docs/knowledge_map.html — visual connection table
  6. Writes data/knowledge_gaps.json for SELF_BUILDER to act on
"""
import re, json
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")


def scan_engine(path):
    try: code = path.read_text()
    except: return {"reads": [], "writes": []}
    reads, writes = set(), set()
    for m in re.finditer(r'["\']data/([\w_.-]+\.json)["\']', code):
        fname = m.group(1)
        start = max(0, m.start() - 150)
        end = min(len(code), m.end() + 150)
        ctx = code[start:end]
        if any(w in ctx for w in ["write_text", ".write(", "json.dumps"]):
            writes.add(fname)
        else:
            reads.add(fname)
    return {"reads": sorted(reads - writes), "writes": sorted(writes)}


def build_map():
    engines = {}
    for py in sorted(MYCELIUM.glob("*.py")):
        if py.name.startswith("__"): continue
        info = scan_engine(py)
        if info["reads"] or info["writes"]:
            engines[py.name] = info

    file_readers, file_writers = {}, {}
    for engine, info in engines.items():
        for f in info["reads"]:
            file_readers.setdefault(f, []).append(engine)
        for f in info["writes"]:
            file_writers.setdefault(f, []).append(engine)

    all_files = set(file_readers) | set(file_writers)
    gaps = {
        "written_but_not_read": sorted(set(file_writers) - set(file_readers)),
        "read_but_not_written": sorted(set(file_readers) - set(file_writers)),
    }
    bridges = []
    for f in gaps["read_but_not_written"]:
        bridges.append({
            "gap": f"data/{f} is NEEDED by {file_readers[f]} but nothing writes it",
            "suggestion": f"Build a generator engine that creates/maintains data/{f}",
            "priority": "critical"
        })
    for f in gaps["written_but_not_read"]:
        bridges.append({
            "gap": f"data/{f} is written by {file_writers[f]} but nothing reads it",
            "suggestion": f"Build a consumer engine that reads data/{f} and acts on it",
            "priority": "high"
        })
    return engines, file_readers, file_writers, all_files, gaps, bridges


def build_html(engines, file_readers, file_writers, gaps, bridges):
    gap_html = ""
    for b in bridges[:12]:
        color = "#ff2d6b" if b["priority"] == "critical" else "#ffd700"
        gap_html += (
            f'<div style="border-left:3px solid {color};background:rgba(255,255,255,.03);'
            f'border-radius:6px;padding:10px 14px;margin-bottom:8px;font-size:.76rem;line-height:1.7">'
            f'<b style="color:{color}">[{b["priority"].upper()}]</b> {b["gap"]}<br>'
            f'<span style="color:rgba(255,255,255,.4)">{b["suggestion"]}</span></div>'
        )

    rows = ""
    for engine, info in sorted(engines.items()):
        reads = " ".join(
            f'<span style="background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.2);'
            f'border-radius:3px;padding:1px 6px;font-size:.65rem;color:#00ff88;margin:2px;display:inline-block">{f}</span>'
            for f in info["reads"]
        ) or '<span style="color:rgba(255,255,255,.15)">—</span>'
        writes = " ".join(
            f'<span style="background:rgba(255,107,138,.08);border:1px solid rgba(255,107,138,.2);'
            f'border-radius:3px;padding:1px 6px;font-size:.65rem;color:#ff6b8a;margin:2px;display:inline-block">{f}</span>'
            for f in info["writes"]
        ) or '<span style="color:rgba(255,255,255,.15)">—</span>'
        rows += f'<tr><td style="color:#00ff88;font-weight:700;white-space:nowrap">{engine.replace(".py","")}</td><td>{reads}</td><td>{writes}</td></tr>'

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk™ Knowledge Map</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#05050e;color:#ccd;font-family:-apple-system,sans-serif;padding:20px;max-width:1000px;margin:0 auto}}
h1{{color:#00ff88;font-size:1.5rem;margin-bottom:4px}}
.sub{{color:rgba(255,255,255,.3);font-size:.8rem;margin-bottom:24px}}
h2{{color:#ffd700;font-size:.95rem;margin:24px 0 10px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
.stat{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:8px;padding:12px 16px;text-align:center;min-width:100px}}
.stat .n{{font-size:1.4rem;font-weight:900;color:#00ff88}}
.stat .l{{font-size:.65rem;color:rgba(255,255,255,.3)}}
table{{width:100%;border-collapse:collapse;font-size:.75rem}}
th{{background:rgba(255,255,255,.04);padding:8px 10px;text-align:left;color:rgba(255,255,255,.4)}}
td{{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.04);vertical-align:top}}
footer{{text-align:center;padding:20px;color:rgba(255,255,255,.18);font-size:.7rem;margin-top:20px}}
footer a{{color:#ff6b8a;text-decoration:none}}
nav{{margin-bottom:20px;display:flex;gap:12px}}
nav a{{color:rgba(255,255,255,.3);text-decoration:none;font-size:.8rem}}
nav a:hover{{color:#00ff88}}
</style></head><body>
<nav><a href="index.html">Home</a><a href="dashboard.html">Dashboard</a><a href="setup.html">Setup</a></nav>
<h1>🧠 SolarPunk™ Knowledge Map</h1>
<p class="sub">Auto-generated by KNOWLEDGE_BRIDGE · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
<div class="stats">
  <div class="stat"><div class="n">{len(engines)}</div><div class="l">Connected Engines</div></div>
  <div class="stat"><div class="n">{len(set(file_readers)|set(file_writers))}</div><div class="l">Data Files</div></div>
  <div class="stat"><div class="n">{len(gaps.get('read_but_not_written',[]))}</div><div class="l">Critical Gaps</div></div>
  <div class="stat"><div class="n">{len(bridges)}</div><div class="l">Bridges Needed</div></div>
</div>
<h2>⚠️ Gaps & Bridge Suggestions</h2>
{gap_html or '<p style="color:rgba(255,255,255,.3);font-size:.8rem">No gaps detected.</p>'}
<h2>📊 Engine Connection Table</h2>
<table><thead><tr><th>Engine</th><th style="color:#00ff88">Reads ←</th><th style="color:#ff6b8a">Writes →</th></tr></thead>
<tbody>{rows}</tbody></table>
<footer>SolarPunk™ · <a href="index.html">Home</a> · <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">GitHub</a></footer>
</body></html>"""


def run():
    print("KNOWLEDGE_BRIDGE running...")
    now = datetime.now(timezone.utc).isoformat()

    engines, file_readers, file_writers, all_files, gaps, bridges = build_map()

    print(f"  📊 Mapped {len(engines)} engines across {len(all_files)} data files")
    print(f"  🔴 Critical gaps: {len(gaps['read_but_not_written'])}")
    print(f"  🟡 Orphaned outputs: {len(gaps['written_but_not_read'])}")
    print(f"  💡 Bridge suggestions: {len(bridges)}")

    gap_data = {
        "last_scan": now, "total_engines": len(engines),
        "total_files": len(all_files), "gaps": gaps,
        "bridge_suggestions": bridges[:20],
        "priority_builds": [b for b in bridges if b.get("priority") == "critical"]
    }
    (DATA / "knowledge_gaps.json").write_text(json.dumps(gap_data, indent=2))

    html = build_html(engines, file_readers, file_writers, gaps, bridges)
    (DOCS / "knowledge_map.html").write_text(html)
    print(f"  🗺️  Knowledge map → docs/knowledge_map.html")

    for b in bridges[:5]:
        print(f"  [{b['priority'].upper()}] {b['gap'][:80]}")


if __name__ == "__main__": run()
