import os
import shutil
import logging
import re
from pathlib import Path
from typing import Union, Optional, Dict, Any

from gitvisioncli.core.editing_engine import EditingEngine, EditingError

logger = logging.getLogger(__name__)


class SafePatchEngine:
    """
    Safe Patch Engine (Stage 2)

    - Only Python-based file editing
    - Backup-compatible
    - Secure sandbox (never leaves workspace root)
    """

    def __init__(self, project_root: Union[str, Path], backup_dir: Optional[Path] = None):
        self.project_root = Path(project_root).resolve()
        self.cwd = self.project_root   # Updated dynamically by TerminalEngine

        self.backup_dir = backup_dir
        if self.backup_dir:
            self.backup_dir = Path(self.backup_dir)
            self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Use the shared EditingEngine so that low-level text semantics
        # match ActionSupervisor’s behavior for all operations.
        self._engine = EditingEngine(base_dir=self.project_root)

    # -----------------------------------------------------------
    # PATH VALIDATION (CRITICAL)
    # -----------------------------------------------------------

    def _validate_path(self, file_path: Union[str, Path]) -> Path:
        """
        Ensures file_path is always inside the project root.
        """
        path = Path(self.cwd / file_path).resolve()

        if self.project_root not in path.parents and path != self.project_root:
            raise ValueError(f"Sandbox Violation: {path} outside workspace root")

        return path

    # -----------------------------------------------------------
    # BACKUP
    # -----------------------------------------------------------

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        if not file_path.exists():
            return None

        # backup basic
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")

        if self.backup_dir:
            timestamp = int(os.path.getmtime(file_path))
            safe_name = f"{file_path.name}_{timestamp}.bak"
            backup_path = self.backup_dir / safe_name

        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    # -----------------------------------------------------------
    # READ
    # -----------------------------------------------------------

    def _read_content(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="latin-1")

    # -----------------------------------------------------------
    # EDIT INTENTS (With CommandNormalizer)
    # -----------------------------------------------------------

    def apply_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        intent_type = intent.get("type")
        path = intent.get("path")
        content = intent.get("content", "")

        result = {"success": False, "backup": None, "path": path}

        try:
            if intent_type == "intent_rewrite_file":
                result["backup"] = self.rewrite_file(path, content)
                result["success"] = True

            elif intent_type == "intent_append_file":
                result["backup"] = self.append_to_file(path, content)
                result["success"] = True

            else:
                result["error"] = f"Unknown intent type: {intent_type}"

        except Exception as e:
            result["error"] = str(e)

        return result

    # -----------------------------------------------------------
    # OPERATIONS
    # -----------------------------------------------------------

    def rewrite_file(self, file_path: Union[str, Path], content: str):
        path = self._validate_path(file_path)
        backup = self._create_backup(path)
        # Normalize newlines via EditingEngine for consistency
        normalized = self._engine._normalize_newlines(content)
        path.write_text(normalized, encoding="utf-8")
        return backup

    def append_to_file(self, file_path: Union[str, Path], content: str):
        path = self._validate_path(file_path)
        backup = self._create_backup(path)

        current = self._read_content(path) if path.exists() else ""
        try:
            result = self._engine.insert_at_bottom(current, block=content)
            path.write_text(result.content, encoding="utf-8")
        except EditingError as e:
            logger.error(f"Append failed for {path}: {e}")
            raise

        return backup

    # ----------------------------------------------------------------
    # BLOCK REPLACER
    # ----------------------------------------------------------------

    def replace_block(self, file_path, old_block, new_block):
        path = self._validate_path(file_path)

        content = self._read_content(path)
        backup = self._create_backup(path)

        try:
            result = self._engine.replace_by_exact_match(
                content,
                old=self._engine._normalize_newlines(old_block),
                new=self._engine._normalize_newlines(new_block),
            )
            path.write_text(result.content, encoding="utf-8")
        except EditingError as e:
            raise ValueError(str(e)) from e

        return backup

    # ----------------------------------------------------------------
    # INSERTION
    # ----------------------------------------------------------------

    def insert_block_before_match(self, file_path, pattern, block):
        path = self._validate_path(file_path)
        content = self._read_content(path)

        m = re.search(pattern, content)
        if not m:
            raise ValueError("Pattern not found")

        backup = self._create_backup(path)

        # Split around the match boundary and delegate to block insert
        prefix = content[: m.start()]
        suffix = content[m.start() :]
        combined = prefix + "\n" + block + ("\n" if not block.endswith("\n") else "") + suffix
        try:
            normalized = self._engine._normalize_newlines(combined)
            path.write_text(normalized, encoding="utf-8")
        except Exception as e:
            logger.error(f"insert_block_before_match failed for {path}: {e}")
            raise

        return backup

    def insert_block_after_match(self, file_path, pattern, block):
        path = self._validate_path(file_path)
        content = self._read_content(path)

        m = re.search(pattern, content)
        if not m:
            raise ValueError("Pattern not found")

        backup = self._create_backup(path)

        prefix = content[: m.end()]
        suffix = content[m.end() :]
        combined = prefix + ("\n" if not prefix.endswith("\n") else "") + block + ("\n" if not block.endswith("\n") else "") + suffix
        try:
            normalized = self._engine._normalize_newlines(combined)
            path.write_text(normalized, encoding="utf-8")
        except Exception as e:
            logger.error(f"insert_block_after_match failed for {path}: {e}")
            raise

        return backup
