# Changelog

All notable changes to GitVisionCLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-XX

### 🎉 Major Release - Comprehensive Fixes and Improvements

This release includes major bug fixes, comprehensive ANSI code handling, improved command routing, and enhanced panel synchronization.

### ✨ Added

- **Comprehensive ANSI Code Stripping**: Added shared ANSI utility module (`gitvisioncli/utils/ansi_utils.py`) that handles both full ANSI sequences and corrupted/partial sequences (like `38;5;46m`)
- **Word-to-Number Conversion**: Expanded grammar normalization to support word numbers (zero through one hundred) in line operations
- **Enhanced Line Operation Detection**: Added support for "edit X in line N with Y" format (e.g., "edit hi in line one with hello")
- **Improved Path Resolution**: Fixed path resolution to use executor's base_dir for consistent file operations

### 🔧 Fixed

#### Command Routing
- **Fixed `:set-ai` command**: Now properly handles both `:set-ai` and `:set-ai <model>` formats. Workspace handler no longer intercepts this command.
- **Fixed Git Command Routing**: Git commands (`git init`, `git add`, `git checkout`, etc.) now explicitly route to shell execution before natural language processing, ensuring they work correctly as direct commands while preserving natural language git operations.

#### ANSI Code Handling
- **Comprehensive ANSI Stripping**: All file write operations now strip ANSI codes:
  - `safe_patch_engine.py`: All file operations (rewrite, append, replace_block, insert_block_before_match, insert_block_after_match)
  - `supervisor.py`: `_normalize_content()` and `_write_safe()` methods
  - `editor_panel.py`: File loading and saving operations
  - Streaming operations: ANSI codes stripped during live edit streaming
- **Corrupted ANSI Sequence Handling**: Now properly handles corrupted sequences like `38;5;46m` that appear in files

#### Panel Operations
- **Line-Based Operations in Editor**: Fixed issue where line-based operations (insert, add, remove, edit) didn't work when editor panel was opened manually via `:edit`. Now properly routes to action engine instead of live edit mode.
- **Panel Synchronization**: Verified and ensured all panels (`:sheet`, `:tree`, `:banner`, `:models`, `:edit`) work correctly
- **Editor Panel State**: Fixed editor panel state management when closing and reopening

#### Path Resolution
- **Fixed File Path Resolution**: Line-based operations now use executor's base_dir for path resolution, ensuring files are edited correctly instead of being created

### 🔄 Changed

- **Version Updated**: Bumped version from 1.1.0 to 2.0.0
- **Grammar Normalization**: Enhanced to support word numbers (zero through one hundred) in both hyphenated and space-separated formats
- **Command Detection Priority**: Line-based operations are now checked before live edit mode to ensure proper routing

### 📝 Documentation

- **Version Updates**: All markdown files updated to reflect version 2.0.0
- **Command References**: Verified all command examples are accurate
- **Feature Documentation**: All features documented correctly

### 🐛 Known Minor Issues

The following minor bugs may still exist and will be addressed in future patches:

1. **Edge Cases in Natural Language Parsing**: Some complex natural language commands may not be recognized correctly
2. **Panel Rendering**: Occasional rendering glitches in very large files
3. **Streaming Performance**: Minor performance issues with very large code blocks during live edit streaming

### 🔍 Technical Details

#### Files Modified
- `gitvisioncli/cli.py`: Command routing fixes, line operation detection
- `gitvisioncli/core/safe_patch_engine.py`: ANSI stripping in all file operations
- `gitvisioncli/core/supervisor.py`: ANSI stripping, path resolution
- `gitvisioncli/core/natural_language_action_engine.py`: Word number support, pattern improvements
- `gitvisioncli/workspace/editor_panel.py`: ANSI stripping, file operations
- `gitvisioncli/utils/ansi_utils.py`: New shared ANSI utility module
- All markdown files: Version updates

#### Breaking Changes
None - This is a backward-compatible release with bug fixes and improvements.

---

## [1.1.0] - Previous Release

See git history for previous changelog entries.

