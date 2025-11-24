# 🎬 GitVisionCLI Demo Script

**Quick demo commands for LinkedIn & GitHub video**

---

## 🚀 **Setup**

```bash
# 1. Launch GitVisionCLI
gitvision

# 2. Show banner (quick commands)
:banner
```

---

## 📝 **Part 1: Natural Language File Operations**

```bash
# Create a file with content
create app.py with print("Hello from GitVisionCLI!")

# Read the file
read file app.py

# Create multiline file
:ml
create server.py with
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "GitVisionCLI Demo!"
:end
```

---

## ✏️ **Part 2: Live Editing (The Magic!)**

```bash
# Open file in editor
:edit app.py

# Now edit with natural language (file is open, no questions asked!)
add line 1 with # GitVisionCLI Demo
replace line 2 with print("AI-Powered Terminal IDE!")
add print("Built with Python") at bottom
remove line 3
```

---

## 🌳 **Part 3: Git Integration**

```bash
# Initialize Git
git init

# Stage and commit
git add .
git commit "Initial commit with GitVisionCLI demo"

# Create branch
git branch feature

# Switch branch
git checkout feature

# View commit graph
:git-graph
```

---

## 🐙 **Part 4: GitHub Integration**

```bash
# Create GitHub repository
create github repo gitvisioncli-demo --private

# Push to GitHub
git push -u origin main
```

---

## 🤖 **Part 5: AI Features**

```bash
# Switch AI models
:models
:set-ai gpt-4o-mini

# Ask AI about code
explain the file app.py
how can I improve this code?
```

---

## 🎨 **Part 6: UI Panels**

```bash
# Show different panels
:tree          # File browser
:sheet         # Command reference
:git-graph     # Git visualization
:models        # AI model manager
```

---

## 🎯 **Quick Highlights**

- ✅ Natural language commands (no syntax to learn!)
- ✅ Zero clarification loops (context-aware)
- ✅ Beautiful dual-panel UI
- ✅ Complete Git workflow
- ✅ Direct GitHub integration
- ✅ Multi-model AI support
- ✅ Live streaming responses

---

## 📸 **Video Tips**

1. **Start**: Show terminal, launch `gitvision`, show banner
2. **File Ops**: Create files with natural language
3. **Live Edit**: Open file, edit with natural language (highlight no questions!)
4. **Git**: Show git workflow, commit graph visualization
5. **GitHub**: Create repo, push (if you have token)
6. **AI**: Switch models, ask questions
7. **End**: Show all panels, highlight key features

---

**Duration**: 2-3 minutes  
**Focus**: Natural language editing + Git integration + Beautiful UI

