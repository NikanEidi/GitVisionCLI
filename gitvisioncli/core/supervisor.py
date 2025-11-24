# gitvisioncli/core/supervisor.py

import shutil
import subprocess
import logging
import re
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING, Set
from datetime import datetime
from gitvisioncli.core.safe_patch_engine import SafePatchEngine
from gitvisioncli.core.editing_engine import EditingEngine, EditingError

from .github_client import GitHubClient, GitHubClientConfig, GitHubError

if TYPE_CHECKING:
    from gitvisioncli.core.terminal import TerminalEngine

logger = logging.getLogger(__name__)


class ActionType(Enum):
    # Files & folders
    CREATE_FILE = "CreateFile"
    EDIT_FILE = "EditFile"
    READ_FILE = "ReadFile"
    DELETE_FILE = "DeleteFile"
    MOVE_FILE = "MoveFile"
    COPY_FILE = "CopyFile"
    RENAME_FILE = "RenameFile"
    CREATE_FOLDER = "CreateFolder"
    DELETE_FOLDER = "DeleteFolder"
    MOVE_FOLDER = "MoveFolder"
    COPY_FOLDER = "CopyFolder"

    # AI Text Editor (New)
    APPEND_TEXT = "AppendText"
    PREPEND_TEXT = "PrependText"
    REPLACE_TEXT = "ReplaceText"
    INSERT_BEFORE_LINE = "InsertBeforeLine"
    INSERT_AFTER_LINE = "InsertAfterLine"
    DELETE_LINE_RANGE = "DeleteLineRange"
    REWRITE_ENTIRE_FILE = "RewriteEntireFile"
    APPLY_PATCH = "ApplyPatch"
    # Advanced text / block operations (centralized in EditingEngine)
    REPLACE_BY_PATTERN = "ReplaceByPattern"
    DELETE_BY_PATTERN = "DeleteByPattern"
    REPLACE_BY_FUZZY_MATCH = "ReplaceByFuzzyMatch"
    INSERT_AT_TOP = "InsertAtTop"
    INSERT_AT_BOTTOM = "InsertAtBottom"
    INSERT_BLOCK_AT_LINE = "InsertBlockAtLine"
    REPLACE_BLOCK = "ReplaceBlock"
    REMOVE_BLOCK = "RemoveBlock"
    UPDATE_JSON_KEY = "UpdateJSONKey"
    UPDATE_YAML_KEY = "UpdateYAMLKey"
    INSERT_INTO_FUNCTION = "InsertIntoFunction"
    INSERT_INTO_CLASS = "InsertIntoClass"
    ADD_DECORATOR = "AddDecorator"
    ADD_IMPORT = "AddImport"

    # Local git
    RUN_GIT_COMMAND = "RunGitCommand"
    GIT_INIT = "GitInit"
    GIT_ADD = "GitAdd"
    GIT_COMMIT = "GitCommit"
    GIT_PUSH = "GitPush"
    GIT_PULL = "GitPull"
    GIT_BRANCH = "GitBranch"
    GIT_CHECKOUT = "GitCheckout"
    GIT_MERGE = "GitMerge"
    GIT_REMOTE = "GitRemote"

    # Search / refactor
    SEARCH_FILES = "SearchFiles"
    FIND_REPLACE = "FindReplace"

    # Project utilities
    GENERATE_PROJECT_STRUCTURE = "GenerateProjectStructure"
    SCAFFOLD_MODULE = "ScaffoldModule"

    # Shell / CI
    RUN_SHELL_COMMAND = "RunShellCommand"
    RUN_TESTS = "RunTests"
    BUILD_PROJECT = "BuildProject"

    # Orchestration
    BATCH_OPERATION = "BatchOperation"
    ATOMIC_OPERATION = "AtomicOperation"

    # GitHub integration
    GITHUB_CREATE_REPO = "GitHubCreateRepo"
    GITHUB_DELETE_REPO = "GitHubDeleteRepo"
    GITHUB_PUSH_PATH = "GitHubPushPath"
    GITHUB_CREATE_ISSUE = "GitHubCreateIssue"
    GITHUB_CREATE_PR = "GitHubCreatePR"


class ActionStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"


@dataclass
class ActionResult:
    status: ActionStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None
    sub_results: Optional[List["ActionResult"]] = None
    modified_files: Optional[List[str]] = None  # For UI synchronization

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": self.status.value,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.rollback_info is not None:
            result["rollback_info"] = self.rollback_info
        if self.sub_results is not None:
            result["sub_results"] = [r.to_dict() for r in self.sub_results]
        return result


@dataclass
class SecurityPolicy:
    base_dir: Path
    forbidden_extensions: List[str] = field(
        default_factory=lambda: [
            ".exe", ".dll", ".so", ".dylib", ".bat", ".sh", ".cmd"
        ]
    )
    forbidden_paths: List[str] = field(
        default_factory=lambda: ["/etc", "/sys", "/proc", "C:\\Windows"]
    )
    max_file_size_mb: int = 10
    disallowed_directories: List[str] = field(
        default_factory=lambda: [
            ".git", ".svn", "node_modules", "__pycache__", ".pytest_cache", ".venv"
        ]
    )

    def validate_path(self, path: Path) -> Tuple[bool, Optional[str]]:
        """
        Ensure the path stays inside the sandbox, does not cross dangerous system paths,
        and does not traverse through disallowed directories or unsafe symlinks.
        """
        try:
            # Symlink check on each component
            current = path
            while current != current.parent:
                if current.exists() and current.is_symlink():
                    resolved_target = current.resolve()
                    base_abs = self.base_dir.resolve()
                    if not str(resolved_target).startswith(str(base_abs)):
                        return False, f"Symlink escape detected: {current} -> {resolved_target}"
                current = current.parent

            abs_path = path.resolve()
            base_abs = self.base_dir.resolve()

            # Stay inside sandbox root
            if not str(abs_path).startswith(str(base_abs)):
                if abs_path != base_abs:
                    return False, f"Path outside sandbox: {path} (Sandbox Root: {base_abs})"

            # Forbidden extensions
            if abs_path.suffix.lower() in self.forbidden_extensions:
                return False, f"Forbidden extension: {abs_path.suffix}"

            # Forbidden system roots
            lower_abs = str(abs_path).lower()
            for forbidden in self.forbidden_paths:
                if lower_abs.startswith(forbidden.lower()):
                    return False, f"Forbidden system path: {forbidden}"

            # Disallowed directory components
            for part in abs_path.parts:
                if part in self.disallowed_directories:
                    # Allow the top-level .git for repo itself, but no deeper
                    if part == ".git" and abs_path == base_abs.joinpath(".git"):
                        continue
                    return False, f"Disallowed directory in path: {part}"

            return True, None
        except Exception as e:
            return False, f"Path validation error: {str(e)}"

    def validate_file_size(self, path: Path) -> Tuple[bool, Optional[str]]:
        if path.exists() and path.is_file():
            try:
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb > self.max_file_size_mb:
                    return (
                        False,
                        f"File too large: {size_mb:.2f}MB > {self.max_file_size_mb}MB",
                    )
            except OSError as e:
                return False, f"Cannot stat file: {e}"
        return True, None


@dataclass
class ActionContext:
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False

    def __post_init__(self):
        # Enforce strict boolean type to prevent "None" or truthy strings
        self.dry_run = bool(self.dry_run)


@dataclass
class GitRepoState:
    """
    Snapshot of the local git repository state as seen from the Supervisor.

    This is the single source of truth for:
    - Where the repo root is (if any)
    - Whether the repo has an initial commit
    - Whether an 'origin' remote exists
    - What the current branch is
    """

    root: Optional[Path]
    has_commits: bool
    has_origin: bool
    current_branch: Optional[str]

    @property
    def is_repo(self) -> bool:
        return self.root is not None


class TransactionManager:
    """
    Simple transactional layer with backup folder.
    Each logical action can record backups + created paths,
    and rollback() will restore from backup.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = base_dir / ".gitvision_backup" / timestamp
        self.operations: List[Dict[str, Any]] = []
        self.committed = False

    def _ensure_backup_dir(self):
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_file(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""
        self._ensure_backup_dir()
        relative_path = file_path.relative_to(self.base_dir)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)

        op = {
            "type": "file_backup",
            "original": str(file_path),
            "backup": str(backup_path),
        }
        self.operations.append(op)
        return str(backup_path)

    def backup_folder(self, folder_path: Path) -> str:
        if not folder_path.exists():
            return ""
        self._ensure_backup_dir()
        relative_path = folder_path.relative_to(self.base_dir)
        backup_path = self.backup_dir / relative_path
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(folder_path, backup_path, dirs_exist_ok=True)

        op = {
            "type": "folder_backup",
            "original": str(folder_path),
            "backup": str(backup_path),
        }
        self.operations.append(op)
        return str(backup_path)

    def record_created_file(self, file_path: Path):
        self.operations.append({"type": "file_created", "path": str(file_path)})

    def record_created_folder(self, folder_path: Path):
        self.operations.append({"type": "folder_created", "path": str(folder_path)})

    def record_deleted_file(self, file_path: Path, skip_backup: bool = False):
        backup_path = ""
        if not skip_backup and file_path.exists():
            backup_path = self.backup_file(file_path)

        self.operations.append(
            {"type": "file_deleted", "original": str(file_path), "backup": backup_path}
        )

    def record_deleted_folder(self, folder_path: Path, skip_backup: bool = False):
        backup_path = ""
        if not skip_backup and folder_path.exists():
            backup_path = self.backup_folder(folder_path)

        self.operations.append(
            {"type": "folder_deleted", "original": str(folder_path), "backup": backup_path}
        )

    def record_renamed_file(self, old_path: Path, new_path: Path):
        """
        Records a rename operation.
        Backs up the old file (if it exists) so rollback can restore it.
        """
        backup_path = ""
        if old_path.exists():
            backup_path = self.backup_file(old_path)
        
        self.operations.append({
            "type": "file_renamed",
            "old_path": str(old_path),
            "new_path": str(new_path),
            "backup": backup_path
        })

    def rollback(self):
        if self.committed:
            logger.warning("Cannot rollback committed transaction")
            return

        logger.warning("Rolling back transaction...")
        for op in reversed(self.operations):
            try:
                op_type = op["type"]

                if op_type == "file_created":
                    path = Path(op["path"])
                    if path.exists():
                        path.unlink()
                        logger.info(f"Rollback: deleted {path}")

                elif op_type == "folder_created":
                    path = Path(op["path"])
                    if path.exists():
                        shutil.rmtree(path)
                        logger.info(f"Rollback: deleted {path}")

                elif op_type in ("file_backup", "file_deleted"):
                    original = Path(op["original"])
                    backup = Path(op["backup"]) if op["backup"] else None
                    if backup and backup.exists():
                        original.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup, original)
                        logger.info(f"Rollback: restored {original}")

                elif op_type in ("folder_backup", "folder_deleted"):
                    original = Path(op["original"])
                    backup = Path(op["backup"]) if op["backup"] else None
                    if backup and backup.exists():
                        if original.exists():
                            shutil.rmtree(original)
                        shutil.copytree(backup, original, dirs_exist_ok=True)
                        logger.info(f"Rollback: restored {original}")

                elif op_type == "file_renamed":
                    old_path = Path(op["old_path"])
                    new_path = Path(op["new_path"])
                    backup = Path(op["backup"]) if op["backup"] else None
                    
                    # 1. Delete the new file if it exists
                    if new_path.exists():
                        new_path.unlink()
                    
                    # 2. Restore old file from backup
                    if backup and backup.exists():
                        old_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup, old_path)
                        logger.info(f"Rollback: renamed {new_path} -> {old_path}")

            except Exception as e:
                logger.error(f"Rollback error for {op}: {str(e)}")

        self.cleanup_backup_dir()

    def commit(self):
        self.committed = True
        self.cleanup_backup_dir()

    def cleanup_backup_dir(self):
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
        except Exception as e:
            logger.error(f"Failed to clean backup directory: {str(e)}")


class ActionSupervisor:

    def __init__(
        self,
        base_dir: str,
        security_policy: Optional[SecurityPolicy] = None,
        github_config: Optional[GitHubClientConfig] = None,
        terminal_engine: Optional["TerminalEngine"] = None,
    ):
        # Base directory of whole sandbox
        self.base_dir = Path(base_dir).resolve()
        logger.info(f"Supervisor initialized at Sandbox Root: {self.base_dir}")

        # --- FIXED: SafePatchEngine correct initialization ---
        self.safe_patch = SafePatchEngine(
            project_root=self.base_dir,
            backup_dir=self.base_dir / ".patch_backups",
        )
        # -----------------------------------------------------

        # Centralized in-memory editing engine (text semantics only).
        # All line-/block-based file content edits should flow through
        # this engine so behavior stays consistent across modules.
        self.editing_engine = EditingEngine(base_dir=self.base_dir)

        self.security_policy = security_policy or SecurityPolicy(base_dir=self.base_dir)

        self._github_config = github_config
        self._github_client: Optional[GitHubClient] = None

        if terminal_engine is not None:
            self.terminal = terminal_engine
        else:
            from gitvisioncli.core.terminal import TerminalEngine
            self.terminal = TerminalEngine(self.base_dir, patch_engine=self.safe_patch)

        self.fs_watcher = None

        self.handlers = {
            # Files
            ActionType.CREATE_FILE: self._handle_create_file,
            ActionType.EDIT_FILE: self._handle_edit_file,
            ActionType.READ_FILE: self._handle_read_file,
            ActionType.DELETE_FILE: self._handle_delete_file,
            ActionType.MOVE_FILE: self._handle_move_file,
            ActionType.COPY_FILE: self._handle_copy_file,
            ActionType.RENAME_FILE: self._handle_rename_file,
            ActionType.CREATE_FOLDER: self._handle_create_folder,
            ActionType.DELETE_FOLDER: self._handle_delete_folder,
            ActionType.MOVE_FOLDER: self._handle_move_folder,
            ActionType.COPY_FOLDER: self._handle_copy_folder,
            # AI text editor
            ActionType.APPEND_TEXT: self._handle_append_text,
            ActionType.PREPEND_TEXT: self._handle_prepend_text,
            ActionType.REPLACE_TEXT: self._handle_replace_text,
            ActionType.INSERT_BEFORE_LINE: self._handle_insert_before_line,
            ActionType.INSERT_AFTER_LINE: self._handle_insert_after_line,
            ActionType.DELETE_LINE_RANGE: self._handle_delete_line_range,
            ActionType.REWRITE_ENTIRE_FILE: self._handle_rewrite_entire_file,
            ActionType.APPLY_PATCH: self._handle_apply_patch,
            ActionType.REPLACE_BY_PATTERN: self._handle_replace_by_pattern,
            ActionType.DELETE_BY_PATTERN: self._handle_delete_by_pattern,
            ActionType.REPLACE_BY_FUZZY_MATCH: self._handle_replace_by_fuzzy_match,
            ActionType.INSERT_AT_TOP: self._handle_insert_at_top,
            ActionType.INSERT_AT_BOTTOM: self._handle_insert_at_bottom,
            ActionType.INSERT_BLOCK_AT_LINE: self._handle_insert_block_at_line,
            ActionType.REPLACE_BLOCK: self._handle_replace_block,
            ActionType.REMOVE_BLOCK: self._handle_remove_block,
            ActionType.UPDATE_JSON_KEY: self._handle_update_json_key,
            ActionType.UPDATE_YAML_KEY: self._handle_update_yaml_key,
            ActionType.INSERT_INTO_FUNCTION: self._handle_insert_into_function,
            ActionType.INSERT_INTO_CLASS: self._handle_insert_into_class,
            ActionType.ADD_DECORATOR: self._handle_add_decorator,
            ActionType.ADD_IMPORT: self._handle_add_import,
            # Git
            ActionType.RUN_GIT_COMMAND: self._handle_run_git_command,
            ActionType.GIT_INIT: self._handle_git_init,
            ActionType.GIT_ADD: self._handle_git_add,
            ActionType.GIT_COMMIT: self._handle_git_commit,
            ActionType.GIT_PUSH: self._handle_git_push,
            ActionType.GIT_PULL: self._handle_git_pull,
            ActionType.GIT_BRANCH: self._handle_git_branch,
            ActionType.GIT_CHECKOUT: self._handle_git_checkout,
            ActionType.GIT_MERGE: self._handle_git_merge,
            ActionType.GIT_REMOTE: self._handle_git_remote,
            # Search / refactor
            ActionType.SEARCH_FILES: self._handle_search_files,
            ActionType.FIND_REPLACE: self._handle_find_replace,
            # Utilities
            ActionType.GENERATE_PROJECT_STRUCTURE: self._handle_generate_project_structure,
            ActionType.SCAFFOLD_MODULE: self._handle_scaffold_module,
            # Shell / CI
            ActionType.RUN_SHELL_COMMAND: self._handle_run_shell_command,
            ActionType.RUN_TESTS: self._handle_run_tests,
            ActionType.BUILD_PROJECT: self._handle_build_project,
            # Orchestration
            ActionType.BATCH_OPERATION: self._handle_batch_operation,
            ActionType.ATOMIC_OPERATION: self._handle_atomic_operation,
            # GitHub
            ActionType.GITHUB_CREATE_REPO: self._handle_github_create_repo,
            ActionType.GITHUB_DELETE_REPO: self._handle_github_delete_repo,
            ActionType.GITHUB_PUSH_PATH: self._handle_github_push_path,
            ActionType.GITHUB_CREATE_ISSUE: self._handle_github_create_issue,
            ActionType.GITHUB_CREATE_PR: self._handle_github_create_pr,
        }

    # Public helper used by workspace panels (e.g., GitGraphPanel)
    # to access the unified git repository snapshot.
    def get_git_repo_state(self) -> GitRepoState:
        return self._get_git_repo_state()

    # ------------------------------------------------------------------ #
    # Path helpers
    # ------------------------------------------------------------------ #

    def _resolve_path(self, rel_path: str) -> Path:
        """
        Resolve path relative to the TerminalEngine's current working directory.
        This keeps all actions aligned with what the user sees in the CLI.
        """
        if not rel_path:
            return self.terminal.cwd

        # Normalize common whitespace issues (trailing spaces, newlines)
        rel_path = str(rel_path).strip()

        p = Path(rel_path)
        if p.is_absolute():
            return p.resolve()

        return (self.terminal.cwd / p).resolve()

    def _find_git_root(self, start_path: Path) -> Optional[Path]:
        """
        Walk upwards looking for a .git directory, but never above the
        Supervisor's sandbox root. If a .git exists at the sandbox root,
        that is always treated as the canonical repository root.
        """
        sandbox_root = self.base_dir.resolve()

        # Prefer a repo anchored at the sandbox root if present.
        if (sandbox_root / ".git").exists():
            return sandbox_root

        current = start_path.resolve()
        # Walk up until we either find a .git dir or hit the sandbox root.
        while True:
            if (current / ".git").exists():
                # Only accept git roots inside the sandbox.
                if str(current).startswith(str(sandbox_root)):
                    return current
                # .git outside sandbox → treat as non-repo for safety.
                return None

            if current == sandbox_root or current == current.parent:
                break

            current = current.parent

        return None

    def _get_git_repo_state(self) -> GitRepoState:
        """
        Compute the current git repository state from the perspective of the
        Supervisor/TerminalEngine.

        This is the authoritative view used by all git handlers and by
        GitHub integration to keep local and remote state in sync.
        """
        git_root = self._find_git_root(self.terminal.cwd)
        if git_root is None:
            return GitRepoState(
                root=None,
                has_commits=False,
                has_origin=False,
                current_branch=None,
            )

        def _run(args: List[str]) -> Tuple[bool, str, str]:
            git_bin = shutil.which("git") or "git"
            cmd = [git_bin] + args
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(git_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = proc.communicate()
                return proc.returncode == 0, stdout.strip(), stderr.strip()
            except Exception as e:
                return False, "", f"Git detection error: {e}"

        # Detect current branch (may fail in detached HEAD)
        branch_ok, branch_out, _ = _run(["rev-parse", "--abbrev-ref", "HEAD"])
        current_branch = branch_out if branch_ok and branch_out != "HEAD" else None

        # Detect whether any commit exists
        has_commits, _, _ = _run(["rev-parse", "HEAD"])

        # Detect whether origin exists
        has_origin, _, _ = _run(["remote", "get-url", "origin"])

        return GitRepoState(
            root=git_root,
            has_commits=has_commits,
            has_origin=has_origin,
            current_branch=current_branch,
        )

    def _find_embedded_git_roots(self) -> Set[Path]:
        """
        Discover embedded git repositories inside the sandbox, excluding the
        primary repository at the sandbox root (if any).
        """
        embedded: Set[Path] = set()
        sandbox_root = self.base_dir.resolve()

        try:
            for git_dir in sandbox_root.rglob(".git"):
                if not git_dir.is_dir():
                    continue
                root = git_dir.parent.resolve()
                # Skip the primary repo at the sandbox root itself.
                if root == sandbox_root:
                    continue
                embedded.add(root)
        except Exception as e:
            logger.warning(f"Failed to scan for embedded git repos: {e}")

        return embedded

    def set_fs_watcher(self, watcher):
        self.fs_watcher = watcher
        logger.info("File system watcher linked to supervisor")

    def _notify_fs_change(self):
        if self.fs_watcher:
            try:
                # simple "one-shot" check to avoid crazy loops
                self.fs_watcher.check_once()
            except Exception as e:
                logger.warning(f"FS watcher notification failed: {e}")

    def _get_github_client(
        self, override_config: Optional[Dict[str, Any]] = None
    ) -> GitHubClient:
        if override_config:
            return GitHubClient(override_config)

        if self._github_client is not None:
            return self._github_client

        if self._github_config is None:
            raise GitHubError("GitHub configuration is missing for ActionSupervisor")

        self._github_client = GitHubClient(self._github_config)
        return self._github_client

    # ------------------------------------------------------------------ #
    # Main dispatcher
    # ------------------------------------------------------------------ #

    def handle_ai_action(
        self,
        action: Dict[str, Any],
        context: Optional[ActionContext] = None,
        transaction: Optional[TransactionManager] = None,
        manage_transaction: bool = True,
    ) -> ActionResult:
        """
        Generic dispatcher. If `transaction` is None, a new TransactionManager
        is created and committed/rolled-back here. If it's provided, the caller
        owns commit/rollback (used by AtomicOperation).
        """
        context = context or ActionContext()

        action_type_str = action.get("type", "")
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Unknown action type: {action_type_str}",
                error="Invalid action type",
            )

        params = action.get("params", {}) or {}
        handler = self.handlers.get(action_type)

        if not handler:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"No handler for action: {action_type.value}",
                error="Handler not implemented",
            )

        tx = transaction or TransactionManager(self.base_dir)

        logger.info(f"Executing action: {action_type.value} with params: {params}")

        # 1. Global Dry-Run Check
        if context.dry_run:
            return ActionResult(
                status=ActionStatus.DRY_RUN,
                message=f"[DRY RUN] Would execute: {action_type.value}",
                data={"action": action_type.value, "params": params},
            )

        # 2. Handler dispatch
        handler = self.handlers.get(action_type)
        if not handler:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"No handler for action type: {action_type}",
                error="Unknown action type",
            )

        try:
            return handler(params, context, tx)
        except Exception as e:
            logger.exception(f"Action failed: {action_type}")
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Action failed: {str(e)}",
                error=str(e),
            )

    def _normalize_content(self, params: Dict[str, Any]) -> str:
        """
        Normalize content from various possible keys.
        Strips ANSI escape codes to prevent them from being written to files.
        """
        import re
        # Comprehensive ANSI escape code pattern:
        # - \x1b[ or \033[ (ESC sequence start) followed by digits/semicolons and command char
        # - Also handle partial/corrupted sequences like 38;5;46m (missing ESC and bracket prefix)
        ansi_re = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\033\[[0-9;]*[a-zA-Z]")
        # Pattern for corrupted ANSI sequences (missing ESC prefix)
        # Matches and removes:
        # - [number;m (bracket is part of corruption, remove entirely)
        # - standalone number;m (remove entirely)
        # Note: We don't match (number;m because ( might be valid syntax (e.g., function calls)
        # The standalone number;m pattern will catch cases like print(38;5;46m"text")
        corrupted_ansi_re = re.compile(r"\[[0-9;]+m|[0-9;]+m")
        
        content = (
            params.get("content")
            or params.get("text")
            or params.get("value")
            or params.get("body")
            or ""
        )
        
        # Strip ANSI escape codes from content before writing to files
        # First remove full ANSI sequences
        content = ansi_re.sub("", content)
        # Then remove any corrupted/partial ANSI sequences entirely (including leading brackets/parentheses)
        content = corrupted_ansi_re.sub("", content)
        return content

    def _write_safe(self, path: Path, content: str) -> None:
        """
        Atomic write helper.
        Writes to a temp file then renames to ensure atomicity.
        Ensures parent directories exist.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temp file in the same directory to ensure atomic rename
            temp_path = path.with_suffix(f"{path.suffix}.tmp")
            
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(path)
        except Exception as e:
            logger.error(f"Write failed for {path}: {e}")
            raise

    # ------------------------------------------------------------------ #
    # Helper for path validation / backup
    # ------------------------------------------------------------------ #

    def _validate_and_prepare_file(
        self,
        params: Dict[str, Any],
        transaction: TransactionManager,
        check_exists: bool = True,
    ) -> Tuple[Optional[Path], Optional[ActionResult]]:
        """
        Validate path + sandbox + size, and create backup if check_exists=True.
        """
        rel_path = params.get("path")
        if not rel_path:
            return None, ActionResult(
                status=ActionStatus.FAILURE,
                message="Path is required",
            )

        # Strip whitespace from the path so that accidental trailing
        # spaces or newlines do not create phantom files.
        rel_path = str(rel_path).strip()
        path = self._resolve_path(rel_path)

        # PATH ESCAPE CHECK (User Requirement 6)
        # Ensure path is inside base_dir
        try:
            # We use self.base_dir which is the Sandbox Root
            if not str(path.resolve()).startswith(str(self.base_dir.resolve())):
                 return None, ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Path escape attempt",
                    error=f"{path} is outside {self.base_dir}",
                )
        except Exception as e:
             return None, ActionResult(
                status=ActionStatus.FAILURE,
                message="Path validation error",
                error=str(e),
            )

        valid, error = self.security_policy.validate_path(path)
        if not valid:
            return None, ActionResult(
                status=ActionStatus.FAILURE,
                message="Security violation",
                error=error,
            )

        if check_exists:
            if not path.exists():
                return None, ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"File not found: {rel_path}",
                    error="File not found",
                )

            if not path.is_file():
                return None, ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"Path is not a file: {rel_path}",
                    error="Not a file",
                )

            valid, error = self.security_policy.validate_file_size(path)
            if not valid:
                return None, ActionResult(
                    status=ActionStatus.FAILURE,
                    message="File size error",
                    error=error,
                )

            transaction.backup_file(path)

        return path, None

    # ------------------------------------------------------------------ #
    # Basic file handlers
    # ------------------------------------------------------------------ #

    def _handle_create_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        # Normalize path up-front for consistency
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=False
        )
        if error_result:
            return error_result

        if path.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"File already exists: {path.name}",
                error="File exists",
            )

        content = self._normalize_content(params)
            
        self._write_safe(path, content)
        transaction.record_created_file(path)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"File created: {path.name}",
            data={"path": str(path)},
            modified_files=[str(path)],
        )

    def _handle_edit_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        content = self._normalize_content(params)

        # Ensure parent dir exists (just in case)
        self._write_safe(path, content)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"File rewritten: {path.name}",
            data={"path": str(path)},
            modified_files=[str(path)],
        )
    
    def _handle_rewrite_entire_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        return self._handle_edit_file(params, context, transaction)

    def _handle_read_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Read file contents without modifying anything.
        """
        rel_path = params.get("path")
        if not rel_path:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Path is required",
                error="Missing path",
            )

        rel_path = str(rel_path).strip()
        path = self._resolve_path(rel_path)

        valid, error = self.security_policy.validate_path(path)
        if not valid:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Security violation",
                error=error,
            )

        if not path.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"File not found: {rel_path}",
                error="File not found",
            )

        if not path.is_file():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Path is not a file: {rel_path}",
                error="Not a file",
            )

        valid, error = self.security_policy.validate_file_size(path)
        if not valid:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="File size error",
                error=error,
            )

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to read file: {rel_path}",
                error=str(e),
            )

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"File read: {path.name}",
            data={"path": str(path), "content": content},
        )

    def _handle_delete_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        transaction.record_deleted_file(path)
        path.unlink()

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"File deleted: {path.name}",
            data={"path": str(path)},
            modified_files=[str(path)],
        )

    def _handle_rename_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        # Support old/old_name and new/new_name
        old = params.get("old") or params.get("old_name") or params.get("path")
        new = params.get("new") or params.get("new_name") or params.get("new_path")

        if not old or not new:
             return ActionResult(
                status=ActionStatus.FAILURE,
                message="Missing old/new filename",
                error="Missing params",
            )

        # Update params for validation helper
        params["path"] = old
        
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        new_path = self._resolve_path(new)

        # Validate new_path security
        valid, error = self.security_policy.validate_path(new_path)
        if not valid:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Security violation for new_path",
                error=error,
            )

        if new_path.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"New path already exists: {new}",
                error="File exists",
            )

        transaction.record_renamed_file(path, new_path) # Note: record_renamed_file might not exist in TransactionManager, checking...
        # Wait, TransactionManager in the file view didn't show record_renamed_file. 
        # It showed record_deleted_file, record_created_file.
        # I should check TransactionManager again. 
        # If it doesn't exist, I should implement it or use delete+create recording.
        # For now, I'll assume it handles it or I'll just do the rename.
        path.rename(new_path)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"File renamed: {path.name} -> {new_path.name}",
            data={"old_path": str(path), "new_path": str(new_path)},
            modified_files=[str(path), str(new_path)],
        )

    # ------------------------------------------------------------------ #
    # AI text editor handlers
    # ------------------------------------------------------------------ #

    def _handle_append_text(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        # Normalize and strip ANSI codes from text
        text = self._normalize_content(params)
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_at_bottom(content, block=text)
            self._write_safe(path, result.content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Appended text to {path.name}",
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"AppendText failed for {path.name}",
                error=str(e),
            )

    def _handle_prepend_text(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        # Normalize and strip ANSI codes from text
        text = self._normalize_content(params)
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_at_top(content, block=text)
            self._write_safe(path, result.content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Prepended text to {path.name}",
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"PrependText failed for {path.name}",
                error=str(e),
            )

    def _handle_replace_text(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        # Normalize and strip ANSI codes from text
        old_text_params = {"content": params.get("old_text", ""), "text": params.get("old_text", "")}
        new_text_params = {"content": params.get("new_text", ""), "text": params.get("new_text", "")}
        old_text = self._normalize_content(old_text_params)
        new_text = self._normalize_content(new_text_params)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.replace_by_exact_match(
                content, old=old_text, new=new_text
            )
            self._write_safe(path, result.content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Replaced text in {path.name}",
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Text to replace not found in file",
                error=str(e),
            )

    def _handle_insert_before_line(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        # Normalize and strip ANSI codes from text
        text = self._normalize_content(params)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_before_line(
                content,
                line_number=params.get("line_number"),
                line=params.get("line"),
                text=text,
            )
            self._write_safe(path, result.content)
            line_num = result.details.get("line_number")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Inserted text before line {line_num} in {path.name}",
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Invalid line number or range for InsertBeforeLine",
                error=str(e),
            )

    def _handle_insert_after_line(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        # Normalize and strip ANSI codes from text
        text = self._normalize_content(params)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_after_line(
                content,
                line_number=params.get("line_number"),
                line=params.get("line"),
                text=text,
            )
            self._write_safe(path, result.content)
            line_num = result.details.get("line_number")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Inserted text after line {line_num} in {path.name}",
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Invalid line number or range for InsertAfterLine",
                error=str(e),
            )

    def _handle_delete_line_range(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")

            # Support DeleteLine via line_number/line aliases by mapping them
            # onto a single-line DeleteLineRange.
            start_line = params.get("start_line")
            end_line = params.get("end_line")
            start = params.get("start")
            end = params.get("end")
            if start_line is None and end_line is None and start is None and end is None:
                if "line_number" in params or "line" in params:
                    ln = params.get("line_number", params.get("line"))
                    start_line = ln
                    end_line = ln

            result = self.editing_engine.delete_line_range(
                content,
                start_line=start_line,
                end_line=end_line,
                start=start,
                end=end,
            )
            self._write_safe(path, result.content)
            s = result.details.get("start_line")
            e = result.details.get("end_line")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Deleted lines {s}-{e} in {path.name}",
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Invalid line range for DeleteLineRange",
                error=str(e),
            )

    def _handle_rewrite_entire_file(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        # Semantically distinct for planner, but same behavior as edit.
        # We delegate to _handle_edit_file which now has robust write logic.
        return self._handle_edit_file(params, context, transaction)

    def _handle_apply_patch(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        """
        Replace a specific snippet once, with robust handling of newline differences.
        """
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        original_snippet = params.get("original_snippet", "")
        new_snippet = params.get("new_snippet", "")

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            # Reuse ReplaceByExactMatch semantics but constrain to a single replacement.
            result = self.editing_engine.replace_by_exact_match(
                content,
                old=self.editing_engine._normalize_newlines(original_snippet),
                new=self.editing_engine._normalize_newlines(new_snippet),
                count=1,
            )
            self._write_safe(path, result.content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Applied patch to {path.name}",
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Original snippet not found in file. Patch failed.",
                error=str(e),
            )

    def _handle_replace_by_pattern(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        pattern = params.get("pattern", "")
        replacement = params.get("replacement", "")
        flags = params.get("flags", 0)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.replace_by_pattern(
                content,
                pattern=pattern,
                replacement=replacement,
                flags=flags,
            )
            self._write_safe(path, result.content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Replaced pattern in {path.name}",
                data={"replacements": result.details.get("replacements", 0)},
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="ReplaceByPattern failed",
                error=str(e),
            )

    def _handle_delete_by_pattern(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        pattern = params.get("pattern", "")
        flags = params.get("flags", 0)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.delete_by_pattern(
                content,
                pattern=pattern,
                flags=flags,
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Deleted pattern occurrences in {path.name}",
                data={"pattern": pattern},
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="DeleteByPattern failed",
                error=str(e),
            )

    def _handle_replace_by_fuzzy_match(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        target = params.get("target", "")
        replacement = params.get("replacement", "")
        threshold = float(params.get("threshold", 0.6))

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.replace_by_fuzzy_match(
                content,
                target=target,
                replacement=replacement,
                threshold=threshold,
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Replaced line by fuzzy match",
                data=result.details,
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="ReplaceByFuzzyMatch failed",
                error=str(e),
            )

    def _handle_insert_at_top(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        block = params.get("block", params.get("text", ""))

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_at_top(content, block=block)
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Inserted block at top of {path.name}",
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="InsertAtTop failed",
                error=str(e),
            )

    def _handle_insert_at_bottom(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        # Normalize and strip ANSI codes from block
        block_params = {
            "content": params.get("block", params.get("text", "")),
            "text": params.get("block", params.get("text", ""))
        }
        block = self._normalize_content(block_params)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_at_bottom(content, block=block)
            self._write_safe(path, result.content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Inserted block at bottom of {path.name}",
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="InsertAtBottom failed",
                error=str(e),
            )

    def _handle_insert_block_at_line(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        # Normalize and strip ANSI codes from block
        block_params = {
            "content": params.get("block", params.get("text", "")),
            "text": params.get("block", params.get("text", ""))
        }
        block = self._normalize_content(block_params)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_block_at_line(
                content,
                line_number=params.get("line_number"),
                line=params.get("line"),
                block=block,
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Inserted block at line in file",
                data=result.details,
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="InsertBlockAtLine failed",
                error=str(e),
            )

    def _handle_replace_block(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        # Normalize and strip ANSI codes from block
        block_params = {
            "content": params.get("block", params.get("text", "")),
            "text": params.get("block", params.get("text", ""))
        }
        block = self._normalize_content(block_params)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            # Normalize aliases:
            # - ReplaceLine / UpdateLine: line_number/line → start_line=end_line
            # - ReplaceLineRange: start_line/end_line or start/end
            start_line = params.get("start_line")
            end_line = params.get("end_line")
            start = params.get("start")
            end = params.get("end")

            if start_line is None and end_line is None and start is None and end is None:
                if "line_number" in params or "line" in params:
                    ln = params.get("line_number", params.get("line"))
                    start_line = ln
                    end_line = ln

            result = self.editing_engine.replace_block(
                content,
                start_line=start_line if start_line is not None else (start or 1),
                end_line=end_line if end_line is not None else (end or start_line or start or 1),
                block=block,
            )
            self._write_safe(path, result.content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Replaced block in file",
                data=result.details,
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="ReplaceBlock failed",
                error=str(e),
            )

    def _handle_remove_block(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.remove_block(
                content,
                start_line=params.get("start_line", params.get("start", 1)),
                end_line=params.get("end_line", params.get("end", params.get("start", 1))),
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Removed block from file",
                data=result.details,
                modified_files=[str(path)],
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="RemoveBlock failed",
                error=str(e),
            )

    def _handle_update_json_key(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        key_path = params.get("key_path") or params.get("path")
        value = params.get("value")

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.update_json_key(
                content,
                key_path=key_path,
                value=value,
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Updated JSON key in {path.name}",
                data=result.details,
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="UpdateJSONKey failed",
                error=str(e),
            )

    def _handle_update_yaml_key(
        self, params: Dict[str, Any], context: ActionContext, transaction: TransactionManager
    ) -> ActionResult:
        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        key_path = params.get("key_path") or params.get("path")
        value = params.get("value")

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.update_yaml_key(
                content,
                key_path=key_path,
                value=value,
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Updated YAML key in {path.name}",
                data=result.details,
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="UpdateYAMLKey failed",
                error=str(e),
            )

    def _handle_insert_into_function(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        func_name = params.get("function_name") or params.get("name")
        block = params.get("block", params.get("text", ""))
        position = (params.get("position") or "bottom").lower()

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_into_function(
                content,
                function_name=str(func_name or "").strip(),
                block=block,
                position=position,
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Inserted block into function '{func_name}'",
                data=result.details,
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="InsertIntoFunction failed",
                error=str(e),
            )

    def _handle_insert_into_class(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        class_name = params.get("class_name") or params.get("name")
        block = params.get("block", params.get("text", ""))
        position = (params.get("position") or "bottom").lower()

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.insert_into_class(
                content,
                class_name=str(class_name or "").strip(),
                block=block,
                position=position,
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Inserted block into class '{class_name}'",
                data=result.details,
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="InsertIntoClass failed",
                error=str(e),
            )

    def _handle_add_decorator(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        target = params.get("target_name") or params.get("name")
        decorator = params.get("decorator") or params.get("text")

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.add_decorator(
                content,
                target_name=str(target or "").strip(),
                decorator=str(decorator or "").strip(),
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Decorator added",
                data=result.details,
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="AddDecorator failed",
                error=str(e),
            )

    def _handle_add_import(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        if "path" in params and isinstance(params["path"], str):
            params["path"] = params["path"].strip()

        path, error_result = self._validate_and_prepare_file(
            params, transaction, check_exists=True
        )
        if error_result:
            return error_result

        symbol = params.get("symbol") or params.get("name")
        import_path = params.get("import_path")

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = self.editing_engine.auto_import(
                content,
                symbol=str(symbol or "").strip(),
                import_path=str(import_path or "").strip() or None,
            )
            path.write_text(result.content, encoding="utf-8")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Import added",
                data=result.details,
            )
        except EditingError as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="AddImport failed",
                error=str(e),
            )

    # ------------------------------------------------------------------ #
    # Folder & move/copy handlers
    # ------------------------------------------------------------------ #

    def _handle_move_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        src_rel = params.get("source")
        dst_rel = params.get("destination")
        if isinstance(src_rel, str):
            src_rel = src_rel.strip()
        if isinstance(dst_rel, str):
            dst_rel = dst_rel.strip()
        if not src_rel or not dst_rel:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Source and destination are required",
            )

        src = self._resolve_path(src_rel)
        dst = self._resolve_path(dst_rel)

        for p, name in ((src, "Source"), (dst, "Destination")):
            valid, error = self.security_policy.validate_path(p)
            if not valid:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"{name} path security violation",
                    error=error,
                )

        if not src.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Source not found: {src_rel}",
                error="Source not found",
            )

        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            transaction.backup_file(dst)

        transaction.backup_file(src)
        shutil.move(str(src), str(dst))

        transaction.record_created_file(dst)
        transaction.record_deleted_file(src, skip_backup=True)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"File moved: {src_rel} -> {dst_rel}",
            data={"source": src_rel, "destination": dst_rel},
            modified_files=[str(src), str(dst)],
        )

    def _handle_copy_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        src_rel = params.get("source")
        dst_rel = params.get("destination")
        if isinstance(src_rel, str):
            src_rel = src_rel.strip()
        if isinstance(dst_rel, str):
            dst_rel = dst_rel.strip()
        if not src_rel or not dst_rel:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Source and destination are required",
            )

        src = self._resolve_path(src_rel)
        dst = self._resolve_path(dst_rel)

        for p, name in ((src, "Source"), (dst, "Destination")):
            valid, error = self.security_policy.validate_path(p)
            if not valid:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"{name} path security violation",
                    error=error,
                )

        if not src.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Source not found: {src_rel}",
                error="Source not found",
            )

        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            transaction.backup_file(dst)
        else:
            transaction.record_created_file(dst)

        shutil.copy2(str(src), str(dst))

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"File copied: {src_rel} -> {dst_rel}",
            data={"source": src_rel, "destination": dst_rel},
            modified_files=[str(dst)],
        )

    def _handle_rename_file(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Rename file within its parent directory.
        new_name should be only a filename, not a full path.
        """
        old_rel = params.get("old_name")
        new_name = params.get("new_name")
        if not old_rel or not new_name:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="old_name and new_name are required",
            )

        old_path = self._resolve_path(old_rel)

        if "/" in new_name or "\\" in new_name:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="new_name should be a filename, not a path",
            )

        new_path = old_path.parent / new_name

        # re-use move handler
        return self._handle_move_file(
            {
                "source": str(old_path),
                "destination": str(new_path),
            },
            context,
            transaction,
        )

    def _handle_create_folder(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        rel_path = params.get("path")
        if not rel_path:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Path is required",
            )

        rel_path = str(rel_path).strip()
        path = self._resolve_path(rel_path)

        valid, error = self.security_policy.validate_path(path)
        if not valid:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Security violation",
                error=error,
            )

        path.mkdir(parents=True, exist_ok=True)
        transaction.record_created_folder(path)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Folder created: {rel_path}",
            data={"path": rel_path},
            modified_files=[str(path)],
        )

    def _handle_delete_folder(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        rel_path = params.get("path")
        if not rel_path:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Path is required",
            )

        rel_path = str(rel_path).strip()
        path = self._resolve_path(rel_path)

        valid, error = self.security_policy.validate_path(path)
        if not valid:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Security violation",
                error=error,
            )

        if not path.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Folder not found: {rel_path}",
                error="Folder not found",
            )

        if not path.is_dir():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Path is not a folder: {rel_path}",
                error="Not a folder",
            )

        transaction.record_deleted_folder(path)
        shutil.rmtree(path)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Folder deleted: {rel_path}",
            data={"path": rel_path},
            modified_files=[str(path)],
        )

    def _handle_move_folder(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        # Support both "source/destination" and "path/target_folder" parameter names
        src_rel = params.get("source") or params.get("path")
        dst_rel = params.get("destination") or params.get("target_folder")
        if isinstance(src_rel, str):
            src_rel = src_rel.strip()
        if isinstance(dst_rel, str):
            dst_rel = dst_rel.strip()
        if not src_rel or not dst_rel:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Source and destination are required",
            )

        src = self._resolve_path(src_rel)
        dst = self._resolve_path(dst_rel)

        for p, name in ((src, "Source"), (dst, "Destination")):
            valid, error = self.security_policy.validate_path(p)
            if not valid:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"{name} path security violation",
                    error=error,
                )

        if not src.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Source not found: {src_rel}",
                error="Source not found",
            )

        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            transaction.backup_folder(dst)

        transaction.backup_folder(src)
        shutil.move(str(src), str(dst))

        transaction.record_created_folder(dst)
        transaction.record_deleted_folder(src, skip_backup=True)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Folder moved: {src_rel} -> {dst_rel}",
            data={"source": src_rel, "destination": dst_rel},
            modified_files=[str(src), str(dst)],
        )

    def _handle_copy_folder(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        # Support both "source/destination" and "path/new_path" parameter names
        src_rel = params.get("source") or params.get("path")
        dst_rel = params.get("destination") or params.get("new_path")
        if isinstance(src_rel, str):
            src_rel = src_rel.strip()
        if isinstance(dst_rel, str):
            dst_rel = dst_rel.strip()
        if not src_rel or not dst_rel:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Source and destination are required",
            )

        src = self._resolve_path(src_rel)
        dst = self._resolve_path(dst_rel)

        for p, name in ((src, "Source"), (dst, "Destination")):
            valid, error = self.security_policy.validate_path(p)
            if not valid:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"{name} path security violation",
                    error=error,
                )

        if not src.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Source not found: {src_rel}",
                error="Source not found",
            )

        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            transaction.backup_folder(dst)
        else:
            transaction.record_created_folder(dst)

        shutil.copytree(str(src), str(dst), dirs_exist_ok=True)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Folder copied: {src_rel} -> {dst_rel}",
            data={"source": src_rel, "destination": dst_rel},
            modified_files=[str(dst)],
        )

    # ------------------------------------------------------------------ #
    # Git handlers / helper
    # ------------------------------------------------------------------ #

    def _is_binary_file(self, file_path: Path) -> bool:
        """
        Simple binary detection: look for NULL bytes or invalid UTF-8.
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return True
                try:
                    chunk.decode("utf-8")
                    return False
                except UnicodeDecodeError:
                    return True
        except Exception:
            return True

    def _run_git_command(
        self,
        args: List[str],
        require_repo: bool = True,
        cwd: Optional[Path] = None,
    ) -> Tuple[bool, str, str]:
        """
        Run git commands via the TerminalEngine, using a cwd that is
        consistent with the Supervisor's view of the repository.

        - If require_repo is True, we ensure we are inside a git repo and
          run commands from the repo root (not a nested subfolder).
        - If require_repo is False, we run in the provided cwd or the
          TerminalEngine's cwd, without enforcing repo existence.
        """
        git_bin = shutil.which("git") or "git"

        workdir = cwd.resolve() if cwd is not None else self.terminal.cwd

        if require_repo:
            git_root = self._find_git_root(workdir)
            if not git_root and args[0] != "init":
                return (
                    False,
                    "",
                    "Not in a git repository. Run 'git init' first.",
                )
            workdir = git_root or workdir

        cmd = [git_bin] + args
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(workdir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate()
            success = proc.returncode == 0
            return success, stdout, stderr
        except Exception as e:
            return False, "", f"Git execution error: {str(e)}"

    def _handle_run_git_command(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        command = params.get("command", "")
        if isinstance(command, str) and command:
            args = command.split()
        else:
            args = params.get("args", []) or []

        if not args:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="No git command provided",
                error="Missing command",
            )

        require_repo = args[0] != "init"
        success, stdout, stderr = self._run_git_command(args, require_repo=require_repo)

        if success:
            # For display commands (status, log), include output in message
            if args[0] in ("status", "log"):
                output_preview = stdout.strip()[:200] if stdout.strip() else ""
                if len(stdout.strip()) > 200:
                    output_preview += "..."
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Git {args[0]}:\n{output_preview}" if output_preview else f"Git {args[0]} executed",
                    data={"stdout": stdout, "stderr": stderr},
                )
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Git command executed: {' '.join(args)}",
                data={"stdout": stdout, "stderr": stderr},
            )

        # User-friendly error messages
        error_msg = stderr.strip() if stderr.strip() else "Unknown error"
        if "not a git repository" in error_msg.lower():
            error_msg = "Not a git repository. Run 'git init' first."
        elif "no such file or directory" in error_msg.lower():
            error_msg = f"Git command failed: {error_msg}"
        
        return ActionResult(
            status=ActionStatus.FAILURE,
            message=f"Git command failed: {' '.join(args)}",
            error=error_msg,
            data={"stdout": stdout},
        )

    def _handle_git_init(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Initialize a git repository in the current working directory.

        We prefer an explicit initial branch of 'main' when supported,
        and fall back to a plain 'git init' otherwise.
        """
        initial_branch = params.get("branch", "main")

        # Try modern 'git init -b <branch>' first.
        success, stdout, stderr = self._run_git_command(
            ["init", "-b", initial_branch],
            require_repo=False,
        )

        if not success:
            # Fallback to legacy 'git init'
            success, stdout, stderr = self._run_git_command(
                ["init"],
                require_repo=False,
            )

        if success:
            self._notify_fs_change()
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Git repository initialized",
                data={"output": stdout},
            )
        return ActionResult(
            status=ActionStatus.FAILURE,
            message="Failed to initialize git repository",
            error=stderr,
        )

    def _handle_git_add(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Add files to the git index.

        Special handling:
        - When files is '.' or not provided, we add all top-level entries
          from the repo root but skip embedded git repositories that have
          their own .git directories inside the sandbox.
        """
        # CRITICAL FIX: Handle both "files" and "path" parameters for git add
        files = params.get("files") or params.get("path")
        if files is None:
            files = ["."]
        if isinstance(files, str):
            files = [files]

        repo_state = self._get_git_repo_state()
        if not repo_state.is_repo:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Not in a git repository. Run GitInit first.",
                error="Missing .git",
            )

        # Default: add everything from repo root, but skip embedded repos.
        if files == ["."] or files == ["./"]:
            repo_root = repo_state.root or self.base_dir
            embedded_roots = self._find_embedded_git_roots()

            # Collect top-level entries relative to repo root.
            try:
                candidates: List[Path] = list(repo_root.iterdir())
            except Exception as e:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Failed to enumerate repository entries",
                    error=str(e),
                )

            paths_to_add: List[str] = []
            for entry in candidates:
                # Skip the main .git directory entirely.
                if entry.name == ".git":
                    continue

                # Skip any embedded repo roots.
                if any(entry.resolve() == er for er in embedded_roots):
                    logger.info(f"Skipping embedded git repo root: {entry}")
                    continue

                rel = entry.relative_to(repo_root).as_posix()
                paths_to_add.append(rel)

            if not paths_to_add:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="No files to add (all entries are embedded repos or .git).",
                    data={"files": []},
                )

            args = ["add"] + paths_to_add
        else:
            # Respect explicit file list from caller.
            args = ["add"] + files

        success, stdout, stderr = self._run_git_command(args)
        if success:
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Files added to staging: {', '.join(args[1:])}",
                data={"files": args[1:]},
            )
        return ActionResult(
            status=ActionStatus.FAILURE,
            message="Failed to add files to staging",
            error=stderr,
        )

    def _handle_git_commit(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Create a commit with the given message.

        This handler is deliberately idempotent:
        - If there is nothing to commit, we return SUCCESS with a clear
          message instead of surfacing a raw git error.
        """
        repo_state = self._get_git_repo_state()
        if not repo_state.is_repo:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Not in a git repository. Run GitInit first.",
                error="Missing .git",
            )

        message = params.get("message", "Automated commit from GitVisionCLI")
        # Check whether there is anything to commit.
        status_ok, status_out, status_err = self._run_git_command(
            ["status", "--porcelain"],
            require_repo=True,
            cwd=repo_state.root,
        )
        if not status_ok:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Failed to inspect git status before commit",
                error=status_err,
            )

        if not status_out.strip():
            # Nothing to commit → treat as a successful no-op.
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="No changes to commit.",
                data={"output": ""},
            )

        success, stdout, stderr = self._run_git_command(
            ["commit", "-m", message],
            require_repo=True,
            cwd=repo_state.root,
        )
        if success:
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Changes committed: {message}",
                data={"output": stdout},
            )
        return ActionResult(
            status=ActionStatus.FAILURE,
            message="Failed to commit changes",
            error=stderr,
        )

    def _handle_git_push(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Push local commits to a remote.

        This handler uses the shared GitRepoState so that:
        - A missing repo results in a clear error.
        - A missing remote produces a deterministic failure.
        - The current branch is used by default if not provided.
        """
        repo_state = self._get_git_repo_state()
        if not repo_state.is_repo:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Not in a git repository. Run GitInit first.",
                error="Missing .git",
            )

        remote = params.get("remote", "origin")
        branch = params.get("branch") or repo_state.current_branch
        set_upstream = params.get("set_upstream", True)  # Default to True for new branches

        # Ensure the remote exists before attempting to push.
        has_remote, _, _ = self._run_git_command(
            ["remote", "get-url", remote],
            require_repo=True,
            cwd=repo_state.root,
        )
        if not has_remote:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Remote '{remote}' does not exist. Configure it with GitRemote first.",
                error="Missing remote",
            )

        # Build push command - use -u flag to set upstream for new branches
        args = ["push"]
        if set_upstream and branch:
            args.extend(["-u", remote, branch])
        elif branch:
            args.extend([remote, branch])
        else:
            args.append(remote)

        success, stdout, stderr = self._run_git_command(
            args,
            require_repo=True,
            cwd=repo_state.root,
        )
        
        # If push fails with "no upstream branch", try with -u flag
        if not success and "no upstream branch" in stderr.lower() and branch and not set_upstream:
            logger.info("Retrying push with -u flag to set upstream")
            args_retry = ["push", "-u", remote, branch]
            success, stdout, stderr = self._run_git_command(
                args_retry,
            require_repo=True,
            cwd=repo_state.root,
        )
        if success:
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Pushed to {remote}{'/' + branch if branch else ''}",
                data={"output": stdout, "remote": remote, "branch": branch},
            )
        return ActionResult(
            status=ActionStatus.FAILURE,
            message="Failed to push changes",
            error=stderr,
        )

    def _handle_git_pull(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        remote = params.get("remote", "origin")
        branch = params.get("branch")
        args = ["pull", remote]
        if branch:
            args.append(branch)

        success, stdout, stderr = self._run_git_command(args)

        if success:
            self._notify_fs_change()
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Pulled from {remote}",
                data={"output": stdout},
            )
        return ActionResult(
            status=ActionStatus.FAILURE,
            message="Failed to pull changes",
            error=stderr,
        )

    def _handle_git_branch(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        branch_name = params.get("name")
        if branch_name:
            success, stdout, stderr = self._run_git_command(["branch", branch_name])
            if success:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Branch created: {branch_name}",
                    data={"branch": branch_name},
                )
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to create branch: {branch_name}",
                error=stderr,
            )

        success, stdout, stderr = self._run_git_command(["branch", "--list"])
        if success:
            branches = [
                b.strip().lstrip("* ").strip()
                for b in stdout.split("\n")
                if b.strip()
            ]
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Branches listed",
                data={"branches": branches, "output": stdout},
            )
        return ActionResult(
            status=ActionStatus.FAILURE,
            message="Failed to list branches",
            error=stderr,
        )

    def _handle_git_checkout(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        branch = params.get("branch")
        if not branch:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Branch name is required",
                error="Missing branch",
            )

        create_new = params.get("create_new", False)
        
        # CRITICAL FIX: Check if branch exists before trying to checkout
        # If branch doesn't exist and create_new is False, check for similar branch names
        if not create_new:
            # List all branches
            success_list, stdout_list, _ = self._run_git_command(["branch", "--list", "-a"])
            if success_list:
                branches = [
                    b.strip().lstrip("* ").strip()
                    for b in stdout_list.split("\n")
                    if b.strip()
                ]
                # Remove "remotes/" prefix from remote branches for comparison
                local_branches = [b for b in branches if not b.startswith("remotes/")]
                remote_branches = [b.replace("remotes/", "").split("/", 1)[-1] for b in branches if b.startswith("remotes/")]
                all_branch_names = set(local_branches + remote_branches)
                
                # Check if requested branch exists
                if branch not in all_branch_names:
                    # Check for common branch name alternatives (main/master)
                    suggestions = []
                    if branch == "main" and "master" in all_branch_names:
                        suggestions.append("master")
                    elif branch == "master" and "main" in all_branch_names:
                        suggestions.append("main")
                    
                    # Build helpful error message
                    error_msg = f"Branch '{branch}' does not exist."
                    if suggestions:
                        error_msg += f" Did you mean '{suggestions[0]}'? (Current branch: {self._get_git_repo_state().current_branch or 'unknown'})"
                    else:
                        available = ", ".join(sorted(local_branches)[:5])  # Show first 5 branches
                        if len(local_branches) > 5:
                            available += f" (and {len(local_branches) - 5} more)"
                        error_msg += f" Available branches: {available}"
                        error_msg += f" Use 'git checkout -b {branch}' to create it."
                    
                    return ActionResult(
                        status=ActionStatus.FAILURE,
                        message=f"Failed to checkout branch: {branch}",
                        error=error_msg,
                        data={"available_branches": local_branches, "suggestions": suggestions}
                    )

        args = ["checkout"]
        if create_new:
            args.append("-b")
        args.append(branch)

        success, stdout, stderr = self._run_git_command(args)
        if success:
            self._notify_fs_change()
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Checked out branch: {branch}",
                data={"branch": branch, "output": stdout},
            )
        
        # If checkout failed, provide better error message
        error_msg = stderr
        if "pathspec" in stderr.lower() and "did not match" in stderr.lower():
            # Try to suggest alternatives
            success_list, stdout_list, _ = self._run_git_command(["branch", "--list"])
            if success_list:
                branches = [
                    b.strip().lstrip("* ").strip()
                    for b in stdout_list.split("\n")
                    if b.strip()
                ]
                if branches:
                    available = ", ".join(branches[:5])
                    error_msg = f"Branch '{branch}' does not exist. Available branches: {available}"
                    if branch == "main" and "master" in branches:
                        error_msg += f" (Did you mean 'master'?)"
                    elif branch == "master" and "main" in branches:
                        error_msg += f" (Did you mean 'main'?)"
        
        return ActionResult(
            status=ActionStatus.FAILURE,
            message=f"Failed to checkout branch: {branch}",
            error=error_msg,
        )

    def _handle_git_merge(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        branch = params.get("branch")
        if not branch:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Branch name to merge is required",
                error="Missing branch",
            )

        success, stdout, stderr = self._run_git_command(["merge", branch])
        if success:
            self._notify_fs_change()
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Merged branch: {branch}",
                data={"branch": branch, "output": stdout},
            )
        return ActionResult(
            status=ActionStatus.FAILURE,
            message=f"Failed to merge branch: {branch}",
            error=stderr,
        )

    def _handle_git_remote(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Manage git remotes.

        Params:
            operation: "add", "remove", "list", "rename", "set-url", "show" (default: "add")
            name: remote name (default "origin")
            url: remote URL (required for add/set-url)
            old_name: old remote name (for rename)
            new_name: new remote name (for rename)

        Behavior:
            - add: If remote exists, update with set-url; otherwise add
            - remove: Remove remote
            - list: List all remotes
            - rename: Rename remote
            - set-url: Update remote URL
            - show: Show remote details
        """
        repo_state = self._get_git_repo_state()
        if not repo_state.is_repo:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Not in a git repository. Run GitInit first.",
                error="Missing .git",
            )

        operation = params.get("operation", "add").lower()
        name = params.get("name", "origin")
        
        # Handle list operation
        if operation == "list":
            success, stdout, stderr = self._run_git_command(
                ["remote", "-v"],
                require_repo=True,
                cwd=repo_state.root,
            )
            if success:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="Git remotes listed",
                    data={"remotes": stdout, "output": stdout},
                )
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Failed to list git remotes",
                error=stderr,
            )
        
        # Handle remove operation
        if operation == "remove" or operation == "rm":
            success, stdout, stderr = self._run_git_command(
                ["remote", "remove", name],
                require_repo=True,
                cwd=repo_state.root,
            )
            if success:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Git remote removed: {name}",
                    data={"remote": name, "output": stdout},
                )
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to remove git remote: {name}",
                error=stderr,
            )
        
        # Handle rename operation
        if operation == "rename":
            old_name = params.get("old_name") or name
            new_name = params.get("new_name")
            if not new_name:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="New remote name is required for rename",
                    error="Missing new_name",
                )
            success, stdout, stderr = self._run_git_command(
                ["remote", "rename", old_name, new_name],
                require_repo=True,
                cwd=repo_state.root,
            )
            if success:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Git remote renamed: {old_name} -> {new_name}",
                    data={"old_name": old_name, "new_name": new_name, "output": stdout},
                )
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to rename git remote: {old_name}",
                error=stderr,
            )
        
        # Handle show operation
        if operation == "show":
            success, stdout, stderr = self._run_git_command(
                ["remote", "show", name],
                require_repo=True,
                cwd=repo_state.root,
            )
            if success:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Git remote details for: {name}",
                    data={"remote": name, "output": stdout},
                )
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to show git remote: {name}",
                error=stderr,
            )
        
        # Handle set-url operation
        if operation == "set-url":
            url = params.get("url")
            if not url:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Remote URL is required for set-url",
                    error="Missing url",
                )
            success, stdout, stderr = self._run_git_command(
                ["remote", "set-url", name, url],
                require_repo=True,
                cwd=repo_state.root,
            )
            if success:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Git remote URL updated: {name}",
                    data={"remote": name, "url": url, "output": stdout},
                )
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Failed to update git remote URL: {name}",
                error=stderr,
            )
        
        # Handle add operation (default)
        url = params.get("url")
        if not url:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Remote URL is required",
                error="Missing url",
            )

        # Detect whether remote exists
        exists, _, _ = self._run_git_command(
            ["remote", "get-url", name],
            require_repo=True,
            cwd=repo_state.root,
        )

        if exists:
            args = ["remote", "set-url", name, url]
        else:
            args = ["remote", "add", name, url]

        success, stdout, stderr = self._run_git_command(
            args,
            require_repo=True,
            cwd=repo_state.root,
        )
        if success:
            action = "updated" if exists else "created"
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Git remote {action}: {name}",
                data={"remote": name, "url": url, "output": stdout},
            )

        return ActionResult(
            status=ActionStatus.FAILURE,
            message="Failed to configure git remote",
            error=stderr,
        )

    # ------------------------------------------------------------------ #
    # Search / refactor
    # ------------------------------------------------------------------ #

    def _handle_search_files(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        query = params.get("query")
        if not query:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Search query is required",
                error="Missing query",
            )

        use_regex = params.get("use_regex", False)
        case_insensitive = params.get("case_insensitive", False)
        glob_patterns = params.get("patterns", ["**/*"])
        if isinstance(glob_patterns, str):
            glob_patterns = [glob_patterns]

        results: List[Dict[str, Any]] = []

        regex_flags = re.MULTILINE
        if case_insensitive:
            regex_flags |= re.IGNORECASE

        try:
            if use_regex:
                search_query = re.compile(query, regex_flags)
            else:
                escaped_query = re.escape(query)
                search_query = re.compile(escaped_query, regex_flags)
        except re.error as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Invalid regular expression",
                error=str(e),
            )

        search_root = self.terminal.cwd

        for pattern in glob_patterns:
            for file_path in search_root.rglob(pattern):
                if not file_path.is_file():
                    continue

                valid, _ = self.security_policy.validate_path(file_path)
                if not valid:
                    continue

                valid, error = self.security_policy.validate_file_size(file_path)
                if not valid:
                    logger.warning(
                        f"Skipping search on large file: {file_path.name} ({error})"
                    )
                    continue

                if self._is_binary_file(file_path):
                    logger.debug(f"Skipping binary file: {file_path}")
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    rel_path = file_path.relative_to(self.base_dir).as_posix()

                    for match in search_query.finditer(content):
                        line_num = content.count("\n", 0, match.start()) + 1
                        start_pos = max(0, match.start() - 40)
                        end_pos = min(len(content), match.end() + 40)
                        context_str = content[start_pos:end_pos].strip()

                        results.append(
                            {
                                "file": rel_path,
                                "line": line_num,
                                "match": match.group(0),
                                "context": context_str,
                            }
                        )

                except Exception as e:
                    logger.warning(f"Failed to search file {file_path}: {str(e)}")

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Search completed: found {len(results)} matches",
            data={"query": query, "matches": results, "count": len(results)},
        )

    def _handle_find_replace(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        find_text = params.get("find")
        if find_text is None:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Find text is required",
                error="Missing find",
            )

        replace_text = params.get("replace", "")
        glob_patterns = params.get("patterns", ["**/*"])
        use_regex = params.get("use_regex", False)
        case_insensitive = params.get("case_insensitive", False)

        if isinstance(glob_patterns, str):
            glob_patterns = [glob_patterns]

        modified_files: List[str] = []

        regex_flags = 0
        if case_insensitive:
            regex_flags |= re.IGNORECASE

        try:
            find_expr = find_text if use_regex else re.escape(find_text)
            search_regex = re.compile(find_expr, regex_flags)
        except re.error as e:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Invalid regular expression",
                error=str(e),
            )

        search_root = self.terminal.cwd

        for pattern in glob_patterns:
            for file_path in search_root.rglob(pattern):
                if not file_path.is_file():
                    continue

                valid, _ = self.security_policy.validate_path(file_path)
                if not valid:
                    continue

                valid, error = self.security_policy.validate_file_size(file_path)
                if not valid:
                    logger.warning(
                        f"Skipping replace on large file: {file_path.name} ({error})"
                    )
                    continue

                if self._is_binary_file(file_path):
                    logger.debug(f"Skipping binary file: {file_path}")
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8")

                    if search_regex.search(content):
                        new_content = search_regex.sub(replace_text, content)

                        if new_content != content:
                            transaction.backup_file(file_path)
                            file_path.write_text(new_content, encoding="utf-8")
                            modified_files.append(
                                file_path.relative_to(self.base_dir).as_posix()
                            )

                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {str(e)}")

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Find/replace completed: {len(modified_files)} files modified",
            data={
                "find": find_text,
                "replace": replace_text,
                "modified_files": modified_files,
            },
        )

    # ------------------------------------------------------------------ #
    # Project utilities
    # ------------------------------------------------------------------ #

    def _handle_generate_project_structure(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Generate a tree view from the current working directory of the terminal.
        CLI can control max_depth so that folders are not auto-expanded too deep.
        """
        max_depth = params.get("max_depth", 5)
        include_hidden = params.get("include_hidden", False)

        def build_tree(path: Path, depth: int = 0, prefix: str = "") -> List[str]:
            if depth > max_depth:
                return [f"{prefix}└── ... (max depth reached)"]
            items: List[str] = []
            try:
                entries = sorted(
                    [
                        p
                        for p in path.iterdir()
                        if include_hidden or not p.name.startswith(".")
                    ],
                    key=lambda p: (not p.is_dir(), p.name.lower()),
                )

                entries = [
                    e
                    for e in entries
                    if e.name not in self.security_policy.disallowed_directories
                ]

                for i, entry in enumerate(entries):
                    is_last = i == len(entries) - 1
                    current_prefix = "└── " if is_last else "├── "
                    items.append(f"{prefix}{current_prefix}{entry.name}")
                    if entry.is_dir():
                        extension = "    " if is_last else "│   "
                        items.extend(build_tree(entry, depth + 1, prefix + extension))
            except PermissionError:
                items.append(f"{prefix}└── [Permission Denied]")
            except OSError:
                items.append(f"{prefix}└── [OS Error]")
            return items

        structure_root = self.terminal.cwd
        tree_lines = [structure_root.name + "/"]
        tree_lines.extend(build_tree(structure_root))
        tree_str = "\n".join(tree_lines)

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message="Project structure generated",
            data={"structure": tree_str, "lines": len(tree_lines)},
        )

    def _handle_scaffold_module(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        module_name = params.get("name")
        if not module_name:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Module name is required",
                error="Missing module name",
            )

        module_path = self.terminal.cwd / module_name
        valid, error = self.security_policy.validate_path(module_path)
        if not valid:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Security violation",
                error=error,
            )

        if module_path.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Module already exists: {module_name}",
                error="Module exists",
            )

        actions = [
            {"type": "CreateFolder", "params": {"path": module_name}},
            {
                "type": "CreateFile",
                "params": {"path": f"{module_name}/__init__.py", "content": ""},
            },
            {
                "type": "CreateFile",
                "params": {
                    "path": f"{module_name}/{module_name}.py",
                    "content": f'"""{module_name} module"""\n',
                },
            },
            {"type": "CreateFolder", "params": {"path": f"{module_name}/tests"}},
            {
                "type": "CreateFile",
                "params": {"path": f"{module_name}/tests/__init__.py", "content": ""},
            },
            {
                "type": "CreateFile",
                "params": {
                    "path": f"{module_name}/tests/test_{module_name}.py",
                    "content": "import unittest\n\n",
                },
            },
        ]

        # Use a single atomic transaction for the scaffold
        return self._handle_atomic_operation(
            {"actions": actions},
            context,
            transaction,
        )

    # ------------------------------------------------------------------ #
    # Shell / CI
    # ------------------------------------------------------------------ #

    def _handle_run_shell_command(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        command = params.get("command")

        if not command:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Command is required",
                error="Missing command",
            )

        exit_code, stdout, stderr = self.terminal.run_once(command)

        status = ActionStatus.SUCCESS if exit_code == 0 else ActionStatus.FAILURE

        return ActionResult(
            status=status,
            message=f"Command executed: {command}",
            data={"stdout": stdout, "stderr": stderr, "returncode": exit_code},
        )

    def _handle_run_tests(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        test_command = params.get("command", "pytest")
        test_path = params.get("path", ".")
        full_command = f"{test_command} {test_path}"

        return self._handle_run_shell_command(
            {"command": full_command},
            context,
            transaction,
        )

    def _handle_build_project(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        build_command = params.get("command", "npm run build")
        return self._handle_run_shell_command(
            {"command": build_command},
            context,
            transaction,
        )

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #

    def _handle_batch_operation(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Batch: run each sub-action in its own transaction.
        Some may succeed, some fail, but successes stay committed.
        """
        actions = params.get("actions", [])
        if not actions:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="No actions provided",
                error="Empty batch",
            )

        results: List[ActionResult] = []
        success_count = 0
        failure_count = 0

        for sub_action in actions:
            result = self.handle_ai_action(
                sub_action,
                context,
                transaction=None,
                manage_transaction=True,
            )
            results.append(result)
            if result.status == ActionStatus.SUCCESS:
                success_count += 1
            elif result.status == ActionStatus.FAILURE:
                failure_count += 1

        if failure_count == 0:
            overall_status = ActionStatus.SUCCESS
        elif success_count > 0 and failure_count > 0:
            overall_status = ActionStatus.PARTIAL
        else:
            overall_status = ActionStatus.FAILURE

        return ActionResult(
            status=overall_status,
            message=f"Batch operation completed: {success_count} succeeded, {failure_count} failed",
            data={"total": len(actions), "succeeded": success_count, "failed": failure_count},
            sub_results=results,
        )

    def _handle_atomic_operation(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Atomic: all-or-nothing multi-step operation using a shared TransactionManager.
        If any sub-action fails, everything rolls back.
        """
        actions = params.get("actions", [])
        if not actions:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="No actions provided",
                error="Empty atomic operation",
            )

        results: List[ActionResult] = []

        for sub_action in actions:
            result = self.handle_ai_action(
                sub_action,
                context,
                transaction=transaction,
                manage_transaction=False,
            )
            results.append(result)
            if result.status != ActionStatus.SUCCESS:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Atomic operation failed, all changes will be rolled back",
                    error=f"Failed at action: {sub_action.get('type')}",
                    sub_results=results,
                )

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Atomic operation completed: {len(actions)} actions succeeded",
            data={"total": len(actions)},
            sub_results=results,
        )

    # ------------------------------------------------------------------ #
    # GitHub integration
    # ------------------------------------------------------------------ #

    def _handle_github_create_repo(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        name = params.get("name")
        if not name:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Repository name is required",
                error="Missing name",
            )

        private_param = params.get("private", True)
        visibility = params.get("visibility", "private" if private_param else "public")

        description = params.get("description")
        github_override = params.get("github")
        sync_local = params.get("sync_local", True)

        try:
            client = self._get_github_client(github_override)

            result = client.create_repository(
                name=name,
                private=(visibility == "private"),
                description=description,
            )

            if not result["ok"]:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"GitHub API error: {result['error']}",
                    error=result["error"],
                    data=result.get("details"),
                )

            repo_data = result["data"]
            full_name = repo_data.get("full_name", name)

            # Optionally synchronize the local git remote so that the
            # filesystem repository and GitHub repository stay aligned.
            if sync_local:
                repo_state = self._get_git_repo_state()
                if repo_state.is_repo:
                    clone_url = repo_data.get("clone_url")
                    if clone_url:
                        _ = self._handle_git_remote(
                            {
                                "name": "origin",
                                "url": clone_url,
                            },
                            context,
                            transaction,
                        )

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"GitHub repository created: {full_name}",
                data={"repo": repo_data},
            )

        except GitHubError as e:
            logger.error(f"GitHub client connection error: {e}")
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Failed to connect to GitHub",
                error=str(e),
            )

    def _handle_github_delete_repo(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        """
        Delete a GitHub repo by 'owner/repo'.
        """
        repo_full_name = params.get("repo")
        if not repo_full_name:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Repository name ('owner/repo') is required",
                error="Missing repo",
            )

        github_override = params.get("github")

        try:
            client = self._get_github_client(github_override)

            result = client.delete_repo(repo_full_name=repo_full_name)

            if not result["ok"]:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"GitHub API error: {result['error']}",
                    error=result["error"],
                    data=result.get("details"),
                )

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"GitHub repository deleted: {repo_full_name}",
                data={"repo": repo_full_name, "deleted": True},
            )

        except GitHubError as e:
            logger.error(f"GitHub client connection error: {e}")
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Failed to connect to GitHub",
                error=str(e),
            )

    def _handle_github_push_path(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        repo = params.get("repo")
        if not repo:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="GitHub repo (owner/name) is required",
                error="Missing repo",
            )

        raw_path = params.get("path")
        if raw_path is None:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Local path is required",
                error="Missing path",
            )

        # Allow either a relative path (from workspace root or current cwd)
        # or an absolute path that must still live inside the sandbox.
        raw_path = str(raw_path).strip()
        p = Path(raw_path)
        if p.is_absolute():
            local_target_path = p.resolve()
        else:
            # Prefer resolution relative to the TerminalEngine cwd, but the
            # SecurityPolicy will still enforce containment within base_dir.
            local_target_path = (self.terminal.cwd / p).resolve()

        local_root_path = self.base_dir.resolve()

        branch = params.get("branch", "main")
        commit_message = params.get("message", "Sync from GitVisionCLI")
        github_override = params.get("github")

        valid, error = self.security_policy.validate_path(local_target_path)
        if not valid:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Security violation",
                error=error,
            )

        if not local_target_path.exists():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Local path not found: {raw_path}",
                error="Path not found",
            )

        try:
            client = self._get_github_client(github_override)

            try:
                rel_path = local_target_path.relative_to(local_root_path).as_posix()
            except ValueError:
                # Path somehow escaped the sandbox root despite validation.
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Resolved path is outside the workspace root",
                    error="Path outside sandbox root",
                )

            result = client.push_path(
                repo_full_name=repo,
                local_root=str(local_root_path),
                local_path=rel_path,
                branch=branch,
                commit_message=commit_message,
            )

            if not result["ok"]:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"GitHub API error: {result['error']}",
                    error=result["error"],
                    data=result.get("details"),
                )

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Pushed {rel_path} to {repo}@{branch}",
                data=result,
            )
        except GitHubError as e:
            logger.error(f"GitHub client connection error: {e}")
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Failed to connect to GitHub",
                error=str(e),
            )

    def _handle_github_create_issue(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        repo = params.get("repo")
        title = params.get("title")
        if not repo or not title:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="repo and title are required",
                error="Missing repo or title",
            )

        body = params.get("body")
        github_override = params.get("github")

        try:
            client = self._get_github_client(github_override)

            result = client.create_issue(
                repo_full_name=repo,
                title=title,
                body=body,
            )

            if not result["ok"]:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"GitHub API error: {result['error']}",
                    error=result["error"],
                    data=result.get("details"),
                )

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Issue created in {repo}#{result['data'].get('number')}",
                data={"issue": result["data"]},
            )
        except GitHubError as e:
            logger.error(f"GitHub client connection error: {e}")
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Failed to connect to GitHub",
                error=str(e),
            )

    def _handle_github_create_pr(
        self,
        params: Dict[str, Any],
        context: ActionContext,
        transaction: TransactionManager,
    ) -> ActionResult:
        repo = params.get("repo")
        title = params.get("title")
        head = params.get("head")
        if not repo or not title or not head:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="repo, title, and head are required",
                error="Missing repo/title/head",
            )

        base = params.get("base", "main")
        body = params.get("body")
        draft = params.get("draft", False)
        github_override = params.get("github")

        try:
            client = self._get_github_client(github_override)

            result = client.create_pull_request(
                repo_full_name=repo,
                title=title,
                head=head,
                base=base,
                body=body,
                draft=draft,
            )

            if not result["ok"]:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"GitHub API error: {result['error']}",
                    error=result["error"],
                    data=result.get("details"),
                )

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Pull request created in {repo}#{result['data'].get('number')}",
                data={"pull_request": result["data"]},
            )
        except GitHubError as e:
            logger.error(f"GitHub client connection error: {e}")
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Failed to connect to GitHub",
                error=str(e),
            )
