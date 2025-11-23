#!/usr/bin/env python3
"""
Validation script for AI editing pipeline improvements.
Tests the new methods in ProviderNormalizer and NaturalLanguageEditMapper.
"""

import sys
from pathlib import Path

# Ensure local project root is importable in a portable way
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from gitvisioncli.core.provider_normalizer import ProviderNormalizer, NormalizedToolCall
from gitvisioncli.core.natural_language_mapper import NaturalLanguageEditMapper, FileContext

def test_provider_normalizer():
    print("=" * 60)
    print("Testing ProviderNormalizer Enhancements")
    print("=" * 60)
    
    normalizer = ProviderNormalizer()
    
    # Test 1: Extract code from assistant text
    print("\n1. Testing extract_code_from_assistant_text()...")
    text_with_code = """Here's the code you requested:
```python
def hello():
    print("Hello, World!")
```
This should work perfectly."""
    
    extracted = normalizer.extract_code_from_assistant_text(text_with_code)
    assert extracted is not None, "Should extract code from fenced block"
    assert "def hello()" in extracted, "Should contain function definition"
    print("   ✓ Successfully extracted code from fenced block")
    
    # Test 2: Normalize edit action with missing content
    print("\n2. Testing normalize_edit_action()...")
    incomplete_action = {
        "type": "EditFile",
        "params": {
            "path": "test.py",
            "content": None
        }
    }
    
    normalized = normalizer.normalize_edit_action(incomplete_action)
    assert normalized.get("_incomplete") == True, "Should flag incomplete action"
    assert normalized.get("_missing_field") == "content", "Should identify missing field"
    print("   ✓ Successfully detected incomplete EditFile action")
    
    # Test 3: Combine text and tool call
    print("\n3. Testing combine_text_and_tool_call()...")
    assistant_text = """I'll create that file for you:
```python
print("test")
```"""
    
    tool_call = NormalizedToolCall(
        name="execute_action",
        arguments={
            "action": {
                "type": "CreateFile",
                "params": {
                    "path": "test.py",
                    "content": None
                }
            }
        }
    )
    
    combined = normalizer.combine_text_and_tool_call(assistant_text, tool_call)
    content = combined.arguments["action"]["params"].get("content")
    assert content is not None, "Should fill in missing content"
    assert 'print("test")' in content, "Should extract code from text"
    print("   ✓ Successfully combined text with tool call")
    
    print("\n✅ All ProviderNormalizer tests passed!")


def test_natural_language_mapper():
    print("\n" + "=" * 60)
    print("Testing NaturalLanguageEditMapper Enhancements")
    print("=" * 60)
    
    mapper = NaturalLanguageEditMapper()
    
    # Test 1: Vague "add this" instruction
    print("\n1. Testing vague 'add this' instruction...")
    ctx = FileContext(path="test.py", content="# existing code\n")
    result = mapper.map_instruction(
        "add this code here",
        active_file=ctx,
        attached_block="print('new code')"
    )
    
    assert not result.error, f"Should not error: {result.error}"
    assert not result.clarification, f"Should not need clarification: {result.clarification}"
    assert len(result.intents) == 1, "Should return one intent"
    assert result.intents[0].type == "AppendBlock", "Should default to AppendBlock"
    assert result.intents[0].params["text"] == "print('new code')", "Should include the block"
    print("   ✓ Successfully mapped vague 'add this' to AppendBlock")
    
    # Test 2: Vague "write X in this file" instruction
    print("\n2. Testing 'write X in this file' instruction...")
    result = mapper.map_instruction(
        "write this in this file",
        active_file=ctx,
        attached_block="def foo():\n    pass"
    )
    
    assert len(result.intents) == 1, "Should return one intent"
    assert result.intents[0].type == "AppendBlock", "Should default to AppendBlock"
    print("   ✓ Successfully mapped 'write X' to AppendBlock")
    
    # Test 3: Vague "update" instruction asks for clarification
    print("\n3. Testing vague 'update' instruction...")
    result = mapper.map_instruction(
        "update this function",
        active_file=ctx,
        attached_block=None
    )
    
    assert result.clarification is not None, "Should ask for clarification"
    assert "specify" in result.clarification.lower(), "Should ask to specify location"
    print("   ✓ Successfully requested clarification for vague update")
    
    # Test 4: Existing functionality still works
    print("\n4. Testing existing 'after line N' functionality...")
    result = mapper.map_instruction(
        "add this after line 5",
        active_file=ctx,
        attached_block="new_line()"
    )
    
    assert len(result.intents) == 1, "Should return one intent"
    assert result.intents[0].type == "InsertAfterLine", "Should use InsertAfterLine"
    assert result.intents[0].params["line_number"] == 5, "Should target line 5"
    print("   ✓ Existing functionality preserved")
    
    print("\n✅ All NaturalLanguageEditMapper tests passed!")


if __name__ == "__main__":
    try:
        test_provider_normalizer()
        test_natural_language_mapper()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("  • ProviderNormalizer can extract code from text")
        print("  • ProviderNormalizer can detect incomplete actions")
        print("  • ProviderNormalizer can combine text + tool calls")
        print("  • NaturalLanguageEditMapper handles vague 'add' instructions")
        print("  • NaturalLanguageEditMapper defaults to AppendBlock when appropriate")
        print("  • NaturalLanguageEditMapper asks for clarification when needed")
        print("  • Existing functionality is preserved")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
