"""
Git Operation Handlers

Comprehensive handlers for all Git operations.
"""

import re
from typing import Optional, List, Dict, Any
from gitvisioncli.core.handlers.base import BaseHandler, HandlerResult, HandlerPriority


class GitHandlerCategory:
    """Category manager for all Git operation handlers."""
    
    def __init__(self):
        """Initialize the Git handler category."""
        self.handlers = [
            # Git handlers can be added here in the future
            # For now, Git operations are handled by the natural language action engine
        ]
    
    def get_handlers(self) -> List[BaseHandler]:
        """Get all Git handlers."""
        return self.handlers

