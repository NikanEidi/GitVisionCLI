# gitvisioncli/ui/banner.py
"""
GitVisionCLI — Banner, Info, and Startup Sequence
Handles the responsive ASCII art, startup animation, and info display.
"""

import shutil
import time
import random
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass

# Import from our stabilized UI files
from .colors import (
    RESET, BOLD, DIM,
    NEON_PURPLE, BRIGHT_MAGENTA, ELECTRIC_CYAN, DEEP_VIOLET,
    GLITCH_RED, GLITCH_GREEN, MID_GRAY, DARK_GRAY,
    THEMES, gradient, glitch_color
)
from .glitch_effects import GLITCH_CHARS, MATRIX_CHARS, glitch_line

# ═══════════════════════════════════════════════════════════════
# ASCII ART
# ═══════════════════════════════════════════════════════════════

# This is the primary banner used by the CLI
BANNER_FULL = r"""
  ██████╗   ██╗████████╗██╗   ██╗██╗███████╗  ██╗ ██████╗ ███╗   ██╗
  ██╔════╝  ██║╚══██╔══╝██║   ██║██║██╔════╝  ██║██╔═══██╗████╗  ██║
  ██║  ███╗ ██║   ██║   ██║   ██║██║███████╗ ╱██║██║   ██║██╔██╗ ██║
  ██║   ██║ ██║   ██║   ╚██╗ ██╔╝██║╚════██ ╱~⟡~╲██║   ██║██║╚██╗██║
  ╚██████╔╝ ██║   ██║    ╚████╔╝ ██║███████ ~░▓░~╲█████╔╝ ██║ ╚████║
   ╚═════╝  ╚═╝   ╚═╝     ╚═══╝  ╚═╝╚═════  ╱░◉░╲ ╚════╝  ╚═╝  ╚═══╝
                        ╲░▓░╱
                            ╲~╱   
"""

BANNER_COMPACT = r"""
 ╔═══════════════════════════════════════════════════╗
 ║   ██████╗ ██╗████████╗██╗   ██╗                   ║
 ║  ██╔════╝ ██║╚══██╔══╝██║   ██║                   ║
 ║  ██║  ███╗██║   ██║   ██║   ██║ ╱~⟡~╲             ║
 ║  ╚██████╔╝██║   ██║    ╚████╔╝  ~░◉░~             ║
 ║   ╚═════╝ ╚═╝   ╚═╝     ╚═══╝    ╲~╱              ║
 ╠═══════════════════════════════════════════════════╣
 ║   ⚡ GITVISION CLI — CYBER SERPENT EDITION ⚡       ║
 ╚═══════════════════════════════════════════════════╝
"""

BANNER_MINIMAL = r"""
 ┌────────────────────────────────┐
 │ ╔═╗╦╔╦╗╦  ╦╦╔═╗╦╔═╗╔╗╔  ╔═╗╦  ╦│
 │ ║ ╦║ ║ ╚╗╔╝║╚═╗║║ ║║║║  ║  ║  ║│
 │ ╚═╝╩ ╩  ╚╝ ╩╚═╝╩╚═╝╝╚╝  ╚═╝╩═╝╩│
 │          ~⟡~  Cyber Snake      │
 └────────────────────────────────┘
"""

# Snake components for animation
SNAKE_BODY_CHARS = ['~', '░', '▓', '═', '─']
SNAKE_EYE_CHARS = ['◉', '⦿', '●', '⟡']
SNAKE_DIAGONAL = ['╱', '╲', '╳']

# Application metadata
TAGLINE = "» AUTONOMOUS CODE VISION SYSTEM «"
VERSION = "v1.0.0"
SUBTITLE = "⚡ NEON CYBER SERPENT EDITION ⚡"

# Layout thresholds
MIN_WIDTH_FULL = 70      # Minimum width for full banner
MIN_WIDTH_COMPACT = 54   # Minimum width for compact banner
FALLBACK_WIDTH = 80      # Default if detection fails

# Animation constants
ANIMATION_FRAME_DELAY = 0.08
TYPEWRITER_CHAR_DELAY = 0.005
PULSE_CYCLES = 2
MATRIX_LINE_DELAY = 0.08

# ═══════════════════════════════════════════════════════════════
# TERMINAL SIZE DETECTION
# ═══════════════════════════════════════════════════════════════

def get_terminal_width() -> int:
    """Get current terminal width with fallback."""
    try:
        size = shutil.get_terminal_size(fallback=(FALLBACK_WIDTH, 24))
        return size.columns
    except Exception:
        return FALLBACK_WIDTH

def get_banner_for_width(width: int) -> Tuple[str, str]:
    """Select appropriate banner variant based on terminal width."""
    if width >= MIN_WIDTH_FULL:
        return BANNER_FULL, 'full'
    elif width >= MIN_WIDTH_COMPACT:
        return BANNER_COMPACT, 'compact'
    else:
        return BANNER_MINIMAL, 'minimal'

# ═══════════════════════════════════════════════════════════════
# ANSI-AWARE TEXT UTILITIES
# ═══════════════════════════════════════════════════════════════

def strip_ansi(text: str) -> str:
    """Remove all ANSI escape codes from text."""
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_pattern.sub('', text)

def visible_length(text: str) -> int:
    """Get visible length of text (excluding ANSI codes)"""
    return len(strip_ansi(text))

def center_text(text: str, width: Optional[int] = None, fill_char: str = " ") -> str:
    """Center text within terminal width, accounting for ANSI codes."""
    if width is None:
        width = get_terminal_width()
    
    vis_len = visible_length(text)
    
    if vis_len >= width:
        return text
    
    padding = width - vis_len
    left_pad = padding // 2
    
    # We must pad *outside* the ANSI-formatted string
    return (fill_char * left_pad) + text

def pad_line_to_width(line: str, width: Optional[int] = None, align: str = 'center') -> str:
    """Pad a line to specified width with alignment."""
    if width is None:
        width = get_terminal_width()
    
    vis_len = visible_length(line)
    
    if vis_len >= width:
        return line
    
    padding = width - vis_len
    
    if align == 'center':
        left_pad = padding // 2
        right_pad = padding - left_pad
        return (" " * left_pad) + line + (" " * right_pad)
    elif align == 'left':
        return line + (" " * padding)
    else:  # right
        return (" " * padding) + line

# ═══════════════════════════════════════════════════════════════
# BANNER DISPLAY MODES
# ═══════════════════════════════════════════════════════════════

class BannerMode:
    """Available banner display modes"""
    CLEAN = "clean"
    GLITCH = "glitch"
    ANIMATED = "animated"
    PULSE = "pulse"
    CYBERPUNK = "cyberpunk"
    MATRIX = "matrix"
    GLITCH_PULSE = "glitch_pulse"
    SNAKE_ANIMATE = "snake_animate"

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

@dataclass
class BannerConfig:
    """Configuration for banner rendering"""
    theme: str = "neon_purple"
    glitch_intensity: float = 0.12
    flicker_enabled: bool = True
    shake_intensity: int = 1
    auto_responsive: bool = True

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def apply_color_theme(line: str, theme_colors: List[str], line_index: int) -> str:
    """Apply color theme to a single line using cycling logic"""
    color = theme_colors[line_index % len(theme_colors)]
    return f"{BOLD}{color}{line}{RESET}"

def apply_glitch_layer(line: str, intensity: float, colored: bool = True) -> str:
    """Apply glitch distortion with controlled intensity"""
    if not line or intensity <= 0:
        return line
    
    glitched = ""
    for char in line:
        if char.strip() and random.random() < intensity:
            glitch_char = random.choice(GLITCH_CHARS + MATRIX_CHARS)
            if colored:
                glitched += f"{glitch_color()}{glitch_char}{RESET}"
            else:
                glitched += glitch_char
        else:
            glitched += char
    
    return glitched

def apply_subtle_shake(line: str, intensity: int = 1) -> str:
    """Apply mild horizontal shake for motion effect"""
    if intensity <= 0:
        return line
    shake_amount = random.randint(0, intensity)
    return " " * shake_amount + line

def apply_neon_flicker(line: str, color: str) -> str:
    """Simulate neon tube flicker with random brightness states"""
    flicker_chance = random.random()
    
    if flicker_chance < 0.15:
        return f"{DIM}{color}{line}{RESET}"
    elif flicker_chance < 0.30:
        return f"{color}{line}{RESET}"
    else:
        return f"{BOLD}{color}{line}{RESET}"

def clear_screen_and_home() -> None:
    """Hard terminal reset (clears scrollback) and homes cursor."""
    print("\033c", end="", flush=True)

def move_cursor_up(lines: int) -> None:
    """Move cursor up by specified number of lines"""
    print(f"\033[{lines}A", end="", flush=True)

def animate_snake_char(frame: int) -> str:
    """Return animated snake character for given frame."""
    chars = SNAKE_BODY_CHARS
    colors = [NEON_PURPLE, BRIGHT_MAGENTA, ELECTRIC_CYAN]
    
    char = chars[frame % len(chars)]
    color = colors[frame % len(colors)]
    
    return f"{BOLD}{color}{char}{RESET}"

# ═══════════════════════════════════════════════════════════════
# RESPONSIVE BANNER CLASS
# ═══════════════════════════════════════════════════════════════

class Banner:
    """Responsive banner renderer that adapts to terminal width."""
    
    def __init__(self, 
                 ascii_art: Optional[str] = None,
                 config: Optional[BannerConfig] = None,
                 force_width: Optional[int] = None):
        """Initialize responsive banner."""
        self.config = config or BannerConfig()
        self.terminal_width = force_width or get_terminal_width()
        
        # Auto-select banner if not provided
        if ascii_art is None and self.config.auto_responsive:
            ascii_art, self.banner_type = get_banner_for_width(self.terminal_width)
        else:
            ascii_art = ascii_art or BANNER_FULL
            self.banner_type = 'custom'
        
        self.ascii_art = ascii_art
        self.lines = ascii_art.split("\n")
        self.theme_colors = THEMES.get(self.config.theme, THEMES["neon_purple"])
    
    def refresh_terminal_width(self) -> None:
        """Update terminal width and re-select banner if needed"""
        self.terminal_width = get_terminal_width()
        
        if self.config.auto_responsive:
            new_art, new_type = get_banner_for_width(self.terminal_width)
            if new_type != self.banner_type:
                self.ascii_art = new_art
                self.lines = new_art.split("\n")
                self.banner_type = new_type
    
    def render_clean(self) -> str:
        """Render banner with pure color gradient, centered"""
        result = []
        
        for i, line in enumerate(self.lines):
            if line.strip():
                colored = apply_color_theme(line, self.theme_colors, i)
                centered = center_text(colored, self.terminal_width)
                result.append(centered)
            else:
                result.append("")
        
        return "\n".join(result)
    
    def render_gradient(self) -> str:
        """Apply character-by-character gradient, centered"""
        result = []
        
        for line in self.lines:
            if line.strip():
                gradientized = gradient(line, self.theme_colors)
                centered = center_text(gradientized, self.terminal_width)
                result.append(centered)
            else:
                result.append("")
        
        return "\n".join(result)
    
    def render_glitch(self, intensity: Optional[float] = None) -> str:
        """Render with static glitch distortion, centered"""
        intensity = intensity or self.config.glitch_intensity
        result = []
        
        for i, line in enumerate(self.lines):
            if line.strip():
                color = self.theme_colors[i % len(self.theme_colors)]
                glitched = apply_glitch_layer(line, intensity, colored=True)
                colored = f"{BOLD}{color}{glitched}{RESET}"
                centered = center_text(colored, self.terminal_width)
                result.append(centered)
            else:
                result.append("")
        
        return "\n".join(result)
    
    def render_cyberpunk(self, intensity: Optional[float] = None) -> str:
        """Full cyberpunk effect stack, centered"""
        intensity = intensity or self.config.glitch_intensity
        result = []
        
        for i, line in enumerate(self.lines):
            if line.strip():
                color = self.theme_colors[i % len(self.theme_colors)]
                
                # Multi-layer effects
                processed = apply_glitch_layer(line, intensity, colored=False)
                
                if self.config.shake_intensity > 0:
                    processed = apply_subtle_shake(processed, self.config.shake_intensity)
                
                if self.config.flicker_enabled:
                    processed = apply_neon_flicker(processed, color)
                else:
                    processed = f"{BOLD}{color}{processed}{RESET}"
                
                # Color corruption on glitched chars
                final = ""
                # This is complex, so we rebuild the string
                for char in strip_ansi(processed): # Iterate over plain chars
                    if char in GLITCH_CHARS + MATRIX_CHARS and random.random() < 0.5:
                        final += f"{glitch_color()}{char}{RESET}"
                    else:
                        # Re-apply the base flicker/color
                        final += f"{color}{char}{RESET}"
                
                centered = center_text(final, self.terminal_width)
                result.append(centered)
            else:
                result.append("")
        
        return "\n".join(result)
    
    def render_pulse_frame(self, frame: int) -> str:
        """Render single pulse frame, centered"""
        pulse_colors = [
            DEEP_VIOLET, NEON_PURPLE, BRIGHT_MAGENTA,
            ELECTRIC_CYAN, BRIGHT_MAGENTA, NEON_PURPLE,
            DEEP_VIOLET, f"{DIM}{NEON_PURPLE}"
        ]
        
        frame_color = pulse_colors[frame % len(pulse_colors)]
        result = []
        
        for line in self.lines:
            if line.strip():
                colored = f"{frame_color}{line}{RESET}"
                centered = center_text(colored, self.terminal_width)
                result.append(centered)
            else:
                result.append("")
        
        return "\n".join(result)
    
    def render_snake_animate_frame(self, frame: int) -> str:
        """Render frame with animated snake elements."""
        result = []
        
        for i, line in enumerate(self.lines):
            if line.strip():
                color = self.theme_colors[i % len(self.theme_colors)]
                animated_line = ""
                
                # Animate snake characters
                for char in line:
                    if char in SNAKE_BODY_CHARS:
                        animated_line += animate_snake_char(frame)
                    elif char in SNAKE_EYE_CHARS:
                        eye_colors = [GLITCH_RED, BRIGHT_MAGENTA, ELECTRIC_CYAN]
                        eye_color = eye_colors[frame % len(eye_colors)]
                        animated_line += f"{BOLD}{eye_color}{char}{RESET}"
                    elif char in SNAKE_DIAGONAL:
                        diag_color = ELECTRIC_CYAN if frame % 2 == 0 else NEON_PURPLE
                        animated_line += f"{diag_color}{char}{RESET}"
                    else:
                        # Apply base color to non-snake chars
                        animated_line += f"{BOLD}{color}{char}{RESET}"
                
                # No base color here, it's applied per-char
                centered = center_text(animated_line, self.terminal_width)
                result.append(centered)
            else:
                result.append("")
        
        return "\n".join(result)
    
    def display(self, mode: str = BannerMode.CLEAN) -> None:
        """Display banner with specified rendering mode"""
        self.refresh_terminal_width()
        
        mode_handlers = {
            BannerMode.CLEAN: self._display_clean,
            BannerMode.GLITCH: self._display_glitch,
            BannerMode.CYBERPUNK: self._display_cyberpunk,
            BannerMode.PULSE: self._display_pulse,
            BannerMode.ANIMATED: self._display_animated,
            BannerMode.MATRIX: self._display_matrix,
            BannerMode.GLITCH_PULSE: self._display_glitch_pulse,
            BannerMode.SNAKE_ANIMATE: self._display_snake_animate,
        }
        
        handler = mode_handlers.get(mode, self._display_clean)
        handler()
    
    def get(self, mode: str = BannerMode.CLEAN) -> str:
        """Return rendered banner as string"""
        self.refresh_terminal_width()
        
        mode_renderers = {
            BannerMode.CLEAN: self.render_clean,
            BannerMode.GLITCH: self.render_glitch,
            BannerMode.CYBERPUNK: self.render_cyberpunk,
        }
        
        renderer = mode_renderers.get(mode, self.render_clean)
        return renderer()
    
    # ═══════════════════════════════════════════════════════════
    # DISPLAY MODE IMPLEMENTATIONS
    # ═══════════════════════════════════════════════════════════
    
    def _display_clean(self) -> None:
        print(self.render_clean())
    
    def _display_glitch(self) -> None:
        print(self.render_glitch())
    
    def _display_cyberpunk(self) -> None:
        print(self.render_cyberpunk())
    
    def _display_pulse(self) -> None:
        """Animate pulsing glow with smooth cursor movement"""
        line_count = len(self.lines)
        
        for cycle in range(PULSE_CYCLES):
            for frame in range(8):
                if cycle == 0 and frame == 0:
                    # First frame, just print
                    print(self.render_pulse_frame(frame))
                else:
                    # Subsequent frames, move cursor up and overwrite
                    move_cursor_up(line_count)
                    print(self.render_pulse_frame(frame), end="", flush=True)
                
                time.sleep(ANIMATION_FRAME_DELAY)
        
        print() # Move cursor down after animation
    
    def _display_animated(self) -> None:
        """Typewriter-style reveal with proper centering"""
        for i, line in enumerate(self.lines):
            if not line.strip():
                print()
                continue
            
            # Get color for this line
            color = self.theme_colors[i % len(self.theme_colors)]
            
            # Calculate centering for the ORIGINAL line (not colored)
            visible_line = strip_ansi(line) # Should be plain ASCII art
            left_padding = (self.terminal_width - len(visible_line)) // 2
            
            # Print padding first
            if left_padding > 0:
                print(" " * left_padding, end="", flush=True)
            
            # Animate each character with color
            for char in visible_line:
                print(f"{BOLD}{color}{char}{RESET}", end="", flush=True)
                time.sleep(TYPEWRITER_CHAR_DELAY)
            
            print() # Newline after line is done
            
            # Random pause for dramatic effect
            if random.random() < 0.2:
                time.sleep(0.02)
    
    def _display_matrix(self) -> None:
        """Matrix cascade reveal with centered content"""
        clear_screen_and_home()
        for reveal_idx in range(len(self.lines)):
            
            for i, line in enumerate(self.lines):
                if i > reveal_idx:
                    # This line hasn't been "revealed" yet
                    print()
                elif not line.strip():
                    # Preserve empty lines
                    print()
                else:
                    color = self.theme_colors[i % len(self.theme_colors)]
                    distance = reveal_idx - i
                    
                    if distance == 0: # The "leading" edge
                        rendered = f"{BOLD}{BRIGHT_MAGENTA}{line}{RESET}"
                    elif distance == 1: # Just behind the edge
                        rendered = f"{BOLD}{color}{line}{RESET}"
                    elif distance <= 3: # Fading out
                        rendered = f"{color}{line}{RESET}"
                    else: # Faded
                        rendered = f"{DIM}{color}{line}{RESET}"
                    
                    centered = center_text(rendered, self.terminal_width)
                    print(centered)
            
            time.sleep(MATRIX_LINE_DELAY)
            if reveal_idx < len(self.lines) - 1:
                # Move cursor up to overwrite
                move_cursor_up(len(self.lines))
        
        time.sleep(0.3)
        # Final redraw
        clear_screen_and_home()
        print(self.render_clean())
    
    def _display_glitch_pulse(self) -> None:
        """Combined glitch and pulse effect"""
        line_count = len(self.lines)
        
        for cycle in range(PULSE_CYCLES):
            for frame in range(8):
                if frame % 2 == 0:
                    content = self.render_glitch(intensity=0.08)
                else:
                    content = self.render_pulse_frame(frame)
                
                if cycle == 0 and frame == 0:
                    print(content)
                else:
                    move_cursor_up(line_count)
                    print(content, end="", flush=True)
                
                time.sleep(ANIMATION_FRAME_DELAY)
        
        print()
    
    def _display_snake_animate(self) -> None:
        """Animate the cyber snake elements"""
        line_count = len(self.lines)
        frames = 12
        
        for frame in range(frames):
            if frame == 0:
                print(self.render_snake_animate_frame(frame))
            else:
                move_cursor_up(line_count)
                print(self.render_snake_animate_frame(frame), end="", flush=True)
            
            time.sleep(0.1)
        
        print()

# ═══════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def show_banner(mode: str = BannerMode.CYBERPUNK,
                theme: str = "neon_purple",
                compact: bool = False,
                glitch_intensity: float = 0.12) -> None:
    """Display responsive banner with sensible defaults."""
    config = BannerConfig(
        theme=theme,
        glitch_intensity=glitch_intensity,
        flicker_enabled=True,
        shake_intensity=1,
        auto_responsive=not compact
    )
    
    if compact:
        banner = Banner(BANNER_COMPACT, config)
    else:
        banner = Banner(None, config) # Auto-selects
    
    banner.display(mode)

def get_banner(mode: str = BannerMode.CLEAN,
               theme: str = "neon_purple") -> str:
    """Get rendered banner as string"""
    config = BannerConfig(theme=theme)
    banner = Banner(None, config) # Auto-selects
    return banner.get(mode)

def banner_with_info(cwd: str = "") -> None:
    """Display banner with centered tagline, version, and environment info."""
    banner = Banner()
    # Use a static, fast render mode for quick display
    print(banner.get(BannerMode.CLEAN))
    
    width = banner.terminal_width
    
    print()
    tagline = f"{BOLD}{ELECTRIC_CYAN}{TAGLINE}{RESET}"
    print(center_text(tagline, width))
    
    version_text = f"{DIM}{MID_GRAY}Version {VERSION}{RESET}"
    print(center_text(version_text, width))
    
    # Environment + workspace info (more detailed CLI banner)
    import platform
    os_name = platform.system()
    shell_hint = {
        "Windows": "PowerShell (p.* / c.*)",
        "Darwin": "zsh (m.* / l.*)",
        "Linux": "bash (l.* / m.*)",
    }.get(os_name, "host shell")

    env_line = (
        f"{DIM}{MID_GRAY}"
        f"Host: {os_name}  •  Default shell: {shell_hint}  •  Cross-OS prefixes: "
        f"{BRIGHT_MAGENTA}p.*{MID_GRAY}/{BRIGHT_MAGENTA}c.*{MID_GRAY}/"
        f"{BRIGHT_MAGENTA}l.*{MID_GRAY}/{BRIGHT_MAGENTA}m.*{RESET}"
    )
    print(center_text(env_line, width))

    if cwd:
        cwd_text = f"{DIM}{MID_GRAY}Workspace: {cwd}{RESET}"
        print(center_text(cwd_text, width))
    print()

# ═══════════════════════════════════════════════════════════════
# RESPONSIVE STARTUP SEQUENCE
# ═══════════════════════════════════════════════════════════════

def startup_sequence() -> None:
    """
    Cinematic startup animation with responsive centering.
    """
    clear_screen_and_home()
    width = get_terminal_width()
    
    # Phase 1: Boot message
    boot_msg = "⚡ INITIALIZING GITVISION TERMINAL ⚡"
    boot_text = f"{DIM}{MID_GRAY}{boot_msg}{RESET}"
    print(f"\n{center_text(boot_text, width)}")
    time.sleep(0.4)
    
    # Phase 2: Responsive loading bar
    load_bar_width = min(40, width - 10)
    padding_str = " " * ((width - load_bar_width - 2) // 2)
    
    print(f"\n{padding_str}{DIM}{DARK_GRAY}[{RESET}", end="", flush=True)
    
    for i in range(load_bar_width):
        if i % 4 == 0:
            color = ELECTRIC_CYAN
        elif i % 4 == 2:
            color = NEON_PURPLE
        else:
            color = BRIGHT_MAGENTA
        
        if random.random() < 0.1:
            glitch_char = random.choice(['▓', '▒', '░'])
            print(f"{glitch_color()}{glitch_char}{RESET}", end="", flush=True)
        else:
            print(f"{color}█{RESET}", end="", flush=True)
        
        time.sleep(0.025)
    
    print(f"{DIM}{DARK_GRAY}]{RESET}\n", flush=True)
    time.sleep(0.3)
    
    # Phase 3: Use MATRIX mode for better alignment
    banner = Banner()
    banner.display(BannerMode.MATRIX) # This prints the final clean banner
    
    # Phase 4: Animated tagline
    print()
    tagline_visible = strip_ansi(TAGLINE)
    tagline_padding_str = " " * ((width - len(tagline_visible)) // 2)
    
    print(tagline_padding_str, end="", flush=True)
    
    for char in tagline_visible:
        color = random.choice([NEON_PURPLE, ELECTRIC_CYAN, BRIGHT_MAGENTA])
        print(f"{BOLD}{color}{char}{RESET}", end="", flush=True)
        time.sleep(0.015)
    
    print()
    
    version_text = f"{DIM}{MID_GRAY}Version {VERSION}{RESET}"
    print(center_text(version_text, width))
    print()
    
    # Phase 5: Pulsing system ready
    ready_msg = "» SYSTEM READY «"
    
    for _ in range(3):
        ready_bright = f"{BOLD}{GLITCH_GREEN}{ready_msg}{RESET}"
        print(f"\r{center_text(ready_bright, width)}", end="", flush=True)
        time.sleep(0.15)
        
        ready_dim = f"{DIM}{GLITCH_GREEN}{ready_msg}{RESET}"
        print(f"\r{center_text(ready_dim, width)}", end="", flush=True)
        time.sleep(0.15)
    
    ready_final = f"{BOLD}{GLITCH_GREEN}{ready_msg}{RESET}"
    print(f"\r{center_text(ready_final, width)}\n", flush=True)
    time.sleep(0.3)
