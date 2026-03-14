# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
PLUGIN_REGISTRY.py — Open Mycelium Protocol
=============================================
SolarPunk is a protocol, not a product.
This engine manages external engines that plug into the mycelium.

Any engine that follows the interface contract can live here:
  def run() -> dict

The registry:
  - Discovers engines in mycelium/ that declare themselves plugins
  - Validates their interface
  - Registers them with contributor_registry for revenue splits
  - Publishes docs/plugins.html — the open mycelium directory
  - Routes plugin outputs into the main data/ state

This is how SolarPunk becomes infrastructure.
Other builders plug in. Their engines run inside the organism.
Their revenue routes through the same dispatch system.
Their contributions get credited. Their Gaza share routes automatically.
"""
import os, json, importlib.util, sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from AI_CLIENT import ask_json
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask_json(prompt, **kw): return None

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")

# Built-in core engines that are NOT plugins (they're the organism itself)
CORE_ENGINES = {
    "OMNIBUS", "AI_CLIENT", "GUARDIAN", "ENGINE_INTEGRITY", "SECRETS_CHECKER",
    "BOTTLENECK_SCANNER", "AUTO_HEALER", "CAPABILITY_SCANNER", "CYCLE_MEMORY",
    "NARRATOR", "PLUGIN_REGISTRY",
}

# Plugin manifest fields (declared in engine docstring or plugin_manifest.json)
REQUIRED_MANIFEST_FIELDS = ["name", "author", "description", "version"]

REGISTRY_FILE = DATA / "plugin_registry.json"
MANIFEST_FILE = DATA / "plugin_manifests.json"


def load_registry():
    if REGISTRY_FILE.exists():
        try: return json.loads(REGISTRY_FILE.read_text())
        except: pass
    return {"plugins": {}, "last_scan": None, "total_registered": 0}


def save_registry(reg):
    REGISTRY_FILE.write_text(json.dumps(reg, indent=2))


def load_manifests():
    if MANIFEST_FILE.exists():
        try: return json.loads(MANIFEST_FILE.read_text())
        except: pass
    return {}


def save_manifests(m):
    MANIFEST_FILE.write_text(json.dumps(m, indent=2))


def discover_plugins():
    """
    Scan mycelium/ for engines that declare themselves as plugins.
    A plugin declares itself by including '# SOLARPUNK_PLUGIN' in its first 10 lines,
    OR by having a corresponding entry in data/plugin_manifests.json.
    """
    plugins = []
    manifests = load_manifests()

    if not MYCELIUM.exists():
        return plugins

    for f in sorted(MYCELIUM.glob("*.py")):
        name = f.stem
        if name in CORE_ENGINES:
            continue

        # Check for plugin declaration in source
        try:
            lines = f.read_text(errors="replace").split("\n")[:20]
            is_plugin = any("SOLARPUNK_PLUGIN" in line for line in lines)
        except:
            is_plugin = False

        # Check manifest file
        in_manifest = name in manifests

        if is_plugin or in_manifest:
            manifest = manifests.get(name, {})
            plugins.append({
                "name":        manifest.get("name", name),
                "engine_file": str(f),
                "stem":        name,
                "author":      manifest.get("author", "unknown"),
                "description": manifest.get("description", ""),
                "version":     manifest.get("version", "0.1"),
                "category":    manifest.get("category", "general"),
                "revenue_share": manifest.get("revenue_share", 0),
                "declared":    is_plugin,
                "manifested":  in_manifest,
            })

    return plugins


def validate_engine_interface(engine_path):
    """Check that an engine file exposes a run() function."""
    try:
        spec = importlib.util.spec_from_file_location("_test", engine_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return hasattr(mod, "run") and callable(mod.run), "ok"
    except Exception as e:
        return False, str(e)


def register_plugin_contributor(plugin, registry):
    """Add plugin author to contributor_registry if not present."""
    author = plugin.get("author", "")
    if not author or author == "unknown":
        return

    contrib_file = DATA / "contributor_registry.json"
    if not contrib_file.exists():
        return

    try:
        contrib = json.loads(contrib_file.read_text())
    except:
        return

    contributors = contrib.get("contributors", [])
    existing_names = [c.get("name", "") for c in contributors]

    if author not in existing_names:
        contributors.append({
            "name":         author,
            "role":         "plugin_contributor",
            "engine":       plugin.get("stem", ""),
            "share":        plugin.get("revenue_share", 0),
            "paypal_email": "",
            "earned":       0.0,
            "paid":         0.0,
            "joined":       datetime.now(timezone.utc).isoformat()[:10],
        })
        contrib["contributors"] = contributors
        contrib_file.write_text(json.dumps(contrib, indent=2))
        print(f"  Registered contributor: {author}")


def build_plugins_html(plugins, registry):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(plugins)

    cards_html = ""
    if plugins:
        for p in plugins:
            valid = registry.get("plugins", {}).get(p["stem"], {}).get("valid", False)
            status = "✅ valid" if valid else "⚠️ unvalidated"
            cards_html += f"""
      <div class="plugin-card">
        <div class="plugin-header">
          <span class="plugin-name">{p['name']}</span>
          <span class="plugin-status {'ok' if valid else 'warn'}">{status}</span>
        </div>
        <div class="plugin-meta">
          <span>by <strong>{p['author']}</strong></span> ·
          <span>v{p['version']}</span> ·
          <span class="category">{p['category']}</span>
        </div>
        <p class="plugin-desc">{p['description'] or 'No description provided.'}</p>
        {f'<div class="rev-share">Revenue share: {p["revenue_share"]}%</div>' if p.get("revenue_share") else ''}
      </div>"""
    else:
        cards_html = """
      <div class="empty-state">
        <p>No plugins registered yet.</p>
        <p>Be the first to plug into the mycelium.</p>
      </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarPunk — Open Mycelium</title>
<style>
  :root {{
    --green: #1b4332; --pulse: #52b788; --paper: #f7f4ef;
    --ink: #0a0a0a; --dim: #888; --border: #ddd;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Georgia', serif; background: var(--paper); color: var(--ink); }}
  header {{
    background: var(--green); color: white;
    padding: 48px 24px; text-align: center;
  }}
  header p {{ opacity: 0.7; margin-top: 8px; font-style: italic; }}
  .container {{ max-width: 800px; margin: 0 auto; padding: 48px 24px; }}
  .section-label {{
    font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--dim); margin-bottom: 20px;
  }}
  h2 {{ font-size: 28px; font-weight: 400; margin-bottom: 16px; }}
  .intro {{ font-size: 17px; line-height: 1.7; color: #444; margin-bottom: 40px; }}
  .contract {{
    background: var(--ink); color: var(--pulse);
    padding: 24px; font-family: monospace; font-size: 14px;
    line-height: 1.7; margin-bottom: 48px;
  }}
  .plugins-grid {{ display: grid; gap: 16px; }}
  .plugin-card {{
    background: white; border: 1px solid var(--border); padding: 20px;
  }}
  .plugin-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 8px;
  }}
  .plugin-name {{ font-size: 17px; font-weight: 600; }}
  .plugin-status {{ font-size: 12px; }}
  .plugin-status.ok {{ color: var(--pulse); }}
  .plugin-status.warn {{ color: #b5854a; }}
  .plugin-meta {{ font-size: 13px; color: var(--dim); margin-bottom: 10px; }}
  .category {{
    background: var(--paper); padding: 2px 8px;
    border-radius: 2px; font-size: 11px;
  }}
  .plugin-desc {{ font-size: 15px; color: #444; line-height: 1.5; }}
  .rev-share {{ font-size: 12px; color: var(--pulse); margin-top: 8px; }}
  .empty-state {{ text-align: center; padding: 48px; color: var(--dim); font-size: 16px; }}
  .empty-state p {{ margin-bottom: 8px; }}
  .step {{
    display: flex; gap: 20px; padding: 20px 0;
    border-bottom: 1px solid var(--border); align-items: flex-start;
  }}
  .step:last-child {{ border-bottom: none; }}
  .step-num {{ font-size: 24px; font-weight: 700; color: var(--pulse); min-width: 36px; }}
  .step-body h4 {{ font-size: 16px; margin-bottom: 6px; }}
  .step-body p {{ font-size: 14px; color: #555; line-height: 1.5; }}
  footer {{
    text-align: center; padding: 32px; font-size: 12px;
    color: var(--dim); border-top: 1px solid var(--border);
  }}
  footer a {{ color: var(--green); text-decoration: none; }}
</style>
</head>
<body>
<header>
  <h1>Open Mycelium</h1>
  <p>Plug your engine into SolarPunk. Your work runs inside the organism.</p>
</header>

<div class="container">
  <div class="section-label">What this is</div>
  <h2>SolarPunk is a protocol.</h2>
  <p class="intro">Any engine that follows the interface contract can run inside the mycelium. Your engine gets access to the same data layer, the same AI backbone (Groq, free), the same dispatch system that routes revenue to Gaza. You write <code>run()</code> and the organism does the rest.</p>

  <div class="contract">
# The entire interface contract:
# Any .py file in mycelium/ with a run() function is an engine.

# SOLARPUNK_PLUGIN  &lt;-- add this comment to declare yourself a plugin

def run():
    # read from data/
    # write to data/
    # return what you did
    return {{"status": "ok", "built": "something"}}
  </div>

  <div class="section-label">How to plug in</div>
  <div>
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-body">
        <h4>Fork the repo</h4>
        <p>github.com/meekotharaccoon-cell/meeko-nerve-center — fork it, clone it, you own it.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">2</div>
      <div class="step-body">
        <h4>Write your engine</h4>
        <p>Drop a .py file in <code>mycelium/</code>. Add <code># SOLARPUNK_PLUGIN</code> in the first 10 lines. Expose <code>run()</code>. Write outputs to <code>data/</code>.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">3</div>
      <div class="step-body">
        <h4>Add your manifest</h4>
        <p>Add an entry to <code>data/plugin_manifests.json</code> with your name, description, category, and revenue_share (0–15%).</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">4</div>
      <div class="step-body">
        <h4>Open a pull request</h4>
        <p>The organism will validate your engine interface. If it passes, it gets added to the next OMNIBUS cycle. If it generates revenue, you get paid.</p>
      </div>
    </div>
  </div>

  <div class="section-label" style="margin-top:48px">Registered plugins — {total} total</div>
  <div class="plugins-grid">
    {cards_html}
  </div>
</div>

<footer>
  <p>SolarPunk Open Mycelium — {ts}</p>
  <p style="margin-top:8px">
    <a href="https://meekotharaccoon-cell.github.io/meeko-nerve-center/solarpunk.html">What is SolarPunk</a> ·
    <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/MANIFESTO.md">Manifesto</a> ·
    <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center">GitHub</a>
  </p>
</footer>
</body>
</html>"""


def run():
    registry = load_registry()
    registry["cycles"] = registry.get("cycles", 0) + 1

    print(f"PLUGIN_REGISTRY cycle {registry['cycles']}")

    # Discover plugins
    plugins = discover_plugins()
    print(f"  Discovered: {len(plugins)} plugins")

    # Validate each plugin's interface
    for p in plugins:
        valid, reason = validate_engine_interface(p["engine_file"])
        registry.setdefault("plugins", {})[p["stem"]] = {
            "name":    p["name"],
            "author":  p["author"],
            "valid":   valid,
            "reason":  reason,
            "scanned": datetime.now(timezone.utc).isoformat()[:16],
        }
        status = "✅" if valid else "❌"
        print(f"  {status} {p['name']} (by {p['author']}): {reason}")

        # Register contributor
        if valid:
            register_plugin_contributor(p, registry)

    registry["last_scan"]        = datetime.now(timezone.utc).isoformat()
    registry["total_registered"] = len([p for p in registry.get("plugins", {}).values() if p.get("valid")])

    # Build plugins page
    html = build_plugins_html(plugins, registry)
    (DOCS / "plugins.html").write_text(html)
    print(f"  docs/plugins.html — {len(plugins)} plugins")
    print(f"  URL: https://meekotharaccoon-cell.github.io/meeko-nerve-center/plugins.html")

    save_registry(registry)
    return registry


if __name__ == "__main__":
    run()
