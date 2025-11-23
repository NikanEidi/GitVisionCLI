# gitvisioncli/ui/dual_panel.py
"""
Dual Panel Renderer — Split-screen IDE layout with integrated input terminal.
Fully responsive. Automatically clears terminal each frame to prevent stretching.
Left and right panels are always vertically synchronized.
"""

import re
import logging
import shutil
from typing import List, Optional
from dataclasses import dataclass

from gitvisioncli.ui.colors import (
    RESET, BOLD, DIM,
    NEON_PURPLE, BRIGHT_MAGENTA, ELECTRIC_CYAN,
    DARK_GRAY, MID_GRAY
)
from gitvisioncli.ui.banner import get_terminal_width
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gitvisioncli.workspace.right_panel import RightPanel

logger = logging.getLogger(__name__)

# ========================================================================
# ANSI HELPERS
# ========================================================================

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI sequences."""
    return ANSI_RE.sub("", text)


def visible_len(text: str) -> int:
    """Length ignoring ANSI codes."""
    return len(strip_ansi(text))


def clear_screen() -> str:
    """
    Full screen clear.
    
    Uses ANSI escape sequence to clear the entire screen and move cursor home.
    This prevents duplicate panels from stacking up.
    """
    return "\x1b[2J\x1b[H"


# ========================================================================
# CONFIG
# ========================================================================

@dataclass
class DualPanelConfig:
    total_width: int = 140
    left_ratio: float = 0.48
    min_left: int = 40
    min_right: int = 40
    # gutter is kept for future use, but real width math
    # is based on left + 1 + right (middle separator) + 2 borders
    gutter: int = 1
    # total height of the bottom block (separator + input + bottom border)
    input_height: int = 3


# ========================================================================
# MAIN RENDERER
# ========================================================================

class DualPanelRenderer:
    """
    Renders:
    - Header (3 lines)
    - Left panel (chat) | Right panel (workspace)
    - Input bar
    Automatically clamps height to terminal height.
    """

    def __init__(self, right_panel: "RightPanel", config: Optional[DualPanelConfig] = None):
        self.right_panel = right_panel
        self.config = config or DualPanelConfig()
        self.left_width = 0
        self.right_width = 0
        self._calculate_widths()
        self.right_panel.width = self.right_width
        if hasattr(self.right_panel, "tree_panel"):
            self.right_panel.tree_panel.width = self.right_width

    # --------------------------------------------------------------------
    # WIDTH CALC
    # --------------------------------------------------------------------
    def _calculate_widths(self):
        """Recalculate panel widths based on current terminal width."""
        self.config.total_width = get_terminal_width()
        border_width = 3  # outer left + middle + outer right chars

        # Sum of left_width + right_width (without middle separator)
        inner = self.config.total_width - border_width

        if inner < (self.config.min_left + self.config.min_right):
            self.left_width = max(self.config.min_left, inner // 2)
            self.right_width = inner - self.left_width
        else:
            ideal = int(inner * self.config.left_ratio)
            ideal = max(ideal, self.config.min_left)
            ideal = min(ideal, inner - self.config.min_right)
            self.left_width = ideal
            self.right_width = inner - ideal

        self.right_panel.width = self.right_width
        if hasattr(self.right_panel, "tree_panel"):
            self.right_panel.tree_panel.width = self.right_width

    # --------------------------------------------------------------------
    # PUBLIC RENDER
    # --------------------------------------------------------------------
    def render(self, left_content_str: str, input_text: str = "", status_line: str = "") -> str:
        """
        Full render pipeline.
        The input_text argument is the *current* raw input buffer, which
        will be wrapped into a multi-line input box at the bottom of the
        frame. The overall frame height adjusts dynamically so borders
        remain perfectly aligned.
        """
        self._calculate_widths()

        # Right panel content
        try:
            right_lines = self.right_panel.render_as_lines()
        except Exception as e:
            logger.error(f"RightPanel render failed: {e}", exc_info=True)
            right_lines = [f"PANEL ERROR: {e}"]

        # Prepare left lines
        left_lines = left_content_str.splitlines()

        # Build the combined frame with height limits and optional status row
        return self._render_frame(left_lines, right_lines, input_text, status_line)

    # --------------------------------------------------------------------
    # FRAME BUILDER
    # --------------------------------------------------------------------
    def _render_frame(
        self,
        left_lines: List[str],
        right_lines: List[str],
        input_text: str,
        status_line: str,
    ) -> str:
        """Combine header, panels, and footer into a single screen."""

        # Terminal height (fallback 120x40 if unknown)
        terminal_size = shutil.get_terminal_size((120, 40))
        terminal_height = terminal_size.lines

        # Bottom block height (separator + N input lines + bottom border)
        input_lines = self._build_input_lines(input_text)
        bottom_height = 1 + max(1, len(input_lines)) + 1

        # header (3) + dynamic bottom block
        reserved_height = 3 + bottom_height
        available_height = max(5, terminal_height - reserved_height)

        # Clamp content panels to visible height (TAIL behaviour)
        left_lines = left_lines[-available_height:]
        right_lines = right_lines[-available_height:]

        # Align heights
        max_rows = max(len(left_lines), len(right_lines))
        left_lines += [""] * (max_rows - len(left_lines))
        right_lines += [""] * (max_rows - len(right_lines))

        out = []

        # Header
        out += self._top_header()

        # Content rows
        for L, R in zip(left_lines, right_lines):
            out.append(self._content_row(L, R))

        # Optional status bar just above the input block
        if status_line:
            out.append(self._status_row(status_line))

        # Footer (input block + bottom border)
        out.append(self._input_separator())
        out.extend(input_lines)
        out.append(self._bottom_border())

        return "\n".join(out)

    # --------------------------------------------------------------------
    # HEADER ROWS
    # --------------------------------------------------------------------
    def _hborder(self, left_ch: str, mid_ch: str, right_ch: str) -> str:
        """
        Enhanced horizontal border builder with gradient effect.

        Uses vibrant neon colors with glow effect for ultra-modern look.
        """
        left_bar = "═" * self.left_width
        right_bar = "═" * self.right_width

        # Enhanced border with gradient effect - ultra-vibrant NEON_PURPLE theme
        return (
            f"{BOLD}{NEON_PURPLE}{left_ch}{RESET}"
            f"{BOLD}{NEON_PURPLE}{left_bar}{RESET}"
            f"{BOLD}{BRIGHT_MAGENTA}{mid_ch}{RESET}"
            f"{BOLD}{NEON_PURPLE}{right_bar}{RESET}"
            f"{BOLD}{NEON_PURPLE}{right_ch}{RESET}"
        )

    def _vframe_row(self, left_text: str, right_text: str, middle_char: str = "│") -> str:
        """
        Enhanced vertical frame row with vibrant borders.

        - Ultra-bright borders with glow effect
        - Middle separator uses gradient colors
        """
        return (
            f"{BOLD}{NEON_PURPLE}║{RESET}"
            f"{left_text}"
            f"{BOLD}{BRIGHT_MAGENTA}{middle_char}{RESET}"
            f"{right_text}"
            f"{BOLD}{NEON_PURPLE}║{RESET}"
        )

    def _top_header(self) -> List[str]:
        """Render the 3-line top header."""
        # Line 1
        top = self._hborder("╔", "╤", "╗") + RESET

        # Line 2 titles - ENHANCED with ultra-vibrant colors and glow
        left_title = self._fit_line_with_ansi(f"{BOLD}{ELECTRIC_CYAN}✨ AI CONSOLE ✨{RESET}", self.left_width)
        right_title_txt = f"{BOLD}{BRIGHT_MAGENTA}⚡{RESET}{BOLD}{NEON_PURPLE} GITVISION WORKSPACE {RESET}{BOLD}{BRIGHT_MAGENTA}⚡{RESET}"
        right_title = self._center_text_with_ansi(right_title_txt, self.right_width)

        titles = (
            f"{BOLD}{NEON_PURPLE}║{RESET}"
            f"{left_title}"
            f"{BOLD}{BRIGHT_MAGENTA}║{RESET}"
            f"{right_title}"
            f"{BOLD}{NEON_PURPLE}║{RESET}"
        )

        # Line 3: Mode bar
        mode = self.right_panel.get_current_mode_name()
        mode_col = f"{BOLD}{BRIGHT_MAGENTA}{mode}{RESET}"
        mode_bar = self._mode_separator(mode_col, self.right_width)

        sep = (
            f"{BOLD}{NEON_PURPLE}╠"
            f"{BOLD}{NEON_PURPLE}{'═' * self.left_width}"
            f"{BOLD}{BRIGHT_MAGENTA}╪{RESET}"
            f"{mode_bar}"
            f"{BOLD}{NEON_PURPLE}╣{RESET}"
        )

        return [top, titles, sep]

    def _mode_separator(self, text: str, width: int) -> str:
        """Enhanced mode separator with gradient effect."""
        tlen = visible_len(text)
        if tlen >= width:
            return self._fit_line_with_ansi(text, width)

        pad = width - tlen
        L = pad // 2
        R = pad - L

        # Gradient effect: purple -> magenta -> purple
        return f"{BOLD}{NEON_PURPLE}{'═' * L}{RESET}{text}{BOLD}{NEON_PURPLE}{'═' * R}{RESET}"

    # --------------------------------------------------------------------
    # FOOTER (INPUT)
    # --------------------------------------------------------------------
    def _input_separator(self) -> str:
        """Horizontal separator above the input box."""
        return self._hborder("╠", "╧", "╣") + RESET

    def _build_input_lines(self, text: str) -> List[str]:
        """
        Build one or more input rows for the bottom input box.

        - Wraps the raw text across multiple lines.
        - Keeps a single neon frame around the entire block.
        - Ensures no horizontal overflow by hard-wrapping.
        """
        full_width = self.left_width + 1 + self.right_width

        label = f"{BOLD}{ELECTRIC_CYAN}▶{RESET}{BOLD}{BRIGHT_MAGENTA} INPUT{RESET}"
        # Visible width for the first line text after " <label> "
        label_prefix = f" {label} "
        label_prefix_vis = visible_len(label_prefix)

        # Max visible text width for wrapped lines
        first_line_width = max(1, full_width - label_prefix_vis)
        subsequent_width = first_line_width

        # Raw text is user input (no ANSI)
        raw = text or ""

        # Simple whitespace-preserving wrap
        import textwrap

        wrapped: List[str] = (
            textwrap.wrap(raw, width=first_line_width, break_long_words=False, break_on_hyphens=False)
            if raw
            else [""]
        )

        lines: List[str] = []
        for idx, chunk in enumerate(wrapped):
            if idx == 0:
                inner = f"{label_prefix}{chunk}"
            else:
                # Align continuation lines under the text start column
                inner = " " * label_prefix_vis + chunk

            padded = self._fit_line_with_ansi(inner, full_width)
            lines.append(f"{BOLD}{NEON_PURPLE}║{RESET}{padded}{BOLD}{NEON_PURPLE}║{RESET}")

        return lines

    def _bottom_border(self) -> str:
        # same inside width as input row
        # Use the unified horizontal border builder so styling matches
        # the top header and input separator.
        full = self.left_width + 1 + self.right_width
        line = (
            f"{BOLD}{NEON_PURPLE}╚"
            f"{BOLD}{NEON_PURPLE}{'═' * full}"
            f"{BOLD}{NEON_PURPLE}╝"
        )
        return line + RESET

    def _status_row(self, text: str) -> str:
        """
        Single-line status bar spanning both panels.

        The caller provides a preformatted ANSI-aware string; we clamp it
        to the full inner width so that it never overflows the frame.
        """
        inner_width = self.left_width + 1 + self.right_width
        fitted = self._fit_line_with_ansi(text, inner_width)
        return f"{BOLD}{NEON_PURPLE}║{RESET}{fitted}{BOLD}{NEON_PURPLE}║{RESET}"

    # --------------------------------------------------------------------
    # CONTENT ROWS
    # --------------------------------------------------------------------
    def _content_row(self, ltxt: str, rtxt: str) -> str:
        # Both sides may contain ANSI colors; use ANSI-aware fitting.
        L = self._fit_line_with_ansi(ltxt, self.left_width)
        R = self._fit_line_with_ansi(rtxt, self.right_width)
        return self._vframe_row(L, R, middle_char="│")

    # --------------------------------------------------------------------
    # TEXT FITTING HELPERS
    # --------------------------------------------------------------------
    def _fit_line(self, txt: str, width: int) -> str:
        """Exact-width fit for plain (non-ANSI) text."""
        if txt is None:
            txt = ""
        if len(txt) < width:
            return txt + " " * (width - len(txt))
        if len(txt) == width:
            return txt
        if width <= 1:
            return txt[:1]
        return txt[:width - 1] + "…"

    def _fit_line_with_ansi(self, txt: str, width: int) -> str:
        """Exact-width fit for text containing ANSI sequences."""
        if not txt:
            return " " * width

        vis = visible_len(txt)
        if vis == width:
            return txt
        if vis < width:
            return txt + " " * (width - vis)

        # ANSI-aware truncation
        out = []
        vis_count = 0
        in_ansi = False
        max_vis = width - 1

        i = 0
        while i < len(txt) and vis_count < max_vis:
            ch = txt[i]
            if ch == "\x1b" and i + 1 < len(txt) and txt[i + 1] == "[":
                in_ansi = True
                out.append(ch)
            elif in_ansi:
                out.append(ch)
                if ch == "m":
                    in_ansi = False
            else:
                out.append(ch)
                vis_count += 1
            i += 1

        result = "".join(out) + "…"
        pad = width - visible_len(result)
        if pad > 0:
            result += " " * pad
        return result

    def _center_text_with_ansi(self, txt: str, width: int) -> str:
        vis = visible_len(txt)
        if vis >= width:
            return self._fit_line_with_ansi(txt, width)

        pad = width - vis
        L = pad // 2
        R = pad - L
        return (" " * L) + txt + (" " * R)
