#!/usr/bin/env python3
"""
GAZA ROSE - AUTONOMOUS DOWNLOADER & INTEGRATOR
Downloads the best solutions from GitHub and integrates them into your system.
Based on self-assembling multi-agent research [citation:4]
"""

import os
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

class AutonomousIntegrator:
    def __init__(self):
        self.solutions_file = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\solutions.json"
        self.inventory_file = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\inventory.json"
        self.download_dir = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\downloads"
        self.integration_log = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\integration_log.json"
        
        os.makedirs(self.download_dir, exist_ok=True)
        
    def load_solutions(self):
        """Load the solutions found by the finder"""
        if os.path.exists(self.solutions_file):
            with open(self.solutions_file, 'r') as f:
                return json.load(f)
        return {"solutions": []}
    
    def download_repo(self, repo_url, repo_name):
        """Download a GitHub repository"""
        target_dir = os.path.join(self.download_dir, repo_name)
        
        # Check if already downloaded
        if os.path.exists(target_dir):
            print(f"   Already downloaded: {repo_name}")
            return target_dir
        
        print(f"   Downloading: {repo_name}")
        try:
            result = subprocess.run(
                ["git", "clone", repo_url, target_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"   Downloaded to: {target_dir}")
                return target_dir
            else:
                print(f"   Download failed: {result.stderr[:100]}")
                return None
        except Exception as e:
            print(f"   Download error: {e}")
            return None
    
    def find_best_integration_target(self, solution):
        """Find the best GAZA ROSE directory to integrate this solution into"""
        inventory_file = self.inventory_file
        if os.path.exists(inventory_file):
            with open(inventory_file, 'r') as f:
                inventory = json.load(f)
                dirs = inventory.get("directories", [])
                
                # Prefer working bot or continuation directories
                for d in dirs:
                    if "WORKING_BOT" in d or "CONTINUATION" in d:
                        return d
                
                # Otherwise use the first directory
                if dirs:
                    return dirs[0]
        
        # Default fallback
        return r"C:\Users\meeko\Desktop\GAZA_ROSE_CONTINUATION"
    
    def integrate_solution(self, solution, downloaded_path):
        """Integrate a downloaded solution into your system"""
        if not downloaded_path:
            return False
        
        target_base = self.find_best_integration_target(solution)
        solution_name = solution["name"]
        target_dir = os.path.join(target_base, f"integrated_{solution_name}")
        
        print(f"   Integrating into: {target_dir}")
        
        # Copy the solution to the target directory
        try:
            shutil.copytree(downloaded_path, target_dir, dirs_exist_ok=True)
            print(f"   Copied to: {target_dir}")
            
            # Create integration marker
            marker_file = os.path.join(target_dir, ".GAZA_ROSE_INTEGRATED")
            with open(marker_file, 'w') as f:
                f.write(f"Integrated on: {datetime.now()}\n")
                f.write(f"Source: {solution['url']}\n")
                f.write(f"Gap: {solution.get('gap', 'unknown')}\n")
            
            # Try to install dependencies
            if os.path.exists(os.path.join(target_dir, "requirements.txt")):
                print(f"   Installing Python dependencies...")
                subprocess.run(
                    ["pip", "install", "-r", "requirements.txt"],
                    cwd=target_dir,
                    capture_output=True
                )
            
            if os.path.exists(os.path.join(target_dir, "package.json")):
                print(f"   Installing Node dependencies...")
                subprocess.run(["npm", "install"], cwd=target_dir, capture_output=True)
            
            return True
        except Exception as e:
            print(f"   Integration failed: {e}")
            return False
    
    def run_integration_cycle(self):
        """Run one integration cycle"""
        solutions_data = self.load_solutions()
        solutions = solutions_data.get("solutions", [])
        
        if not solutions:
            print(" No solutions found to integrate.")
            return
        
        print(f"\n Integrating {len(solutions)} solutions...")
        
        integration_results = []
        
        for solution in solutions[:5]:  # Limit to top 5 per cycle
            print(f"\n Processing: {solution['name']}")
            downloaded = self.download_repo(solution['url'], solution['name'])
            if downloaded:
                success = self.integrate_solution(solution, downloaded)
                integration_results.append({
                    "name": solution['name'],
                    "url": solution['url'],
                    "success": success,
                    "time": str(datetime.now())
                })
        
        # Save integration log
        with open(self.integration_log, 'w') as f:
            json.dump({
                "last_run": str(datetime.now()),
                "integrations": integration_results
            }, f, indent=2)
        
        return integration_results

if __name__ == "__main__":
    integrator = AutonomousIntegrator()
    results = integrator.run_integration_cycle()
    
    print(f"\n INTEGRATION COMPLETE:")
    print(f"   Successful integrations: {len([r for r in results if r['success']])}")
    print(f"   Failed integrations: {len([r for r in results if not r['success']])}")
