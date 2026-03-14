import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
path = r'C:\Users\meeko\Desktop\REVENUE_ENGINE.py'
content = open(path, encoding='utf-8').read()

content = content.replace(
    "def ask_ollama(prompt, model='mycelium'):",
    "def ask_ollama(prompt, model='llama3.2:latest'):"
)
content = content.replace(
    "urllib.request.urlopen(req, timeout=60)",
    "urllib.request.urlopen(req, timeout=120)"
)
old_opts = "'options': {'temperature': 0.7, 'num_predict': 800}"
new_opts = "'options': {'temperature': 0.6, 'num_predict': 300}"
content = content.replace(old_opts, new_opts)

open(path, 'w', encoding='utf-8').write(content)
print('PATCHED: llama3.2, timeout=120, num_predict=300')
