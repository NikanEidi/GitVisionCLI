# 📋 GitVisionCLI - Complete Command Reference

**The Ultimate Command Sheet - All Commands in One Place**

<div align="center">

[![Commands](https://img.shields.io/badge/Commands-100%2B-blue.svg)](https://github.com/NikanEidi/GitVisionCLI)
[![Version](https://img.shields.io/badge/Version-2.0.0-purple.svg)](https://github.com/NikanEidi/GitVisionCLI)

</div>

---

## 📑 **Quick Navigation**

| Section | Commands | Page |
|---------|----------|------|
| [Panel Commands](#-panel-commands) | `:banner`, `:tree`, `:edit`, `:sheet`, etc. | ⬇️ |
| [File Operations](#-file-operations) | `create`, `read`, `delete`, `rename`, etc. | ⬇️ |
| [Line Editing](#-line-editing) | `remove line`, `add line`, `replace line`, etc. | ⬇️ |
| [Git Commands](#-git-commands) | `git init`, `git add`, `git commit`, etc. | ⬇️ |
| [GitHub Commands](#-github-commands) | `create github repo`, `create github issue`, etc. | ⬇️ |
| [AI Commands](#-ai-commands) | `:models`, `:set-ai`, `explain`, etc. | ⬇️ |
| [Shell Commands](#-shell-commands) | `ls`, `cd`, `cat`, `grep`, etc. | ⬇️ |

---

## 🎛️ **Panel Commands**

**Control the UI and navigate between panels**

| Command | Description | Example |
|---------|-------------|---------|
| `:banner` | Show workspace banner with quick commands | `:banner` |
| `:tree` | Open file tree browser | `:tree` |
| `:edit <file>` | Open file in code editor | `:edit app.py` |
| `:live-edit <file>` | AI live editor with streaming | `:live-edit app.py` |
| `:markdown <file>` | Preview markdown file | `:markdown README.md` |
| `:sheet` | Show complete command reference | `:sheet` |
| `:git-graph` | Visual Git commit history | `:git-graph` |
| `:models` | AI model manager | `:models` |
| `:save` | Save current editor buffer | `:save` |
| `:close` | Close current panel | `:close` |

**Usage:**
```bash
:banner          # Show quick commands
:tree            # Browse project files
:edit app.py     # Open in editor
:git-graph       # View commits
:models          # Manage AI
:close           # Close panel
```

---

## 📁 **File Operations**

### **Create Files**

**Single line:**
```bash
create file <name> with <content>
create a file called <name> with <content>
```

**Examples:**
```bash
create file app.py with print("Hello World!")
create a file called config.json with {"key": "value"}
```

**Multiline (use `:ml` mode):**
```bash
:ml
create a file called <name> with
<line 1>
<line 2>
<more lines>
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
read <name>
open <name>
```

**Examples:**
```bash
read file app.py
read config.json
open README.md
```

### **Delete Files**

```bash
delete file <name>
remove file <name>
erase <name>
trash <name>
```

**Examples:**
```bash
delete file old.py
remove file temp.txt
erase backup.py
```

### **Rename Files**

```bash
rename <old> to <new>
rename file <old> to <new>
```

**Examples:**
```bash
rename app.py to main.py
rename file old.txt to new.txt
```

### **Move Files**

```bash
move <file> to <folder>
move file <file> to <folder>
```

**Examples:**
```bash
move app.py to src/
move file config.json to config/
```

### **Copy Files**

```bash
copy <file> to <new>
copy file <file> to <new>
```

**Examples:**
```bash
copy app.py to app_backup.py
copy file config.json to config_backup.json
```

---

## 📂 **Folder Operations**

| Command | Description | Example |
|---------|-------------|---------|
| `create folder <name>` | Create directory | `create folder src` |
| `delete folder <name>` | Delete directory | `delete folder old` |
| `rename folder <old> to <new>` | Rename folder | `rename src to lib` |
| `move folder <path> to <target>` | Move folder | `move src to lib` |
| `copy folder <path> to <new>` | Copy folder | `copy src to src_backup` |

**Examples:**
```bash
create folder src
create folder tests/unit
delete folder old
rename folder src to lib
move folder src to lib
copy folder src to src_backup
```

---

## ✏️ **Line Editing**

**⚠️ Prerequisite:** Open file first with `:edit <filename>`

### **Delete Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `remove line N` | Delete line N | `remove line 5` |
| `delete line N` | Delete line N | `delete line 10` |
| `rm N` | Short form | `rm 5` |
| `delete lines N-M` | Delete range | `delete lines 5-10` |
| `remove lines N to M` | Delete range | `remove lines 3 to 7` |
| `delete lines N through M` | Delete range | `delete lines 2 through 8` |

**Examples:**
```bash
:edit app.py
remove line 5
delete line 10
rm 3                    # Short form
delete lines 5-10
remove lines 3 to 7
```

### **Insert Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `add <text> at line N` | Insert after line N | `add print("hi") at line 10` |
| `insert <text> at line N` | Insert before line N | `insert import os at line 1` |
| `add line N with <text>` | Insert before line N | `add line 1 with # comment` |
| `insert line N with <text>` | Insert before line N | `insert line 5 with x = 42` |
| `add <text> at top` | Insert at beginning | `add # -*- coding: utf-8 -*- at top` |
| `add <text> at bottom` | Append to end | `add print("end") at bottom` |

**Examples:**
```bash
:edit app.py
add # comment at line 1
insert import os at line 1
add line 5 with x = 42
add print("test") at bottom
```

### **Replace Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `replace line N with <text>` | Replace line N | `replace line 3 with x = 100` |
| `edit line N with <text>` | Replace line N | `edit line 3 with new code` |
| `update line N with <text>` | Replace line N | `update line 4 with data = []` |

**Examples:**
```bash
:edit app.py
replace line 3 with x = 100
edit line 2 with print("Updated!")
update line 4 with data = []
```

### **Grammar Auto-Fix**

Broken grammar is automatically fixed:
- `line1` → `line 1`
- `ln5` → `line 5`
- `rm 2` → `remove line 2`
- `delete ln3-7` → `delete lines 3-7`

---

## 🔁 **Git Commands**

### **Repository Management**

| Command | Description | Example |
|---------|-------------|---------|
| `git init` | Initialize repository | `git init` |
| `git status` | Show status | `git status` |
| `git log` | Show commit history | `git log` |

### **Staging & Committing**

| Command | Description | Example |
|---------|-------------|---------|
| `git add <files>` | Stage files | `git add app.py` |
| `git add .` | Stage all files | `git add .` |
| `git commit "message"` | Commit changes | `git commit "Initial commit"` |
| `git commit -m "message"` | Commit with message | `git commit -m "Fix bug"` |

**Examples:**
```bash
git init
git add .
git commit "Initial commit"
git add app.py
git commit "Add app.py"
```

### **Branching**

| Command | Description | Example |
|---------|-------------|---------|
| `git branch <name>` | Create branch | `git branch feature` |
| `git checkout <branch>` | Switch branch | `git checkout main` |
| `git checkout -b <branch>` | Create and switch | `git checkout -b feature` |
| `go to <branch>` | Switch branch (NL) | `go to main` |
| `git merge <branch>` | Merge branch | `git merge feature` |

**Examples:**
```bash
git branch feature
git checkout feature
git checkout -b hotfix
go to main
git merge feature
```

### **Remote Operations**

| Command | Description | Example |
|---------|-------------|---------|
| `git push` | Push to remote | `git push` |
| `git push origin main` | Push to specific remote/branch | `git push origin main` |
| `git push -u origin main` | Push and set upstream | `git push -u origin main` |
| `git pull` | Pull from remote | `git pull` |
| `git pull origin main` | Pull from specific remote/branch | `git pull origin main` |
| `git remote add <name> <url>` | Add remote | `git remote add origin https://...` |

**Examples:**
```bash
git remote add origin https://github.com/user/repo.git
git push -u origin main
git pull origin main
```

### **Visualization**

| Command | Description | Example |
|---------|-------------|---------|
| `:git-graph` | Open Git graph panel | `:git-graph` |
| `git graph` | Open Git graph (NL) | `git graph` |

---

## 🐙 **GitHub Commands**

**⚠️ Requires:** `GITHUB_TOKEN` environment variable

### **Repository Management**

| Command | Description | Example |
|---------|-------------|---------|
| `create github repo <name>` | Create public repo | `create github repo my-app` |
| `create github repo <name> --private` | Create private repo | `create github repo my-app --private` |
| `create github repo <name> private` | Create private repo | `create github repo my-app private` |

**Examples:**
```bash
create github repo my-project
create github repo my-project --private
create github repo my-project private
```

### **Issues & Pull Requests**

| Command | Description | Example |
|---------|-------------|---------|
| `create github issue "title"` | Create issue | `create github issue "Bug fix"` |
| `create github issue "title" --body "desc"` | Create issue with body | `create github issue "Bug" --body "Description"` |
| `create github pr "title"` | Create pull request | `create github pr "New feature"` |

**Examples:**
```bash
create github issue "Fix bug in login"
create github issue "Enhancement" --body "Add new feature"
create github pr "Add authentication"
```

---

## 🤖 **AI Commands**

### **Model Management**

| Command | Description | Example |
|---------|-------------|---------|
| `:models` | Show all available models | `:models` |
| `:set-ai <model>` | Switch AI model | `:set-ai gpt-4o-mini` |
| `stats` | Show current model stats | `stats` |

**Available Models:**
```bash
:set-ai gpt-4o-mini        # OpenAI GPT-4o Mini
:set-ai gpt-4o             # OpenAI GPT-4o
:set-ai gemini-1.5-pro     # Google Gemini 1.5 Pro
:set-ai claude-3.5-sonnet  # Anthropic Claude 3.5 Sonnet
:set-ai ollama/llama2      # Ollama (local)
```

### **AI Interactions**

| Command | Description | Example |
|---------|-------------|---------|
| `explain <file>` | Explain code | `explain app.py` |
| `analyze this code` | Analyze current code | `analyze this code` |
| `find bugs` | Find bugs | `find bugs` |
| `refactor this` | Refactor code | `refactor this` |
| `optimize this code` | Optimize code | `optimize this code` |
| `create test for <file>` | Generate tests | `create test for app.py` |

**Examples:**
```bash
explain app.py
how can I improve this code?
find bugs in this file
refactor this function
create a test file for app.py
```

### **Ollama Commands** (Local AI)

```bash
ollama models              # List installed models
ollama pull <model>        # Install model
ollama pull llama2         # Example
```

---

## 🐚 **Shell Commands**

**All standard shell commands are fully supported!**

### **Navigation**

```bash
pwd                    # Print working directory
cd <path>              # Change directory
cd ..                  # Go up one level
```

### **File Operations**

```bash
ls                     # List files
ll                     # List files (long)
cat <file>             # View file
head <file>            # View first lines
tail <file>            # View last lines
touch <file>           # Create empty file
mkdir <dir>            # Create directory
rm <file>              # Delete file
cp <src> <dst>         # Copy file
mv <src> <dst>         # Move file
```

### **Search & Find**

```bash
grep <pattern> <file>  # Search in file
find <name>            # Find files
search for <text>      # Search (NL)
find files named <name> # Find files (NL)
```

### **Text Processing**

```bash
grep <pattern>         # Search text
sed <command>          # Stream editor
awk <script>           # Text processing
sort                   # Sort lines
wc                     # Word count
cut                    # Cut columns
```

### **System**

```bash
whoami                 # Current user
uname                  # System info
date                   # Current date
ps                     # Process list
top                    # Process monitor
```

---

## 📄 **Multi-line Input**

### **Manual Multi-line Mode**

```bash
:ml
<your content>
<multiple lines>
:end
```

**Example:**
```bash
:ml
create a file called app.py with
def main():
    print("Hello!")
    return 0

if __name__ == "__main__":
    main()
:end
```

### **Fenced Code Blocks**

You can paste code blocks directly:

````bash
```python
def hello():
    print("World")
```
````

These are automatically treated as single messages.

---

## ⌨️ **Keyboard Shortcuts**

| Shortcut | Description |
|----------|-------------|
| `Ctrl+C` | Cancel current operation / exit multi-line mode |
| `Ctrl+D` | Exit GitVision (or use `exit`/`quit` command) |
| `↑ / ↓` | Navigate command history |
| `Tab` | Autocomplete (if available) |

---

## 🎯 **Quick Reference**

### **Most Used Commands**

```bash
# Launch
gitvision

# Panels
:banner          # Quick commands
:tree            # File browser
:edit <file>     # Code editor
:git-graph       # Git visualization
:models          # AI manager

# File Ops
create file <name> with <content>
read file <name>
delete file <name>

# Line Editing (after :edit)
remove line N
add <text> at line N
replace line N with <text>

# Git
git init
git add .
git commit "message"
git push

# GitHub
create github repo <name> --private
```

---

## 📚 **Complete Action Types**

GitVisionCLI supports **50+ action types**:

### **Filesystem Actions**
- `CreateFile`, `ReadFile`, `DeleteFile`
- `RenameFile`, `MoveFile`, `CopyFile`
- `CreateFolder`, `DeleteFolder`, `MoveFolder`, `CopyFolder`

### **Line Operations**
- `InsertBeforeLine`, `InsertAfterLine`
- `ReplaceLine`, `DeleteLineRange`
- `InsertAtTop`, `InsertAtBottom`
- `AppendText`, `PrependText`

### **Git Actions**
- `GitInit`, `GitAdd`, `GitCommit`
- `GitPush`, `GitPull`
- `GitBranch`, `GitCheckout`, `GitMerge`
- `GitRemote`

### **GitHub Actions**
- `GitHubCreateRepo`, `GitHubDeleteRepo`
- `GitHubCreateIssue`, `GitHubCreatePR`

### **Advanced Actions**
- `ReplaceByPattern`, `DeleteByPattern`
- `ReplaceBlock`, `InsertBlock`, `RemoveBlock`
- `UpdateJSONKey`, `UpdateYAMLKey`
- `InsertIntoFunction`, `InsertIntoClass`
- `AddDecorator`, `AddImport`

---

## 💡 **Tips & Tricks**

1. **No Clarification Questions**: When a file is open, AI never asks "which file?"
2. **Grammar Auto-Fix**: Broken grammar is automatically fixed (`line1` → `line 1`)
3. **Streaming Writes**: AI text streams token-by-token into editor
4. **Multi-line Input**: Use `:ml` for multi-line content
5. **Context-Aware**: Remembers open files, project structure, recent edits
6. **Natural Language**: Speak naturally, GitVision understands

---

## 🔗 **More Documentation**

- **[README.md](README.md)** - Main project documentation
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Quick start guide
- **[COMMANDS.md](docs/COMMANDS.md)** - Detailed command docs
- **[FEATURES.md](docs/FEATURES.md)** - Feature overview
- **[RUN_AND_TEST.md](docs/RUN_AND_TEST.md)** - Testing guide

---

**Last Updated**: 2024-12-XX  
**Version**: 2.0.0

