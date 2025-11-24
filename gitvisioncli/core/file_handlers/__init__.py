"""
Modular File Operation Handlers

This module provides specialized handlers for different file editing operations.
Each handler is responsible for parsing natural language and converting it to
structured actions.
"""

from gitvisioncli.core.file_handlers.base import FileHandler, HandlerResult
from gitvisioncli.core.file_handlers.insert_handler import InsertHandler
from gitvisioncli.core.file_handlers.replace_handler import ReplaceHandler
from gitvisioncli.core.file_handlers.delete_handler import DeleteHandler
from gitvisioncli.core.file_handlers.append_handler import AppendHandler

__all__ = [
    "FileHandler",
    "HandlerResult",
    "InsertHandler",
    "ReplaceHandler",
    "DeleteHandler",
    "AppendHandler",
]

