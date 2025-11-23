# GitVisionCLI - Complete Testing Guide

## 🎯 Quick Start

```bash
cd ~/Desktop
mkdir gitvision-test
cd gitvision-test
gitvision
```

---

## 📝 Part 1: File Operations

### Test File Creation
```
create a file called hello.py with print("Hello World!")
```
✅ File created with content

### Test Multiline File Creation
```
:ml
create a file called app.py with
def main():
    print("GitVision")
    return 0

if __name__ == "__main__":
    main()
:end
```
✅ File created with all lines preserved

### Test File Reading
```
read file hello.py
```
✅ Shows file content

### Test File Deletion
```
delete file hello.py
```
✅ File removed

### Test File Rename
```
rename app.py to main.py
```
✅ File renamed, Git tracks change

---

## ✏️ Part 2: Line Editing (CORE FEATURES)

### Open File in Editor
```
:edit main.py
```
✅ Right panel shows editor with numbered lines

### Test Delete Line
```
remove line 1
delete line 2
```
✅ Executes immediately, NO "Please specify..." questions

### Test Add Line
```
add line 1 with # This is a comment
insert line 2 with x = 42
```
✅ Lines inserted at specified positions

### Test Edit/Replace Line
```
edit line 1 with # Updated comment
replace line 2 with y = 100
update line 3 with print(y)
```
✅ Lines replaced with new content

### Test Line Ranges
```
delete lines 1-3
```
✅ Multiple lines deleted

---

## 🌳 Part 3: Git Operations

### Initialize Git
```
git init
```
✅ `.git` folder created

### Check Status
```
git status
```
✅ Shows untracked files

### Stage Files
```
git add main.py
git add .
```
✅ Files staged

### Commit
```
git commit "Initial commit"
```
✅ Commit created with message

### View Log
```
git log
```
✅ Shows commit history

### Visual Git Graph
```
:git-graph
```
✅ Visual commit tree displayed

### Branching
```
git branch feature-test
git checkout feature-test
```
✅ Branch created and switched

### Merging
```
git checkout main
git merge feature-test
```
✅ Changes merged

---

## 🐙 Part 4: GitHub Integration

### Setup Token
```
export GITHUB_TOKEN="your_token_here"
gitvision
```

### Create Private Repo
```
create github repo gitvision-test --private
```
✅ Repo created on GitHub

### Push to GitHub
```
git push -u origin main
```
✅ Code uploaded

### Pull from GitHub
```
git pull
```
✅ Changes downloaded

### Create Issue
```
create github issue "Test" --body "Testing GitVision"
```
✅ Issue created

### Create Pull Request
```
create github pr "Feature" --head feature-test --base main
```
✅ PR created

---

## 🎨 Part 5: UI Panels

### Banner Panel
```
:banner
```
✅ Shows logo + compact command list

### Command Sheet
```
:sheet
```
✅ Full command reference with shortcuts

### File Tree
```
:tree
```
✅ Directory browser

### Switch Between Panels
```
:banner
:tree
:sheet
:banner
```
✅ NO duplicate panels (clears properly)

---

## 🤖 Part 6: AI Features

### Natural Language Queries
```
explain the file main.py
analyze this code
how does this function work?
```
✅ AI provides contextual responses

### Code Generation
```
create a test file for main.py
add error handling to this function
refactor this code
```
✅ AI generates appropriate code

### Model Switching
```
:models
:set-ai anthropic/claude-3.5-sonnet
```
✅ Switches AI model

---

## 🔍 Part 7: Search & Analysis

### Search Project
```
search for "print" in project
search for "def" in main.py
```
✅ Finds occurrences with line numbers

### Code Analysis
```
analyze the file main.py
explain how this works
find bugs in this code
```
✅ AI provides detailed analysis

---

## ⚙️ Part 8: Workspace Commands

### Statistics
```
stats
```
✅ Shows file count, Git status, branch

### Clear Console
```
clear
```
✅ AI console cleared

### Change Directory
```
cd ../other-project
pwd
```
✅ Working directory changed

### Exit
```
exit
quit
```
✅ Clean exit

---

## 🧪 Part 9: Complete Workflow Test

```bash
# 1. Setup
gitvision
git init

# 2. Create files with multiline
:ml
create a file called src/app.py with
#!/usr/bin/env python3

def hello(name):
    return f"Hello, {name}!"

def main():
    print(hello("World"))

if __name__ == "__main__":
    main()
:end

# 3. Edit file
:edit src/app.py
add line 1 with # -*- coding: utf-8 -*-
edit line 8 with     print(hello("GitVision"))

# 4. Git workflow
git add .
git commit "Add main app"
git log
:git-graph

# 5. GitHub
create github repo my-project --private
git push -u origin main

# 6. Development cycle
git branch feature
git checkout feature
:edit src/app.py
add line 10 with     print("New feature!")
git add src/app.py
git commit "Add feature"
git push origin feature
create github pr "New feature"

# 7. Verify
stats
:tree
git status
```

---

## ✅ Success Criteria

All these must work perfectly:

**File Operations:**
- [x] Create files
- [x] Multiline file creation (`:ml`)
- [x] Read files
- [x] Delete files
- [x] Rename files

**Line Editing:**
- [x] `remove line X` - NO clarification
- [x] `add line X with content`
- [x] `edit line X with content`
- [x] `replace line X with content`
- [x] `delete lines X-Y`

**Git:**
- [x] init, add, commit, log
- [x] branch, checkout, merge
- [x] Visual git graph

**GitHub:**
- [x] Create repo
- [x] Push/pull
- [x] Issues, PRs

**UI:**
- [x] No duplicate panels
- [x] Banner shows logo
- [x] Panels switch cleanly

**AI:**
- [x] Natural language understanding
- [x] Context-aware responses
- [x] Model switching

---

## 🐛 Known Issues

None! All major bugs fixed:
✅ Line editing works instantly
✅ No duplicate panels
✅ Banner logo visible
✅ Files have content
✅ Multiline input supported

---

**Test Status: READY FOR PRODUCTION** 🚀
