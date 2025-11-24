"""
Insert Operation Handler

Handles all insert operations:
- Insert at line
- Insert before line
- Insert after line
- Insert at top
"""

import re
from typing import Optional, List, Dict, Any
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
            # Variations: "add X at top", "insert X to beginning"
            re.compile(
                r'\b(insert|add|write|put|place|prepend)\s+(.+?)\s+(?:at|to)\s+(?:the\s+)?(?:top|beginning|start|head)\b',
                re.IGNORECASE | re.DOTALL
            ),
            # Match "prepend X" (without "at top")
            re.compile(
                r'\bprepend\s+(.+?)(?:\s|$)',
                re.IGNORECASE | re.DOTALL
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
            # Natural variations: "put X at line 5", "write X on line 5", "place X at line 5"
            re.compile(
                r'\b(insert|add|write|put|place)\s+(.+?)\s+(?:at|on|in)\s+line\s*(\d+)\b',
                re.IGNORECASE | re.DOTALL
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Check if this is an insert operation."""
        text_lower = text.lower()
        
        # Only handle if there's an active file (context-aware)
        if not context or not context.get("active_file"):
            return 0.0
        
        # Make sure it's not a git command
        if text_lower.startswith('git '):
            return 0.0  # Git command, not file operation
        
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
                return 0.95  # Higher confidence when active file exists
        
        # Check patterns
        for pattern in self.patterns:
            if pattern.search(text):
                return 0.95
        
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        """Parse insert instruction."""
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
        
        text_lower = text.lower()
        
        # Determine insert position
        line_num = None
        position = "after"  # default
        
        # Check for "at top" / "at beginning" / "at start"
        if re.search(r'\b(?:at|to)\s+(?:the\s+)?(?:top|beginning|start|head)\b', text_lower):
            # Extract content - try to get content before "at top"
            content = self.extract_content(text, full_message)
            if not content:
                # Try pattern: "add X at top" -> extract X
                content_match = re.search(
                    r'\b(?:add|insert|write|put|place|prepend)\s+(.+?)\s+(?:at|to)\s+(?:the\s+)?(?:top|beginning|start|head)\b',
                    text,
                    re.IGNORECASE | re.DOTALL
                )
                if content_match:
                    content = content_match.group(1).strip()
            return HandlerResult(
                success=True,
                action_type="InsertAtTop",
                params={
                    "path": active_file,
                    "text": content or ""
                },
                confidence=0.95
            )
        
        # Check for standalone "prepend X" (without "at top")
        if re.search(r'^prepend\s+', text_lower):
            content = self.extract_content(text, full_message)
            if not content:
                # Try pattern: "prepend X" -> extract X
                content_match = re.search(r'^prepend\s+(.+?)(?:\s|$)', text, re.IGNORECASE | re.DOTALL)
                if content_match:
                    content = content_match.group(1).strip()
            return HandlerResult(
                success=True,
                action_type="InsertAtTop",
                params={
                    "path": active_file,
                    "text": content or ""
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
        
        # Extract content - try multiple methods
        content = None
        
        # First, check if this is a multiline command (has ":" and newlines)
        if full_message and "\n" in full_message and ":" in full_message.split("\n", 1)[0]:
            # Multiline format: "insert at line 10:\ncontent..."
            first_line = full_message.split("\n", 1)[0]
            if ":" in first_line:
                # Extract everything after the first line
                content = "\n".join(full_message.split("\n")[1:]).strip()
        
        # If not multiline, try to extract content before "at line", "in line", etc.
        # Pattern: "insert import os at line 1" -> extract "import os"
        if not content:
            content_match = re.search(
                r'\b(?:insert|add|write|put|place)\s+(.+?)\s+(?:at|in|on|before|after)\s+line',
                text,
                re.IGNORECASE | re.DOTALL
            )
            if content_match:
                potential = content_match.group(1).strip()
                # Make sure it's not just "at" or a preposition
                if potential and potential.lower() not in ['at', 'in', 'on', 'before', 'after']:
                    content = potential
                    # Clean up any trailing punctuation
                    content = re.sub(r'[.,;:!?]+$', '', content).strip()
        
        # If no content from pattern, try extract_content method
        if not content:
            content = self.extract_content(text, full_message)
        
        # If still no content, try to extract from patterns
        if not content:
            for pattern in self.patterns:
                match = pattern.search(text)
                if match:
                    # Try to get content from match groups
                    if len(match.groups()) >= 3:
                        potential = match.group(3).strip()
                        # Make sure it's not just a number (line number)
                        if potential and not potential.isdigit():
                            content = potential
                    break
        
        # If still no content and we have full_message, try extracting from multiline
        if not content and full_message and "\n" in full_message:
            # Check if the command has ":" at the end of first line (multiline indicator)
            first_line = full_message.split("\n", 1)[0]
            if ":" in first_line and ("insert" in first_line.lower() or "add" in first_line.lower()):
                # Extract everything after the first line (command line)
                lines = full_message.split("\n")
                if len(lines) > 1:
                    # Skip the command line and get the rest
                    content = "\n".join(lines[1:]).strip()
            else:
                # Try to extract from after ":" if present
                if ":" in text:
                    # Split on first ":" only
                    parts = full_message.split(":", 1)
                    if len(parts) > 1:
                        potential = parts[1].strip()
                        # If it's multiline, take everything after the colon
                        if "\n" in potential:
                            content = potential
                        else:
                            # Single line after colon - might be part of command, check if there's more
                            if len(full_message.split("\n")) > 1:
                                # There are more lines, so take everything after first line
                                content = "\n".join(full_message.split("\n")[1:]).strip()
                            else:
                                content = potential
        
        if not content:
            return HandlerResult(
                success=False,
                error="Could not extract content to insert"
            )
        
        # Determine action type based on position
        # Map to valid ActionType enum values
        if position == "before":
            action_type = "InsertBeforeLine"
        elif position == "after":
            action_type = "InsertAfterLine"
        else:  # position == "at"
            # For "at line N", if N is 1, insert at top (before line 1)
            # Otherwise, insert before the line (pushes line N down)
            if line_num == 1:
                action_type = "InsertAtTop"
            else:
                action_type = "InsertBeforeLine"
        
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

