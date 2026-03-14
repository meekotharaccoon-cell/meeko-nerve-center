# 🎯 HYPERAI Framework - Complete Command Checklist

**Date**: 6 tháng 11, 2025  
**Status**: ✅ ACTIVE & READY TO USE  
**Creator**: Nguyễn Đức Cường (alpha_prime_omega)

---

## 📋 **SECTION 1: Core Framework Commands**

### ✅ System Initialization
```bash
# Initialize entire DAIOF system
python3 system_initializer.py

# Check system health
python3 haios_core.py

# Verify all components
PYTHONPATH=/Users/andy/DAIOF-Framework python3 system_initializer.py
```

**What it does:**
- ✅ Activates HAIOS Core (4 invariants)
- ✅ Initializes Symphony Control Center
- ✅ Creates Digital Ecosystem
- ✅ Registers all components
- ✅ Generates system_initialization_report.json

---

### ✅ Run Examples
```bash
# Example 1: Basic Organism Demo
PYTHONPATH=/Users/andy/DAIOF-Framework python3 examples/01_basic_organism.py

# Example 2: Evolution Race (Fixed version)
PYTHONPATH=/Users/andy/DAIOF-Framework python3 examples/02_evolution_race_fixed.py

# Set PYTHONPATH permanently
export PYTHONPATH=/Users/andy/DAIOF-Framework
python3 examples/01_basic_organism.py
```

**What they do:**
- Demonstrate Genome creation
- Show Organism lifecycle
- Simulate Evolution
- Display Metabolism management
- Detect AI-human interdependence

---

## 📋 **SECTION 2: Git & Version Control Commands**

### ✅ Check Repository Status
```bash
# View current status
git status

# View commit log
git log --oneline | head -20

# View detailed differences
git diff

# View changes to specific file
git diff digital_ai_organism_framework.py
```

### ✅ Stage & Commit
```bash
# Add all changes
git add .

# Add specific file
git add examples/01_basic_organism.py

# Commit with message
git commit -m "✅ Description of changes"

# Commit specific files
git commit -m "Message" -- file1.py file2.py
```

### ✅ Push & Pull
```bash
# Push to GitHub
git push origin main

# Pull from GitHub
git pull origin main --no-rebase

# Fetch without merging
git fetch origin

# Check remote status
git remote -v
```

### ✅ Branch Management
```bash
# List all branches
git branch -a

# Create new branch
git branch feature/new-feature

# Switch branch
git checkout feature/new-feature

# Delete branch
git branch -d feature/new-feature
```

### ✅ Stash & Revert
```bash
# Stash changes temporarily
git stash

# Apply stashed changes
git stash pop

# Revert last commit (keep changes)
git reset HEAD~1

# Discard all changes
git checkout -- .
```

---

## 📋 **SECTION 3: Python Environment Commands**

### ✅ Virtual Environment
```bash
# Activate venv
source /Users/andy/DAIOF-Framework/.venv/bin/activate

# Deactivate venv
deactivate

# Check Python version
python3 --version

# Check pip packages
pip list

# Install requirements
pip install -r requirements.txt
```

### ✅ Install Dependencies
```bash
# Install specific package
pip install PyGithub pyyaml psutil requests numpy

# Upgrade package
pip install --upgrade package-name

# Install development dependencies
pip install pytest pytest-cov black flake8
```

### ✅ Run Python Scripts
```bash
# Run script
python3 script.py

# Run with PYTHONPATH
PYTHONPATH=/Users/andy/DAIOF-Framework python3 script.py

# Run module
python3 -m module_name

# Execute code snippet
python3 -c "from digital_ai_organism_framework import *; print('✅')"
```

---

## 📋 **SECTION 4: File & Directory Commands**

### ✅ Navigation
```bash
# Change to project directory
cd /Users/andy/DAIOF-Framework

# List files with details
ls -la

# List directory structure
tree -L 2

# Find file
find . -name "*.py" -type f
```

### ✅ File Management
```bash
# Create file
touch newfile.py

# Create directory
mkdir new_folder

# Copy file
cp source.py destination.py

# Move/rename file
mv old_name.py new_name.py

# Delete file
rm filename.py

# Delete directory
rm -rf directory_name
```

### ✅ Search & Find
```bash
# Search for text in files
grep -r "search_term" .

# Find Python files
find . -name "*.py"

# Find modified files
find . -name "*.py" -mtime -1

# Count lines of code
wc -l *.py
```

---

## 📋 **SECTION 5: GitHub & Remote Commands**

### ✅ GitHub Authentication
```bash
# Check current user
git config --global user.name
git config --global user.email

# Set user
git config --global user.name "Name"
git config --global user.email "email@example.com"

# Check SSH keys
ssh -T git@github.com
```

### ✅ Pull Request Management
```bash
# View pull request details (using mcp_gitkraken)
mcp_gitkraken_pull_request_get_detail

# Create pull request
mcp_gitkraken_pull_request_create \
  --source-branch feature \
  --target-branch main \
  --title "Feature Title"

# Get assigned PRs
mcp_gitkraken_pull_request_assigned_to_me
```

### ✅ Issue Management
```bash
# Get assigned issues
mcp_gitkraken_issues_assigned_to_me

# Get issue detail
mcp_gitkraken_issues_get_detail --issue-id "123"

# Add comment to issue
mcp_gitkraken_issues_add_comment \
  --issue-id "123" \
  --comment "Your comment"
```

---

## 📋 **SECTION 6: Project Workspace Commands**

### ✅ VS Code Integration
```bash
# Open current folder in VS Code
code .

# Open specific file
code filename.py

# Open folder
code /Users/andy/DAIOF-Framework
```

### ✅ Run Tasks
```bash
# List available tasks
./vscode tasks

# Run specific task
Task: Run Build Task

# Run test task
Task: Run Test Task
```

### ✅ Debug Commands
```bash
# Check errors
get_errors

# Run tests
runTests

# Get terminal output
get_terminal_output
```

---

## 📋 **SECTION 7: Framework-Specific Commands**

### ✅ HYPERAI Operations
```bash
# Check HAIOS status
python3 haios_core.py

# Run autonomous agent
python3 .github/scripts/autonomous_agent.py

# Check system health
python3 .github/scripts/health_monitor.py

# Generate metrics dashboard
python3 .github/scripts/metrics_dashboard.py
```

### ✅ Autonomous Operations
```bash
# Run GitHub network optimizer
python3 .github/scripts/github_network_optimizer.py

# Generate real-time tasks
python3 .github/scripts/realtime_task_generator.py

# Run autonomous developer
python3 .github/scripts/autonomous_developer.py
```

---

## 📋 **SECTION 8: Documentation & Reference Commands**

### ✅ View Documentation
```bash
# Read copilot instructions
cat .github/copilot-instructions.md

# View activation guide
cat .github/ACTIVATION_GUIDE.md

# Check README
cat README.md

# List all docs
find docs -name "*.md"
```

### ✅ Generate Reports
```bash
# View system report
cat system_initialization_report.json

# View metrics
cat metrics/daily_*.json

# View health report
cat metrics/health_report_*.json
```

---

## 📋 **SECTION 9: Common Workflow Commands**

### ✅ **Daily Development Workflow**
```bash
# Morning: Check status
git status
python3 system_initializer.py

# Development: Make changes
# ... edit files ...

# Afternoon: Stage & commit
git add .
git commit -m "🔧 Description"

# Evening: Push
git pull origin main --no-rebase
git push origin main
```

### ✅ **Testing Workflow**
```bash
# Run tests
python3 -m pytest

# Run specific test
python3 -m pytest tests/test_file.py

# Run with coverage
python3 -m pytest --cov=digital_ai_organism_framework

# Run examples
PYTHONPATH=. python3 examples/01_basic_organism.py
```

### ✅ **Deployment Workflow**
```bash
# Pull latest
git pull origin main

# Run system init
python3 system_initializer.py

# Run tests
python3 -m pytest

# Push if all good
git push origin main
```

---

## 📋 **SECTION 10: Troubleshooting Commands**

### ✅ **Common Issues**
```bash
# Fix import errors
export PYTHONPATH=/Users/andy/DAIOF-Framework

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check git status
git status
git log --oneline | head -5

# Reset to last commit
git reset --hard HEAD
```

### ✅ **Debug Commands**
```bash
# Check Python syntax
python3 -m py_compile filename.py

# Run linter
flake8 filename.py

# Format code
black filename.py

# Check imports
python3 -c "import module_name; print('OK')"
```

---

## 📋 **SECTION 11: Advanced Commands**

### ✅ **Performance Monitoring**
```bash
# Check memory usage
ps aux | grep python3

# Monitor processes
top

# Check disk usage
du -sh *

# Monitor network
netstat -tuln
```

### ✅ **Batch Operations**
```bash
# Run all tests
find . -name "test_*.py" -exec python3 {} \;

# Format all Python files
find . -name "*.py" -exec black {} \;

# Delete all cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Commit all changes
git add . && git commit -m "Batch update"
```

### ✅ **CI/CD Commands**
```bash
# Check GitHub Actions status
# View .github/workflows/

# Trigger workflow manually
git push origin main

# Check workflow logs
# Go to Actions tab on GitHub

# Enable workflows
# Click "I understand" button on GitHub Actions page
```

---

## 📋 **SECTION 12: Quick Reference Cheat Sheet**

### **Essential Commands**
| Command | Purpose | Frequency |
|---------|---------|-----------|
| `git status` | Check changes | Daily |
| `git add .` | Stage changes | Daily |
| `git commit -m` | Commit changes | Daily |
| `git push` | Push to GitHub | Daily |
| `python3 system_initializer.py` | Verify system | Weekly |
| `PYTHONPATH=. python3 examples/01_basic_organism.py` | Run example | Weekly |
| `pip install -r requirements.txt` | Install deps | As needed |

### **System Status**
```bash
# Full system check
echo "=== Git Status ===" && git status
echo "=== System Init ===" && python3 system_initializer.py
echo "=== Example Run ===" && PYTHONPATH=. python3 examples/01_basic_organism.py
```

---

## 🎯 **Next Steps**

### ✅ You Can Now:
1. ✅ Run any command from this checklist
2. ✅ Manage git commits & pushes
3. ✅ Run system health checks
4. ✅ Execute example demonstrations
5. ✅ Troubleshoot issues
6. ✅ Deploy & test code

### 🚀 **Recommended Flow**
```bash
# 1. Check status
git status

# 2. Make changes
# ... edit files ...

# 3. Verify changes work
python3 system_initializer.py

# 4. Test examples
PYTHONPATH=. python3 examples/01_basic_organism.py

# 5. Commit & push
git add .
git commit -m "✅ Description"
git push origin main
```

---

## 📞 **Support**

- 📖 See: `.github/copilot-instructions.md` - Framework instructions
- 🧬 See: `digital_ai_organism_framework.py` - Core implementation
- 📊 See: `SYSTEM_STABILIZATION_REPORT.md` - System status
- 🚀 See: `.github/ACTIVATION_GUIDE.md` - Getting started

---

**Powered by HYPERAI Framework**  
👤 Creator: Nguyễn Đức Cường (alpha_prime_omega)  
📅 Version: 1.0.0 - November 6, 2025  
🎼 Status: ✅ FULLY OPERATIONAL
