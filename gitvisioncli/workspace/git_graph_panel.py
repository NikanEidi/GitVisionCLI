"""
Git Graph Panel — ASCII commit graph view for the right panel.

This panel is read-only and reuses the unified git detection logic from
ActionSupervisor (GitRepoState + _run_git_command) via a small public API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from gitvisioncli.ui.colors import (
    BOLD,
    RESET,
    DIM,
    MID_GRAY,
    ELECTRIC_CYAN,
    NEON_PURPLE,
)


@dataclass
class GitGraphPanel:
    """Render a git commit graph using the shared ActionSupervisor."""

    supervisor: "ActionSupervisor"
    width: int = 80

    def _strip_ansi(self, text: str) -> str:
        import re

        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        return ansi_pattern.sub("", text)

    def _fit_line(self, text: str) -> str:
        raw = self._strip_ansi(text)
        if len(raw) <= self.width:
            return text
        # Truncate preserving left part; add ellipsis
        trimmed = raw[: self.width - 1] + "…"
        return trimmed

    def _header(self) -> List[str]:
        title = f"{BOLD}{NEON_PURPLE}GIT COMMIT GRAPH{RESET}"
        raw_len = len(self._strip_ansi(title))
        pad = max(0, (self.width - raw_len) // 2)
        return ["", " " * pad + title, ""]

    def render_content_lines(self) -> List[str]:
        """
        Return the current git graph as a list of lines.
        Uses the supervisor's git state so that repo discovery logic is
        identical to other git operations.
        """
        lines: List[str] = []
        lines.extend(self._header())

        try:
            repo_state = self.supervisor._get_git_repo_state()
        except Exception:
            repo_state = None

        if not repo_state or not repo_state.is_repo:
            lines.append(
                f"{DIM}{MID_GRAY}No git repository detected in the current workspace.{RESET}"
            )
            lines.append(
                f"{DIM}{MID_GRAY}Use GitInit via the AI tools or run git init in the workspace root.{RESET}"
            )
            return lines

        if not repo_state.has_commits:
            lines.append(
                f"{DIM}{MID_GRAY}Repository initialized but no commits yet.{RESET}"
            )
            lines.append(
                f"{DIM}{MID_GRAY}Create files, stage them, and commit to populate the graph.{RESET}"
            )
            return lines

        # Use the same git command entry point as other git operations.
        success, stdout, stderr = self.supervisor._run_git_command(
            ["log", "--graph", "--oneline", "--decorate", "--all", "--max-count=50"],
            require_repo=True,
            cwd=repo_state.root,
        )

        if not success:
            lines.append(
                f"{DIM}{MID_GRAY}Failed to read git history: {stderr or 'unknown error'}{RESET}"
            )
            return lines

        graph_lines = stdout.splitlines() if stdout else []
        if not graph_lines:
            lines.append(
                f"{DIM}{MID_GRAY}No commits to display in the graph view.{RESET}"
            )
            return lines

        for raw in graph_lines:
            # Mild coloring: highlight graph glyphs, commit hashes and branch decorations.
            pretty = raw
            # Shape: graph prefix + hash + rest, e.g.:
            # "*   abcd123 (HEAD -> main, origin/main) message"
            import re as _re

            m = _re.match(r"^([*|\\/ ]+)\s*([0-9a-f]{7,})\s*(.*)$", raw)
            if m:
                graph_prefix, commit_hash, rest = m.groups()
                graph_col = f"{DIM}{MID_GRAY}{graph_prefix}{RESET}"
                hash_col = f"{ELECTRIC_CYAN}{commit_hash}{RESET}"
                decor = ""
                msg = rest
                if rest.startswith("(") and ")" in rest:
                    end = rest.find(")")
                    decor = rest[: end + 1]
                    msg = rest[end + 1 :].lstrip()
                if decor:
                    decor_col = f"{BRIGHT_MAGENTA}{decor}{RESET}"
                    pretty = f"{graph_col} {hash_col} {decor_col} {msg}".rstrip()
                else:
                    pretty = f"{graph_col} {hash_col} {msg}".rstrip()
            lines.append(self._fit_line(pretty))

        lines.append("")
        lines.append(
            f"{DIM}{MID_GRAY}Showing up to 50 recent commits across all branches.{RESET}"
        )
        return lines
