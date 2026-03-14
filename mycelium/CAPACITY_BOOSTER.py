import os
import time
import subprocess

def get_idle_time():
    # USES Windows 'User32.dll' to find how long since last input
    try:
        from ctypes import Structure, windll, c_uint, sizeof, byref
        class LASTINPUTINFO(Structure):
            _fields_ = [("cbSize", c_uint), ("dwTime", c_uint)]
        
        lii = LASTINPUTINFO()
        lii.cbSize = sizeof(lii)
        windll.user32.GetLastInputInfo(byref(lii))
        millis = windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    except:
        return 0

def regulate_swarm():
    idle_seconds = get_idle_time()
    
    if idle_seconds > 300: # 5 Minutes
        print(f"🌙 System Idle ({int(idle_seconds)}s). Activating TURBO MODE.")
        # Trigger heavy tasks
        os.environ["SWARM_MODE"] = "TURBO"
        # Example: start local LLM or heavy data crunching
    else:
        print("👤 User Active. Throttling Swarm to background priority.")
        os.environ["SWARM_MODE"] = "STEALTH"
        # Lower process priority of other python scripts
        pid = os.getpid()
        os.system(f"wmic process where ProcessId={pid} CALL setpriority 'low priority'")

if __name__ == "__main__":
    regulate_swarm()
