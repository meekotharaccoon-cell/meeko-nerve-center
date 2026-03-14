# Ralph Loops - Complete User Manual

## Welcome to Ralph Loops! 🌙

Ralph Loops is your personal AI coding army that works while you sleep. Using old laptops and free AI tools, you can have autonomous agents writing code overnight and wake up to completed tasks.

**Cost:** $10-20/month electricity only

---

## Table of Contents

1. [What is Ralph Loops?](#1-what-is-ralph-loops)
2. [Architecture Overview](#2-architecture-overview)
3. [Prerequisites](#3-prerequisites)
4. [Setting Up the Manager (Windows)](#4-setting-up-the-manager-windows)
5. [Setting Up an Agent (Linux)](#5-setting-up-an-agent-linux)
6. [Connecting Agent to Network](#6-connecting-agent-to-network)
7. [Creating Tasks](#7-creating-tasks)
8. [Running the System](#8-running-the-system)
9. [Morning Review](#9-morning-review)
10. [Adding More Agents](#10-adding-more-agents)
11. [Troubleshooting](#11-troubleshooting)
12. [Lessons Learned](#12-lessons-learned)
13. [Script Reference](#13-script-reference)
14. [Quick Reference Card](#14-quick-reference-card)

---

## 1. What is Ralph Loops?

Ralph Loops is an autonomous coding system where:

- **You** create task files describing what you want built
- **AI Agents** (Claude CLI primary, Gemini fallback) pick up tasks and write code
- **Git** coordinates everything - it's the "source of truth"
- **You wake up** to completed code, committed and ready for review

### Why "Ralph Loops"?

Because your agents loop through tasks all night, like a tireless employee named Ralph who never sleeps!

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              YOUR WINDOWS PC (Control)                   │
│                                                          │
│   - Creates tasks                                        │
│   - Triggers night runs                                  │
│   - Monitors status                                      │
│                                                          │
└───────────────────────────│──────────────────────────────┘
                            │
                       Tailscale VPN
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    │              ┌────────▼────────┐              │
    │              │      PC5        │              │
    │              │    Manager      │              │
    │              │ Reviews results │              │
    │              │ Creates fixes   │              │
    │              └────────┬────────┘              │
    │                       │ SSH                   │
    ▼           ▼           ▼           ▼          ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│  PC1  │ │  PC2  │ │  PC3  │ │  PC4  │ │  PC6  │
│Backend│ │Frontend│ │ Tests │ │Design │ │Utility│
│Claude │ │Claude │ │Claude │ │Claude │ │Claude │
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘
    │         │         │         │         │
    └─────────┴─────────┴─────────┴─────────┘
                        │
                        ▼
          ┌─────────────────────────────┐
          │     GitHub Repository       │
          │     (Source of Truth)       │
          │                             │
          │  tasks/pending/   ← New     │
          │  tasks/in-progress/         │
          │  tasks/done/      ← Done    │
          │  tasks/review/    ← Review  │
          │  results/         ← Reports │
          │  src/             ← Code    │
          └─────────────────────────────┘
```

### How It Works

1. You put task files in `tasks/pending/ROLE/` (backend, frontend, tests, design, utility)
2. Run `start-night.sh` before bed
3. Each agent picks tasks for its role
4. Agent moves task to `in-progress/`, executes with Claude (Gemini fallback)
5. Agent moves task to `done/`, creates result file
6. **Manager (pc5)** reviews results via Claude API, creates fix tasks if needed
7. Everything is committed and pushed to GitHub
8. In the morning, run `morning-review.sh` to see what happened

### Machine Roles

| Machine | Role | Description |
|---------|------|-------------|
| Windows | Control | Triggers runs, monitors status |
| pc1 | backend | Express.js microservices |
| pc2 | frontend | Vanilla HTML/CSS/JS pages |
| pc3 | tests | Bash test scripts with curl |
| pc4 | design | CSS, styling, visual design |
| pc5 | manager | Reviews results, creates fixes |
| pc6 | utility | Documentation, overflow work |

---

## 3. Prerequisites

### Hardware

| Component | Requirement |
|-----------|-------------|
| Manager PC | Windows 10/11 with internet |
| Agent PCs | Any old laptop (2GB+ RAM, any CPU) |
| Network | All machines on same network or internet |

### Software (We'll install these)

| Software | Purpose |
|----------|---------|
| Linux Mint | OS for agents (free, lightweight) |
| Tailscale | VPN to connect all machines (free) |
| Git | Version control |
| Node.js | Required for Gemini CLI |
| Claude CLI | Primary AI that writes the code |
| Gemini CLI | Fallback AI (free) |
| OpenSSH | Remote access |

### Accounts Needed

| Account | Purpose | Link |
|---------|---------|------|
| GitHub | Store code and coordinate | https://github.com |
| Google | For Tailscale and Gemini | Use existing |
| Google AI Studio | API key for higher limits | https://aistudio.google.com |

---

## 4. Setting Up the Manager (Windows)

### 4.1 Install OpenSSH Client

1. Open **Settings** → **Apps** → **Optional features**
2. Click **Add a feature**
3. Search for **OpenSSH Client** and install
4. Restart PowerShell after installation

**Test it:**
```powershell
C:\Windows\System32\OpenSSH\ssh.exe -V
```

### 4.2 Generate SSH Key

```powershell
C:\Windows\System32\OpenSSH\ssh-keygen.exe -t ed25519 -C "ralph-manager"
```

Press Enter three times (accept defaults, no passphrase).

**View your public key:**
```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

Save this key - you'll add it to each agent!

### 4.3 Install Tailscale

1. Download from https://tailscale.com/download/windows
2. Install and sign in with your Google account
3. Note your Windows Tailscale IP (100.x.x.x)

**Check status:**
```powershell
& "C:\Program Files\Tailscale\tailscale.exe" status
```

### 4.4 Create GitHub Repository

1. Go to https://github.com/new
2. Name: `ralph-loops-project` (or your choice)
3. Make it **Private**
4. **Don't** add README (keep it empty)
5. Click **Create repository**

---

## 5. Setting Up an Agent (Linux)

### 5.1 Install Linux Mint

1. Download Linux Mint from https://linuxmint.com/download.php
2. Create bootable USB with Rufus or balenaEtcher
3. Boot from USB (usually F12, F2, or ESC at startup)
4. If boot menu doesn't appear:
   - In BIOS, disable **Secure Boot**
   - Enable **Legacy Boot** or **CSM**
   - Set USB as first boot priority
5. Install Linux Mint (use default options)

### 5.2 Run Setup Commands

Open terminal on the new Linux machine and run each step:

**Step 1: Disable sleep/hibernate**
```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

**Step 2: Configure lid close (for laptops)**
```bash
sudo sed -i 's/#HandleLidSwitch=suspend/HandleLidSwitch=ignore/' /etc/systemd/logind.conf
sudo systemctl restart systemd-logind
```

**Step 3: Install packages**
```bash
sudo apt update
sudo apt install -y openssh-server git curl jq
```

**Step 4: Enable SSH**
```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

**Step 5: Configure Git identity**
```bash
git config --global user.name "ralph-ROLE"
git config --global user.email "ralph-ROLE@localhost"
```
(Replace ROLE with: backend, frontend, or tests)

**Step 6: Install Node.js**
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

**Step 7: Install Tailscale**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Complete authentication in browser.

**Step 8: Install Claude CLI (Primary AI)**
```bash
cd ~
npm install @anthropic-ai/claude-code
```

Test it:
```bash
~/node_modules/.bin/claude --version
```

**Step 9: Install Gemini CLI (Fallback)**
```bash
sudo npm install -g @google/gemini-cli
```

**Step 10: Configure Gemini API Key (for fallback)**

Get your API key from https://aistudio.google.com/app/apikey

```bash
echo 'GEMINI_API_KEY=YOUR_API_KEY_HERE' | sudo tee -a /etc/environment
```

Log out and back in, then test:
```bash
gemini -p "Say hello"
```

**Step 11: Generate SSH key for GitHub**
```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N '' -C "ralph-ROLE"
cat ~/.ssh/id_ed25519.pub
```

Add this key to GitHub: https://github.com/settings/keys

---

## 6. Connecting Agent to Network

### 6.1 Get Agent's Tailscale IP

On the agent:
```bash
tailscale ip
```

Note the IP (e.g., 100.x.x.1)

### 6.2 ⚠️ CRITICAL: Restart Windows Tailscale

**Every time you add a new agent**, restart Tailscale on Windows:

```powershell
& "C:\Program Files\Tailscale\tailscale.exe" down
& "C:\Program Files\Tailscale\tailscale.exe" up
```

**If you skip this step, Windows won't be able to connect to the new agent!**

### 6.3 Test Connection

From Windows:
```powershell
& "C:\Windows\System32\PING.EXE" AGENT_IP
```

Should get replies. If timeout, restart Tailscale on both machines.

### 6.4 Add Manager SSH Keys to Agent (Dual Key Setup)

You need TWO SSH keys on each agent:
1. **Windows control machine key** - for triggering runs
2. **pc5 manager key** - for manager to SSH to workers

From Windows (replace AGENT_IP and USER):
```powershell
# Add Windows key
type $env:USERPROFILE\.ssh\id_ed25519.pub | C:\Windows\System32\OpenSSH\ssh.exe USER@AGENT_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

Then add pc5's key:
```powershell
# Get pc5's public key and add to new agent
C:\Windows\System32\OpenSSH\ssh.exe pc5 "cat ~/.ssh/id_ed25519.pub" | C:\Windows\System32\OpenSSH\ssh.exe USER@AGENT_IP "cat >> ~/.ssh/authorized_keys"
```

Enter password when prompted (last time you'll need it!).

### 6.5 Test Passwordless SSH

```powershell
C:\Windows\System32\OpenSSH\ssh.exe USER@AGENT_IP "echo 'SSH works without password'"
```

Should work without password.

### 6.6 Add to SSH Config

```powershell
@"

Host pcN
    HostName AGENT_IP
    User USER
    IdentityFile ~/.ssh/id_ed25519
"@ | Add-Content -Path $env:USERPROFILE\.ssh\config
```

(Replace N with 1, 2, 3; AGENT_IP with actual IP; USER with username)

Test:
```powershell
C:\Windows\System32\OpenSSH\ssh.exe pcN "hostname"
```

### 6.7 Clone Repository on Agent

```powershell
C:\Windows\System32\OpenSSH\ssh.exe pcN "ssh -T git@github.com -o StrictHostKeyChecking=accept-new"
C:\Windows\System32\OpenSSH\ssh.exe pcN "git clone git@github.com:USERNAME/ralph-loops-project.git ~/project"
```

---

## 7. Creating Tasks

### 7.1 Task File Format

Tasks are markdown files in `tasks/pending/ROLE/`:

```markdown
# Task: Short Title

## Description
What you want built, in plain language.

## Requirements
- Specific requirement 1
- Specific requirement 2
- Server should bind to 0.0.0.0 (for network access)
- Enable CORS if frontend will access it

## Files to Create
- src/ROLE/path/to/file.js
- src/ROLE/path/to/other.js

## Validation
```bash
# Script to verify task completion
node --check src/path/to/file.js || exit 1
echo "PASS: Validation complete"
```

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

### 7.1.1 Auto-Validation (v11+)

**Tasks without a `## Validation` section will have one auto-generated** before execution. The worker automatically adds role-appropriate validation:

| Role | Auto-Validation |
|------|-----------------|
| backend | Check JS syntax with `node --check` |
| frontend/design | Verify HTML/CSS files exist |
| tests | Check scripts have bash shebang |
| utility | Verify files exist in src/ |

**Best Practice:** Include explicit validation for better coverage. Auto-validation is a fallback, not a replacement for specific checks.

### 7.2 Task Naming Convention

```
NNN-short-description.md
```

Examples:
- `001-create-auth-api.md`
- `002-add-validation.md`
- `003-user-dashboard.md`

Numbers ensure tasks run in order.

### 7.3 Example Backend Task

File: `tasks/pending/backend/001-hello-api.md`

```markdown
# Task: Create Hello API

## Description
Create a simple Express server with a hello endpoint.

## Requirements
- GET /api/hello returns { "message": "Hello from Ralph!" }
- Server runs on port 3001
- Bind to 0.0.0.0 (important - not localhost!)
- Enable CORS for frontend access

## Files to Create
- src/backend/hello/server.js
- src/backend/hello/package.json

## Validation
```bash
cd src/backend/hello && npm install --silent
node --check server.js || { echo "FAIL: Syntax error"; exit 1; }
timeout 5 node server.js &
sleep 2
curl -s http://localhost:3001/api/hello | grep -q "Hello" || { echo "FAIL: API not responding"; exit 1; }
pkill -f "node server.js"
echo "PASS: Hello API works"
```

## Success Criteria
- [ ] Server starts without errors
- [ ] Endpoint returns correct JSON
- [ ] Accessible from other machines
```

### 7.4 Example Frontend Task

File: `tasks/pending/frontend/001-hello-page.md`

```markdown
# Task: Create Hello Page

## Description
Create a simple HTML page that displays a greeting from the API.

## Requirements
- Fetch from http://100.x.x.1:3001/api/hello
- Display the message on the page
- Handle loading and error states
- Simple, clean styling

## Files to Create
- src/frontend/hello/index.html
- src/frontend/hello/style.css
- src/frontend/hello/app.js

## Success Criteria
- [ ] Page loads without errors
- [ ] Shows message from API
- [ ] Graceful error handling
```

### 7.5 Coordinating Frontend and Backend

For related tasks, create a **shared spec file** first:

File: `specs/api-contracts.md`

```markdown
# API Contract: User System

## Base URL
Backend: http://100.x.x.1:3001

## Endpoints

### POST /api/users
Request: { "name": "string", "email": "string" }
Response: { "id": "number", "name": "string", "email": "string" }

### GET /api/users/:id
Response: { "id": "number", "name": "string", "email": "string" }

## Field Names (IMPORTANT)
- Use "name" not "username"
- Use "email" not "mail"
- Use "id" not "userId"
```

Reference this spec in both backend and frontend task files!

---

## 8. Running the System

### 8.1 Before First Run

Verify everything is ready:

```powershell
# Check SSH works
C:\Windows\System32\OpenSSH\ssh.exe pc1 "hostname"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "hostname"
C:\Windows\System32\OpenSSH\ssh.exe pc3 "hostname"

# Check Gemini works
C:\Windows\System32\OpenSSH\ssh.exe pc1 "gemini -p 'Say hello'"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "gemini -p 'Say hello'"
C:\Windows\System32\OpenSSH\ssh.exe pc3 "gemini -p 'Say hello'"

# Check repo is cloned
C:\Windows\System32\OpenSSH\ssh.exe pc1 "ls ~/project"

# Make scripts executable
C:\Windows\System32\OpenSSH\ssh.exe pc1 "chmod +x ~/project/scripts/*.sh"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "chmod +x ~/project/scripts/*.sh"
C:\Windows\System32\OpenSSH\ssh.exe pc3 "chmod +x ~/project/scripts/*.sh"
```

### 8.2 Create Your Tasks

Put task files in appropriate folders:
- `tasks/pending/backend/` - Backend agent tasks
- `tasks/pending/frontend/` - Frontend agent tasks
- `tasks/pending/tests/` - Tests agent tasks

Commit and push:
```powershell
cd your-local-repo
git add -A
git commit -m "Add tasks for tonight"
git push
```

### 8.3 Sync All Agents

```powershell
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cd ~/project && git pull"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "cd ~/project && git pull"
C:\Windows\System32\OpenSSH\ssh.exe pc3 "cd ~/project && git pull"
```

### 8.4 Start Night Run

Start workers on all agents:

```powershell
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cd ~/project && git pull && nohup ./scripts/worker.sh backend > /dev/null 2>&1 &"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "cd ~/project && git pull && nohup ./scripts/worker.sh frontend > /dev/null 2>&1 &"
C:\Windows\System32\OpenSSH\ssh.exe pc3 "cd ~/project && git pull && nohup ./scripts/worker.sh tests > /dev/null 2>&1 &"
```

### 8.5 Verify Workers Are Running

```powershell
C:\Windows\System32\OpenSSH\ssh.exe pc1 "pgrep -f worker.sh && echo 'Running' || echo 'Stopped'"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "pgrep -f worker.sh && echo 'Running' || echo 'Stopped'"
C:\Windows\System32\OpenSSH\ssh.exe pc3 "pgrep -f worker.sh && echo 'Running' || echo 'Stopped'"
```

### 8.6 Go to Sleep! 😴

Workers will:
- Process tasks automatically
- Stop at 6:00 AM
- Handle up to 10 tasks each

---

## 9. Morning Review

### 9.1 Run Morning Review

```powershell
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cd ~/project && git pull && ./scripts/morning-review.sh"
```

This shows:
- Tasks completed per role
- Success/failure status
- Recent commits
- Worker status

### 9.2 Check Detailed Results

```powershell
# List result files
C:\Windows\System32\OpenSSH\ssh.exe pc1 "ls ~/project/results/"

# Read a specific result
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cat ~/project/results/001-task-name-result.md"
```

### 9.3 Check Logs

```powershell
# Recent log entries
C:\Windows\System32\OpenSSH\ssh.exe pc1 "tail -100 ~/project/logs/backend-*.log"

# Search for errors
C:\Windows\System32\OpenSSH\ssh.exe pc1 "grep -i error ~/project/logs/backend-*.log"
```

### 9.4 Review Generated Code

```powershell
# View recent commits
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cd ~/project && git log --oneline -10"

# See what files changed
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cd ~/project && git diff HEAD~5 HEAD --stat"

# View specific file
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cat ~/project/src/backend/hello/server.js"
```

### 9.5 Stop Workers (if still running)

```powershell
C:\Windows\System32\OpenSSH\ssh.exe pc1 "pkill -f worker.sh"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "pkill -f worker.sh"
C:\Windows\System32\OpenSSH\ssh.exe pc3 "pkill -f worker.sh"
```

---

## 10. Adding More Agents

### 10.1 Quick Checklist

| Step | Command/Action |
|------|----------------|
| 1. Install Linux Mint | Boot from USB, install |
| 2. Disable sleep | `sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target` |
| 3. Disable lid suspend | `sudo sed -i 's/#HandleLidSwitch=suspend/HandleLidSwitch=ignore/' /etc/systemd/logind.conf && sudo systemctl restart systemd-logind` |
| 4. Install packages | `sudo apt update && sudo apt install -y openssh-server git curl jq` |
| 5. Enable SSH | `sudo systemctl enable ssh && sudo systemctl start ssh` |
| 6. Install Node.js | `curl -fsSL https://deb.nodesource.com/setup_22.x \| sudo -E bash - && sudo apt install -y nodejs` |
| 7. Install Tailscale | `curl -fsSL https://tailscale.com/install.sh \| sh && sudo tailscale up` |
| 8. **RESTART WINDOWS TAILSCALE** | `& "C:\Program Files\Tailscale\tailscale.exe" down` then `up` |
| 9. Install Gemini | `sudo npm install -g @google/gemini-cli` |
| 10. Set API key | `echo 'GEMINI_API_KEY=KEY' \| sudo tee -a /etc/environment` |
| 11. Add manager SSH key | From Windows, copy key to agent |
| 12. Add to SSH config | Add Host entry on Windows |
| 13. Generate GitHub key | `ssh-keygen -t ed25519` then add to GitHub |
| 14. Clone repo | `git clone git@github.com:USER/REPO.git ~/project` |
| 15. Update config.json | Add new agent entry |

### 10.2 Update config.json

```json
{
  "agents": {
    "pc1": { "name": "ralph-backend", "role": "backend", "ip": "100.x.x.1" },
    "pc2": { "name": "ralph-frontend", "role": "frontend", "ip": "100.x.x.2" },
    "pc3": { "name": "ralph-tests", "role": "tests", "ip": "100.x.x.3" },
    "pc4": { "name": "ralph-newrole", "role": "newrole", "ip": "100.x.x.x" }
  }
}
```

---

## 11. Troubleshooting

### SSH Connection Timeout

**Symptom:** `ssh: connect to host ... Connection timed out`

**Fix:**
1. Restart Tailscale on Windows:
   ```powershell
   & "C:\Program Files\Tailscale\tailscale.exe" down
   & "C:\Program Files\Tailscale\tailscale.exe" up
   ```

2. Restart Tailscale on Linux:
   ```bash
   sudo systemctl restart tailscaled
   ```

### Gemini Auth Error

**Symptom:** "Please set an Auth method"

**Fix:** Set API key in `/etc/environment`:
```bash
echo 'GEMINI_API_KEY=YOUR_KEY' | sudo tee -a /etc/environment
```
Then log out and back in.

**⚠️ NEVER delete oauth_creds.json** - quota is tied to Google account!

### Gemini Hangs or Times Out

**Possible causes:**
- Quota exhausted (wait for reset)
- Network issue

**Test:**
```bash
GEMINI_API_KEY=YOUR_KEY gemini -p "test"
```

### Git Push Conflicts

**Symptom:** Push rejected, remote has changes

**Fix:** safe-push.sh handles this automatically with retries. If stuck:
```bash
git pull --rebase origin main
git push origin main
```

### Laptop Suspends When Lid Closed

**Fix:**
```bash
sudo sed -i 's/#HandleLidSwitch=suspend/HandleLidSwitch=ignore/' /etc/systemd/logind.conf
sudo systemctl restart systemd-logind
```

**Verify:** `grep HandleLidSwitch /etc/systemd/logind.conf` → Should show `ignore`

### Worker Creates Files in Wrong Directory

**Cause:** worker.sh running Gemini from wrong directory

**Fix:** Ensure worker.sh has `cd "$REPO_DIR"` (not `cd "$REPO_DIR/src"`)

---

## 12. Lessons Learned

### Gemini CLI
- ✅ Use API key from Google AI Studio (not OAuth) for automation
- ✅ Set key in `/etc/environment` for non-interactive SSH
- ❌ Never delete `oauth_creds.json` - quota is per account
- ✅ Add pre-flight check before processing tasks

### SSH & Networking
- ✅ **Always restart Windows Tailscale** after adding new agent
- ✅ Use full paths: `C:\Windows\System32\OpenSSH\ssh.exe`
- ✅ SSH config aliases save time and errors
- ✅ Test connectivity from both directions

### Git Coordination
- ✅ Separate folders per role prevent conflicts
- ✅ safe-push.sh with retries handles race conditions
- ✅ Always pull before starting work

### Task Design
- ✅ Be specific - vague tasks get vague results
- ✅ Always include "bind to 0.0.0.0" for servers
- ✅ Always include "enable CORS" for APIs
- ✅ Specify exact file paths
- ✅ Create shared API specs for frontend/backend coordination
- ✅ Use consistent field names (document them!)

### Scripts
- ❌ No exclamation marks in echo (Bash history expansion)
- ✅ Redirect git output to prevent variable pollution
- ✅ Use Tailscale IPs directly (not hostnames)
- ✅ Add timeouts to prevent hanging

---

## 13. Script Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `worker.sh` | Main agent loop (v11: auto-validation) | `./worker.sh ROLE` |
| `safe-push.sh` | Git push with retries | Called by worker.sh |
| `start-night.sh` | Start all workers + manager | `./start-night.sh` |
| `morning-review.sh` | Show overnight summary + metrics | `./morning-review.sh` |
| `status.sh` | Real-time status dashboard | `./status.sh` |
| `generate-tasks.sh` | AI-powered task generation | `./generate-tasks.sh "idea"` |
| `add-validation.sh` | Add validation to tasks (optional*) | `./add-validation.sh` |
| `manager-loop.sh` | Manager review loop | Runs on pc5 |
| `telegram-bot.js` | Remote monitoring bot | `node telegram-bot.js` |

*Since worker v11, validation is auto-added if missing. Manual script useful for bulk updates.

---

## 14. Quick Reference Card

### Your Machines

| Alias | IP | Role |
|-------|-----|------|
| pc1 | 100.x.x.1 | backend |
| pc2 | 100.x.x.2 | frontend |
| pc3 | 100.x.x.3 | tests |
| pc4 | 100.x.x.4 | design |
| pc5 | 100.x.x.5 | manager |
| pc6 | 100.x.x.6 | utility |

### Daily Commands

```powershell
# Start night run
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cd ~/project && git pull && nohup ./scripts/worker.sh backend &"
C:\Windows\System32\OpenSSH\ssh.exe pc2 "cd ~/project && git pull && nohup ./scripts/worker.sh frontend &"
C:\Windows\System32\OpenSSH\ssh.exe pc3 "cd ~/project && git pull && nohup ./scripts/worker.sh tests &"

# Check status
C:\Windows\System32\OpenSSH\ssh.exe pc1 "pgrep -f worker.sh && echo Running || echo Stopped"

# View logs
C:\Windows\System32\OpenSSH\ssh.exe pc1 "tail -50 ~/project/logs/backend-*.log"

# Morning review
C:\Windows\System32\OpenSSH\ssh.exe pc1 "cd ~/project && git pull && ./scripts/morning-review.sh"

# Stop workers
C:\Windows\System32\OpenSSH\ssh.exe pc1 "pkill -f worker.sh"
```

### Folder Structure

```
~/project/
├── tasks/
│   ├── pending/ROLE/     ← New tasks
│   ├── in-progress/ROLE/ ← Being worked
│   └── done/ROLE/        ← Completed
├── results/              ← Result reports
├── src/                  ← Generated code
├── scripts/              ← Automation
├── specs/                ← Shared API contracts
└── .ralph/config.json    ← Configuration
```

### API Key Setup

Get your own Gemini API key from: https://aistudio.google.com/app/apikey

Then set it in `/etc/environment` on each agent machine:
```
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

---

## Congratulations! 🎉

You now have your own AI coding army. Create tasks, start the night run, and wake up to code!

**Happy coding while sleeping!** 🌙

---

*Ralph Loops v4.2 - 6-machine architecture with Claude primary, Gemini fallback*
