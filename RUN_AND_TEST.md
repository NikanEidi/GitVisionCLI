# 🚀 How to Run & Test GitVisionCLI

**Comprehensive guide for running, testing, and validating GitVisionCLI.**

<div align="center">

[![Testing](https://img.shields.io/badge/Testing-Comprehensive-blue.svg)](https://github.com/NikanEidi/GitVisionCLI)
[![Version](https://img.shields.io/badge/Version-1.1.0-purple.svg)](https://github.com/NikanEidi/GitVisionCLI)

</div>

---

## 📦 **Installation**

### **Step 1: Install Dependencies**

```bash
# Navigate to project directory
cd /path/to/GitVisionCLI

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

# Then run directly from the project root
cd /path/to/GitVisionCLI
python3 -m gitvisioncli.cli
```

### **Set API Key (Required)**

```bash
# Choose at least one AI provider
export OPENAI_API_KEY="sk-..."              # For GPT-4/GPT-4o-mini
export ANTHROPIC_API_KEY="sk-ant-..."       # For Claude
export GOOGLE_API_KEY="..."                 # For Gemini (get from https://makersuite.google.com/app/apikey)

# Optional: GitHub integration
export GITHUB_TOKEN="ghp_..."
```

**Note:** After setting Gemini API key, switch to Gemini:
```bash
gitvision
:set-ai gemini-1.5-pro
```

---

## 🎮 **How to Run**

### **Basic Launch**

```bash
gitvision
```

### **Interactive Mode**

```bash
gitvision interactive
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
:models          # Should show model manager
:close           # Should return to banner
```

**Expected Results:**
- ✅ Dual-panel UI appears (AI Console + Workspace)
- ✅ All panels render correctly
- ✅ Colors are consistent (neon purple, cyan, magenta)
- ✅ No errors in console
- ✅ Smooth transitions between panels
- ✅ No flicker or duplicate rendering

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
- ✅ File paths resolve correctly

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
- ✅ Folder deletion works

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
- ✅ Line numbers displayed with vibrant colors
- ✅ All line operations work instantly
- ✅ Grammar fixes work (line1→line 1, rm 5→remove line 5)
- ✅ No questions asked when file is open
- ✅ Changes reflect immediately

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
- ✅ Branch operations work correctly
- ✅ Status and log display correctly

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
- ✅ No duplicate outputs
- ✅ Proper cleanup on completion

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

### **8. Shell Commands** ✅

```bash
# Test various shell commands
ls
ls -la
cat app.py
grep "def" app.py
find . -name "*.py"
python app.py
node server.js
pip install requests
```

**Expected Results:**
- ✅ All shell commands work directly
- ✅ No AI overhead for shell commands
- ✅ Output displayed correctly
- ✅ Exit codes handled properly

---

### **9. Natural Language Commands** ✅

```bash
# Search
search for "TODO"
search for "def" in app.py

# Find
find files named "test"
list files in src/

# Run
run app.py
debug buggy.py
test test_suite.py
```

**Expected Results:**
- ✅ Search works correctly
- ✅ Find files works
- ✅ Run scripts auto-detects type
- ✅ Debug and test commands work

---

### **10. AI Model Switching** ✅

```bash
# View available models
:models

# Switch model
:set-ai gpt-4o-mini
:set-ai gemini-1.5-pro
:set-ai claude-3-5-sonnet
:set-ai llama2

# Check stats
stats
```

**Expected Results:**
- ✅ :models panel shows all providers
- ✅ Model switching works
- ✅ Stats show current model
- ✅ AI responses use new model
- ✅ All models support streaming

---

### **11. Multi-line Input** ✅

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
- ✅ Proper formatting preserved

---

### **12. Path Resolution (No Doubling)** ✅

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
- ✅ Error messages helpful if token missing

---

### **16. AI Streaming & Tools** ✅

```bash
# Test streaming
:edit app.py
explain this file
# Watch response stream token-by-token

# Test tool calling
create a test file for app.py
# Should execute file creation tool
```

**Expected Results:**
- ✅ Streaming works for all models
- ✅ Tool calling works correctly
- ✅ No duplicate outputs
- ✅ Proper error handling

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

# 8. Test shell commands
ls
cat main.py
grep "print" main.py

# 9. Test natural language
search for "print"
find files named "main"

# 10. Test AI
explain the file main.py
find bugs

# 11. Save and verify
:save
read file main.py

# 12. Cleanup
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

### **Issue: Gemini model not found**

```bash
# Solution: Use correct model name
:set-ai gemini-1.5-pro  # ✅ Correct
:set-ai gemini-pro      # ❌ Not available in v1beta API
```

### **Issue: Editor panel shows "Render error"**

```bash
# Solution: This was fixed in v1.1.0. Update to latest version:
pip install --upgrade -e .
```

### **Issue: Panels stacking/not clearing**

```bash
# Solution: This was fixed in v1.1.0. Update to latest version:
pip install --upgrade -e .
```

### **Issue: Error messages in conversation history**

```bash
# Solution: This was fixed in v1.1.0. Update to latest version:
pip install --upgrade -e .
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
- ✅ Colors are consistent (neon purple theme)
- ✅ File system watcher syncs changes
- ✅ Documentation auto-updates
- ✅ No crashes on errors
- ✅ All shell commands work
- ✅ All AI models support streaming
- ✅ Error messages properly filtered
- ✅ No duplicate outputs

---

## 🧪 **Advanced Testing**

### **Test All Models**

```bash
# Test OpenAI
:set-ai gpt-4o-mini
explain the file app.py

# Test Gemini
:set-ai gemini-1.5-pro
explain the file app.py

# Test Claude
:set-ai claude-3-5-sonnet
explain the file app.py

# Test Ollama (if installed)
:set-ai llama2
explain the file app.py
```

### **Test Streaming**

```bash
# Test streaming for each model
:live-edit app.py
add a function that calculates fibonacci
# Watch token-by-token streaming
```

### **Test Error Handling**

```bash
# Test with invalid API key
export OPENAI_API_KEY="invalid"
:set-ai gpt-4o-mini
explain the file app.py
# Should show helpful error message

# Test with missing file
delete file nonexistent.txt
# Should show error, not crash
```

### **Test Edge Cases**

```bash
# Test empty file
create file empty.txt with

# Test very long file
:ml
create a file called long.py with
# (paste 1000+ lines)
:end

# Test special characters
create file test.txt with Hello "World" & 'Test'
```

---

## 📊 **Test Results Template**

Use this template to track your testing:

```markdown
## Test Results

### Basic Functionality
- [ ] UI renders correctly
- [ ] Panels switch smoothly
- [ ] Colors display properly

### File Operations
- [ ] Create file works
- [ ] Read file works
- [ ] Delete file works
- [ ] Rename file works
- [ ] Move file works
- [ ] Copy file works

### Line Editing
- [ ] Remove line works
- [ ] Add line works
- [ ] Edit line works
- [ ] Delete range works
- [ ] Append works

### Git Operations
- [ ] Init works
- [ ] Add works
- [ ] Commit works
- [ ] Branch works
- [ ] Checkout works
- [ ] Merge works
- [ ] Push works
- [ ] Pull works
- [ ] Graph displays

### AI Features
- [ ] Model switching works
- [ ] Streaming works
- [ ] Tool calling works
- [ ] Error handling works

### Shell Commands
- [ ] ls works
- [ ] cd works
- [ ] grep works
- [ ] find works
- [ ] python works
- [ ] All other commands work
```

---

## 🎉 **You're Ready!**

Once all tests pass, your GitVisionCLI is **PRODUCTION READY**! 🚀

**Next Steps:**
- Read [COMMANDS.md](docs/COMMANDS.md) for complete command reference
- Read [FEATURES.md](docs/FEATURES.md) for detailed features
- Read [QUICKSTART.md](docs/QUICKSTART.md) for quick start guide

---

**Version**: 1.1.0  
**Last Updated**: 2024-12-XX
