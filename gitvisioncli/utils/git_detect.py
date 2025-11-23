# gitvisioncli/utils/git_detect.py
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger("GitVision.GitDetect")


class GitDetect:
    """Utilities for detecting Git repository info and states."""

    @staticmethod
    def _run(cmd: str, cwd: Optional[str] = None) -> Optional[str]:
        try:
            result = subprocess.run(
                cmd.split(),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=3,
                encoding='utf-8' # Explicitly set encoding
            )
            if result.returncode == 0:
                return result.stdout.strip()
            # Use debug level for failed checks, as they can be noisy
            logger.debug(f"[git] Cmd failed ({cmd}): {result.stderr.strip()}")
            return None
        except Exception as e:
            logger.error(f"[git] Command error ({cmd}): {e}")
            return None

    @staticmethod
    def is_git_repo(path: str) -> bool:
        """Checks if the given path is the root of a git repository."""
        return (Path(path) / ".git").is_dir()

    @staticmethod
    def current_branch(path: str) -> Optional[str]:
        """Gets the current active branch name."""
        return GitDetect._run("git rev-parse --abbrev-ref HEAD", cwd=path)

    @staticmethod
    def remote_url(path: str) -> Optional[str]:
        """Gets the URL of the 'origin' remote."""
        return GitDetect._run("git config --get remote.origin.url", cwd=path)

    @staticmethod
    def last_commit(path: str) -> Optional[str]:
        """Gets the SHA of the last commit."""
        return GitDetect._run("git rev-parse HEAD", cwd=path)

    @staticmethod
    def git_installed() -> bool:
        """Checks if the 'git' command is available in the system PATH."""
        return GitDetect._run("git --version") is not None