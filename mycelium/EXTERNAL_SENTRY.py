import os
import requests

def look_outside():
    sentry_log = 'data/external_signals.txt'
    # Example: Watching a public GitHub Gist or a specific URL for 'commands'
    # For now, we simulate by checking for a local 'incoming.signal' file
    signal_file = 'incoming.signal'
    
    if os.path.exists(signal_file):
        with open(signal_file, 'r') as f:
            signal = f.read().strip()
        
        with open(sentry_log, 'a') as log:
            log.write(f"SIGNAL RECEIVED: {signal}\n")
        
        print(f"🛰️ Sentry: Detected external signal: {signal}")
        os.remove(signal_file)
    else:
        print("🛰️ Sentry: No external signals detected.")

if __name__ == "__main__":
    look_outside()
