# gitvisioncli/workspace/right_panel.py
"""
Right Panel – Unified Workspace Renderer
Shows TREE / EDITOR / MARKDOWN / BANNER views.
Fully synchronized with PanelManager + FSWatcher.
"""

import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Any

from .panel_manager import PanelManager, PanelMode
from .tree_panel import TreePanel
from .editor_panel import EditorPanel
from .markdown_panel import MarkdownPanel
from .banner_panel import BannerPanel
from .sheet_panel import CommandSheetPanel
from .model_manager_panel import ModelManagerPanel
from .git_graph_panel import GitGraphPanel

logger = logging.getLogger(__name__)


@dataclass
class RightPanel:
    """
    Main controller for right side panels.
    Rendering happens every frame through DualPanelRenderer.
    """
    base_dir: Path
    panel_manager: PanelManager
    width: int = 80

    # Sub-panels
    tree_panel: TreePanel = field(init=False)
    editor_panel: EditorPanel = field(init=False)
    markdown_panel: MarkdownPanel = field(init=False)
    banner_panel: BannerPanel = field(init=False)
    sheet_panel: CommandSheetPanel = field(init=False)
    models_panel: ModelManagerPanel = field(init=False)
    git_graph_panel: GitGraphPanel = field(init=False)

    def __post_init__(self):
        """Initialize subpanels using provided width."""
        self.tree_panel = TreePanel(str(self.base_dir), width=self.width)

        # Wire editor callbacks into PanelManager so that the modified
        # flag and UI state stay in sync with the in-memory buffer.
        self.editor_panel = EditorPanel(
            width=self.width,
            on_change_callback=self._on_editor_change,
            on_modified_callback=self._on_editor_modified,
        )
        self.markdown_panel = MarkdownPanel(width=self.width)
        self.banner_panel = BannerPanel(width=self.width)
        self.sheet_panel = CommandSheetPanel(width=self.width)
        self.models_panel = ModelManagerPanel(width=self.width)
        # Git graph panel is read-only and uses the shared ActionSupervisor
        # via PanelManager's attached UI (RightPanel itself).
        from gitvisioncli.core.supervisor import ActionSupervisor  # local import
        supervisor: Optional[ActionSupervisor] = getattr(self.panel_manager, "supervisor", None)  # type: ignore[attr-defined]
        if supervisor is not None:
            self.git_graph_panel = GitGraphPanel(supervisor=supervisor, width=self.width)
        else:
            # Dummy panel that renders an informative message if supervisor is missing
            self.git_graph_panel = GitGraphPanel(supervisor=None, width=self.width)  # type: ignore[arg-type]

    # ----------------------------------------------------------------------
    # Editor callbacks → PanelManager
    # ----------------------------------------------------------------------
    def _on_editor_change(self) -> None:
        """
        Invoked whenever the EditorPanel buffer content changes.
        Currently the main render loop re-draws every tick, so we do not
        need to force a redraw here, but the hook is kept for extensibility.
        """
        # Placeholder for future smart refresh logic
        logger.debug("RightPanel: editor content changed.")

    def _on_editor_modified(self, is_modified: bool) -> None:
        """
        Keep PanelManager's modified flag aligned with the editor buffer.
        This is used by PanelManager.handle_fs_event to decide whether
        disk changes should overwrite the in-memory buffer.
        """
        try:
            self.panel_manager.set_modified(is_modified)
        except Exception as e:
            logger.warning(f"RightPanel: failed to update modified state: {e}")

    # ----------------------------------------------------------------------
    # Mode header name (required by DualPanelRenderer)
    # ----------------------------------------------------------------------
    def get_current_mode_name(self) -> str:
        """Pretty name for panel header."""
        try:
            return self.panel_manager.get_current_mode_name()
        except Exception:
            return "Unknown"

    # ----------------------------------------------------------------------
    # Directory state
    # ----------------------------------------------------------------------
    def update_base_dir(self, new_base_dir: Path):
        """
        Update workspace directory without changing active mode.
        Does NOT auto-open Tree panel.
        """
        self.base_dir = new_base_dir
        self.tree_panel.update_base_dir(new_base_dir)

        # Clear stale file reference
        self.panel_manager.clear_file()

        # Refresh tree only if tree mode is active
        if self.panel_manager.get_mode() == PanelMode.TREE:
            self.refresh_tree_panel()

    def refresh_tree_panel(self):
        """Refresh tree listing without changing panel."""
        self.tree_panel.update_base_dir(self.base_dir)

    # ----------------------------------------------------------------------
    # FSWatcher event hook
    # ----------------------------------------------------------------------
    def on_fs_change(self, change: Optional[Any] = None):
        """
        FSWatcher calls this directly.
        Delegates handling to PanelManager logic.
        """
        try:
            self.panel_manager.handle_fs_event(change)
        except Exception as e:
            logger.error(f"RightPanel: FS change error {e}")

    # ----------------------------------------------------------------------
    # RENDER ACTIVE PANEL
    # ----------------------------------------------------------------------
    def render_as_lines(self) -> List[str]:
        """Render active panel contents as list of lines."""
        mode = self.panel_manager.get_mode()

        # Sync widths before rendering
        self.tree_panel.width = self.width
        self.editor_panel.width = self.width
        self.markdown_panel.width = self.width
        self.banner_panel.width = self.width
        self.sheet_panel.width = self.width
        self.models_panel.width = self.width
        self.git_graph_panel.width = self.width

        try:
            # TREE MODE
            if mode == PanelMode.TREE:
                return self.tree_panel.render_content_lines()

            # EDITOR MODE
            if mode == PanelMode.EDITOR:
                active = self.panel_manager.get_active_path()
                if active and self.editor_panel.file_path != active:
                    self.editor_panel.load_file(active)
                return self.editor_panel.render_content_lines()

            # MARKDOWN MODE
            if mode == PanelMode.MARKDOWN:
                active = self.panel_manager.get_active_path()
                if active and self.markdown_panel.file_path != active:
                    self.markdown_panel.load_file(active)
                return self.markdown_panel.render_content_lines()

            # COMMAND SHEET MODE
            if mode == PanelMode.SHEET:
                return self.sheet_panel.render_content_lines()

            # MODEL MANAGER MODE
            if mode == PanelMode.MODELS:
                return self.models_panel.render_content_lines()

            # GIT GRAPH MODE
            if mode == PanelMode.GIT_GRAPH:
                return self.git_graph_panel.render_content_lines()

            # BANNER MODE (default)
            return self.banner_panel.render_as_lines()

        except Exception as e:
            logger.error(f"RightPanel render failed: {e}", exc_info=True)
            return [f"Render error: {e}"]

    # ----------------------------------------------------------------------
    # ':' WORKSPACE COMMANDS
    # ----------------------------------------------------------------------
    def handle_command(self, command: str):
        """
        Supported commands:
            :tree
            :banner
            :sheet
            :close
            :edit <file>
            :markdown <file>
            :save
            :up / :down / :pageup / :pagedown   (editor scrolling)
        """
        parts = command.strip().split()
        if not parts:
            return False, ""

        cmd = parts[0]

        try:
            # Switch to TREE
            if cmd == ":tree":
                self.panel_manager.clear_file()
                self.panel_manager.set_mode(PanelMode.TREE)
                return True, "Tree view activated."

            # Switch to BANNER
            if cmd == ":banner":
                self.panel_manager.clear_file()
                self.panel_manager.set_mode(PanelMode.BANNER)
                return True, "Banner view restored."

            # Git commit graph (support both :gitgraph and :git-graph)
            if cmd in {":gitgraph", ":git-graph"}:
                self.panel_manager.clear_file()
                self.panel_manager.set_mode(PanelMode.GIT_GRAPH)
                return True, "Git commit graph opened."

            # Open COMMAND SHEET
            if cmd in {":sheet", ":commands"}:
                self.panel_manager.clear_file()
                self.panel_manager.set_mode(PanelMode.SHEET)
                return True, "Command sheet opened."

            # Model manager sheet
            if cmd == ":models":
                self.panel_manager.clear_file()
                self.panel_manager.set_mode(PanelMode.MODELS)
                return True, "Model manager opened."

            # Universal close for any panel mode
            if cmd in {":close", ":x"}:
                self.panel_manager.clear_file()
                self.panel_manager.set_mode(PanelMode.BANNER)
                return True, "Right panel closed. Banner restored."

            # Markdown preview
            if cmd == ":markdown":
                if len(parts) < 2:
                    return False, "Usage: :markdown <file>"

                filepath = self.base_dir / parts[1]

                if not filepath.exists():
                    return False, f"File not found: {parts[1]}"
                if not filepath.is_file():
                    return False, f"Not a file: {parts[1]}"

                if self.markdown_panel.load_file(filepath):
                    self.panel_manager.open_file(filepath)
                    self.panel_manager.set_mode(PanelMode.MARKDOWN)
                    return True, f"Markdown loaded: {parts[1]}"

                return False, "Could not load markdown."

            # Open file in Editor (unified :edit command - auto-enables live edit if file exists)
            if cmd == ":edit":
                if len(parts) < 2:
                    return False, "Usage: :edit <file>"

                filepath = self.base_dir / parts[1]

                # Allow creating new files (touch-like behavior)
                if filepath.exists() and not filepath.is_file():
                    return False, f"Not a file: {parts[1]}"

                if self.editor_panel.load_file(filepath):
                    self.panel_manager.open_file(filepath)
                    self.panel_manager.set_mode(PanelMode.EDITOR)
                    # If file exists, automatically enable live edit mode for seamless AI editing
                    if filepath.exists() and filepath.is_file():
                        # Return special marker to trigger live edit prompt in CLI
                        return True, f"LIVE_EDIT_READY:{parts[1]}"
                    else:
                        # New file - just open in editor without live edit
                        return True, f"Editing: {parts[1]}"

                return False, f"Could not load: {parts[1]}"

            # Legacy :live-edit command (now just an alias for :edit)
            if cmd == ":live-edit":
                if len(parts) < 2:
                    return False, "Usage: :live-edit <file> (use :edit instead)"

                filepath = self.base_dir / parts[1]

                # File must exist for live editing
                if not filepath.exists():
                    return False, f"File not found: {parts[1]}"
                if not filepath.is_file():
                    return False, f"Not a file: {parts[1]}"

                # Open file in EDITOR mode with live edit
                if self.editor_panel.load_file(filepath):
                    self.panel_manager.open_file(filepath)
                    self.panel_manager.set_mode(PanelMode.EDITOR)
                    # Return special marker to trigger live edit prompt in CLI
                    return True, f"LIVE_EDIT_READY:{parts[1]}"

                return False, f"Could not load: {parts[1]}"


            # Save editor buffer
            if cmd == ":save":
                if self.panel_manager.get_mode() != PanelMode.EDITOR:
                    return False, "Not in editor mode."

                if self.editor_panel.save_file():
                    self.panel_manager.set_modified(False)
                    return True, "File saved."

                return False, "Save failed."

            # Editor scrolling (viewport only; buffer is unchanged)
            if cmd in {":up", ":scroll-up"}:
                if self.panel_manager.get_mode() != PanelMode.EDITOR:
                    return False, "Scroll commands are only available in editor mode."
                self.editor_panel.scroll_up()
                return True, ""

            if cmd in {":down", ":scroll-down"}:
                if self.panel_manager.get_mode() != PanelMode.EDITOR:
                    return False, "Scroll commands are only available in editor mode."
                self.editor_panel.scroll_down()
                return True, ""

            if cmd in {":pageup", ":pu"}:
                if self.panel_manager.get_mode() != PanelMode.EDITOR:
                    return False, "Scroll commands are only available in editor mode."
                self.editor_panel.page_up()
                return True, ""

            if cmd in {":pagedown", ":pd"}:
                if self.panel_manager.get_mode() != PanelMode.EDITOR:
                    return False, "Scroll commands are only available in editor mode."
                self.editor_panel.page_down()
                return True, ""

        except Exception as e:
            logger.error(f"Command error: {command}", exc_info=True)
            return False, f"Command failed: {e}"

        return False, "Unknown command."

    # ----------------------------------------------------------------------
    # AI CONTEXT
    # ----------------------------------------------------------------------
    def get_workspace_context(self) -> dict:
        """
        Summary of workspace state for ChatEngine prompt context.
        Includes editor buffer when EDITOR mode active.
        """
        ctx = self.panel_manager.export_context()

        if self.panel_manager.get_mode() == PanelMode.EDITOR:
            try:
                ctx["file_content"] = self.editor_panel.get_text()
            except Exception as e:
                ctx["file_content"] = f"Error reading: {e}"

        return ctx
