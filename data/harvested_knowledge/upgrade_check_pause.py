#!/usr/bin/env python3
"""
Agent command: Check system and suggest upgrades
Run: python upgrade_check_pause.py
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
    print("=" * 50)
    print("AGENT: Running upgrade diagnostic...")
    print("=" * 50)
    
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
        status = "✓" if ok else "✗"
        print(f"\n{status} {name}:")
        print(f"  {versions[name]}")
    
    # Check Ollama models
    print("\n" + "=" * 50)
    print("OLLAMA MODELS")
    print("=" * 50)
    ok, models = run("ollama list")
    if ok:
        print(models)
    else:
        print("✗ Cannot list models - Ollama not running?")
        print("  Fix: ollama serve")
    
    # Check Docker containers
    print("\n" + "=" * 50)
    print("DOCKER CONTAINERS")
    print("=" * 50)
    ok, containers = run("docker ps --format '{{.Names}}'")
    if ok and containers.strip():
        print("✓ Running:", containers.replace('\n', ', '))
    else:
        print("✗ No containers running")
        print("  Fix: docker compose up -d")
    
    # Suggest upgrades
    print("\n" + "=" * 50)
    print("AGENT RECOMMENDATIONS")
    print("=" * 50)
    
    if ok and "llama3.2" in models:
        print("• Update llama3.2: ollama pull llama3.2")
    
    if ok and "n8n" not in containers:
        print("• Start n8n: docker compose up -d n8n")
    
    if ok and "qdrant" not in containers:
        print("• Start qdrant: docker compose up -d qdrant")
    
    print("\n• Update all models: ollama list | ForEach { ollama pull $_.Split()[0] }")
    print("• Update Docker images: docker compose pull")
    print("• Update Python packages: pip list --outdated")
    
    # PAUSE - keep window open
    print("\n" + "=" * 50)
    print("Press Enter to close...")
    print("=" * 50)
    input()

if __name__ == "__main__":
    main()