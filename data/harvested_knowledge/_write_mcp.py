import sys, os, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load secrets
secrets_path = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\.secrets')
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1)
        k,v = k.strip(), v.strip()
        if k and v:
            os.environ[k] = v

mcp_path = Path(os.environ.get('APPDATA','')) / 'Claude' / 'claude_desktop_config.json'

# Load existing to preserve preferences
existing = {}
if mcp_path.exists():
    try:
        existing = json.loads(mcp_path.read_text(encoding='utf-8'))
    except Exception:
        pass

conductor = os.environ.get('CONDUCTOR_TOKEN','')
stripe_key = os.environ.get('STRIPE_SECRET_KEY','')
pp_id  = os.environ.get('PAYPAL_CLIENT_ID','')
pp_sec = os.environ.get('PAYPAL_CLIENT_SECRET','')

config = dict(existing)
config['mcpServers'] = {
    "phantom-docs": {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://docs.phantom.com/mcp"]
    },
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": conductor}
    },
    "filesystem": {
        "command": "npx",
        "args": [
            "-y", "@modelcontextprotocol/server-filesystem",
            r"C:\Users\meeko\Desktop",
            r"C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY",
            r"C:\Users\meeko\Desktop\INVESTMENT_HQ",
            r"C:\Users\meeko\Desktop\UltimateAI_Master",
            r"C:\Users\meeko\Desktop\GAZA_ROSE_OMNI",
            r"C:\Users\meeko\Desktop\atomic-agents-conductor"
        ]
    },
    "memory": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "sqlite-gazarose": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite",
                 "--db-path", r"C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db"]
    },
    "stripe": {
        "command": "npx",
        "args": ["-y", "@stripe/agent-toolkit", "mcp-server", "--tools=all"],
        "env": {"STRIPE_SECRET_KEY": stripe_key}
    },
    "paypal": {
        "command": "npx",
        "args": ["-y", "@paypal/agent-toolkit", "--mode=mcp"],
        "env": {
            "PAYPAL_CLIENT_ID": pp_id,
            "PAYPAL_CLIENT_SECRET": pp_sec,
            "PAYPAL_ENVIRONMENT": "production"
        }
    }
}

# Backup
if mcp_path.exists():
    backup = mcp_path.with_suffix('.json.bak')
    backup.write_text(mcp_path.read_text(encoding='utf-8'))
    print("Backed up existing config to: " + str(backup))

mcp_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
servers = list(config['mcpServers'].keys())
print("MCP config written: " + str(len(servers)) + " servers")
for s in servers:
    print("  + " + s)
print()
print("Restart Claude Desktop to activate MCP servers.")
