"""
DESKTOP_INTEGRATOR.py
=====================
Connects your ENTIRE Windows desktop to the Meeko Nerve Center.

What it does:
1. Scans your Windows machine — Desktop, Downloads, Documents, Pictures,
   Videos, Music, AppData — cataloging everything that exists
2. Extracts knowledge from local files (text, code, docs, images metadata)
3. Discovers LOCAL APIs already running (localhost ports, installed apps)
4. Maps connections between local assets and cloud engines
5. Feeds everything into long_term_memory.py and knowledge_harvester
6. Finds "missed opportunity" connections you didn't know you had
7. Generates an ACTION PLAN: specific steps to wire each local asset

Examples of connections it finds:
  - Local Python scripts → can be added to OMNIBRAIN workflow
  - Downloaded datasets → can feed into knowledge_synthesizer
  - Local videos → can be uploaded to youtube_manager pipeline
  - Desktop screenshots → can be posted to social via cross_poster
  - Local .env files → missing secrets it can flag (don't upload, just alert)
  - Installed apps → APIs that can be called (Spotify, Slack, etc.)

Run: python DESKTOP_INTEGRATOR.py
     python DESKTOP_INTEGRATOR.py --scan-only
     python DESKTOP_INTEGRATOR.py --connect-local-scripts
"""

import os
import sys
import json
import socket
import subprocess
import platform
from datetime import datetime
from pathlib import Path

# ─── CONFIG ─────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DESKTOP_MAP_FILE = DATA_DIR / "desktop_map.json"
INTEGRATION_LOG = DATA_DIR / "desktop_integration_log.json"

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# Windows-specific paths (works in Actions too via env vars)
HOME = Path.home()

SCAN_TARGETS = {
    "Desktop": HOME / "Desktop",
    "Downloads": HOME / "Downloads",
    "Documents": HOME / "Documents",
    "Pictures": HOME / "Pictures",
    "Videos": HOME / "Videos",
    "Music": HOME / "Music",
    "Projects": HOME / "Projects",
    "repos": HOME / "repos",
    "code": HOME / "code",
    "src": HOME / "src",
    "OneDrive": HOME / "OneDrive",
}

# File types and what they mean for the system
ASSET_TYPES = {
    ".py": "python_script",
    ".js": "javascript",
    ".ts": "typescript",
    ".sh": "shell_script",
    ".bat": "windows_script",
    ".ps1": "powershell",
    ".csv": "data_file",
    ".json": "data_config",
    ".xlsx": "spreadsheet",
    ".pdf": "document",
    ".md": "documentation",
    ".txt": "text",
    ".mp4": "video",
    ".mp3": "audio",
    ".jpg": "image",
    ".png": "image",
    ".svg": "vector_image",
    ".env": "secrets_file",
    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".ipynb": "notebook",
    ".sql": "database",
}

# Apps that have APIs we can integrate with
INTEGRABLE_APPS = {
    "Spotify.exe": {"name": "Spotify", "api": "https://developer.spotify.com/", "port": None},
    "slack.exe": {"name": "Slack", "api": "https://api.slack.com/", "port": None},
    "discord.exe": {"name": "Discord", "api": "already_integrated_discord_bridge.py", "port": None},
    "notion.exe": {"name": "Notion", "api": "already_integrated_notion_bridge.py", "port": None},
    "obsidian.exe": {"name": "Obsidian", "api": "vault_integration", "port": None},
    "code.exe": {"name": "VS Code", "api": "file_system_access", "port": None},
    "chrome.exe": {"name": "Chrome", "api": "chrome_extension_bridge", "port": None},
    "vlc.exe": {"name": "VLC", "api": "media_pipeline", "port": None},
}

# ─── SCANNER ────────────────────────────────────────────────────────────────

def scan_directory(path: Path, max_depth: int = 3, max_files: int = 500) -> dict:
    """Recursively scan a directory, return structured asset map."""
    if not path.exists():
        return {}
    
    assets = {
        "python_scripts": [],
        "data_files": [],
        "documents": [],
        "videos": [],
        "images": [],
        "configs": [],
        "notebooks": [],
        "unknown": [],
        "total_files": 0,
        "total_size_mb": 0.0
    }
    
    file_count = 0
    
    try:
        for item in path.rglob("*"):
            if file_count >= max_files:
                break
            
            # Skip hidden/system dirs
            parts = item.parts
            if any(p.startswith(".") or p in ("__pycache__", "node_modules", ".git", "venv") for p in parts):
                continue
            
            if item.is_file():
                ext = item.suffix.lower()
                asset_type = ASSET_TYPES.get(ext, "unknown")
                size_mb = 0.0
                
                try:
                    size_mb = item.stat().st_size / (1024 * 1024)
                except:
                    pass
                
                file_info = {
                    "path": str(item),
                    "name": item.name,
                    "type": asset_type,
                    "size_mb": round(size_mb, 3),
                    "ext": ext
                }
                
                # Categorize
                if asset_type == "python_script":
                    assets["python_scripts"].append(file_info)
                elif asset_type in ("data_file", "spreadsheet", "database"):
                    assets["data_files"].append(file_info)
                elif asset_type in ("document", "text", "documentation"):
                    assets["documents"].append(file_info)
                elif asset_type == "video":
                    assets["videos"].append(file_info)
                elif asset_type in ("image", "vector_image"):
                    assets["images"].append(file_info)
                elif asset_type in ("config", "secrets_file"):
                    assets["configs"].append(file_info)
                    # NEVER log contents of .env files
                    if ext == ".env":
                        file_info["contains"] = "[SECRETS — NOT SCANNED]"
                elif asset_type == "notebook":
                    assets["notebooks"].append(file_info)
                else:
                    if size_mb < 10:  # Skip huge unknowns
                        assets["unknown"].append(file_info)
                
                assets["total_files"] += 1
                assets["total_size_mb"] += size_mb
                file_count += 1
    except PermissionError:
        pass
    except Exception as e:
        assets["scan_error"] = str(e)
    
    return assets

def scan_running_processes() -> list:
    """Find running processes that might have APIs."""
    if platform.system() != "Windows":
        return []
    
    integrable = []
    try:
        output = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            encoding="utf-8", errors="ignore", timeout=10
        )
        for line in output.strip().split("\n"):
            parts = line.strip('"').split('","')
            if parts:
                proc_name = parts[0].strip('"').lower()
                for app_exe, app_info in INTEGRABLE_APPS.items():
                    if app_exe.lower() in proc_name:
                        integrable.append({
                            "process": proc_name,
                            "app": app_info["name"],
                            "integration": app_info["api"]
                        })
    except Exception as e:
        pass
    
    return integrable

def scan_localhost_ports() -> list:
    """Check which localhost ports are active (local APIs/servers)."""
    active_ports = []
    common_ports = {
        3000: "Node.js/React dev server",
        5000: "Flask/Python server",
        5001: "Alternative Flask",
        8000: "Django/Python server",
        8080: "Generic web server",
        8765: "WebSocket (network_node.py)",
        9000: "PHP/misc server",
        27017: "MongoDB",
        5432: "PostgreSQL",
        3306: "MySQL",
        6379: "Redis",
        11434: "Ollama (local LLM!)",
        1234: "LM Studio (local LLM!)",
        8888: "Jupyter Notebook",
    }
    
    for port, description in common_ports.items():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            result = s.connect_ex(("127.0.0.1", port))
            s.close()
            if result == 0:
                active_ports.append({"port": port, "description": description})
        except:
            pass
    
    return active_ports

# ─── OPPORTUNITY FINDER ──────────────────────────────────────────────────────

def find_connections(desktop_map: dict, running_apps: list, active_ports: list) -> list:
    """Find actionable connection opportunities between local assets and cloud engines."""
    opportunities = []
    
    # Local Python scripts not in mycelium
    mycelium_path = str(Path(__file__).parent)
    for scan_area, assets in desktop_map.items():
        py_scripts = assets.get("python_scripts", [])
        for script in py_scripts:
            if mycelium_path not in script["path"] and script["size_mb"] < 1.0:
                opportunities.append({
                    "type": "local_script",
                    "priority": "HIGH",
                    "asset": script["path"],
                    "action": "Review and potentially add to OMNIBRAIN workflow",
                    "engine": "OMNIBRAIN.yml + SYNTHESIS_FACTORY.py",
                    "revenue_potential": "Depends on script function"
                })
    
    # Local videos → YouTube pipeline
    for scan_area, assets in desktop_map.items():
        videos = assets.get("videos", [])
        for video in videos[:5]:  # Cap at 5
            opportunities.append({
                "type": "local_video",
                "priority": "MEDIUM",
                "asset": video["path"],
                "action": "Upload to YouTube via youtube_manager.py",
                "engine": "youtube_manager.py",
                "revenue_potential": "Ad revenue + channel growth"
            })
    
    # Local data files → knowledge pipeline
    for scan_area, assets in desktop_map.items():
        data_files = assets.get("data_files", [])
        for df in data_files[:3]:
            if df["size_mb"] < 50:  # Skip giant files
                opportunities.append({
                    "type": "local_data",
                    "priority": "MEDIUM",
                    "asset": df["path"],
                    "action": "Ingest via folder_ingestion_engine.py → knowledge_synthesizer",
                    "engine": "folder_ingestion_engine.py + knowledge_synthesizer.py",
                    "revenue_potential": "Knowledge = content = revenue"
                })
    
    # Local LLM running!
    for port_info in active_ports:
        if "LLM" in port_info["description"] or "Ollama" in port_info["description"] or "LM Studio" in port_info["description"]:
            opportunities.append({
                "type": "local_llm",
                "priority": "CRITICAL",
                "asset": f"localhost:{port_info['port']}",
                "action": f"Wire {port_info['description']} as FREE alternative to Claude API during rate limits",
                "engine": "SYNTHESIS_FACTORY.py (add local LLM fallback)",
                "revenue_potential": "HUGE — eliminates API costs entirely"
            })
    
    # Running apps with integrations
    for app in running_apps:
        if "already_integrated" not in app.get("integration", ""):
            opportunities.append({
                "type": "running_app",
                "priority": "MEDIUM",
                "asset": f"{app['app']} (running on this machine)",
                "action": f"Build bridge using {app['integration']}",
                "engine": f"{app['app'].lower()}_bridge.py (new)",
                "revenue_potential": f"{app['app']} integration expands audience reach"
            })
    
    # Jupyter notebooks → content pipeline
    for scan_area, assets in desktop_map.items():
        notebooks = assets.get("notebooks", [])
        for nb in notebooks[:3]:
            opportunities.append({
                "type": "notebook",
                "priority": "MEDIUM",
                "asset": nb["path"],
                "action": "Convert notebook to blog post + YouTube tutorial",
                "engine": "newsletter_engine.py + youtube_manager.py",
                "revenue_potential": "Technical tutorials convert well"
            })
    
    # Sort by priority
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    opportunities.sort(key=lambda x: priority_order.get(x["priority"], 99))
    
    return opportunities[:20]  # Top 20

# ─── INTEGRATION ACTIONS ────────────────────────────────────────────────────

def connect_local_scripts(desktop_map: dict) -> list:
    """Actually copy/link promising local Python scripts into mycelium."""
    mycelium_path = Path(__file__).parent
    connected = []
    
    for scan_area, assets in desktop_map.items():
        for script in assets.get("python_scripts", []):
            script_path = Path(script["path"])
            
            # Skip if tiny/empty
            if script["size_mb"] < 0.001:
                continue
            
            # Skip if already in mycelium
            if str(mycelium_path) in script["path"]:
                continue
            
            # Read and check if it's useful
            try:
                content = script_path.read_text(encoding="utf-8", errors="ignore")
                # Check if it has actual functions
                if "def " in content and len(content) > 200:
                    dest = mycelium_path / f"imported_{script_path.name}"
                    if not dest.exists():
                        dest.write_text(content, encoding="utf-8")
                        connected.append(str(dest))
                        print(f"   📥 Imported: {script_path.name}")
            except Exception as e:
                pass
    
    return connected

# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    scan_only = "--scan-only" in sys.argv
    connect_scripts = "--connect-local-scripts" in sys.argv
    
    print("🖥️  DESKTOP INTEGRATOR starting...")
    print(f"   Platform: {platform.system()} {platform.release()}")
    print(f"   Home: {HOME}")
    
    # Load or init map
    desktop_map = {}
    
    # Scan each target directory
    print("\n📁 Scanning local directories...")
    total_files = 0
    for area_name, area_path in SCAN_TARGETS.items():
        if area_path.exists():
            print(f"   Scanning {area_name} ({area_path})...")
            assets = scan_directory(area_path)
            desktop_map[area_name] = assets
            count = assets.get("total_files", 0)
            total_files += count
            if count > 0:
                print(f"   → {count} files, {assets.get('total_size_mb', 0):.1f}MB")
                py_count = len(assets.get("python_scripts", []))
                vid_count = len(assets.get("videos", []))
                data_count = len(assets.get("data_files", []))
                if py_count: print(f"     🐍 {py_count} Python scripts")
                if vid_count: print(f"     🎬 {vid_count} videos")
                if data_count: print(f"     📊 {data_count} data files")
    
    print(f"\n📊 Total: {total_files} files scanned")
    
    # Running processes
    print("\n⚙️  Scanning running processes...")
    running_apps = scan_running_processes()
    if running_apps:
        for app in running_apps:
            print(f"   ✅ {app['app']} is running → {app['integration']}")
    else:
        print("   (No integrable apps detected or Windows API unavailable)")
    
    # Active localhost ports
    print("\n🔌 Scanning localhost ports...")
    active_ports = scan_localhost_ports()
    if active_ports:
        for p in active_ports:
            print(f"   ✅ Port {p['port']}: {p['description']}")
    else:
        print("   (No active local ports detected)")
    
    # Save desktop map
    DESKTOP_MAP_FILE.write_text(json.dumps({
        "scanned_at": datetime.now().isoformat(),
        "total_files": total_files,
        "running_apps": running_apps,
        "active_ports": active_ports,
        "directories": desktop_map
    }, indent=2, default=str))
    
    # Find opportunities
    print("\n💡 Finding connection opportunities...")
    opportunities = find_connections(desktop_map, running_apps, active_ports)
    
    if opportunities:
        print(f"\n🎯 TOP OPPORTUNITIES ({len(opportunities)} found):\n")
        for i, opp in enumerate(opportunities[:10], 1):
            emoji = {"CRITICAL": "🚨", "HIGH": "🔥", "MEDIUM": "💡", "LOW": "📌"}.get(opp["priority"], "📌")
            print(f"   {i}. {emoji} [{opp['priority']}] {opp['type'].upper()}")
            print(f"      Asset: {Path(opp['asset']).name if '/' in opp['asset'] or '\\' in opp['asset'] else opp['asset']}")
            print(f"      Action: {opp['action']}")
            print(f"      Revenue: {opp['revenue_potential']}\n")
    else:
        print("   No new opportunities found (system is well-connected!)")
    
    # Connect local scripts if requested
    if connect_scripts:
        print("\n📥 Connecting local Python scripts...")
        connected = connect_local_scripts(desktop_map)
        print(f"   Connected {len(connected)} new scripts")
    
    # Save integration log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "total_files_found": total_files,
        "opportunities_found": len(opportunities),
        "running_apps": [a["app"] for a in running_apps],
        "active_ports": [p["port"] for p in active_ports],
        "top_opportunity": opportunities[0] if opportunities else None
    }
    
    existing_log = []
    if INTEGRATION_LOG.exists():
        try:
            existing_log = json.loads(INTEGRATION_LOG.read_text())
        except:
            pass
    existing_log.append(log_entry)
    INTEGRATION_LOG.write_text(json.dumps(existing_log[-30:], indent=2, default=str))
    
    # Summary
    print("\n" + "="*50)
    print("🖥️  DESKTOP INTEGRATION SUMMARY")
    print("="*50)
    print(f"Files found:       {total_files}")
    print(f"Running apps:      {len(running_apps)}")
    print(f"Active APIs:       {len(active_ports)}")
    print(f"Opportunities:     {len(opportunities)}")
    
    if any(p["port"] in (11434, 1234) for p in active_ports):
        print("\n🚨 LOCAL LLM DETECTED — can eliminate API costs!")
    
    print(f"\nFull desktop map saved to: {DESKTOP_MAP_FILE}")
    
    return {
        "total_files": total_files,
        "opportunities": len(opportunities),
        "running_apps": len(running_apps),
        "active_local_apis": len(active_ports)
    }

if __name__ == "__main__":
    result = main()
