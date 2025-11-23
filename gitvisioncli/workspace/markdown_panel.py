# gitvisioncli/workspace/markdown_panel.py
"""
Markdown Panel — Terminal markdown renderer
"""

import logging
from pathlib import Path
from typing import Optional, List
import re

# Import the stabilized colors
from gitvisioncli.ui.colors import *

logger = logging.getLogger(__name__)

class MarkdownPanel:
    """
    Render markdown files with formatting.
    """
    
    def __init__(self, width: int = 80):
        self.width = width
        self.content: Optional[str] = None
        self.file_path: Optional[Path] = None
    
    # ----------------------------------------------------------
    # LOADING
    # ----------------------------------------------------------

    def load_file(self, file_path: Path) -> bool:
        """Load file content into memory."""
        try:
            self.file_path = file_path.resolve()
            self.content = self.file_path.read_text(encoding='utf-8', errors='ignore')
            logger.info(f"MarkdownPanel loaded: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading markdown {file_path}: {e}")
            self.content = f"# Error loading file\n\nCould not read file: {file_path}\n\nReason: {e}"
            self.file_path = None
            return False
    
    def load_content(self, content: str, title: str = "Preview"):
        """Load raw string content into memory."""
        self.content = content
        # Create a dummy path for the header
        self.file_path = Path(title) 

    # ----------------------------------------------------------
    # NATIVE PLAIN-TEXT RENDERER (for Dual-Panel UI)
    # ----------------------------------------------------------

    def render_as_lines(self) -> List[str]:
        """
        Wrapper for render_content_lines.
        """
        return self.render_content_lines()
        
    def render_content_lines(self) -> List[str]:
        """
        Plain text version for dual-panel mode, NO HEADER.
        """
        lines = self.content.split("\n") if self.content else []
        result: List[str] = [""] # Initial spacer
        
        if self.content is None:
            result.append(" <No file loaded>")
            return result

        i = 0
        in_code_block = False
        while i < len(lines):
            line = lines[i]

            # Code block toggle
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                # Add padding
                result.append(f" {line.strip()}")
                i += 1
                continue

            # Inside a code block
            if in_code_block:
                result.append(f"   {line}") # Indent code
                i += 1
                continue
            
            # Not in code block, process other elements

            if not line.strip():
                result.append("")
                i += 1
                continue

            # Headers (H1/H2 get underlines)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2)
                
                # Add padding
                result.append(f" {line}")
                if level == 1:
                    result.append(' ' + ('═' * len(text)))
                elif level == 2:
                    result.append(' ' + ('─' * len(text)))
                
                i += 1
                continue

            # Horizontal Rule
            if re.match(r'^[\-\*_]{3,}$', line.strip()):
                hr_width = max(10, self.width - 4) 
                # Add padding
                result.append(' ' + ('─' * hr_width)) 
                i += 1
                continue

            # Blockquote
            if line.startswith(">"):
                # Add padding and use clean vertical line for quote
                result.append(f" ┃ {line[1:].strip()}")
                i += 1
                continue

            # List Items
            if re.match(r'^\s*[*\-\+\d\.]\s+', line):
                # Add padding
                result.append(f" {line}")
                i += 1
                continue

            # Paragraph (just the line)
            # Add padding
            result.append(f" {line}")
            i += 1
            
        result.append("")

        # Add a footer/separator line manually
        footer_line = "──────────────────────────────────────────────────"
        result.append(f" {footer_line}")

        return result

    # ----------------------------------------------------------
    # COLOR RENDERER (for standalone/debug use)
    # ----------------------------------------------------------

    def _render_header_color(self, line: str) -> str:
        """(Color) Render H1-H6 headers."""
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if not match:
            return line
        
        level = len(match.group(1))
        text = match.group(2)

        if level == 1:
            return f"{BOLD}{ELECTRIC_CYAN}{text}{RESET}\n{'═'*len(text)}"
        elif level == 2:
            return f"{BOLD}{NEON_PURPLE}{text}{RESET}\n{'─'*len(text)}"
        elif level == 3:
            return f"{BOLD}{BRIGHT_MAGENTA}▸ {text}{RESET}"
        else:
            return f"{BOLD}{MID_GRAY}{'  '*(level-3)}▸ {text}{RESET}"

    def _render_list_item_color(self, line: str) -> str:
        """(Color) Render ul/ol list items."""
        m = re.match(r'^(\s*)[*\-+]\s+(.+)$', line)
        if m:
            indent = m.group(1)
            text = m.group(2)
            return f"{indent}{ELECTRIC_CYAN}•{RESET} {text}"

        m = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
        if m:
            indent, num, text = m.groups()
            return f"{indent}{BRIGHT_MAGENTA}{num}.{RESET} {text}"

        return line

    def _render_code_block_color(self, lines: List[str], start_idx: int):
        """(Color) Render a fenced code block."""
        end_idx = start_idx + 1
        code_lines = []
        
        # find closing ```
        lang = lines[start_idx].strip()[3:]
        
        for i in range(start_idx + 1, len(lines)):
            if lines[i].strip().startswith("```"):
                end_idx = i
                break
            code_lines.append(lines[i])
        
        # Use a width relative to the panel
        code_width = max(40, self.width - 4)
        
        header = f"┌─── {lang} {'─'*(code_width - 8 - len(lang))}┐"
        result = [f"{DIM}{DARK_GRAY}{header}{RESET}"]
        
        for code in code_lines:
            # Pad line to full width
            padded_code = f"{code:<{code_width-2}}" 
            result.append(f"{DIM}{DARK_GRAY}│{RESET} {GLITCH_GREEN}{padded_code}{RESET} {DIM}{DARK_GRAY}│{RESET}")
            
        footer = f"└{'─'*(code_width)}┘"
        result.append(f"{DIM}{DARK_GRAY}{footer}{RESET}")

        return "\n".join(result), end_idx

    def _render_inline_formatting_color(self, text: str) -> str:
        """(Color) Render bold, italic, code, links."""
        text = re.sub(r'\*\*(.+?)\*\*', f'{BOLD}\\1{RESET}', text)
        text = re.sub(r'__(.+?)__', f'{BOLD}\\1{RESET}', text)
        text = re.sub(r'\*(.+?)\*', f'{DIM}\\1{RESET}', text) # Use DIM for italic
        text = re.sub(r'_(.+?)_', f'{DIM}\\1{RESET}', text) # Use DIM for italic
        text = re.sub(r'`(.+?)`', f'{GLITCH_GREEN}\\1{RESET}', text)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', f'{ELECTRIC_CYAN}\\1{RESET} {DIM}({MID_GRAY}\\2{RESET}{DIM}){RESET}', text)
        return text

    def _render_blockquote_color(self, line: str) -> str:
        """(Color) Render a blockquote."""
        m = re.match(r'^>\s+(.+)$', line)
        if m:
            return f"{DIM}{DARK_GRAY}┃{RESET} {DIM}{m.group(1)}{RESET}"
        return line

    def _render_hr_color(self, line: str) -> str:
        """(Color) Render a horizontal rule."""
        if re.match(r'^[\-\*_]{3,}$', line.strip()):
            return f"{DIM}{DARK_GRAY}{'─'*self.width}{RESET}"
        return line

    def render_color(self) -> str:
        """Render with full ANSI colors (for debugging)."""
        if self.content is None:
            return f"{GLITCH_RED}No markdown loaded{RESET}"

        lines = self.content.split("\n")
        result = []

        # Header
        if self.file_path:
            name = self.file_path.name
            result.append(f"{BOLD}{NEON_PURPLE}╔═══ MARKDOWN: {name} ═══{RESET}")
            result.append("")

        i = 0
        while i < len(lines):
            line = lines[i]

            # code block
            if line.strip().startswith("```"):
                block, end = self._render_code_block_color(lines, i)
                result.append(block)
                i = end + 1
                continue

            if not line.strip():
                result.append("")
                i += 1
                continue

            if line.startswith("#"):
                result.append(self._render_header_color(line))
                i += 1
                continue

            if re.match(r'^[\-\*_]{3,}$', line.strip()):
                result.append(self._render_hr_color(line))
                i += 1
                continue

            if line.startswith(">"):
                result.append(self._render_blockquote_color(line))
                i += 1
                continue

            if re.match(r'^\s*[*\-\+\d\.]\s+', line):
                result.append(self._render_list_item_color(line))
                i += 1
                continue

            # paragraph
            result.append(self._render_inline_formatting_color(line))
            i += 1

        result.append("")
        result.append(f"{BOLD}{NEON_PURPLE}{'═' * 50}{RESET}")

        return "\n".join(result)

    def display(self):
        """Helper to print the colorized version to terminal."""
        print(self.render_color())