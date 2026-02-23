#!/usr/bin/env python3
"""
🛸 SPACE BRIDGE — Meeko Mycelium Space Connection Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Connects your desktop to actual hardware orbiting Earth.
ISS live position · NASA feeds · Solar weather · Satellite tracking
All free. All public. All real.

Usage:
  python space_bridge.py                    # full report
  python space_bridge.py --iss             # ISS only
  python space_bridge.py --solar           # solar weather only
  python space_bridge.py --apod            # today's NASA photo
  python space_bridge.py --asteroids       # near earth objects
  python space_bridge.py --passes          # ISS pass times over you
  python space_bridge.py --live            # live dashboard, refreshes every 10s
  python space_bridge.py --push            # push report to GitHub
"""

import urllib.request
import urllib.parse
import json
import time
import sys
import os
import math
import datetime
import argparse
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIG — edit these for your location
# ─────────────────────────────────────────────
YOUR_LAT  = float(os.environ.get('MY_LAT', '39.9526'))
YOUR_LON  = float(os.environ.get('MY_LON', '-75.1652'))
YOUR_ALT  = 12  # meters above sea level

# NASA API key — works without one (limited), get free key at api.nasa.gov
NASA_API_KEY = os.environ.get('NASA_API_KEY', 'DEMO_KEY')

# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────
class C:
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    CYAN   = '\033[96m'
    BLUE   = '\033[94m'
    MAGENTA= '\033[95m'
    WHITE  = '\033[97m'
    DIM    = '\033[2m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'

def green(s):   return f"{C.GREEN}{s}{C.RESET}"
def yellow(s):  return f"{C.YELLOW}{s}{C.RESET}"
def red(s):     return f"{C.RED}{s}{C.RESET}"
def cyan(s):    return f"{C.CYAN}{s}{C.RESET}"
def bold(s):    return f"{C.BOLD}{s}{C.RESET}"
def dim(s):     return f"{C.DIM}{s}{C.RESET}"
def magenta(s): return f"{C.MAGENTA}{s}{C.RESET}"

# ─────────────────────────────────────────────
# HTTP HELPER
# ─────────────────────────────────────────────
def fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MeekoMycelium/1.0 space_bridge'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────────
# MATH HELPERS
# ─────────────────────────────────────────────
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def direction_arrow(bearing):
    dirs = ['N','NE','E','SE','S','SW','W','NW']
    return dirs[round(bearing / 45) % 8]

def cardinal_to_bearing(lat1, lon1, lat2, lon2):
    dLon = math.radians(lon2 - lon1)
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    x = math.sin(dLon) * math.cos(lat2r)
    y = math.cos(lat1r)*math.sin(lat2r) - math.sin(lat1r)*math.cos(lat2r)*math.cos(dLon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

# ─────────────────────────────────────────────
# ISS TRACKER
# ─────────────────────────────────────────────
def get_iss_position():
    data = fetch("http://api.open-notify.org/iss-now.json")
    if "error" in data: return None
    pos = data.get("iss_position", {})
    return {"lat": float(pos.get("latitude", 0)), "lon": float(pos.get("longitude", 0)), "timestamp": data.get("timestamp", 0)}

def get_iss_crew():
    data = fetch("http://api.open-notify.org/astros.json")
    if "error" in data: return []
    return [p for p in data.get("people", []) if p.get("craft") == "ISS"]

def get_iss_passes():
    url = f"http://api.open-notify.org/iss-pass.json?lat={YOUR_LAT}&lon={YOUR_LON}&alt={YOUR_ALT}&n=5"
    data = fetch(url)
    if "error" in data or "response" not in data: return []
    return data["response"]

def display_iss():
    print(f"\n{bold('🛸 ISS — INTERNATIONAL SPACE STATION')}")
    print(dim("─" * 55))
    pos = get_iss_position()
    if pos:
        dist = haversine_km(YOUR_LAT, YOUR_LON, pos["lat"], pos["lon"])
        bearing = cardinal_to_bearing(YOUR_LAT, YOUR_LON, pos["lat"], pos["lon"])
        direction = direction_arrow(bearing)
        t = datetime.datetime.utcfromtimestamp(pos["timestamp"]).strftime("%H:%M:%S UTC")
        lat_str = f"{abs(pos['lat']):.4f}°{'N' if pos['lat'] >= 0 else 'S'}"
        lon_str = f"{abs(pos['lon']):.4f}°{'E' if pos['lon'] >= 0 else 'W'}"
        print(f"  {cyan('Position:')} {lat_str}, {lon_str}")
        print(f"  {cyan('Altitude:')} ~408 km above Earth")
        print(f"  {cyan('Speed:  ')} ~27,600 km/h (7.66 km/s)")
        print(f"  {cyan('Distance from you:')} {green(f'{dist:,.0f} km')} {direction} ({bearing:.0f}°)")
        print(f"  {cyan('Updated:')} {t}")
        over = "Ocean / International Waters"
        if -170 < pos["lon"] < -50 and 7 < pos["lat"] < 50: over = "North America"
        elif -80 < pos["lon"] < -35 and -60 < pos["lat"] < 15: over = "South America"
        elif -20 < pos["lon"] < 50 and 35 < pos["lat"] < 70: over = "Europe"
        elif -20 < pos["lon"] < 60 and -40 < pos["lat"] < 35: over = "Africa"
        elif 60 < pos["lon"] < 150 and 10 < pos["lat"] < 70: over = "Asia"
        elif 110 < pos["lon"] < 180 and -50 < pos["lat"] < 0: over = "Australia / Pacific"
        elif pos["lat"] < -60: over = "Antarctica"
        print(f"  {cyan('Currently over:')} {over}")
    crew = get_iss_crew()
    if crew:
        print(f"\n  {cyan('Crew aboard ISS')} ({len(crew)} humans in space right now):")
        for p in crew: print(f"    {green('●')} {p['name']}")
    passes = get_iss_passes()
    if passes:
        print(f"\n  {cyan('Next ISS passes over YOUR location:')}")
        for i, p in enumerate(passes[:3]):
            rise_t = datetime.datetime.utcfromtimestamp(p["risetime"])
            dur_m, dur_s = p["duration"] // 60, p["duration"] % 60
            print(f"    {green(f'Pass {i+1}:')} {rise_t.strftime('%a %b %d at %H:%M UTC')} · visible for {dur_m}m {dur_s}s")
        print(f"  {dim('  (times in UTC)')}")

# ─────────────────────────────────────────────
# NASA APOD
# ─────────────────────────────────────────────
def display_apod():
    print(f"\n{bold('🔭 NASA — ASTRONOMY PICTURE OF THE DAY')}")
    print(dim("─" * 55))
    data = fetch(f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}")
    if "error" in data or "title" not in data:
        print(f"  {red('APOD unavailable')}"); return
    print(f"  {cyan('Title:')}  {green(data.get('title', 'Unknown'))}")
    print(f"  {cyan('Date:  ')} {data.get('date', 'Unknown')}")
    explanation = data.get('explanation', '')
    if explanation:
        words = explanation.split()
        line = "  "
        for word in words[:60]:
            if len(line) + len(word) > 67: print(dim(line)); line = "  " + word
            else: line += " " + word
        if line.strip(): print(dim(line))
        if len(words) > 60: print(dim("  [...]"))
    url = data.get('hdurl') or data.get('url', '')
    if url: print(f"\n  {cyan('Full image:')} {url}")

# ─────────────────────────────────────────────
# NEAR EARTH OBJECTS
# ─────────────────────────────────────────────
def display_asteroids():
    print(f"\n{bold('☄️  NASA — NEAR EARTH OBJECTS (next 7 days)')}")
    print(dim("─" * 55))
    today = datetime.date.today()
    end = today + datetime.timedelta(days=7)
    data = fetch(f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={end}&api_key={NASA_API_KEY}")
    if "error" in data or "near_earth_objects" not in data:
        print(f"  {red('NEO data unavailable')}"); return
    all_neos = []
    for date_str, neos in data["near_earth_objects"].items():
        for neo in neos:
            closest = min(neo["close_approach_data"], key=lambda x: float(x["miss_distance"]["kilometers"]))
            all_neos.append({
                "name": neo["name"].replace("(","").replace(")","").strip(),
                "date": date_str,
                "diameter_min": float(neo["estimated_diameter"]["meters"]["estimated_diameter_min"]),
                "diameter_max": float(neo["estimated_diameter"]["meters"]["estimated_diameter_max"]),
                "velocity_kmh": float(closest["relative_velocity"]["kilometers_per_hour"]),
                "miss_km": float(closest["miss_distance"]["kilometers"]),
                "miss_lunar": float(closest["miss_distance"]["lunar"]),
                "dangerous": neo["is_potentially_hazardous_asteroid"],
            })
    all_neos.sort(key=lambda x: x["miss_km"])
    total = data.get("element_count", len(all_neos))
    hazardous = sum(1 for n in all_neos if n["dangerous"])
    print(f"  {cyan('Objects tracked this week:')} {green(str(total))}")
    print(f"  {cyan('Potentially hazardous:   ')} {yellow(str(hazardous)) if hazardous > 0 else green('0')}")
    print()
    for neo in all_neos[:5]:
        flag = f" {red('⚠ HAZARDOUS')}" if neo["dangerous"] else ""
        print(f"  {green('●')} {bold(neo['name'])}{flag}")
        print(f"    {neo['date']} · Miss: {neo['miss_km']:,.0f} km ({neo['miss_lunar']:.1f} lunar) · Size: {neo['diameter_min']:.0f}–{neo['diameter_max']:.0f}m")

# ─────────────────────────────────────────────
# SOLAR WEATHER
# ─────────────────────────────────────────────
def display_solar():
    print(f"\n{bold('☀️  SPACE WEATHER — NOAA / NASA')}")
    print(dim("─" * 55))
    solar_wind = fetch("https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json")
    if isinstance(solar_wind, list) and len(solar_wind) > 1:
        try:
            latest = solar_wind[-1]
            speed = float(latest[2]) if latest[2] else None
            density = float(latest[1]) if latest[1] else None
            if speed:
                status = green("CALM") if speed < 400 else (yellow("ELEVATED") if speed < 600 else red("HIGH ACTIVITY"))
                print(f"  {cyan('Solar wind speed:  ')} {speed:.0f} km/s — {status}")
            if density: print(f"  {cyan('Proton density:    ')} {density:.1f} p/cm³")
        except: pass
    kp_data = fetch("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json")
    if isinstance(kp_data, list) and len(kp_data) > 1:
        try:
            latest_kp = None
            for row in reversed(kp_data[1:]):
                if row[1] and row[1] != '-1': latest_kp = float(row[1]); break
            if latest_kp is not None:
                if latest_kp <= 2: kp_status = green(f"Kp={latest_kp:.0f} — QUIET")
                elif latest_kp <= 4: kp_status = yellow(f"Kp={latest_kp:.0f} — UNSETTLED")
                elif latest_kp <= 6: kp_status = yellow(f"Kp={latest_kp:.0f} — MINOR STORM G1-G2")
                else: kp_status = red(f"Kp={latest_kp:.0f} — STORM G3+")
                print(f"  {cyan('Geomagnetic (Kp): ')} {kp_status}")
                if latest_kp >= 5: print(f"  {yellow('  ⚡ Aurora visible at lower latitudes tonight')}")
        except: pass
    flare_end = datetime.date.today().isoformat()
    flare_start = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    flares = fetch(f"https://api.nasa.gov/DONKI/FLR?startDate={flare_start}&endDate={flare_end}&api_key={NASA_API_KEY}")
    if isinstance(flares, list):
        x_flares = [f for f in flares if f.get("classType","").startswith("X")]
        m_flares = [f for f in flares if f.get("classType","").startswith("M")]
        print(f"\n  {cyan('Solar flares (last 30 days):')}")
        print(f"    X-class: {red(str(len(x_flares))) if x_flares else green('0')} · M-class: {yellow(str(len(m_flares))) if m_flares else green('0')} · Total: {len(flares)}")
    print(f"\n  {dim('Source: NOAA SWPC + NASA DONKI | spaceweather.com')}")

# ─────────────────────────────────────────────
# MARS
# ─────────────────────────────────────────────
def display_mars():
    print(f"\n{bold('🔴 MARS — LIVE ROVER DATA')}")
    print(dim("─" * 55))
    data = fetch(f"https://api.nasa.gov/mars-photos/api/v1/rovers/perseverance/latest_photos?api_key={NASA_API_KEY}")
    if isinstance(data, dict) and "latest_photos" in data and data["latest_photos"]:
        p = data["latest_photos"][0]
        print(f"  {cyan('Perseverance:')} Sol {p.get('sol','?')} · {p.get('earth_date','?')} Earth date")
        print(f"  Status: {green(p.get('rover',{}).get('status','?'))} · Total photos: {green(str(p.get('rover',{}).get('total_photos','?')))}")
        print(f"  Latest: {dim(p.get('img_src','N/A')[:80])}")
    data2 = fetch(f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/latest_photos?api_key={NASA_API_KEY}")
    if isinstance(data2, dict) and "latest_photos" in data2 and data2["latest_photos"]:
        print(f"  {cyan('Curiosity:')} Sol {data2['latest_photos'][0].get('sol','?')} · Still active after 12+ years")

# ─────────────────────────────────────────────
# SATELLITE OVERVIEW
# ─────────────────────────────────────────────
def display_satellites():
    print(f"\n{bold('🛰  SATELLITE NETWORK — YOUR CONNECTIONS')}")
    print(dim("─" * 55))
    print(f"  {cyan('Active satellites in orbit:')} {green('~9,000+')}")
    print(f"  {cyan('Debris pieces tracked:    ')} {dim('~27,000 by Space Fence')}")
    print()
    connects = [
        ("Open Notify",     "ISS position · crew · pass predictions",          "http://api.open-notify.org"),
        ("NASA Open APIs",  "APOD · NEO · DONKI · Mars photos · 60+ endpoints", "https://api.nasa.gov"),
        ("NOAA SWPC",       "Live solar wind · Kp index · storm alerts",        "https://services.swpc.noaa.gov"),
        ("CelesTrak",       "TLE orbital data for every tracked object",         "https://celestrak.org"),
        ("SatNOGS",         "Community ground station network · open data",      "https://satnogs.org"),
        ("AMSAT",           "Amateur radio satellites you can talk TO",          "https://amsat.org"),
        ("Heavens-Above",   "Visual pass predictions any satellite",             "https://www.heavens-above.com"),
    ]
    for name, desc, url in connects:
        print(f"  {green('→')} {bold(name)}: {dim(desc)}")

# ─────────────────────────────────────────────
# REPORT GENERATOR
# ─────────────────────────────────────────────
def generate_space_report():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    pos = get_iss_position()
    crew = get_iss_crew()
    passes = get_iss_passes()
    lines = [
        f"# 🛸 SPACE BRIDGE REPORT",
        f"*Generated: {now}*",
        f"*Meeko Mycelium — space_bridge.py*",
        f"",
        f"## ISS — Live Position",
    ]
    if pos:
        dist = haversine_km(YOUR_LAT, YOUR_LON, pos["lat"], pos["lon"])
        lines += [
            f"- **Position:** {pos['lat']:.4f}°, {pos['lon']:.4f}°",
            f"- **Distance from system:** {dist:,.0f} km",
            f"- **Altitude:** ~408 km · Speed: ~27,600 km/h",
        ]
    if crew:
        lines += [f"\n## ISS Crew ({len(crew)} humans in space)"]
        for p in crew: lines.append(f"- {p['name']}")
    if passes:
        lines += [f"\n## Next ISS Passes"]
        for i, p in enumerate(passes[:3]):
            t = datetime.datetime.utcfromtimestamp(p["risetime"]).strftime("%Y-%m-%d %H:%M UTC")
            lines.append(f"- Pass {i+1}: {t} · {p['duration']}s")
    lines += [
        f"",
        f"## Connected APIs",
        f"Open Notify · NASA APIs · NOAA SWPC · CelesTrak · SatNOGS",
        f"",
        f"*All connections: public APIs · permission-first · $0/month*",
        f"*github.com/meekotharaccoon-cell*",
    ]
    return "\n".join(lines)

def push_to_github(content):
    report_path = Path("data/space_report.md")
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(content)
    print(f"  {green('✓')} Report saved to {report_path}")
    if os.system("git status > /dev/null 2>&1") == 0:
        os.system('git add data/space_report.md')
        os.system('git commit -m "🛸 space bridge report update"')
        result = os.system('git push origin main 2>&1')
        if result == 0: print(f"  {green('✓')} Pushed to GitHub")

# ─────────────────────────────────────────────
# LIVE DASHBOARD
# ─────────────────────────────────────────────
def live_dashboard():
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print_header()
            display_iss()
            print(f"\n  {dim('Refreshing every 10s · Ctrl+C to stop')}")
            time.sleep(10)
    except KeyboardInterrupt:
        print(f"\n{green('Space bridge closed. The cosmos continues.')}")

def print_header():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print()
    print(green("━" * 60))
    print(green("  🛸 MEEKO MYCELIUM — SPACE BRIDGE"))
    print(f"  {dim('Connecting your desktop to actual hardware in orbit')}")
    print(f"  {dim(now)}")
    print(green("━" * 60))

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Meeko Mycelium Space Bridge")
    parser.add_argument("--iss",        action="store_true")
    parser.add_argument("--apod",       action="store_true")
    parser.add_argument("--asteroids",  action="store_true")
    parser.add_argument("--solar",      action="store_true")
    parser.add_argument("--mars",       action="store_true")
    parser.add_argument("--satellites", action="store_true")
    parser.add_argument("--live",       action="store_true")
    parser.add_argument("--push",       action="store_true")
    parser.add_argument("--lat",        type=float, default=None)
    parser.add_argument("--lon",        type=float, default=None)
    args = parser.parse_args()

    global YOUR_LAT, YOUR_LON
    if args.lat: YOUR_LAT = args.lat
    if args.lon: YOUR_LON = args.lon

    if args.live: live_dashboard(); return

    print_header()

    if args.push:
        report = generate_space_report()
        push_to_github(report)
        print(report)
        return

    if any([args.iss, args.apod, args.asteroids, args.solar, args.mars, args.satellites]):
        if args.iss:        display_iss()
        if args.apod:       display_apod()
        if args.asteroids:  display_asteroids()
        if args.solar:      display_solar()
        if args.mars:       display_mars()
        if args.satellites: display_satellites()
    else:
        display_iss()
        display_solar()
        display_asteroids()
        display_apod()
        display_mars()
        display_satellites()

    print()
    print(green("━" * 60))
    print(f"  {dim('space_bridge.py · Meeko Mycelium · $0/month · permission-first')}")
    print(green("━" * 60))
    print()

if __name__ == "__main__":
    main()
