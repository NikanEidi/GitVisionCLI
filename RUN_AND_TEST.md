# 🚀 How to Run & Test GitVisionCLI

## 📦 **Installation**

### **Step 1: Install Dependencies**

```bash
# Navigate to project directory
cd /Users/kuroko/Desktop/APPs/GitVisionCLI

# Install all dependencies
pip install -e .

# This will install:
# - colorama, rich, requests, markdown-it-py
# - openai, anthropic, google-generativeai
# - And all other required packages
```

### **Step 2: Development Mode (Recommended for Testing)**

```bash
# Already done with pip install -e .
# This installs in "editable" mode so changes are immediate

# Or use pipx (isolated environment)
pipx install -e .
```

### **Option 2: Direct Python Execution (After Dependencies)**

```bash
# First install dependencies
pip install -e .

# Then run directly
cd /Users/kuroko/Desktop/APPs/GitVisionCLI
python3 -m gitvisioncli.cli
```

### **Option 3: Use Quick Start Script**

```bash
# Make executable (first time only)
chmod +x QUICK_START.sh

# Run it
./QUICK_START.sh
```

### **Set API Key (Required)**

```bash
# Choose at least one AI provider
export OPENAI_API_KEY="sk-..."              # For GPT-4/GPT-4o-mini
export ANTHROPIC_API_KEY="sk-ant-..."       # For Claude
export GOOGLE_API_KEY="..."                 # For Gemini

# Optional: GitHub integration
export GITHUB_TOKEN="ghp_..."
```

---

## 🎮 **How to Run**

### **Basic Launch**

```bash
gitvision
```

### **With Options**

```bash
gitvision --fast              # Skip startup animation
gitvision --dry-run           # Test without making changes
gitvision --model gpt-4o-mini # Use specific model
```

### **Subcommands**

```bash
gitvision doctor              # System health check
gitvision scan .              # Scan current directory
gitvision demo                # Run automated demo
gitvision init myproject      # Initialize new project
```

---

## ✅ **Complete Testing Checklist**

### **1. Basic UI & Navigation** ✅

```bash
# Launch GitVision
gitvision

# Test panel commands
:banner          # Should show banner with logo
:sheet           # Should show complete command sheet
:tree            # Should show file tree
:close           # Should return to banner
```

**Expected Results:**
- ✅ Dual-panel UI appears (AI Console + Workspace)
- ✅ All panels render correctly
- ✅ Colors are consistent (neon purple, cyan, magenta)
- ✅ No errors in console

---

### **2. File Operations (Natural Language)** ✅

```bash
# Create file
create file test.txt with Hello World

# Read file
read file test.txt

# Rename file
rename test.txt to hello.txt

# Move file
move hello.txt to subfolder

# Copy file
copy hello.txt to hello_backup.txt

# Delete file
delete file hello_backup.txt
```

**Expected Results:**
- ✅ All operations execute immediately (no AI call)
- ✅ No clarification questions asked
- ✅ Files created/deleted correctly
- ✅ Success messages appear

---

### **3. Folder Operations** ✅

```bash
# Create folder
create folder demo

# Create folder and go to it
create folder test and go to it

# Verify you're in the folder
pwd

# Delete folder
cd ..
delete folder test
```

**Expected Results:**
- ✅ Folder created successfully
- ✅ "create folder X and go to it" works (creates + cd)
- ✅ No "Path is not a file" errors
- ✅ Directory changes correctly

---

### **4. Line Editing (With File Open)** ✅

```bash
# Create a test file
create file app.py with
print("Line 1")
print("Line 2")
print("Line 3")

# Open in editor
:edit app.py

# Test line operations
remove line 1
delete line 2
replace line 1 with print("Updated")
add print("New line") at line 2
add print("End") at bottom
```

**Expected Results:**
- ✅ Editor opens file correctly
- ✅ Line numbers displayed
- ✅ All line operations work instantly
- ✅ Grammar fixes work (line1→line 1, rm 5→remove line 5)
- ✅ No questions asked when file is open

---

### **5. Git Operations** ✅

```bash
# Initialize repo
git init

# Stage files
git add .

# Commit
git commit "Initial commit"

# Create branch
git branch feature

# Switch branch
git checkout feature

# View graph
:git-graph
# OR
git graph
```

**Expected Results:**
- ✅ Git operations work via natural language
- ✅ :git-graph command opens graph panel
- ✅ "git graph" natural language works
- ✅ Graph panel shows commit history

---

### **6. Editor Streaming** ✅

```bash
# Open a file
:edit app.py

# Use live edit mode
:live-edit app.py

# Type: "add a function that prints hello"
# Watch text stream token-by-token into editor
```

**Expected Results:**
- ✅ Text streams character-by-character
- ✅ Editor updates in real-time
- ✅ No lag or delays
- ✅ Streaming finishes cleanly

---

### **7. Navigation Commands** ✅

```bash
# Change directory
cd subfolder

# Go up
cd ..

# Show current directory
pwd

# Clear screen
clear

# Show stats
stats

# Exit
exit
```

**Expected Results:**
- ✅ cd works correctly
- ✅ pwd shows current directory
- ✅ clear clears console
- ✅ stats shows workspace info
- ✅ exit closes program

---

### **8. Editor Scrolling** ✅

```bash
# Open a large file
:edit large_file.py

# Test scrolling
:up
:down
:pageup
:pagedown
:scroll-up
:scroll-down
```

**Expected Results:**
- ✅ All scroll commands work
- ✅ Viewport moves correctly
- ✅ Only works in editor mode (error if not)

---

### **9. AI Model Switching** ✅

```bash
# View available models
:models

# Switch model
:set-ai gpt-4o-mini
:set-ai gemini-1.5-pro
:set-ai claude-3.5-sonnet

# Check stats
stats
```

**Expected Results:**
- ✅ :models panel shows all providers
- ✅ Model switching works
- ✅ Stats show current model
- ✅ AI responses use new model

---

### **10. Multi-line Input** ✅

```bash
# Test multi-line mode
:ml
create a file called complex.py with
def complex_function():
    """This is a complex function"""
    result = []
    for i in range(10):
        result.append(i * 2)
    return result
:end
```

**Expected Results:**
- ✅ Multi-line input works
- ✅ File created with all lines
- ✅ No truncation

---

### **11. Path Resolution (No Doubling)** ✅

```bash
# Create folder
create folder demo

# Go into it
cd demo

# Create file (should NOT be demo/demo/file.txt)
create file test.txt

# Verify path
pwd
# Should show: /path/to/demo (not /path/to/demo/demo)
```

**Expected Results:**
- ✅ No path doubling (demo/demo → demo)
- ✅ Files created in correct location
- ✅ Paths resolve correctly

---

### **12. Documentation Auto-Sync** ✅

```bash
# Create a new file
create file new_feature.py

# Check if docs updated
read file README.md
read file docs/COMMANDS.md
```

**Expected Results:**
- ✅ Documentation files update automatically
- ✅ No manual doc updates needed

---

### **13. File System Watcher** ✅

```bash
# Open file in editor
:edit test.txt

# In another terminal, modify the file externally
echo "External change" >> test.txt

# Watch editor panel auto-refresh (if not modified)
```

**Expected Results:**
- ✅ File changes detected automatically
- ✅ Editor refreshes (if not modified)
- ✅ Tree panel updates
- ✅ No manual refresh needed

---

### **14. Error Handling** ✅

```bash
# Test error cases
delete file nonexistent.txt    # Should show error, not crash
cd /invalid/path               # Should show error, not crash
:edit nonexistent.txt          # Should handle gracefully
```

**Expected Results:**
- ✅ Errors shown clearly
- ✅ No crashes
- ✅ Program continues running
- ✅ User-friendly error messages

---

### **15. GitHub Operations** ✅

```bash
# Create GitHub repo (requires GITHUB_TOKEN)
create github repo my-project

# Create issue
create github issue "Bug: Fix path doubling"

# Create PR
create github pr "Add new feature"
```

**Expected Results:**
- ✅ GitHub operations work (if token set)
- ✅ Repos created successfully
- ✅ Issues/PRs created

---

## 🎯 **Quick Test Script**

Run this sequence to test everything quickly:

```bash
# 1. Launch
gitvision

# 2. View commands
:sheet

# 3. Create test project
create folder test_project
cd test_project

# 4. Create files
create file main.py with print("Hello")
create file utils.py with def helper(): pass

# 5. Edit file
:edit main.py
add line 1 with # Main module
replace line 2 with print("Hello GitVision!")

# 6. Git workflow
git init
git add .
git commit "Initial commit"
:git-graph

# 7. Test line operations
remove line 1
add print("Test") at bottom

# 8. Save and verify
:save
read file main.py

# 9. Cleanup
cd ..
delete folder test_project
```

---

## 🔍 **Troubleshooting**

### **Issue: "gitvision: command not found"**

```bash
# Solution: Install in development mode
pip install -e .

# Or add to PATH
export PATH="$PATH:/path/to/GitVisionCLI"
```

### **Issue: "No API key configured"**

```bash
# Solution: Set at least one API key
export OPENAI_API_KEY="sk-..."
```

### **Issue: "Module not found" or "No module named 'requests'"**

```bash
# Solution: Install all dependencies
pip install -e .

# This installs everything from pyproject.toml:
# - colorama, rich, requests, markdown-it-py
# - openai, anthropic, google-generativeai
```

### **Issue: Colors not showing**

```bash
# Solution: Check terminal supports ANSI colors
echo -e "\033[38;5;165mTest\033[0m"
# Should show colored text
```

---

## ✅ **Success Criteria**

Your program is working correctly if:

- ✅ All `:sheet` commands are documented
- ✅ All natural language commands work instantly
- ✅ No path doubling occurs
- ✅ No "Path is not a file" errors for folders
- ✅ Editor streaming works smoothly
- ✅ All panels render correctly
- ✅ Colors are consistent
- ✅ File system watcher syncs changes
- ✅ Documentation auto-updates
- ✅ No crashes on errors

---

## 🎉 **You're Ready!**

Once all tests pass, your GitVisionCLI is **PUBLISH READY**! 🚀

