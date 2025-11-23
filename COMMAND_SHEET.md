# 📋 GitVisionCLI - Complete Command Sheet

**The Ultimate Reference Guide for All GitVisionCLI Commands**

---

## 📑 **Table of Contents**

1. [Workspace & Panel Commands](#workspace--panel-commands)
2. [Natural Language Commands (Direct)](#natural-language-commands-direct)
3. [File Operations](#file-operations)
4. [Folder Operations](#folder-operations)
5. [Line Editing Commands](#line-editing-commands)
6. [Git Commands](#git-commands)
7. [GitHub Commands](#github-commands)
8. [AI Engine Commands](#ai-engine-commands)
9. [Navigation & Workspace](#navigation--workspace)
10. [Editor Commands](#editor-commands)
11. [Multi-line Input](#multi-line-input)
12. [Shell Commands](#shell-commands)
13. [All Action Types](#all-action-types)

---

## 🎛️ **Workspace & Panel Commands**

| Command | Description |
|---------|-------------|
| `:banner` | Show workspace banner with quick commands |
| `:tree` | Show project tree explorer (file browser) |
| `:edit <file>` | Open file in editor panel with line numbers |
| `:markdown <file>` | Preview markdown file with rendering |
| `:sheet` or `:commands` | Show complete command reference (this sheet) |
| `:models` | AI Model Manager (view engines, models, API keys) |
| `:git-graph` or `:gitgraph` | Git commit graph visualization |
| `:live-edit <file>` | AI Live Editor Mode (edit file via AI with streaming) |
| `:save` | Save current editor buffer to disk |
| `:close` or `:x` | Close right panel and return to banner |

---

## 💬 **Natural Language Commands (Direct)**

**These commands work instantly without AI (via Natural Language Action Engine):**

### **File Operations**

| Command | Description | Example |
|---------|-------------|---------|
| `create file <path>` | Create new file | `create file app.py` |
| `read file <path>` | Read/display file content | `read file app.py` |
| `delete file <path>` | Delete file | `delete file old.py` |
| `rename <old> to <new>` | Rename file | `rename app.py to main.py` |
| `move <file> to <folder>` | Move file to folder | `move app.py to src/` |
| `copy <file> to <new>` | Copy file | `copy app.py to app_backup.py` |
| `open <file>` | Open file in editor | `open app.py` |

### **Folder Operations**

| Command | Description | Example |
|---------|-------------|---------|
| `create folder <path>` | Create new folder/directory | `create folder src` |
| `delete folder <path>` | Delete folder/directory | `delete folder old` |
| `move folder <path> to <target>` | Move folder to new location | `move src to lib` |
| `copy folder <path> to <new>` | Copy folder | `copy src to src_backup` |
| `rename folder <old> to <new>` | Rename folder | `rename src to lib` |

### **Line Editing** (when file is open in editor)

| Command | Description | Example |
|---------|-------------|---------|
| `remove line 5` | Delete single line | `remove line 5` |
| `delete line 5` | Same as remove | `delete line 5` |
| `rm 5` | Short form (auto-fixed) | `rm 5` → `remove line 5` |
| `delete lines 4-9` | Delete line range | `delete lines 4-9` |
| `remove lines 4 to 9` | Same as above | `remove lines 4 to 9` |
| `replace line 3 with <text>` | Replace line content | `replace line 3 with x = 100` |
| `edit line 3 with <text>` | Same as replace | `edit line 3 with new code` |
| `add <text> at line 10` | Insert after line 10 | `add print("hi") at line 10` |
| `add <text> at bottom` | Append to end of file | `add print("end") at bottom` |
| `insert <text> at line 5` | Insert before line 5 | `insert # comment at line 5` |

**Grammar Fix:** Broken grammar is auto-fixed:
- `line1` → `line 1`
- `ln5` → `line 5`
- `rm 2` → `remove line 2`

### **Git Operations**

| Command | Description | Example |
|---------|-------------|---------|
| `:git-graph` | Open Git graph panel (command) | `:git-graph` |
| `git graph` | Open Git graph panel (natural language) | `git graph` |
| `git init` | Initialize repository | `git init` |
| `git add <files>` | Stage files | `git add .` or `git add app.py` |
| `git commit 'message'` | Commit with message | `git commit "Initial commit"` |
| `git branch <name>` | Create new branch | `git branch feature` |
| `git checkout <branch>` | Switch to branch | `git checkout main` |
| `go to <branch>` | Same as checkout | `go to main` |
| `git merge <branch>` | Merge branch | `git merge feature` |

### **GitHub Operations**

| Command | Description | Example |
|---------|-------------|---------|
| `create github repo <name>` | Create GitHub repository | `create github repo my-app` |
| `create github repo <name> private` | Create private repo | `create github repo my-app private` |
| `create github issue 'title'` | Create GitHub issue | `create github issue "Bug fix"` |
| `create github pr 'title'` | Create pull request | `create github pr "New feature"` |

### **Directory Navigation**

| Command | Description | Example |
|---------|-------------|---------|
| `cd <path>` | Change directory | `cd src` |
| `cd ..` | Go up one directory | `cd ..` |
| `pwd` | Show current directory | `pwd` |
| `create folder X and go to it` | Create folder + change directory | `create folder demo and go to it` |

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

**Multiline (use `:ml`):**
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
read file <path>
read file app.py
read file src/utils.py
```

### **Delete Files**

```bash
delete file <path>
delete file old.py
```

### **Rename Files**

```bash
rename <old> to <new>
rename app.py to main.py
```

### **Move Files**

```bash
move <file> to <folder>
move app.py to src/
```

### **Copy Files**

```bash
copy <file> to <new>
copy app.py to app_backup.py
```

---

## 📂 **Folder Operations**

### **Create Folders**

```bash
create folder <path>
create folder src
create folder tests/unit
```

### **Delete Folders**

```bash
delete folder <path>
delete folder old
```

### **Move Folders**

```bash
move folder <path> to <target>
move folder src to lib
```

### **Copy Folders**

```bash
copy folder <path> to <new>
copy folder src to src_backup
```

### **Rename Folders**

```bash
rename folder <old> to <new>
rename folder src to lib
```

---

## ✏️ **Line Editing Commands**

**These work when a file is open in the editor (`:edit <file>`):**

### **Delete Lines**

```bash
remove line 5          # Delete line 5
delete line 5          # Same as above
rm 5                   # Short form (auto-fixed)
delete lines 4-9       # Delete range
remove lines 4 to 9    # Same as above
```

### **Insert Lines**

```bash
add <text> at line 10      # Insert after line 10
insert <text> at line 5    # Insert before line 5
add <text> at bottom        # Append to end
add <text> at top           # Insert at beginning
```

### **Replace Lines**

```bash
replace line 3 with <text>
edit line 3 with <text>
```

### **Examples**

```bash
:edit app.py
remove line 1
add # -*- coding: utf-8 -*- at line 1
replace line 5 with print("Updated!")
add print("End") at bottom
```

---

## 🔁 **Git Commands**

### **Repository Management**

```bash
git init                    # Initialize repository
git status                  # View status (via AI)
git log                     # View history (via AI)
```

### **Staging & Committing**

```bash
git add <files>             # Stage files
git add .                   # Stage all files
git commit 'message'        # Commit with message
git commit "Initial commit" # Example
```

### **Branching**

```bash
git branch <name>           # Create branch
git branch feature          # Example
git checkout <branch>       # Switch branch
git checkout main           # Example
go to <branch>              # Alternative syntax
git merge <branch>          # Merge branch
```

### **Remote Operations**

```bash
git push                    # Push to remote (via AI)
git pull                    # Pull from remote (via AI)
git remote add <name> <url> # Add remote (via AI)
```

### **Visualization**

```bash
:git-graph                  # Open Git graph panel
git graph                   # Same (natural language)
```

---

## 🌐 **GitHub Commands**

**Requires `GITHUB_TOKEN` environment variable:**

```bash
export GITHUB_TOKEN="ghp_..."
```

### **Repository Management**

```bash
create github repo <name>           # Create public repo
create github repo <name> private   # Create private repo
create github repo my-app           # Example
delete github repo <name>           # Delete repo (via AI)
```

### **Issues & Pull Requests**

```bash
create github issue 'title'         # Create issue
create github issue "Bug fix"       # Example
create github pr 'title'            # Create pull request
create github pr "New feature"      # Example
```

---

## 🤖 **AI Engine Commands**

### **Model Management**

```bash
:models                    # View all available models
:set-ai <model>            # Switch AI model
stats                      # Show current model and stats
```

### **Model Examples**

```bash
:set-ai gpt-4o-mini
:set-ai gpt-4o
:set-ai gemini-1.5-pro
:set-ai claude-3.5-sonnet
:set-ai ollama/llama2
```

### **Ollama Commands** (Local AI)

```bash
ollama models              # List installed models
ollama pull <model>        # Install model
ollama pull llama2         # Example
```

---

## 🧭 **Navigation & Workspace**

| Command | Description |
|---------|-------------|
| `cd <path>` | Change directory |
| `cd ..` | Go up one directory |
| `pwd` | Print current working directory |
| `clear` | Clear console screen |
| `stats` | Show workspace statistics |
| `exit` or `quit` | Exit GitVisionCLI |

---

## 📝 **Editor Commands**

### **Editor Scrolling** (when in editor mode)

| Command | Description |
|---------|-------------|
| `:up` or `:scroll-up` | Scroll editor view up |
| `:down` or `:scroll-down` | Scroll editor view down |
| `:pageup` or `:pu` | Scroll editor one page up |
| `:pagedown` or `:pd` | Scroll editor one page down |

### **Editor Features**

- **Line Numbers**: Automatically displayed
- **Auto-save**: Changes sync to UI when saved
- **Live Streaming**: AI text streams token-by-token
- **Grammar Fix**: Broken grammar auto-fixed
- **No Questions**: AI never asks questions when file is open

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

You can also paste code blocks directly:

````bash
```python
def hello():
    print("World")
```
````

These are automatically treated as single messages.

---

## 💻 **Shell Commands**

### **Shell Prefix Modes** (Cross-OS)

| Prefix | Mode | Example |
|--------|------|---------|
| `p.*` | PowerShell | `p.get-process`, `p.dir` |
| `c.*` | Windows CMD | `c.dir`, `c.echo hello` |
| `l.*` | Linux bash | `l.ls`, `l.cat file` |
| `m.*` | macOS zsh | `m.open`, `m.say` |
| `.<cmd>` | Local shell | `.ls`, `.git status` |

### **Local Shell Shortcuts**

| Command | Description |
|---------|-------------|
| `pwd` | Print working directory |
| `ls` or `ll` | Directory listing |
| `whoami` | Show current user |
| `cat <file>` | Display file content |
| `tree` | Directory tree |
| `mkdir <dir>` | Create directory |
| `rmdir <dir>` | Remove directory |
| `rm <file>` | Remove file |
| `touch <file>` | Create empty file |

---

## 🔧 **All Action Types**

**All supported action types (50+ actions):**

### **Filesystem Actions**

| Action | Category | Description |
|--------|----------|-------------|
| `CreateFile` | Filesystem | Create new file |
| `EditFile` | Filesystem | Edit existing file |
| `ReadFile` | Other | Read file content |
| `DeleteFile` | Filesystem | Delete file |
| `MoveFile` | Filesystem | Move file |
| `CopyFile` | Filesystem | Copy file |
| `RenameFile` | Filesystem | Rename file |
| `CreateFolder` | Filesystem | Create folder |
| `DeleteFolder` | Filesystem | Delete folder |
| `MoveFolder` | Filesystem | Move folder |
| `CopyFolder` | Filesystem | Copy folder |

### **AI Text/Edit Actions**

| Action | Category | Description |
|--------|----------|-------------|
| `AppendText` | AI Text/Edit | Append text to file |
| `PrependText` | AI Text/Edit | Prepend text to file |
| `ReplaceText` | AI Text/Edit | Replace text in file |
| `InsertBeforeLine` | AI Text/Edit | Insert before line |
| `InsertAfterLine` | AI Text/Edit | Insert after line |
| `DeleteLineRange` | Filesystem | Delete line range |
| `RewriteEntireFile` | AI Text/Edit | Rewrite entire file |
| `ApplyPatch` | AI Text/Edit | Apply patch to file |

### **Advanced Text Actions**

| Action | Category | Description |
|--------|----------|-------------|
| `ReplaceByPattern` | Other | Replace by regex pattern |
| `DeleteByPattern` | Filesystem | Delete by pattern |
| `ReplaceByFuzzyMatch` | Other | Replace by fuzzy match |
| `InsertAtTop` | Other | Insert at top of file |
| `InsertAtBottom` | Other | Insert at bottom |
| `InsertBlockAtLine` | Other | Insert block at line |
| `ReplaceBlock` | Other | Replace block |
| `RemoveBlock` | Other | Remove block |
| `UpdateJSONKey` | Other | Update JSON key |
| `UpdateYAMLKey` | Other | Update YAML key |
| `InsertIntoFunction` | Other | Insert into function |
| `InsertIntoClass` | Other | Insert into class |
| `AddDecorator` | Other | Add decorator |
| `AddImport` | Other | Add import |

### **Git Actions**

| Action | Category | Description |
|--------|----------|-------------|
| `RunGitCommand` | Other | Run arbitrary git command |
| `GitInit` | Git | Initialize repository |
| `GitAdd` | Git | Stage files |
| `GitCommit` | Git | Commit changes |
| `GitPush` | Git | Push to remote |
| `GitPull` | Git | Pull from remote |
| `GitBranch` | Git | Create/manage branches |
| `GitCheckout` | Git | Switch branch |
| `GitMerge` | Git | Merge branch |
| `GitRemote` | Git | Manage remotes |

### **GitHub Actions**

| Action | Category | Description |
|--------|----------|-------------|
| `GitHubCreateRepo` | GitHub | Create repository |
| `GitHubDeleteRepo` | GitHub | Delete repository |
| `GitHubPushPath` | GitHub | Push path to GitHub |
| `GitHubCreateIssue` | GitHub | Create issue |
| `GitHubCreatePR` | GitHub | Create pull request |

### **Other Actions**

| Action | Category | Description |
|--------|----------|-------------|
| `SearchFiles` | Other | Search files |
| `FindReplace` | Other | Find and replace |
| `GenerateProjectStructure` | Other | Generate project structure |
| `ScaffoldModule` | Other | Scaffold module |
| `RunShellCommand` | Other | Run shell command |
| `RunTests` | Other | Run tests |
| `BuildProject` | Other | Build project |
| `BatchOperation` | Other | Batch operation |
| `AtomicOperation` | Other | Atomic operation |

---

## ⌨️ **Keyboard Shortcuts**

| Shortcut | Description |
|----------|-------------|
| `Ctrl+C` | Cancel current operation / exit multi-line mode |
| `Ctrl+D` | Exit GitVision (or use `exit`/`quit` command) |
| `↑ / ↓` | Navigate command history |
| `Tab` | Autocomplete (if available) |

---

## 🎯 **Quick Tips**

1. **No Clarification Questions**: When a file is open, AI never asks "which file?"
2. **Grammar Auto-Fix**: Broken grammar is automatically fixed (`line1` → `line 1`)
3. **Streaming Writes**: AI text streams token-by-token into editor
4. **Multi-line Input**: Use `:ml` for multi-line content
5. **Environment Variables**: API keys can be set via environment variables
6. **Direct Actions**: Many commands work instantly without AI

---

## 📚 **More Documentation**

- [README.md](README.md) - Main project documentation
- [QUICKSTART.md](docs/QUICKSTART.md) - Quick start guide
- [FEATURES.md](docs/FEATURES.md) - Feature overview
- [RUN_AND_TEST.md](RUN_AND_TEST.md) - Testing guide

---

**Last Updated**: 2024-12-XX  
**Version**: 1.0.0

