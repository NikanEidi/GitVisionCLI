# 🌟 GitVision CLI Features

**Deep dive into everything GitVisionCLI can do - comprehensive feature documentation.**

<div align="center">

[![Features](https://img.shields.io/badge/Features-50%2B-blue.svg)](https://github.com/NikanEidi/GitVisionCLI)
[![Version](https://img.shields.io/badge/Version-2.0.0-purple.svg)](https://github.com/NikanEidi/GitVisionCLI)

</div>

---

## 📑 **Table of Contents**

- [AI-Powered Editing](#-ai-powered-editing)
- [File Operations](#-file-operations)
- [Folder Operations](#-folder-operations)
- [Line Editing](#-line-editing)
- [Shell Commands](#-shell-commands)
- [Natural Language Commands](#-natural-language-commands)
- [Git Integration](#-git-integration)
- [GitHub Features](#-github-features)
- [UI & Panels](#-ui--panels)
- [Advanced Features](#-advanced-features)
- [Performance](#-performance)
- [Security](#-security)

---

## 🤖 **AI-Powered Editing**

### **Natural Language Processing**

GitVisionCLI understands human language, not rigid syntax:

| You Say | GitVision Does |
|---------|----------------|
| "remove line 5" | Deletes line 5 instantly |
| "add a comment at the top" | Inserts comment at line 1 |
| "explain this function" | AI analyzes and explains |
| "find bugs" | AI scans for issues |
| "refactor this code" | AI suggests improvements |
| "create a test file" | AI generates test file |
| "optimize this" | AI suggests optimizations |

### **Zero Clarification Loops** ✨

**Before (Other Tools):**
```
User: remove line 5
AI: Please specify which file and exact line number
User: app.py line 5  
AI: Please confirm the file path
User: ./app.py line 5
AI: [Finally executes]
```

**GitVisionCLI:**
```
User: remove line 5
AI: [Executes immediately] ✓ Deleted line 5 in app.py
```

**How it works:**
- When a file is open in `:edit`, context is automatically known
- No questions asked - direct execution
- Grammar auto-fix handles broken syntax
- Context-aware inference from project structure

### **Multi-Model Support**

Switch between AI providers seamlessly:

| Provider | Models | Use Case | Streaming | Tools |
|----------|--------|----------|-----------|-------|
| **OpenAI** | GPT-4, GPT-4 Turbo, GPT-4o-mini | Best overall, coding | ✅ Yes | ✅ Yes |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus | Long context, analysis | ✅ Yes | ✅ Yes |
| **Google** | Gemini 1.5 Pro | Fast, multilingual | ✅ Yes | ✅ Yes |
| **Ollama** | Local models (llama2, mistral, etc.) | Private, offline | ✅ Yes | ⚠️ Limited |

**Model Switching:**
```bash
:models                                    # List available
:set-ai openai/gpt-4                      # Switch model
:set-ai anthropic/claude-3-5-sonnet       # Another model
:set-ai gemini-1.5-pro                    # Gemini model
:set-ai llama2                            # Local Ollama model
```

**All models support:**
- ✅ Full streaming (token-by-token)
- ✅ Function calling (where supported)
- ✅ Natural language understanding
- ✅ Context-aware responses
- ✅ Tool execution

### **Context-Aware**

GitVision remembers:
- ✅ Currently open file
- ✅ Project structure
- ✅ Recent edits
- ✅ Git status
- ✅ Active directory
- ✅ Command history

**Example:**
```bash
:edit app.py
remove line 5        # Works on app.py automatically
add comment at top   # Adds to app.py
explain this         # Explains app.py
```

### **Live Streaming Editor**

Watch AI write code token-by-token:

```bash
:live-edit app.py
add a function that calculates fibonacci
```

**Features:**
- Real-time token streaming
- Live editor updates
- Smooth character-by-character display
- No lag or delays
- Proper cleanup on completion

---

## 📝 **File Operations**

### **Smart File Creation**

**Single line:**
```bash
create a file called app.py with print("Hello!")
```

**Multiline with `:ml`:**
```bash
:ml
create a file called server.py with
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello World!"

if __name__ == "__main__":
    app.run(debug=True)
:end
```

**Fenced code blocks:**
````bash
```python
def hello():
    print("World")
```
````

### **Content Normalization**

GitVision automatically:
- ✅ Handles UTF-8 encoding
- ✅ Normalizes line endings (CRLF → LF)
- ✅ Preserves indentation
- ✅ Validates file paths
- ✅ Prevents path traversal attacks

### **Transactional Edits**

All operations are transactional:
- ✅ Rollback on error
- ✅ No partial writes
- ✅ Content integrity guaranteed
- ✅ Atomic file operations
- ✅ Backup creation (optional)

### **File Operations Supported**

| Operation | Command | Example |
|-----------|---------|---------|
| **Create** | `create file <name> with <content>` | `create file app.py with print("Hi")` |
| **Read** | `read file <name>` | `read file app.py` |
| **Delete** | `delete file <name>` | `delete file old.py` |
| **Rename** | `rename <old> to <new>` | `rename app.py to main.py` |
| **Move** | `move <file> to <dest>` | `move app.py to src/` |
| **Copy** | `copy <file> to <dest>` | `copy app.py to backup.py` |
| **Open** | `open <file>` | `open app.py` |
| **View** | `view <file>` | `view README.md` |

---

## 📂 **Folder Operations**

### **Complete Folder Support**

| Operation | Command | Example |
|-----------|---------|---------|
| **Create** | `create folder <name>` | `create folder src` |
| **Delete** | `delete folder <name>` | `delete folder temp` |
| **Move** | `move folder <name> to <dest>` | `move folder src to lib/` |
| **Copy** | `copy folder <name> to <dest>` | `copy folder src to backup/` |
| **Rename** | `rename folder <old> to <new>` | `rename folder old to new` |

**Examples:**
```bash
create folder src
create folder tests and go to it
delete folder temp
move folder src to lib/
copy folder src to backup/
rename folder old_name to new_name
```

---

## ✏️ **Line Editing**

### **Complete Line Editing Support**

When a file is open in `:edit`, all operations are **instant**:

**Delete Operations:**
```bash
remove line 5              # Delete single line
delete line 10             # Same as remove
delete lines 5-10          # Delete range
remove lines 3-7           # Same as delete
```

**Add Operations:**
```bash
add line 1 with # comment  # Insert before line 1
insert line 5 with code     # Same as add
add print("hi") at line 10  # Insert after line 10
insert x = 42 at line 3    # Insert before line 3
```

**Replace Operations:**
```bash
edit line 3 with new code   # Replace line 3
replace line 2 with text   # Same as edit
update line 4 with data     # Same as edit
```

**Append Operations:**
```bash
add print("end") at bottom  # Append to end
append # End to end         # Same as add
```

### **Grammar Auto-Fix**

Broken grammar is automatically fixed:

```bash
remove line1    # → remove line 1
delete ln5      # → delete line 5
rm 2            # → remove line 2 (when file is open)
edit line3      # → edit line 3
add at line10   # → add at line 10
```

### **Pattern Variations**

All these patterns work:

```bash
# Delete
remove line 5
delete line 10
delete lines 1-3
rm 2 (when file is open)

# Add
add line 1 with # comment
insert line 5 with code
write line 10 with data

# Replace
edit line 3 with new
replace line 7 with updated
update line 2 with changed
change line 4 with modified
```

---

## 🐚 **Shell Commands**

### **Complete Shell Command Support**

**40+ shell commands fully supported:**

| Category | Commands | Examples |
|----------|----------|----------|
| **Navigation** | `pwd`, `cd`, `cd..` | `pwd`, `cd src/`, `cd ..` |
| **File Listing** | `ls`, `ll`, `la`, `dir` | `ls`, `ls -la`, `dir` |
| **File Operations** | `cat`, `head`, `tail`, `touch`, `mkdir`, `rm`, `cp`, `mv` | `cat file.txt`, `rm old.txt` |
| **Search & Find** | `grep`, `find`, `which`, `whereis` | `grep "def" app.py`, `find . -name "*.py"` |
| **Text Processing** | `grep`, `sed`, `awk`, `sort`, `uniq`, `wc`, `cut`, `tr` | `grep "error" log.txt`, `sort names.txt` |
| **System Info** | `whoami`, `uname`, `hostname`, `date`, `uptime`, `df`, `du`, `free` | `whoami`, `date`, `df -h` |
| **Process Management** | `ps`, `top`, `kill`, `killall`, `jobs`, `bg`, `fg` | `ps aux`, `kill 1234` |
| **Network** | `ping`, `curl`, `wget`, `netstat`, `ifconfig`, `ip` | `ping google.com`, `curl https://api.example.com` |
| **Archives** | `tar`, `zip`, `unzip`, `gzip`, `gunzip` | `tar -czf backup.tar.gz src/` |
| **Package Managers** | `pip`, `npm`, `yarn`, `brew`, `apt`, `yum` | `pip install requests`, `npm install express` |
| **Debugging** | `python`, `python3`, `node`, `debug`, `test` | `python app.py`, `node server.js` |
| **Utilities** | `clear`, `history`, `alias`, `export`, `env`, `echo`, `printenv` | `clear`, `history` |

**Direct Execution:**
```bash
ls                    # Works directly
cd src/               # Works directly
grep "def" app.py     # Works directly
python app.py         # Works directly
```

**Prefix for Explicit Shell:**
```bash
.ls -la               # Explicit shell command
.cat file.txt         # Explicit shell command
```

---

## 🗣️ **Natural Language Commands**

### **File Operations**

```bash
list files in <dir>              # List directory
list files                       # List current directory
show files in <dir>              # Same as list
display files                    # Same as list
```

### **Search & Find**

```bash
search for <text>                # Search for text
search for <text> in <file>      # Search in file
find files named <name>          # Find files by name
find files called <name>         # Same as named
```

### **Debug & Run**

```bash
run <script>                     # Run script (auto-detects type)
execute <script>                 # Same as run
launch <script>                  # Same as run
debug <file>                     # Debug file
test <file>                      # Test file
```

**Auto-Detection:**
- `.py` files → `python3 <file>`
- `.js` files → `node <file>`
- `.sh` files → `bash <file>`
- Other → Generic execution

### **Navigation**

```bash
navigate to <path>               # Change directory
go to <path>                     # Same as navigate
go into <folder>                 # Same as navigate
enter <folder>                   # Same as navigate
cd ..                            # Go up directory
```

---

## 🌳 **Git Integration**

### **Complete Git Workflow**

| Operation | Command | Description |
|-----------|---------|-------------|
| **Init** | `git init` | Initialize repository |
| **Stage** | `git add .` | Stage all changes |
| **Commit** | `git commit "msg"` | Commit with message |
| **Branch** | `git branch name` | Create branch |
| **Checkout** | `git checkout name` | Switch branch |
| **Merge** | `git merge name` | Merge branches |
| **Push** | `git push` | Push to remote |
| **Pull** | `git pull` | Pull from remote |
| **Status** | `git status` | Check status |
| **Log** | `git log` | View history |
| **Remote** | `git remote add <name> <url>` | Add remote |

### **Visual Git Graph** 📊

`:git-graph` shows beautiful ASCII commit tree:

```
*   commit abc123 (HEAD -> main)
|\  Merge: def456 + ghi789
| |
| * commit ghi789 (feature)
| | Add feature
|/
* commit def456
| Update docs
*
```

**Features:**
- ASCII art visualization
- Branch visualization
- Commit details
- Up to 50 recent commits
- All branches shown

### **Integrated Status**

Git status is always visible:
- Current branch in status bar
- Uncommitted changes count
- Remote sync status
- Last commit info

---

## 🐙 **GitHub Features**

### **Direct Repository Management**

**Create private repo:**
```bash
create github repo my-secret-project --private
```

**Create public repo:**
```bash
create github repo my-opensource-lib --public
```

### **Issue Management**

```bash
# Simple issue
create github issue "Bug: Login broken"

# Issue with body
create github issue "Bug: Login broken" --body "Users can't log in with OAuth"
```

### **Pull Requests**

```bash
# From feature branch
git checkout feature-auth
git push origin feature-auth
create github pr "Add OAuth authentication" --head feature-auth --base main
```

### **Seamless Integration**

Set once, use forever:
```bash
export GITHUB_TOKEN="ghp_xxxxx"
```

Then:
- ✅ Auto-authentication
- ✅ Private repo access
- ✅ Organization support
- ✅ No manual browser needed

---

## 🎨 **UI & Panels**

### **Dual-Panel Layout**

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

### **Banner Panel** (`:banner`)

Quick command reference with:
- 📁 File operations
- 🤖 AI commands
- ⚙️ System controls
- 🎨 Beautiful logo

### **Command Sheet** (`:sheet`)

Comprehensive reference with:
- All commands organized by category
- Keyboard shortcuts
- Git commands
- AI tips
- Shell commands
- Natural language patterns

### **File Tree** (`:tree`)

Interactive file browser:
- Navigate directories
- View file structure
- Color-coded file types
- Enhanced icons
- Stats display

### **Editor Panel** (`:edit <file>`)

Code editor with:
- Line numbers (vibrant colors)
- Syntax-aware
- Instant editing
- Real-time updates
- ANSI-aware truncation
- Footer with file info

### **Live Editor** (`:live-edit <file>`)

AI live editor with:
- Token-by-token streaming
- Real-time updates
- Smooth character display
- Proper cleanup

### **Git Graph** (`:git-graph`)

Visual commit history:
- ASCII art tree
- Branch visualization
- Commit details
- Enhanced styling

### **Model Manager** (`:models`)

AI model manager:
- List all providers
- Show configured models
- Display current model
- Switch models easily

### **Markdown Panel** (`:markdown <file>`)

Rendered markdown preview:
- Headers with gradient effects
- Lists with colored bullets
- Enhanced formatting
- Beautiful styling

---

## 🔥 **Advanced Features**

### **Line Editing Patterns**

All these patterns work:

```bash
# Delete
remove line 5
delete line 10
delete lines 1-3

# Add
add line 1 with # comment
insert line 5 with code
write line 10 with data

# Replace
edit line 3 with new
replace line 7 with updated
update line 2 with changed
change line 4 with modified
```

### **Search & Analysis**

```bash
search for "TODO" in project
search for "def" in app.py
find files named "test"
```

### **Code Understanding**

```bash
explain the file app.py
analyze this code
how does this function work?
what are the design patterns here?
```

### **Code Generation**

```bash
create a test file for app.py
add error handling to this function
refactor this code for readability
optimize this algorithm
```

### **Workspace Stats**

```bash
stats
```

Shows:
- File count
- Git status
- Current branch
- Uncommitted changes
- Last commit
- Current directory

---

## ⚡ **Performance**

### **Fast Operations**

| Operation | Speed |
|-----------|-------|
| Line edit | Instant |
| File create | < 100ms |
| Git status | < 50ms |
| Panel switch | Instant |
| AI response | 1-3s (model-dependent) |
| Streaming | Real-time (token-by-token) |

### **Efficient Rendering**

- No flicker
- No duplicate panels
- Smooth transitions
- Minimal redraws
- ANSI-aware rendering
- Proper screen clearing

---

## 🔐 **Security**

### **Local-First**

- ✅ API keys in environment variables
- ✅ No data sent except to chosen AI provider
- ✅ Git credentials stay in Git config
- ✅ GitHub token never logged
- ✅ Path sandboxing enforced

### **Safe Operations**

- ✅ Transactional file operations
- ✅ Rollback on errors
- ✅ Path escape detection
- ✅ Content validation
- ✅ Sandbox enforcement
- ✅ No arbitrary code execution (without explicit shell commands)

---

## 🎯 **Use Cases Matrix**

| Use Case | Features Used | Time Saved |
|----------|---------------|------------|
| **Quick Bug Fix** | Edit file, Git commit, push | 5 min → 1 min |
| **New Feature** | Create files, AI help, Git branch | 30 min → 15 min |
| **Code Review** | AI analysis, Git graph, explain | 20 min → 10 min |
| **Learning** | AI explanations, examples | N/A |
| **Prototyping** | Fast file creation, AI generation | 2 hr → 1 hr |
| **Debugging** | Run, debug, find bugs, fix | 30 min → 10 min |
| **Search** | Search files, find patterns | 5 min → 30 sec |

---

## 🚀 **What's Next?**

Planned features:
- [ ] Syntax highlighting in editor
- [ ] Collaborative editing
- [ ] Plugin system
- [ ] Custom AI prompts
- [ ] Enhanced Git visualization
- [ ] Conflict resolution UI
- [ ] Performance profiling tools
- [ ] Multi-file editing support
- [ ] Advanced search and replace
- [ ] Code snippets and templates

---

**Explore more: [COMMANDS.md](COMMANDS.md) | [QUICKSTART.md](QUICKSTART.md)**

**Version**: 2.0.0  
**Last Updated**: 2024-12-XX
