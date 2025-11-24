"""
Plugin Manager

Orchestrates plugin lifecycle and command routing.
"""

import logging
from typing import Dict, Any, List, Optional

from gitvisioncli.plugins.registry import PluginRegistry
from gitvisioncli.plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages plugin lifecycle and command routing.
    
    Responsibilities:
    - Initialize plugins
    - Route commands to plugins
    - Manage plugin dependencies
    - Handle plugin errors gracefully
    """
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        """
        Initialize plugin manager.
        
        Args:
            registry: Optional plugin registry (creates new if not provided)
        """
        self.registry = registry or PluginRegistry()
        self._initialized = False
    
    def initialize_plugins(self, context: Dict[str, Any]) -> None:
        """
        Initialize all registered plugins.
        
        Args:
            context: Application context
        """
        if self._initialized:
            logger.warning("Plugins already initialized")
            return
        
        for plugin in self.registry.get_all_plugins():
            try:
                plugin.initialize(context)
                logger.info(f"Initialized plugin: {plugin.metadata.name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin.metadata.name}: {e}", exc_info=True)
                plugin.enabled = False
        
        self._initialized = True
    
    def route_command(self, command: str, params: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Route command to appropriate plugin.
        
        Args:
            command: Command string
            params: Command parameters
            context: Command context
        
        Returns:
            Action result or None if no plugin handled it
        """
        for plugin in self.registry.get_enabled_plugins():
            try:
                if plugin.can_handle(command, context):
                    result = plugin.handle_command(command, params, context)
                    if result is not None:
                        return result
            except Exception as e:
                logger.error(f"Plugin {plugin.metadata.name} error handling command: {e}", exc_info=True)
        
        return None
    
    def get_all_commands(self) -> List[str]:
        """
        Get all commands from all plugins.
        
        Returns:
            List of command strings
        """
        commands = []
        for plugin in self.registry.get_enabled_plugins():
            commands.extend(plugin.get_commands())
        return commands
    
    def get_plugin_help(self, plugin_name: Optional[str] = None) -> str:
        """
        Get help text for plugin(s).
        
        Args:
            plugin_name: Optional plugin name (all plugins if None)
        
        Returns:
            Help text
        """
        if plugin_name:
            plugin = self.registry.get_plugin(plugin_name)
            if plugin:
                return plugin.get_help()
            return f"Plugin not found: {plugin_name}"
        
        help_text = []
        for plugin in self.registry.get_enabled_plugins():
            help_text.append(plugin.get_help())
        return "\n\n".join(help_text)
    
    def cleanup(self) -> None:
        """Cleanup all plugins."""
        for plugin in self.registry.get_all_plugins():
            try:
                plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin.metadata.name}: {e}", exc_info=True)
        
        self._initialized = False

