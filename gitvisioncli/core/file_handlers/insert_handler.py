"""
Insert Operation Handler

Handles all insert operations:
- Insert at line
- Insert before line
- Insert after line
- Insert at top
"""

import re
from typing import Optional, List
from gitvisioncli.core.file_handlers.base import FileHandler, HandlerResult, FileHandlerPriority


class InsertHandler(FileHandler):
    """Handler for insert operations."""
    
    def __init__(self):
        """Initialize insert handler with normal priority."""
        super().__init__(priority=FileHandlerPriority.NORMAL)
    
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize patterns for insert operations."""
        return [
            # Insert at line: "insert at line 5", "add at line 5", "put at line 5"
            re.compile(
                r'\b(insert|add|write|put|place|append)\s+(?:at|on|in)\s+line\s*(\d+)\b',
                re.IGNORECASE
            ),
            # Insert before: "insert before line 5", "add above line 5"
            re.compile(
                r'\b(insert|add|write|put|place)\s+(?:before|above|prior\s+to|ahead\s+of)\s+line\s*(\d+)\b',
                re.IGNORECASE
            ),
            # Insert after: "insert after line 5", "add below line 5"
            re.compile(
                r'\b(insert|add|write|put|place)\s+(?:after|below|following|afterwards)\s+line\s*(\d+)\b',
                re.IGNORECASE
            ),
            # Insert at top: "insert at top", "add at beginning", "prepend"
            re.compile(
                r'\b(insert|add|write|put|place|prepend)\s+(?:at|to)\s+(?:the\s+)?(?:top|beginning|start|head)\b',
                re.IGNORECASE
            ),
            # Insert in line: "add X in line 5", "insert X into line 5"
            re.compile(
                r'\b(insert|add|write|put)\s+(.+?)\s+in\s+line\s*(\d+)\b',
                re.IGNORECASE
            ),
            # Insert line with: "add line 5 with X", "insert line 5 with X"
            re.compile(
                r'\b(insert|add|write|put)\s+line\s*(\d+)\s+with\s+(.+?)(?:\s+in\s+|\s*$)',
                re.IGNORECASE | re.DOTALL
            ),
            # Natural variations: "put X at line 5", "write X on line 5"
            re.compile(
                r'\b(insert|add|write|put|place)\s+(.+?)\s+(?:at|on|in)\s+line\s*(\d+)\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, active_file: Optional[str] = None) -> float:
        """Check if this is an insert operation."""
        text_lower = text.lower()
        
        # High confidence keywords
        if any(kw in text_lower for kw in ['insert', 'add', 'put', 'place', 'write']):
            # Check if it's clearly an insert (not replace/delete)
            if any(kw in text_lower for kw in ['replace', 'delete', 'remove', 'update']):
                return 0.0  # Likely a different operation
            
            # Check for insert indicators
            insert_indicators = [
                'at line', 'before line', 'after line', 'in line',
                'at top', 'at beginning', 'at start',
                'line with', 'line:', 'line '
            ]
            if any(ind in text_lower for ind in insert_indicators):
                return 0.9
        
        # Check patterns
        for pattern in self.patterns:
            if pattern.search(text):
                return 0.95
        
        return 0.0
    
    def parse(self, text: str, active_file: Optional[str] = None, full_message: Optional[str] = None) -> HandlerResult:
        """Parse insert instruction."""
        if not active_file:
            return HandlerResult(
                success=False,
                error="No active file specified"
            )
        
        text_lower = text.lower()
        
        # Determine insert position
        line_num = None
        position = "after"  # default
        
        # Check for "at top" / "at beginning"
        if re.search(r'\b(?:at|to)\s+(?:the\s+)?(?:top|beginning|start|head)\b', text_lower):
            return HandlerResult(
                success=True,
                action_type="InsertAtTop",
                params={
                    "path": active_file,
                    "text": self.extract_content(text, full_message) or ""
                },
                confidence=0.95
            )
        
        # Check for "before" / "above"
        before_match = re.search(r'\b(?:before|above|prior\s+to|ahead\s+of)\s+line\s*(\d+)\b', text_lower)
        if before_match:
            line_num = int(before_match.group(1))
            position = "before"
        else:
            # Check for "after" / "below"
            after_match = re.search(r'\b(?:after|below|following|afterwards)\s+line\s*(\d+)\b', text_lower)
            if after_match:
                line_num = int(after_match.group(1))
                position = "after"
            else:
                # Check for "at line" / "on line" / "in line"
                at_match = re.search(r'\b(?:at|on|in)\s+line\s*(\d+)\b', text_lower)
                if at_match:
                    line_num = int(at_match.group(1))
                    position = "at"
                else:
                    # Try generic line number extraction
                    line_num = self.extract_line_number(text)
        
        if line_num is None:
            return HandlerResult(
                success=False,
                error="Could not determine line number"
            )
        
        # Extract content
        content = self.extract_content(text, full_message)
        if not content:
            # Try to extract from patterns
            for pattern in self.patterns:
                match = pattern.search(text)
                if match:
                    # Try to get content from match groups
                    if len(match.groups()) >= 3:
                        content = match.group(3).strip()
                    elif len(match.groups()) >= 2:
                        # Might be content before "in line"
                        content_match = re.search(
                            r'(.+?)\s+(?:in|at|on)\s+line',
                            text,
                            re.IGNORECASE
                        )
                        if content_match:
                            content = content_match.group(1).strip()
                    break
        
        if not content:
            return HandlerResult(
                success=False,
                error="Could not extract content to insert"
            )
        
        # Determine action type based on position
        if position == "before":
            action_type = "InsertBeforeLine"
        elif position == "after":
            action_type = "InsertAfterLine"
        else:  # position == "at"
            action_type = "InsertAtLine"
        
        return HandlerResult(
            success=True,
            action_type=action_type,
            params={
                "path": active_file,
                "line_number": line_num,
                "text": content
            },
            confidence=0.95
        )

