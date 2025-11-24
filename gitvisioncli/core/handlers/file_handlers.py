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
    
    def __init__(self):
        """Initialize with normal priority."""
        super().__init__(priority=HandlerPriority.NORMAL)
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for create file operations."""
        return [
            # Pattern: "create app.py with content" - match filename before "with"
            re.compile(
                r'\b(create|make|new|write|generate)\s+(?:file\s+)?([^\s\n]+)\s+with\s+(.+)$',
                re.IGNORECASE | re.DOTALL
            ),
            # Pattern: "create app.py: content" or "create app.py content" - match filename before colon or content
            re.compile(
                r'\b(create|make|new|write|generate)\s+(?:file\s+)?([^\s\n:]+)\s*:?\s*(.+)$',
                re.IGNORECASE | re.DOTALL
            ),
            # Pattern: "create app.py" (no content) - match just the filename
            re.compile(
                r'\b(create|make|new|write|generate)\s+(?:file\s+)?([^\s\n]+)\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is a create file operation."""
        text_lower = text.lower()
        
        # CRITICAL FIX: Don't match if it's clearly a GitHub or Git repo command
        if 'github' in text_lower:
            if 'repo' in text_lower or 'repository' in text_lower:
                return 0.0
            if 'issue' in text_lower:
                return 0.0
            if 'pr' in text_lower or 'pull request' in text_lower:
                return 0.0
        
        # CRITICAL FIX: Don't match "create private repo" or "create public repo" - these are GitHub repos
        if re.search(r'\b(?:create|make)\s+(?:private|public)\s+(?:repo|repository)\b', text_lower):
            return 0.0  # Let GitHub handler take this
        
        # CRITICAL FIX: Don't match "create repo" without explicit file keywords
        if re.search(r'^(?:create|make)\s+repo\b', text_lower) and 'file' not in text_lower:
            return 0.0  # Likely a GitHub repo command
        
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
        # First try to extract quoted file path (only before "with" keyword)
        file_path = None
        # Check for quoted path before "with"
        before_with = text.split(" with ", 1)[0] if " with " in text.lower() else text.split("\n", 1)[0]
        quoted_path_match = re.search(r'["\']([^"\']+)["\']', before_with)
        if quoted_path_match:
            file_path = quoted_path_match.group(1).strip()
        
        # Try patterns if no quoted path found
        if not file_path:
            # Use first line only for pattern matching to avoid matching content
            first_line = text.split("\n", 1)[0] if "\n" in text else text
            for pattern in self.patterns:
                match = pattern.search(first_line)
                if match:
                    file_path = match.group(2) if len(match.groups()) >= 2 else None
                    if file_path:
                        # Clean up quotes if present
                        file_path = file_path.strip('"\'')
                        # Validate: must be a valid filename (not "/", not starting with "@", etc.)
                        if file_path and file_path != "/" and not file_path.startswith("@") and not file_path.startswith("("):
                            # Prefer files with extensions, but allow others
                            if "." in file_path or len(file_path.split()) == 1:
                                break
        
        if not file_path:
            return HandlerResult(
                success=False,
                error="Could not extract file path"
            )
        
        # Extract content - try multiple methods
        # First, try to extract from patterns
        content = None
        for pattern in self.patterns:
            match = pattern.search(text)
            if match and len(match.groups()) >= 3:
                potential_content = match.group(3).strip()
                if potential_content:
                    content = potential_content
                    break
        
        # If no content from patterns, try extract_content method
        if not content:
                content = self.extract_content(text, full_message)
        
        # If still no content, try to extract from after "with"
        if not content:
            # Look for content after "with" keyword - capture everything to end
            with_match = re.search(r'\bwith\s+(.+)$', text, re.DOTALL | re.IGNORECASE)
            if with_match:
                content = with_match.group(1).strip()
        
        # If still no content, try to extract from multiline input
        if not content and full_message and "\n" in full_message:
            # Check if full_message has more content than text
            if len(full_message) > len(text):
                # Extract everything after the file path
                path_pos = full_message.find(file_path)
                if path_pos >= 0:
                    after_path = full_message[path_pos + len(file_path):].strip()
                    # Remove "with" if present
                    after_path = re.sub(r'^\s*with\s+', '', after_path, flags=re.IGNORECASE)
                    if after_path:
                        content = after_path.strip()
                
        # Return result (with or without content)
                return HandlerResult(
                    success=True,
                    action_type="CreateFile",
                    params={
                        "path": file_path,
                        "content": content or ""
                    },
                    confidence=0.95
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
        
        # Clean up quotes from path
        file_path = file_path.strip('"\'')
        
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
        # First check if it's a line operation - if so, don't match
        if 'line' in text_lower or 'lines' in text_lower:
            return 0.0  # It's a line operation, not file operation
        
        if any(kw in text_lower for kw in ['delete file', 'remove file', 'rm file']):
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
        
        # Clean up quotes from path
        file_path = file_path.strip('"\'')
        
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

