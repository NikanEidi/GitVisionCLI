"""
Configuration Service

Modular service for configuration management.
Refactored to use service pattern.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from gitvisioncli.services.config_service import ConfigService

logger = logging.getLogger(__name__)

# Legacy compatibility - maintain original interface
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

# Global config service instance
_config_service: Optional[ConfigService] = None


def _get_config_service() -> ConfigService:
    """Get or create global config service instance."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService(config_path=CONFIG_PATH)
    return _config_service


def load_config() -> Dict[str, Any]:
    """
    Loads config.json from gitvisioncli/config/
    Returns a Python dictionary.
    Raises FileNotFoundError if missing.
    
    Legacy function - now uses ConfigService.
    """
    service = _get_config_service()
    return service.load()


def save_config(data: Dict[str, Any]) -> None:
    """
    Write configuration back to config.json.
    
    Legacy function - now uses ConfigService.
    """
    service = _get_config_service()
    service.save(data)