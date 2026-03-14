import os 
import json 
from datetime import datetime 
 
print("=" * 70) 
print("?? SIMPLE KNOWLEDGE BASE SETUP") 
print("=" * 70) 
 
"# Create directories" 
os.makedirs("knowledge_base/signed_documents", exist_ok=True) 
os.makedirs("knowledge_base/chat_history", exist_ok=True) 
 
"# Create simple index" 
index = {"last_updated": datetime.now().isoformat(), "files": []} 
 
"# Create README" 
with open("knowledge_base/README.md", "w") as f: 
    f.write("# ?? SOLARPUNK KNOWLEDGE BASE\\n\\nEverything from our chat history goes here.") 
index["files"].append("README.md") 
 
"print('? Created knowledge base structure')" 
"print(f'Location: {os.path.abspath(\"knowledge_base\")}')" 
