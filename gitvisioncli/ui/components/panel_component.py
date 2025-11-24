"""
Panel Component

Base class for panel components.
"""

from typing import Optional, Any
from pathlib import Path

from gitvisioncli.ui.components.renderer_component import RendererComponent, ComponentConfig


class PanelComponent(RendererComponent):
    """
    Base class for panel components.
    
    Panels are specialized components that:
    - Display content in a bordered area
    - Handle file operations
    - Manage state
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize panel component."""
        super().__init__(config)
        self.title: Optional[str] = None
        self.file_path: Optional[Path] = None
        self._content: list[str] = []
    
    def set_title(self, title: str) -> None:
        """Set panel title."""
        self.title = title
    
    def set_file_path(self, file_path: Optional[Path]) -> None:
        """Set active file path."""
        self.file_path = file_path
    
    def get_file_path(self) -> Optional[Path]:
        """Get active file path."""
        return self.file_path
    
    def set_content(self, content: list[str]) -> None:
        """Set panel content."""
        self._content = content
    
    def get_content(self) -> list[str]:
        """Get panel content."""
        return self._content
    
    def render_border(self, char: str = "═") -> str:
        """
        Render top/bottom border.
        
        Args:
            char: Border character
        
        Returns:
            Border string
        """
        return char * self.get_width()
    
    def render_title(self) -> str:
        """
        Render panel title.
        
        Returns:
            Title string
        """
        if not self.title:
            return ""
        return f" {self.title} ".center(self.get_width(), "═")

