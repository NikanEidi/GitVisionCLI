# gitvisioncli/ui/__init__.py
"""
GitVisionCLI UI Module
Exports for cyberpunk terminal interface components.
"""

# Import the stabilized modules
from .banner import banner_with_info, startup_sequence
from .chat_box import (
    ChatBox,
    ConversationHistory,
    print_ai_message,
    print_user_message,
    print_system_message,
    print_error_message,
    AnimatedChatBox,
    STYLE_CYBER,
    STYLE_SLEEK,
    STYLE_MINIMAL,
)
from .dual_panel import (
    DualPanelRenderer,
    DualPanelConfig,
    clear_screen,
)

# --- STABILIZATION FIX ---
# Import the modules themselves so we can reference them
from . import colors
from . import glitch_effects

# Also import * to make colors available for other UI modules
from .colors import *
from .glitch_effects import *
# --- END FIX ---


# Define what is exported when a user imports `from gitvisioncli.ui import *`
__all__ = [
    # Banner/startup
    "banner_with_info",
    "startup_sequence",
    
    # Chat box classes
    "ChatBox",
    "ConversationHistory",
    "AnimatedChatBox",
    
    # Legacy print functions
    "print_ai_message",
    "print_user_message",
    "print_system_message",
    "print_error_message",
    
    # Premium box styles
    "STYLE_CYBER",
    "STYLE_SLEEK",
    "STYLE_MINIMAL",
    
    # Dual panel
    "DualPanelRenderer",
    "DualPanelConfig",
    "clear_screen",
]

# Dynamically add all public members from colors and glitch_effects
# This fixes the unpacking syntax error by extending the list
if hasattr(colors, "__all__"):
    __all__.extend(colors.__all__)
else:
    # Fallback if __all__ isn't defined in colors.py
    __all__.extend([k for k in colors.__dict__ if not k.startswith("_") and k != "annotations"]) 

if hasattr(glitch_effects, "__all__"):
    __all__.extend(glitch_effects.__all__)
else:
    # Fallback if __all__ isn't defined in glitch_effects.py
    __all__.extend([k for k in glitch_effects.__dict__ if not k.startswith("_") and k != "annotations"])