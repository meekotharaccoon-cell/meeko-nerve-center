import os
import subprocess
import re
import json

def scan_network():
    print("📡 Network Sentry: Pinging the garden perimeter...")
    # Get local ARP table
    try:
        output = subprocess.check_output("arp -a", shell=True).decode('ascii')
        # Find all IP/MAC patterns
        devices = re.findall(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]{17})', output)
        
        known_path = 'data/known_devices.json'
        if not os.path.exists(known_path):
            with open(known_path, 'w') as f: json.dump([], f)
        
        with open(known_path, 'r') as f:
            known_macs = json.load(f)

        new_devices = []
        for ip, mac in devices:
            if mac not in known_macs:
                new_devices.append({"ip": ip, "mac": mac})
                print(f"⚠️ UNKNOWN DEVICE DETECTED: {ip} [{mac}]")

        if new_devices:
            with open('data/knowledge_bank.txt', 'a', encoding='utf-8') as f:
                for dev in new_devices:
                    f.write(f"\n🚨 [Sentry Alert] Unknown device at {dev['ip']} ({dev['mac']})\n")
        else:
            print("✅ Perimeter secure. Only known lifeforms detected.")

    except Exception as e:
        print(f"Sentry Error: {e}")

if __name__ == "__main__":
    scan_network()
