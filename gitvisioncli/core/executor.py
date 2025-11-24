# gitvisioncli/core/executor.py
"""
GitVisionCLI Executor
Facade for the ActionSupervisor.

This class is the main entry point for the ChatEngine. It handles two
types of actions:
1.  **Special Executor Actions**: Commands that change the state of the
    Executor itself (e.g., 'ChangeDirectory', 'OpenEditor').
2.  **Supervisor Actions**: All other actions (e.g., 'CreateFile',
    'GitHubCreateRepo') which are passed directly to the ActionSupervisor.
"""

import logging
import shutil
import subprocess
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from pathlib import Path

from gitvisioncli.core.supervisor import (
    ActionSupervisor,
    ActionResult,
    ActionContext,
    ActionType,
    ActionStatus,
    SecurityPolicy,
    GitHubClientConfig,
)
# --- PHASE 1 UPDATE ---
from gitvisioncli.core.terminal import TerminalEngine
# ----------------------

logger = logging.getLogger(__name__)


# ---------------------------
# Utility — normalize type
# ---------------------------
def normalize_action_type(raw_type: Any) -> Optional[ActionType]:
    """
    Normalizes various string formats to a canonical ActionType enum.
    e.g., "CreateFile", "create_file", "create file" -> ActionType.CREATE_FILE
    """
    if not isinstance(raw_type, str):
        return None

    # Clean string: remove separators, lowercase
    cleaned = raw_type.replace("-", "").replace("_", "").replace(" ", "").lower()

    # Match against ActionType enum values
    for at in ActionType:
        enum_cleaned = at.value.replace("_", "").lower()
        if cleaned == enum_cleaned:
            return at

    # Special alias mapping
    if cleaned == "createfolder":
        return ActionType.CREATE_FOLDER
    if cleaned == "deletefolder":
        return ActionType.DELETE_FOLDER

    # Map higher-level editing aliases onto canonical text actions.
    if cleaned == "overwritefile":
        return ActionType.REWRITE_ENTIRE_FILE
    if cleaned in {"appendline", "insertatbottom"}:
        return ActionType.INSERT_AT_BOTTOM
    if cleaned in {"prependline", "insertattop"}:
        return ActionType.INSERT_AT_TOP
    if cleaned in {"replaceline", "updateline", "replacelinerange"}:
        # ReplaceLine / UpdateLine / ReplaceLineRange are modeled as block replacements
        return ActionType.REPLACE_BLOCK
    if cleaned in {"deleteline"}:
        return ActionType.DELETE_LINE_RANGE
    if cleaned in {"deletebypattern"}:
        return ActionType.DELETE_BY_PATTERN
    if cleaned in {"replacebypattern"}:
        return ActionType.REPLACE_BY_PATTERN
    if cleaned in {"replacebyfuzzymatch"}:
        return ActionType.REPLACE_BY_FUZZY_MATCH
    if cleaned in {"insertblock"}:
        return ActionType.INSERT_BLOCK_AT_LINE
    if cleaned in {"removeblock"}:
        return ActionType.REMOVE_BLOCK

    if cleaned in {"insertintofunction"}:
        return ActionType.INSERT_INTO_FUNCTION
    if cleaned in {"insertintoclass"}:
        return ActionType.INSERT_INTO_CLASS
    if cleaned in {"adddecorator"}:
        return ActionType.ADD_DECORATOR
    if cleaned in {"addimport", "autoimport"}:
        return ActionType.ADD_IMPORT


    return None


def normalize_action_content(action: Dict[str, Any]) -> str:
    """
    GitVision AI may send:
    - content
    - text
    - value
    - body
    This function extracts whichever exists.
    Never return None. Always return a string.
    """
    params = action.get("params", {}) or {}
    return (
        params.get("content")
        or params.get("text")
        or params.get("value")
        or params.get("body")
        or ""
    )


# ---------------------------
# Executor
# ---------------------------
class AIActionExecutor:
    """
    Facade wrapper for ActionSupervisor.
    Dispatches filesystem, git, search, shell, and GitHub actions.
    """

    def __init__(
        self,
        base_dir: Union[str, Path],
        dry_run: bool = False,
        security_policy: Optional[SecurityPolicy] = None,
        github_config: Optional[GitHubClientConfig] = None,
    ):
        # base_dir here starts as the Project Root.
        # It will update as we 'cd' around, representing the USER'S CURRENT VIEW.
        self.base_dir = Path(base_dir).resolve()
        self.dry_run = dry_run
        self.fs_watcher = None

        # --- PHASE 1 UPDATE: Initialize Central Terminal Engine ---
        # NOTE: patch_engine will be wired after Supervisor is created.
        self.terminal = TerminalEngine(self.base_dir)
        # ----------------------------------------------------------

        # security policy
        if security_policy is None:
            security_policy = SecurityPolicy(base_dir=self.base_dir)

        # supervisor
        # FIX 1.1: Supervisor is anchored to the initial PROJECT ROOT.
        # We do NOT update this when we 'cd'.
        self.supervisor = ActionSupervisor(
            base_dir=str(self.base_dir),
            security_policy=security_policy,
            github_config=github_config,
            terminal_engine=self.terminal,  # Pass the engine to supervisor
        )

        # ---- CRITICAL: Wire SafePatchEngine into TerminalEngine ----
        # This ensures echo "x" > file, sed-style edits, etc. go through SafePatch.
        if hasattr(self.supervisor, "safe_patch"):
            self.terminal.patch_engine = self.supervisor.safe_patch
        # -----------------------------------------------------------

        # Keep Executor's base_dir in sync with TerminalEngine.cwd,
        # even when `cd` occurs via raw shell commands.
        if hasattr(self.terminal, "on_directory_change"):
            self.terminal.on_directory_change = self._on_terminal_directory_change

        # Define special commands handled by the Executor, not Supervisor
        self.special_commands: Set[str] = {
            "changedirectory",
            "navigateback",
            "openeditor",
        }

        logger.info(f"Executor ready base_dir={self.base_dir}")

    # ---------------------------------------------------------------
    # Internal hooks
    # ---------------------------------------------------------------
    def _on_terminal_directory_change(self, new_cwd: Path) -> None:
        """
        Called whenever TerminalEngine.cwd changes (shell cd, planner shell steps, etc.).
        Keeps the executor's base_dir aligned with the visible terminal cwd.
        """
        try:
            self.base_dir = Path(new_cwd).resolve()
            logger.info(f"Executor base_dir synced to Terminal cwd: {self.base_dir}")
        except Exception as e:
            logger.warning(f"Failed to sync Executor base_dir from Terminal: {e}")

    # ---------------------------------------------------------------
    # FS watcher
    # ---------------------------------------------------------------
    def set_fs_watcher(self, watcher) -> None:
        """Links the FSWatcher to the Supervisor for UI updates."""
        self.fs_watcher = watcher
        self.supervisor.set_fs_watcher(watcher)
        
        # Wire filesystem changes to refresh UI components
        if watcher and hasattr(watcher, 'register_callback'):
            def on_fs_change(event):
                """Refresh UI when filesystem changes occur."""
                try:
                    # Force refresh of tree panel if active
                    # Force refresh of editor if file is open and not modified
                    # This is handled by PanelManager.handle_fs_event
                    pass  # PanelManager will handle the refresh logic
                except Exception as e:
                    logger.debug(f"FS change callback error (non-fatal): {e}")
            
            # The watcher already has callbacks registered by CLI
            # This is just ensuring the connection exists
            logger.debug("FS watcher connected to executor")

    # ---------------------------------------------------------------
    # Special Executor-level Action Handlers
    # ---------------------------------------------------------------

    def _change_directory(self, new_path: str) -> ActionResult:
        """
        Handles the 'ChangeDirectory' action.
        This changes the state of the Executor (User View) and Terminal (Shell CWD).
        It DOES NOT change the Supervisor (Sandbox Root).
        """
        try:
            # Handle explicit parent directory
            if new_path == "..":
                target = self.base_dir.parent
            else:
                p = Path(new_path)

                # Absolute path → trust directly
                if p.is_absolute():
                    target = p.resolve()
                else:
                    # We have two candidates:
                    # 1) relative to project ROOT (security_policy.base_dir)
                    # 2) relative to current VIEW (self.base_dir)
                    root = Path(self.supervisor.security_policy.base_dir).resolve()
                    root_candidate = (root / p).resolve()
                    current_candidate = (self.base_dir / p).resolve()

                    # Prefer the one that actually exists as a directory
                    if root_candidate.is_dir() and not current_candidate.is_dir():
                        target = root_candidate
                    elif current_candidate.is_dir():
                        target = current_candidate
                    else:
                        # Fallback: try root_candidate and let the not-dir check fail if needed
                        target = root_candidate

            # Simple check: is it a dir?
            if not target.is_dir():
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"Directory not found: {new_path}",
                    error="Path is not a directory or does not exist",
                )

            # --- STABILIZATION FIX 1.1 ---
            # Update local view state
            self.base_dir = target

            # Update Terminal Engine CWD
            self.terminal.cwd = target

            # CRITICAL: DO NOT update self.supervisor.base_dir or security policy.
            # The supervisor stays anchored to the project root.

            logger.info(f"Changed directory to: {self.base_dir}")
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Changed directory to: {self.base_dir.as_posix()}",
                data={"path": str(self.base_dir)},
            )
        except Exception as e:
            logger.error(f"Failed to change directory: {e}", exc_info=True)
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Failed to change directory",
                error=str(e),
            )

    def _navigate_back(self) -> ActionResult:
        """Handles the 'NavigateBack' (e.g., `:back`) action."""
        return self._change_directory("..")

    def _open_editor(self, file_path: str, editor: str = "nano") -> ActionResult:
        """Handles the 'OpenEditor' action (nano or code)."""

        # Resolve path relative to current view (self.base_dir)
        full_path = (self.base_dir / file_path).resolve()

        # Use supervisor's policy to validate against SANDBOX ROOT
        valid, error = self.supervisor.security_policy.validate_path(full_path)
        if not valid:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Invalid editor path",
                error=error,
            )

        # Allow creating a new file
        if not full_path.exists():
            pass

        # But block opening a directory
        elif not full_path.is_file():
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Path is a directory, not a file",
                error="Cannot open a directory in editor",
            )

        try:
            editor_cmd = "nano"  # Default
            if editor == "code":
                if shutil.which("code") is not None:
                    editor_cmd = "code"
                else:
                    logger.warning("VSCode ('code') not in PATH, defaulting to nano.")

            # Use subprocess.call to block until the editor is closed
            subprocess.call([editor_cmd, str(full_path)])

            # Notify watcher that file *may* have changed
            if self.fs_watcher:
                self.fs_watcher.check_once()
                self.fs_watcher.manual_trigger("editor_close")

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Closed {file_path} (opened with {editor_cmd})",
                data={"path": str(full_path)},
            )

        except Exception as e:
            logger.error(f"Failed to open editor: {e}", exc_info=True)
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Editor error",
                error=str(e),
            )

    # ---------------------------------------------------------------
    # RUN SINGLE ACTION (called by ChatEngine)
    # ---------------------------------------------------------------
    def run_action(
        self,
        action: Dict[str, Any],
        context: Optional[ActionContext] = None,
    ) -> ActionResult:
        """
        Main entry point to run a single action.
        It checks for special executor actions first, then passes
        all other actions to the ActionSupervisor.
        """
        if context is None:
            context = ActionContext(dry_run=self.dry_run)
        else:
            # Ensure strict boolean logic
            context.dry_run = bool(context.dry_run) or bool(self.dry_run)

        # Safety check: If dry_run is active, log it (debug only)
        if context.dry_run:
            logger.debug(f"EXECUTOR: Action {action.get('type')} running in DRY-RUN mode")





        if "type" not in action:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message="Action 'type' is missing",
            )

        raw_type = action.get("type", "").lower()
        params = action.get("params", {}) or {}

        # --- 0. NORMALIZE CONTENT (Fix for silent failures) ---
        # AI often sends "text", "value", "body" instead of "content".
        # Check BOTH action root level AND params level.
        content_from_root = (
            action.get("content")
            or action.get("text")
            or action.get("value")
            or action.get("body")
        )
        content_from_params = (
            params.get("content")
            or params.get("text")
            or params.get("value")
            or params.get("body")
        )
        
        # Priority: params > root level
        final_content = content_from_params or content_from_root
        
        if final_content is not None and "content" not in params:
            params["content"] = final_content
            logger.debug(f"Normalized content: {len(final_content)} chars")


        # --- 1. Handle Special Executor-level Actions FIRST (no path mangling) ---

        if raw_type == "changedirectory":
            if "path" not in params:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Missing 'path' for ChangeDirectory",
                )
            return self._change_directory(params["path"])

        if raw_type == "navigateback":
            return self._navigate_back()

        if raw_type == "openeditor":
            if "path" not in params:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Missing 'path' for OpenEditor",
                )
            return self._open_editor(
                file_path=params["path"],
                editor=params.get("editor", "nano"),
            )

        if raw_type == "openfile":
            # OpenFile is handled by the CLI to open in internal editor panel
            # This action just validates the path and returns success with file path
            if "path" not in params:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Missing 'path' for OpenFile",
                )
            
            # Resolve path relative to current view (self.base_dir)
            full_path = (self.base_dir / params["path"]).resolve()
            
            # Use supervisor's policy to validate against SANDBOX ROOT
            valid, error = self.supervisor.security_policy.validate_path(full_path)
            if not valid:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message="Invalid file path",
                    error=error,
                )
            
            # Check if file exists
            if not full_path.exists():
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"File not found: {params['path']}",
                    error="File does not exist",
                )
            
            # Check if it's actually a file (not a directory)
            if not full_path.is_file():
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"Path is a directory, not a file: {params['path']}",
                    error="Cannot open a directory",
                )
            
            # Return success with file path for CLI to handle
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"File ready to open: {params['path']}",
                data={"path": str(full_path), "relative_path": params["path"]},
            )

        # --- 2. Normalize type and perform path resolution for Supervisor actions ---

        atype = normalize_action_type(raw_type)
        if not atype:
            return ActionResult(
                status=ActionStatus.FAILURE,
                message=f"Unknown or unhandled action type: {action.get('type')}",
            )

        # For create-like actions, paths MUST be resolved relative to the
        # user's current working directory (Executor.base_dir / TerminalEngine.cwd)
        # to avoid accidental doubling such as demo/demo/src.
        if "path" in params:
            p = Path(params["path"])

            # Absolute path → leave as is (Supervisor + SecurityPolicy will validate)
            if not p.is_absolute():
                if atype in {ActionType.CREATE_FOLDER, ActionType.CREATE_FILE}:
                    # Always anchor folder/file creation to the user's current view.
                    params["path"] = str((self.base_dir / p).resolve())
                else:
                    # Existing heuristic for read/edit/delete/etc.
                    root = Path(self.supervisor.security_policy.base_dir).resolve()
                    root_candidate = (root / p).resolve()
                    current_candidate = (self.base_dir / p).resolve()

                    # Prefer existing target; otherwise default to "current view"
                    if root_candidate.exists() and not current_candidate.exists():
                        params["path"] = str(root_candidate)
                    elif current_candidate.exists():
                        params["path"] = str(current_candidate)
                    else:
                        params["path"] = str(current_candidate)
            
            # CRITICAL FIX: Prevent path doubling (e.g., /path/to/demo/demo/app.py)
            # Check if the resolved path contains base_dir twice and fix it
            resolved_path = Path(params["path"]).resolve()
            base_dir_resolved = self.base_dir.resolve()
            path_str = str(resolved_path)
            base_str = str(base_dir_resolved)
            base_name = base_dir_resolved.name
            
            # Pattern: /path/to/demo/demo/file -> /path/to/demo/file
            # Check if path contains: base_dir + "/" + base_name + "/"
            duplicate_pattern = f"{base_str}/{base_name}/"
            if duplicate_pattern in path_str:
                # Remove the duplicate: base_dir + "/" + base_name
                fixed_str = path_str.replace(f"{base_str}/{base_name}", base_str, 1)
                params["path"] = str(Path(fixed_str).resolve())
                logger.debug(f"Fixed doubled path: {path_str} -> {params['path']}")

        # Update action with canonical type string for the supervisor
        action["type"] = atype.value

        # Pass the validated, normalized action to the supervisor
        result = self.supervisor.handle_ai_action(action, context)

        # ---- NEW: Force FSWatcher to refresh Editor panel ----
        if self.fs_watcher:
            self.fs_watcher.manual_trigger("ai_modify")

        # ---- NEW: Sync documentation after file changes ----
        if result.modified_files:
            try:
                from gitvisioncli.core.doc_sync import DocumentationSyncer
                doc_syncer = DocumentationSyncer(self.base_dir)
                modified_paths = [Path(f) for f in result.modified_files]
                doc_syncer.sync_documentation(modified_paths, action_type=atype.value if atype else None)
            except Exception as e:
                logger.debug(f"Documentation sync failed (non-fatal): {e}")

        return result

    # ---------------------------------------------------------------
    # MULTI-ACTION PLAN (atomic/batch)
    # ---------------------------------------------------------------
    def run_plan(
        self,
        actions: List[Dict[str, Any]],
        atomic: bool = False,
        context: Optional[ActionContext] = None,
    ) -> ActionResult:
        """
        Runs a list of actions as a single batch or atomic operation
        by wrapping them and sending to the supervisor.
        """
        if context is None:
            context = ActionContext(dry_run=self.dry_run)
        else:
            context.dry_run = bool(context.dry_run) or bool(self.dry_run)


        # Sanitize all action types in the plan *before* sending
        sanitized_actions = []
        for act in actions:
            raw_type = act.get("type")
            atype = normalize_action_type(raw_type)

            if not atype:
                return ActionResult(
                    status=ActionStatus.FAILURE,
                    message=f"Plan contains unknown action type: {raw_type}",
                )

            # Use canonical type string
            act["type"] = atype.value
            sanitized_actions.append(act)

        # Wrap the sanitized list in a single supervisor action
        wrapper_action = {
            "type": (
                ActionType.ATOMIC_OPERATION.value
                if atomic
                else ActionType.BATCH_OPERATION.value
            ),
            "params": {"actions": sanitized_actions},
        }

        # The supervisor will handle the batch/atomic logic
        result = self.supervisor.handle_ai_action(wrapper_action, context)

        if self.fs_watcher:
            self.fs_watcher.manual_trigger("ai_batch_modify")

        return result

    # ---------------------------------------------------------------
    # DRY RUN + UTIL
    # ---------------------------------------------------------------
    def enable_dry_run(self):
        self.dry_run = True

    def disable_dry_run(self):
        self.dry_run = False

    def is_dry_run(self) -> bool:
        return self.dry_run

    def get_base_dir(self) -> Path:
        return self.base_dir

    # ---------------------------------------------------------------
    # VALIDATION + HELP
    # ---------------------------------------------------------------
    def validate_action(self, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Checks if an action dict is well-formed."""
        if not isinstance(action, dict):
            return False, "Action must be a dictionary"

        if "type" not in action:
            return False, "Action is missing 'type' key"

        raw_type = action["type"].lower()

        if "params" not in action or not isinstance(action["params"], dict):
            return False, "Action is missing 'params' key or params is not a dict"

        # Check if it's a special command
        if raw_type in self.special_commands:
            # Add simple param checks for special commands
            if raw_type == "changedirectory" and "path" not in action["params"]:
                return False, "ChangeDirectory requires 'path' param"
            if raw_type == "openeditor" and "path" not in action["params"]:
                return False, "OpenEditor requires 'path' param"
            return True, None

        # If not special, check if it's a valid supervisor action
        if not normalize_action_type(raw_type):
            return False, f"Unknown action type: {action['type']}"

        return True, None

    def get_supported_actions(self) -> List[str]:
        """Returns all valid action type strings."""
        supervisor_actions = [t.value for t in ActionType]
        special_actions = [
            "ChangeDirectory",
            "NavigateBack",
            "OpenEditor",
        ]
        return supervisor_actions + special_actions

    def get_action_help(self, action_type: str) -> Dict[str, Any]:
        """Provides basic help for an action (schema)."""
        # This can be expanded with full JSON schemas later
        if action_type.lower() == "changedirectory":
            return {
                "description": "Changes the current working directory.",
                "params": {"path": "str"},
            }
        if action_type.lower() == "navigateback":
            return {
                "description": "Goes up one directory (e.g., 'cd ..').",
                "params": {},
            }
        if action_type.lower() == "openeditor":
            return {
                "description": "Opens a file in a terminal editor.",
                "params": {"path": "str", "editor": "str (optional: 'nano' or 'code')"},
            }

        # Default for supervisor actions
        return {
            "description": f"Supervisor action: {action_type}",
            "params": {"..."},
        }
