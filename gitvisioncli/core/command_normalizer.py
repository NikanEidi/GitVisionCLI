import os
import re
import shlex
import platform
from pathlib import Path
from typing import Optional, Dict, Any, Union


class CommandNormalizer:
    """
    Universal Command Engine.

    Mode A Behavior (Free Terminal):
      - Terminal can cd / nano / run commands anywhere on the system
      - Only one thing always remains sandboxed: AI edit intents
        (echo "x" > file → SafePatchEngine only on files inside project_root)

    Responsibilities:
      1. Sanitize paths within project_root for AI-edit ONLY
      2. Translate between POSIX / CMD / PowerShell
      3. Detect destructive commands (rm -rf / dd / ...)
      4. Convert echo "x" > file → intent for SafePatchEngine
    """

    def __init__(self, project_root: Union[str, Path]):
        self.project_root = Path(project_root).resolve()

        self.blocked_commands = {
            "format",
            "mkfs",
            "fdisk",
            "dd",
            "shutdown",
            "reboot",
            ":(){ :|:& };:",
        }

        self.dangerous_patterns = [
            re.compile(r"rm\s+-rf\s+/$"),      # root nuke
            re.compile(r"rm\s+-rf\s+/\*"),     # root wildcard nuke
            re.compile(r"rm\s+-rf\s+\.\."),    # parent directory nuke
            re.compile(r">\s*/dev/sd[a-z]"),   # device write
        ]

    # ---------------------------------------------------------- #
    #   PUBLIC API
    # ---------------------------------------------------------- #

    def normalize(
        self,
        command: str,
        shell: str = "auto",
        target_platform: str = "auto",
        cwd: Optional[Union[str, Path]] = None,
        enforce_sandbox: bool = True,
    ) -> Union[str, Dict[str, Any]]:
        """
        If enforce_sandbox = False:
            - path check is disabled for NON-EDIT commands
            - BUT edit-intent is still created only inside project_root
        """

        command = command.strip()
        if not command:
            return ""

        if target_platform == "auto":
            target_platform = platform.system()

        if cwd is None:
            cwd_path = self.project_root
        else:
            cwd_path = Path(cwd).resolve()

        # 1) Edit intents always remain sandboxed
        edit_intent = self._detect_edit_intent(command, cwd_path)
        if edit_intent:
            return edit_intent

        # 2) Security checks always active
        self._check_safety(command)

        # 3) Path normalization
        safe_command = self._normalize_paths(
            command,
            cwd_path,
            enforce_sandbox=enforce_sandbox,
        )

        # 4) OS translation
        final_command = self._translate_for_platform(
            safe_command, shell, target_platform
        )
        return final_command

    def is_destructive(self, command: str) -> bool:
        cmd_parts = command.split()
        if not cmd_parts:
            return False

        base_cmd = cmd_parts[0].lower()

        destructive_keywords = {
            "rm",
            "del",
            "erase",
            "mv",
            "move",
            "cp",
            "copy",
        }

        if base_cmd in destructive_keywords:
            return True

        if ">" in command and ">>" not in command:
            return True

        return False

    # ---------------------------------------------------------- #
    #   SAFETY
    # ---------------------------------------------------------- #

    def _check_safety(self, command: str):
        parts = command.split()
        if not parts:
            return

        base_cmd = parts[0].lower()

        if base_cmd in self.blocked_commands:
            raise ValueError(
                f"Security Violation: Command '{base_cmd}' is strictly blocked."
            )

        for pattern in self.dangerous_patterns:
            if pattern.search(command):
                raise ValueError(
                    f"Security Violation: Dangerous pattern detected in '{command}'"
                )

    # ---------------------------------------------------------- #
    #   EDIT INTENT DETECTION (AI only)
    # ---------------------------------------------------------- #

    def _detect_edit_intent(
        self,
        command: str,
        cwd: Path,
    ) -> Optional[Dict[str, Any]]:
        """
        echo "content" > file.txt  → intent_rewrite_file
        echo "content" >> file.txt → intent_append_file

        If file is outside project_root → intent = None (let the shell handle it)
        """

        # echo "..." > file
        write_match = re.match(
            r'^echo\s+[\'"](.*)[\'"]\s*>\s*(.+)$', command, re.DOTALL
        )
        if write_match:
            content, filepath = write_match.groups()
            filepath = filepath.strip()
            if self._is_path_safe(filepath, cwd):
                rel_path = self._rel_to_root(filepath, cwd)
                return {
                    "type": "intent_rewrite_file",
                    "path": rel_path,
                    "content": content,
                }

        # echo "..." >> file
        append_match = re.match(
            r'^echo\s+[\'"](.*)[\'"]\s*>>\s*(.+)$', command, re.DOTALL
        )
        if append_match:
            content, filepath = append_match.groups()
            filepath = filepath.strip()
            if self._is_path_safe(filepath, cwd):
                rel_path = self._rel_to_root(filepath, cwd)
                return {
                    "type": "intent_append_file",
                    "path": rel_path,
                    "content": content,
                }

        return None

    # ---------------------------------------------------------- #
    #   PATH NORMALIZATION / SANDBOX
    # ---------------------------------------------------------- #

    def _normalize_paths(
        self,
        command: str,
        cwd: Path,
        enforce_sandbox: bool = True,
    ) -> str:
        """
        If enforce_sandbox=False:
            No path-check is performed (free terminal)
        If enforce_sandbox=True:
            Any path that resolves outside project_root → error
        """

        is_windows = platform.system() == "Windows"

        if is_windows:
            parts = command.split()
        else:
            parts = shlex.split(command, posix=True)

        if not enforce_sandbox:
            # Free terminal mode: we have no path restrictions
            return " ".join(parts)

        new_parts = []
        for part in parts:
            if "/" in part or "\\" in part or part.startswith("."):
                try:
                    potential_path = (cwd / part).resolve()

                    if not self._is_under_root(potential_path):
                        raise ValueError(
                            f"Path Sandbox Violation: {part} resolves to {potential_path}"
                        )

                    new_parts.append(part)
                except OSError:
                    new_parts.append(part)
            else:
                new_parts.append(part)

        return " ".join(new_parts)

    def _is_under_root(self, path: Path) -> bool:
        try:
            path = path.resolve()
        except Exception:
            return False

        root = self.project_root
        return root == path or root in path.parents

    def _is_path_safe(self, filepath: str, cwd: Path) -> bool:
        try:
            target = (cwd / filepath).resolve()
            return self._is_under_root(target)
        except Exception:
            return False

    def _rel_to_root(self, filepath: str, cwd: Path) -> str:
        target = (cwd / filepath).resolve()
        if not self._is_under_root(target):
            raise ValueError(
                f"Path Sandbox Violation: {filepath} -> {target} outside project root"
            )
        return target.relative_to(self.project_root).as_posix()

    # ---------------------------------------------------------- #
    #   OS TRANSLATION
    # ---------------------------------------------------------- #

    def _translate_for_platform(
        self,
        command: str,
        shell: str,
        target_platform: str,
    ) -> str:
        parts = command.split()
        if not parts:
            return command

        cmd = parts[0]
        args = parts[1:]

        is_windows = target_platform == "Windows"

        posix_to_win = {
            "ls": "dir" if shell == "cmd" else "Get-ChildItem",
            "rm": "del" if shell == "cmd" else "Remove-Item",
            "cp": "copy" if shell == "cmd" else "Copy-Item",
            "mv": "move" if shell == "cmd" else "Move-Item",
            "cat": "type" if shell == "cmd" else "Get-Content",
            "grep": "findstr" if shell == "cmd" else "Select-String",
            "pwd": "cd" if shell == "cmd" else "Get-Location",
            "touch": "type nul >" if shell == "cmd" else "New-Item -ItemType File -Force",
            "clear": "cls" if shell == "cmd" else "Clear-Host",
        }

        win_to_posix = {
            "dir": "ls",
            "del": "rm",
            "erase": "rm",
            "copy": "cp",
            "move": "mv",
            "type": "cat",
            "ren": "mv",
        }

        if is_windows:
            if cmd in posix_to_win:
                translated = posix_to_win[cmd]

                # rm -rf
                if cmd == "rm" and ("-rf" in args or "-r" in args):
                    if shell == "cmd":
                        return "rmdir /s /q " + " ".join(
                            [a for a in args if not a.startswith("-")]
                        )
                    else:
                        return "Remove-Item -Recurse -Force " + " ".join(
                            [a for a in args if not a.startswith("-")]
                        )

                if cmd == "touch" and shell == "cmd":
                    return f"{translated} {' '.join(args)}"

                return f"{translated} {' '.join(args)}"

        else:
            if cmd.lower() in win_to_posix:
                translated = win_to_posix[cmd.lower()]
                return f"{translated} {' '.join(args)}"

        return command

    # ---------------------------------------------------------- #
    #   GIT HELPER
    # ---------------------------------------------------------- #

    def normalize_git_command(self, command: str) -> str:
        if not command.startswith("git"):
            return command
        if "--no-pager" not in command:
            command = command.replace("git ", "git --no-pager ", 1)
        return command