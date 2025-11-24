"""
Base UI Component

Abstract base class for all UI components.
Implements component pattern for modular UI architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class ComponentConfig:
    """Configuration for UI components."""
    width: int = 80
    height: int = 24
    enabled: bool = True
    visible: bool = True
    style: Optional[Dict[str, Any]] = None


class BaseComponent(ABC):
    """
    Abstract base class for all UI components.
    
    All UI components inherit from this class, providing:
    - Consistent interface
    - Configuration management
    - Lifecycle methods
    - Event handling
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        """
        Initialize the component.
        
        Args:
            config: Component configuration
        """
        self.config = config or ComponentConfig()
        self._initialized = False
    
    @abstractmethod
    def render(self) -> str:
        """
        Render the component.
        
        Returns:
            Rendered component as string
        """
        pass
    
    def initialize(self) -> None:
        """Initialize the component (called once)."""
        if not self._initialized:
            self._on_initialize()
            self._initialized = True
    
    def _on_initialize(self) -> None:
        """Override for custom initialization logic."""
        pass
    
    def update_config(self, **kwargs) -> None:
        """
        Update component configuration.
        
        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def is_enabled(self) -> bool:
        """Check if component is enabled."""
        return self.config.enabled
    
    def is_visible(self) -> bool:
        """Check if component is visible."""
        return self.config.visible
    
    def get_width(self) -> int:
        """Get component width."""
        return self.config.width
    
    def get_height(self) -> int:
        """Get component height."""
        return self.config.height

