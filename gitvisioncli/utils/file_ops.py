# gitvisioncli/utils/file_ops.py
from pathlib import Path
import json
import shutil
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger("GitVision.FileOps")


class FileOps:
    """High-level, safe file operations used across GitVisionCLI."""

    # --------------------------------------------------------
    # Basic Read / Write
    # --------------------------------------------------------
    @staticmethod
    def read(path: str, encoding="utf-8") -> Optional[str]:
        try:
            p = Path(path)
            if not p.exists():
                return None
            return p.read_text(encoding=encoding)
        except Exception as e:
            logger.error(f"[read] Failed to read {path}: {e}")
            return None

    @staticmethod
    def write(path: str, content: str, encoding="utf-8") -> bool:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding=encoding)
            return True
        except Exception as e:
            logger.error(f"[write] Failed to write {path}: {e}")
            return False

    @staticmethod
    def append(path: str, content: str, encoding="utf-8") -> bool:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"[append] Failed to append to {path}: {e}")
            return False

    # --------------------------------------------------------
    # File / Directory Management
    # --------------------------------------------------------
    @staticmethod
    def delete(path: str) -> bool:
        try:
            p = Path(path)
            if not p.exists():
                return False
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return True
        except Exception as e:
            logger.error(f"[delete] Failed to delete {path}: {e}")
            return False

    @staticmethod
    def copy(src: str, dst: str) -> bool:
        try:
            src_p = Path(src)
            dst_p = Path(dst)
            dst_p.parent.mkdir(parents=True, exist_ok=True)

            if not src_p.exists():
                logger.error(f"[copy] Source does not exist: {src}")
                return False

            if src_p.is_dir():
                shutil.copytree(src_p, dst_p, dirs_exist_ok=True)
            else:
                shutil.copy2(src_p, dst_p)
            return True
        except Exception as e:
            logger.error(f"[copy] Failed to copy {src} → {dst}: {e}")
            return False

    @staticmethod
    def move(src: str, dst: str) -> bool:
        try:
            src_p = Path(src)
            dst_p = Path(dst)
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_p), str(dst_p))
            return True
        except Exception as e:
            logger.error(f"[move] Failed to move {src} → {dst}: {e}")
            return False

    # --------------------------------------------------------
    # Listing
    # --------------------------------------------------------
    @staticmethod
    def list_files(path: str) -> List[str]:
        try:
            p = Path(path)
            if not p.exists():
                return []
            return [str(f) for f in p.rglob("*") if f.is_file()]
        except Exception as e:
            logger.error(f"[list_files] Error listing files in {path}: {e}")
            return []

    @staticmethod
    def list_dirs(path: str) -> List[str]:
        try:
            p = Path(path)
            if not p.exists():
                return []
            return [str(f) for f in p.rglob("*") if f.is_dir()]
        except Exception as e:
            logger.error(f"[list_dirs] Error listing dirs in {path}: {e}")
            return []

    # --------------------------------------------------------
    # JSON Helpers
    # --------------------------------------------------------
    @staticmethod
    def read_json(path: str) -> Optional[Dict[str, Any]]:
        try:
            p = Path(path)
            if not p.exists():
                return None
            return json.loads(p.read_text())
        except Exception as e:
            logger.error(f"[read_json] Failed to read JSON {path}: {e}")
            return None

    @staticmethod
    def write_json(path: str, data: Dict[str, Any]) -> bool:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, indent=2))
            return True
        except Exception as e:
            logger.error(f"[write_json] Failed to write JSON {path}: {e}")
            return False