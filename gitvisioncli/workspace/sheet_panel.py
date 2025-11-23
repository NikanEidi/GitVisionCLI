"""
Command Sheet Panel — Live command reference for GitVisionCLI.
Lists workspace commands, panel controls, shell prefixes, and all
ActionSupervisor tool actions in a responsive, colorized view.
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
    Renders a read-only "command sheet" into the right panel.
    """

    def __init__(self, width: int = 80):
        self.width = width

    def _strip_ansi(self, text: str) -> str:
        import re

        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        return ansi_pattern.sub("", text)

    def _fit_line(self, text: str, width: int) -> str:
        """Fit text to exact width (no ANSI inside)."""
        length = len(text)
        if length == width:
            return text
        if length < width:
            return text + (" " * (width - length))
        if width <= 1:
            return text[:1]
        return text[: width - 1] + "…"

    def _section_header(self, title: str) -> List[str]:
        title_col = f"{BOLD}{ELECTRIC_CYAN}{title}{RESET}"
        raw_len = len(self._strip_ansi(title_col))
        if raw_len >= self.width:
            return [title_col]
        pad = (self.width - raw_len) // 2
        return [(" " * pad) + title_col]

    def _workspace_commands(self) -> List[str]:
        cmds = [
            (":banner", "Show workspace banner/help"),
            (":tree", "Show project tree explorer"),
            (":edit <file>", "Open file in editor panel"),
            (":markdown <file>", "Preview markdown file with rendering"),
            (":sheet / :commands", "Show this live command sheet"),
            (":models", "AI Model Manager (engines, models, API keys)"),
            (":git-graph / :gitgraph", "Git commit graph visualization"),
            (":live-edit <file>", "AI Live Editor Mode (edit file via AI)"),
            (":save", "Save current editor buffer to disk"),
            (":close / :x", "Close right panel and return to banner"),
        ]
        lines: List[str] = []
        for cmd, desc in cmds:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<20}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        return lines

    def _keyboard_shortcuts(self) -> List[str]:
        """Essential keyboard and quick shortcuts."""
        shortcuts = [
            ("Ctrl+C", "Cancel current operation / exit multi-line mode"),
            ("Ctrl+D", "Exit GitVision (or 'exit'/'quit' command)"),
            ("↑ / ↓", "Navigate command history"),
            ("Tab", "Autocomplete (if available)"),
        ]
        lines: List[str] = []
        for key, desc in shortcuts:
            k = f"{BOLD}{BRIGHT_MAGENTA}{key:<12}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {k} {d}")
        return lines
    
    def _navigation_commands(self) -> List[str]:
        """Navigation and workspace control commands."""
        cmds = [
            ("cd <path>", "Change directory (or 'cd ..' to go up)"),
            ("pwd", "Print current working directory"),
            ("clear", "Clear console screen"),
            ("stats", "Show workspace statistics"),
            ("exit / quit", "Exit GitVisionCLI"),
        ]
        lines: List[str] = []
        for cmd, desc in cmds:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<20}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        return lines
    
    def _editor_scroll_commands(self) -> List[str]:
        """Editor scrolling commands (when in editor mode)."""
        cmds = [
            (":up / :scroll-up", "Scroll editor view up"),
            (":down / :scroll-down", "Scroll editor view down"),
            (":pageup / :pu", "Scroll editor one page up"),
            (":pagedown / :pd", "Scroll editor one page down"),
        ]
        lines: List[str] = []
        for cmd, desc in cmds:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<20}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        return lines
        lines: List[str] = []
        for key, desc in shortcuts:
            k = f"{BOLD}{BRIGHT_MAGENTA}{key:<12}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {k} {d}")
        return lines

    def _multiline_input_commands(self) -> List[str]:
        """
        Commands and patterns for stable multi-line input handling.
        """
        cmds = [
            (":paste / :ml / :block", "Start manual multi-line input; finish with a line ':end'"),
            ("fenced blocks (```...```)", "Paste code/JSON/Markdown blocks; treated as a single message"),
        ]
        lines: List[str] = []
        for cmd, desc in cmds:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<30}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        return lines

    def _ai_engine_commands(self) -> List[str]:
        """
        Commands and concepts for the hot-swappable AI engine system.
        """
        cmds = [
            (":set-ai <name>", "Switch active AI engine/model at runtime"),
            (":models", "Inspect providers, models, and API keys"),
            ("stats", "Show current provider/model and message count"),
            ("ollama models", "List installed local Ollama models"),
            ("ollama pull <model>", "Install a local Ollama model"),
        ]
        lines: List[str] = []
        for cmd, desc in cmds:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")
        lines.append(
            f"{DIM}{DARK_GRAY}"
            "Engines: Ollama (local), OpenAI / Gemini / Claude (cloud API)."
            f"{RESET}"
        )
        lines.append(
            f"{DIM}{DARK_GRAY}"
            "Use :models to see available models, key status, and provider setup tips."
            f"{RESET}"
        )
        lines.append(
            f"{DIM}{DARK_GRAY}"
            "API keys live in config.json under 'providers'. Use :set-ai <name> to switch "
            "models (e.g. gpt-4o, gemini-1.5-pro, claude-3.5-sonnet, or an Ollama model)."
            f"{RESET}"
        )
        return lines

    def _sandbox_commands(self) -> List[str]:
        cmds = [
            (":sandbox on", "Restrict navigation to project root"),
            (":sandbox off", "Allow full filesystem navigation"),
            (":sandbox status", "Show current sandbox state"),
        ]
        lines: List[str] = []
        for cmd, desc in cmds:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<18}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        return lines

    def _shell_prefixes(self) -> List[str]:
        lines: List[str] = []
        lines.append(
            f"{DIM}{DARK_GRAY}Prefix-based cross-OS execution (overrides host OS):{RESET}"
        )
        prefixes = [
            ("p.*", "PowerShell mode (e.g., p.get-process, p.dir)"),
            ("c.*", "Windows CMD mode (e.g., c.dir, c.echo hello)"),
            ("l.*", "Linux bash mode (e.g., l.ls, l.cat file)"),
            ("m.*", "macOS zsh mode (e.g., m.open, m.say)"),
            (".<cmd>", "Run local shell directly (e.g., .ls, .git status)"),
        ]
        for pfx, desc in prefixes:
            p = f"{BOLD}{BRIGHT_MAGENTA}{pfx:<10}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {p} {d}")
        return lines

    def _shell_shortcuts(self) -> List[str]:
        """
        Local shell shortcuts (no prefix) routed via TerminalEngine
        when the user types them directly at the prompt.
        """
        shortcuts = [
            ("pwd / ls / ll", "Quick directory listing"),
            ("whoami", "Show current user"),
            ("cat / tree", "Inspect files and folders"),
            ("mkdir / rmdir / rm / touch", "Basic filesystem operations"),
        ]
        lines: List[str] = []
        for cmd, desc in shortcuts:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<22}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        return lines

    def _action_types(self) -> List[str]:
        """
        List all ActionSupervisor action types so the sheet stays in sync
        when new operations are added.
        """
        lines: List[str] = []
        for at in ActionType:
            name = at.value
            group = "Other"
            if "GitHub" in name:
                group = "GitHub"
            elif name.startswith("Git"):
                group = "Git"
            elif any(
                name.startswith(prefix)
                for prefix in ("Create", "Edit", "Delete", "Move", "Copy", "Rename")
            ):
                group = "Filesystem"
            elif name in {
                "AppendText",
                "PrependText",
                "ReplaceText",
                "InsertBeforeLine",
                "InsertAfterLine",
                "DeleteLineRange",
                "RewriteEntireFile",
                "ApplyPatch",
            }:
                group = "AI Text/Edit"

            c = f"{BOLD}{BRIGHT_MAGENTA}{name:<26}{RESET}"
            g = f"{DIM}{MID_GRAY}{group}{RESET}"
            lines.append(f"  {c} {g}")
        return lines

    def render_content_lines(self) -> List[str]:
        lines: List[str] = []

        # Title
        title = f"{BOLD}{NEON_PURPLE}GITVISION COMMAND SHEET{RESET}"
        raw_len = len(self._strip_ansi(title))
        if raw_len < self.width:
            pad = (self.width - raw_len) // 2
            lines.append((" " * pad) + title)
        else:
            lines.append(title)

        # Quick usage hint for this panel
        lines.append("")
        intro = (
            f"{DIM}{MID_GRAY}"
            "Use :sheet any time to reopen this cheat sheet. "
            "Use :models to manage AI engines and models."
            f"{RESET}"
        )
        raw_len_intro = len(self._strip_ansi(intro))
        if raw_len_intro < self.width:
            pad_intro = (self.width - raw_len_intro) // 2
            lines.append((" " * pad_intro) + intro)
        else:
            lines.append(intro)

        lines.append("")

        # Workspace / Panels
        lines += self._section_header("Workspace & Panel Commands")
        lines.append("")
        lines += self._workspace_commands()
        lines.append("")

        # Sandbox
        lines += self._section_header("Sandbox")
        lines.append("")
        lines += self._sandbox_commands()
        lines.append("")

        # Multi-line input
        lines += self._section_header("Multi-line Input")
        lines.append("")
        lines += self._multiline_input_commands()
        lines.append("")

        # Shell prefixes (cross-OS)
        lines += self._section_header("Shell Prefix Modes (Cross-OS)")
        lines.append("")
        lines += self._shell_prefixes()
        lines.append("")

        # Shell shortcuts
        lines += self._section_header("Local Shell Shortcuts")
        lines.append("")
        lines += self._shell_shortcuts()
        lines.append("")

        # AI Engines / Models
        lines += self._section_header("AI Engines & Models")
        lines.append("")
        lines += self._ai_engine_commands()
        lines.append("")

        # Navigation & Workspace
        lines += self._section_header("🧭 Navigation & Workspace")
        lines.append("")
        lines += self._navigation_commands()
        lines.append("")
        
        # Editor Scrolling
        lines += self._section_header("📜 Editor Scrolling (Editor Mode)")
        lines.append("")
        lines += self._editor_scroll_commands()
        lines.append("")
        
        # Keyboard shortcuts
        lines += self._section_header("⌨️  Keyboard Shortcuts")
        lines.append("")
        lines += self._keyboard_shortcuts()
        lines.append("")

        # Git commands section (legacy - now covered in Natural Language section)
        lines += self._section_header("🔁 Git Commands (All Methods)")
        lines.append("")
        lines.append(
            f"{DIM}{DARK_GRAY}Use natural language, :git-graph command, or AI for Git operations:{RESET}"
        )
        lines.append("")
        git_cmds = [
            (":git-graph", "Open Git graph panel (or :gitgraph, or 'git graph')"),
            ("git init", "Initialize repository (direct NLAE)"),
            ("git add <files>", "Stage files (direct NLAE)"),
            ("git commit 'message'", "Commit with message (direct NLAE)"),
            ("git branch <name>", "Create branch (direct NLAE)"),
            ("git checkout <branch>", "Switch branch (direct NLAE)"),
            ("git merge <branch>", "Merge branch (direct NLAE)"),
            ("git graph", "Open Git graph panel (natural language)"),
            ("git push / git pull", "Remote sync (via AI)"),
            ("git status / git log", "View status/history (via AI)"),
        ]
        for cmd, desc in git_cmds:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")

        # Natural Language Commands (Direct Action Engine)
        lines += self._section_header("💬 Natural Language Commands (Direct)")
        lines.append("")
        lines.append(
            f"{DIM}{DARK_GRAY}These commands work instantly without AI (via Natural Language Action Engine):{RESET}"
        )
        lines.append("")
        
        nl_file_ops = [
            ("create file <path>", "Create new file"),
            ("read file <path>", "Read/display file content"),
            ("delete file <path>", "Delete file"),
            ("rename <old> to <new>", "Rename file"),
            ("move <file> to <folder>", "Move file to folder"),
            ("copy <file> to <new>", "Copy file"),
            ("open <file>", "Open file in editor"),
        ]
        for cmd, desc in nl_file_ops:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")
        
        lines.append(
            f"{DIM}{DARK_GRAY}Folder operations:{RESET}"
        )
        lines.append("")
        nl_folder_ops = [
            ("create folder <path>", "Create new folder/directory"),
            ("delete folder <path>", "Delete folder/directory"),
            ("move folder <path> to <target>", "Move folder to new location"),
            ("copy folder <path> to <new>", "Copy folder"),
            ("rename folder <old> to <new>", "Rename folder"),
        ]
        for cmd, desc in nl_folder_ops:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")
        
        lines.append(
            f"{DIM}{DARK_GRAY}Line editing (when file is open in editor):{RESET}"
        )
        lines.append("")
        nl_line_ops = [
            ("remove line 5", "Delete single line (also: rm 5, delete line1)"),
            ("delete lines 4-9", "Delete line range (also: remove lines 4 to 9)"),
            ("replace line 3 with <text>", "Replace line content"),
            ("add <text> at line 10", "Insert at specific line (after line 10)"),
            ("add <text> at bottom", "Append to end of file"),
            ("insert <text> at line 5", "Insert before line 5"),
        ]
        for cmd, desc in nl_line_ops:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")
        
        lines.append(
            f"{DIM}{DARK_GRAY}Git operations:{RESET}"
        )
        lines.append("")
        nl_git_ops = [
            (":git-graph", "Open Git graph panel (command)"),
            ("git graph", "Open Git graph panel (natural language)"),
            ("git init", "Initialize repository"),
            ("git add <files>", "Stage files (or 'git add .' for all)"),
            ("git commit 'message'", "Commit with message"),
            ("git branch <name>", "Create new branch"),
            ("git checkout <branch>", "Switch to branch (or 'go to <branch>')"),
            ("git merge <branch>", "Merge branch"),
        ]
        for cmd, desc in nl_git_ops:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")
        
        lines.append(
            f"{DIM}{DARK_GRAY}GitHub operations:{RESET}"
        )
        lines.append("")
        nl_github_ops = [
            ("create github repo <name>", "Create GitHub repository (public/private)"),
            ("create github issue 'title'", "Create GitHub issue with title"),
            ("create github pr 'title'", "Create pull request with title"),
        ]
        for cmd, desc in nl_github_ops:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")
        
        lines.append(
            f"{DIM}{DARK_GRAY}Directory navigation:{RESET}"
        )
        lines.append("")
        nl_dir_ops = [
            ("cd <path>", "Change directory"),
            ("cd ..", "Go up one directory"),
            ("pwd", "Show current directory"),
            ("create folder X and go to it", "Create folder + change directory"),
        ]
        for cmd, desc in nl_dir_ops:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")
        
        # Editor shortcuts
        lines += self._section_header("✏️  Editor Tips & Features")
        lines.append("")
        editor_tips = [
            ("Use :live-edit <file>", "AI edits the file in real-time with streaming"),
            ("Natural edits", "Say: 'add hello world after line 5'"),
            ("Line references", "AI understands line numbers when file is open"),
            ("Auto-save", "Changes auto-sync to UI when saved"),
            ("Grammar fix", "Broken grammar auto-fixed (line1→line 1, rm 5→remove line 5)"),
            ("Streaming writes", "AI text streams token-by-token into editor"),
            ("No questions", "AI never asks questions when file is open"),
        ]
        for tip, desc in editor_tips:
            t = f"{BOLD}{BRIGHT_MAGENTA}{tip:<22}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {t} {d}")
        lines.append("")

        # Action types
        lines += self._section_header("🔧 All Supported Action Types")
        lines.append("")
        lines.append(
            f"{DIM}{DARK_GRAY}All actions below work via AI (execute_action). Many also work directly via NLAE:{RESET}"
        )
        lines.append("")
        lines += self._action_types()
        lines.append("")
        lines.append(
            f"{DIM}{DARK_GRAY}Advanced actions (UpdateJSONKey, InsertIntoFunction, etc.) work via AI model calls.{RESET}"
        )
        lines.append("")

        footer = f"{DIM}{DARK_GRAY}Use :close to return to the workspace banner.{RESET}"
        lines.append(footer)

        return lines
