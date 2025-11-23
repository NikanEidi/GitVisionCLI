# Tests

Unit tests for GitVisionCLI.

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=gitvisioncli

# Specific test
pytest tests/test_editing_engine.py

# Verbose output
pytest -v
```

## Test Files

- `test_brain.py` - Brain/memory system tests
- `test_chat_engine_and_context.py` - Chat engine and context manager tests
- `test_editing_engine.py` - File editing operations tests
- `test_natural_language_mapper.py` - Natural language mapping tests
- `test_provider_normalizer.py` - AI provider normalization tests

## Writing Tests

Follow pytest conventions:
- Test functions start with `test_`
- Use fixtures for common setup
- Test one thing per test function
- Use descriptive names

Example:
```python
def test_delete_line_range():
    """Test deleting a range of lines."""
    engine = EditingEngine()
    content = "line1\nline2\nline3\n"
    result = engine.delete_line_range(content, 2, 2)
    assert result == "line1\nline3\n"
```

## Coverage

Target: 80%+ coverage

Run coverage report:
```bash
pytest --cov=gitvisioncli --cov-report=html
open htmlcov/index.html
```
