#!/usr/bin/env python3
"""
GAZA ROSE - AUTONOMOUS GITHUB SOLUTION FINDER
Searches GitHub for the best open-source solutions to fill gaps in your system.
Based on self-evolving agent research [citation:1] and recursive intelligence [citation:4]
"""

import os
import json
import requests
import time
from datetime import datetime

class SolutionFinder:
    def __init__(self):
        self.inventory_file = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\inventory.json"
        self.solutions_file = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\solutions.json"
        self.search_terms = {
            "metacognitive_loop": ["self-aware agent", "metacognitive AI", "self-monitoring system"],
            "evaluation_framework": ["agent evaluation", "LLM as judge", "prompt evals"],
            "feedback_collector": ["feedback collection", "human feedback loop", "RLHF"],
            "auto_retrain": ["automatic retraining", "self-improving model", "online learning"],
            "performance_tracker": ["agent metrics", "performance monitoring", "observability"]
        }
        self.found_solutions = []
        
    def load_inventory(self):
        """Load the inventory to see what's missing"""
        if os.path.exists(self.inventory_file):
            with open(self.inventory_file, 'r') as f:
                return json.load(f)
        return None
    
    def search_github(self, query, max_results=5):
        """Search GitHub for repositories matching the query"""
        try:
            # Using GitHub's public search API (no key needed for basic search)
            url = f"https://api.github.com/search/repositories?q={query}+stars:>10&sort=stars&order=desc"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GAZA-ROSE-Self-Upgrading-System"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])[:max_results]
            else:
                print(f" GitHub API returned {response.status_code}")
                return []
        except Exception as e:
            print(f" GitHub search error: {e}")
            return []
    
    def search_pypi(self, query):
        """Search PyPI for Python packages"""
        try:
            url = f"https://pypi.org/pypi/{query}/json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return {"name": query, "source": "pypi", "exists": True}
            return None
        except:
            return None
    
    def find_solutions_for_gap(self, gap_name, search_terms):
        """Find solutions for a specific gap using multiple search terms"""
        print(f"\n   Searching for: {gap_name}")
        solutions = []
        
        for term in search_terms:
            print(f"    Query: '{term}'")
            github_results = self.search_github(term)
            
            for repo in github_results:
                solution = {
                    "gap": gap_name,
                    "search_term": term,
                    "name": repo["name"],
                    "url": repo["html_url"],
                    "description": repo["description"],
                    "stars": repo["stargazers_count"],
                    "language": repo["language"],
                    "source": "github",
                    "score": repo["stargazers_count"] * 1.0
                }
                solutions.append(solution)
                print(f"       Found: {repo['name']} ({repo['stargazers_count']} )")
            
            time.sleep(0.5)  # Be nice to GitHub API
        
        # Sort by stars (best first)
        solutions.sort(key=lambda x: x["stars"], reverse=True)
        return solutions[:3]  # Top 3 solutions per gap
    
    def find_all_solutions(self):
        """Find solutions for all missing components"""
        inventory = self.load_inventory()
        if not inventory:
            print(" No inventory found. Run inventory scanner first.")
            return []
        
        missing = inventory.get("missing_components", [])
        print(f"\n Searching for solutions to {len(missing)} missing components...")
        
        for gap in missing:
            if gap in self.search_terms:
                solutions = self.find_solutions_for_gap(gap, self.search_terms[gap])
                for sol in solutions:
                    self.found_solutions.append(sol)
            else:
                # Generic search
                solutions = self.find_solutions_for_gap(gap, [gap])
                for sol in solutions:
                    self.found_solutions.append(sol)
        
        # Save solutions
        with open(self.solutions_file, 'w') as f:
            json.dump({
                "scan_time": str(datetime.now()),
                "solutions_found": len(self.found_solutions),
                "solutions": self.found_solutions
            }, f, indent=2)
        
        return self.found_solutions

if __name__ == "__main__":
    finder = SolutionFinder()
    solutions = finder.find_all_solutions()
    
    print(f"\n SOLUTION SCAN COMPLETE:")
    print(f"   Solutions found: {len(solutions)}")
    print(f"   Top recommendations saved to: {finder.solutions_file}")
