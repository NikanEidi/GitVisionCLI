# gitvisioncli/workspace/fs_watcher.py
"""
File System Watcher — Real-time file change detection
Uses polling + manual triggers to update Editor/Tree panels immediately.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Set, Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class FileChange:
    """Represents a detected file system change."""
    path: Path
    change_type: str  # 'created', 'modified', 'deleted', 'editor_close', 'ai_modify'
    timestamp: datetime


class FileSystemWatcher:
    """
    Monitors a directory by polling for mtime/hash changes.
    Also supports manual triggers from Executor (editor_close, ai_modify).
    """

    def __init__(self, base_dir: str, poll_interval: float = 1.0):
        self.base_dir = Path(base_dir).resolve()
        self.poll_interval = poll_interval
        self.is_watching = False 
        
        # File state tracking
        self.file_snapshots: Dict[Path, str] = {}
        self.file_mtimes: Dict[Path, float] = {}

        # Ignore rules
        self.ignore_dirs = {
            '.git', '__pycache__', 'node_modules', '.gitvision_backup',
            '.venv', 'venv', '.egg-info', 'dist', 'build', '.pytest_cache'
        }
        self.ignore_exts = {
            '.pyc', '.pyo', '.log', '.tmp', '.swo', '.swp', '.DS_Store'
        }

        # Subscribers — UI Panels register here
        self.on_change_callbacks: List[Callable[[FileChange], None]] = []

        logger.info(f"FSWatcher: Initializing baseline scan for {self.base_dir}")
        self._scan_directory()

    # ----------------------------------------------------------------------
    # Manual triggers from Executor (AI modify, editor close)
    # ----------------------------------------------------------------------
    def manual_trigger(self, change_type: str = "manual"):
        """
        Called when Executor modifies files or editor closes.
        Forces all UI refresh callbacks to run immediately.
        """
        dummy_change = FileChange(
            path=self.base_dir,
            change_type=change_type,
            timestamp=datetime.now()
        )

        logger.info(f"FSWatcher: manual trigger = {change_type}")

        for cb in self.on_change_callbacks:
            try:
                cb(dummy_change)
            except Exception as e:
                logger.error(f"Manual FSWatcher callback error: {e}")

    # ----------------------------------------------------------------------
    def register_callback(self, callback: Callable[[FileChange], None]):
        """
        Panels register themselves so they can refresh when FS changes.
        """
        self.on_change_callbacks.append(callback)
    
    def _should_ignore(self, path: Path) -> bool:
        if path.suffix in self.ignore_exts:
            return True
        for part in path.parts:
            if part in self.ignore_dirs:
                return True
        return False

    def _get_file_hash(self, file_path: Path) -> str:
        try:
            with open(file_path, 'rb') as f:
                hash_md5 = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
                return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Could not hash file {file_path}: {e}")
            return ""

    def _custom_file_walker(self, dir_path: Path) -> List[Path]:
        """
        Recursively collects all files except ignored paths.
        """
        files = []
        try:
            for entry in dir_path.iterdir():
                if entry.is_dir() and entry.name not in self.ignore_dirs:
                    files.extend(self._custom_file_walker(entry))
                elif entry.is_file() and not self._should_ignore(entry):
                    files.append(entry)
        except Exception as e:
            logger.warning(f"Cannot scan {dir_path}: {e}")
        return files

    def _scan_directory(self):
        """Creates initial snapshot of all files."""
        self.file_mtimes.clear()
        self.file_snapshots.clear()
        for file_path in self._custom_file_walker(self.base_dir):
            try:
                mtime = file_path.stat().st_mtime
                self.file_mtimes[file_path] = mtime
                self.file_snapshots[file_path] = self._get_file_hash(file_path)
            except Exception as e:
                logger.warning(f"Could not scan file {file_path}: {e}")

    # ----------------------------------------------------------------------
    # Detect real file changes (OS-level)
    # ----------------------------------------------------------------------
    def _detect_changes(self) -> List[FileChange]:
        changes = []
        current_files = set()

        for file_path in self._custom_file_walker(self.base_dir):
            current_files.add(file_path)
            try:
                current_mtime = file_path.stat().st_mtime
                old_mtime = self.file_mtimes.get(file_path)

                # NEW FILE
                if old_mtime is None:
                    current_hash = self._get_file_hash(file_path)
                    changes.append(FileChange(file_path, 'created', datetime.now()))
                    self.file_mtimes[file_path] = current_mtime
                    self.file_snapshots[file_path] = current_hash

                # MODIFIED FILE
                elif current_mtime != old_mtime:
                    current_hash = self._get_file_hash(file_path)
                    if self.file_snapshots.get(file_path) != current_hash:
                        changes.append(FileChange(file_path, 'modified', datetime.now()))
                        self.file_snapshots[file_path] = current_hash
                    self.file_mtimes[file_path] = current_mtime

            except Exception as e:
                logger.warning(f"Could not check file {file_path}: {e}")

        # DELETED FILES
        deleted_files = set(self.file_mtimes.keys()) - current_files
        for file_path in deleted_files:
            changes.append(FileChange(file_path, 'deleted', datetime.now()))
            self.file_mtimes.pop(file_path, None)
            self.file_snapshots.pop(file_path, None)

        return changes

    # ----------------------------------------------------------------------
    # Core Watcher Loop
    # ----------------------------------------------------------------------
    def start(self):
        self.is_watching = True
        logger.info("FSWatcher enabled.")

    def stop(self):
        self.is_watching = False
        logger.info("FSWatcher disabled.")

    def update_base_dir(self, new_base_dir: Path):
        new_dir = Path(new_base_dir).resolve()
        if new_dir == self.base_dir:
            return
        self.base_dir = new_dir
        self._scan_directory()

    def check_once(self) -> List[FileChange]:
        """
        Called by main loop — detects real file OS-level changes.
        """
        if not self.is_watching:
            return []
        
        changes = self._detect_changes()

        for change in changes:
            for cb in self.on_change_callbacks:
                try:
                    cb(change)
                except Exception as e:
                    logger.error(f"FSWatcher callback error: {e}")

        return changes