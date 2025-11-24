"""
Plugin Registry

Manages plugin registration and discovery.
"""

import logging
from typing import Dict, List, Type, Optional
from pathlib import Path

from gitvisioncli.plugins.base_plugin import BasePlugin, PluginMetadata

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for managing plugins.
    
    Supports:
    - Dynamic plugin registration
    - Plugin discovery
    - Plugin dependency resolution
    """
    
    def __init__(self):
        """Initialize plugin registry."""
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_classes: Dict[str, Type[BasePlugin]] = {}
    
    def register(self, plugin: BasePlugin) -> None:
        """
        Register a plugin instance.
        
        Args:
            plugin: Plugin instance
        """
        name = plugin.metadata.name
        if name in self._plugins:
            logger.warning(f"Plugin {name} already registered, overwriting")
        self._plugins[name] = plugin
        logger.info(f"Registered plugin: {name} v{plugin.metadata.version}")
    
    def register_class(self, plugin_class: Type[BasePlugin], metadata: PluginMetadata) -> None:
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class
            metadata: Plugin metadata
        """
        name = metadata.name
        self._plugin_classes[name] = plugin_class
        logger.info(f"Registered plugin class: {name}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Get plugin by name.
        
        Args:
            name: Plugin name
        
        Returns:
            Plugin instance or None
        """
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> List[BasePlugin]:
        """
        Get all registered plugins.
        
        Returns:
            List of plugin instances
        """
        return list(self._plugins.values())
    
    def get_enabled_plugins(self) -> List[BasePlugin]:
        """
        Get all enabled plugins.
        
        Returns:
            List of enabled plugin instances
        """
        return [p for p in self._plugins.values() if p.enabled]
    
    def unregister(self, name: str) -> None:
        """
        Unregister a plugin.
        
        Args:
            name: Plugin name
        """
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.cleanup()
            del self._plugins[name]
            logger.info(f"Unregistered plugin: {name}")
    
    def discover_plugins(self, plugin_dir: Path) -> List[str]:
        """
        Discover plugins in a directory.
        
        Args:
            plugin_dir: Directory to search
        
        Returns:
            List of discovered plugin names
        """
        discovered = []
        if not plugin_dir.exists():
            return discovered
        
        # Look for Python files in plugin directory
        for file_path in plugin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            # Try to import and discover plugins
            # This is a simplified version - full implementation would use importlib
            discovered.append(file_path.stem)
        
        return discovered

