"""
File Service

Service class for file operations.
Refactored from utils/file_ops.py with OOP principles.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import shutil

logger = logging.getLogger("GitVision.FileService")


class FileService:
    """
    Service class for file operations.
    
    Provides high-level, safe file operations with:
    - Error handling
    - Validation
    - Atomic operations
    - Logging
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize file service.
        
        Args:
            base_dir: Base directory for operations (optional)
        """
        self.base_dir = Path(base_dir).resolve() if base_dir else None
        logger.info(f"FileService initialized (base_dir: {self.base_dir})")
    
    def read(self, path: str, encoding: str = "utf-8") -> Optional[str]:
        """
        Read file content.
        
        Args:
            path: File path
            encoding: File encoding
        
        Returns:
            File content or None if error
        """
        try:
            p = self._resolve_path(path)
            if not p.exists():
                logger.warning(f"File not found: {path}")
                return None
            return p.read_text(encoding=encoding)
        except Exception as e:
            logger.error(f"Failed to read {path}: {e}")
            return None
    
    def write(self, path: str, content: str, encoding: str = "utf-8") -> bool:
        """
        Write file content.
        
        Args:
            path: File path
            content: Content to write
            encoding: File encoding
        
        Returns:
            True if successful
        """
        try:
            p = self._resolve_path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding=encoding)
            logger.debug(f"File written: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write {path}: {e}")
            return False
    
    def append(self, path: str, content: str, encoding: str = "utf-8") -> bool:
        """
        Append to file.
        
        Args:
            path: File path
            content: Content to append
            encoding: File encoding
        
        Returns:
            True if successful
        """
        try:
            p = self._resolve_path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding=encoding) as f:
                f.write(content)
            logger.debug(f"Content appended to: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to append to {path}: {e}")
            return False
    
    def delete(self, path: str) -> bool:
        """
        Delete file or directory.
        
        Args:
            path: Path to delete
        
        Returns:
            True if successful
        """
        try:
            p = self._resolve_path(path)
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p)
            else:
                logger.warning(f"Path does not exist: {path}")
                return False
            logger.debug(f"Deleted: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            return False
    
    def exists(self, path: str) -> bool:
        """
        Check if path exists.
        
        Args:
            path: Path to check
        
        Returns:
            True if exists
        """
        p = self._resolve_path(path)
        return p.exists()
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        p = self._resolve_path(path)
        return p.is_file()
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory."""
        p = self._resolve_path(path)
        return p.is_dir()
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve path relative to base_dir if set.
        
        Args:
            path: Path to resolve
        
        Returns:
            Resolved Path object
        """
        p = Path(path)
        if self.base_dir and not p.is_absolute():
            return (self.base_dir / p).resolve()
        return p.resolve()
    
    def read_json(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Read JSON file.
        
        Args:
            path: JSON file path
        
        Returns:
            Parsed JSON or None if error
        """
        content = self.read(path)
        if content is None:
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON {path}: {e}")
            return None
    
    def write_json(self, path: str, data: Dict[str, Any], indent: int = 2) -> bool:
        """
        Write JSON file.
        
        Args:
            path: JSON file path
            data: Data to write
            indent: JSON indentation
        
        Returns:
            True if successful
        """
        try:
            content = json.dumps(data, indent=indent)
            return self.write(path, content)
        except Exception as e:
            logger.error(f"Failed to write JSON {path}: {e}")
            return False

