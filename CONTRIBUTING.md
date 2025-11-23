# 🤝 Contributing to GitVisionCLI

**We welcome contributions!** Thank you for helping make GitVisionCLI better.

---

## 📋 **Table of Contents**

- [Code of Conduct](#-code-of-conduct)
- [How Can I Contribute?](#-how-can-i-contribute)
- [Development Setup](#-development-setup)
- [Pull Request Process](#-pull-request-process)
- [Coding Standards](#-coding-standards)

---

## 📜 **Code of Conduct**

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct.

**Be respectful, inclusive, and collaborative.**

---

## 💡 **How Can I Contribute?**

### **🐛 Reporting Bugs**

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title** and description
- **Steps to reproduce**
- **Expected vs. actual behavior**
- **Environment** (OS, Python version, terminal)
- **Screenshots** if applicable

### **✨ Suggesting Features**

Feature suggestions are welcome! Please:

- **Check existing issues** first
- **Explain the use case**
- **Describe the proposed solution**
- **Consider alternatives**

### **🔧 Pull Requests**

- Fix bugs
- Add features
- Improve documentation
- Enhance tests

---

## 🛠️ **Development Setup**

### **1. Fork & Clone**

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/GitVisionCLI.git
cd GitVisionCLI
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

### **4. Install Pre-commit Hooks**

```bash
pre-commit install
```

### **5. Run Tests**

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

### **2. Make Changes**

- Write clear, documented code
- Add tests for new features
- Update documentation
- Follow coding standards

### **3. Test Your Changes**

```bash
# Run tests
pytest tests/

# Run type checking
mypy gitvisioncli/

# Run linter
black gitvisioncli/
flake8 gitvisioncli/
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
│   └── supervisor.py
├── ui/                # UI components
│   └── dual_panel.py
├── workspace/         # Workspace panels
│   ├── banner_panel.py
│   └── tree_panel.py
└── providers/         # AI providers
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
```

### **Write Tests**

- Test normal cases
- Test edge cases
- Test error conditions
- Mock external dependencies

---

## 📚 **Documentation Updates**

When adding features, update:

- `README.md` - If it's a major feature
- `docs/COMMANDS.md` - For new commands
- `docs/FEATURES.md` - For feature details
- `CHANGELOG.md` - Always!

---

## 🎯 **Areas for Contribution**

### **High Priority**

- Additional AI provider integrations
- Enhanced Git visualization
- Syntax highlighting in editor
- Improved error messages
- Performance optimizations

### **Good First Issues**

- Documentation improvements
- Test coverage
- UI polish
- Bug fixes

---

## ❓ **Questions?**

- **Discussions:** Use GitHub Discussions
- **Chat:** Join our community (if applicable)
- **Email:** Contact maintainers

---

## 🌟 **Recognition**

Contributors will be:

- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- Forever appreciated! 🙏

---

**Thank you for contributing to GitVisionCLI!** ❤️
