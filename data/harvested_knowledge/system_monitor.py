import json, requests, time, os, sys, subprocess
from datetime import datetime
import psutil

print("?? SOLARPUNK SYSTEM MONITOR")
print("="*60)
print("Ensuring all autonomous systems remain running 24/7")

def check_process(name):
    """Check if a Python process is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if name in cmdline:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def restart_process(script_name):
    """Restart a Python script"""
    try:
        subprocess.Popen([sys.executable, script_name], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except:
        return False

def system_health_check():
    """Check health of all systems"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] SYSTEM HEALTH CHECK")
    print("-" * 40)
    
    systems = {
        "twitter_bot": "twitter_bot.py",
        "github_deployer": "github_deployer.py", 
        "revenue_engine": "tax_simple_revenue.py"
    }
    
    all_healthy = True
    
    for name, script in systems.items():
        if os.path.exists(script):
            if check_process(script):
                print(f"? {name}: RUNNING")
            else:
                print(f"? {name}: STOPPED - RESTARTING")
                if restart_process(script):
                    print(f"   ? RESTARTED: {name}")
                else:
                    print(f"   ? FAILED TO RESTART: {name}")
                    all_healthy = False
        else:
            print(f"??  {name}: SCRIPT NOT FOUND")
    
    return all_healthy

def log_system_status():
    """Log system status to file"""
    with open("system_status.log", "a") as f:
        f.write(f"{datetime.now().isoformat()} - System monitoring active\n")

# Main monitoring loop
print("\n?? Starting 24/7 system monitor...")
print("Will check and restart failed processes every 5 minutes")

while True:
    try:
        system_health_check()
        log_system_status()
        
        # Check every 5 minutes
        for i in range(300):  # 300 seconds = 5 minutes
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n?? Monitor stopped by user")
        break
    except Exception as e:
        print(f"\n??  Monitor error: {e}")
        time.sleep(60)  # Wait 1 minute on error
