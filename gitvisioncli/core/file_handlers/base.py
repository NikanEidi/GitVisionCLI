"""
Base File Handler Interface

All file operation handlers inherit from this base class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import re


class FileHandlerPriority(Enum):
    """Priority levels for file handlers (higher = checked first)."""
    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    FALLBACK = 0


@dataclass
class HandlerResult:
    """Result from a file handler."""
    success: bool
    action_type: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    confidence: float = 0.0  # 0.0 to 1.0
    error: Optional[str] = None


class FileHandler(ABC):
    """
    Base class for all file operation handlers.
    
    Each handler is responsible for:
    1. Detecting if it can handle a given natural language instruction
    2. Parsing the instruction to extract parameters
    3. Returning a structured action
    """
    
    def __init__(self, priority: FileHandlerPriority = FileHandlerPriority.NORMAL):
        """
        Initialize the file handler.
        
        Args:
            priority: Priority level for this handler (higher = checked first)
        """
        self.priority = priority
        self.patterns = self._init_patterns()
    
    @abstractmethod
    def _init_patterns(self) -> List[re.Pattern]:
        """Initialize regex patterns for this handler."""
        pass
    
    @abstractmethod
    def can_handle(self, text: str, active_file: Optional[str] = None) -> float:
        """
        Check if this handler can process the given text.
        
        Returns:
            Confidence score (0.0 to 1.0) indicating how well this handler
            matches the instruction. 0.0 means no match, 1.0 means perfect match.
        """
        pass
    
    @abstractmethod
    def parse(self, text: str, active_file: Optional[str] = None, full_message: Optional[str] = None) -> HandlerResult:
        """
        Parse the instruction and return a structured action.
        
        Args:
            text: The instruction text
            active_file: Path to the currently active file (if any)
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
        - Quoted strings (single, double, triple quotes)
        - Multi-line content
        - Code blocks (```)
        - Content after keywords like "with", "to", "by", ":"
        """
        if keywords is None:
            keywords = ["with", "to", "by", ":"]
        
        # Try to extract from code blocks first
        code_block_match = re.search(r'```(?:\w+)?\n(.*?)```', full_message or text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # Try triple quotes
        triple_quote_match = re.search(r'"""([^"]*(?:"""[^"]*)*)"""', full_message or text, re.DOTALL)
        if triple_quote_match:
            return triple_quote_match.group(1).strip()
        
        triple_single_match = re.search(r"'''([^']*(?:'''[^']*)*)'''", full_message or text, re.DOTALL)
        if triple_single_match:
            return triple_single_match.group(1).strip()
        
        # Try to find content after keywords
        for keyword in keywords:
            # Pattern: keyword followed by content
            pattern = rf'\b{re.escape(keyword)}\s+(.+?)(?:\s+(?:in|at|to|from|of)\s+[^\s]+\s*$|$)'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Remove trailing punctuation that might be part of sentence
                content = re.sub(r'[.,;:!?]+$', '', content)
                if content:
                    return self._clean_quotes(content)
        
        # Try to extract quoted content
        quoted_match = re.search(r'["\']([^"\']*(?:\\.[^"\']*)*)["\']', full_message or text)
        if quoted_match:
            return quoted_match.group(1).strip()
        
        # Try to extract after colon (common pattern)
        colon_match = re.search(r':\s*(.+?)(?:\s+(?:in|at|to|from|of)\s+[^\s]+\s*$|$)', text, re.DOTALL)
        if colon_match:
            content = colon_match.group(1).strip()
            content = re.sub(r'[.,;:!?]+$', '', content)
            if content:
                return self._clean_quotes(content)
        
        return None
    
    def _clean_quotes(self, text: str) -> str:
        """Remove outer quotes if they wrap the entire content."""
        text = text.strip()
        # Only remove quotes if they wrap the entire string
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            # Check if there are matching quotes inside (don't strip if content has quotes)
            inner = text[1:-1]
            if '"' not in inner and "'" not in inner:
                return inner
        return text
    
    def extract_line_number(self, text: str) -> Optional[int]:
        """Extract line number from text."""
        # Match "line 5", "line5", "ln 5", "line:5", etc.
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
        """Extract line range from text."""
        # Match "lines 5-10", "lines 5 to 10", "line 5-10", etc.
        patterns = [
            r'\blines?\s+(\d+)\s*[-~]\s*(\d+)\b',
            r'\blines?\s+(\d+)\s+to\s+(\d+)\b',
            r'\blines?\s+(\d+)\s+through\s+(\d+)\b',
            r'\bline\s+(\d+)\s*[-~]\s*(\d+)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return (int(match.group(1)), int(match.group(2)))
        return None

