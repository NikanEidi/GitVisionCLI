# 📚 Complete Command Reference

**All GitVisionCLI commands in one place.**

---

## 📑 **Table of Contents**

- [File Operations](#-file-operations)
- [Line Editing](#-line-editing)
- [Git Commands](#-git-commands)
- [GitHub Integration](#-github-integration)
- [AI Commands](#-ai-commands)
- [Panel Navigation](#-panel-navigation)
- [Workspace](#-workspace)

---

## 📁 **File Operations**

### **Create Files**

**Single line:**
```bash
create a file called <name> with <content>
```

**Example:**
```bash
create a file called hello.py with print("Hello World!")
```

**Multiline:**
```bash
:ml
create a file called <name> with
<content>
<more content>
:end
```

**Example:**
```bash
:ml
create a file called app.py with
def main():
    print("Hello!")
    
if __name__ == "__main__":
    main()
:end
```

### **Read Files**

```bash
read file <name>
```

**Example:**
```bash
read file app.py
```

### **Delete Files**

```bash
delete file <name>
```

**Example:**
```bash
delete file old_file.py
```

### **Rename Files**

```bash
rename <old_name> to <new_name>
```

**Example:**
```bash
rename app.py to main.py
```

---

## ✏️ **Line Editing**

**Prerequisites:** Open file in editor first

```bash
:edit <filename>
```

### **Delete Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `remove line N` | Delete line N | `remove line 5` |
| `delete line N` | Delete line N | `delete line 10` |
| `delete lines N-M` | Delete range | `delete lines 5-10` |

### **Add Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `add line N with TEXT` | Insert before line N | `add line 1 with # comment` |
| `insert line N with TEXT` | Insert before line N | `insert line 5 with x = 42` |

### **Edit/Replace Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `edit line N with TEXT` | Replace line N | `edit line 3 with y = 100` |
| `replace line N with TEXT` | Replace line N | `replace line 2 with new code` |
| `update line N with TEXT` | Replace line N | `update line 4 with data = []` |

---

## 🌳 **Git Commands**

### **Initialize**

```bash
git init
```

### **Staging**

```bash
git add <file>           # Stage specific file
git add .                # Stage all files
```

### **Committing**

```bash
git commit "<message>"
```

**Example:**
```bash
git commit "Add new feature"
```

### **Status & History**

```bash
git status               # Check repository status
git log                  # View commit history
:git-graph              # Visual commit graph
```

### **Branching**

```bash
git branch <name>        # Create branch
git checkout <name>      # Switch branch
git merge <name>         # Merge branch
```

**Example:**
```bash
git branch feature-auth
git checkout feature-auth
# make changes
git checkout main
git merge feature-auth
```

### **Remote Operations**

```bash
git push                 # Push to remote
git pull                 # Pull from remote
git push -u origin main  # First push (set upstream)
```

---

## 🐙 **GitHub Integration**

**Prerequisites:** Set GitHub token

```bash
export GITHUB_TOKEN="ghp_..."
```

### **Create Repository**

```bash
create github repo <name> --private
create github repo <name> --public
```

**Example:**
```bash
create github repo my-awesome-project --private
```

### **Create Issue**

```bash
create github issue "<title>" --body "<description>"
```

**Example:**
```bash
create github issue "Bug: Login fails" --body "Users cannot log in with valid credentials"
```

### **Create Pull Request**

```bash
create github pr "<title>" --head <branch> --base <target>
```

**Example:**
```bash
create github pr "Add authentication" --head feature-auth --base main
```

---

## 🤖 **AI Commands**

### **Code Analysis**

```bash
explain the file <name>
analyze this code
find bugs in this file
```

**Examples:**
```bash
explain the file app.py
analyze this code
find bugs in this file
```

### **Code Generation**

```bash
create a test file for <name>
refactor this function
add error handling
optimize this code
```

**Examples:**
```bash
create a test file for app.py
refactor this function
add error handling to the main function
```

### **Model Management**

```bash
:models                          # List available models
:set-ai <model>                  # Switch model
```

**Examples:**
```bash
:set-ai openai/gpt-4
:set-ai anthropic/claude-3.5-sonnet
:set-ai google/gemini-pro
```

---

## 🎨 **Panel Navigation**

| Command | Panel | Description |
|---------|-------|-------------|
| `:banner` | Banner | Quick command list |
| `:sheet` | Sheet | Full command reference |
| `:tree` | Tree | File browser |
| `:git-graph` | Git Graph | Visual commit history |
| `:edit <file>` | Editor | Code editor with line numbers |

**Examples:**
```bash
:banner
:tree
:git-graph
:edit app.py
```

---

## ⚙️ **Workspace**

### **Navigation**

```bash
cd <path>                # Change directory
pwd                      # Print working directory
```

**Examples:**
```bash
cd ../other-project
pwd
```

### **Information**

```bash
stats                    # Workspace statistics
clear                    # Clear console
```

### **Exit**

```bash
exit
quit
```

---

## 💡 **Pro Tips**

### **Natural Language**

Be conversational! GitVision understands:

✅ `remove line 5`  
✅ `delete that line`  
✅ `add a comment at the top`  
✅ `explain this function`

### **Multiline Everything**

Use `:ml` for any multi-line input:

```bash
:ml
<your content>
<multiple lines>
:end
```

### **Chain Commands**

When file is open in `:edit`, chain edits:

```bash
:edit app.py
add line 1 with # comment
edit line 5 with new code
remove line 10
git add app.py
git commit "Updates"
```

### **Panel Shortcuts**

Quick navigation:

```bash
:b          # :banner
:s          # :sheet
:t          # :tree
:g          # :git-graph
```

---

## 🔎 **Search & Find**

```bash
search for "<term>" in project
search for "<term>" in <file>
```

**Examples:**
```bash
search for "TODO" in project
search for "def" in app.py
```

---

## 🎯 **Complete Workflow Example**

```bash
# 1. Launch
gitvision

# 2. Initialize project
git init

# 3. Create files
:ml
create a file called app.py with
def main():
    print("Hello")
:end

# 4. Edit
:edit app.py
add line 1 with # My app
edit line 3 with     print("GitVision!")

# 5. Git workflow
git add .
git commit "Initial commit"
:git-graph

# 6. GitHub
export GITHUB_TOKEN="ghp_..."
create github repo my-app --private
git push -u origin main

# 7. Verify
:tree
stats

# 8. Exit
exit
```

---

**📖 For more details, see [FEATURES.md](FEATURES.md)**
