# 📚 Complete Command Reference

**All GitVisionCLI commands in one place - comprehensive guide with examples.**

<div align="center">

[![Commands](https://img.shields.io/badge/Commands-100%2B-blue.svg)](https://github.com/NikanEidi/GitVisionCLI)
[![Version](https://img.shields.io/badge/Version-1.1.0-purple.svg)](https://github.com/NikanEidi/GitVisionCLI)

</div>

---

## 📑 **Table of Contents**

- [Panel Commands](#-panel-commands)
- [File Operations](#-file-operations)
- [Folder Operations](#-folder-operations)
- [Line Editing](#-line-editing)
- [Shell Commands](#-shell-commands)
- [Natural Language Commands](#-natural-language-commands)
- [Git Commands](#-git-commands)
- [GitHub Integration](#-github-integration)
- [AI Commands](#-ai-commands)
- [Navigation & Utilities](#-navigation--utilities)
- [Multiline Mode](#-multiline-mode)
- [Complete Workflows](#-complete-workflows)

---

## 🎨 **Panel Commands**

### **Panel Navigation**

| Command | Panel | Description | Example |
|---------|-------|-------------|---------|
| `:banner` | Banner | Quick commands and logo | `:banner` |
| `:sheet` | Sheet | Full command reference | `:sheet` |
| `:tree` | Tree | File browser | `:tree` |
| `:git-graph` | Git Graph | Visual commit history | `:git-graph` |
| `:edit <file>` | Editor | Code editor with line numbers | `:edit app.py` |
| `:live-edit <file>` | Live Editor | AI live editor with streaming | `:live-edit app.py` |
| `:markdown <file>` | Markdown | Rendered markdown preview | `:markdown README.md` |
| `:models` | Models | AI model manager | `:models` |
| `:close` | Close | Close current panel | `:close` |

**Examples:**
```bash
:banner          # Show banner
:sheet           # Show command sheet
:tree            # Browse files
:edit app.py     # Open editor
:git-graph       # View commits
:models          # Manage AI
:close           # Close panel
```

---

## 📁 **File Operations**

### **Create Files**

**Single line:**
```bash
create a file called <name> with <content>
```

**Examples:**
```bash
create a file called hello.py with print("Hello World!")
create a file called config.json with {"key": "value"}
create a file called README.md with # My Project
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

**Examples:**
```bash
read file app.py
read file config.json
read file README.md
```

### **Delete Files**

```bash
delete file <name>
```

**Examples:**
```bash
delete file old_file.py
delete file temp.txt
```

### **Rename Files**

```bash
rename <old_name> to <new_name>
```

**Examples:**
```bash
rename app.py to main.py
rename old.txt to new.txt
```

### **Move Files**

```bash
move <file> to <destination>
```

**Examples:**
```bash
move app.py to src/
move config.json to config/
```

### **Copy Files**

```bash
copy <file> to <destination>
```

**Examples:**
```bash
copy app.py to app_backup.py
copy config.json to config/config.json
```

### **Open Files**

```bash
open <file>
view <file>
edit <file>
```

**Examples:**
```bash
open app.py
view README.md
edit config.json
```

---

## 📂 **Folder Operations**

### **Create Folders**

```bash
create folder <name>
create directory <name>
mkdir <name>
```

**Examples:**
```bash
create folder src
create directory tests
mkdir config
```

### **Delete Folders**

```bash
delete folder <name>
delete directory <name>
rmdir <name>
```

**Examples:**
```bash
delete folder temp
delete directory old_files
```

### **Move Folders**

```bash
move folder <name> to <destination>
```

**Examples:**
```bash
move folder src to lib/
```

### **Copy Folders**

```bash
copy folder <name> to <destination>
```

**Examples:**
```bash
copy folder src to backup/
```

### **Rename Folders**

```bash
rename folder <old> to <new>
```

**Examples:**
```bash
rename folder old_name to new_name
```

---

## ✏️ **Line Editing**

**Prerequisites:** Open file in editor first with `:edit <filename>`

### **Delete Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `remove line N` | Delete line N | `remove line 5` |
| `delete line N` | Delete line N | `delete line 10` |
| `delete lines N-M` | Delete range | `delete lines 5-10` |
| `remove lines N-M` | Delete range | `remove lines 3-7` |

**Examples:**
```bash
:edit app.py
remove line 5
delete line 10
delete lines 5-10
remove lines 3-7
```

### **Add Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `add line N with TEXT` | Insert before line N | `add line 1 with # comment` |
| `insert line N with TEXT` | Insert before line N | `insert line 5 with x = 42` |
| `add TEXT at line N` | Insert after line N | `add print("hi") at line 10` |
| `insert TEXT at line N` | Insert before line N | `insert x = 100 at line 5` |

**Examples:**
```bash
:edit app.py
add line 1 with # -*- coding: utf-8 -*-
insert line 5 with import os
add print("test") at line 10
insert x = 42 at line 3
```

### **Edit/Replace Lines**

| Command | Description | Example |
|---------|-------------|---------|
| `edit line N with TEXT` | Replace line N | `edit line 3 with y = 100` |
| `replace line N with TEXT` | Replace line N | `replace line 2 with new code` |
| `update line N with TEXT` | Replace line N | `update line 4 with data = []` |

**Examples:**
```bash
:edit app.py
edit line 3 with y = 100
replace line 2 with print("Updated!")
update line 4 with data = []
```

### **Append to End**

```bash
add <text> at bottom
append <text> to end
```

**Examples:**
```bash
:edit app.py
add print("End") at bottom
append # End of file to end
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

**Examples:**
```bash
pwd
cd src/
cd ../other-project
cd ..
```

### **File Listing**

```bash
ls                     # List files
ll                     # List files (long format)
la                     # List all files (including hidden)
dir                    # List files (Windows)
```

**Examples:**
```bash
ls
ls -la
ll
dir
```

### **File Operations**

```bash
cat <file>             # View file
head <file>            # View first lines
tail <file>            # View last lines
touch <file>           # Create empty file
mkdir <dir>            # Create directory
rm <file>              # Delete file
cp <src> <dst>         # Copy file
mv <src> <dst>         # Move file
```

**Examples:**
```bash
cat app.py
head -n 10 app.py
tail -n 5 app.py
touch new_file.txt
mkdir new_dir
rm old_file.txt
cp app.py app_backup.py
mv old.txt new.txt
```

### **Search & Find**

```bash
grep <pattern> <file>  # Search in file
grep -r <pattern> .    # Search recursively
find . -name <name>    # Find files by name
which <command>        # Find command location
whereis <command>      # Find command
```

**Examples:**
```bash
grep "def" app.py
grep -r "TODO" .
find . -name "*.py"
which python
whereis python
```

### **Text Processing**

```bash
grep <pattern>         # Search text
sed <command>          # Stream editor
awk <script>           # Text processing
sort <file>            # Sort lines
uniq <file>            # Remove duplicates
wc <file>              # Word count
cut <options>          # Cut columns
tr <options>           # Translate characters
```

**Examples:**
```bash
grep "error" log.txt
sed 's/old/new/g' file.txt
awk '{print $1}' data.txt
sort names.txt
uniq list.txt
wc -l file.txt
```

### **System Info**

```bash
whoami                 # Current user
uname                  # System info
hostname               # Hostname
date                   # Current date
uptime                 # System uptime
df                     # Disk usage
du                     # Directory usage
free                   # Memory usage
```

**Examples:**
```bash
whoami
uname -a
hostname
date
uptime
df -h
du -sh .
free -h
```

### **Process Management**

```bash
ps                     # List processes
top                    # Process monitor
kill <pid>             # Kill process
killall <name>         # Kill all by name
jobs                   # List jobs
bg                     # Background job
fg                     # Foreground job
```

**Examples:**
```bash
ps aux
top
kill 1234
killall python
jobs
bg %1
fg %1
```

### **Network**

```bash
ping <host>            # Ping host
curl <url>             # HTTP request
wget <url>             # Download file
netstat                # Network stats
ifconfig               # Network config
ip                     # IP commands
```

**Examples:**
```bash
ping google.com
curl https://api.example.com
wget https://example.com/file.zip
netstat -an
ifconfig
ip addr
```

### **Archives**

```bash
tar -czf <archive> <files>  # Create tar.gz
tar -xzf <archive>          # Extract tar.gz
zip <archive> <files>       # Create zip
unzip <archive>            # Extract zip
gzip <file>                 # Compress
gunzip <file>               # Decompress
```

**Examples:**
```bash
tar -czf backup.tar.gz src/
tar -xzf backup.tar.gz
zip archive.zip file1 file2
unzip archive.zip
gzip large_file.txt
gunzip large_file.txt.gz
```

### **Package Managers**

```bash
pip install <package>  # Python package
npm install <package>  # Node package
yarn add <package>     # Yarn package
brew install <package> # Homebrew
apt install <package>  # Debian/Ubuntu
yum install <package>  # RedHat/CentOS
```

**Examples:**
```bash
pip install requests
npm install express
yarn add react
brew install git
apt install vim
yum install python3
```

### **Debugging**

```bash
python <file>          # Run Python
python3 <file>         # Run Python 3
node <file>            # Run Node.js
debug <file>           # Debug file
test <file>            # Test file
```

**Examples:**
```bash
python app.py
python3 server.py
node index.js
debug buggy.py
test test_suite.py
```

### **Utilities**

```bash
clear                  # Clear screen
history                # Command history
alias                  # List aliases
export <var>=<value>   # Set environment variable
env                    # List environment variables
echo <text>            # Print text
printenv               # Print environment
```

**Examples:**
```bash
clear
history
alias
export PATH="$PATH:/new/path"
env
echo "Hello"
printenv
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

**Examples:**
```bash
list files in src/
list files
show files in tests/
display files
```

### **Search & Find**

```bash
search for <text>                # Search for text
search for <text> in <file>      # Search in file
find files named <name>          # Find files by name
find files called <name>         # Same as named
```

**Examples:**
```bash
search for "TODO"
search for "def" in app.py
find files named "test"
find files called "config"
```

### **Debug & Run**

```bash
run <script>                     # Run script (auto-detects type)
execute <script>                 # Same as run
launch <script>                  # Same as run
debug <file>                     # Debug file
test <file>                      # Test file
```

**Examples:**
```bash
run app.py                       # Auto-detects Python
run server.js                    # Auto-detects Node
run script.sh                    # Auto-detects Bash
debug buggy.py
test test_suite.py
```

### **Navigation**

```bash
navigate to <path>               # Change directory
go to <path>                     # Same as navigate
go into <folder>                 # Same as navigate
enter <folder>                   # Same as navigate
```

**Examples:**
```bash
navigate to src/
go to tests/
go into config/
enter project/
```

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
git add all              # Same as .
```

**Examples:**
```bash
git add app.py
git add .
git add src/
```

### **Committing**

```bash
git commit "<message>"
```

**Examples:**
```bash
git commit "Initial commit"
git commit "Add new feature"
git commit "Fix bug in authentication"
```

### **Status & History**

```bash
git status               # Check repository status
git log                  # View commit history
:git-graph              # Visual commit graph
```

**Examples:**
```bash
git status
git log
git log --oneline
:git-graph
```

### **Branching**

```bash
git branch <name>        # Create branch
git checkout <name>       # Switch branch
git merge <name>         # Merge branch
```

**Examples:**
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
git remote add <name> <url>  # Add remote
```

**Examples:**
```bash
git push
git pull
git push -u origin main
git push origin feature
git remote add origin https://github.com/user/repo.git
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
create github repo <name> private
create github repo <name> public
```

**Examples:**
```bash
create github repo my-awesome-project --private
create github repo my-opensource-lib --public
create github repo secret-project private
```

### **Create Issue**

```bash
create github issue "<title>"
create github issue "<title>" --body "<description>"
```

**Examples:**
```bash
create github issue "Bug: Login fails"
create github issue "Feature: Add dark mode" --body "Users want dark mode support"
```

### **Create Pull Request**

```bash
create github pr "<title>"
create github pr "<title>" --head <branch> --base <target>
```

**Examples:**
```bash
create github pr "Add authentication"
create github pr "Fix bug" --head feature-fix --base main
```

---

## 🤖 **AI Commands**

### **Code Analysis**

```bash
explain the file <name>
explain <file>
analyze this code
find bugs in this file
find bugs
```

**Examples:**
```bash
explain the file app.py
explain app.py
analyze this code
find bugs in this file
find bugs
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
optimize this algorithm
```

### **Model Management**

```bash
:models                          # List available models
:set-ai <model>                  # Switch model
stats                           # Show model stats
```

**Examples:**
```bash
:models
:set-ai gpt-4o-mini
:set-ai gemini-1.5-pro
:set-ai claude-3-5-sonnet
:set-ai llama2
stats
```

**Available Models:**
- OpenAI: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- Gemini: `gemini-1.5-pro`
- Claude: `claude-3-5-sonnet`, `claude-3-opus`
- Ollama: Any local model (e.g., `llama2`, `mistral`)

---

## 🧭 **Navigation & Utilities**

### **Navigation**

```bash
cd <path>                # Change directory
cd ..                    # Go up one level
pwd                      # Print working directory
```

**Examples:**
```bash
cd src/
cd ../other-project
cd ..
pwd
```

### **Information**

```bash
stats                    # Workspace statistics
clear                    # Clear console
```

**Examples:**
```bash
stats
clear
```

### **Exit**

```bash
exit
quit
```

---

## 📝 **Multiline Mode**

### **Using `:ml`**

```bash
:ml
<your content>
<multiple lines>
:end
```

**Example:**
```bash
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

### **Fenced Code Blocks**

````bash
```python
def hello():
    print("World")
```
````

---

## 💡 **Pro Tips**

### **Natural Language**

Be conversational! GitVision understands:

✅ `remove line 5`  
✅ `delete that line`  
✅ `add a comment at the top`  
✅ `explain this function`  
✅ `find bugs`  
✅ `refactor this`

### **Context-Aware Editing**

When file is open in `:edit`, chain edits:

```bash
:edit app.py
add line 1 with # comment
edit line 5 with new code
remove line 10
git add app.py
git commit "Updates"
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

### **Shell Command Prefixes**

Use `.` prefix for direct shell execution:

```bash
.pwd            # Direct shell command
.ls -la         # Direct shell command
.cat file.txt   # Direct shell command
```

### **Cross-OS Commands**

Use prefixes for cross-platform commands:

```bash
p.clear         # POSIX clear
c.dir           # CMD dir
l.ls            # Linux ls
m.say "hi"      # macOS say
```

---

## 🎯 **Complete Workflow Examples**

### **Workflow 1: New Project Setup**

```bash
# 1. Launch
gitvision

# 2. Initialize project
git init

# 3. Create README
:ml
create a file called README.md with
# My Project
Description here
:end

# 4. Create main file
create a file called main.py with print("Hello!")

# 5. Stage and commit
git add .
git commit "Initial commit"

# 6. View graph
:git-graph
```

### **Workflow 2: Edit Existing Project**

```bash
# 1. Open file
:edit app.py

# 2. Make edits (no filename needed!)
add line 1 with # Updated
edit line 5 with print("New code")
remove line 10

# 3. Save
:save

# 4. Commit
git add app.py
git commit "Update app"
```

### **Workflow 3: GitHub Integration**

```bash
# 1. Set token
export GITHUB_TOKEN="ghp_..."

# 2. Create repo
create github repo my-project --private

# 3. Push code
git push -u origin main

# 4. Create issue
create github issue "Bug: Fix path doubling"

# 5. Create PR
create github pr "Add new feature"
```

### **Workflow 4: AI-Powered Development**

```bash
# 1. Open file
:edit app.py

# 2. Use live edit mode
:live-edit app.py

# 3. Ask AI to edit
add error handling to this function
optimize this code
refactor this function
explain how this works
```

### **Workflow 5: Search & Debug**

```bash
# 1. Search for issues
search for "TODO"
search for "FIXME" in app.py

# 2. Find files
find files named "test"
list files in src/

# 3. Debug
debug buggy.py
run test_suite.py

# 4. Fix issues
:edit buggy.py
find bugs
fix this error
```

---

## 🔎 **Command Categories Summary**

| Category | Commands | Count |
|----------|----------|-------|
| **Panel Commands** | `:banner`, `:sheet`, `:tree`, `:edit`, etc. | 9 |
| **File Operations** | `create`, `read`, `delete`, `rename`, `move`, `copy` | 6 |
| **Folder Operations** | `create folder`, `delete folder`, `move folder`, etc. | 5 |
| **Line Editing** | `remove`, `add`, `edit`, `replace`, `delete` | 10+ |
| **Shell Commands** | `ls`, `cd`, `grep`, `find`, `python`, etc. | 40+ |
| **Natural Language** | `search for`, `find files`, `run`, `debug` | 10+ |
| **Git Commands** | `init`, `add`, `commit`, `push`, `pull`, etc. | 12+ |
| **GitHub Commands** | `create repo`, `create issue`, `create pr` | 3 |
| **AI Commands** | `explain`, `analyze`, `find bugs`, `refactor` | 10+ |
| **Navigation** | `cd`, `pwd`, `navigate to` | 5+ |

**Total: 100+ commands supported!**

---

## 📖 **Related Documentation**

- [FEATURES.md](FEATURES.md) - Detailed feature documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [RUN_AND_TEST.md](../RUN_AND_TEST.md) - Testing guide

---

**Version**: 1.1.0  
**Last Updated**: 2024-12-XX
