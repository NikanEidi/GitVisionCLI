# 🚀 QuickStart Guide

**Get started with GitVisionCLI in 5 minutes!**

---

## 📦 **Installation**

### **Step 1: Install**

```bash
cd /path/to/GitVisionCLI
pipx install -e .
```

### **Step 2: Set API Key**

Pick your favorite AI provider:

```bash
# OpenAI (Recommended)
export OPENAI_API_KEY="sk-..."

# Or Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# Or Gemini
export GOOGLE_API_KEY="..."
```

### **Step 3: Launch**

```bash
gitvision
```

🎉 **You're in!**

---

## ⚡ **Your First 5 Minutes**

### **Minute 1: Explore the UI**

```bash
:banner         # Quick commands
:sheet          # Full reference
:tree           # File browser
```

### **Minute 2: Create a File**

```bash
create a file called hello.py with print("Hello GitVision!")
```

### **Minute 3: Edit with Natural Language**

```bash
:edit hello.py
add line 1 with # My first GitVision file
edit line 2 with print("This is amazing!")
```

### **Minute 4: Git Workflow**

```bash
git init
git add .
git commit "Initial commit"
:git-graph
```

### **Minute 5: Ask AI**

```bash
explain the file hello.py
how can I improve this code?
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

### **2. Context-Aware Editing**

When a file is open in `:edit`, you can:
- Omit filename: `remove line 1`
- Chain commands: Multiple edits in sequence

### **3. Panels**

| Command | Panel |
|---------|-------|
| `:banner` | Quick commands |
| `:sheet` | Full reference |
| `:tree` | File browser |
| `:git-graph` | Commit visualization |
| `:edit FILE` | Code editor |

---

## 💡 **Common Workflows**

### **Create New Project**

```bash
gitvision
git init
:ml
create a file called README.md with
# My Project
Description here
:end
git add .
git commit "Initial commit"
```

### **Edit Existing File**

```bash
:edit app.py
remove line 5
add line 1 with # -*- coding: utf-8 -*-
git add app.py
git commit "Update app"
```

### **GitHub Integration**

```bash
export GITHUB_TOKEN="ghp_..."
gitvision
create github repo my-project --private
git push -u origin main
```

---

## ❓ **Troubleshooting**

**Issue:** "Please specify file..."  
**Fix:** Open file first with `:edit FILENAME`

**Issue:** Multiline not working  
**Fix:** Use `:ml` before content, end with `:end`

**Issue:** GitHub token  
**Fix:** `export GITHUB_TOKEN="ghp_xxx"` before launching

---

## 📚 **Next Steps**

- 📖 Read [COMMANDS.md](COMMANDS.md) for full reference
- 🎯 Check [FEATURES.md](FEATURES.md) for advanced features
- 🧪 Try [TESTING_GUIDE.md](../TESTING_GUIDE.md) for comprehensive testing

---

**Ready to become a GitVision master? Let's go!** 🎯
