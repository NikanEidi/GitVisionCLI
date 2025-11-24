# GitVisionCLI v2.0.0 Release Notes

## 🎉 Major Release - Comprehensive Bug Fixes and Improvements

**Release Date**: December 2024  
**Version**: 2.0.0

---

## 🚀 What's New

### Critical Fixes

1. **`:set-ai` Command Now Works**
   - Fixed routing issue that caused "Unknown command" error
   - Now properly handles both `:set-ai` and `:set-ai <model>` formats
   - Works correctly whether editor is open or closed

2. **Git Commands Fixed**
   - Direct git commands (`git init`, `git add`, `git checkout`, etc.) now work correctly
   - Commands route to shell execution before natural language processing
   - Natural language git operations still work as before

3. **ANSI Code Issues Resolved**
   - Comprehensive ANSI code stripping added to all file operations
   - No more ANSI escape codes appearing in saved files
   - Handles both full sequences and corrupted/partial sequences (like `38;5;46m`)

4. **Line Operations in Editor**
   - Fixed issue where line operations didn't work when editor opened manually
   - Commands like "insert hello in line 1" now work correctly
   - Works whether editor is opened automatically or manually via `:edit`

5. **Panel Synchronization**
   - All panels (`:sheet`, `:tree`, `:banner`, `:models`) work correctly
   - Panel state properly synchronized
   - File system changes properly reflected in panels

### Enhancements

1. **Word Number Support**
   - Can now use word numbers in line operations
   - Examples: "insert text at line one", "remove line twenty-five", "edit line one hundred"
   - Supports numbers zero through one hundred

2. **Improved Pattern Matching**
   - Added support for "edit X in line N with Y" format
   - Better grammar normalization
   - More flexible command parsing

3. **Better Path Resolution**
   - Fixed path resolution to use correct base directory
   - Prevents files from being created instead of edited
   - Consistent file operations across all commands

---

## 📋 All Fixed Issues

### Command Routing
- ✅ `:set-ai` command routing fixed
- ✅ Git command routing fixed
- ✅ Line operation detection improved

### ANSI Code Handling
- ✅ ANSI codes stripped from all file writes
- ✅ Streaming operations strip ANSI codes
- ✅ Corrupted ANSI sequences handled

### Panel Operations
- ✅ Line operations work in manually opened editor
- ✅ Panel synchronization verified
- ✅ All panel commands work correctly

### File Operations
- ✅ Path resolution fixed
- ✅ Files edited instead of created
- ✅ Consistent behavior across all operations

---

## 🐛 Known Minor Issues

The following minor issues may still exist:

1. **Edge Cases**: Some very complex natural language commands may not parse correctly
2. **Performance**: Minor performance issues with very large files during streaming
3. **Rendering**: Occasional rendering glitches in extremely large files

These will be addressed in future patches.

---

## 📦 Installation

Update to v2.0.0:

```bash
pip install --upgrade -e .
```

Or reinstall:

```bash
./reinstall.sh
```

---

## 🔄 Migration from v1.1.0

No breaking changes - this is a backward-compatible release. All existing commands and workflows continue to work.

---

## 📚 Documentation

All documentation has been updated:
- ✅ README.md
- ✅ COMMAND_SHEET.md
- ✅ All docs/ files
- ✅ CONTRIBUTING.md

---

## 🙏 Credits

Thank you for using GitVisionCLI! This release includes comprehensive fixes based on user feedback and testing.

---

## 🔗 Links

- **GitHub**: https://github.com/NikanEidi/gitvisioncli
- **Documentation**: See `docs/` folder
- **Issues**: Report bugs on GitHub Issues

