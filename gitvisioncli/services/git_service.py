"""
Git Service

Service class for Git operations.
Refactored from utils/git_detect.py with OOP principles.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("GitVision.GitService")


class GitService:
    """
    Service class for Git operations.
    
    Provides utilities for:
    - Detecting Git repositories
    - Getting Git information
    - Checking Git installation
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize Git service.
        
        Args:
            base_dir: Base directory for Git operations
        """
        self.base_dir = Path(base_dir).resolve() if base_dir else None
        logger.info(f"GitService initialized (base_dir: {self.base_dir})")
    
    @staticmethod
    def is_git_repo(path: Path) -> bool:
        """
        Check if path is a Git repository.
        
        Args:
            path: Path to check
        
        Returns:
            True if Git repository
        """
        return (Path(path) / ".git").is_dir()
    
    @staticmethod
    def current_branch(path: Path) -> Optional[str]:
        """
        Get current Git branch.
        
        Args:
            path: Repository path
        
        Returns:
            Branch name or None
        """
        return GitService._run_command("git rev-parse --abbrev-ref HEAD", cwd=path)
    
    @staticmethod
    def remote_url(path: Path, remote: str = "origin") -> Optional[str]:
        """
        Get remote URL.
        
        Args:
            path: Repository path
            remote: Remote name
        
        Returns:
            Remote URL or None
        """
        return GitService._run_command(f"git config --get remote.{remote}.url", cwd=path)
    
    @staticmethod
    def last_commit(path: Path) -> Optional[str]:
        """
        Get last commit SHA.
        
        Args:
            path: Repository path
        
        Returns:
            Commit SHA or None
        """
        return GitService._run_command("git rev-parse HEAD", cwd=path)
    
    @staticmethod
    def git_installed() -> bool:
        """
        Check if Git is installed.
        
        Returns:
            True if Git is available
        """
        return GitService._run_command("git --version") is not None
    
    @staticmethod
    def _run_command(cmd: str, cwd: Optional[Path] = None, timeout: int = 3) -> Optional[str]:
        """
        Run Git command.
        
        Args:
            cmd: Command to run
            cwd: Working directory
            timeout: Command timeout
        
        Returns:
            Command output or None
        """
        try:
            result = subprocess.run(
                cmd.split(),
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return result.stdout.strip()
            logger.debug(f"Git command failed ({cmd}): {result.stderr.strip()}")
            return None
        except Exception as e:
            logger.error(f"Git command error ({cmd}): {e}")
            return None

