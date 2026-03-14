#!/usr/bin/env python3
"""
GAZA ROSE - AUTONOMOUS SYSTEM INVENTORY SCANNER
Scans every GAZA ROSE directory, every config file, every Python script
to build a complete inventory of what exists and what's missing.
Based on observability-first self-healing principles [citation:6]
"""

import os
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

class SystemInventory:
    def __init__(self):
        self.scan_root = r"C:\Users\meeko\Desktop"
        self.inventory_file = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\inventory.json"
        self.gaza_dirs = []
        self.components = {}
        self.missing = []
        self.outdated = []
        
    def scan_all_gaza_dirs(self):
        """Find every GAZA ROSE directory on your system"""
        print(" Scanning for GAZA ROSE directories...")
        
        for item in os.listdir(self.scan_root):
            if "GAZA_ROSE" in item.upper() and os.path.isdir(os.path.join(self.scan_root, item)):
                full_path = os.path.join(self.scan_root, item)
                self.gaza_dirs.append(full_path)
                print(f"   Found: {item}")
        
        # Also check autogpt directory
        if os.path.exists(r"C:\Users\meeko\autogpt"):
            self.gaza_dirs.append(r"C:\Users\meeko\autogpt")
            print(f"   Found: autogpt")
            
        return self.gaza_dirs
    
    def scan_for_components(self):
        """Scan every directory for Python files, configs, and requirements"""
        for gaza_dir in self.gaza_dirs:
            components = []
            
            # Check for Python files
            py_files = list(Path(gaza_dir).rglob("*.py"))
            components.append({"type": "python_scripts", "count": len(py_files), "files": [str(f) for f in py_files[:10]]})
            
            # Check for requirements.txt
            req_files = list(Path(gaza_dir).rglob("requirements.txt"))
            components.append({"type": "requirements", "count": len(req_files), "files": [str(f) for f in req_files]})
            
            # Check for package.json (Node.js)
            pkg_files = list(Path(gaza_dir).rglob("package.json"))
            components.append({"type": "package_json", "count": len(pkg_files), "files": [str(f) for f in pkg_files]})
            
            # Check for .env files (configuration)
            env_files = list(Path(gaza_dir).rglob(".env"))
            components.append({"type": "env_configs", "count": len(env_files), "files": [str(f) for f in env_files]})
            
            # Check for README (documentation)
            readme_files = list(Path(gaza_dir).rglob("README*"))
            components.append({"type": "documentation", "count": len(readme_files), "files": [str(f) for f in readme_files]})
            
            self.components[gaza_dir] = components
            
        return self.components
    
    def identify_gaps(self):
        """Identify what's missing from a complete autonomous system"""
        
        # Critical components for a self-evolving system [citation:4]
        critical_components = [
            {"name": "metacognitive_loop", "check": "self_monitoring", "status": False},
            {"name": "evaluation_framework", "check": "eval", "status": False},
            {"name": "feedback_collector", "check": "feedback", "status": False},
            {"name": "auto_retrain", "check": "retrain", "status": False},
            {"name": "performance_tracker", "check": "metrics", "status": False}
        ]
        
        # Search for these patterns in Python files
        for gaza_dir in self.gaza_dirs:
            for py_file in Path(gaza_dir).rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        for comp in critical_components:
                            if comp['check'] in content.lower():
                                comp['status'] = True
                                comp['found_in'] = str(py_file)
                except:
                    pass
        
        # Identify missing components
        for comp in critical_components:
            if not comp['status']:
                self.missing.append(comp['name'])
        
        return self.missing
    
    def generate_report(self):
        """Generate complete inventory report"""
        report = {
            "scan_time": str(datetime.now()),
            "directories_found": len(self.gaza_dirs),
            "directories": self.gaza_dirs,
            "components": self.components,
            "missing_components": self.missing,
            "system_health": "needs_upgrade" if len(self.missing) > 0 else "optimal"
        }
        
        with open(self.inventory_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

if __name__ == "__main__":
    inventory = SystemInventory()
    inventory.scan_all_gaza_dirs()
    inventory.scan_for_components()
    inventory.identify_gaps()
    report = inventory.generate_report()
    
    print(f"\n SCAN COMPLETE:")
    print(f"   Directories found: {len(inventory.gaza_dirs)}")
    print(f"   Missing components: {len(inventory.missing)}")
    print(f"   Report saved to: {inventory.inventory_file}")
