import json
import re
import sys

print("?? LOCAL JSON FIXER")
print("=" * 50)

def clean_string(text):
    """Remove control characters that break JSON"""
    if not text:
        return text
    
    # Remove control characters (ASCII 0-31 except \t, \n, \r)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Fix common issues
    cleaned = cleaned.replace('\\', '\\\\')  # Escape backslashes
    cleaned = cleaned.replace('\r', '')      # Remove carriage returns
    
    return cleaned

def fix_json_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"?? File size: {len(content)} characters")
        
        # Try to parse as-is first
        try:
            data = json.loads(content)
            print("? JSON is ALREADY VALID!")
            return True
        except json.JSONDecodeError as e:
            print(f"??  Found JSON error: {e}")
            
            # Try line-by-line cleaning
            lines = content.split('\n')
            cleaned_lines = []
            
            for i, line in enumerate(lines, 1):
                cleaned_line = clean_string(line)
                if line != cleaned_line:
                    print(f"   Fixed line {i}: removed control characters")
                cleaned_lines.append(cleaned_line)
            
            # Reassemble
            cleaned_content = '\n'.join(cleaned_lines)
            
            # Try to parse cleaned version
            try:
                data = json.loads(cleaned_content)
                print("? JSON is VALID after cleaning!")
                
                # Write fixed version
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"?? Saved fixed version to {filename}")
                return True
                
            except json.JSONDecodeError as e2:
                print(f"? Still invalid after cleaning: {e2}")
                
                # Create minimal valid JSON structure
                print("\n?? Creating minimal valid JSON structure...")
                minimal_config = {
                    "github": {"token": ""},
                    "twitter": {
                        "api_key": "",
                        "api_secret": "",
                        "access_token": "",
                        "access_secret": "",
                        "bearer_token": ""
                    }
                }
                
                with open(filename + '.minimal', 'w', encoding='utf-8') as f:
                    json.dump(minimal_config, f, indent=2)
                
                print(f"? Created {filename}.minimal")
                print("Copy your actual keys into this file and rename it to config.json")
                return False
                
    except Exception as e:
        print(f"? Critical error: {e}")
        return False

if __name__ == "__main__":
    fix_json_file("config.json")
