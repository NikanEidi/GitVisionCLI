import os
import shlex
import shutil
import subprocess
import logging
import platform
from pathlib import Path
from typing import Generator, Tuple, Union, Any, Dict, Optional, Callable

# Conditional import for PTY (Linux/Mac only)
try:
    import pty
    HAS_PTY = True
except ImportError:
    HAS_PTY = False

from gitvisioncli.core.command_normalizer import CommandNormalizer

logger = logging.getLogger(__name__)

# Global sandbox flag, toggled via CLI (`:sandbox on/off`)
SANDBOX_ENABLED: bool = True


class TerminalEngine:
    """
    Universal Terminal Engine.
    Handles:
    1. Command normalization
    2. SafePatchEngine editing
    3. PTY/Subprocess execution

    NOTE:
    - Path sandboxing is controlled by the module-level SANDBOX_ENABLED flag.
      The CLI toggles this via `gitvisioncli.core.terminal.SANDBOX_ENABLED`.
    """

    def __init__(self, base_dir: Union[str, Path], patch_engine: Any = None):
        # Base directory of the GitVision workspace
        self.base_dir = Path(base_dir).resolve()

        # Initialize working directory BEFORE patch engine
        self._cwd = self.base_dir

        # SafePatchEngine
        self.patch_engine = patch_engine
        if self.patch_engine:
            self.patch_engine.cwd = self._cwd

        # Normalizer (only once)
        self.normalizer = CommandNormalizer(project_root=self.base_dir)

        # Optional callback so higher-level components (Executor) can track
        # directory changes even when `cd` is executed via plain shell.
        self.on_directory_change: Optional[Callable[[Path], None]] = None

        # System info
        self.platform = platform.system()
        self.shell_type = self._detect_shell()

        logger.info(
            f"TerminalEngine initialized at: {self._cwd} "
            f"[{self.platform}/{self.shell_type}]"
        )

    # -----------------------------------------------------------
    # Shell detection
    # -----------------------------------------------------------

    def _detect_shell(self) -> str:
        """
        Detect the default shell based on host OS.

        - Windows  → PowerShell (preferred) or cmd
        - macOS    → zsh
        - Linux    → bash
        """
        if self.platform == "Windows":
            return "powershell" if "PSModulePath" in os.environ else "cmd"

        if self.platform == "Darwin":
            return "zsh"

        # Linux / other Unix
        return "bash"

    # -----------------------------------------------------------
    # Working directory (CWD)
    # -----------------------------------------------------------

    @property
    def cwd(self) -> Path:
        return self._cwd

    @cwd.setter
    def cwd(self, target: Union[str, Path]):
        try:
            if isinstance(target, Path):
                target_path = target
            else:
                target_path = Path(str(target))

            # If absolute → resolve directly
            if target_path.is_absolute():
                new_path = target_path.resolve()
            else:
                # Relative path → inside current cwd
                new_path = (self._cwd / target_path).resolve()

            # SANDBOX: when enabled, restrict navigation to project root
            base = self.base_dir
            if SANDBOX_ENABLED:
                if base not in new_path.parents and new_path != base:
                    raise ValueError(
                        f"Sandbox Violation: Cannot cd outside base root ({base})"
                    )

            if not new_path.exists():
                raise FileNotFoundError(f"Directory not found: {new_path}")

            if not new_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {new_path}")

            # Apply directory
            self._cwd = new_path

            if self.patch_engine:
                self.patch_engine.cwd = self._cwd

            # Notify listeners (e.g., AIActionExecutor) that cwd changed
            if self.on_directory_change:
                try:
                    self.on_directory_change(self._cwd)
                except Exception as cb_err:
                    logger.warning(f"on_directory_change callback failed: {cb_err}")

        except Exception as e:
            raise ValueError(f"Invalid path: {e}")

    # -----------------------------------------------------------
    # STREAM EXECUTION (.run)
    # -----------------------------------------------------------

    def run(self, command: str) -> Generator[str, None, None]:
        command = command.strip()
        if not command:
            return
            yield

        # Cross-shell routing (p./c./l./m. prefixes)
        prefix_info = self._detect_cross_shell_prefix(command)
        if prefix_info is not None:
            env, inner = prefix_info
            yield from self._run_cross_shell_stream(env, inner)
            return

        # Normalize command
        try:
            normalized = self.normalizer.normalize(
                command,
                shell=self.shell_type,
                target_platform=self.platform,
                cwd=self._cwd,
                enforce_sandbox=SANDBOX_ENABLED,
            )
        except ValueError as e:
            yield f"❌ Security/Normalization Error: {e}\n"
            return

        # Edit intent (Structured dict)
        if isinstance(normalized, dict):
            yield from self._handle_edit_intent_stream(normalized)
            return

        # Manual cd handling
        if normalized.startswith("cd "):
            yield from self._handle_cd(normalized)
            return

        # Detect interactive
        is_interactive = any(x in normalized for x in ["git add -p", "python -i", "node"])

        # PTY if available
        if HAS_PTY and is_interactive and self.platform != "Windows":
            yield from self._run_pty(normalized)
        else:
            yield from self._run_subprocess_stream(normalized)

    # -----------------------------------------------------------
    # ATOMIC EXECUTION (.run_once)
    # -----------------------------------------------------------

    def run_once(self, command: str) -> Tuple[int, str, str]:
        command = command.strip()
        if not command:
            return 0, "", ""

        # Cross-shell routing (p./c./l./m. prefixes)
        prefix_info = self._detect_cross_shell_prefix(command)
        if prefix_info is not None:
            env, inner = prefix_info
            return self._run_cross_shell_once(env, inner)

        # Normalize
        try:
            normalized = self.normalizer.normalize(
                command,
                shell=self.shell_type,
                target_platform=self.platform,
                cwd=self._cwd,
                enforce_sandbox=SANDBOX_ENABLED,
            )
        except ValueError as e:
            return 1, "", f"Security Error: {e}"

        # Edit Intent
        if isinstance(normalized, dict):
            return self._handle_edit_intent_atomic(normalized)

        # cd handling
        if normalized.startswith("cd "):
            try:
                self._handle_cd_atomic(normalized)
                return 0, f"Changed directory to {self.cwd}", ""
            except Exception as e:
                return 1, "", str(e)

        # Safe shell run
        try:
            result = subprocess.run(
                normalized,
                cwd=str(self._cwd),
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return result.returncode, result.stdout, result.stderr

        except Exception as e:
            return 1, "", str(e)

    # -----------------------------------------------------------
    # INTERNAL HANDLERS
    # -----------------------------------------------------------

    def _handle_edit_intent_stream(
        self, intent: Dict[str, Any]
    ) -> Generator[str, None, None]:

        if not self.patch_engine:
            yield "❌ SafePatchEngine not connected.\n"
            return

        result = self.patch_engine.apply_intent(intent)

        if result.get("success"):
            yield f"✅ Edited: {intent.get('path')}\n"
            if result.get("backup"):
                yield f"   Backup: {result['backup']}\n"
        else:
            yield f"❌ Edit failed: {result.get('error')}\n"

    def _handle_edit_intent_atomic(
        self, intent: Dict[str, Any]
    ) -> Tuple[int, str, str]:

        if not self.patch_engine:
            return 1, "", "SafePatchEngine not connected."

        result = self.patch_engine.apply_intent(intent)

        if result.get("success"):
            msg = f"Edited {intent.get('path')}"
            if result.get("backup"):
                msg += f" (Backup: {result['backup']})"
            return 0, msg, ""

        return 1, "", result.get("error", "Unknown error")

    # ---------------- CD --------------------

    def _handle_cd(self, command: str):
        try:
            target = command.split(" ", 1)[1].strip()
            target = target.strip('"').strip("'")
            if not target:
                target = str(self.base_dir)

            self.cwd = target
            yield f"➜ PWD: {self.cwd}\n"
        except Exception as e:
            yield f"❌ cd error: {e}\n"

    def _handle_cd_atomic(self, command: str):
        target = command.split(" ", 1)[1].strip()
        target = target.strip('"').strip("'")
        if not target:
            target = str(self.base_dir)
        self.cwd = target

    # ---------------- Subprocess --------------------

    def _run_subprocess_stream(self, command: str):
        try:
            proc = subprocess.Popen(
                command,
                cwd=str(self._cwd),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in proc.stdout:
                yield line
            proc.wait()
        except Exception as e:
            yield f"❌ Exec Error: {e}\n"

    # ---------------- PTY --------------------

    def _run_pty(self, command: str):
        if not HAS_PTY:
            yield from self._run_subprocess_stream(command)
            return

        try:
            master_fd, slave_fd = pty.openpty()
            pid = os.fork()

            if pid == 0:  # child
                os.chdir(str(self._cwd))
                argv = shlex.split(command)
                os.execvp(argv[0], argv)

            else:  # parent
                os.close(slave_fd)
                while True:
                    try:
                        data = os.read(master_fd, 1024)
                        if not data:
                            break
                        yield data.decode("utf-8", errors="replace")
                    except OSError:
                        break

                os.close(master_fd)
                os.waitpid(pid, 0)

        except Exception as e:
            yield f"❌ PTY Error: {e}\n"

    # -----------------------------------------------------------
    # CROSS-OS SHELL ROUTING
    # -----------------------------------------------------------

    def _detect_cross_shell_prefix(self, command: str) -> Optional[Tuple[str, str]]:
        """
        Detects prefix-based execution:
          p.* -> PowerShell
          c.* -> Windows CMD
          l.* -> Linux bash
          m.* -> macOS zsh
        Returns (env_key, inner_command) or None.
        """
        stripped = command.strip()
        if len(stripped) < 3:
            return None

        # Expect form: "<prefix>.<command>"
        prefix = stripped[0].lower()
        if stripped[1] != ".":
            return None

        inner = stripped[2:].strip()
        if not inner:
            return None

        if prefix in {"p", "c", "l", "m"}:
            return prefix, inner
        return None

    def _run_cross_shell_once(self, env: str, inner: str) -> Tuple[int, str, str]:
        """
        Execute a command in a cross-OS shell environment.
        If the target shell is unavailable, return a standardized error.
        """
        try:
            if env == "p":
                # PowerShell
                shell_bin = shutil.which("pwsh") or shutil.which("powershell")
                if not shell_bin:
                    return (
                        127,
                        "",
                        "Cross-shell 'powershell' is not available on this system (requested via 'p.*').",
                    )
                cmd = [shell_bin, "-NoLogo", "-NoProfile", "-Command", inner]
            elif env == "c":
                # Windows CMD
                shell_bin = shutil.which("cmd") or shutil.which("cmd.exe")
                if not shell_bin:
                    return (
                        127,
                        "",
                        "Cross-shell 'cmd' is not available on this system (requested via 'c.*').",
                    )
                cmd = [shell_bin, "/C", inner]
            elif env == "l":
                # Linux bash
                shell_bin = shutil.which("bash")
                if not shell_bin:
                    return (
                        127,
                        "",
                        "Cross-shell 'bash' is not available on this system (requested via 'l.*').",
                    )
                cmd = [shell_bin, "-lc", inner]
            else:  # env == "m"
                # macOS zsh
                shell_bin = shutil.which("zsh")
                if not shell_bin:
                    return (
                        127,
                        "",
                        "Cross-shell 'zsh' is not available on this system (requested via 'm.*').",
                    )
                cmd = [shell_bin, "-lc", inner]

            result = subprocess.run(
                cmd,
                cwd=str(self._cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", f"Cross-shell execution error: {e}"

    def _run_cross_shell_stream(self, env: str, inner: str) -> Generator[str, None, None]:
        """
        Streaming variant of cross-shell execution.
        """
        code, out, err = self._run_cross_shell_once(env, inner)
        if out:
            yield out
        if err:
            yield err
