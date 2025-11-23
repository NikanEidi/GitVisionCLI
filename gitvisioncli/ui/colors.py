# gitvisioncli/ui/colors.py
"""
GitVisionCLI — Neon Cyberpunk Color System
ANSI color codes and gradient engine for terminal styling
"""

import random
from typing import List, Tuple

# ═══════════════════════════════════════════════════════════════
# NEON CYBERPUNK PALETTE
# ═══════════════════════════════════════════════════════════════

# Purple Spectrum (primary brand line) - ENHANCED VIBRANCY & FIXED ANSI
DEEP_VIOLET = "\033[38;5;54m"      # Deep background accent
NEON_PURPLE = "\033[38;5;165m"     # Primary brand / borders - ULTRA-VIBRANT
BRIGHT_MAGENTA = "\033[38;5;201m"  # High-energy highlights
LIGHT_PURPLE = "\033[38;5;141m"    # Softer accent for gradients
ULTRA_PURPLE = "\033[38;5;129m"    # Ultra-vibrant purple
PINK_NEON = "\033[38;5;213m"       # Bright pink accent
# Enhanced NEON_PURPLE variants for maximum visibility
NEON_PURPLE_BOLD = "\033[1;38;5;165m"  # Bold neon purple
NEON_PURPLE_GLOW = "\033[1;38;5;165m"   # Glowing neon purple

# Cyan Accents (secondary brand line) - ENHANCED VIBRANCY
ELECTRIC_CYAN = "\033[38;5;51m"    # Primary accent / links
DEEP_CYAN = "\033[38;5;39m"        # Secondary accent / user borders
TEAL = "\033[38;5;45m"             # Ambient glow / matrix effects
BRIGHT_CYAN = "\033[38;5;87m"      # Ultra-bright cyan
AQUA = "\033[38;5;122m"            # Aqua green-cyan blend

# Grayscale (for scanlines / muted text) - OPTIMIZED FOR VISIBILITY
DARK_GRAY = "\033[38;5;240m"       # Frame shading / scanlines (brighter)
MID_GRAY = "\033[38;5;250m"        # Muted labels (much brighter, almost white)
LIGHT_GRAY = "\033[38;5;252m"      # Subtle highlights (very bright)
WHITE = "\033[38;5;15m"            # Pure white text
OFF_WHITE = "\033[38;5;255m"       # Soft white for backgrounds

# Glitch Colors (alerts / matrix) - ENHANCED
GLITCH_RED = "\033[38;5;196m"      # Errors / critical alerts
GLITCH_GREEN = "\033[38;5;46m"     # Matrix-style output / success pulses
NEON_YELLOW = "\033[38;5;226m"     # Bright yellow for warnings
NEON_ORANGE = "\033[38;5;208m"     # Orange accent

# Background Colors (for contrast)
BG_DARK = "\033[48;5;235m"         # Dark background
BG_DARKER = "\033[48;5;232m"       # Very dark background
BG_PURPLE = "\033[48;5;54m"        # Purple background tint

# Backwards-compat alias (used by cli.py)
RED = GLITCH_RED

# ═══════════════════════════════════════════════════════════════
# TEXT STYLES
# ═══════════════════════════════════════════════════════════════

BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
RAPID_BLINK = "\033[6m"
REVERSE = "\033[7m"
HIDDEN = "\033[8m"

RESET = "\033[0m"

# ═══════════════════════════════════════════════════════════════
# SEMANTIC COLOR ROLES
# ═══════════════════════════════════════════════════════════════

# High-level semantic aliases (for consistent styling) - ENHANCED
PRIMARY_FG = NEON_PURPLE          # Brand / main borders
ACCENT_FG = ELECTRIC_CYAN         # Headings / active labels
ACCENT_ALT_FG = BRIGHT_MAGENTA    # Secondary accent (AI, model names)
ACCENT_ULTRA_FG = BRIGHT_CYAN     # Ultra-bright accents
ACCENT_WARM_FG = PINK_NEON        # Warm accent for highlights
MUTED_FG = MID_GRAY               # Hints / secondary text
MUTED_DARK_FG = DARK_GRAY         # Frames / scanlines / separators
ERROR_FG = GLITCH_RED             # Errors / warnings
SUCCESS_FG = GLITCH_GREEN         # Success indicators
WARNING_FG = NEON_YELLOW          # Warnings / notices

# Chat / console roles (used by ChatBox and system messages)
CHAT_BORDER_USER = DEEP_CYAN
CHAT_BORDER_AI = NEON_PURPLE
CHAT_BORDER_SYSTEM = DARK_GRAY
CHAT_BORDER_ERROR = GLITCH_RED

CHAT_TEXT_USER = f"{BOLD}{ELECTRIC_CYAN}"
CHAT_TEXT_AI = BRIGHT_MAGENTA
CHAT_TEXT_SYSTEM = f"{DIM}{WHITE}"
CHAT_TEXT_ERROR = GLITCH_RED

CHAT_LABEL_USER = f"{BOLD}{ELECTRIC_CYAN}"
CHAT_LABEL_AI = f"{BOLD}{BRIGHT_MAGENTA}"
CHAT_LABEL_SYSTEM = f"{BOLD}{MID_GRAY}"
CHAT_LABEL_ERROR = f"{BOLD}{GLITCH_RED}"

# ═══════════════════════════════════════════════════════════════
# COLOR UTILITIES
# ═══════════════════════════════════════════════════════════════

def colorize(text: str, color: str, style: str = "") -> str:
    """Apply color and optional style to text"""
    return f"{style}{color}{text}{RESET}"

def gradient(text: str, colors: List[str]) -> str:
    """
    Apply color gradient across text.
    Each character cycles through the color list.
    """
    if not text or not colors:
        return text
    
    result = []
    color_count = len(colors)
    
    for i, char in enumerate(text):
        color = colors[i % color_count]
        result.append(f"{color}{char}")
    
    result.append(RESET)
    return "".join(result)

def purple_gradient(text: str) -> str:
    """Apply signature purple gradient"""
    return gradient(text, [
        DEEP_VIOLET,
        NEON_PURPLE,
        BRIGHT_MAGENTA,
        NEON_PURPLE,
    ])

def cyber_gradient(text: str) -> str:
    """Apply purple-cyan cyberpunk gradient"""
    return gradient(text, [
        DEEP_VIOLET,
        NEON_PURPLE,
        BRIGHT_MAGENTA,
        ELECTRIC_CYAN,
        DEEP_CYAN,
        BRIGHT_MAGENTA,
        NEON_PURPLE,
    ])

def pulse_color() -> str:
    """Return random color from neon palette for pulse effect"""
    return random.choice([
        NEON_PURPLE,
        BRIGHT_MAGENTA,
        ELECTRIC_CYAN,
        LIGHT_PURPLE,
    ])

def glitch_color() -> str:
    """Return random glitch color"""
    return random.choice([
        GLITCH_RED,
        GLITCH_GREEN,
        ELECTRIC_CYAN,
        BRIGHT_MAGENTA,
    ])

# ═══════════════════════════════════════════════════════════════
# RGB TO ANSI CONVERTER (for custom gradients)
# ═══════════════════════════════════════════════════════════════

def rgb_to_ansi(r: int, g: int, b: int) -> str:
    """Convert RGB to ANSI 256 color code"""
    # Use 216-color cube: 16 + 36×r + 6×g + b
    r_idx = int(r / 255 * 5)
    g_idx = int(g / 255 * 5)
    b_idx = int(b / 255 * 5)
    code = 16 + (36 * r_idx) + (6 * g_idx) + b_idx
    return f"\033[38;5;{code}m"

def hex_to_ansi(hex_color: str) -> str:
    """Convert hex color to ANSI"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return rgb_to_ansi(r, g, b)

# ═══════════════════════════════════════════════════════════════
# PRESET THEMES
# ═══════════════════════════════════════════════════════════════

THEMES = {
    "neon_purple": [DEEP_VIOLET, NEON_PURPLE, BRIGHT_MAGENTA],
    "cyber_mix": [DEEP_VIOLET, NEON_PURPLE, ELECTRIC_CYAN, BRIGHT_MAGENTA],
    "matrix": [GLITCH_GREEN, ELECTRIC_CYAN, TEAL],
    "blood": [GLITCH_RED, BRIGHT_MAGENTA, DEEP_VIOLET],
    "ice": [ELECTRIC_CYAN, LIGHT_PURPLE, WHITE],
}

def apply_theme(text: str, theme_name: str = "neon_purple") -> str:
    """Apply preset color theme"""
    colors = THEMES.get(theme_name, THEMES["neon_purple"])
    return gradient(text, colors)

# ═══════════════════════════════════════════════════════════════
# GLOW EFFECT
# ═══════════════════════════════════════════════════════════════

def glow(text: str, color: str = NEON_PURPLE) -> str:
    """Create neon glow effect using bold + color"""
    return f"{BOLD}{color}{text}{RESET}"

def mega_glow(text: str) -> str:
    """Ultra-bright glow effect"""
    return f"{BOLD}{BRIGHT_MAGENTA}{text}{RESET}"
