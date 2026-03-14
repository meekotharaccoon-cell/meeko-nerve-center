#!/usr/bin/env python3
"""
Agent command: Check system and suggest upgrades
Run: python upgrade_check.py
"""

import subprocess
import os
import sys

def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def main():
    print("AGENT: Running upgrade diagnostic...\n")
    
    # Check current versions
    checks = [
        ("Ollama", "ollama --version"),
        ("Docker", "docker --version"),
        ("Python", "python --version"),
        ("Chainlit", "chainlit --version"),
    ]
    
    versions = {}
    for name, cmd in checks:
        ok, output = run(cmd)
        versions[name] = output.strip() if ok else "NOT FOUND"
        print(f"{name}: {versions[name]}")
    
    # Check Ollama models
    print("\n--- Ollama Models ---")
    ok, models = run("ollama list")
    if ok:
        print(models)
    else:
        print("Cannot list models - Ollama not running?")
    
    # Check Docker containers
    print("\n--- Docker Containers ---")
    ok, containers = run("docker ps --format '{{.Names}}'")
    if ok and containers.strip():
        print("Running:", containers.replace('\n', ', '))
    else:
        print("No containers running")
    
    # Suggest upgrades
    print("\n--- AGENT UPGRADE RECOMMENDATIONS ---")
    
    if "llama3.2" in models:
        print("✓ llama3.2 present - update with: ollama pull llama3.2")
    
    if "n8n" not in containers:
        print("✗ n8n not running - start with: docker compose up -d n8n")
    
    if "qdrant" not in containers:
        print("✗ qdrant not running - start with: docker compose up -d qdrant")
    
    print("\n--- QUICK FIXES ---")
    print("Update all Ollama models: ollama list | ForEach { ollama pull $_.Split()[0] }")
    print("Update Docker images: docker compose pull")
    print("Update Python packages: pip list --outdated")

if __name__ == "__main__":
    main()