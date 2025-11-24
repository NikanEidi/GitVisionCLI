#!/usr/bin/env python3
"""
Comprehensive test script for all GitVisionCLI scenarios.
This script tests all the scenarios mentioned by the user.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from gitvisioncli.core.command_router import CommandRouter
from gitvisioncli.core.natural_language_action_engine import ActiveFileContext

def test_scenario(name, test_func):
    """Run a test scenario and report results."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)
    try:
        result = test_func()
        if result:
            print(f"✓ PASSED: {name}")
            return True
        else:
            print(f"✗ FAILED: {name}")
            return False
    except Exception as e:
        print(f"✗ ERROR in {name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_1_create_file():
    """Test 1: Create File with Content"""
    with tempfile.TemporaryDirectory() as tmpdir:
        router = CommandRouter()
        action = router.route("create app.py with print(\"Hello World\")")
        if not action:
            return False
        if action.type != "CreateFile":
            return False
        if action.params.get("path") != "app.py":
            return False
        if "Hello World" not in action.params.get("content", ""):
            return False
        return True

def test_2_multiline_creation():
    """Test 2: Multi-line File Creation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        router = CommandRouter()
        multiline_input = """create server.py with
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, World!"
"""
        action = router.route(multiline_input)
        if not action:
            return False
        if action.type != "CreateFile":
            return False
        if action.params.get("path") != "server.py":
            return False
        content = action.params.get("content", "")
        if "from flask import Flask" not in content:
            return False
        if "@app.route" not in content:
            return False
        return True

def test_3_edit_file():
    """Test 3: Open File and Live Edit"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file first
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text('print("Hello")\n')
        
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        action = router.route("add print(\"Updated!\") at the bottom", active_file=active_file)
        if not action:
            return False
        # Should be an append or insert operation
        if action.type not in ["InsertAtBottom", "AppendLine"]:
            print(f"Expected InsertAtBottom or AppendLine, got {action.type}")
            return False
        return True

def test_4_line_operations():
    """Test 4: Line Operations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text('line1\nline2\nline3\nline4\nline5\n')
        
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        # Test insert at line 1
        action1 = router.route("insert import os at line 1", active_file=active_file)
        if not action1 or action1.type not in ["InsertBeforeLine", "InsertAtTop"]:
            print(f"Insert at line 1 failed: {action1}")
            return False
        
        # Test replace line 3
        action2 = router.route("replace line 3 with print(\"Modified\")", active_file=active_file)
        if not action2 or action2.type != "ReplaceLine":
            print(f"Replace line 3 failed: {action2}")
            return False
        
        # Test remove line 5
        action3 = router.route("remove line 5", active_file=active_file)
        if not action3 or action3.type not in ["DeleteLineRange", "DeleteLine"]:
            print(f"Remove line 5 failed: {action3}")
            return False
        
        return True

def test_5_natural_language_delete():
    """Test 5: Natural Language Variations"""
    router = CommandRouter()
    
    variations = [
        "delete file test.py",
        "erase test.py",
        "trash test.py"
    ]
    
    for cmd in variations:
        action = router.route(cmd)
        if not action:
            print(f"Failed to parse: {cmd}")
            return False
        if action.type != "DeleteFile":
            print(f"Wrong action type for '{cmd}': {action.type}")
            return False
        if action.params.get("path") != "test.py":
            print(f"Wrong path for '{cmd}': {action.params.get('path')}")
            return False
    
    return True

def test_6_git_workflow():
    """Test 6: Git Workflow"""
    router = CommandRouter()
    
    commands = [
        ("git init", "GitInit"),
        ("git add .", "GitAdd"),
        ('git commit "Initial commit"', "GitCommit"),
        ("git branch feature", "GitBranch"),
        ("git checkout feature", "GitCheckout"),
    ]
    
    for cmd, expected_type in commands:
        action = router.route(cmd)
        if not action:
            print(f"Failed to parse: {cmd}")
            return False
        if action.type != expected_type:
            print(f"Wrong action type for '{cmd}': expected {expected_type}, got {action.type}")
            return False
    
    return True

def test_7_natural_language_branch():
    """Test 7: Natural Language Branch Switch"""
    router = CommandRouter()
    action = router.route("go to feature")
    if not action:
        return False
    if action.type != "GitCheckout":
        print(f"Expected GitCheckout, got {action.type}")
        return False
    if action.params.get("branch") != "feature":
        print(f"Expected branch 'feature', got {action.params.get('branch')}")
        return False
    return True

def test_8_git_remote():
    """Test 8: Git Remote Operations"""
    router = CommandRouter()
    
    commands = [
        ("git remote add origin https://github.com/user/repo.git", "GitRemote"),
        ("git push -u origin main", "GitPush"),
        ("git pull origin main", "GitPull"),
    ]
    
    for cmd, expected_type in commands:
        action = router.route(cmd)
        if not action:
            print(f"Failed to parse: {cmd}")
            return False
        if action.type != expected_type:
            print(f"Wrong action type for '{cmd}': expected {expected_type}, got {action.type}")
            return False
    
    return True

def test_9_multiline_insert():
    """Test 9: Multi-line Insertions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text('line1\n' * 15)
        
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        multiline_input = """insert at line 10:
def complex_function():
    \"\"\"Docstring\"\"\"
    if condition:
        return result
    return None
"""
        action = router.route(multiline_input, active_file=active_file)
        if not action:
            return False
        if action.type not in ["InsertBlockAtLine", "InsertAfterLine", "InsertBeforeLine"]:
            print(f"Expected insert block operation, got {action.type}")
            return False
        content = action.params.get("content", "") or action.params.get("block", "") or action.params.get("text", "")
        if "def complex_function" not in content:
            print(f"Content not found in action params: {action.params}")
            return False
        return True

def test_10_file_with_spaces():
    """Test 10: File Operations with Spaces"""
    router = CommandRouter()
    
    # Test create with quotes
    action1 = router.route('create "my file.txt" with hello world')
    if not action1:
        return False
    if action1.type != "CreateFile":
        return False
    path = action1.params.get("path", "")
    if path not in ['"my file.txt"', 'my file.txt']:
        print(f"Expected 'my file.txt' (with or without quotes), got '{path}'")
        return False
    
    # Test read with quotes
    action2 = router.route('read "my file.txt"')
    if not action2:
        return False
    if action2.type != "ReadFile":
        return False
    path2 = action2.params.get("path", "")
    if path2 not in ['"my file.txt"', 'my file.txt']:
        print(f"Expected 'my file.txt' (with or without quotes), got '{path2}'")
        return False
    
    return True

def test_11_complete_workflow():
    """Test 11: Complete Git + GitHub Workflow"""
    router = CommandRouter()
    
    commands = [
        ("git init", "GitInit"),
        ('create app.py with print("hello")', "CreateFile"),
        ("git add .", "GitAdd"),
        ('git commit "Initial"', "GitCommit"),
        ("create github repo my-app", "GitHubCreateRepo"),
        ("git remote add origin https://github.com/user/my-app.git", "GitRemote"),
        ("git push -u origin main", "GitPush"),
    ]
    
    for cmd, expected_type in commands:
        action = router.route(cmd)
        if not action:
            print(f"Failed to parse: {cmd}")
            return False
        if action.type != expected_type:
            print(f"Wrong action type for '{cmd}': expected {expected_type}, got {action.type}")
            return False
    
    return True

def test_12_advanced_git():
    """Test 12: Advanced Git Operations"""
    router = CommandRouter()
    
    commands = [
        ("git checkout -b feature", "GitCheckout"),
        ('create feature.py with print("feature")', "CreateFile"),
        ("git add .", "GitAdd"),
        ('git commit "Add feature"', "GitCommit"),
        ("git push -u origin feature", "GitPush"),
        ("git checkout main", "GitCheckout"),
        ("git merge feature", "GitMerge"),
        ("git push", "GitPush"),
    ]
    
    for cmd, expected_type in commands:
        action = router.route(cmd)
        if not action:
            print(f"Failed to parse: {cmd}")
            return False
        if action.type != expected_type:
            print(f"Wrong action type for '{cmd}': expected {expected_type}, got {action.type}")
            return False
    
    return True

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("GITVISION CLI - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Test 1: Create File with Content", test_1_create_file),
        ("Test 2: Multi-line File Creation", test_2_multiline_creation),
        ("Test 3: Open File and Live Edit", test_3_edit_file),
        ("Test 4: Line Operations", test_4_line_operations),
        ("Test 5: Natural Language Variations", test_5_natural_language_delete),
        ("Test 6: Git Workflow", test_6_git_workflow),
        ("Test 7: Natural Language Branch Switch", test_7_natural_language_branch),
        ("Test 8: Git Remote Operations", test_8_git_remote),
        ("Test 9: Multi-line Insertions", test_9_multiline_insert),
        ("Test 10: File Operations with Spaces", test_10_file_with_spaces),
        ("Test 11: Complete Git + GitHub Workflow", test_11_complete_workflow),
        ("Test 12: Advanced Git Operations", test_12_advanced_git),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_scenario(name, test_func)
        results.append((name, result))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

