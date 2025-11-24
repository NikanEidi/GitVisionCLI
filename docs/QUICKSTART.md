# 🚀 GitVisionCLI Quick Start Guide

**Get started with GitVisionCLI in 5 minutes!**

<div align="center">

[![Quick Start](https://img.shields.io/badge/Time-5%20Minutes-blue.svg)](https://github.com/NikanEidi/GitVisionCLI)
[![Version](https://img.shields.io/badge/Version-1.1.0-purple.svg)](https://github.com/NikanEidi/GitVisionCLI)

</div>

---

## 📦 **Installation**

### **Step 1: Clone or Download**

```bash
# Clone from GitHub
git clone https://github.com/NikanEidi/GitVisionCLI.git
cd GitVisionCLI

# Or download and extract ZIP
```

### **Step 2: Install Dependencies**

```bash
# Install in development mode (recommended)
pip install -e .

# Or use pipx for isolated installation
pipx install -e .
```

**What gets installed:**
- Core dependencies (colorama, rich, requests, markdown-it-py)
- AI SDKs (openai, anthropic, google-generativeai)
- All other required packages

### **Step 3: Set API Key**

**Choose at least one AI provider:**

#### **Option 1: OpenAI** (Recommended for beginners)
```bash
export OPENAI_API_KEY="sk-..."
```

#### **Option 2: Claude**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### **Option 3: Gemini**
```bash
# Get key from https://makersuite.google.com/app/apikey
export GOOGLE_API_KEY="..."
# Then switch to Gemini: :set-ai gemini-1.5-pro
```

#### **Option 4: Ollama** (Local, free - no API key needed)
```bash
# Install Ollama: https://ollama.com
ollama pull llama2
# Then switch: :set-ai llama2
```

**Alternative: Config File**

API keys can also be set in `gitvisioncli/config/config.json`:
```json
{
  "providers": {
    "openai": {"api_key": "sk-..."},
    "gemini": {"api_key": "..."},
    "claude": {"api_key": "sk-ant-..."}
  }
}
```

### **Step 4: Verify Installation**

```bash
gitvision doctor
```

**Expected Output:**
```
✓ Python 3.x.x
✓ openai SDK installed
✓ anthropic SDK installed
✓ google-generativeai SDK installed
✓ OpenAI API key configured
✅ All systems operational
```

### **Step 5: Launch**

```bash
gitvision
```

Or use interactive mode:
```bash
gitvision interactive
```

🎉 **You're in!**

---

## ⚡ **Your First 5 Minutes**

### **Minute 1: Explore the UI**

```bash
:banner         # Quick commands and logo
:sheet          # Full command reference
:tree           # File browser
:close          # Return to banner
```

**What you'll see:**
- **Left Panel**: AI Console (chat interface with neon purple borders)
- **Right Panel**: Workspace (banner/tree/editor/etc.)

**Key Features:**
- Beautiful dual-panel layout
- Neon purple theme with gradient effects
- Smooth, flicker-free rendering
- Responsive to terminal size

### **Minute 2: Create Your First File**

**Simple single-line file:**
```bash
create a file called hello.py with print("Hello GitVision!")
```

**Multiline file:**
```bash
:ml
create a file called app.py with
def main():
    print("Hello GitVision!")
    return 0

if __name__ == "__main__":
    main()
:end
```

**Alternative: Fenced code blocks**
````bash
```python
def hello():
    print("World")
```
````

### **Minute 3: Edit with Natural Language**

```bash
# Open file in editor
:edit hello.py

# Now edit it (no need to specify filename - it's open!)
add line 1 with # My first GitVision file
replace line 2 with print("This is amazing!")
add print("End of file") at bottom
```

**Key Feature:** When a file is open, you don't need to specify the filename!

**All line editing commands:**
```bash
remove line 5              # Delete line 5
delete lines 3-7           # Delete range
add line 1 with # comment # Insert at line 1
insert line 5 with code    # Insert before line 5
edit line 3 with new code  # Replace line 3
replace line 2 with text   # Same as edit
add text at bottom         # Append to end
```

### **Minute 4: Git Workflow**

```bash
# Initialize repository
git init

# Stage files
git add .

# Commit
git commit "Initial commit"

# View commit graph (beautiful ASCII visualization)
:git-graph
```

**Complete Git commands:**
```bash
git init                           # Initialize repo
git add .                          # Stage all files
git commit "Message"               # Commit changes
git branch feature                 # Create branch
git checkout feature               # Switch branch
git merge main                     # Merge branches
git push                           # Push to remote
git pull                           # Pull from remote
git status                         # Check status
git log                            # View history
git remote add origin <url>        # Add remote
```

### **Minute 5: Ask AI**

```bash
# Ask questions about your code
explain the file hello.py
how can I improve this code?
what does this function do?
find bugs in this file
refactor this function
create a test file for hello.py
```

**AI Features:**
- Natural language understanding
- Context-aware responses
- Code analysis and suggestions
- Bug detection
- Refactoring recommendations
- Test generation

---

## 🎯 **Core Concepts**

### **1. Multiline Input**

For multi-line content, use `:ml`:

```bash
:ml
create a file called app.py with
def main():
    print("Hello!")
    
if __name__ == "__main__":
    main()
:end
```

**Alternative:** You can also paste fenced code blocks:
````bash
```python
def hello():
    print("World")
```
````

### **2. Context-Aware Editing**

When a file is open in `:edit`, you can:
- **Omit filename**: `remove line 1` (works on open file)
- **Chain commands**: Multiple edits in sequence
- **No questions**: AI never asks "which file?"

**Example:**
```bash
:edit app.py
remove line 1
add # -*- coding: utf-8 -*- at line 1
replace line 5 with print("Updated!")
```

### **3. Panels**

| Command | Panel | Description |
|---------|-------|-------------|
| `:banner` | Banner | Quick commands and logo |
| `:sheet` | Sheet | Full command reference |
| `:tree` | Tree | File browser |
| `:git-graph` | Git Graph | Commit visualization |
| `:edit FILE` | Editor | Code editor with line numbers |
| `:live-edit FILE` | Live Editor | AI live editor with streaming |
| `:markdown FILE` | Markdown | Rendered markdown preview |
| `:models` | Models | AI model manager |
| `:close` | Close | Close current panel |

### **4. Natural Language Commands**

Many commands work **instantly** without AI:

**File operations:**
```bash
create file app.py
read file app.py
delete file old.py
rename app.py to main.py
move app.py to src/
copy app.py to backup.py
```

**Line editing (when file is open):**
```bash
remove line 5
add print("hi") at line 10
replace line 3 with new_code
delete lines 5-10
```

**Git operations:**
```bash
git init
git add .
git commit "Message"
git branch feature
git checkout feature
git merge main
git push
git pull
```

**Shell commands (all supported!):**
```bash
ls, cd, pwd, cat, grep, find, mkdir, rm, cp, mv
python, node, npm, pip, brew, apt, yum
# And 30+ more commands!
```

### **5. Grammar Auto-Fix**

Broken grammar is automatically fixed:

```bash
remove line1    # → remove line 1
delete ln5      # → delete line 5
rm 2            # → remove line 2 (when file is open)
edit line3      # → edit line 3
add at line10   # → add at line 10
```

### **6. Search & Find**

```bash
# Search for text
search for "TODO"
search for "def" in app.py

# Find files
find files named "test"
list files in src/
```

### **7. Debug & Run**

```bash
# Run scripts
run app.py              # Auto-detects Python/Node/Bash
debug buggy.py
test test_suite.py

# Shell commands
python app.py
node server.js
bash script.sh
```

---

## 💡 **Common Workflows**

### **Workflow 1: Create New Project**

```bash
# Launch GitVision
gitvision

# Initialize Git
git init

# Create README
:ml
create a file called README.md with
# My Project
Description here
:end

# Create main file
create a file called main.py with print("Hello!")

# Stage and commit
git add .
git commit "Initial commit"
```

### **Workflow 2: Edit Existing File**

```bash
# Open file
:edit app.py

# Make edits (no filename needed!)
remove line 5
add # Updated at line 1
replace line 10 with print("New code")

# Save
:save

# Commit
git add app.py
git commit "Update app"
```

### **Workflow 3: GitHub Integration**

```bash
# Set GitHub token
export GITHUB_TOKEN="ghp_..."

# Launch GitVision
gitvision

# Create GitHub repo
create github repo my-project --private

# Push code
git push -u origin main

# Create issue
create github issue "Bug: Fix path doubling"

# Create PR
create github pr "Add new feature"
```

### **Workflow 4: AI-Powered Editing**

```bash
# Open file
:edit app.py

# Use live edit mode (streaming)
:live-edit app.py

# Ask AI to edit
add error handling to this function
optimize this code
refactor this function
explain how this works
```

### **Workflow 5: Multi-Model Development**

```bash
# Switch between models
:models                    # View available models
:set-ai gpt-4o-mini        # Use OpenAI
:set-ai gemini-1.5-pro     # Use Gemini
:set-ai claude-3-5-sonnet  # Use Claude
:set-ai llama2             # Use Ollama (local)

# All models support:
# - Full streaming
# - Tool calling
# - Natural language
```

---

## 🎨 **UI Features**

### **Dual-Panel Interface**

```
╔═══════════════════════════════╦═══════════════════════════════╗
║      LEFT: AI CONSOLE         ║     RIGHT: WORKSPACE           ║
╠═══════════════════════════════╬═══════════════════════════════╣
║  💬 Chat Stream               ║  📁 File Tree                  ║
║  🔧 Tool Logs                 ║  ✏️ Editor (line numbers)     ║
║  ⚡ Status Updates            ║  📊 Git Graph                 ║
║  🎨 Neon Purple Theme         ║  📖 Command Sheet             ║
║  ⚡ Real-time Streaming       ║  📄 Markdown Preview          ║
╚═══════════════════════════════╩═══════════════════════════════╝
            📊 Status Bar (branch, cwd, time)
                      ● INPUT
```

### **Editor Features**

- **Line Numbers**: Automatically displayed with vibrant colors
- **Auto-save**: Changes sync to UI when saved
- **Live Streaming**: AI text streams token-by-token into editor
- **Scrolling**: `:up`, `:down`, `:pageup`, `:pagedown`
- **Syntax Awareness**: AI understands code structure
- **ANSI-Aware**: Proper color handling, no bleeding

### **Panel Features**

- **Banner**: Quick command reference with logo
- **Sheet**: Comprehensive command list organized by category
- **Tree**: Interactive file browser with color coding
- **Editor**: Code editor with line numbers and syntax awareness
- **Git Graph**: Beautiful ASCII commit visualization
- **Models**: AI model manager with provider info

---

## 🔧 **Configuration**

### **Environment Variables**

```bash
# AI Providers (choose at least one)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# GitHub (optional)
export GITHUB_TOKEN="ghp_..."
```

### **Config File**

Location: `gitvisioncli/config/config.json`

```json
{
  "api_key": "sk-...",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 4096,
  "dry_run": false,
  "providers": {
    "openai": {"api_key": "sk-..."},
    "gemini": {"api_key": "..."},
    "claude": {"api_key": "sk-ant-..."}
  },
  "github": {
    "token": "ghp_...",
    "user": "your-username"
  }
}
```

---

## ❓ **Troubleshooting**

### **Issue: "Please specify file..."**

**Fix:** Open file first with `:edit FILENAME`

```bash
:edit app.py
remove line 1  # Now works!
```

### **Issue: Multiline not working**

**Fix:** Use `:ml` before content, end with `:end`

```bash
:ml
<content>
:end
```

### **Issue: GitHub token not working**

**Fix:** Set environment variable before launching

```bash
export GITHUB_TOKEN="ghp_..."
gitvision
```

### **Issue: API key not found**

**Fix:** Set environment variable or update config.json

```bash
export OPENAI_API_KEY="sk-..."
# Or edit gitvisioncli/config/config.json
```

### **Issue: Module not found**

**Fix:** Install dependencies

```bash
pip install -e .
```

### **Issue: Colors not showing**

**Fix:** Check terminal supports ANSI colors

```bash
echo -e "\033[38;5;165mTest\033[0m"
# Should show colored text
```

### **Issue: Gemini model not found**

**Fix:** Use correct model name

```bash
:set-ai gemini-1.5-pro  # ✅ Correct
:set-ai gemini-pro      # ❌ Not available in v1beta API
```

### **Issue: Editor panel shows "Render error"**

**Fix:** This was fixed in v1.1.0. Update to latest version:

```bash
pip install --upgrade -e .
```

---

## 📚 **Next Steps**

### **Learn More**

- 📖 [COMMANDS.md](COMMANDS.md) - Complete command reference (all commands)
- 🎯 [FEATURES.md](FEATURES.md) - Advanced features overview
- 🧪 [RUN_AND_TEST.md](RUN_AND_TEST.md) - Comprehensive testing guide
- 📝 [CHANGELOG.md](../CHANGELOG.md) - Version history and changes

### **Advanced Topics**

- Natural Language Action Engine
- AI Model Switching
- GitHub Integration
- Custom Workflows
- Shell Command Integration
- Search and Find Operations

---

## 🎉 **You're Ready!**

You now know the basics of GitVisionCLI. Start coding and explore!

**Quick Commands to Remember:**
- `:sheet` - See all commands
- `:edit <file>` - Open file
- `:tree` - Browse files
- `:git-graph` - View commits
- `:models` - Manage AI models
- `gitvision doctor` - Check system health

**Pro Tips:**
- Use `:ml` for multiline content
- Open files with `:edit` to enable context-aware editing
- All shell commands work directly (ls, cd, grep, etc.)
- Switch models with `:set-ai <model>`
- Use natural language for search and find

**Happy Coding!** 🚀

---

**Version**: 1.1.0  
**Last Updated**: 2024-12-XX
