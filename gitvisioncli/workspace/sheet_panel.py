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
            (":gitgraph", "Git commit graph visualization"),
            (":live-edit", "AI Live Editor Mode (edit open file via AI)"),
            (":save", "Save current editor buffer to disk"),
            (":close", "Close right panel and return to banner"),
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

        # Keyboard shortcuts
        lines += self._section_header("⌨️  Keyboard Shortcuts")
        lines.append("")
        lines += self._keyboard_shortcuts()
        lines.append("")

        # Git commands section
        lines += self._section_header("🔁 Git Commands (Natural Language)")
        lines.append("")
        git_cmds = [
            ("git init", "Initialize new repository"),
            ("git status", "Check repository status"),
            ("git add <files>", "Stage files for commit"),
            ("git commit", "Commit staged changes"),
            ("git log / git graph", "View commit history"),
            ("git branch / git checkout", "Branch management"),
            ("git push / git pull", "Remote sync operations"),
        ]
        for cmd, desc in git_cmds:
            c = f"{BOLD}{BRIGHT_MAGENTA}{cmd:<24}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {c} {d}")
        lines.append("")

        # Editor shortcuts
        lines += self._section_header("✏️  Editor Tips")
        lines.append("")
        editor_tips = [
            ("Use :live-edit", "AI edits the currently open file in real-time"),
            ("Natural edits", "Say: 'add hello world after line 5'"),
            ("Line references", "AI understands line numbers when file is open"),
            ("Auto-save", "Changes auto-sync to UI when saved"),
        ]
        for tip, desc in editor_tips:
            t = f"{BOLD}{BRIGHT_MAGENTA}{tip:<22}{RESET}"
            d = f"{DIM}{MID_GRAY}{desc}{RESET}"
            lines.append(f"  {t} {d}")
        lines.append("")

        # Action types
        lines += self._section_header("🔧 AI Action Types (execute_action)")
        lines.append("")
        lines += self._action_types()
        lines.append("")

        footer = f"{DIM}{DARK_GRAY}Use :close to return to the workspace banner.{RESET}"
        lines.append(footer)

        return lines
