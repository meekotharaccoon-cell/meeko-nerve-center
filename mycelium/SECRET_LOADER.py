import json
import os

def load_secrets():
    path = 'data/secrets.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            secrets = json.load(f)
            for key, value in secrets.items():
                os.environ[key] = value
        return True
    return False

if __name__ == "__main__":
    if load_secrets():
        print("🔑 Vault Unlocked. Environment variables set.")
    else:
        print("⚠️ Vault Missing! Create data/secrets.json first.")
