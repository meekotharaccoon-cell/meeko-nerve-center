# SIMPLE ERROR SCANNER
import os, json, datetime

print("=== SIMPLE ERROR SCANNER ===")

# Check what exists right now
print("\n📁 Checking connected/ folder...")

connected_path = "connected"
if not os.path.exists(connected_path):
    print("❌ 'connected' folder doesn't exist!")
    print("   Creating it now...")
    os.makedirs(connected_path, exist_ok=True)
    print("   ✅ Created 'connected' folder")
else:
    # List what's in connected folder
    items = os.listdir(connected_path)
    print(f"   Found {len(items)} items in connected/")
    
    for item in items:
        item_path = os.path.join(connected_path, item)
        if os.path.isdir(item_path):
            # Check for .git
            has_git = os.path.exists(os.path.join(item_path, ".git"))
            # Count files
            try:
                file_count = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
            except:
                file_count = 0
            
            status = "✅" if has_git else "❌"
            print(f"   {status} {item}: Git={has_git}, Files={file_count}")

# Save simple report
report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "connected_folder_exists": os.path.exists("connected"),
    "items_in_connected": len(os.listdir("connected")) if os.path.exists("connected") else 0,
    "has_start_bat": os.path.exists("START.bat"),
    "has_push_bat": os.path.exists("PUSH.bat"),
    "cloudflare_site": "https://solarpunkagent.pages.dev"
}

with open("simple_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(f"\n📊 Simple report saved to: simple_report.json")
print("\n" + "="*50)
print("To see ACTUAL errors, we need repos in connected/ folder.")
print("\nIf connected/ is empty, we need to:")
print("1. Clone your existing repos into connected/")
print("2. Then run the error scanner")
print("="*50)
