# 🤝 Contributing to GitVisionCLI

**We welcome contributions!** Thank you for helping make GitVisionCLI better.

<div align="center">

[![Contributing](https://img.shields.io/badge/Contributions-Welcome-green.svg)](https://github.com/NikanEidi/GitVisionCLI)
[![Version](https://img.shields.io/badge/Version-1.1.0-purple.svg)](https://github.com/NikanEidi/GitVisionCLI)

</div>

---

## 📋 **Table of Contents**

- [Code of Conduct](#-code-of-conduct)
- [How Can I Contribute?](#-how-can-i-contribute)
- [Development Setup](#-development-setup)
- [Pull Request Process](#-pull-request-process)
- [Coding Standards](#-coding-standards)
- [Testing Guidelines](#-testing-guidelines)
- [Documentation Updates](#-documentation-updates)
- [Areas for Contribution](#-areas-for-contribution)

---

## 📜 **Code of Conduct**

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct.

**Be respectful, inclusive, and collaborative.**

---

## 💡 **How Can I Contribute?**

### **🐛 Reporting Bugs**

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title** and description
- **Steps to reproduce** (detailed)
- **Expected vs. actual behavior**
- **Environment** (OS, Python version, terminal)
- **Screenshots** if applicable
- **Error messages** (full traceback if available)

**Bug Report Template:**
```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Launch GitVision
2. Execute command X
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: macOS/Windows/Linux
- Python: 3.9+
- Terminal: iTerm2/Alacritty/etc.
- GitVisionCLI version: 1.1.0

## Screenshots
If applicable
```

### **✨ Suggesting Features**

Feature suggestions are welcome! Please:

- **Check existing issues** first
- **Explain the use case** clearly
- **Describe the proposed solution**
- **Consider alternatives**
- **Show examples** if possible

**Feature Request Template:**
```markdown
## Feature Description
Brief description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches you've thought about

## Examples
Code examples or mockups
```

### **🔧 Pull Requests**

- Fix bugs
- Add features
- Improve documentation
- Enhance tests
- Optimize performance
- Improve UI/UX

---

## 🛠️ **Development Setup**

### **1. Fork & Clone**

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/GitVisionCLI.git
cd GitVisionCLI

# Add upstream remote
git remote add upstream https://github.com/NikanEidi/GitVisionCLI.git
```

### **2. Create Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **3. Install in Development Mode**

```bash
pip install -e ".[dev]"
```

This installs:
- All production dependencies
- Development dependencies (pytest, black, mypy, etc.)

### **4. Install Pre-commit Hooks**

```bash
pre-commit install
```

### **5. Set Up API Keys**

```bash
# At least one AI provider
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# Optional: GitHub
export GITHUB_TOKEN="ghp_..."
```

### **6. Verify Installation**

```bash
gitvision doctor
```

Should show all systems operational.

### **7. Run Tests**

```bash
pytest tests/
```

---

## 📝 **Pull Request Process**

### **1. Create a Branch**

```bash
git checkout -b feature/amazing-feature
# or
git checkout -b fix/bug-description
```

**Branch naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `style/` - Code style changes

### **2. Make Changes**

- Write clear, documented code
- Add tests for new features
- Update documentation
- Follow coding standards
- Test your changes thoroughly

### **3. Test Your Changes**

```bash
# Run tests
pytest tests/

# Run type checking
mypy gitvisioncli/

# Run linter
black gitvisioncli/
flake8 gitvisioncli/

# Test manually
gitvision
# Test your changes
```

### **4. Commit**

```bash
git add .
git commit -m "feat: add amazing feature"
```

**Commit message format:**

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Maintenance

**Examples:**
```
feat: add multiline input support
fix: resolve duplicate panel rendering
docs: update command reference
refactor: improve error handling
test: add tests for line editing
```

### **5. Push & Create PR**

```bash
git push origin feature/amazing-feature
```

Then create a Pull Request on GitHub with:

- **Clear title**
- **Description of changes**
- **Related issues** (if any)
- **Screenshots** (if UI changes)
- **Test results**
- **Checklist** of what was tested

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Tests pass
- [ ] Manual testing completed
- [ ] All features work as expected

## Screenshots
If applicable

## Related Issues
Closes #123
```

---

## 🎨 **Coding Standards**

### **Python Style**

- **PEP 8** compliance
- **Black** for formatting (line length: 88)
- **Type hints** for all functions
- **Docstrings** for public APIs

**Example:**

```python
def delete_line_range(
    self, content: str, start_line: int, end_line: int
) -> str:
    """
    Delete a range of lines from content.
    
    Args:
        content: File content
        start_line: Starting line (1-indexed)
        end_line: Ending line (1-indexed, inclusive)
        
    Returns:
        Modified content with lines removed
        
    Raises:
        ValueError: If line numbers are invalid
    """
    # Implementation
    pass
```

### **File Organization**

```
gitvisioncli/
├── core/              # Core logic
│   ├── chat_engine.py
│   ├── editing_engine.py
│   ├── supervisor.py
│   └── natural_language_action_engine.py
├── ui/                # UI components
│   ├── dual_panel.py
│   ├── chat_box.py
│   └── colors.py
├── workspace/         # Workspace panels
│   ├── banner_panel.py
│   ├── tree_panel.py
│   ├── editor_panel.py
│   └── sheet_panel.py
└── providers/         # AI providers (if needed)
    ├── openai_provider.py
    └── claude_provider.py
```

### **Testing**

- **pytest** for all tests
- **Test coverage** > 80%
- **Unit tests** for core logic
- **Integration tests** for workflows

**Example:**

```python
def test_delete_line_range():
    """Test deleting a range of lines."""
    engine = EditingEngine()
    content = "line1\nline2\nline3\nline4\n"
    result = engine.delete_line_range(content, 2, 3)
    assert result == "line1\nline4\n"
```

### **Documentation**

- **Docstrings** for all public functions/classes
- **Inline comments** for complex logic
- **README** updates for new features
- **CHANGELOG** entries

---

## 🧪 **Testing Guidelines**

### **Run Tests**

```bash
# All tests
pytest

# With coverage
pytest --cov=gitvisioncli

# Specific file
pytest tests/test_editing_engine.py

# Verbose
pytest -v

# With output
pytest -s
```

### **Write Tests**

- Test normal cases
- Test edge cases
- Test error conditions
- Mock external dependencies
- Test UI components (if applicable)

**Test Structure:**
```python
def test_feature_name():
    """Test description."""
    # Arrange
    engine = EditingEngine()
    content = "test content"
    
    # Act
    result = engine.some_method(content)
    
    # Assert
    assert result == expected
```

---

## 📚 **Documentation Updates**

When adding features, update:

- `README.md` - If it's a major feature
- `docs/COMMANDS.md` - For new commands
- `docs/FEATURES.md` - For feature details
- `docs/QUICKSTART.md` - If it affects getting started
- `CHANGELOG.md` - Always!
- `docs/RUN_AND_TEST.md` - If it affects testing

**Documentation Standards:**
- Clear, concise descriptions
- Code examples for all commands
- Expected results
- Troubleshooting tips
- Cross-references to related docs

---

## 🎯 **Areas for Contribution**

### **High Priority**

- Additional AI provider integrations
- Enhanced Git visualization
- Syntax highlighting in editor
- Improved error messages
- Performance optimizations
- Better test coverage
- Enhanced UI/UX

### **Good First Issues**

- Documentation improvements
- Test coverage
- UI polish
- Bug fixes
- Code cleanup
- Example additions

### **Advanced**

- Plugin system
- Collaborative editing
- Custom AI prompts
- Advanced search
- Code snippets
- Performance profiling

---

## 🔍 **Code Review Process**

1. **Automated Checks**: CI runs tests, linting, type checking
2. **Manual Review**: Maintainers review code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, PR is merged

**Review Criteria:**
- Code quality and style
- Test coverage
- Documentation updates
- Backward compatibility
- Performance impact

---

## ❓ **Questions?**

- **Discussions:** Use GitHub Discussions
- **Issues:** Create an issue for bugs/features
- **Email:** Contact maintainers (if applicable)

---

## 🌟 **Recognition**

Contributors will be:

- Listed in `CONTRIBUTORS.md` (if applicable)
- Mentioned in release notes
- Forever appreciated! 🙏

---

## 📖 **Resources**

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)

---

**Thank you for contributing to GitVisionCLI!** ❤️

---

**Version**: 1.1.0  
**Last Updated**: 2024-12-XX
