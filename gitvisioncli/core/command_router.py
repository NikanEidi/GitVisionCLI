"""
Command Router

Unified command routing system that uses the modular handler architecture.
This is the main entry point for converting natural language to actions.
"""

from typing import Optional, Dict, Any
from gitvisioncli.core.handlers.manager import HandlerManager
from gitvisioncli.core.handlers.registry import HandlerRegistry
from gitvisioncli.core.handlers.file_handlers import FileHandlerCategory
from gitvisioncli.core.handlers.git_handlers import GitHandlerCategory
from gitvisioncli.core.handlers.github_handlers import GitHubHandlerCategory
from gitvisioncli.core.handlers.github_handlers import (
    FolderHandlerCategory,
    SearchHandlerCategory,
    ShellHandlerCategory,
)
from gitvisioncli.core.natural_language_action_engine import ActionJSON, ActiveFileContext


class CommandRouter:
    """
    Unified command router using modular handler architecture.
    
    This class provides a single entry point for converting natural language
    commands into structured actions. It uses the handler system for
    extensible, modular parsing.
    """
    
    def __init__(self):
        """Initialize the command router with all handler categories."""
        self.registry = HandlerRegistry()
        self.manager = HandlerManager(self.registry)
        
        # Register all handler categories
        self._register_all_handlers()
    
    def _register_all_handlers(self) -> None:
        """Register all handlers from all categories."""
        categories = [
            FileHandlerCategory(),
            GitHandlerCategory(),
            GitHubHandlerCategory(),
            FolderHandlerCategory(),
            SearchHandlerCategory(),
            ShellHandlerCategory(),
        ]
        
        category_names = {
            FileHandlerCategory: "file",
            GitHandlerCategory: "git",
            GitHubHandlerCategory: "github",
            FolderHandlerCategory: "folder",
            SearchHandlerCategory: "search",
            ShellHandlerCategory: "shell",
        }
        
        for category in categories:
            category_name = category_names.get(type(category), "unknown")
            handlers = category.get_handlers()
            for handler in handlers:
                self.registry.register(handler, category_name)
    
    def route(
        self,
        user_message: str,
        active_file: Optional[ActiveFileContext] = None
    ) -> Optional[ActionJSON]:
        """
        Route a user message to the appropriate handler and return an action.
        
        Args:
            user_message: The user's natural language command
            active_file: Optional active file context
        
        Returns:
            ActionJSON if a handler successfully parsed the command, None otherwise
        """
        if not user_message or not user_message.strip():
            return None
        
        # Build context
        context = {}
        if active_file:
            context["active_file"] = active_file.path if isinstance(active_file, str) else active_file.path
        
        # Try to find best handler
        # Pass full_message to handlers for multiline content extraction
        result = self.manager.find_best_handler(user_message, context)
        
        if result and result.success:
            # If handler didn't get full_message, try parsing again with it
            if "\n" in user_message and result.params and not any(
                result.params.get(k) for k in ["content", "text", "block"] if result.params.get(k)
            ):
                # Retry with full message for content extraction
        result = self.manager.find_best_handler(user_message, context)
        
        if result and result.success:
            return ActionJSON(
                type=result.action_type,
                params=result.params or {}
            )
        
        return None
    
    def register_handler(
        self,
        handler,
        category: str,
        name: Optional[str] = None
    ) -> None:
        """
        Register a custom handler.
        
        Args:
            handler: Handler instance
            category: Category name
            name: Optional handler name
        """
        self.registry.register(handler, category, name)
    
    def get_available_handlers(self) -> Dict[str, list]:
        """
        Get all available handlers organized by category.
        
        Returns:
            Dictionary mapping category names to lists of handler names
        """
        categories = {}
        for category_name in self.registry.get_categories():
            handlers = self.registry.get_handlers(category_name)
            categories[category_name] = [h.__class__.__name__ for h in handlers]
        return categories

