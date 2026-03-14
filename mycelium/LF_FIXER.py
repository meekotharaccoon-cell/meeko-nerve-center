import os

def fix_line_endings():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.py', '.ps1', '.md', '.txt')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                    new_content = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
                    if new_content != content:
                        with open(path, 'wb') as f:
                            f.write(new_content)
                        print(f"🛠️ Fixed formatting: {file}")
                except:
                    pass

if __name__ == "__main__":
    fix_line_endings()
