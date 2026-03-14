"""Fix double-quote syntax errors left by PCRF replacement in Python files"""
import os, re

DESKTOP = r"C:\Users\meeko\Desktop"
SKIP = {"mycelium_env", "node_modules", "__pycache__", ".git", "venv"}

fixed = []

for root, dirs, files in os.walk(DESKTOP):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in files:
        if not f.endswith(".py"):
            continue
        path = os.path.join(root, f)
        try:
            content = open(path, "r", encoding="utf-8", errors="ignore").read()
            # Fix ""https://... pattern (double leading quote)
            new = content.replace('"https://give.pcrf.net/campaign/739651/donate"',
                                  '"https://give.pcrf.net/campaign/739651/donate"')
            new = new.replace('"https://give.pcrf.net/campaign/739651/donate"',
                              '"https://give.pcrf.net/campaign/739651/donate"')
            if new != content:
                open(path, "w", encoding="utf-8").write(new)
                fixed.append(path.replace(DESKTOP, ""))
        except Exception as e:
            print(f"Error {f}: {e}")

print(f"Fixed {len(fixed)} files:")
for f in fixed:
    print(f"  {f}")
print("DONE")
