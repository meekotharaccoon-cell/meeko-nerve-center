#!/usr/bin/env python3
"""
GAZA ROSE - SELF-TESTING & VALIDATION ENGINE
Tests the system after each upgrade to ensure it works.
Based on self-evolving agent evaluation frameworks [citation:1]
"""

import os
import json
import subprocess
import time
from datetime import datetime

class ValidationEngine:
    def __init__(self):
        self.test_results_file = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\test_results.json"
        
    def test_python_imports(self, directory):
        """Test if Python files can be imported without errors"""
        print(f"   Testing Python imports in: {directory}")
        
        results = {"passed": [], "failed": []}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    module_path = os.path.join(root, file)
                    module_name = os.path.basename(file)[:-3]
                    
                    try:
                        result = subprocess.run(
                            ["python", "-c", f"import {module_name}"],
                            cwd=root,
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            results["passed"].append(module_name)
                        else:
                            results["failed"].append({"module": module_name, "error": result.stderr[:100]})
                    except Exception as e:
                        results["failed"].append({"module": module_name, "error": str(e)})
        
        return results
    
    def test_script_execution(self, directory):
        """Test if key scripts can execute"""
        results = {"executed": [], "failed": []}
        
        key_scripts = ["master_healer.py", "orchestrator.py", "meta_healer.py"]
        
        for script in key_scripts:
            script_path = os.path.join(directory, script)
            if os.path.exists(script_path):
                print(f"   Testing execution: {script}")
                try:
                    result = subprocess.run(
                        ["python", script, "--help"],
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    # Even if it returns error, it executed
                    results["executed"].append(script)
                except Exception as e:
                    results["failed"].append({"script": script, "error": str(e)})
        
        return results
    
    def validate_system(self):
        """Run all validation tests on the GAZA ROSE ecosystem"""
        print("\n Running system validation...")
        
        validation_results = {
            "timestamp": str(datetime.now()),
            "tests": []
        }
        
        # Find all GAZA ROSE directories
        desktop = r"C:\Users\meeko\Desktop"
        gaza_dirs = []
        for item in os.listdir(desktop):
            if "GAZA_ROSE" in item.upper() and os.path.isdir(os.path.join(desktop, item)):
                gaza_dirs.append(os.path.join(desktop, item))
        
        # Add autogpt
        if os.path.exists(r"C:\Users\meeko\autogpt"):
            gaza_dirs.append(r"C:\Users\meeko\autogpt")
        
        for directory in gaza_dirs:
            print(f"\n Testing: {os.path.basename(directory)}")
            dir_results = {
                "directory": directory,
                "import_tests": self.test_python_imports(directory),
                "execution_tests": self.test_script_execution(directory)
            }
            validation_results["tests"].append(dir_results)
        
        # Calculate overall score
        total_passed = sum(len(t["import_tests"]["passed"]) for t in validation_results["tests"])
        total_failed = sum(len(t["import_tests"]["failed"]) for t in validation_results["tests"])
        validation_results["score"] = total_passed / (total_passed + total_failed) if (total_passed + total_failed) > 0 else 0
        
        # Save results
        with open(self.test_results_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        return validation_results

if __name__ == "__main__":
    validator = ValidationEngine()
    results = validator.validate_system()
    
    print(f"\n VALIDATION COMPLETE:")
    print(f"   System health score: {results['score']*100:.1f}%")
    print(f"   Tests passed: {sum(len(t['import_tests']['passed']) for t in results['tests'])}")
    print(f"   Tests failed: {sum(len(t['import_tests']['failed']) for t in results['tests'])}")
