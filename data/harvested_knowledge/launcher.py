# launcher.py - Simple Python launcher (no batch files needed)
import os, sys, subprocess, time

print("SolarPunk Launcher")
print("1. Start agent")
print("2. Push to GitHub")
print("3. Exit")

choice = input("Select: ")

if choice == "1":
    print("Starting agent...")
    subprocess.run([sys.executable, "ultimate_agent.py"])
elif choice == "2":
    print("Pushing to GitHub...")
    os.chdir(r"C:\Users\carol\SolarPunk")
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"Update {time.strftime('%Y-%m-%d %H:%M')}"])
    subprocess.run(["git", "push", "origin", "master"])
    print("✅ Pushed! Cloudflare will update in 30s")
    print("Check: https://solarpunkagent.pages.dev")
else:
    print("Goodbye!")
