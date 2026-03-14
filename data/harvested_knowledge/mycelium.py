from langchain_community.llms import Ollama
import subprocess
import json

llm = Ollama(model="mistral")

# Get real system info
processes = subprocess.run(
    ["powershell", "-Command", 
     "Get-Process | Sort-Object -Property WS -Descending | Select-Object -First 10 Name, WS, CPU | ConvertTo-Json"],
    capture_output=True, text=True
).stdout

# Have your local AI analyze YOUR actual running system
analysis = llm.invoke(f"""
You are a system optimization AI. Analyze these real running processes from my machine and give me specific actionable recommendations:

{processes}

Be specific, practical, and prioritize what matters most.
""")

print("\n=== YOUR SYSTEM ANALYSIS ===\n")
print(analysis)