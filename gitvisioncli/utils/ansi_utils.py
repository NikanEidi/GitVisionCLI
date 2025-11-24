"""
ANSI Code Stripping Utilities

Comprehensive ANSI escape sequence removal for file content.
Handles both full ANSI sequences and corrupted/partial sequences.
"""

import re

# Comprehensive ANSI escape sequence patterns
# Full ANSI sequences: \x1b[ or \033[ followed by digits/semicolons and command char
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\033\[[0-9;]*[a-zA-Z]")
# Corrupted ANSI sequences (missing ESC prefix)
# Matches and removes:
# - [number;m (bracket is part of corruption, remove entirely)
# - standalone number;m (remove entirely)
# Note: We don't match (number;m because ( might be valid syntax (e.g., function calls)
# The standalone number;m pattern will catch cases like print(38;5;46m"text")
CORRUPTED_ANSI_RE = re.compile(r"\[[0-9;]+m|[0-9;]+m")


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape sequences from text, including partial/corrupted ones.
    
    This function handles:
    - Full ANSI sequences: \x1b[38;5;46m, \033[0m, etc.
    - Corrupted sequences: 38;5;46m, [38;5;46m (missing ESC prefix)
    
    Args:
        text: Input text that may contain ANSI codes
        
    Returns:
        Text with all ANSI codes removed
    """
    if not text:
        return text
    
    # First remove full ANSI sequences
    text = ANSI_RE.sub("", text)
    # Then remove any corrupted/partial ANSI sequences
    text = CORRUPTED_ANSI_RE.sub("", text)
    return text


def visible_len(text: str) -> int:
    """
    Get visible length of text ignoring ANSI codes.
    
    Args:
        text: Input text that may contain ANSI codes
        
    Returns:
        Length of text without ANSI codes
    """
    return len(strip_ansi(text))

