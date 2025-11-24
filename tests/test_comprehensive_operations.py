#!/usr/bin/env python3
"""
Comprehensive Test Suite for All GitVisionCLI Operations

This test suite covers all operations supported by the system:
- File Operations (create, read, delete, rename, move, copy)
- Line Operations (insert, replace, delete, append)
- Git Operations (init, add, commit, branch, checkout, merge, push, pull, remote)
- GitHub Operations (create repo, create issue, create PR)
- Edge Cases and Variations
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
# FILE OPERATIONS
# ============================================================================

def test_file_create_single_line():
    """Create file with single line content"""
    router = CommandRouter()
    action = router.route('create test.py with print("hello")')
    return action and action.type == "CreateFile" and action.params.get("path") == "test.py"

def test_file_create_multiline():
    """Create file with multiline content"""
    router = CommandRouter()
    multiline = """create app.py with
def main():
    print("Hello")
"""
    action = router.route(multiline)
    return action and action.type == "CreateFile" and "def main" in action.params.get("content", "")

def test_file_create_with_quotes():
    """Create file with quoted path"""
    router = CommandRouter()
    action = router.route('create "my file.txt" with hello')
    path = action.params.get("path", "") if action else ""
    return action and action.type == "CreateFile" and ("my file.txt" in path or '"my file.txt"' in path)

def test_file_read():
    """Read file operation"""
    router = CommandRouter()
    action = router.route("read file app.py")
    return action and action.type == "ReadFile" and action.params.get("path") == "app.py"

def test_file_read_quoted():
    """Read file with quoted path"""
    router = CommandRouter()
    action = router.route('read "my file.txt"')
    path = action.params.get("path", "") if action else ""
    return action and action.type == "ReadFile" and ("my file.txt" in path or '"my file.txt"' in path)

def test_file_delete():
    """Delete file operation"""
    router = CommandRouter()
    action = router.route("delete file test.py")
    return action and action.type == "DeleteFile" and action.params.get("path") == "test.py"

def test_file_delete_erase():
    """Delete file with 'erase' variation"""
    router = CommandRouter()
    action = router.route("erase test.py")
    return action and action.type == "DeleteFile"

def test_file_delete_trash():
    """Delete file with 'trash' variation"""
    router = CommandRouter()
    action = router.route("trash test.py")
    return action and action.type == "DeleteFile"

def test_file_rename():
    """Rename file operation"""
    router = CommandRouter()
    action = router.route("rename old.py to new.py")
    return action and action.type == "RenameFile"

def test_file_move():
    """Move file operation"""
    router = CommandRouter()
    action = router.route("move app.py to src/")
    return action and action.type == "MoveFile"

def test_file_copy():
    """Copy file operation"""
    router = CommandRouter()
    action = router.route("copy app.py to backup.py")
    return action and action.type == "CopyFile"

# ============================================================================
# LINE OPERATIONS
# ============================================================================

def test_line_insert_before():
    """Insert before line"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        action = router.route("insert import os before line 1", active_file=active_file)
        return action and action.type in ["InsertBeforeLine", "InsertAtTop"]

def test_line_insert_after():
    """Insert after line"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        action = router.route("insert print('hi') after line 1", active_file=active_file)
        return action and action.type == "InsertAfterLine"

def test_line_insert_at():
    """Insert at line"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        action = router.route("insert import os at line 1", active_file=active_file)
        return action and action.type in ["InsertBeforeLine", "InsertAtTop"]

def test_line_insert_at_top():
    """Insert at top"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        action = router.route("add # comment at top", active_file=active_file)
        return action and action.type == "InsertAtTop"

def test_line_insert_at_bottom():
    """Insert at bottom"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        action = router.route("add print('end') at bottom", active_file=active_file)
        return action and action.type == "InsertAtBottom"

def test_line_replace():
    """Replace line"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\nline3\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        action = router.route("replace line 2 with print('new')", active_file=active_file)
        return action and action.type == "ReplaceLine"

def test_line_delete_single():
    """Delete single line"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\nline3\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        action = router.route("remove line 2", active_file=active_file)
        return action and action.type in ["DeleteLineRange", "DeleteLine"]

def test_line_delete_range():
    """Delete line range"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\nline3\nline4\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        action = router.route("delete lines 2-3", active_file=active_file)
        return action and action.type == "DeleteLineRange"

def test_line_insert_block():
    """Insert multiline block"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\n" * 10)
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        multiline = """insert at line 5:
def func():
    return True
"""
        action = router.route(multiline, active_file=active_file)
        if not action:
            return False
        content = action.params.get("content", "") or action.params.get("block", "") or action.params.get("text", "")
        return action.type in ["InsertBlockAtLine", "InsertBeforeLine", "InsertAfterLine"] and "def func" in content

# ============================================================================
# GIT OPERATIONS
# ============================================================================

def test_git_init():
    """Git init operation"""
    router = CommandRouter()
    action = router.route("git init")
    return action and action.type == "GitInit"

def test_git_add_dot():
    """Git add . operation"""
    router = CommandRouter()
    action = router.route("git add .")
    return action and action.type == "GitAdd" and action.params.get("path") == "."

def test_git_add_file():
    """Git add specific file"""
    router = CommandRouter()
    action = router.route("git add app.py")
    return action and action.type == "GitAdd"

def test_git_add_all():
    """Git add all"""
    router = CommandRouter()
    action = router.route("git add all")
    return action and action.type == "GitAdd"

def test_git_commit_quoted():
    """Git commit with quoted message"""
    router = CommandRouter()
    action = router.route('git commit "Initial commit"')
    return action and action.type == "GitCommit" and "Initial commit" in action.params.get("message", "")

def test_git_commit_unquoted():
    """Git commit with unquoted message"""
    router = CommandRouter()
    action = router.route("git commit Initial")
    return action and action.type == "GitCommit"

def test_git_commit_with_m():
    """Git commit with -m flag"""
    router = CommandRouter()
    action = router.route('git commit -m "Test message"')
    return action and action.type == "GitCommit"

def test_git_branch():
    """Git branch creation"""
    router = CommandRouter()
    action = router.route("git branch feature")
    return action and action.type == "GitBranch" and action.params.get("name") == "feature"

def test_git_checkout():
    """Git checkout branch"""
    router = CommandRouter()
    action = router.route("git checkout main")
    return action and action.type == "GitCheckout" and action.params.get("branch") == "main"

def test_git_checkout_b():
    """Git checkout -b (create and switch)"""
    router = CommandRouter()
    action = router.route("git checkout -b feature")
    return action and action.type == "GitCheckout" and action.params.get("create_new") == True

def test_git_checkout_natural():
    """Git checkout with natural language"""
    router = CommandRouter()
    action = router.route("go to feature")
    return action and action.type == "GitCheckout" and action.params.get("branch") == "feature"

def test_git_merge():
    """Git merge operation"""
    router = CommandRouter()
    action = router.route("git merge feature")
    return action and action.type == "GitMerge" and action.params.get("branch") == "feature"

def test_git_push():
    """Git push operation"""
    router = CommandRouter()
    action = router.route("git push")
    return action and action.type == "GitPush"

def test_git_push_remote_branch():
    """Git push with remote and branch"""
    router = CommandRouter()
    action = router.route("git push origin main")
    return action and action.type == "GitPush" and action.params.get("remote") == "origin"

def test_git_push_u():
    """Git push with -u flag"""
    router = CommandRouter()
    action = router.route("git push -u origin main")
    return action and action.type == "GitPush" and action.params.get("remote") == "origin"

def test_git_pull():
    """Git pull operation"""
    router = CommandRouter()
    action = router.route("git pull")
    return action and action.type == "GitPull"

def test_git_pull_remote_branch():
    """Git pull with remote and branch"""
    router = CommandRouter()
    action = router.route("git pull origin main")
    return action and action.type == "GitPull" and action.params.get("remote") == "origin"

def test_git_remote_add():
    """Git remote add operation"""
    router = CommandRouter()
    action = router.route("git remote add origin https://github.com/user/repo.git")
    return action and action.type == "GitRemote" and action.params.get("operation") == "add"

def test_git_remote_remove():
    """Git remote remove operation"""
    router = CommandRouter()
    action = router.route("git remote remove origin")
    return action and action.type == "GitRemote" and action.params.get("operation") == "remove"

# ============================================================================
# GITHUB OPERATIONS
# ============================================================================

def test_github_create_repo():
    """GitHub create repository"""
    router = CommandRouter()
    action = router.route("create github repo my-app")
    return action and action.type == "GitHubCreateRepo" and action.params.get("name") == "my-app"

def test_github_create_repo_private():
    """GitHub create private repository"""
    router = CommandRouter()
    action = router.route("create github repo my-app private")
    return action and action.type == "GitHubCreateRepo" and action.params.get("private") == True

def test_github_create_repo_public():
    """GitHub create public repository"""
    router = CommandRouter()
    action = router.route("create github repo my-app public")
    return action and action.type == "GitHubCreateRepo" and action.params.get("private") == False

def test_github_create_issue():
    """GitHub create issue"""
    router = CommandRouter()
    action = router.route('create github issue "Bug fix"')
    return action and action.type == "GitHubCreateIssue"

def test_github_create_pr():
    """GitHub create pull request"""
    router = CommandRouter()
    # Try both "pr" and "pull request" variations
    action = router.route('create github pr "New feature"')
    if not action or action.type != "GitHubCreatePR":
        # Try full form
        action = router.route('create github pull request "New feature"')
    return action and action.type == "GitHubCreatePR"

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all comprehensive tests."""
    print("\n" + "="*70)
    print("COMPREHENSIVE GITVISION CLI TEST SUITE")
    print("="*70)
    
    tests = [
        # File Operations
        ("File: Create Single Line", test_file_create_single_line),
        ("File: Create Multiline", test_file_create_multiline),
        ("File: Create With Quotes", test_file_create_with_quotes),
        ("File: Read", test_file_read),
        ("File: Read Quoted", test_file_read_quoted),
        ("File: Delete", test_file_delete),
        ("File: Delete (erase)", test_file_delete_erase),
        ("File: Delete (trash)", test_file_delete_trash),
        ("File: Rename", test_file_rename),
        ("File: Move", test_file_move),
        ("File: Copy", test_file_copy),
        
        # Line Operations
        ("Line: Insert Before", test_line_insert_before),
        ("Line: Insert After", test_line_insert_after),
        ("Line: Insert At", test_line_insert_at),
        ("Line: Insert At Top", test_line_insert_at_top),
        ("Line: Insert At Bottom", test_line_insert_at_bottom),
        ("Line: Replace", test_line_replace),
        ("Line: Delete Single", test_line_delete_single),
        ("Line: Delete Range", test_line_delete_range),
        ("Line: Insert Block", test_line_insert_block),
        
        # Git Operations
        ("Git: Init", test_git_init),
        ("Git: Add .", test_git_add_dot),
        ("Git: Add File", test_git_add_file),
        ("Git: Add All", test_git_add_all),
        ("Git: Commit Quoted", test_git_commit_quoted),
        ("Git: Commit Unquoted", test_git_commit_unquoted),
        ("Git: Commit -m", test_git_commit_with_m),
        ("Git: Branch", test_git_branch),
        ("Git: Checkout", test_git_checkout),
        ("Git: Checkout -b", test_git_checkout_b),
        ("Git: Checkout Natural", test_git_checkout_natural),
        ("Git: Merge", test_git_merge),
        ("Git: Push", test_git_push),
        ("Git: Push Remote Branch", test_git_push_remote_branch),
        ("Git: Push -u", test_git_push_u),
        ("Git: Pull", test_git_pull),
        ("Git: Pull Remote Branch", test_git_pull_remote_branch),
        ("Git: Remote Add", test_git_remote_add),
        ("Git: Remote Remove", test_git_remote_remove),
        
        # GitHub Operations
        ("GitHub: Create Repo", test_github_create_repo),
        ("GitHub: Create Repo Private", test_github_create_repo_private),
        ("GitHub: Create Repo Public", test_github_create_repo_public),
        ("GitHub: Create Issue", test_github_create_issue),
        ("GitHub: Create PR", test_github_create_pr),
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
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

