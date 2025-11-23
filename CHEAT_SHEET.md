# GitVisionCLI - Command Cheat Sheet

## 🚀 Quick Reference

### Essential Commands
```bash
gitvision              # Launch GitVision
:banner                # Show quick commands
:sheet                 # Full command list
:tree                  # File browser
exit                   # Quit GitVision
```

---

## 📁 File Operations

### Create Files
```
create a file called NAME with CONTENT
create a file called app.py with print("hello")
```

### Multiline Files
```
:ml
create a file called app.py with
def main():
    print("hello")
:end
```

### File Management
```
read file NAME              # View file content
delete file NAME            # Remove file
rename OLD to NEW           # Rename file
```

---

## ✏️ Line Editing

### Prerequisites
```
:edit FILENAME              # Open file in editor
```

### Delete Lines
```
remove line 1               # Delete line 1
delete line 5               # Delete line 5
delete lines 1-3            # Delete range
```

### Add Lines
```
add line 1 with CONTENT     # Insert before line 1
insert line 5 with TEXT     # Insert before line 5
```

### Edit Lines
```
edit line 1 with NEW        # Replace line 1
replace line 2 with TEXT    # Replace line 2
update line 3 with DATA     # Replace line 3
```

---

## 🌳 Git Commands

### Initialize
```
git init                    # Initialize repo
```

### Staging
```
git add FILE                # Stage file
git add .                   # Stage all files
```

### Committing
```
git commit "MESSAGE"        # Commit with message
```

### Status & History
```
git status                  # Check status
git log                     # View commits
:git-graph                  # Visual graph
```

### Branching
```
git branch NAME             # Create branch
git checkout NAME           # Switch branch
git merge NAME              # Merge branch
```

### Remote
```
git push                    # Push to remote
git pull                    # Pull from remote
git push -u origin main     # First push
```

---

## 🐙 GitHub Integration

### Setup
```bash
export GITHUB_TOKEN="ghp_..."
gitvision
```

### Repository
```
create github repo NAME --private     # Create private repo
create github repo NAME --public      # Create public repo
```

### Issues & PRs
```
create github issue "TITLE" --body "TEXT"
create github pr "TITLE" --head BRANCH --base main
```

---

## 🎨 UI Panels

### Panel Commands
```
:banner                     # Quick command list
:sheet                      # Full command sheet
:tree                       # File browser
:git-graph                  # Commit graph
:edit FILENAME              # File editor
```

---

## 🤖 AI Commands

### Natural Language
```
explain the file app.py
analyze this code
how does this function work?
find bugs in this code
create a test file for main.py
refactor this function
add error handling
```

### Model Management
```
:models                     # List available models
:set-ai MODEL               # Switch model

# Examples:
:set-ai openai/gpt-4
:set-ai anthropic/claude-3.5-sonnet
:set-ai openai/gpt-4-turbo
```

---

## 🔍 Search & Analysis

### Search
```
search for "TERM" in project
search for "def" in file.py
```

### Analysis
```
analyze the file app.py
explain how git works
```

---

## ⚙️ Workspace

### Navigation
```
cd PATH                     # Change directory
pwd                         # Print working dir
```

### Info
```
stats                       # Workspace stats
clear                       # Clear console
```

---

## 💡 Pro Tips

### Multiline Input
Always use `:ml` for multi-line content:
```
:ml
create a file called app.py with
def main():
    print("hello")
    return 0
:end
```

### Context-Aware Editing
When file is open in `:edit`, you can:
- Omit filename: `remove line 1` (uses active file)
- Chain commands: Multiple edits in sequence

### Natural Language
Be conversational:
- ❌ "execute action delete line 1"
- ✅ "remove line 1"
- ✅ "delete that line"
- ✅ "add a comment at the top"

### Git Workflow
```
:edit app.py
# make changes
git add app.py
git commit "Update app"
git push
```

### Panel Shortcuts
```
:b      # :banner
:s      # :sheet
:t      # :tree
:g      # :git-graph
```

---

## 🎯 Common Workflows

### Create New Project
```
gitvision
git init
:ml
create a file called README.md with
# My Project
Description here
:end
git add .
git commit "Initial commit"
create github repo my-project --private
git push -u origin main
```

### Edit Existing File
```
:edit app.py
remove line 1
add line 1 with # -*- coding: utf-8 -*-
edit line 5 with     print("updated")
git add app.py
git commit "Update app"
git push
```

### Feature Branch Workflow
```
git branch feature-x
git checkout feature-x
:edit app.py
# make changes
git add app.py
git commit "Add feature X"
git push origin feature-x
create github pr "Add feature X"
```

---

## 🐛 Troubleshooting

### "Please specify file..."
**Fix:** Open file first with `:edit FILENAME`

### Duplicate Panels
**Fix:** Already fixed! Update to latest version

### Multiline Not Working
**Fix:** Use `:ml` before content, end with `:end`

### GitHub Token
**Fix:** `export GITHUB_TOKEN="ghp_xxx"` before launching

---

## 📚 More Help

```
:sheet          # Full command reference
:help           # Help text
```

---

**Made with GitVisionCLI 🚀**
