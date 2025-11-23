
import os
from pathlib import Path
from typing import Optional, Union

def resolve_base_dir(
    cli_arg: Optional[str] = None,
    config_val: Optional[str] = None,
    cwd: Optional[Union[str, Path]] = None
) -> Path:
    """
    Resolves the absolute base directory for the workspace.
    
    Priority:
    1. CLI argument (--dir)
    2. Config value
    3. Current working directory (cwd)
    
    Returns:
        Path: Absolute, resolved path to the workspace root.
    """
    path_str = cli_arg or config_val
    
    if path_str:
        # Expand user (~) and resolve absolute path
        target = Path(path_str).expanduser().resolve()
    else:
        # Default to CWD
        target = Path(cwd or os.getcwd()).resolve()
        
    return target

def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """
    Verifies that target_path is within base_dir or is base_dir itself.
    Prevents path traversal attacks.
    """
    try:
        # Resolve both to absolute paths
        base = base_dir.resolve()
        target = target_path.resolve()
        
        # Check if target starts with base
        return str(target).startswith(str(base))
    except Exception:
        return False
