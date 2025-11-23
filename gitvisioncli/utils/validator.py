# gitvisioncli/utils/validator.py
import re
from pathlib import Path
from typing import Any, Dict
import json


class Validator:
    """Input validators used across GitVision."""

    # Allows letters, numbers, underscores, and hyphens. 1-64 chars.
    _name_pattern = re.compile(r"[A-Za-z0-9_\-]{1,64}")
    # Standard Python identifier (letters, numbers, underscores, starting with letter or _).
    _identifier_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Valid project/module name."""
        return bool(Validator._name_pattern.fullmatch(name))

    @staticmethod
    def file_exists(path: str) -> bool:
        """Check if a file or directory exists at the path."""
        return Path(path).exists()

    @staticmethod
    def is_directory(path: str) -> bool:
        """Check if the path is a directory."""
        return Path(path).is_dir()

    @staticmethod
    def is_valid_json(data: str) -> bool:
        """Check if a string is valid JSON."""
        try:
            json.loads(data)
            return True
        except Exception:
            return False

    @staticmethod
    def is_python_identifier(name: str) -> bool:
        """Check if a string is a valid Python identifier."""
        return bool(Validator._identifier_pattern.fullmatch(name))

    @staticmethod
    def ensure_git_repo(path: str) -> bool:
        """Check if a .git directory exists at the path."""
        return (Path(path) / ".git").is_dir()