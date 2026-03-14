import json

print("?? CONFIG.JSON EDITOR")
print("="*50)

# Current content
try:
    with open("config.json", "r") as f:
        current = json.load(f)
except:
    current = {"github": {"token": ""}, "twitter": {"api_key": "", "api_secret": "", "access_token": "", "access_secret": "", "bearer_token": ""}}

print("Current keys (masked):")
for platform, values in current.items():
    print(f"\n{platform.upper()}:")
    for key, value in values.items():
        masked = "*" * min(10, len(value)) if value else "[EMPTY]"
        print(f"  {key}: {masked}")

print("\nTo edit, add your keys to config.json manually.")
print("The file structure is valid JSON.")
