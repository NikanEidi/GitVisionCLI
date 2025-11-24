"""
Tree Panel — Recursive project directory tree viewer
"""

import logging
from pathlib import Path
from typing import List, Optional, Set
from gitvisioncli.ui.colors import (
    BOLD,
    RESET,
    DIM,
    MID_GRAY,
    WHITE,
    NEON_PURPLE,
    BRIGHT_MAGENTA,
    ELECTRIC_CYAN,
    GLITCH_GREEN,
    DEEP_CYAN,
)
import re

logger = logging.getLogger(__name__)

from gitvisioncli.ui.components.panel_component import PanelComponent, ComponentConfig

class TreePanel(PanelComponent):
    """
    Display colorized directory tree of the project.
    
    Refactored to use PanelComponent base class for modular architecture.
    """
    
    def __init__(self, base_dir: str, max_depth: int = 7, width: int = 80):
        # Initialize with ComponentConfig
        config = ComponentConfig(width=width, height=24, enabled=True, visible=True)
        super().__init__(config)
        
        self.base_dir = Path(base_dir).resolve()
        self.max_depth = max_depth
        self.width = width
        
        self.ignore_dirs: Set[str] = {
            '.git', '__pycache__', 'node_modules', '.gitvision_backup',
            '.venv', 'venv', '.egg-info', 'dist', 'build', '.pytest_cache'
        }
        
        self.ignore_exts: Set[str] = {
            '.pyc', '.pyo', '.log', '.tmp', '.swo', '.swp', '.DS_Store'
        }
        
        self.extension_colors = {
            '.py': BRIGHT_MAGENTA,
            '.js': ELECTRIC_CYAN,
            '.json': GLITCH_GREEN,
            '.md': NEON_PURPLE,
            '.txt': MID_GRAY,
            '.yml': DEEP_CYAN,
            '.yaml': DEEP_CYAN,
            '.toml': DEEP_CYAN,
            '.ini': MID_GRAY,
            '.sh': GLITCH_GREEN,
            '.html': BRIGHT_MAGENTA,
            '.css': ELECTRIC_CYAN,
        }

    def update_base_dir(self, new_base_dir: Path):
        """Update tree root on cd."""
        self.base_dir = new_base_dir.resolve()
        logger.debug(f"TreePanel base_dir updated to {self.base_dir}")

    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        return ansi_pattern.sub("", text)

    def _should_ignore(self, path: Path) -> bool:
        if path.suffix in self.ignore_exts:
            return True
        for part in path.parts:
            if part in self.ignore_dirs:
                return True
        return False

    def _get_file_color(self, file_path: Path) -> str:
        return self.extension_colors.get(file_path.suffix.lower(), WHITE)

    def _build_tree(self, path: Path, prefix: str = "", depth: int = 0, color: bool = False) -> List[str]:
        if depth > self.max_depth:
            return [f"{prefix}└── ... (max depth)"]

        lines = []

        try:
            entries = [e for e in path.iterdir() if not self._should_ignore(e)]
            entries.sort(key=lambda p: (not p.is_dir(), p.name.lower()))

            for i, entry in enumerate(entries):
                is_last = (i == len(entries) - 1)
                branch = "└── " if is_last else "├── "
                extension = "    " if is_last else "│   "

                if entry.is_dir():
                    # Ultra-vibrant folder icon with glow
                    icon = f"{BOLD}{ELECTRIC_CYAN}📁{RESET} " if color else "📁 "
                    name = f"{entry.name}/"
                    if color:
                        name = f"{BOLD}{ELECTRIC_CYAN}{name}{RESET}"
                else:
                    # Ultra-vibrant file icon with enhanced colors
                    file_icon = "📄 "
                    if color:
                        file_color = self._get_file_color(entry)
                        icon = f"{BOLD}{file_color}{file_icon}{RESET}"
                    else:
                        icon = file_icon
                    name = entry.name
                    if color:
                        name = f"{BOLD}{self._get_file_color(entry)}{name}{RESET}"

                lines.append(f"{prefix}{branch}{icon}{name}")

                if entry.is_dir():
                    sub = self._build_tree(entry, prefix + extension, depth + 1, color=color)
                    lines.extend(sub)

        except PermissionError:
            lines.append(f"{prefix}└── ⛔ [Permission Denied]")
        except OSError as e:
            lines.append(f"{prefix}└── ❌ [Error: {e.strerror}]")

        return lines

    def render(self) -> str:
        lines = []
        lines.append("")
        lines.append(f" 🌲 {self.base_dir.name}/")
        lines.append("")

        tree_lines = self._build_tree(self.base_dir, color=False)
        lines.extend([f" {line}" for line in tree_lines])

        lines.append("")
        lines.append(f" Total items: {len(tree_lines)} (Depth: {self.max_depth})")
        return "\n".join(lines)

    def render_color(self) -> str:
        header = f"{BOLD}{NEON_PURPLE}{'═' * 50}{RESET}"
        title = f"{BOLD}{ELECTRIC_CYAN}PROJECT TREE: {self.base_dir.name}{RESET}"
        
        lines = [header, title, header, ""]
        
        root_name = f"{BOLD}{ELECTRIC_CYAN}{self.base_dir.name}/{RESET}"
        lines.append(root_name)
        
        tree_lines = self._build_tree(self.base_dir, color=True)
        lines.extend(tree_lines)

        lines.append("")
        lines.append(f"{DIM}{MID_GRAY}Total items: {len(tree_lines)}{RESET}")

        return "\n".join(lines)

    def display(self):
        print(self.render_color())

    def render_content_lines(self) -> List[str]:
        """
        Enhanced render for dual-panel with better visual design.
        """
        lines: List[str] = []
        lines.append("")  # Top spacer
        
        # Ultra-vibrant header with gradient effect
        header = f"{BOLD}{ELECTRIC_CYAN}╔═══ 📁 {self.base_dir.name}/ ═══╗{RESET}"
        header_len = len(self._strip_ansi(header))
        pad = max(0, (self.width - header_len) // 2)
        lines.append((" " * pad) + header)
        # Add decorative underline
        underline = f"{BOLD}{BRIGHT_MAGENTA}{'═' * (header_len - 2)}{RESET}"
        lines.append((" " * (pad + 1)) + underline)
        lines.append("")
        
        # Build tree with enhanced colors
        tree_lines = self._build_tree(self.base_dir, color=True)
        for line in tree_lines:
            # Enhance tree lines with better visual design
            enhanced_line = f" {line}"
            lines.append(enhanced_line)
        
        lines.append("")
        
        # Ultra-vibrant footer with enhanced stats display
        total_items = len(tree_lines)
        footer = (
            f"{BOLD}{ELECTRIC_CYAN}╚═══{RESET} {BOLD}{BRIGHT_MAGENTA}Total:{RESET} {BOLD}{ELECTRIC_CYAN}{total_items}{RESET} {MID_GRAY}items "
            f"(max depth: {self.max_depth}){RESET}"
        )
        lines.append(f" {footer}")
        
        return lines
