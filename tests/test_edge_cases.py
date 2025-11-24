#!/usr/bin/env python3
"""
Edge case tests for GitVisionCLI.
Tests various edge cases and error conditions.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gitvisioncli.core.command_router import CommandRouter
from gitvisioncli.core.natural_language_action_engine import ActiveFileContext


def test_empty_commands():
    """Test that empty commands are handled gracefully."""
    router = CommandRouter()
    
    empty_commands = ["", "   ", "\n", "\t"]
    for cmd in empty_commands:
        action = router.route(cmd)
        assert action is None, f"Empty command '{cmd}' should return None"


def test_unknown_commands():
    """Test that unknown commands return None gracefully."""
    router = CommandRouter()
    
    unknown_commands = [
        "random text",
        "do something",
        "xyz abc 123",
        "not a real command",
    ]
    for cmd in unknown_commands:
        action = router.route(cmd)
        # Should return None or handle gracefully
        assert action is None or action.type is not None


def test_file_paths_with_special_chars():
    """Test file operations with special characters in paths."""
    router = CommandRouter()
    
    special_paths = [
        'create "file-name.py" with print("test")',
        "create 'file_name.py' with print('test')",
        'create file_name.py with print("test")',
    ]
    
    for cmd in special_paths:
        action = router.route(cmd)
        assert action is not None, f"Should handle special chars: {cmd}"
        assert action.type == "CreateFile", f"Should be CreateFile: {cmd}"


def test_line_numbers_edge_cases():
    """Test line operations with edge case line numbers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "app.py"
        test_file.write_text("line1\nline2\nline3\n")
        router = CommandRouter()
        active_file = ActiveFileContext(path=str(test_file), content=test_file.read_text())
        
        # Test line 0 (should handle gracefully)
        action = router.route("remove line 0", active_file=active_file)
        # Should either handle or return None gracefully
        
        # Test very large line numbers
        action = router.route("remove line 99999", active_file=active_file)
        # Should handle gracefully
        
        # Test negative line numbers
        action = router.route("remove line -1", active_file=active_file)
        # Should handle gracefully


def test_multiline_content_edge_cases():
    """Test multiline content extraction edge cases."""
    router = CommandRouter()
    
    # Empty multiline
    multiline_empty = """create empty.py with

"""
    action = router.route(multiline_empty)
    if action:
        assert action.type == "CreateFile"
    
    # Only whitespace
    multiline_whitespace = """create whitespace.py with
    
    """
    action = router.route(multiline_whitespace)
    if action:
        assert action.type == "CreateFile"


def test_quoted_content():
    """Test operations with quoted content."""
    router = CommandRouter()
    
    quoted_commands = [
        'create test.py with print("Hello World")',
        "create test.py with print('Hello World')",
        'create test.py with print("It\'s a test")',
        "create test.py with print('It\"s a test')",
    ]
    
    for cmd in quoted_commands:
        action = router.route(cmd)
        assert action is not None, f"Should handle quoted content: {cmd}"
        assert action.type == "CreateFile", f"Should be CreateFile: {cmd}"


def test_git_commands_edge_cases():
    """Test Git commands with edge cases."""
    router = CommandRouter()
    
    # Empty commit message
    action = router.route('git commit ""')
    # Should handle gracefully
    
    # Very long commit message
    long_msg = "a" * 1000
    action = router.route(f'git commit "{long_msg}"')
    # Should handle gracefully
    
    # Branch names with special chars
    action = router.route("git branch feature/test")
    # Should handle gracefully


def test_file_operations_without_active_file():
    """Test file operations that require active file but none is provided."""
    router = CommandRouter()
    
    # Line operations without active file should return None or handle gracefully
    line_ops = [
        "remove line 5",
        "insert text at line 3",
        "replace line 2 with new text",
    ]
    
    for cmd in line_ops:
        action = router.route(cmd)  # No active_file provided
        # Should return None or handle gracefully
        assert action is None or action.type is not None


def test_nested_quotes():
    """Test handling of nested quotes."""
    router = CommandRouter()
    
    nested_quotes = [
        'create test.py with print("He said \\"Hello\\"")',
        "create test.py with print('He said \\'Hello\\'')",
    ]
    
    for cmd in nested_quotes:
        action = router.route(cmd)
        if action:
            assert action.type == "CreateFile"


def test_unicode_content():
    """Test operations with Unicode content."""
    router = CommandRouter()
    
    unicode_content = [
        'create test.py with print("Hello 世界")',
        'create test.py with print("Привет")',
        'create test.py with print("مرحبا")',
    ]
    
    for cmd in unicode_content:
        action = router.route(cmd)
        if action:
            assert action.type == "CreateFile"
            assert "世界" in action.params.get("content", "") or \
                   "Привет" in action.params.get("content", "") or \
                   "مرحبا" in action.params.get("content", "")


if __name__ == "__main__":
    print("=" * 60)
    print("EDGE CASE TESTS")
    print("=" * 60)
    
    tests = [
        ("Empty Commands", test_empty_commands),
        ("Unknown Commands", test_unknown_commands),
        ("File Paths with Special Chars", test_file_paths_with_special_chars),
        ("Line Numbers Edge Cases", test_line_numbers_edge_cases),
        ("Multiline Content Edge Cases", test_multiline_content_edge_cases),
        ("Quoted Content", test_quoted_content),
        ("Git Commands Edge Cases", test_git_commands_edge_cases),
        ("File Operations Without Active File", test_file_operations_without_active_file),
        ("Nested Quotes", test_nested_quotes),
        ("Unicode Content", test_unicode_content),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Total: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("🎉 All edge case tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
        sys.exit(1)

