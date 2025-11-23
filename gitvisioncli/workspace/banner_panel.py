# gitvisioncli/workspace/banner_panel.py
"""
Banner Panel — Display ASCII logo, commands, and help.
Fully responsive with dynamic ASCII art scaling.
"""

import logging
import re
from typing import List
from gitvisioncli.ui.colors import *
from gitvisioncli.ui.glitch_effects import multi_flicker

logger = logging.getLogger(__name__)

# Professional ASCII art that scales based on width
def get_logo_for_width(width: int) -> List[str]:
    """Return ASCII logo scaled to available width."""
    
    # Full logo for wide panels (80+ chars)
    if width >= 80:
        return [
            "   ██████╗ ██╗████████╗██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗",
            "  ██╔════╝ ██║╚══██╔══╝██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║",
            "  ██║  ███╗██║   ██║   ██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║",
            "  ██║   ██║██║   ██║   ╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║",
            "  ╚██████╔╝██║   ██║    ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║",
            "   ╚═════╝ ╚═╝   ╚═╝     ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
            "",
        ]
    
    # Medium logo for medium panels (55-79 chars)
    elif width >= 55:
        return [
            "   ██████╗ ██╗████████╗",
            "  ██╔════╝ ██║╚══██╔══╝",
            "  ██║  ███╗██║   ██║   ",
            "  ██║   ██║██║   ██║   ",
            "  ╚██████╔╝██║   ██║   ",
            "   ╚═════╝ ╚═╝   ╚═╝   ",
            "",
            "  ██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗",
            "  ██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║",
            "  ██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║",
            "  ╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║",
            "   ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║",
            "    ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
            "",
            "   🚀 AI-POWERED WORKSPACE 🚀",
        ]
    
    # Compact logo for narrow panels (35-54 chars)
    elif width >= 35:
        return [
            "  ╔═══════════════════════════════╗",
            "  ║                               ║",
            "  ║      ██████╗ ██╗████████╗     ║",
            "  ║     ██╔════╝ ██║╚══██╔══╝     ║",
            "  ║     ██║  ███╗██║   ██║        ║",
            "  ║     ██║   ██║██║   ██║        ║",
            "  ║     ╚██████╔╝██║   ██║        ║",
            "  ║      ╚═════╝ ╚═╝   ╚═╝        ║",
            "  ║                               ║",
            "  ║          VISION CLI           ║",
            "  ║       AI WORKSPACE            ║",
            "  ║                               ║",
            "  ╚═══════════════════════════════╝",
        ]
    
    # Minimal for very narrow
    else:
        return [
            "  ╔═══════════════════╗",
            "  ║                   ║",
            "  ║    GITVISION      ║",
            "  ║    WORKSPACE      ║",
            "  ║                   ║",
            "  ╚═══════════════════╝",
        ]


# Compact command list - ONLY the most critical commands
# Keep this SHORT so the logo is always visible!
ESSENTIAL_COMMANDS = [
    ("📁 Quick Start", [
        (":tree", "Browse files"),
        (":edit <file>", "Edit file"),
        (":sheet", "Full command list"),
        (":models", "Manage AI engines"),
    ]),
    ("🤖 AI", [
        ("create/edit <file>", "AI file operations"),
        ("analyze / explain", "AI code help"),
        (":set-ai <model>", "Switch AI model"),
    ]),
    ("⚙ System", [
        ("cd <path> / pwd", "Navigation"),
        ("clear / stats", "Workspace control"),
        ("exit / quit", "Exit GitVision"),
    ]),
]


class BannerPanel:
    """
    Display banner with logo, commands, and help information.
    Fully responsive for dual-panel rendering.
    """
    
    def __init__(self, width: int = 80):
        self.width = width
    
    def _strip_ansi(self, text: str) -> str:
        """Strip ANSI codes from text for length calculation."""
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_pattern.sub('', text)
    
    def _fit_line(self, text: str, width: int) -> str:
        """
        Fit a plain text line to exact width with padding or truncation.

        IMPORTANT: Do not truncate lines that contain box-drawing characters,
        so borders like ╔═══╗ never lose their edge glyphs.
        """
        border_chars = "╔╗╚╝╠╣╦╩╤╧╪║│"
        if any(ch in text for ch in border_chars):
            # Never truncate border lines; allow them to overflow slightly
            # rather than clipping frame characters.
            text_len = len(text)
            if text_len < width:
                return text + (" " * (width - text_len))
            return text

        text_len = len(text)
        if text_len == width:
            return text
        if text_len < width:
            return text + (" " * (width - text_len))

        # Truncate with ellipsis
        if width <= 1:
            return text[0] if width == 1 else ""
        return text[:width - 1] + "…"
    
    def render_as_lines(self) -> List[str]:
        """
        Render banner as plain text lines for dual-panel display (content only).
        Includes ASCII logo and FULL COMMAND LIST.
        """
        lines: List[str] = []
        
        # Add some top spacing
        lines.append("")
        lines.append("")
        
        # Get appropriately sized logo and apply neon flicker/glitch styling
        logo_lines_raw = get_logo_for_width(self.width)
        logo_lines = multi_flicker(logo_lines_raw, color=NEON_PURPLE)
        
        # Center the logo (ANSI-aware)
        for logo_line in logo_lines:
            logo_len = len(self._strip_ansi(logo_line))
            if logo_len < self.width:
                left_pad = (self.width - logo_len) // 2
                centered = (" " * left_pad) + logo_line
                lines.append(self._fit_line(centered, self.width))
            else:
                lines.append(self._fit_line(logo_line, self.width))
        
        lines.append("")
        lines.append("")

        # Ultra-vibrant workspace title with gradient effect
        title = f"{BOLD}{ELECTRIC_CYAN}⚡{RESET}{BOLD}{NEON_PURPLE} GITVISION WORKSPACE {RESET}{BOLD}{ELECTRIC_CYAN}⚡{RESET}"
        title_len = len(self._strip_ansi(title))
        if title_len < self.width:
            t_pad = (self.width - title_len) // 2
            lines.append(self._fit_line((" " * t_pad) + title, self.width))
        else:
            lines.append(self._fit_line(title, self.width))

        lines.append("")

        # Separator (dim scanline-style)
        sep_core = "─" * min(self.width - 4, 60)
        sep_line = f"{DIM}{DARK_GRAY}{sep_core}{RESET}"
        left_pad = (self.width - len(self._strip_ansi(sep_line))) // 2
        lines.append((" " * left_pad) + sep_line)
        lines.append("")
        
        # Commands sections with ULTRA-ENHANCED visual design
        for section_name, commands in ESSENTIAL_COMMANDS:
            # Ultra-vibrant section header with gradient effect
            header_text = f"{BOLD}{ELECTRIC_CYAN}╔═══ {section_name} ═══╗{RESET}"
            header_len = len(self._strip_ansi(header_text))
            left_pad = (self.width - header_len) // 2
            lines.append((" " * left_pad) + header_text)
            # Add decorative underline
            underline = f"{BOLD}{BRIGHT_MAGENTA}{'═' * (len(self._strip_ansi(header_text)) - 2)}{RESET}"
            lines.append((" " * (left_pad + 1)) + underline)
            lines.append("")
            
            # Commands with ULTRA-ENHANCED formatting and visual hierarchy
            for cmd, desc in commands:
                # Ultra-vibrant formatting with glow effects
                cmd_col = f"{BOLD}{ELECTRIC_CYAN}▶{RESET} {BOLD}{BRIGHT_MAGENTA}{cmd}{RESET}"
                desc_col = f"{MID_GRAY}{desc}{RESET}"

                if self.width >= 60:
                    # CRITICAL FIX: Use ANSI-aware padding to avoid counting escape codes
                    # Calculate visible width and pad accordingly
                    cmd_visible = len(self._strip_ansi(cmd_col))
                    padding_needed = max(0, 24 - cmd_visible)
                    line = f"    {cmd_col}{' ' * padding_needed} {desc_col}"
                elif self.width >= 45:
                    # CRITICAL FIX: Use ANSI-aware padding
                    cmd_visible = len(self._strip_ansi(cmd_col))
                    padding_needed = max(0, 22 - cmd_visible)
                    line = f"  {cmd_col}{' ' * padding_needed} {desc_col}"
                else:
                    # Stack vertically for narrow panels with better indentation
                    lines.append(f"  {cmd_col}")
                    lines.append(f"      {DIM}{DARK_GRAY}└─{RESET} {desc_col}")
                    continue
                
                lines.append(self._fit_line(line, self.width))
            
            lines.append("")
        
        # Enhanced footer with better visual design
        lines.append("")
        footer_sep = f"{DIM}{DARK_GRAY}{'─' * min(self.width - 4, 50)}{RESET}"
        footer_sep_len = len(self._strip_ansi(footer_sep))
        left_pad_sep = (self.width - footer_sep_len) // 2
        lines.append((" " * left_pad_sep) + footer_sep)
        lines.append("")
        
        footer = f"{BOLD}{ELECTRIC_CYAN}💬{RESET} {BOLD}{BRIGHT_MAGENTA}Ask AI anything in natural language!{RESET}"
        footer_len = len(self._strip_ansi(footer))
        left_pad = (self.width - footer_len) // 2
        lines.append((" " * left_pad) + footer)
        lines.append("")
        lines.append("")
        
        return lines
    
    def render_compact(self) -> str:
        """
        Render a compact version as a string (for legacy compatibility).
        Returns plain text with newlines.
        """
        lines = []
        
        # Compact header
        lines.append("╔═══════════════════════════════════════╗")
        lines.append("║        GITVISION WORKSPACE            ║")
        lines.append("╚═══════════════════════════════════════╝")
        lines.append("")
        
        # Quick commands
        lines.append("⚡ Quick Commands")
        lines.append("")
        
        quick_cmds = [
            (":tree", "Show file tree"),
            (":edit <file>", "Edit file"),
            (":markdown <file>", "Preview markdown"),
            (":banner", "Full help")
        ]
        
        for cmd, desc in quick_cmds:
            lines.append(f"  {cmd:<20} {desc}")
        
        lines.append("")
        footer = f"{BOLD}{DEEP_CYAN}💬 Ask AI anything in natural language{RESET}"
        lines.append(footer)
        lines.append("")
        
        return "\n".join(lines)
    
    def render(self) -> str:
        """
        Render full banner with ANSI colors for standalone display.
        This is used when banner is displayed outside the dual-panel.
        """
        lines = []
        
        # Logo with colors
        logo_lines = get_logo_for_width(self.width)
        for line in logo_lines:
            colored = f"{BOLD}{NEON_PURPLE}{line}{RESET}"
            lines.append(colored)
        
        lines.append("")
        lines.append("")
        
        # Commands sections
        for section_name, commands in ESSENTIAL_COMMANDS:
            # Section header with colors
            header = f"{section_name}"
            colored_header = f"{BOLD}{ELECTRIC_CYAN}{header}{RESET}"
            lines.append(colored_header)
            lines.append("")
            
            # Commands with colors
            for cmd, desc in commands:
                cmd_colored = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
                desc_colored = f"{DIM}{MID_GRAY}{desc}{RESET}"
                command_line = f"  {cmd_colored} {desc_colored}"
                lines.append(command_line)
            
            lines.append("")
        
        # Footer with colors
        footer = f"{BOLD}{DEEP_CYAN}💬 Ask AI anything in natural language{RESET}"
        lines.append(footer)
        lines.append("")
        
        return "\n".join(lines) + "\n"
    
