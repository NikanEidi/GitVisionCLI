"""
Base Handler Interface

All handlers inherit from this base class, providing a consistent interface
for parsing natural language and executing actions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
import re


class HandlerPriority(Enum):
    """Priority levels for handlers (higher = checked first)."""
    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    FALLBACK = 0


@dataclass
class HandlerResult:
    """
    Result from a handler's parse operation.
    
    Attributes:
        success: Whether the handler successfully parsed the instruction
        action_type: The action type to execute (e.g., "CreateFile", "GitAdd")
        params: Parameters for the action
        confidence: Confidence score (0.0 to 1.0) - how certain the handler is
        error: Error message if parsing failed
        priority: Priority of this handler result
        metadata: Additional metadata about the parsing
    """
    success: bool
    action_type: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    confidence: float = 0.0  # 0.0 to 1.0
    error: Optional[str] = None
    priority: HandlerPriority = HandlerPriority.NORMAL
    metadata: Optional[Dict[str, Any]] = None


class BaseHandler(ABC):
    """
    Base class for all operation handlers.
    
    Each handler is responsible for:
    1. Detecting if it can handle a given natural language instruction
    2. Parsing the instruction to extract parameters
    3. Returning a structured action result
    
    Handlers are organized by category (File, Git, GitHub, etc.) and
    can be easily extended or replaced.
    """
    
    def __init__(self, priority: HandlerPriority = HandlerPriority.NORMAL):
        """
        Initialize the handler.
        
        Args:
            priority: Priority level for this handler (higher = checked first)
        """
        self.priority = priority
        self.patterns = self._init_patterns()
        self.synonyms = self._init_synonyms()
    
    @abstractmethod
    def _init_patterns(self) -> List[re.Pattern]:
        """
        Initialize regex patterns for this handler.
        
        Returns:
            List of compiled regex patterns
        """
        pass
    
    def _init_synonyms(self) -> Dict[str, List[str]]:
        """
        Initialize synonyms for keywords.
        
        Returns:
            Dictionary mapping canonical keywords to lists of synonyms
        """
        return {}
    
    @abstractmethod
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Check if this handler can process the given text.
        
        Args:
            text: The instruction text
            context: Optional context (e.g., active_file, workspace state)
        
        Returns:
            Confidence score (0.0 to 1.0) indicating how well this handler
            matches the instruction. 0.0 means no match, 1.0 means perfect match.
        """
        pass
    
    @abstractmethod
    def parse(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        full_message: Optional[str] = None
    ) -> HandlerResult:
        """
        Parse the instruction and return a structured action.
        
        Args:
            text: The instruction text
            context: Optional context (e.g., active_file, workspace state)
            full_message: The complete user message (for context)
        
        Returns:
            HandlerResult with action details
        """
        pass
    
    def extract_content(
        self,
        text: str,
        full_message: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Extract content from natural language instruction.
        
        Handles:
        - Code blocks (```)
        - Triple quotes (double and single)
        - Quoted strings (single, double)
        - Multi-line content
        - Content after keywords (with, to, by, :)
        
        Args:
            text: The instruction text
            full_message: The complete user message
            keywords: Keywords to look for (default: ["with", "to", "by", ":"])
        
        Returns:
            Extracted content or None
        """
        if keywords is None:
            keywords = ["with", "to", "by", ":"]
        
        # Try to extract from code blocks first
        # Fix: Use [a-zA-Z0-9_] instead of \w to avoid SyntaxWarning
        code_block_match = re.search(r'```(?:[a-zA-Z0-9_]+)?\n(.*?)```', full_message or text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # Try triple quotes (double quotes)
        triple_quote_match = re.search(r'"""([^"]*(?:"""[^"]*)*)"""', full_message or text, re.DOTALL)
        if triple_quote_match:
            return triple_quote_match.group(1).strip()
        
        # Try triple quotes (single quotes) - use escaped single quotes to avoid string literal issues
        triple_single_pattern = r'\'\'\'([^\']*(?:\'\'[^\']*)*)\'\'\''
        triple_single_match = re.search(triple_single_pattern, full_message or text, re.DOTALL)
        if triple_single_match:
            return triple_single_match.group(1).strip()
        
        # Try to find content after keywords
        for keyword in keywords:
            pattern = rf'\b{re.escape(keyword)}\s+(.+?)(?:\s+(?:in|at|to|from|of)\s+[^\s]+\s*$|$)'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                content = re.sub(r'[.,;:!?]+$', '', content)
                if content:
                    return self._clean_quotes(content)
        
        # Try to extract quoted content
        quoted_match = re.search(r'["\']([^"\']*(?:\\.[^"\']*)*)["\']', full_message or text)
        if quoted_match:
            return quoted_match.group(1).strip()
        
        # Try to extract after colon
        colon_match = re.search(r':\s*(.+?)(?:\s+(?:in|at|to|from|of)\s+[^\s]+\s*$|$)', text, re.DOTALL)
        if colon_match:
            content = colon_match.group(1).strip()
            content = re.sub(r'[.,;:!?]+$', '', content)
            if content:
                return self._clean_quotes(content)
        
        return None
    
    def _clean_quotes(self, text: str) -> str:
        """
        Remove outer quotes if they wrap the entire content.
        
        Args:
            text: Text to clean
        
        Returns:
            Cleaned text
        """
        text = text.strip()
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            inner = text[1:-1]
            if '"' not in inner and "'" not in inner:
                return inner
        return text
    
    def extract_line_number(self, text: str) -> Optional[int]:
        """
        Extract line number from text.
        
        Supports: "line 5", "line5", "ln 5", "line:5", etc.
        
        Args:
            text: Text to search
        
        Returns:
            Line number or None
        """
        patterns = [
            r'\bline\s*:?\s*(\d+)\b',
            r'\bln\s*:?\s*(\d+)\b',
            r'\bline\s+number\s+(\d+)\b',
            r'\bat\s+line\s+(\d+)\b',
            r'\bon\s+line\s+(\d+)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None
    
    def extract_line_range(self, text: str) -> Optional[Tuple[int, int]]:
        """
        Extract line range from text.
        
        Supports: "lines 5-10", "lines 5 to 10", "line 5-10", etc.
        
        Args:
            text: Text to search
        
        Returns:
            Tuple of (start, end) line numbers or None
        """
        patterns = [
            r'\blines?\s+(\d+)\s*[-~]\s*(\d+)\b',
            r'\blines?\s+(\d+)\s+to\s+(\d+)\b',
            r'\blines?\s+(\d+)\s+through\s+(\d+)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return (int(match.group(1)), int(match.group(2)))
        return None
    
    def extract_file_path(self, text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Extract file path from text.
        
        Supports:
        - Quoted paths: "my file.txt", 'my file.txt'
        - Unquoted paths: app.py, src/main.py
        - Context-aware: uses active_file if no path specified
        
        Args:
            text: Text to search
            context: Optional context with active_file
        
        Returns:
            File path or None
        """
        # Try quoted path first
        quoted_match = re.search(r'["\']([^"\']+)["\']', text)
        if quoted_match:
            return quoted_match.group(1).strip()
        
        # Try to extract from common patterns
        patterns = [
            r'\b(?:file|path)\s+([^\s]+)',
            r'\b([^\s]+\.(?:py|js|ts|java|cpp|c|h|txt|md|json|yaml|yml|xml|html|css))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Use active file from context if available
        if context and "active_file" in context:
            active_file = context["active_file"]
            if isinstance(active_file, str):
                return active_file
            elif hasattr(active_file, "path"):
                return active_file.path
        
        return None

