"""
Append Operation Handler

Handles append operations:
- Append to bottom
- Append to end
"""

import re
from typing import Optional, List
from gitvisioncli.core.file_handlers.base import FileHandler, HandlerResult, FileHandlerPriority


class AppendHandler(FileHandler):
    """Handler for append operations."""
    
    def __init__(self):
        """Initialize append handler with low priority (least specific)."""
        super().__init__(priority=FileHandlerPriority.LOW)
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for append operations."""
        return [
            # Append to bottom: "add at bottom", "append to end"
            re.compile(
                r'\b(add|append|insert|write|put)\s+(?:comment|text|code|line)?\s*(?:at|to)?\s*(?:the\s+)?(?:bottom|end|tail)\b',
                re.IGNORECASE
            ),
            # Natural variations: "add X at bottom", "append X to end"
            re.compile(
                r'\b(add|append|insert|write|put)\s+(.+?)\s+(?:at|to)\s+(?:the\s+)?(?:bottom|end|tail)\b',
                re.IGNORECASE | re.DOTALL
            ),
        ]
    
    def can_handle(self, text: str, active_file: Optional[str] = None) -> float:
        """Check if this is an append operation."""
        text_lower = text.lower()
        
        # High confidence keywords
        append_keywords = ['append', 'add', 'insert', 'write', 'put']
        if any(kw in text_lower for kw in append_keywords):
            # Check for append indicators
            if any(ind in text_lower for ind in ['at bottom', 'to bottom', 'at end', 'to end', 'at tail']):
                # Make sure it's not an insert at line
                if 'line' in text_lower and re.search(r'\bline\s*\d+', text_lower):
                    return 0.0  # Likely an insert at line
                return 0.9
        
        # Check patterns
        for pattern in self.patterns:
            if pattern.search(text):
                return 0.95
        
        return 0.0
    
    def parse(self, text: str, active_file: Optional[str] = None, full_message: Optional[str] = None) -> HandlerResult:
        """Parse append instruction."""
        if not active_file:
            return HandlerResult(
                success=False,
                error="No active file specified"
            )
        
        # Extract content
        content = self.extract_content(text, full_message)
        
        # If no content extracted, try to get it from the pattern
        if not content:
            # Try "add X at bottom" pattern
            pattern_match = re.search(
                r'\b(add|append|insert|write|put)\s+(.+?)\s+(?:at|to)\s+(?:the\s+)?(?:bottom|end|tail)\b',
                text,
                re.IGNORECASE | re.DOTALL
            )
            if pattern_match:
                content = pattern_match.group(2).strip()
                content = self._clean_quotes(content)
        
        if not content:
            return HandlerResult(
                success=False,
                error="Could not extract content to append"
            )
        
        return HandlerResult(
            success=True,
            action_type="InsertAtBottom",
            params={
                "path": active_file,
                "text": content
            },
            confidence=0.95
        )

