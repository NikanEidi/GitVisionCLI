"""
Validation Service

Service class for validation operations.
Refactored from utils/validator.py with OOP principles.
"""

import re
import logging
from pathlib import Path
from typing import Optional, List, Callable, Dict, Any

logger = logging.getLogger("GitVision.ValidationService")


class ValidationService:
    """
    Service class for validation operations.
    
    Provides:
    - Path validation
    - File validation
    - Content validation
    - Custom validators
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize validation service.
        
        Args:
            base_dir: Base directory for path validation
        """
        self.base_dir = Path(base_dir).resolve() if base_dir else None
        self._validators: Dict[str, Callable] = {}
    
    def validate_path(self, path: str, must_exist: bool = False) -> bool:
        """
        Validate file path.
        
        Args:
            path: Path to validate
            must_exist: Whether path must exist
        
        Returns:
            True if valid
        """
        try:
            p = Path(path)
            if self.base_dir and not p.is_absolute():
                p = (self.base_dir / p).resolve()
            
            if must_exist and not p.exists():
                return False
            
            # Check if path is within base_dir
            if self.base_dir:
                try:
                    p.relative_to(self.base_dir)
                except ValueError:
                    return False
            
            return True
        except Exception:
            return False
    
    def validate_file_extension(self, path: str, allowed: List[str]) -> bool:
        """
        Validate file extension.
        
        Args:
            path: File path
            allowed: List of allowed extensions
        
        Returns:
            True if extension is allowed
        """
        p = Path(path)
        ext = p.suffix.lower()
        return ext in [e.lower() if not e.startswith(".") else e.lower() for e in allowed]
    
    def register_validator(self, name: str, validator: Callable) -> None:
        """
        Register custom validator.
        
        Args:
            name: Validator name
            validator: Validator function
        """
        self._validators[name] = validator
    
    def validate(self, name: str, value: Any) -> bool:
        """
        Run custom validator.
        
        Args:
            name: Validator name
            value: Value to validate
        
        Returns:
            True if validation passes
        """
        if name not in self._validators:
            logger.warning(f"Validator '{name}' not found")
            return False
        try:
            return self._validators[name](value)
        except Exception as e:
            logger.error(f"Validator '{name}' error: {e}")
            return False

