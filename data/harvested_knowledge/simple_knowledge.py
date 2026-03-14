import os 
import json 
from datetime import datetime 
 
print("=" * 70) 
print("SIMPLE KNOWLEDGE BASE SETUP") 
print("=" * 70) 
 
"# Create folders" 
os.makedirs("knowledge_base/chat_history", exist_ok=True) 
os.makedirs("knowledge_base/signed_docs", exist_ok=True) 
os.makedirs("knowledge_base/business_autopilot", exist_ok=True) 
 
"# Create README" 
with open("knowledge_base/README.md", "w") as f: 
    f.write("# SOLARPUNK KNOWLEDGE BASE") 
 
print("Done!") 
print("Folders created at: knowledge_base/") 
