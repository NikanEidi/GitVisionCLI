# Known Bugs and Issues Documentation

## Where to Document Bugs

### For Version 2.0.0 Release

Document any remaining minor bugs in this file (`BUGS_AND_ISSUES.md`) or in the GitHub Issues section.

### Format for Bug Documentation

```markdown
## Bug Title
**Severity**: Minor / Medium / Major  
**Status**: Open / In Progress / Fixed  
**Reported**: YYYY-MM-DD

**Description**:  
Clear description of the bug

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**:  
What should happen

**Actual Behavior**:  
What actually happens

**Workaround**:  
Any temporary workaround (if available)

**Related Files**:  
- file1.py
- file2.py
```

---

## Current Known Minor Issues (v2.0.0)

### 1. Edge Cases in Natural Language Parsing
**Severity**: Minor  
**Status**: Open

**Description**:  
Some very complex natural language commands with unusual grammar may not be recognized correctly by the natural language action engine.

**Example**:  
Commands with multiple nested clauses or very unusual phrasing might not parse correctly.

**Workaround**:  
Use simpler, more direct commands or use structured commands (e.g., `:edit file.py` then `insert text at line 5`).

---

### 2. Performance with Very Large Files
**Severity**: Minor  
**Status**: Open

**Description**:  
Minor performance issues may occur when streaming very large code blocks (10,000+ lines) during live edit mode.

**Workaround**:  
For very large files, consider editing in smaller chunks or using traditional file operations.

---

### 3. Panel Rendering Edge Cases
**Severity**: Minor  
**Status**: Open

**Description**:  
Occasional rendering glitches may occur in extremely large files when switching between panels rapidly.

**Workaround**:  
Close and reopen the panel if rendering issues occur.

---

## How to Report New Bugs

1. **Check if bug already exists** in this file or GitHub Issues
2. **Create a detailed report** following the format above
3. **Add to this file** or create a GitHub Issue
4. **Include**:
   - Exact command/action that caused the bug
   - Error messages (if any)
   - Steps to reproduce
   - Expected vs actual behavior
   - Your system info (OS, Python version)

---

## Fixed Issues (v2.0.0)

The following issues have been fixed in this release:

✅ `:set-ai` command returning "Unknown command"  
✅ Git commands (git init, git add, git checkout) not working  
✅ ANSI escape codes appearing in saved files  
✅ Line operations not working when editor opened manually  
✅ Files being created instead of edited  
✅ Panel synchronization issues  
✅ Path resolution problems  

See `CHANGELOG.md` for complete list of fixes.

