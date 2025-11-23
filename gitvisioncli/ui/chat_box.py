# gitvisioncli/ui/chat_box.py
"""
GitVisionCLI — Chat Box Message Renderer
Premium cyberpunk message boxes with refined ASCII and neon styling.
"""

import re
import textwrap
from typing import List, Literal, Optional
from dataclasses import dataclass

# Import the stabilized color palette
from gitvisioncli.ui.colors import (
    RESET,
    DIM,
    NEON_PURPLE,
    CHAT_BORDER_USER,
    CHAT_BORDER_AI,
    CHAT_BORDER_SYSTEM,
    CHAT_BORDER_ERROR,
    CHAT_TEXT_USER,
    CHAT_TEXT_AI,
    CHAT_TEXT_SYSTEM,
    CHAT_TEXT_ERROR,
    CHAT_LABEL_USER,
    CHAT_LABEL_AI,
    CHAT_LABEL_SYSTEM,
    CHAT_LABEL_ERROR,
)

# ═══════════════════════════════════════════════════════════════
# ANSI HELPERS
# ═══════════════════════════════════════════════════════════════

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def strip_ansi(text: str) -> str:
    """Remove ANSI color codes from text."""
    return ANSI_RE.sub("", text)

def visible_len(text: str) -> int:
    """Length of text without ANSI codes."""
    return len(strip_ansi(text))

# ═══════════════════════════════════════════════════════════════
# PREMIUM BOX STYLES
# ═══════════════════════════════════════════════════════════════

@dataclass
class BoxStyle:
    """Border character sets for box styles."""
    tl: str  # top-left
    tr: str  # top-right
    bl: str  # bottom-left
    br: str  # bottom-right
    h: str   # horizontal
    v: str   # vertical

# Premium cyberpunk styles
STYLE_CYBER = BoxStyle(tl="╔", tr="╗", bl="╚", br="╝", h="═", v="║")
STYLE_SLEEK = BoxStyle(tl="┏", tr="┓", bl="┗", br="┛", h="━", v="┃")
STYLE_MINIMAL = BoxStyle(tl="┌", tr="┐", bl="└", br="┘", h="─", v="│")

# ═══════════════════════════════════════════════════════════════
# CHAT BOX RENDERER
# ═══════════════════════════════════════════════════════════════

class ChatBox:
    """
    Premium cyberpunk message renderer.
    Pure rendering - no I/O.
    """
    
    def __init__(self, width: int = 60, padding: int = 2):
        """
        Args:
            width: Total box width (including borders)
            padding: Internal padding spaces (default 2 for premium look)
        """
        self.width = max(30, width)
        self.padding = padding
    
    def _wrap_text(self, text: str) -> List[str]:
        """Wrap text with proper line breaks, aware of existing newlines."""
        # Calculate the actual drawable content width
        content_width = self.width - (2 * self.padding) - 2 # 2 for borders
        
        if content_width <= 0:
            return [text]
        
        lines: List[str] = []
        # Split by existing newlines first
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("") # Preserve empty lines
                continue
            
            # Wrap the individual paragraph
            wrapped = textwrap.wrap(
                paragraph, 
                width=content_width,
                break_long_words=False,
                break_on_hyphens=False
            )
            
            # Add wrapped lines, or a single empty string if wrapping an empty line
            lines.extend(wrapped if wrapped else [""])
        
        return lines
    
    def _pad_line(self, text: str, target_width: int) -> str:
        """Pad text accounting for ANSI codes."""
        vis_len = visible_len(text)
        if vis_len < target_width:
            return text + " " * (target_width - vis_len)
        return text
    
    def render(
        self,
        text: str,
        role: Literal["user", "ai", "system", "error"] = "ai",
        style: BoxStyle = STYLE_CYBER
    ) -> str:
        """
        Render message in premium cyberpunk box.
        
        Args:
            text: Message content
            role: Message type
            style: Box border style
        """
        # Role-based color schemes (centralised in ui.colors).
        # Border color is always NEON_PURPLE for a consistent neon frame;
        # label/text colors remain role-specific.
        if role == "user":
            label = "◉ USER"
            text_color = CHAT_TEXT_USER
            border_color = NEON_PURPLE
            label_color = CHAT_LABEL_USER
        elif role == "ai":
            label = "◉ AI"
            text_color = CHAT_TEXT_AI
            border_color = NEON_PURPLE
            label_color = CHAT_LABEL_AI
        elif role == "system":
            label = "◉ SYSTEM"
            text_color = CHAT_TEXT_SYSTEM
            border_color = NEON_PURPLE
            label_color = CHAT_LABEL_SYSTEM
        else:  # error
            label = "⚠ ERROR"
            text_color = CHAT_TEXT_ERROR
            border_color = NEON_PURPLE
            label_color = CHAT_LABEL_ERROR
        
        lines: List[str] = []
        content_width = self.width - (2 * self.padding) - 2
        pad_str = " " * self.padding
        
        # --- Top border ---
        top = (
            f"{border_color}{style.tl}"
            f"{style.h * (self.width - 2)}"
            f"{style.tr}{RESET}"
        )
        lines.append(top)
        
        # --- Header with label ---
        header_text = f"{label_color}{label}{RESET}"
        header_padded = self._pad_line(header_text, content_width)
        header_line = (
            f"{border_color}{style.v}{RESET}"
            f"{pad_str}{header_padded}{pad_str}"
            f"{border_color}{style.v}{RESET}"
        )
        lines.append(header_line)
        
        # --- Separator ---
        sep_line = (
            f"{border_color}{style.v}{RESET}"
            # Use spaces for the separator for a cleaner look
            f"{' ' * (self.width - 2)}"
            f"{border_color}{style.v}{RESET}"
        )
        lines.append(sep_line)
        
        # --- Content ---
        wrapped = self._wrap_text(text)
        for line in wrapped:
            colored = f"{text_color}{line}{RESET}" if line.strip() else ""
            padded = self._pad_line(colored, content_width)
            content_line = (
                f"{border_color}{style.v}{RESET}"
                f"{pad_str}{padded}{pad_str}"
                f"{border_color}{style.v}{RESET}"
            )
            lines.append(content_line)
        
        # --- Bottom separator ---
        lines.append(sep_line)
        
        # --- Bottom border ---
        bottom = (
            f"{border_color}{style.bl}"
            f"{style.h * (self.width - 2)}"
            f"{style.br}{RESET}"
        )
        lines.append(bottom)
        
        return "\n".join(lines)
    
    def render_user(self, text: str) -> str:
        """Render user message - electric cyan theme."""
        return self.render(text, role="user", style=STYLE_CYBER)
    
    def render_ai(self, text: str) -> str:
        """Render AI message - magenta/purple theme."""
        return self.render(text, role="ai", style=STYLE_CYBER)
    
    def render_system(self, text: str) -> str:
        """Render system message - minimal gray theme."""
        return self.render(text, role="system", style=STYLE_MINIMAL)
    
    def render_error(self, text: str) -> str:
        """Render error message - red alert theme."""
        return self.render(text, role="error", style=STYLE_SLEEK)


# ═══════════════════════════════════════════════════════════════
# CONVERSATION HISTORY
# ═══════════════════════════════════════════════════════════════

class ConversationHistory:
    """
    Manages a list of rendered message blocks.
    This is the object that will be rendered in the left panel.
    """
    
    def __init__(self, width: int = 60):
        self.width = width
        self.box = ChatBox(width=width, padding=2)
        self.blocks: List[str] = []
        # Track the last error message so the CLI can surface it
        # in the status bar without having to intercept every call site.
        self.last_error: Optional[str] = None
    
    def add_user(self, text: str) -> None:
        """Add user message."""
        self.blocks.append(self.box.render_user(text))
        # A new user turn indicates the previous error has been
        # acknowledged, so clear any stale status-bar error.
        self.last_error = None
    
    def add_ai(self, text: str) -> None:
        """Add AI message."""
        self.blocks.append(self.box.render_ai(text))
        # Successful AI output should clear previous errors from the
        # status bar so it reflects only the most recent failure.
        self.last_error = None
    
    def add_system(self, text: str) -> None:
        """Add system message."""
        self.blocks.append(self.box.render_system(text))
        # System-level notices (mode switches, info banners, etc.)
        # also clear any previous error indicator.
        self.last_error = None
    
    def add_error(self, text: str) -> None:
        """Add error message."""
        self.blocks.append(self.box.render_error(text))
        # Flatten newlines so the status bar can show a concise summary.
        self.last_error = text.strip().replace("\n", " ") or None
    
    def clear(self) -> None:
        """Clear history."""
        self.blocks.clear()
    
    def render(self) -> str:
        """Render full conversation with spacing."""
        # Use a single newline for a tighter fit in the dual panel
        return "\n".join(self.blocks)
    
    def get_last_n(self, n: int) -> str:
        """Get last N messages."""
        if n <= 0:
            return ""
        return "\n".join(self.blocks[-n:])


# ═══════════════════════════════════════════════════════════════
# LEGACY COMPATIBILITY
# ═══════════════════════════════════════════════════════════════

def print_ai_message(text: str, animated: bool = False, width: int = 70) -> None:
    """Legacy print function."""
    box = ChatBox(width=width)
    print(box.render_ai(text))

def print_user_message(text: str, width: int = 70) -> None:
    """Legacy print function."""
    box = ChatBox(width=width)
    print(box.render_user(text))

def print_system_message(text: str, width: int = 70) -> None:
    """Legacy print function."""
    box = ChatBox(width=width)
    print(box.render_system(text))

def print_error_message(text: str, width: int = 70) -> None:
    """Legacy print function."""
    box = ChatBox(width=width)
    print(box.render_error(text))

class AnimatedChatBox(ChatBox):
    """Legacy compatibility wrapper."""
    
    def display_thinking(self, duration: float = 0.7) -> None:
        """Thinking animation."""
        import time
        print(f"{DIM}{NEON_PURPLE}⚡ Processing...{RESET}", end="", flush=True)
        time.sleep(duration)
        # Clear the "Processing" line
        print("\r" + " " * 30 + "\r", end="", flush=True)
