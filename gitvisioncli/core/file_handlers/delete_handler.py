"""
Delete Operation Handler

Handles all delete operations:
- Delete line
- Delete line range
- Delete by pattern
"""

import re
from typing import Optional, List
from gitvisioncli.core.file_handlers.base import FileHandler, HandlerResult, FileHandlerPriority


class DeleteHandler(FileHandler):
    """Handler for delete operations."""
    
    def __init__(self):
        """Initialize delete handler with high priority (most specific)."""
        super().__init__(priority=FileHandlerPriority.HIGH)
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for delete operations."""
        return [
            # Delete line: "delete line 5", "remove line 5", "rm line 5"
            re.compile(
                r'\b(delete|remove|rm|dl|erase|drop|clear)\s+line\s*(\d+)\b',
                re.IGNORECASE
            ),
            # Delete lines: "delete lines 5-10", "remove lines 5 to 10"
            re.compile(
                r'\b(delete|remove|rm|dl|erase|drop|clear)\s+lines?\s+(\d+)\s*[-~]\s*(\d+)\b',
                re.IGNORECASE
            ),
            re.compile(
                r'\b(delete|remove|rm|dl|erase|drop|clear)\s+lines?\s+(\d+)\s+to\s+(\d+)\b',
                re.IGNORECASE
            ),
            # Broken grammar: "rm 5", "dl 5", "delete 5", "remove 5"
            re.compile(
                r'\b(rm|dl)\s+(\d+)(?:\s|$)',
                re.IGNORECASE
            ),
            # Broken grammar: "delete 5", "remove 5" (without "line" keyword)
            re.compile(
                r'\b(delete|remove|erase|drop|clear)\s+(\d+)(?:\s|$)',
                re.IGNORECASE
            ),
            # Delete content: "delete X", "remove X" (only if X is not a number)
            re.compile(
                r'\b(delete|remove|rm|erase|drop|clear)\s+(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, active_file: Optional[str] = None) -> float:
        """Check if this is a delete operation."""
        text_lower = text.lower()
        
        # High confidence keywords
        delete_keywords = ['delete', 'remove', 'rm', 'erase', 'drop', 'clear']
        if any(kw in text_lower for kw in delete_keywords):
            # Check if it's clearly a delete (not insert/replace)
            if any(kw in text_lower for kw in ['insert', 'add', 'replace', 'update', 'with', 'to']):
                return 0.0  # Likely a different operation
            
            # Check for delete indicators
            if 'line' in text_lower or re.search(r'\b(rm|dl)\s+\d+', text_lower):
                return 0.9
        
        # Check patterns
        for pattern in self.patterns:
            if pattern.search(text):
                return 0.95
        
        return 0.0
    
    def parse(self, text: str, active_file: Optional[str] = None, full_message: Optional[str] = None) -> HandlerResult:
        """Parse delete instruction."""
        if not active_file:
            return HandlerResult(
                success=False,
                error="No active file specified"
            )
        
        # Check for line range deletion
        line_range = self.extract_line_range(text)
        if line_range:
            start, end = line_range
            return HandlerResult(
                success=True,
                action_type="DeleteLineRange",
                params={
                    "path": active_file,
                    "start_line": start,
                    "end_line": end
                },
                confidence=0.95
            )
        
        # Check for single line deletion
        line_num = self.extract_line_number(text)
        if line_num:
            return HandlerResult(
                success=True,
                action_type="DeleteLineRange",
                params={
                    "path": active_file,
                    "start_line": line_num,
                    "end_line": line_num
                },
                confidence=0.95
            )
        
        # Check for broken grammar: "delete 5", "remove 5" (without "line" keyword)
        # This pattern catches cases where extract_line_number misses
        broken_line_match = re.search(
            r'\b(delete|remove|erase|drop|clear)\s+(\d+)(?:\s|$)',
            text,
            re.IGNORECASE
        )
        if broken_line_match:
            line_num = int(broken_line_match.group(2))
            return HandlerResult(
                success=True,
                action_type="DeleteLineRange",
                params={
                    "path": active_file,
                    "start_line": line_num,
                    "end_line": line_num
                },
                confidence=0.95
            )
        
        # Try pattern-based deletion
        # Extract "delete X" pattern (but exclude if X is just a number - that's a line deletion)
        pattern_match = re.search(
            r'\b(delete|remove|rm|erase|drop|clear)\s+(.+?)(?:\s+in\s+|\s*$)',
            text,
            re.IGNORECASE
        )
        if pattern_match:
            pattern_text = pattern_match.group(2).strip()
            pattern_text = self._clean_quotes(pattern_text)
            
            # If pattern is just a number, it's a line deletion, not pattern deletion
            # This should have been caught by extract_line_number, but double-check here
            if pattern_text.isdigit():
                line_num = int(pattern_text)
                return HandlerResult(
                    success=True,
                    action_type="DeleteLineRange",
                    params={
                        "path": active_file,
                        "start_line": line_num,
                        "end_line": line_num
                    },
                    confidence=0.95
                )
            
            return HandlerResult(
                success=True,
                action_type="DeleteByPattern",
                params={
                    "path": active_file,
                    "pattern": pattern_text
                },
                confidence=0.85
            )
        
        return HandlerResult(
            success=False,
            error="Could not parse delete instruction"
        )

