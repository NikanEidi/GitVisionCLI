"""
Renderer Component

Base class for components that render content.
"""

from typing import List, Optional
from gitvisioncli.ui.components.base_component import BaseComponent, ComponentConfig


class RendererComponent(BaseComponent):
    """
    Base class for rendering components.
    
    Provides utilities for:
    - Text rendering
    - ANSI color handling
    - Layout management
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize renderer component."""
        super().__init__(config)
        self._lines: List[str] = []
    
    def render(self) -> str:
        """Render the component."""
        self._lines = []
        self._build_lines()
        return "\n".join(self._lines)
    
    def _build_lines(self) -> None:
        """Build render lines (override in subclasses)."""
        pass
    
    def add_line(self, line: str) -> None:
        """Add a line to the render output."""
        self._lines.append(line)
    
    def add_lines(self, lines: List[str]) -> None:
        """Add multiple lines to the render output."""
        self._lines.extend(lines)
    
    def clear_lines(self) -> None:
        """Clear all lines."""
        self._lines = []
    
    def truncate_to_width(self, text: str, width: Optional[int] = None) -> str:
        """
        Truncate text to fit within width.
        
        Args:
            text: Text to truncate
            width: Width limit (uses component width if not provided)
        
        Returns:
            Truncated text
        """
        width = width or self.get_width()
        if len(text) <= width:
            return text
        return text[:width-3] + "..."
    
    def pad_to_width(self, text: str, width: Optional[int] = None, align: str = "left") -> str:
        """
        Pad text to fit within width.
        
        Args:
            text: Text to pad
            width: Target width (uses component width if not provided)
            align: Alignment ("left", "right", "center")
        
        Returns:
            Padded text
        """
        width = width or self.get_width()
        if len(text) >= width:
            return text[:width]
        
        if align == "left":
            return text + " " * (width - len(text))
        elif align == "right":
            return " " * (width - len(text)) + text
        else:  # center
            padding = (width - len(text)) // 2
            return " " * padding + text + " " * (width - len(text) - padding)

