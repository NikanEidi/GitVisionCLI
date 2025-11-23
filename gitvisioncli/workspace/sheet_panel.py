"""
Command Sheet Panel — Compact command reference for GitVisionCLI.
Optimized to fit on one half-page with all essential commands.
"""

from typing import List

from gitvisioncli.ui.colors import (
    RESET,
    BOLD,
    DIM,
    NEON_PURPLE,
    BRIGHT_MAGENTA,
    ELECTRIC_CYAN,
    MID_GRAY,
    DARK_GRAY,
)
from gitvisioncli.core.supervisor import ActionType


class CommandSheetPanel:
    """
    Renders a compact command sheet optimized for half-page display.
    """

    def __init__(self, width: int = 80):
        self.width = width

    def _strip_ansi(self, text: str) -> str:
        import re
        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        return ansi_pattern.sub("", text)

    def _compact_section(self, title: str, items: List[tuple]) -> List[str]:
        """Ultra-vibrant compact section with gradient title."""
        lines = [f"{BOLD}{ELECTRIC_CYAN}▶{RESET} {BOLD}{BRIGHT_MAGENTA}{title}{RESET}"]
        for cmd, desc in items:
            cmd_str = f"{BOLD}{BRIGHT_MAGENTA}{cmd}{RESET}"
            desc_str = f"{MID_GRAY}{desc}{RESET}"
            # ANSI-aware padding: calculate visible width and pad manually
            cmd_visible_len = len(self._strip_ansi(cmd_str))
            padding_needed = max(0, 28 - cmd_visible_len)
            # Fit in one line: cmd | desc
            line = f"  {cmd_str}{' ' * padding_needed} {desc_str}"
            if len(self._strip_ansi(line)) > self.width - 2:
                # Split if too long
                lines.append(f"  {cmd_str}")
                lines.append(f"    {desc_str}")
            else:
                lines.append(line)
        return lines

    def render_content_lines(self) -> List[str]:
        """Render comprehensive command sheet with all features."""
        lines = []

        # Ultra-vibrant title with gradient effect
        title = f"{BOLD}{ELECTRIC_CYAN}╔═══{RESET}{BOLD}{NEON_PURPLE} GITVISION COMMANDS {RESET}{BOLD}{ELECTRIC_CYAN}═══╗{RESET}"
            lines.append(title)
        # Add decorative underline
        underline = f"{BOLD}{BRIGHT_MAGENTA}{'═' * (len(self._strip_ansi(title)) - 2)}{RESET}"
        lines.append(underline)
        lines.append("")
        
        # PANELS
        lines += self._compact_section("PANELS", [
            (":banner", "Workspace banner"),
            (":tree", "File tree"),
            (":edit <file>", "Open editor"),
            (":live-edit <file>", "AI live editor (streaming)"),
            ("LIVE EDIT", "AI writes directly to file"),
            (":markdown <file>", "Preview markdown"),
            (":save", "Save editor"),
            (":sheet", "This sheet"),
            (":models", "AI models"),
            (":git-graph", "Git graph"),
            (":close", "Close panel"),
        ])
        lines.append("")
        
        # AI & MODELS
        lines += self._compact_section("AI & MODELS", [
            (":set-ai <model>", "Switch model"),
            ("  Examples:", "gpt-4o/gemini-1.5-pro/claude-3-5-sonnet"),
            ("stats", "Show model stats"),
            ("ALL MODELS", "OpenAI, Gemini, Claude, Ollama"),
            ("FULL FUNCTIONALITY", "Streaming + tools for all"),
        ])
        lines.append("")
        
        # FILE OPS
        lines += self._compact_section("FILE OPS", [
            ("create file <path>", "Create file"),
            ("create folder <path>", "Create folder"),
            ("read file <path>", "Read file"),
            ("delete file <path>", "Delete file"),
            ("delete folder <path>", "Delete folder"),
            ("rename <old> <new>", "Rename file/folder"),
            ("move <file> <dest>", "Move file/folder"),
            ("open <file>", "Open in editor"),
        ])
        lines.append("")
        
        # LINE EDITING (when file open)
        lines += self._compact_section("LINE EDIT", [
            ("remove line 5", "Delete line"),
            ("delete lines 4-9", "Delete range"),
            ("add <text> at line 10", "Insert after"),
            ("insert <text> at line 5", "Insert before"),
            ("replace line 3 with <text>", "Replace line"),
            ("add <text> at bottom", "Append to end"),
        ])
        lines.append("")
        
        # MULTILINE MODE
        lines += self._compact_section("MULTILINE", [
            (":ml / :paste", "Start multiline mode"),
            (":end", "End multiline mode"),
            ("```code```", "Fenced code blocks"),
        ])
        lines.append("")
        
        # GIT
        lines += self._compact_section("GIT", [
            ("git init", "Init repo"),
            ("git add <files>", "Stage files"),
            ("git commit 'msg'", "Commit"),
            ("git status", "Status"),
            ("git log", "History"),
            ("git branch <name>", "Create branch"),
            ("git checkout <branch>", "Switch branch"),
            ("git merge <branch>", "Merge branch"),
            ("git push", "Push"),
            ("git pull", "Pull"),
            ("git remote add <name> <url>", "Add remote"),
        ])
        lines.append("")
        
        # GITHUB
        lines += self._compact_section("GITHUB", [
            ("create github repo <name>", "Create repo"),
            ("create github repo <name> private", "Private repo"),
            ("create github issue 'title'", "Create issue"),
            ("create github pr 'title'", "Create PR"),
        ])
        lines.append("")
        
        # AI COMMANDS
        lines += self._compact_section("AI COMMANDS", [
            ("explain <file>", "Explain code"),
            ("analyze this code", "Analyze code"),
            ("find bugs", "Find bugs"),
            ("refactor this", "Refactor code"),
            ("create test for <file>", "Generate tests"),
        ])
        lines.append("")
        
        # SHELL COMMANDS
        lines += self._compact_section("SHELL COMMANDS", [
            ("ls / dir", "List files"),
            ("cd <path>", "Change dir"),
            ("cd ..", "Go up"),
            ("pwd", "Current dir"),
            ("cat <file>", "View file"),
            ("grep <pattern>", "Search text"),
            ("find <name>", "Find files"),
            ("mkdir <dir>", "Create dir"),
            ("rm <file>", "Delete file"),
            ("cp <src> <dst>", "Copy file"),
            ("mv <src> <dst>", "Move file"),
            ("touch <file>", "Create file"),
            ("clear", "Clear screen"),
            ("exit/quit", "Exit app"),
        ])
        lines.append("")
        
        # NATURAL LANGUAGE
        lines += self._compact_section("NATURAL LANGUAGE", [
            ("list files in <dir>", "List directory"),
            ("run <script>", "Execute script"),
            ("debug <file>", "Debug file"),
            ("test <file>", "Test file"),
            ("search for <text>", "Search files"),
            ("find files named <name>", "Find files"),
        ])
        lines.append("")

        # KEYBOARD
        lines += self._compact_section("KEYS", [
            ("Ctrl+C", "Cancel"),
            ("Ctrl+D", "Exit"),
            ("↑/↓", "History"),
        ])
        lines.append("")

        # FOOTER
        footer = f"{MID_GRAY}Type :sheet to reopen | :models to manage AI | ALL AI MODELS (OpenAI/Gemini/Claude/Ollama) support streaming + tools | Use :live-edit for AI live editing | ALL shell commands (ls, cd, grep, find, etc.) fully supported{RESET}"
        lines.append(footer)

        return lines
