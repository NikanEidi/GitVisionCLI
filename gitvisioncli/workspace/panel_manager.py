# gitvisioncli/workspace/panel_manager.py
"""
Panel Manager – Centralized workspace state controller.
Keeps UI state in sync with RightPanel and FSWatcher.
"""

import logging
from enum import Enum, auto
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PanelMode(Enum):
    BANNER = auto()
    TREE = auto()
    EDITOR = auto()
    MARKDOWN = auto()
    SHEET = auto()
    MODELS = auto()
    GIT_GRAPH = auto()


class PanelManager:
    """
    Pure logical state manager:
    - Active panel mode
    - Active file path
    - Modified state

    No rendering, no file I/O here.
    """

    def __init__(self):
        self.mode: PanelMode = PanelMode.BANNER
        self.active_path: Optional[Path] = None
        self.is_modified: bool = False

        # UI references injected by attach_ui()
        self.right_panel = None
        self.editor_panel = None
        self.tree_panel = None

        logger.debug("PanelManager initialized.")

    # ---------------------------------------------------------
    # UI attachment (called once on startup)
    # ---------------------------------------------------------
    def attach_ui(self, right_panel, editor_panel, tree_panel):
        self.right_panel = right_panel
        self.editor_panel = editor_panel
        self.tree_panel = tree_panel
        logger.info("PanelManager: UI attached.")

    # ---------------------------------------------------------
    # MODE API
    # ---------------------------------------------------------
    def set_mode(self, mode: PanelMode):
        self.mode = mode
        logger.debug(f"PanelManager: mode changed -> {mode.name}")

    def get_mode(self) -> PanelMode:
        return self.mode

    # ---------------------------------------------------------
    # FILE STATE
    # ---------------------------------------------------------
    def open_file(self, filepath: Path):
        self.active_path = filepath
        self.is_modified = False
        logger.debug(f"PanelManager: active file = {filepath}")

    def clear_file(self):
        self.active_path = None
        self.is_modified = False
        logger.debug("PanelManager: active file cleared")

    def get_active_path(self) -> Optional[Path]:
        return self.active_path

    # ---------------------------------------------------------
    # MODIFIED FLAG
    # ---------------------------------------------------------
    def set_modified(self, status: bool = True):
        """
        Called by EditorPanel callbacks or RightPanel when buffer changes.
        This is the single source of truth for "dirty" state.
        """
        self.is_modified = status
        logger.debug(f"PanelManager: modified = {status}")

    def is_file_modified(self) -> bool:
        return self.is_modified

    # ---------------------------------------------------------
    # REQUIRED BY DualPanelRenderer
    # ---------------------------------------------------------
    def get_current_mode_name(self) -> str:
        """
        Return pretty panel mode name for the header.
        Example: EDITOR -> "Editor"
        """
        try:
            return self.mode.name.title()
        except Exception:
            return "Unknown"

    # ---------------------------------------------------------
    # FSWatcher integration
    # ---------------------------------------------------------
    def handle_fs_event(self, event):
        """
        Sync UI after filesystem changes.

        CRITICAL FIX:
        - Never overwrite unsaved in-memory edits.
        - Only reload Editor/Markdown contents from disk when
          the buffer is *not* marked as modified.
        """

        change_type = getattr(event, "change_type", "UNKNOWN")
        logger.info(f"PanelManager: FS event -> {change_type}")

        # TREE MODE → refresh tree
        if self.mode == PanelMode.TREE:
            try:
                self.tree_panel.update_base_dir(self.right_panel.base_dir)
            except Exception as e:
                logger.error(f"TreePanel update failed: {e}")

        # EDITOR MODE → reload file content only if NOT modified
        if self.mode == PanelMode.EDITOR and self.active_path:
            if not self.is_modified:
                try:
                    self.editor_panel.load_file(self.active_path)
                except Exception as e:
                    logger.error(f"Editor reload failed: {e}")
            else:
                logger.debug(
                    "PanelManager: FS event ignored in EDITOR mode "
                    "because buffer has unsaved changes (is_modified=True)."
                )

        # MARKDOWN MODE → reload file only if there's no unsaved state
        if self.mode == PanelMode.MARKDOWN and self.active_path:
            # Markdown is usually read-only, but we keep the same safety check.
            if not self.is_modified:
                try:
                    self.right_panel.markdown_panel.load_file(self.active_path)
                except Exception as e:
                    logger.error(f"Markdown reload failed: {e}")
            else:
                logger.debug(
                    "PanelManager: FS event ignored in MARKDOWN mode "
                    "because buffer is marked modified."
                )

    # ---------------------------------------------------------
    # AI context
    # ---------------------------------------------------------
    def export_context(self) -> dict:
        """Lightweight workspace summary for ChatEngine."""
        active_path_str = None

        if self.active_path:
            try:
                active_path_str = str(self.active_path.relative_to(Path.cwd()))
            except Exception:
                active_path_str = str(self.active_path)

        return {
            "mode": self.mode.name,
            "active_file": active_path_str,
            "is_modified": self.is_modified,
        }
