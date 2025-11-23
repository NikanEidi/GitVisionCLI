# 🚀 GitVisionCLI Quick Start Guide

**Get started with GitVisionCLI in 5 minutes!**

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

### **Step 3: Set API Key**

**Choose at least one AI provider:**

```bash
# OpenAI (Recommended for beginners)
export OPENAI_API_KEY="sk-..."

# Or Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# Or Gemini (get key from https://makersuite.google.com/app/apikey)
export GOOGLE_API_KEY="..."
# Then switch to Gemini: :set-ai gemini-1.5-pro

# Or use Ollama (local, free - no API key needed)
# Install: https://ollama.com
ollama pull llama2
```

**Note:** API keys can also be set in `gitvisioncli/config/config.json`:
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

You should see:
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
- **Left Panel**: AI Console (chat interface)
- **Right Panel**: Workspace (banner/tree/editor/etc.)

### **Minute 2: Create Your First File**

```bash
# Simple single-line file
create a file called hello.py with print("Hello GitVision!")

# Or multi-line file
:ml
create a file called app.py with
def main():
    print("Hello GitVision!")
    return 0

if __name__ == "__main__":
    main()
:end
```

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

### **Minute 4: Git Workflow**

```bash
# Initialize repository
git init

# Stage files
git add .

# Commit
git commit "Initial commit"

# View commit graph
:git-graph
```

### **Minute 5: Ask AI**

```bash
# Ask questions about your code
explain the file hello.py
how can I improve this code?
what does this function do?
```

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
| `:markdown FILE` | Markdown | Rendered markdown preview |
| `:models` | Models | AI model manager |

### **4. Natural Language Commands**

Many commands work **instantly** without AI:

```bash
# File operations
create file app.py
read file app.py
delete file old.py
rename app.py to main.py

# Line editing (when file is open)
remove line 5
add print("hi") at line 10
replace line 3 with new_code

# Git operations
git init
git add .
git commit "Message"
git branch feature
```

### **5. Grammar Auto-Fix**

Broken grammar is automatically fixed:

```bash
remove line1    # → remove line 1
delete ln5      # → delete line 5
rm 2            # → remove line 2
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
```

### **Workflow 4: AI-Powered Editing**

```bash
# Open file
:edit app.py

# Use live edit mode
:live-edit app.py

# Ask AI to edit
add error handling to this function
optimize this code
refactor this function
```

---

## 🎨 **UI Features**

### **Dual-Panel Interface**

- **Left Panel**: AI Console
  - Chat with AI
  - See AI responses
  - View command history

- **Right Panel**: Workspace
  - Banner (quick commands)
  - Tree (file browser)
  - Editor (code editing)
  - Git Graph (commit visualization)
  - Sheet (command reference)

### **Editor Features**

- **Line Numbers**: Automatically displayed
- **Auto-save**: Changes sync to UI when saved
- **Live Streaming**: AI text streams token-by-token
- **Scrolling**: `:up`, `:down`, `:pageup`, `:pagedown`
- **Syntax Awareness**: AI understands code structure

---

## 🔧 **Configuration**

### **Environment Variables**

```bash
# AI Providers
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

---

## 📚 **Next Steps**

### **Learn More**

- 📖 [COMMAND_SHEET.md](../COMMAND_SHEET.md) - Complete command reference (all commands)
- 📖 [COMMANDS.md](COMMANDS.md) - Detailed command documentation
- 🎯 [FEATURES.md](FEATURES.md) - Advanced features overview
- 🧪 [RUN_AND_TEST.md](../RUN_AND_TEST.md) - Comprehensive testing guide

### **Advanced Topics**

- Natural Language Action Engine
- AI Model Switching
- GitHub Integration
- Custom Workflows

---

## 🎉 **You're Ready!**

You now know the basics of GitVisionCLI. Start coding and explore!

**Quick Commands to Remember:**
- `:sheet` - See all commands
- `:edit <file>` - Open file
- `:tree` - Browse files
- `:git-graph` - View commits
- `gitvision doctor` - Check system health

**Happy Coding!** 🚀

---

**Version**: 1.0.0  
**Last Updated**: 2024-12-XX
