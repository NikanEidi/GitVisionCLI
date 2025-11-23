"""
Persistent memory / brain system for GitVision.

This module stores a small amount of non-sensitive, per-project
configuration and preferences in a JSON file under ~/.gitvision.
It is explicitly forbidden from storing raw code or secrets.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


@dataclass
class Brain:
    """
    Lightweight key/value store with project isolation.

    Keys are always scoped by a project identifier derived from the
    workspace root path. Values must be JSON-serializable and MUST NOT
    contain source code or secrets.
    """

    base_dir: Path
    storage_dir: Path = field(
        default_factory=lambda: Path(os.path.expanduser("~/.gitvision"))
    )
    filename: str = "brain.json"

    def __post_init__(self) -> None:
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Brain: failed to create storage dir: {e}")
        self._data: Dict[str, Dict[str, Any]] = {}
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @property
    def _path(self) -> Path:
        return self.storage_dir / self.filename

    def _project_key(self) -> str:
        """
        Stable project identifier derived from the workspace root path.
        """
        try:
            return str(self.base_dir.resolve())
        except Exception:
            return str(self.base_dir)

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        if not self._path.exists():
            self._data = {}
            return

        try:
            raw = self._path.read_text(encoding="utf-8")
            obj = json.loads(raw)
            if isinstance(obj, dict):
                self._data = obj
            else:
                self._data = {}
        except Exception as e:
            logger.warning(f"Brain: failed to load memory file: {e}")
            self._data = {}

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Brain: failed to save memory file: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def remember(self, key: str, value: Any) -> None:
        """
        Persist a small, non-sensitive value under the given key for the
        current project.
        """
        self._load()
        project = self._project_key()
        project_bucket = self._data.setdefault(project, {})
        project_bucket[key] = value
        self._save()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieve a value for the current project, or default if not set.
        """
        self._load()
        project = self._project_key()
        return (self._data.get(project) or {}).get(key, default)

    def forget(self, key: str) -> None:
        """
        Remove a value for the current project.
        """
        self._load()
        project = self._project_key()
        bucket = self._data.get(project)
        if not bucket or key not in bucket:
            return
        bucket.pop(key, None)
        self._save()

