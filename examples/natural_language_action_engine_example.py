"""
Example: Using the Natural Language Action Engine

This demonstrates how to use the Natural Language Action Engine
to convert user messages directly to structured action JSON.
"""

from gitvisioncli.core.natural_language_action_engine import (
    NaturalLanguageActionEngine,
    ActiveFileContext,
)


def example_basic_usage():
    """Basic usage example."""
    engine = NaturalLanguageActionEngine()
    
    # Example 1: File operation
    user_message = "remove line 5"
    active_file = ActiveFileContext(path="app.py", content="line1\nline2\nline3\nline4\nline5\nline6")
    
    action = engine.convert_to_action(user_message, active_file=active_file)
    if action:
        print(f"Action Type: {action.type}")
        print(f"Params: {action.params}")
        print(f"JSON: {engine.to_json_string(action)}")
    # Output:
    # Action Type: DeleteLineRange
    # Params: {'path': 'app.py', 'start_line': 5, 'end_line': 5}
    # JSON: {
    #   "type": "DeleteLineRange",
    #   "params": {
    #     "path": "app.py",
    #     "start_line": 5,
    #     "end_line": 5
    #   }
    # }


def example_git_operations():
    """Git operations example."""
    engine = NaturalLanguageActionEngine()
    
    # Git init
    action = engine.convert_to_action("git init")
    print(f"Git Init: {action.type if action else None}")
    
    # Git commit
    action = engine.convert_to_action('commit all with message "Initial commit"')
    if action:
        print(f"Git Commit: {action.params['message']}")
    
    # Git branch
    action = engine.convert_to_action("create new branch feature/test")
    if action:
        print(f"Git Branch: {action.params['name']}")


def example_broken_grammar():
    """Broken grammar handling example."""
    engine = NaturalLanguageActionEngine()
    
    # These all get normalized automatically
    test_cases = [
        "remove line1",      # → "remove line 1"
        "delete ln5",        # → "delete line 5"
        "rm 2",              # → "remove line 2" (if context suggests line op)
    ]
    
    active_file = ActiveFileContext(path="test.py")
    
    for msg in test_cases:
        action = engine.convert_to_action(msg, active_file=active_file)
        if action:
            print(f"'{msg}' → {action.type} {action.params}")


def example_file_operations():
    """File operations example."""
    engine = NaturalLanguageActionEngine()
    
    # Read file
    action = engine.convert_to_action("read file utils/app.py")
    print(f"Read: {action.params['path'] if action else None}")
    
    # Create file
    action = engine.convert_to_action("create file hello.py with print('hi')")
    if action:
        print(f"Create: {action.params['path']} with content: {action.params.get('content', '')}")
    
    # Rename file
    action = engine.convert_to_action("rename app.py to main.py")
    if action:
        print(f"Rename: {action.params['old_path']} → {action.params['new_path']}")


def example_github_operations():
    """GitHub operations example."""
    engine = NaturalLanguageActionEngine()
    
    # Create repo
    action = engine.convert_to_action("create github repo my-app private")
    if action:
        print(f"GitHub Repo: {action.params['name']} (private: {action.params['private']})")
    
    # Create issue
    action = engine.convert_to_action('open issue "bug" with body "fix this"')
    if action:
        print(f"Issue: {action.params['title']}")


if __name__ == "__main__":
    print("=== Basic Usage ===")
    example_basic_usage()
    print("\n=== Git Operations ===")
    example_git_operations()
    print("\n=== Broken Grammar ===")
    example_broken_grammar()
    print("\n=== File Operations ===")
    example_file_operations()
    print("\n=== GitHub Operations ===")
    example_github_operations()

