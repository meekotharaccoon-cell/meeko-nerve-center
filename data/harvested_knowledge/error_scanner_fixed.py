import os, json, datetime 
ECHO is off.
print("=== ERROR SCANNER ===") 
ECHO is off.
# Scan connected folder 
connected_path = "connected" 
if os.path.exists(connected_path): 
    items = os.listdir(connected_path) 
    print(f"Found {len(items)} items in connected/") 
    for item in items: 
        path = os.path.join(connected_path, item) 
        if os.path.isdir(path): 
            has_git = os.path.exists(os.path.join(path, ".git")) 
            print(f"  {'✅' if has_git else '❌'} {item}: Git={has_git}") 
else: 
    print("No connected folder") 
ECHO is off.
# Save report 
report = {"timestamp": datetime.datetime.now().isoformat()} 
with open("scan_report.json", "w") as f: 
    json.dump(report, f, indent=2) 
print("Report saved") 
