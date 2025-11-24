"""
Append Operation Handler

Handles append operations:
- Append to bottom
- Append to end
"""

import re
from typing import Optional, List, Dict, Any
from gitvisioncli.core.file_handlers.base import FileHandler, HandlerResult, FileHandlerPriority


class AppendHandler(FileHandler):
    """Handler for append operations."""
    
    def __init__(self):
        """Initialize append handler with normal priority."""
        super().__init__(priority=FileHandlerPriority.NORMAL)
    
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
            # Variations without "the": "add X at bottom", "append X to end"
            re.compile(
                r'\b(add|append|insert|write|put)\s+(?:comment|text|code|line)?\s*(?:at|to)\s+(?:bottom|end|tail)\b',
                re.IGNORECASE
            ),
            # Match "add X at tail"
            re.compile(
                r'\b(add|append|insert|write|put)\s+(.+?)\s+at\s+tail\b',
                re.IGNORECASE | re.DOTALL
            ),
            # Standalone "append X" (without "at bottom")
            re.compile(
                r'^append\s+(.+?)(?:\s|$)',
                re.IGNORECASE | re.DOTALL
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is an append operation."""
        text_lower = text.lower()
        
        # Only handle if there's an active file (context-aware)
        if not context or not context.get("active_file"):
            return 0.0
        
        # High confidence keywords
        append_keywords = ['append', 'add', 'insert', 'write', 'put']
        if any(kw in text_lower for kw in append_keywords):
            # Check for standalone "append" (without "at bottom")
            if text_lower.startswith('append '):
                return 0.95  # Standalone append is always append operation
            # Check for append indicators
            if any(ind in text_lower for ind in ['at bottom', 'to bottom', 'at end', 'to end', 'at tail']):
                # Make sure it's not an insert at line
                if 'line' in text_lower and re.search(r'\bline\s*\d+', text_lower):
                    return 0.0  # Likely an insert at line
                # Make sure it's not a git command
                if text_lower.startswith('git '):
                    return 0.0  # Git command, not file operation
                # Make sure it's not a git add (check for "add ." or "add all" without file operation keywords)
                if text_lower.startswith('add ') and not any(ind in text_lower for ind in ['at bottom', 'to bottom', 'at end', 'to end', 'at tail', 'at top', 'at line']):
                    if re.match(r'^add\s+(?:\.|all|[^\s]+)', text_lower):
                        return 0.0  # Likely git add
                return 0.95  # Higher confidence when active file exists
        
        # Check patterns
        for pattern in self.patterns:
            if pattern.search(text):
                return 0.95
        
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        """Parse append instruction."""
        # Extract active_file from context
        active_file = None
        if context:
            active_file = context.get("active_file")
            if isinstance(active_file, dict):
                # Handle case where active_file is a dict with 'path' key
                active_file = active_file.get("path") or active_file.get("active_file")
        
        if not active_file:
            return HandlerResult(
                success=False,
                error="No active file specified"
            )
        
        # Extract content - try multiple methods
        content = None
        
        # First try pattern: "add X at bottom" -> extract X
            pattern_match = re.search(
                r'\b(add|append|insert|write|put)\s+(.+?)\s+(?:at|to)\s+(?:the\s+)?(?:bottom|end|tail)\b',
                text,
                re.IGNORECASE | re.DOTALL
            )
            if pattern_match:
                content = pattern_match.group(2).strip()
                content = self._clean_quotes(content)
        
        # If no content from pattern, try extract_content method
        if not content:
            content = self.extract_content(text, full_message)
        
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

