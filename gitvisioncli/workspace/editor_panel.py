# gitvisioncli/workspace/editor_panel.py
"""
Editor Panel — In-memory text buffer with line numbers and basic syntax highlighting.
This panel is designed to be the source of truth for the currently viewed/edited file.

Advanced version:
- Fully in-memory buffer (self.content)
- Line-number rendering for right panel
- Basic syntax highlighting (for standalone display)
- Normalized newlines (\r\n, \r -> \n)
- Multi-line operations (for AI / patch-like updates)
- Optional callbacks for UI + PanelManager synchronization
"""

import logging
from pathlib import Path
from typing import List, Optional, Callable, Dict
import re

from gitvisioncli.ui.colors import (
    BOLD,
    RESET,
    DIM,
    MID_GRAY,
    DARK_GRAY,
    NEON_PURPLE,
    GLITCH_GREEN,
    GLITCH_RED,
    ELECTRIC_CYAN,
)

logger = logging.getLogger(__name__)


class EditorPanel:
    """
    Terminal-based text editor with line numbers and basic syntax highlighting.

    DESIGN:
    - This class is a pure in-memory buffer.
    - It does NOT know anything about PanelManager directly.
      Instead, it exposes optional callbacks:
        * on_change_callback     → called whenever content changes
        * on_modified_callback   → called whenever is_modified flag changes
    - RightPanel (or whatever owns EditorPanel) can wire these callbacks
      to PanelManager.set_modified() and/or trigger UI refresh.

    IMPORTANT:
    - EditorPanel is the single source of truth for the file content
      while it is open in the IDE. Disk is only re-read when the user
      explicitly opens/reloads a file (or PanelManager decides to reload).
    """

    def __init__(
        self,
        width: int = 80,
        on_change_callback: Optional[Callable[[], None]] = None,
        on_modified_callback: Optional[Callable[[bool], None]] = None,
    ):
        # Render width (used by right panel to keep layout)
        self.width = width

        # In-memory text buffer (list of lines, without trailing newline)
        self.content: List[str] = []

        # Path to currently loaded file (absolute)
        self.file_path: Optional[Path] = None

        # "Dirty" flag — True if buffer has unsaved changes
        self.is_modified: bool = False

        # Reserved for future interactive movement
        self.cursor_line: int = 0
        # 1-based index of the last buffer line that should be visible
        # in the current viewport. When None, the view is anchored to
        # the bottom of the file.
        self.view_bottom_line: Optional[int] = None

        # External hooks (for UI + panel manager sync)
        self._on_change_callback = on_change_callback
        self._on_modified_callback = on_modified_callback

        # Simple syntax patterns for colorized render
        self.syntax_patterns: Dict[str, List] = {
            "python": [
                (
                    r"\b(def|class|import|from|if|else|elif|for|while|return|"
                    r"try|except|with|as|pass|break|continue|yield)\b",
                    BOLD,
                ),
                (r"#.*$", DIM + MID_GRAY),
                (r'["\'].*?["\']', GLITCH_GREEN),
                (r"\b\d+\b", ELECTRIC_CYAN),
            ],
            "javascript": [
                (
                    r"\b(function|const|let|var|if|else|for|while|return|class|"
                    r"import|export|async|await)\b",
                    BOLD,
                ),
                (r"//.*$", DIM + MID_GRAY),
                (r"/\*.*?\*/", DIM + MID_GRAY),
                (r'["\'].*?["\']', GLITCH_GREEN),
                (r"\b\d+\b", ELECTRIC_CYAN),
            ],
        }

    # ------------------------------------------------------------------
    # INTERNAL HELPERS (STATE + CALLBACKS)
    # ------------------------------------------------------------------

    def _normalize_newlines(self, text: str) -> str:
        """Normalize all newline variants to '\n'."""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _set_modified(self, value: bool) -> None:
        """
        Internal helper to update is_modified and notify listeners only
        when the value actually changes.
        """
        if self.is_modified != value:
            self.is_modified = value
            logger.debug(f"EditorPanel modified state -> {value}")
            if self._on_modified_callback:
                try:
                    self._on_modified_callback(value)
                except Exception as cb_err:
                    logger.warning(f"on_modified_callback failed: {cb_err}")

    def _notify_change(self) -> None:
        """
        Notify owner (e.g., RightPanel) that the buffer content changed.
        This allows the UI to re-render the editor panel on next frame.
        """
        if self._on_change_callback:
            try:
                self._on_change_callback()
            except Exception as cb_err:
                logger.warning(f"on_change_callback failed: {cb_err}")

    # ------------------------------------------------------------------
    # LOAD & SAVE
    # ------------------------------------------------------------------

    def load_file(self, file_path: Path) -> bool:
        """
        Load file content into editor's memory.

        Behavior:
        - File exists and is a regular file  -> load content, modified=False
        - File does not exist                -> treat as new empty file, modified=False
        - Any error                          -> show error line, modified=False
        """
        try:
            self.file_path = file_path.resolve()

            if not self.file_path.exists():
                # New file case: start with a single empty line.
                self.content = [""]
                self.cursor_line = 0
                self.view_bottom_line = 1
                self._set_modified(False)
                logger.info(f"EditorPanel new file (not yet on disk): {self.file_path}")
                self._notify_change()
                return True

            if not self.file_path.is_file():
                # Not a regular file (e.g., folder) - silently skip, don't show error
                logger.debug(f"EditorPanel: Skipping non-file path: {self.file_path}")
                self.file_path = None
                self.content = []
                self.cursor_line = 0
                self.view_bottom_line = None
                self._set_modified(False)
                # Don't notify change - just silently fail
                return False

            # Read text and normalize newlines
            raw = self.file_path.read_text(encoding="utf-8", errors="ignore")
            raw = self._normalize_newlines(raw)
            self.content = raw.split("\n")
            self.cursor_line = 0
            # Anchor viewport to the bottom of the file on load.
            self.view_bottom_line = len(self.content) or 1
            self._set_modified(False)

            logger.info(f"EditorPanel loaded: {self.file_path}")
            self._notify_change()
            return True

        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            self.file_path = None
            self.content = [f"Error loading file: {e}"]
            self.cursor_line = 0
            self.view_bottom_line = 1
            self._set_modified(False)
            self._notify_change()
            return False

    def save_file(self) -> bool:
        """
        Save current in-memory content back to file_path.

        NOTE:
        - If file_path is None, this method returns False.
        """
        if not self.file_path:
            logger.error("Save failed: No file_path is set.")
            return False

        try:
            text = "\n".join(self.content)
            text = self._normalize_newlines(text)
            self.file_path.write_text(text, encoding="utf-8")
            self._set_modified(False)
            logger.info(f"EditorPanel saved: {self.file_path}")
            # Notify that content is stable on disk as well
            self._notify_change()
            return True
        except Exception as e:
            logger.error(f"Error saving file {self.file_path}: {e}")
            return False

    # ------------------------------------------------------------------
    # LANGUAGE & SYNTAX (for color render)
    # ------------------------------------------------------------------

    def get_language(self) -> Optional[str]:
        """Infer language from file extension."""
        if not self.file_path:
            return None

        ext = self.file_path.suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".json": "json",
            ".md": "markdown",
        }
        return lang_map.get(ext)

    def _apply_syntax_highlighting(self, line: str) -> str:
        """Apply simple regex-based syntax highlighting to a single line."""
        language = self.get_language()
        if not language or language not in self.syntax_patterns:
            return line

        for pattern, color in self.syntax_patterns[language]:
            line = re.sub(pattern, lambda m: f"{color}{m.group(0)}{RESET}", line)

        return line

    # ------------------------------------------------------------------
    # RENDERING FOR RIGHT PANEL (PLAIN TEXT)
    # ------------------------------------------------------------------

    def render_as_lines(self) -> List[str]:
        """
        Convenience wrapper for content-only rendering.
        This is what the DualPanelRenderer uses on the right side.
        """
        return self.render_content_lines()

    def render_content_lines(self) -> List[str]:
        """
        Return editor view as plain text with line numbers, NO header/borders.
        Designed to be embedded inside the right panel under a shared frame.
        """
        lines: List[str] = []
        lines.append("")  # Top spacer

        total_lines = len(self.content)
        # Determine which part of the buffer should be visible. We keep
        # the viewport anchored to view_bottom_line, and DualPanelRenderer
        # will further clamp the tail based on terminal height.
        if total_lines == 0:
            visible_content: List[str] = []
        else:
            bottom = self.view_bottom_line if self.view_bottom_line else total_lines
            # Clamp into [1, total_lines]
            bottom = max(1, min(bottom, total_lines))
            visible_content = self.content[:bottom]

        max_lines = len(visible_content)
        line_num_width = len(str(max_lines if max_lines > 0 else 1))

        if max_lines == 0 or (max_lines == 1 and visible_content[0] == ""):
            lines.append(" <empty file>")
        else:
            for i in range(max_lines):
                ln = f"{i + 1:>{line_num_width}}"
                raw = visible_content[i]
                # Truncate to width if necessary (simple safeguard)
                if self.width > 10 and len(raw) > self.width - (line_num_width + 4):
                    raw = raw[: self.width - (line_num_width + 7)] + "..."
                lines.append(f" {ln} │ {raw}")

        # Footer with basic stats
        lines.append("")  # Spacer
        footer = f"Lines: {len(self.content)}"
        try:
            if self.file_path:
                filename = self.file_path.name
                status = " [MODIFIED]" if self.is_modified else ""
                footer += f" | File: {filename}{status}"
            if self.file_path and self.file_path.exists():
                kb = self.file_path.stat().st_size / 1024
                footer += f" | Size: {kb:.2f}KB"
        except (OSError, FileNotFoundError):
            # File might not exist yet; ignore
            pass

        lines.append(f" {footer}")
        return lines

    # ------------------------------------------------------------------
    # COLOR RENDERING (STANDALONE DEBUG)
    # ------------------------------------------------------------------

    def render_color(self) -> str:
        """
        Render the current file with:
        - Header
        - Line numbers
        - ANSI syntax highlighting (best-effort)
        This is more for debugging / standalone usage.
        """
        lines: List[str] = []

        # Header
        if self.file_path:
            filename = self.file_path.name
            status = f" {BOLD}{GLITCH_RED}[MODIFIED]{RESET}" if self.is_modified else ""
            lines.append(f"{BOLD}{NEON_PURPLE}╔═══ EDITOR: {filename}{status}{RESET}")
        else:
            lines.append(f"{BOLD}{NEON_PURPLE}╔═══ EDITOR ═══{RESET}")

        lines.append("")

        # Content
        max_lines = len(self.content)
        line_num_width = len(str(max_lines)) if max_lines > 0 else 1

        if max_lines == 0 or (max_lines == 1 and self.content[0] == ""):
            lines.append(f"{DIM}{MID_GRAY}<empty file>{RESET}")
        else:
            for i in range(max_lines):
                ln = f"{i + 1:>{line_num_width}}"
                ln_col = f"{DIM}{DARK_GRAY}{ln}{RESET}"
                raw = self.content[i]
                highlighted = self._apply_syntax_highlighting(raw)
                lines.append(f"{ln_col} │ {highlighted}")

        # Footer
        lines.append("")
        footer = f"Lines: {len(self.content)}"
        try:
            if self.file_path and self.file_path.exists():
                kb = self.file_path.stat().st_size / 1024
                footer += f" | Size: {kb:.2f}KB"
        except (OSError, FileNotFoundError):
            pass

        lines.append(f"{DIM}{MID_GRAY}{footer}{RESET}")
        lines.append(f"{BOLD}{NEON_PURPLE}{'═' * 50}{RESET}")

        return "\n".join(lines)

    def display(self) -> None:
        """Utility helper to print the colorized version to the real terminal."""
        print(self.render_color())

    # ------------------------------------------------------------------
    # BASIC TEXT OPERATIONS (SINGLE-LINE)
    # ------------------------------------------------------------------

    def insert_line(self, line_num: int, content: str) -> None:
        """
        Insert a line at the given index (0-based).
        If line_num is out of range, the call is ignored.
        """
        if 0 <= line_num <= len(self.content):
            self.content.insert(line_num, content)
            self._set_modified(True)
            self._notify_change()

    def delete_line(self, line_num: int) -> None:
        """
        Delete the line at the given index (0-based).
        If line_num is out of range, the call is ignored.
        """
        if 0 <= line_num < len(self.content):
            del self.content[line_num]
            self._set_modified(True)
            self._notify_change()

    def replace_line(self, line_num: int, content: str) -> None:
        """
        Replace the line at the given index (0-based) with new content.
        If line_num is out of range, the call is ignored.
        """
        if 0 <= line_num < len(self.content):
            self.content[line_num] = content
            self._set_modified(True)
            self._notify_change()

    # ------------------------------------------------------------------
    # ADVANCED TEXT OPERATIONS (MULTI-LINE / RANGE)
    # ------------------------------------------------------------------

    def replace_lines_range(self, start_line: int, end_line: int, new_block: str) -> None:
        """
        Replace a range of lines [start_line, end_line] (1-based inclusive)
        with the given multi-line text block.

        - start_line, end_line are 1-based, as humans usually refer to.
        - If indices are invalid or out of range, the operation is ignored.
        """
        if start_line < 1 or end_line < start_line:
            return

        # Convert to 0-based indices
        start_idx = start_line - 1
        end_idx = end_line  # python slice end is exclusive

        if start_idx >= len(self.content):
            return

        new_block_norm = self._normalize_newlines(new_block)
        new_lines = new_block_norm.split("\n")

        # Clamp end index to content length
        end_idx = min(end_idx, len(self.content))

        self.content[start_idx:end_idx] = new_lines
        self._set_modified(True)
        self._notify_change()

    def insert_block_at_line(self, line_num: int, block: str) -> None:
        """
        Insert a multi-line text block starting at a specific 1-based line.
        Existing lines are pushed down.

        - If line_num is 1, block is inserted at the top.
        - If line_num is len(content)+1, block is appended at the end.
        """
        if line_num < 1:
            return

        idx = line_num - 1
        idx = max(0, min(idx, len(self.content)))

        block_norm = self._normalize_newlines(block)
        new_lines = block_norm.split("\n")

        self.content[idx:idx] = new_lines
        self._set_modified(True)
        self._notify_change()

    def delete_lines_range(self, start_line: int, end_line: int) -> None:
        """
        Delete lines in the range [start_line, end_line] (1-based inclusive).
        If the range is invalid or out of bounds, nothing happens.
        """
        if start_line < 1 or end_line < start_line:
            return

        start_idx = start_line - 1
        end_idx = end_line  # exclusive

        if start_idx >= len(self.content):
            return

        end_idx = min(end_idx, len(self.content))
        del self.content[start_idx:end_idx]

        self._set_modified(True)
        self._notify_change()

    # ------------------------------------------------------------------
    # VIEWPORT / SCROLLING
    # ------------------------------------------------------------------

    def scroll_to_bottom(self) -> None:
        """Anchor the viewport to the end of the buffer."""
        total = len(self.content)
        self.view_bottom_line = total if total > 0 else 1
        self._notify_change()

    def scroll_up(self, lines: int = 1) -> None:
        """
        Scroll the viewport up by the given number of lines.
        Does not move the underlying content; only the visible window.
        """
        if not self.content:
            return
        step = max(1, int(lines))
        total = len(self.content)
        bottom = self.view_bottom_line if self.view_bottom_line else total
        bottom = max(1, bottom - step)
        if bottom != self.view_bottom_line:
            self.view_bottom_line = bottom
            self._notify_change()

    def scroll_down(self, lines: int = 1) -> None:
        """
        Scroll the viewport down by the given number of lines.
        """
        if not self.content:
            return
        step = max(1, int(lines))
        total = len(self.content)
        bottom = self.view_bottom_line if self.view_bottom_line else total
        bottom = min(total, bottom + step)
        if bottom != self.view_bottom_line:
            self.view_bottom_line = bottom
            self._notify_change()

    def page_up(self, approx_lines: int = 20) -> None:
        """Convenience helper for page-up style scrolling."""
        self.scroll_up(lines=approx_lines)

    def page_down(self, approx_lines: int = 20) -> None:
        """Convenience helper for page-down style scrolling."""
        self.scroll_down(lines=approx_lines)

    # ------------------------------------------------------------------
    # FIND / REPLACE
    # ------------------------------------------------------------------

    def find(self, query: str) -> List[int]:
        """
        Return a list of 0-based line indices where query appears.
        Simple substring search, case-sensitive.
        """
        return [i for i, line in enumerate(self.content) if query in line]

    def replace_all(self, old: str, new: str) -> int:
        """
        Replace all occurrences of 'old' with 'new' across the entire buffer.
        Returns the total number of replacements performed.
        """
        if not old:
            return 0

        count = 0
        for i in range(len(self.content)):
            line = self.content[i]
            if old in line:
                replacements = line.count(old)
                if replacements > 0:
                    self.content[i] = line.replace(old, new)
                    count += replacements

        if count > 0:
            self._set_modified(True)
            self._notify_change()

        return count

    # ------------------------------------------------------------------
    # STATS + TEXT HELPERS (FOR AI)
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """
        Return basic statistics about the current buffer.
        Useful for AI tools or debugging.
        """
        total_lines = len(self.content)
        total_chars = sum(len(line) for line in self.content)
        non_empty = sum(1 for line in self.content if line.strip())

        return {
            "total_lines": total_lines,
            "total_chars": total_chars,
            "non_empty_lines": non_empty,
            "is_modified": self.is_modified,
            "file_path": str(self.file_path) if self.file_path else None,
        }

    def get_text(self) -> str:
        """
        Return the entire buffer as a single string, joined by '\n'.
        """
        return "\n".join(self.content)

    def set_text(self, text: str) -> None:
        """
        Replace the entire buffer with new text.
        Newlines are normalized first.
        """
        text = self._normalize_newlines(text)
        self.content = text.split("\n")
        self.cursor_line = 0
        self._set_modified(True)
        self._notify_change()

    # ------------------------------------------------------------------
    # LIVE EDIT API (FOR AI LIVE EDITOR MODE)
    # ------------------------------------------------------------------

    def apply_line_edit(self, start_line: int, end_line: int, new_lines: List[str]) -> None:
        """
        Replace lines [start_line, end_line] (1-based inclusive) with new_lines.
        
        This is the core live edit method used by AI Live Editor Mode.
        Triggers on_change and modified callbacks automatically.
        
        Args:
            start_line: 1-based starting line number
            end_line: 1-based ending line number (inclusive)
            new_lines: List of new line strings to replace the range
        """
        if start_line < 1 or end_line < start_line:
            logger.warning(f"Invalid line range: {start_line}-{end_line}")
            return

        # Convert to 0-based indices
        start_idx = start_line - 1
        end_idx = end_line  # python slice end is exclusive

        if start_idx >= len(self.content):
            logger.warning(f"Start line {start_line} out of range (max: {len(self.content)})")
            return

        # Clamp end index to content length
        end_idx = min(end_idx, len(self.content))

        # Replace the range
        self.content[start_idx:end_idx] = new_lines
        self._set_modified(True)
        self._notify_change()

        logger.debug(f"Live edit: replaced lines {start_line}-{end_line} with {len(new_lines)} new lines")

    def delete_range(self, start_line: int, end_line: int) -> None:
        """
        Delete lines [start_line, end_line] (1-based inclusive).
        
        Wrapper around existing delete_lines_range with explicit callbacks.
        Used by AI Live Editor Mode for line deletions.
        
        Args:
            start_line: 1-based starting line number
            end_line: 1-based ending line number (inclusive)
        """
        if start_line < 1 or end_line < start_line:
            logger.warning(f"Invalid delete range: {start_line}-{end_line}")
            return

        self.delete_lines_range(start_line, end_line)
        logger.debug(f"Live edit: deleted lines {start_line}-{end_line}")

    def insert_after(self, line_number: int, new_lines: List[str]) -> None:
        """
        Insert new_lines after line_number (1-based).
        
        Used by AI Live Editor Mode for inserting code after a specific line.
        Triggers callbacks automatically.
        
        Args:
            line_number: 1-based line number to insert after
            new_lines: List of new line strings to insert
        """
        if line_number < 0:
            logger.warning(f"Invalid line number: {line_number}")
            return

        # Insert after line_number means insert at position line_number + 1
        insert_idx = line_number  # 0-based index for insertion
        insert_idx = max(0, min(insert_idx, len(self.content)))

        self.content[insert_idx:insert_idx] = new_lines
        self._set_modified(True)
        self._notify_change()

        logger.debug(f"Live edit: inserted {len(new_lines)} lines after line {line_number}")

    def replace_range(self, start_line: int, end_line: int, new_text: str) -> None:
        """
        Convenience wrapper: replace range with multi-line text block.
        
        Splits new_text into lines and calls apply_line_edit.
        Used by AI Live Editor Mode when the AI provides a text block.
        
        Args:
            start_line: 1-based starting line number
            end_line: 1-based ending line number (inclusive)
            new_text: Multi-line text string (will be split on newlines)
        """
        new_text_norm = self._normalize_newlines(new_text)
        new_lines = new_text_norm.split("\n")
        self.apply_line_edit(start_line, end_line, new_lines)
        logger.debug(f"Live edit: replaced range {start_line}-{end_line} with text block")

    # ------------------------------------------------------------------
    # STREAMING API (FOR LIVE TYPING DURING AI GENERATION)
    # ------------------------------------------------------------------

    def write_stream(self, text: str) -> None:
        """
        Stream text into the editor during AI generation (live typing effect).
        
        This method accumulates text tokens and updates the editor buffer
        incrementally, providing visual feedback as the AI generates content.
        
        Args:
            text: Text chunk to append to the current streaming buffer
        """
        if not hasattr(self, '_stream_buffer'):
            self._stream_buffer = ""
            self._stream_start_line = len(self.content) + 1 if self.content else 1
        
        # Accumulate text
        self._stream_buffer += text
        
        # Parse accumulated text into lines
        buffer_norm = self._normalize_newlines(self._stream_buffer)
        lines = buffer_norm.split("\n")
        
        # If we have complete lines (ending with newline), update the editor
        if buffer_norm.endswith("\n") or "\n" in self._stream_buffer:
            # Get the last complete line
            complete_lines = lines[:-1] if not buffer_norm.endswith("\n") else lines
            
            if complete_lines:
                # Replace or append at the streaming position
                if self._stream_start_line <= len(self.content):
                    # Replace existing content
                    end_line = min(self._stream_start_line + len(complete_lines) - 1, len(self.content))
                    self.apply_line_edit(self._stream_start_line, end_line, complete_lines)
                else:
                    # Append new content
                    for line in complete_lines:
                        self.content.append(line)
                        self._set_modified(True)
                    self._notify_change()
                
                # Update streaming position
                self._stream_start_line += len(complete_lines)
                
                # Keep only the incomplete last line in buffer
                self._stream_buffer = lines[-1] if lines else ""
        
        # Always notify change for visual updates
        self._notify_change()
    
    def finish_stream(self) -> None:
        """
        Finalize streaming: flush any remaining buffer content.
        Call this when AI generation is complete.
        """
        if hasattr(self, '_stream_buffer') and self._stream_buffer:
            # Append final buffer content
            if self._stream_start_line <= len(self.content):
                # Replace at current position
                self.replace_line(self._stream_start_line - 1, self._stream_buffer)
            else:
                # Append new line
                self.content.append(self._stream_buffer)
                self._set_modified(True)
            self._notify_change()
        
        # Clear streaming state
        if hasattr(self, '_stream_buffer'):
            delattr(self, '_stream_buffer')
        if hasattr(self, '_stream_start_line'):
            delattr(self, '_stream_start_line')
