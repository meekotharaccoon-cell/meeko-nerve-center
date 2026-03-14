"""Auto-configure Medusa with PayPal credentials from .secrets"""
import sys, os, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

secrets_path = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\.secrets')
for line in secrets_path.read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=',1); k,v = k.strip(), v.strip()
        if k and v: os.environ[k]=v

medusa_dir = Path(r'C:\Users\meeko\Desktop\meeko-shop')
if not medusa_dir.exists():
    print("Medusa not installed yet. Run INSTALL_MEDUSA.bat first.")
    sys.exit(0)

# Write .env for Medusa
env_content = f"""
JWT_SECRET=meeko-mycelium-secret-{os.urandom(8).hex()}
COOKIE_SECRET=meeko-cookie-{os.urandom(8).hex()}
DATABASE_URL=./meeko.db
PAYPAL_SANDBOX=false
PAYPAL_CLIENT_ID={os.environ.get('PAYPAL_CLIENT_ID','')}
PAYPAL_CLIENT_SECRET={os.environ.get('PAYPAL_CLIENT_SECRET','')}
MEDUSA_BACKEND_URL=http://localhost:9000
ADMIN_CORS=http://localhost:7001,http://localhost:3000
STORE_CORS=http://localhost:8000,http://localhost:3000
AUTH_CORS=http://localhost:7001,http://localhost:3000,http://localhost:8000
"""
env_path = medusa_dir / '.env'
env_path.write_text(env_content.strip(), encoding='utf-8')
print(f"✓ Medusa .env configured with PayPal credentials")
print(f"✓ Written to: {env_path}")
print()
print("To start Medusa:")
print("  cd C:\\Users\\meeko\\Desktop\\meeko-shop")
print("  npx medusa develop")
print()
print("Then open: http://localhost:7001 (admin panel)")
