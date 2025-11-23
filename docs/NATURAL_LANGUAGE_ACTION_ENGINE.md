# Natural Language Action Engine

## Overview

The Natural Language Action Engine is GitVision's deterministic converter that transforms every user message into a single structured ACTION JSON. It operates with **zero questions, zero clarifications, and zero explanations** (unless no context exists at all).

## Key Features

### 1. **Always Infers Intent**
- Never asks "which file?" if an editor file is open
- Never asks for confirmation unless explicitly requested
- Always picks the most likely action

### 2. **Grammar Normalization**
Automatically fixes broken grammar:
- "remove line1" → "remove line 1"
- "delete ln5" → "delete line 5"
- "rm 2" → "remove line 2" (when context suggests line operation)

### 3. **Comprehensive Action Support**

#### File Operations
- **Line-based**: `remove line 5`, `delete lines 3-10`, `replace line 2 with X`, `insert at line 2: hello`
- **File-level**: `read file app.py`, `delete app.py`, `rename A to B`, `move foo.py to src/`, `copy main.py to backup/main.py`

#### Git Operations
- `git init`
- `git add`, `git commit "message"`
- `branch dev`, `checkout dev`, `merge main`
- `git push`, `git pull`, `git remote add origin <url>`
- `show git graph`

#### GitHub Operations
- `create github repo my-app private`
- `open issue 'bug' with body 'fix this'`
- `create github pr 'title'`

### 4. **Active File Context**
When a file is open in the editor:
- ANY command like "remove line 5" applies to that file WITHOUT asking
- Active file = default target unless user specifies another file

### 5. **Documentation Auto-Sync**
After ANY file change, automatically syncs:
- `README.md`
- `docs/COMMANDS.md`
- `docs/QUICKSTART.md`
- `docs/FEATURES.md`

## Usage

### Basic Usage

```python
from gitvisioncli.core.natural_language_action_engine import (
    NaturalLanguageActionEngine,
    ActiveFileContext,
)

engine = NaturalLanguageActionEngine()

# With active file context
active_file = ActiveFileContext(path="app.py", content="...")
action = engine.convert_to_action("remove line 5", active_file=active_file)

if action:
    print(action.type)  # "DeleteLineRange"
    print(action.params)  # {"path": "app.py", "start_line": 5, "end_line": 5}
    print(engine.to_json_string(action))  # JSON string
```

### Using ActionRouter

```python
from gitvisioncli.core.action_router import ActionRouter
from pathlib import Path

router = ActionRouter(base_dir=Path.cwd())

# Try direct conversion (fast, no AI needed)
action_dict = router.try_direct_action(
    "remove line 1",
    active_file=ActiveFileContext(path="app.py")
)

if action_dict:
    # Execute action directly
    executor.run_action(action_dict)
else:
    # Fall back to AI processing
    await engine.stream(user_message)
```

## Architecture

### Components

1. **NaturalLanguageActionEngine** (`natural_language_action_engine.py`)
   - Core conversion engine
   - Pattern matching and grammar normalization
   - Action JSON generation

2. **ActionRouter** (`action_router.py`)
   - Integration layer
   - Routes between direct action and AI processing
   - Manages active file context

3. **DocumentationSyncer** (`doc_sync.py`)
   - Auto-syncs documentation after file changes
   - Updates COMMANDS.md, FEATURES.md, etc.

## Supported Action Types

### File Operations
- `CreateFile(path, content)`
- `DeleteFile(path)`
- `ReadFile(path)`
- `RenameFile(old_path, new_path)`
- `MoveFile(path, target_folder)`
- `CopyFile(path, new_path)`
- `DeleteLineRange(path, start_line, end_line)`
- `ReplaceBlock(path, start_line, end_line, text)`
- `InsertAfterLine(path, line_number, text)`
- `InsertAtBottom(path, text)`

### Git Operations
- `GitInit()`
- `GitAdd(path)`
- `GitCommit(message)`
- `GitBranch(name)`
- `GitCheckout(branch)`
- `GitMerge(branch)`
- `GitPush(branch?)`
- `GitPull(branch?)`
- `GitRemote(name, url)`
- `ShowGitGraph()` (UI command)

### GitHub Operations
- `GitHubCreateRepo(name, private)`
- `GitHubCreateIssue(title, body)`
- `GitHubCreatePR(title, head, base)`

## Model Compatibility

The engine is designed to work with **ALL** model types:
- OpenAI GPT-4o / GPT-4o-mini
- Gemini Pro / Flash
- Claude Haiku / Sonnet
- LLaMA 3 (Ollama)
- Phi-3
- Any cheap model with small context

No advanced instructions that break small models. Simple → consistent → deterministic action mapping.

## Examples

### Example 1: Line Deletion
```
User: "remove line 1"
Active File: app.py
→ Action: DeleteLineRange(path="app.py", start_line=1, end_line=1)
```

### Example 2: File Creation
```
User: "create file hello.py with print('hi')"
→ Action: CreateFile(path="hello.py", content="print('hi')")
```

### Example 3: Git Commit & Push
```
User: 'commit all with message "Initial commit"'
→ Action: GitCommit(message="Initial commit")

User: 'git push -u origin main'
→ Action: GitPush(branch="main")
```

### Example 4: Broken Grammar
```
User: "remove line1"
→ Normalized: "remove line 1"
→ Action: DeleteLineRange(path="app.py", start_line=1, end_line=1)
```

## Integration Points

The Natural Language Action Engine can be integrated at multiple levels:

1. **Pre-processing**: Convert natural language to actions before sending to AI
2. **Fallback**: Use when AI is unavailable or for simple commands
3. **Hybrid**: Use direct conversion for simple commands, AI for complex ones

## Future Enhancements

- [ ] More sophisticated grammar normalization
- [ ] Context-aware file path resolution
- [ ] Multi-action support (compound commands)
- [ ] Learning from user corrections
- [ ] Custom action pattern definitions

