import subprocess
import os
from datetime import datetime

def generate_content():
    """Generate content with Ollama - NO JSON, NO FILES to break"""
    print(" Generating content with Ollama...")
    
    prompt = """Write a 200-word helpful article about making money online honestly.
    Be practical, no hype, just real advice."""
    
    try:
        result = subprocess.run(
            ['ollama', 'run', 'mistral', prompt],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode == 0:
            content = result.stdout.strip()
            
            # Save it
            os.makedirs("content", exist_ok=True)
            filename = f"content/article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Generated: {datetime.now()}\n")
                f.write("="*50 + "\n")
                f.write(content)
                f.write("\n" + "="*50 + "\n")
                f.write(" AI-generated with Ollama | No hype, just help\n")
            
            print(f" Content saved: {filename}")
            print(f" Preview: {content[:100]}...")
            return True
        else:
            print(f" Ollama error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f" Error: {str(e)}")
        return False

def main():
    print("="*60)
    print(" SIMPLE AUTONOMOUS CONTENT GENERATOR")
    print("="*60)
    
    success = generate_content()
    
    if success:
        print("\n SUCCESS! System is working.")
        print(" Check 'content' folder for generated files.")
    else:
        print("\n Failed. Check if Ollama is running.")
    
    print("="*60)
    print("To schedule: Create Windows Task to run this daily at 6 AM")
    print("="*60)

if __name__ == "__main__":
    main()
