# Modular Handler Architecture

## Overview

This module provides a comprehensive, extensible handler architecture for converting natural language commands into structured actions. The system is designed to be:

- **Modular**: Each operation type has its own handler
- **Extensible**: Easy to add new handlers or categories
- **Powerful**: Handles complex natural language with confidence scoring
- **Maintainable**: Clear separation of concerns

## Architecture

### Core Components

1. **BaseHandler** (`base.py`)
   - Abstract base class for all handlers
   - Provides utilities for content extraction, line number parsing, etc.
   - Defines the interface: `can_handle()` and `parse()`

2. **HandlerRegistry** (`registry.py`)
   - Central registry for all handlers
   - Organizes handlers by category
   - Supports priority-based ordering

3. **HandlerManager** (`manager.py`)
   - Manages handler execution and routing
   - Selects best handler based on confidence scores
   - Provides fallback mechanisms

4. **CommandRouter** (`command_router.py`)
   - Main entry point for command routing
   - Integrates all handler categories
   - Provides unified API

### Handler Categories

1. **File Handlers** (`file_handlers.py`)
   - CreateFileHandler
   - ReadFileHandler
   - DeleteFileHandler
   - RenameFileHandler
   - MoveFileHandler
   - CopyFileHandler
   - Plus line editing handlers (Insert, Replace, Delete, Append)

2. **Git Handlers** (`git_handlers.py`)
   - GitInitHandler
   - GitAddHandler
   - GitCommitHandler
   - GitPushHandler
   - GitPullHandler
   - GitBranchHandler
   - GitCheckoutHandler
   - GitMergeHandler
   - GitRemoteHandler
   - GitStatusHandler
   - GitLogHandler

3. **GitHub Handlers** (`github_handlers.py`)
   - GitHubCreateRepoHandler
   - GitHubCreateIssueHandler
   - GitHubCreatePRHandler

## Usage

### Basic Usage

```python
from gitvisioncli.core.command_router import CommandRouter
from gitvisioncli.core.natural_language_action_engine import ActiveFileContext

router = CommandRouter()

# Route a command
action = router.route(
    "create app.py with print('hello')",
    active_file=None
)

if action:
    print(action.type)  # "CreateFile"
    print(action.params)  # {"path": "app.py", "content": "print('hello')"}
```

### Adding Custom Handlers

```python
from gitvisioncli.core.handlers.base import BaseHandler, HandlerResult
import re

class MyCustomHandler(BaseHandler):
    def _init_patterns(self):
        return [re.compile(r'\bmy\s+command\b', re.IGNORECASE)]
    
    def can_handle(self, text, context=None):
        if 'my command' in text.lower():
            return 0.9
        return 0.0
    
    def parse(self, text, context=None, full_message=None):
        return HandlerResult(
            success=True,
            action_type="MyAction",
            params={},
            confidence=0.9
        )

# Register the handler
router.register_handler(MyCustomHandler(), "custom", "MyCustomHandler")
```

## Extensibility

The system is designed for easy extension:

1. **Add new handlers**: Create a handler class inheriting from `BaseHandler`
2. **Add new categories**: Create a category class with `get_handlers()` method
3. **Modify priorities**: Set handler priority in constructor
4. **Custom parsing**: Override `parse()` method for complex logic

## Benefits

- **Separation of Concerns**: Each handler is responsible for one operation type
- **Testability**: Handlers can be tested independently
- **Maintainability**: Easy to find and fix issues
- **Extensibility**: Add new features without modifying existing code
- **Performance**: Priority-based routing ensures fast matching

