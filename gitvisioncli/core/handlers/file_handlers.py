"""
File Operation Handlers

Comprehensive handlers for all file operations including:
- Create, Read, Delete, Rename, Move, Copy
- Line operations (Insert, Replace, Delete, Append)
- Advanced operations (Pattern matching, Fuzzy matching)
"""

import re
from typing import Optional, List, Dict, Any
from gitvisioncli.core.handlers.base import BaseHandler, HandlerResult, HandlerPriority
from gitvisioncli.core.file_handlers import (
    InsertHandler,
    ReplaceHandler,
    DeleteHandler,
    AppendHandler,
)


class FileHandlerCategory:
    """
    Category manager for all file operation handlers.
    
    Organizes and manages file-related handlers.
    """
    
    def __init__(self):
        """Initialize the file handler category."""
        self.handlers = [
            # Line editing handlers (from file_handlers module)
            InsertHandler(),
            ReplaceHandler(),
            DeleteHandler(),
            AppendHandler(),
            # File-level handlers
            CreateFileHandler(),
            ReadFileHandler(),
            DeleteFileHandler(),
            RenameFileHandler(),
            MoveFileHandler(),
            CopyFileHandler(),
        ]
    
    def get_handlers(self) -> List[BaseHandler]:
        """Get all file handlers."""
        return self.handlers


class CreateFileHandler(BaseHandler):
    """Handler for creating files."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for create file operations."""
        return [
            re.compile(
                r'\b(create|make|new|write|generate)\s+(?:file\s+)?([^\s]+)\s+with\s+(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE | re.DOTALL
            ),
            re.compile(
                r'\b(create|make|new|write|generate)\s+(?:file\s+)?([^\s]+)\s*:?\s*(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE | re.DOTALL
            ),
            re.compile(
                r'\b(create|make|new|write|generate)\s+(?:file\s+)?([^\s]+)\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is a create file operation."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['create file', 'make file', 'new file', 'write file']):
            return 0.9
        if any(pattern.search(text) for pattern in self.patterns):
            return 0.95
        return 0.0
    
    def parse(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        full_message: Optional[str] = None
    ) -> HandlerResult:
        """Parse create file instruction."""
        for pattern in self.patterns:
            match = pattern.search(text)
            if match:
                file_path = match.group(2) if len(match.groups()) >= 2 else None
                if not file_path:
                    continue
                
                # Extract content
                content = self.extract_content(text, full_message)
                if not content and len(match.groups()) >= 3:
                    content = match.group(3).strip()
                
                return HandlerResult(
                    success=True,
                    action_type="CreateFile",
                    params={
                        "path": file_path,
                        "content": content or ""
                    },
                    confidence=0.95
                )
        
        return HandlerResult(
            success=False,
            error="Could not parse create file instruction"
        )


class ReadFileHandler(BaseHandler):
    """Handler for reading files."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for read file operations."""
        return [
            re.compile(
                r'\b(read|view|show|display|open|cat)\s+(?:file\s+)?([^\s]+)\b',
                re.IGNORECASE
            ),
            re.compile(
                r'\b(read|view|show|display)\s+["\']([^"\']+)["\']\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is a read file operation."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['read file', 'view file', 'show file', 'open file']):
            return 0.9
        if any(pattern.search(text) for pattern in self.patterns):
            return 0.95
        return 0.0
    
    def parse(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        full_message: Optional[str] = None
    ) -> HandlerResult:
        """Parse read file instruction."""
        file_path = self.extract_file_path(text, context)
        if not file_path:
            return HandlerResult(
                success=False,
                error="Could not extract file path"
            )
        
        return HandlerResult(
            success=True,
            action_type="ReadFile",
            params={"path": file_path},
            confidence=0.95
        )


class DeleteFileHandler(BaseHandler):
    """Handler for deleting files."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for delete file operations."""
        return [
            re.compile(
                r'\b(delete|remove|rm|erase|trash)\s+(?:file\s+)?([^\s]+)\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is a delete file operation."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['delete file', 'remove file', 'rm file']):
            # Make sure it's not a line operation
            if 'line' in text_lower:
                return 0.0
            return 0.9
        if any(pattern.search(text) for pattern in self.patterns):
            return 0.95
        return 0.0
    
    def parse(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        full_message: Optional[str] = None
    ) -> HandlerResult:
        """Parse delete file instruction."""
        file_path = self.extract_file_path(text, context)
        if not file_path:
            return HandlerResult(
                success=False,
                error="Could not extract file path"
            )
        
        return HandlerResult(
            success=True,
            action_type="DeleteFile",
            params={"path": file_path},
            confidence=0.95
        )


class RenameFileHandler(BaseHandler):
    """Handler for renaming files."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for rename file operations."""
        return [
            re.compile(
                r'\b(rename|mv|change\s+name|rechristen)\s+([^\s]+)\s+(?:to|as|->)\s+([^\s]+)\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is a rename file operation."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['rename', 'change name', 'mv']):
            if 'to' in text_lower or 'as' in text_lower:
                return 0.9
        if any(pattern.search(text) for pattern in self.patterns):
            return 0.95
        return 0.0
    
    def parse(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        full_message: Optional[str] = None
    ) -> HandlerResult:
        """Parse rename file instruction."""
        match = re.search(
            r'\b(rename|mv|change\s+name)\s+([^\s]+)\s+(?:to|as|->)\s+([^\s]+)\b',
            text,
            re.IGNORECASE
        )
        if match:
            old_path = match.group(2)
            new_path = match.group(3)
            
            return HandlerResult(
                success=True,
                action_type="RenameFile",
                params={
                    "old_path": old_path,
                    "new_path": new_path
                },
                confidence=0.95
            )
        
        return HandlerResult(
            success=False,
            error="Could not parse rename file instruction"
        )


class MoveFileHandler(BaseHandler):
    """Handler for moving files."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for move file operations."""
        return [
            re.compile(
                r'\b(move|mv|transfer|relocate)\s+([^\s]+)\s+(?:to|into)\s+([^\s]+)\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is a move file operation."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['move', 'mv', 'transfer']):
            if 'to' in text_lower or 'into' in text_lower:
                return 0.9
        if any(pattern.search(text) for pattern in self.patterns):
            return 0.95
        return 0.0
    
    def parse(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        full_message: Optional[str] = None
    ) -> HandlerResult:
        """Parse move file instruction."""
        match = re.search(
            r'\b(move|mv|transfer)\s+([^\s]+)\s+(?:to|into)\s+([^\s]+)\b',
            text,
            re.IGNORECASE
        )
        if match:
            file_path = match.group(2)
            target = match.group(3)
            
            return HandlerResult(
                success=True,
                action_type="MoveFile",
                params={
                    "path": file_path,
                    "target": target
                },
                confidence=0.95
            )
        
        return HandlerResult(
            success=False,
            error="Could not parse move file instruction"
        )


class CopyFileHandler(BaseHandler):
    """Handler for copying files."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for copy file operations."""
        return [
            re.compile(
                r'\b(copy|cp|duplicate|clone|backup)\s+([^\s]+)\s+(?:to|as)\s+([^\s]+)\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is a copy file operation."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['copy', 'cp', 'duplicate', 'clone']):
            if 'to' in text_lower or 'as' in text_lower:
                return 0.9
        if any(pattern.search(text) for pattern in self.patterns):
            return 0.95
        return 0.0
    
    def parse(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        full_message: Optional[str] = None
    ) -> HandlerResult:
        """Parse copy file instruction."""
        match = re.search(
            r'\b(copy|cp|duplicate|clone)\s+([^\s]+)\s+(?:to|as)\s+([^\s]+)\b',
            text,
            re.IGNORECASE
        )
        if match:
            file_path = match.group(2)
            new_path = match.group(3)
            
            return HandlerResult(
                success=True,
                action_type="CopyFile",
                params={
                    "path": file_path,
                    "new_path": new_path
                },
                confidence=0.95
            )
        
        return HandlerResult(
            success=False,
            error="Could not parse copy file instruction"
        )

