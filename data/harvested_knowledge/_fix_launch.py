import sys
with open(r'C:\Users\meeko\Desktop\LAUNCH_EVERYTHING.py', encoding='utf-8') as f:
    src = f.read()

# Fix unicode chars that break cp1252 terminal
src = src.replace('\u2192', '->')
src = src.replace('\u2190', '<-')
src = src.replace('\u2713', 'OK')
src = src.replace('\u2717', 'X')
src = src.replace('\u2192', '->')

# Fix main block encoding
old = "if __name__ == '__main__':"
new = "if __name__ == '__main__':\n    sys.stdout.reconfigure(encoding='utf-8', errors='replace')"
src = src.replace(old, new, 1)

with open(r'C:\Users\meeko\Desktop\LAUNCH_EVERYTHING.py', 'w', encoding='utf-8') as f:
    f.write(src)

print('Fixed unicode + encoding')
