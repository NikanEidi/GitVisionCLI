"""
Handler Registry

Central registry for all handlers, organized by category and priority.
Provides fast lookup and extensibility.
"""

from typing import Dict, List, Optional, Type
from gitvisioncli.core.handlers.base import BaseHandler, HandlerPriority


class HandlerRegistry:
    """
    Central registry for all operation handlers.
    
    Handlers are organized by category and can be registered dynamically.
    This allows for plugin-based extensibility.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._handlers: Dict[str, List[BaseHandler]] = {}
        self._handler_classes: Dict[str, Type[BaseHandler]] = {}
        self._categories: Dict[str, str] = {}  # handler_name -> category
    
    def register(
        self,
        handler: BaseHandler,
        category: str,
        name: Optional[str] = None
    ) -> None:
        """
        Register a handler.
        
        Args:
            handler: Handler instance to register
            category: Category name (e.g., "file", "git", "github")
            name: Optional name for the handler (default: class name)
        """
        if name is None:
            name = handler.__class__.__name__
        
        if category not in self._handlers:
            self._handlers[category] = []
        
        # Insert handler in priority order (highest first)
        handlers = self._handlers[category]
        inserted = False
        
        # Get priority value (handle both HandlerPriority and FileHandlerPriority)
        handler_priority = getattr(handler, 'priority', None)
        if handler_priority is None:
            # No priority - add at end
            handlers.append(handler)
        else:
            # Get priority value (works for both enum types)
            handler_priority_value = handler_priority.value if hasattr(handler_priority, 'value') else 0
            
            for i, existing_handler in enumerate(handlers):
                existing_priority = getattr(existing_handler, 'priority', None)
                if existing_priority is None:
                    continue
                existing_priority_value = existing_priority.value if hasattr(existing_priority, 'value') else 0
                
                if handler_priority_value > existing_priority_value:
                    handlers.insert(i, handler)
                    inserted = True
                    break
            
            if not inserted:
                handlers.append(handler)
        
        self._categories[name] = category
    
    def register_class(
        self,
        handler_class: Type[BaseHandler],
        category: str,
        name: Optional[str] = None
    ) -> None:
        """
        Register a handler class (will be instantiated on demand).
        
        Args:
            handler_class: Handler class to register
            category: Category name
            name: Optional name for the handler
        """
        if name is None:
            name = handler_class.__name__
        
        self._handler_classes[name] = handler_class
        self._categories[name] = category
    
    def get_handlers(
        self,
        category: Optional[str] = None
    ) -> List[BaseHandler]:
        """
        Get all handlers, optionally filtered by category.
        
        Args:
            category: Optional category to filter by
        
        Returns:
            List of handlers, sorted by priority (highest first)
        """
        if category:
            return self._handlers.get(category, [])
        
        # Return all handlers, sorted by priority
        all_handlers = []
        for handlers in self._handlers.values():
            all_handlers.extend(handlers)
        
        # Sort by priority, handling handlers without priority
        def get_priority_value(handler):
            priority = getattr(handler, 'priority', None)
            if priority is None:
                return 0
            return priority.value if hasattr(priority, 'value') else 0
        
        return sorted(all_handlers, key=get_priority_value, reverse=True)
    
    def get_handler(self, name: str) -> Optional[BaseHandler]:
        """
        Get a specific handler by name.
        
        Args:
            name: Handler name
        
        Returns:
            Handler instance or None
        """
        category = self._categories.get(name)
        if not category:
            return None
        
        handlers = self._handlers.get(category, [])
        for handler in handlers:
            if handler.__class__.__name__ == name:
                return handler
        
        return None
    
    def get_categories(self) -> List[str]:
        """
        Get all registered categories.
        
        Returns:
            List of category names
        """
        return list(self._handlers.keys())
    
    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        self._handler_classes.clear()
        self._categories.clear()

