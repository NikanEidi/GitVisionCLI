"""
Replace Operation Handler

Handles all replace operations:
- Replace line
- Replace line range
- Replace content by pattern
"""

import re
from typing import Optional, List, Tuple
from gitvisioncli.core.file_handlers.base import FileHandler, HandlerResult, FileHandlerPriority


class ReplaceHandler(FileHandler):
    """Handler for replace operations."""
    
    def __init__(self):
        """Initialize replace handler with high priority."""
        super().__init__(priority=FileHandlerPriority.HIGH)
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for replace operations."""
        return [
            # Replace line: "replace line 5", "update line 5", "change line 5"
            re.compile(
                r'\b(replace|update|change|edit|modify|set)\s+line\s*(\d+)\s+(?:with|to|by)\s+(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE | re.DOTALL
            ),
            # Replace lines: "replace lines 5-10", "update lines 5 to 10"
            re.compile(
                r'\b(replace|update|change|edit|modify|set)\s+lines?\s+(\d+)\s*[-~]\s*(\d+)\s+(?:with|to|by)\s+(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE | re.DOTALL
            ),
            re.compile(
                r'\b(replace|update|change|edit|modify|set)\s+lines?\s+(\d+)\s+to\s+(\d+)\s+(?:with|to|by)\s+(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE | re.DOTALL
            ),
            # Replace content: "replace X with Y", "change X to Y"
            re.compile(
                r'\b(replace|update|change|edit|modify|set)\s+(.+?)\s+(?:with|to|by)\s+(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE | re.DOTALL
            ),
            # Natural variations: "change line 5 to X", "update line 5 with X"
            re.compile(
                r'\b(replace|update|change|edit|modify|set)\s+line\s*(\d+)\s+(?:to|with|by)\s+(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE | re.DOTALL
            ),
        ]
    
    def can_handle(self, text: str, active_file: Optional[str] = None) -> float:
        """Check if this is a replace operation."""
        text_lower = text.lower()
        
        # High confidence keywords
        replace_keywords = ['replace', 'update', 'change', 'edit', 'modify', 'set']
        if any(kw in text_lower for kw in replace_keywords):
            # Check if it's clearly a replace (not insert/delete)
            if any(kw in text_lower for kw in ['insert', 'add', 'delete', 'remove']):
                return 0.0  # Likely a different operation
            
            # Check for replace indicators
            if any(ind in text_lower for ind in ['with', 'to', 'by']):
                return 0.9
        
        # Check patterns
        for pattern in self.patterns:
            if pattern.search(text):
                return 0.95
        
        return 0.0
    
    def parse(self, text: str, active_file: Optional[str] = None, full_message: Optional[str] = None) -> HandlerResult:
        """Parse replace instruction."""
        if not active_file:
            return HandlerResult(
                success=False,
                error="No active file specified"
            )
        
        # Check for line range replacement
        line_range = self.extract_line_range(text)
        if line_range:
            start, end = line_range
            content = self.extract_content(text, full_message)
            if not content:
                return HandlerResult(
                    success=False,
                    error="Could not extract replacement content"
                )
            
            return HandlerResult(
                success=True,
                action_type="ReplaceBlock",
                params={
                    "path": active_file,
                    "start_line": start,
                    "end_line": end,
                    "new_text": content
                },
                confidence=0.95
            )
        
        # Check for single line replacement
        line_num = self.extract_line_number(text)
        if line_num:
            content = self.extract_content(text, full_message)
            if not content:
                return HandlerResult(
                    success=False,
                    error="Could not extract replacement content"
                )
            
            return HandlerResult(
                success=True,
                action_type="ReplaceBlock",
                params={
                    "path": active_file,
                    "start_line": line_num,
                    "end_line": line_num,
                    "new_text": content
                },
                confidence=0.95
            )
        
        # Try pattern-based replacement
        # Extract "replace X with Y" pattern
        pattern_match = re.search(
            r'\b(replace|update|change|edit|modify|set)\s+(.+?)\s+(?:with|to|by)\s+(.+?)(?:\s+in\s+|\s*$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if pattern_match:
            old_text = pattern_match.group(2).strip()
            new_text = pattern_match.group(3).strip()
            
            # Clean quotes
            old_text = self._clean_quotes(old_text)
            new_text = self._clean_quotes(new_text)
            
            return HandlerResult(
                success=True,
                action_type="ReplaceByPattern",
                params={
                    "path": active_file,
                    "old_text": old_text,
                    "new_text": new_text
                },
                confidence=0.85
            )
        
        return HandlerResult(
            success=False,
            error="Could not parse replace instruction"
        )

