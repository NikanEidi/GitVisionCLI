"""
Base Plugin Interface

Abstract base class for all plugins.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    description: str
    author: Optional[str] = None
    dependencies: Optional[List[str]] = None


class BasePlugin(ABC):
    """
    Abstract base class for all plugins.
    
    Plugins extend GitVisionCLI functionality in a modular way.
    Each plugin can:
    - Register commands
    - Hook into action execution
    - Provide custom UI components
    - Extend the natural language engine
    """
    
    def __init__(self, metadata: PluginMetadata):
        """
        Initialize plugin.
        
        Args:
            metadata: Plugin metadata
        """
        self.metadata = metadata
        self.enabled = True
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        Initialize plugin with application context.
        
        Args:
            context: Application context (supervisor, executor, etc.)
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    def can_handle(self, command: str, context: Dict[str, Any]) -> bool:
        """
        Check if plugin can handle a command.
        
        Args:
            command: Command string
            context: Command context
        
        Returns:
            True if plugin can handle the command
        """
        return False
    
    def handle_command(self, command: str, params: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle a command.
        
        Args:
            command: Command string
            params: Command parameters
            context: Command context
        
        Returns:
            Action result or None if not handled
        """
        return None
    
    def get_commands(self) -> List[str]:
        """
        Get list of commands this plugin handles.
        
        Returns:
            List of command strings
        """
        return []
    
    def get_help(self) -> str:
        """
        Get help text for this plugin.
        
        Returns:
            Help text string
        """
        return f"{self.metadata.name} v{self.metadata.version}\n{self.metadata.description}"

