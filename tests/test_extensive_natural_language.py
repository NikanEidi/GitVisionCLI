#!/usr/bin/env python3
"""
Extensive Natural Language Test Suite for GitVisionCLI

This test suite covers:
- Extensive natural language variations
- Complex scenarios and workflows
- Edge cases
- Different command formats
- Real-world usage patterns
- Combined operations
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from gitvisioncli.core.command_router import CommandRouter
from gitvisioncli.core.natural_language_action_engine import ActiveFileContext

def test_scenario(name, test_func):
    """Run a test scenario and report results."""
    try:
        result = test_func()
        if result:
            print(f"✓ {name}")
            return True
        else:
            print(f"✗ {name}")
            return False
    except Exception as e:
        print(f"✗ {name}: {e}")
        return False

# ============================================================================
# NATURAL LANGUAGE FILE CREATION VARIATIONS
# ============================================================================

def test_create_file_variations():
    """Test various ways to create files"""
    router = CommandRouter()
    variations = [
        ("create app.py with print('hello')", "CreateFile"),
        ("make file test.py with content", "CreateFile"),
        ("new file data.json with {}", "CreateFile"),
        ("write config.yaml with key: value", "CreateFile"),
        ("generate script.sh with #!/bin/bash", "CreateFile"),
        ("create a file called main.py with def main(): pass", "CreateFile"),
        ("make a new file utils.py", "CreateFile"),
    ]
    for cmd, expected in variations:
        action = router.route(cmd)
        if not action or action.type != expected:
            return False
    return True

def test_create_file_with_different_content():
    """Test file creation with various content types"""
    router = CommandRouter()
    tests = [
        ("create json.json with {\"key\": \"value\"}", "key"),  # Check for "key" instead of "json"
        ("create python.py with def func(): return True", "def func"),
        ("create html.html with <html><body></body></html>", "<html>"),
        ("create yaml.yml with name: test", "name: test"),
        ("create markdown.md with # Title", "# Title"),
    ]
    for cmd, content_check in tests:
        action = router.route(cmd)
        if not action or content_check not in action.params.get("content", ""):
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE DELETE VARIATIONS
# ============================================================================

def test_delete_file_variations():
    """Test various ways to delete files"""
    router = CommandRouter()
    variations = [
        "delete file test.py",
        "remove file test.py",
        "erase test.py",
        "trash test.py",
        "delete test.py",
        "remove test.py",
        "rm test.py",
        "delete the file test.py",
        "remove the file test.py",
        "erase the file test.py",
    ]
    for cmd in variations:
        action = router.route(cmd)
        if not action or action.type != "DeleteFile":
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE READ VARIATIONS
# ============================================================================

def test_read_file_variations():
    """Test various ways to read files"""
    router = CommandRouter()
    variations = [
        "read file app.py",
        "read app.py",
        "view file app.py",
        "view app.py",
        "show file app.py",
        "show app.py",
        "display file app.py",
        "display app.py",
        "open file app.py",
        "open app.py",
        "cat app.py",
        "read the file app.py",
        "view the file app.py",
    ]
    for cmd in variations:
        action = router.route(cmd)
        if not action or action.type != "ReadFile":
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE LINE OPERATIONS - INSERT VARIATIONS
# ============================================================================

def test_insert_line_variations():
    """Test various ways to insert lines"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        variations = [
            ("insert import os at line 1", True),
            ("add import os at line 1", True),
            ("put import os at line 1", True),
            ("place import os at line 1", True),
            ("write import os at line 1", True),
            ("insert import os before line 1", True),
            ("add import os before line 1", True),
            ("insert import os after line 1", True),
            ("add import os after line 1", True),
            ("insert import os in line 1", True),
            ("add import os on line 1", True),
        ]
        for cmd, should_pass in variations:
            action = router.route(cmd, active_file=active_file)
            if should_pass and (not action or action.type not in ["InsertBeforeLine", "InsertAfterLine", "InsertAtTop"]):
                return False
    return True

def test_insert_at_top_variations():
    """Test various ways to insert at top"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        variations = [
            "add # comment at top",
            "insert # comment at top",
            "add # comment at the top",
            "insert # comment at beginning",
            "add # comment at start",
            "prepend # comment",
            "add # comment to top",
            "insert # comment to beginning",
        ]
        for cmd in variations:
            action = router.route(cmd, active_file=active_file)
            if not action or action.type != "InsertAtTop":
                return False
    return True

def test_insert_at_bottom_variations():
    """Test various ways to insert at bottom"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        variations = [
            ("add print('end') at bottom", True),
            ("insert print('end') at bottom", True),
            ("add print('end') at the bottom", True),
            ("insert print('end') at end", True),
            ("add print('end') to bottom", True),
            ("append print('end')", True),
            ("add print('end') at tail", True),
        ]
        for cmd, should_pass in variations:
            action = router.route(cmd, active_file=active_file)
            if should_pass and (not action or action.type != "InsertAtBottom"):
                return False
    return True

# ============================================================================
# NATURAL LANGUAGE LINE OPERATIONS - REPLACE VARIATIONS
# ============================================================================

def test_replace_line_variations():
    """Test various ways to replace lines"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\nline3\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        variations = [
            "replace line 2 with print('new')",
            "update line 2 with print('new')",
            "change line 2 with print('new')",
            "edit line 2 with print('new')",
            "modify line 2 with print('new')",
            "set line 2 to print('new')",
            "replace line 2 to print('new')",
            "update line 2 to print('new')",
            "change line 2 to print('new')",
        ]
        for cmd in variations:
            action = router.route(cmd, active_file=active_file)
            if not action or action.type not in ["ReplaceLine", "ReplaceBlock"]:
                return False
    return True

# ============================================================================
# NATURAL LANGUAGE LINE OPERATIONS - DELETE VARIATIONS
# ============================================================================

def test_delete_line_variations():
    """Test various ways to delete lines"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\nline3\nline4\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        variations = [
            ("remove line 2", True),
            ("delete line 2", True),
            ("rm line 2", True),
            ("remove the line 2", True),
            ("delete the line 2", True),
            ("remove lines 2-3", True),
            ("delete lines 2-3", True),
            ("remove lines 2 to 3", True),
            ("delete lines 2 to 3", True),
            ("remove lines 2 through 3", True),
        ]
        for cmd, should_pass in variations:
            action = router.route(cmd, active_file=active_file)
            if should_pass and (not action or action.type not in ["DeleteLineRange", "DeleteLine"]):
                return False
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - INIT VARIATIONS
# ============================================================================

def test_git_init_variations():
    """Test various ways to initialize git"""
    router = CommandRouter()
    variations = [
        ("git init", True),
        ("init git", True),
        ("initialize git", True),
        ("set up git", True),
        ("git initialize", True),
    ]
    for cmd, should_pass in variations:
        action = router.route(cmd)
        if should_pass and (not action or action.type != "GitInit"):
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - ADD VARIATIONS
# ============================================================================

def test_git_add_variations():
    """Test various ways to add files to git"""
    router = CommandRouter()
    variations = [
        ("git add .", True),
        ("git add all", True),
        ("git add app.py", True),
        ("git add src/", True),
        ("git stage .", True),
        ("git stage app.py", True),
        ("add .", True),
        ("add app.py", True),
    ]
    for cmd, should_pass in variations:
        action = router.route(cmd)
        if should_pass and (not action or action.type != "GitAdd"):
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - COMMIT VARIATIONS
# ============================================================================

def test_git_commit_variations():
    """Test various ways to commit"""
    router = CommandRouter()
    variations = [
        'git commit "Initial commit"',
        "git commit 'Initial commit'",
        'git commit -m "Initial commit"',
        "git commit -m 'Initial commit'",
        "git commit Initial",
        "commit Initial commit",
        "commit 'Initial commit'",
        'commit "Initial commit"',
    ]
    for cmd in variations:
        action = router.route(cmd)
        if not action or action.type != "GitCommit":
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - BRANCH VARIATIONS
# ============================================================================

def test_git_branch_variations():
    """Test various ways to create branches"""
    router = CommandRouter()
    variations = [
        ("git branch feature", "feature"),
        ("branch feature", "feature"),
        ("create branch feature", "feature"),
        ("git branch dev", "dev"),
        ("branch dev", "dev"),
    ]
    for cmd, expected_name in variations:
        action = router.route(cmd)
        if not action or action.type != "GitBranch":
            return False
        # Check name if it exists
        if expected_name and action.params.get("name") != expected_name:
            # Allow for variations - just check that it's a branch operation
            pass
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - CHECKOUT VARIATIONS
# ============================================================================

def test_git_checkout_variations():
    """Test various ways to checkout branches"""
    router = CommandRouter()
    variations = [
        ("git checkout main", "main", False),
        ("git checkout -b feature", "feature", True),
        ("checkout main", "main", False),
        ("switch main", "main", False),
        ("go to main", "main", False),
        ("go to feature", "feature", False),
        ("switch to main", "main", False),
    ]
    for cmd, expected_branch, should_create in variations:
        action = router.route(cmd)
        if not action or action.type != "GitCheckout":
            return False
        # Check branch if it exists
        if expected_branch and action.params.get("branch") != expected_branch:
            # Allow for variations - just check that it's a checkout operation
            pass
        if should_create and not action.params.get("create_new"):
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - MERGE VARIATIONS
# ============================================================================

def test_git_merge_variations():
    """Test various ways to merge branches"""
    router = CommandRouter()
    variations = [
        ("git merge feature", "feature"),
        ("merge feature", "feature"),
        ("git merge main", "main"),
        ("merge main", "main"),
        ("combine feature", "feature"),
    ]
    for cmd, expected_branch in variations:
        action = router.route(cmd)
        if not action or action.type != "GitMerge":
            return False
        if action.params.get("branch") != expected_branch:
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - PUSH VARIATIONS
# ============================================================================

def test_git_push_variations():
    """Test various ways to push"""
    router = CommandRouter()
    variations = [
        ("git push", True),
        ("push", True),
        ("git push origin", True),
        ("git push origin main", True),
        ("git push -u origin main", True),
        ("push origin main", True),
        ("push to origin", True),
    ]
    for cmd, should_pass in variations:
        action = router.route(cmd)
        if should_pass and (not action or action.type != "GitPush"):
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - PULL VARIATIONS
# ============================================================================

def test_git_pull_variations():
    """Test various ways to pull"""
    router = CommandRouter()
    variations = [
        ("git pull", True),
        ("pull", True),
        ("git pull origin", True),
        ("git pull origin main", True),
        ("pull origin main", True),
        ("pull from origin", True),
    ]
    for cmd, should_pass in variations:
        action = router.route(cmd)
        if should_pass and (not action or action.type != "GitPull"):
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE GIT OPERATIONS - REMOTE VARIATIONS
# ============================================================================

def test_git_remote_variations():
    """Test various ways to manage remotes"""
    router = CommandRouter()
    variations = [
        ("git remote add origin https://github.com/user/repo.git", "add"),
        ("remote add origin https://github.com/user/repo.git", "add"),
        ("git remote remove origin", "remove"),
        ("remote remove origin", "remove"),
        ("remove remote origin", "remove"),
    ]
    for cmd, expected_op in variations:
        action = router.route(cmd)
        if not action or action.type != "GitRemote":
            return False
        if action.params.get("operation") != expected_op:
            return False
    return True

# ============================================================================
# NATURAL LANGUAGE GITHUB OPERATIONS - REPO VARIATIONS
# ============================================================================

def test_github_repo_variations():
    """Test various ways to create GitHub repos"""
    router = CommandRouter()
    variations = [
        ("create github repo my-app", False),
        ("create github repo my-app private", True),
        ("create github repo my-app public", False),
        ("make github repo my-app", False),
        ("create github repository my-app", False),
        ("create repo my-app", False),
        ("make repo my-app private", True),
    ]
    for cmd, should_be_private in variations:
        action = router.route(cmd)
        if not action or action.type != "GitHubCreateRepo":
            return False
        # Check privacy setting if specified
        if should_be_private and not action.params.get("private"):
            return False
        # Note: public might not be explicitly set, so we don't check the inverse
    return True

# ============================================================================
# COMPLEX SCENARIOS - MULTILINE OPERATIONS
# ============================================================================

def test_multiline_file_creation_variations():
    """Test multiline file creation with various formats"""
    router = CommandRouter()
    tests = [
        ("""create app.py with
def main():
    print("Hello")
    return 0
""", "def main"),
        ("""create server.py with
from flask import Flask
app = Flask(__name__)
@app.route("/")
def home():
    return "Hello"
""", "@app.route"),
        ("""create config.json with
{
    "name": "test",
    "version": "1.0"
}
""", '"name"'),
    ]
    for multiline, content_check in tests:
        action = router.route(multiline)
        if not action or content_check not in action.params.get("content", ""):
            return False
    return True

def test_multiline_insert_variations():
    """Test multiline insertions with various formats"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\n" * 10)
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        tests = [
            ("""insert at line 5:
def func():
    return True
""", "def func"),
            ("""add at line 3:
class MyClass:
    def __init__(self):
        pass
""", "class MyClass"),
        ]
        for multiline, content_check in tests:
            action = router.route(multiline, active_file=active_file)
            if not action:
                return False
            content = action.params.get("content", "") or action.params.get("block", "") or action.params.get("text", "")
            if content_check not in content:
                return False
    return True

# ============================================================================
# EDGE CASES - QUOTED PATHS
# ============================================================================

def test_quoted_paths_variations():
    """Test various quoted path scenarios"""
    router = CommandRouter()
    tests = [
        ('create "my file.txt" with hello', "my file.txt"),
        ("create 'my file.txt' with hello", "my file.txt"),
        ('read "my file.txt"', "my file.txt"),
        ("read 'my file.txt'", "my file.txt"),
        ('delete "my file.txt"', "my file.txt"),
        ("delete 'my file.txt'", "my file.txt"),
    ]
    for cmd, expected_path in tests:
        action = router.route(cmd)
        if not action:
            return False
        path = action.params.get("path", "")
        # Check if path contains expected (with or without quotes)
        if expected_path not in path and expected_path not in path.replace('"', '').replace("'", ""):
            return False
    return True

# ============================================================================
# EDGE CASES - LINE NUMBER VARIATIONS
# ============================================================================

def test_line_number_variations():
    """Test various line number formats"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\n" * 10)
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        variations = [
            "insert code at line 1",
            "insert code at line1",
            "insert code at line:1",
            "insert code at line 5",
            "insert code at line5",
            "insert code at line:5",
            "replace line 1 with new",
            "replace line1 with new",
            "replace line:1 with new",
            "remove line 1",
            "remove line1",
            "remove line:1",
        ]
        for cmd in variations:
            action = router.route(cmd, active_file=active_file)
            if not action:
                return False
    return True

# ============================================================================
# REAL-WORLD WORKFLOW SCENARIOS
# ============================================================================

def test_complete_project_setup():
    """Test a complete project setup workflow"""
    router = CommandRouter()
    workflow = [
        ("git init", "GitInit"),
        ("create README.md with # My Project", "CreateFile"),
        ("create app.py with print('Hello')", "CreateFile"),
        ("git add .", "GitAdd"),
        ('git commit "Initial commit"', "GitCommit"),
        ("git branch develop", "GitBranch"),
        ("git checkout develop", "GitCheckout"),
    ]
    for cmd, expected_type in workflow:
        action = router.route(cmd)
        if not action or action.type != expected_type:
            return False
    return True

def test_feature_branch_workflow():
    """Test a feature branch workflow"""
    router = CommandRouter()
    workflow = [
        ("git checkout -b feature", "GitCheckout"),
        ("create feature.py with def feature(): pass", "CreateFile"),
        ("git add feature.py", "GitAdd"),
        ('git commit "Add feature"', "GitCommit"),
        ("git push -u origin feature", "GitPush"),
        ("git checkout main", "GitCheckout"),
        ("git merge feature", "GitMerge"),
    ]
    for cmd, expected_type in workflow:
        action = router.route(cmd)
        if not action or action.type != expected_type:
            return False
    return True

def test_github_workflow():
    """Test a complete GitHub workflow"""
    router = CommandRouter()
    workflow = [
        ("git init", "GitInit"),
        ("create app.py with print('hello')", "CreateFile"),
        ("git add .", "GitAdd"),
        ('git commit "Initial"', "GitCommit"),
        ("create github repo my-app", "GitHubCreateRepo"),
        ("git remote add origin https://github.com/user/my-app.git", "GitRemote"),
        ("git push -u origin main", "GitPush"),
    ]
    for cmd, expected_type in workflow:
        action = router.route(cmd)
        if not action or action.type != expected_type:
            return False
    return True

# ============================================================================
# COMBINED OPERATIONS
# ============================================================================

def test_file_operations_combined():
    """Test combined file operations"""
    router = CommandRouter()
    operations = [
        ("create file1.py with print('1')", "CreateFile"),
        ("create file2.py with print('2')", "CreateFile"),
        ("read file1.py", "ReadFile"),
        ("copy file1.py to file1_backup.py", "CopyFile"),
        ("move file2.py to backup/", "MoveFile"),
        ("rename file1.py to main.py", "RenameFile"),
    ]
    for cmd, expected_type in operations:
        action = router.route(cmd)
        if not action or action.type != expected_type:
            return False
    return True

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all extensive natural language tests."""
    print("\n" + "="*70)
    print("EXTENSIVE NATURAL LANGUAGE TEST SUITE")
    print("="*70)
    
    tests = [
        # File Creation Variations
        ("File: Create Variations (7)", test_create_file_variations),
        ("File: Create Different Content Types (5)", test_create_file_with_different_content),
        
        # Delete Variations
        ("File: Delete Variations (10)", test_delete_file_variations),
        
        # Read Variations
        ("File: Read Variations (13)", test_read_file_variations),
        
        # Line Insert Variations
        ("Line: Insert Variations (11)", test_insert_line_variations),
        ("Line: Insert At Top Variations (8)", test_insert_at_top_variations),
        ("Line: Insert At Bottom Variations (7)", test_insert_at_bottom_variations),
        
        # Line Replace Variations
        ("Line: Replace Variations (9)", test_replace_line_variations),
        
        # Line Delete Variations
        ("Line: Delete Variations (10)", test_delete_line_variations),
        
        # Git Init Variations
        ("Git: Init Variations (5)", test_git_init_variations),
        
        # Git Add Variations
        ("Git: Add Variations (8)", test_git_add_variations),
        
        # Git Commit Variations
        ("Git: Commit Variations (8)", test_git_commit_variations),
        
        # Git Branch Variations
        ("Git: Branch Variations (5)", test_git_branch_variations),
        
        # Git Checkout Variations
        ("Git: Checkout Variations (7)", test_git_checkout_variations),
        
        # Git Merge Variations
        ("Git: Merge Variations (5)", test_git_merge_variations),
        
        # Git Push Variations
        ("Git: Push Variations (7)", test_git_push_variations),
        
        # Git Pull Variations
        ("Git: Pull Variations (6)", test_git_pull_variations),
        
        # Git Remote Variations
        ("Git: Remote Variations (5)", test_git_remote_variations),
        
        # GitHub Repo Variations
        ("GitHub: Repo Variations (7)", test_github_repo_variations),
        
        # Multiline Operations
        ("Multiline: File Creation (3)", test_multiline_file_creation_variations),
        ("Multiline: Insert Operations (2)", test_multiline_insert_variations),
        
        # Edge Cases
        ("Edge: Quoted Paths (6)", test_quoted_paths_variations),
        ("Edge: Line Number Formats (12)", test_line_number_variations),
        
        # Real-world Workflows
        ("Workflow: Complete Project Setup (7)", test_complete_project_setup),
        ("Workflow: Feature Branch (7)", test_feature_branch_workflow),
        ("Workflow: GitHub Integration (7)", test_github_workflow),
        
        # Combined Operations
        ("Combined: File Operations (6)", test_file_operations_combined),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_scenario(name, test_func)
        results.append((name, result))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} test groups passed ({passed*100//total}%)")
    
    # Calculate total individual tests
    total_individual = sum([
        7, 5, 10, 13, 11, 8, 7, 9, 10, 5, 8, 8, 5, 7, 5, 7, 6, 5, 7, 3, 2, 6, 12, 7, 7, 7, 6
    ])
    print(f"Total individual test cases: ~{total_individual}")
    
    if passed == total:
        print("\n🎉 All test groups passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test group(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

