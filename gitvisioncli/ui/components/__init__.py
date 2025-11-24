"""
UI Component System

Modular component-based architecture for all UI elements.
"""

from gitvisioncli.ui.components.base_component import BaseComponent, ComponentConfig
from gitvisioncli.ui.components.renderer_component import RendererComponent
from gitvisioncli.ui.components.panel_component import PanelComponent

__all__ = [
    "BaseComponent",
    "ComponentConfig",
    "RendererComponent",
    "PanelComponent",
]

