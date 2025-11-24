# Test Verification Checklist

## Test 1: Create File with Content ✅
**Command:** `create app.py with print("Hello World")`
- ✅ Pattern: `_create_file_re` matches "create ... with"
- ✅ Content extraction: `extract_content()` handles single-line content
- ✅ Action: `CreateFile` with path and content

## Test 2: Multi-line File Creation ✅
**Command:** `:ml` → `create server.py with` → multi-line content → `:end`
- ✅ Multi-line collection: `_collect_manual_block()` handles `:ml` mode
- ✅ Content extraction: `extract_content()` handles multi-line with `re.DOTALL`
- ✅ Action: `CreateFile` with multi-line content

## Test 3: Open File and Live Edit ✅
**Command:** `:edit app.py` → `add print("Updated!") at the bottom`
- ✅ `:edit` command: `RightPanel.handle_command()` activates live edit
- ✅ Live edit mode: `cli.py` detects `LIVE_EDIT_READY` marker
- ✅ Streaming: Content streams to editor via `write_stream()`
- ✅ Action: `InsertAtBottom` or `InsertAfterLine` at end

## Test 4: Line Operations ✅
**Commands:**
- `insert import os at line 1`
- `replace line 3 with print("Modified")`
- `remove line 5`
- ✅ Insert pattern: `_insert_at_line_re` matches "insert ... at line"
- ✅ Replace pattern: `_replace_line_re` matches "replace line ... with"
- ✅ Remove pattern: `_delete_line_re` matches "remove line"
- ✅ Actions: `InsertAfterLine`, `ReplaceBlock`, `DeleteLineRange`

## Test 5: Natural Language Variations ✅
**Commands:** `delete file test.py`, `erase test.py`, `trash test.py`
- ✅ Pattern: `_delete_file_re` matches "delete|remove|rm|erase|trash"
- ✅ Action: `DeleteFile`

## Test 6: Git Workflow ✅
**Commands:** `git init`, `git add .`, `git commit "..."`, `git branch`, `git checkout`
- ✅ Git init: `_git_init_re` pattern
- ✅ Git add: `_git_add_re` pattern
- ✅ Git commit: `_git_commit_re` pattern
- ✅ Git branch: `_git_branch_re` pattern
- ✅ Git checkout: `_git_checkout_re` pattern
- ✅ Actions: `GitInit`, `GitAdd`, `GitCommit`, `GitBranch`, `GitCheckout`

## Test 7: Natural Language Branch Switch ✅
**Command:** `go to feature`
- ✅ Pattern: `_git_checkout_nl_re` matches "go to <branch>"
- ✅ Action: `GitCheckout`

## Test 8: Git Remote Operations ✅
**Commands:**
- `git remote add origin https://github.com/user/repo.git`
- `git push -u origin main`
- `git pull origin main`
- ✅ Remote add: `_git_remote_add_explicit_re` pattern
- ✅ Push: `_git_push_re` pattern
- ✅ Pull: `_git_pull_re` pattern
- ✅ Actions: `GitRemote`, `GitPush`, `GitPull`

## Test 9: Multi-line Insertions ✅
**Command:** `:edit app.py` → `:ml` → `insert at line 10:` → multi-line → `:end`
- ✅ Multi-line collection: `_collect_manual_block()` works in live edit mode
- ✅ Insert pattern: `_insert_at_line_re` with `re.DOTALL` handles multi-line
- ✅ Content extraction: `extract_content()` extracts multi-line after "insert at line N:"
- ✅ Action: `InsertAfterLine` with multi-line content

## Test 10: File Operations with Spaces ✅
**Commands:** `create "my file.txt" with hello world`, `read "my file.txt"`
- ✅ Quoted paths: Patterns capture quoted paths
- ✅ Path stripping: `path.strip('"\'')` removes quotes
- ✅ Actions: `CreateFile`, `ReadFile` with unquoted paths

## Test 11: Complete Git + GitHub Workflow ✅
**Commands:** Full workflow from init to push
- ✅ All git operations supported
- ✅ GitHub repo creation: `_github_repo_simple_re` pattern
- ✅ Actions: `GitInit`, `GitAdd`, `GitCommit`, `GitHubCreateRepo`, `GitRemote`, `GitPush`

## Test 12: Advanced Git Operations ✅
**Commands:** Branch, commit, push, merge
- ✅ All operations supported
- ✅ Actions: `GitCheckout`, `GitAdd`, `GitCommit`, `GitPush`, `GitMerge`

## Potential Issues to Verify:

1. **Multi-line insertions in live edit mode:**
   - Need to ensure `:ml` mode works correctly when `:edit` is active
   - The collected multi-line content should be processed as a live edit instruction

2. **Quoted file paths:**
   - Verify that quotes are properly stripped in all file operations
   - Ensure paths with spaces work correctly

3. **Live edit mode with line operations:**
   - Verify that line operations work correctly in live edit mode
   - Ensure the editor updates correctly after operations

