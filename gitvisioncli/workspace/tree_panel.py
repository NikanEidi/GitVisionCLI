"""
Tree Panel — Recursive project directory tree viewer
"""

import logging
from pathlib import Path
from typing import List, Optional, Set
from gitvisioncli.ui.colors import *
import re

logger = logging.getLogger(__name__)

class TreePanel:
    """
    Display colorized directory tree of the project.
    """
    
    def __init__(self, base_dir: str, max_depth: int = 7, width: int = 80):
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
                    # Unicode-style expansion arrow to indicate an expanded folder.
                    icon = "▾ "
                    name = f"{entry.name}/"
                    if color:
                        name = f"{BOLD}{ELECTRIC_CYAN}{name}{RESET}"
                else:
                    # Simple bullet for files; color and extension mapping carry the
                    # primary semantic weight so we avoid wide glyphs here.
                    icon = "• "
                    name = entry.name
                    if color:
                        name = f"{self._get_file_color(entry)}{name}{RESET}"

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
        return self.render().split("\n")
