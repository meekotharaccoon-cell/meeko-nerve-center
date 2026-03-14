#!/usr/bin/env python3
"""
GAZA ROSE - SELF-HEALING ERROR FIXER
USES YOUR LOCAL AI TO FIX ERRORS IN REAL TIME
"""

import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime

# ==============================================
# YOUR LOCAL AI - OLLAMA + MISTRAL
# ==============================================
OLLAMA_URL = "http://localhost:11434/api/generate"
AI_MODEL = "mistral"

# ==============================================
# YOUR SYSTEM PATHS - AUTO-DETECTED
# ==============================================
AUTOGPT_DIR = "C:/Users/meeko/autogpt"
PYTHON312 = "C:/Users/meeko/AppData/Local/Programs/Python/Python312/python.exe"

class SelfHealingWatcher:
    def __init__(self):
        self.error_log = []
        self.fix_log = []
        self.attempts = 0
        self.successes = 0
        
    def ask_ai(self, error_text, context=""):
        """Send error to your local AI for a fix"""
        prompt = f"""
You are the GAZA ROSE self-healing system. Your job is to fix errors.

ERROR:
{error_text}

CONTEXT:
{context}

TASK:
1. Analyze this error
2. Generate a COMPLETE PowerShell command that will fix it
3. Output ONLY the PowerShell command. No explanations. No comments.
4. The command must be ready to copy-paste and run.

POWER$HELL COMMAND:
"""
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": AI_MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except Exception as e:
            return f"Write-Host ' AI ERROR: {e}'"
        return ""
    
    def execute_fix(self, fix_command):
        """Execute a fix command and capture result"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  APPLYING FIX...")
        try:
            result = subprocess.run(
                ["powershell", "-Command", fix_command],
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def watch_and_heal(self, target_command, max_attempts=10):
        """
        Watch a command, catch errors, fix them, retry
        """
        print("\n" + "="*60)
        print("   GAZA ROSE - SELF-HEALING WATCHER ACTIVATED")
        print("="*60)
        print(f"   WATCHING: {target_command[:50]}...")
        print(f"   AI MODEL: {AI_MODEL}")
        print(f"   MAX ATTEMPTS: {max_attempts}")
        print("="*60 + "\n")
        
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            self.attempts += 1
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  ATTEMPT #{attempt}")
            
            # Execute the target command
            result = subprocess.run(
                ["powershell", "-Command", target_command],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.successes += 1
                print(f"\n SUCCESS! Command executed cleanly.")
                print(f" STATS: {self.successes}/{self.attempts} successes")
                return True
            
            # ERROR DETECTED
            error_text = result.stderr if result.stderr else result.stdout
            print(f"\n ERROR DETECTED:")
            print(f"   {error_text[:200]}...")
            
            # Ask AI for a fix
            print(f"    ASKING AI FOR FIX...")
            fix_command = self.ask_ai(error_text, f"Command that failed: {target_command}")
            
            if not fix_command or "Write-Host" in fix_command:
                print(f"    AI COULDN'T GENERATE FIX. RETRYING...")
                time.sleep(2)
                continue
            
            print(f"    AI SUGGESTS: {fix_command[:100]}...")
            
            # Apply the fix
            fix_result = self.execute_fix(fix_command)
            
            if fix_result["success"]:
                print(f"    FIX APPLIED SUCCESSFULLY")
                self.fix_log.append({
                    "attempt": attempt,
                    "error": error_text[:200],
                    "fix": fix_command,
                    "result": "success"
                })
            else:
                print(f"    FIX FAILED: {fix_result.get('error', 'unknown')}")
                self.fix_log.append({
                    "attempt": attempt,
                    "error": error_text[:200],
                    "fix": fix_command,
                    "result": "failed",
                    "error_details": fix_result.get('stderr', '')
                })
            
            time.sleep(2)
        
        print(f"\n MAX ATTEMPTS ({max_attempts}) REACHED. COULD NOT FIX.")
        return False

# ==============================================
# MAIN EXECUTION - WATCH AND HEAL FOREVER
# ==============================================
if __name__ == "__main__":
    watcher = SelfHealingWatcher()
    
    # TARGET COMMAND TO WATCH (CHANGE THIS AS NEEDED)
    TARGET = "cd C:/Users/meeko/autogpt; C:/Users/meeko/AppData/Local/Programs/Python/Python312/python.exe -m autogpt --agent gaza_rose_agent --continuous"
    
    while True:
        watcher.watch_and_heal(TARGET)
        print("\n RESTARTING WATCHER IN 60 SECONDS...")
        time.sleep(60)
