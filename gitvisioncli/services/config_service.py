"""
Configuration Service

Service class for configuration management.
Refactored from config/settings.py with OOP principles.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("GitVision.ConfigService")


class ConfigService:
    """
    Service class for configuration management.
    
    Provides:
    - Configuration loading
    - Configuration saving
    - Configuration validation
    - Default values
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config service.
        
        Args:
            config_path: Path to config file
        """
        if config_path is None:
            # Default config path
            config_path = Path.home() / ".gitvision" / "config.json"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        
        # Try to load config, but don't fail if it doesn't exist
        try:
            if self.config_path.exists():
                self._load_config()
        except Exception:
            # Config will be empty, which is fine for initialization
            self._config = {}
    
    def _load_config(self) -> None:
        """Load configuration from file (internal method)."""
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {}
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid JSON
        """
        if not self.config_path.exists():
            logger.error(f"Config file not found at: {self.config_path}")
            raise FileNotFoundError(
                f"Config file not found at: {self.config_path}\n"
                "Please create config.json with your 'api_key' and 'github' token."
            )
        
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return self._config.copy()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config.json: {e}")
            raise ValueError(
                f"Error parsing config.json: {e}\n"
                "Please ensure config.json is valid JSON."
            )
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def save(self, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            data: Optional data to save (uses internal config if None)
        
        Returns:
            True if successful
        """
        try:
            if data is not None:
                self._config = data
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with self.config_path.open("w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def save_config(self) -> bool:
        """
        Save configuration to file (legacy method).
        
        Returns:
            True if successful
        """
        return self.save()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation: "openai.api_key")
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with multiple values.
        
        Args:
            updates: Dictionary of updates
        """
        self._config.update(updates)

