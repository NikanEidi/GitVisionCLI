"""
Comprehensive Handler System

This module provides a modular, extensible handler architecture for all operations.
Each handler category has specialized handlers that can parse natural language
and execute actions.
"""

from gitvisioncli.core.handlers.base import (
    BaseHandler,
    HandlerResult,
    HandlerPriority,
)
from gitvisioncli.core.handlers.registry import HandlerRegistry
from gitvisioncli.core.handlers.manager import HandlerManager

# Import all handler categories
from gitvisioncli.core.handlers.file_handlers import FileHandlerCategory
from gitvisioncli.core.handlers.git_handlers import GitHandlerCategory
from gitvisioncli.core.handlers.github_handlers import (
    GitHubHandlerCategory,
    FolderHandlerCategory,
    SearchHandlerCategory,
    ShellHandlerCategory,
)

__all__ = [
    "BaseHandler",
    "HandlerResult",
    "HandlerPriority",
    "HandlerRegistry",
    "HandlerManager",
    "FileHandlerCategory",
    "GitHandlerCategory",
    "GitHubHandlerCategory",
    "FolderHandlerCategory",
    "SearchHandlerCategory",
    "ShellHandlerCategory",
]

