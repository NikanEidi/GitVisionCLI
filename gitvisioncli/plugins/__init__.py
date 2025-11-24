"""
Plugin System

Modular plugin architecture for extensible features.
"""

from gitvisioncli.plugins.base_plugin import BasePlugin, PluginMetadata
from gitvisioncli.plugins.plugin_manager import PluginManager
from gitvisioncli.plugins.registry import PluginRegistry

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginManager",
    "PluginRegistry",
]

