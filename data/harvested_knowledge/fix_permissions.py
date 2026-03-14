#!/usr/bin/env python3
"""
GAZA ROSE - PERMISSION FIXER
Ensures all directories your healer needs are writable [citation:3][citation:9]
"""

import os
import subprocess
import sys
from pathlib import Path

# Directories that need write access
HEALER_DIRS = [
    r"C:\Users\meeko\Desktop\GAZA_ROSE_HEALER",
    r"C:\Users\meeko\autogpt",
    r"C:\Users\meeko\Desktop\GAZA_ROSE_WORKING_BOT",
    r"C:\Users\meeko\Desktop\GAZA_ROSE_FORCE_BOT",
    r"C:\Users\meeko\Desktop\GAZA_ROSE_SELF_HEALING_ECOSYSTEM",
    r"C:\Users\meeko\Desktop\GAZA_ROSE_CONTINUATION",
    r"C:\Users\meeko\Desktop\GAZA_ROSE_VERIFICATION"
]

def fix_permissions(path):
    """Fix permissions on a directory [citation:9]"""
    print(f"🔧 Fixing: {path}")
    
    # Take ownership (Windows)
    try:
        subprocess.run(f"takeown /f \"{path}\" /r /d y", shell=True, capture_output=True)
        subprocess.run(f"icacls \"{path}\" /grant Users:F /T /Q", shell=True, capture_output=True)
        subprocess.run(f"icacls \"{path}\" /grant Everyone:F /T /Q", shell=True, capture_output=True)
        print(f"  ✅ Permissions granted")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🔓 GAZA ROSE - PERMISSION FIXER")
    print("="*60)
    print("  This script grants write access to all healing directories")
    print("  Must be run as Administrator")
    print("="*60 + "\n")
    
    # Check if running as admin
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("❌ This script must be run as Administrator!")
        print("   Right-click and select 'Run as Administrator'")
        sys.exit(1)
    
    for dir_path in HEALER_DIRS:
        if os.path.exists(dir_path):
            fix_permissions(dir_path)
    
    print("\n✅ Permission fixes complete")
    print("🚀 Now run the elevated healer from Desktop")
    input("\nPress Enter to exit...")
