# gitvisioncli/ui/glitch_effects.py
"""
GitVisionCLI — Glitch & Animation Effects Engine
Distortion, scanlines, flicker, pulse, and corruption effects
"""

import random
import time
from typing import List, Callable
# Import the stabilized colors
from .colors import *

# ═══════════════════════════════════════════════════════════════
# GLITCH CHARACTER SETS
# ═══════════════════════════════════════════════════════════════

GLITCH_CHARS = ['▒', '░', '█', '▓', '▀', '▄', '▌', '▐', '■', '□']
MATRIX_CHARS = ['⟟', '⟞', '⟡', '⟐', '⟕', '⟠', '⟣']
TECH_CHARS = ['╳', '╱', '╲', '╪', '┼', '├', '┤', '┬', '┴']
CORRUPTION_CHARS = ['#', '@', '$', '%', '&', '*', '~', '^']

ALL_GLITCH = GLITCH_CHARS + MATRIX_CHARS + TECH_CHARS + CORRUPTION_CHARS

# ═══════════════════════════════════════════════════════════════
# GLITCH DISTORTION
# ═══════════════════════════════════════════════════════════════

def glitch_char(char: str, intensity: float = 0.3) -> str:
    """
    Replace character with glitch symbol based on intensity.
    intensity: 0.0 (no glitch) to 1.0 (full glitch)
    """
    if char.strip() == "" or random.random() > intensity:
        return char
    return random.choice(ALL_GLITCH)

def glitch_text(text: str, intensity: float = 0.15) -> str:
    """Apply glitch distortion to entire text"""
    return "".join(glitch_char(c, intensity) for c in text)

def glitch_line(line: str, intensity: float = 0.2, color: bool = True) -> str:
    """
    Apply glitch to a line with optional random coloring.
    """
    glitched = glitch_text(line, intensity)
    if color:
        # Add random color to glitched chars
        result = []
        for c in glitched:
            if c in ALL_GLITCH:
                # Use the function from colors.py
                result.append(f"{glitch_color()}{c}{RESET}")
            else:
                result.append(c)
        return "".join(result)
    return glitched

def corrupt_burst(text: str, burst_count: int = 3) -> str:
    """
    Create intense glitch bursts at random positions.
    """
    text_list = list(text)
    length = len(text_list)
    
    for _ in range(burst_count):
        pos = random.randint(0, length - 1)
        burst_len = random.randint(2, 5)
        
        for i in range(pos, min(pos + burst_len, length)):
            if text_list[i].strip():
                # Use the function from colors.py
                text_list[i] = f"{glitch_color()}{random.choice(ALL_GLITCH)}{RESET}"
    
    return "".join(text_list)

# ═══════════════════════════════════════════════════════════════
# FLICKER EFFECTS
# ═══════════════════════════════════════════════════════════════

def flicker(text: str, color: str = NEON_PURPLE) -> str:
    """
    Simulate neon tube flicker by randomly dimming.
    """
    if random.random() < 0.3:
        return f"{DIM}{color}{text}{RESET}"
    return f"{BOLD}{color}{text}{RESET}"

def multi_flicker(lines: List[str], color: str = NEON_PURPLE) -> List[str]:
    """Apply flicker effect to multiple lines independently"""
    return [flicker(line, color) for line in lines]

# ═══════════════════════════════════════════════════════════════
# SCANLINE OVERLAY
# ═══════════════════════════════════════════════════════════════

def scanline(text: str, char: str = "─", density: float = 0.3) -> str:
    """
    Add CRT-style scanline overlay to text.
    density: chance each line gets a scanline (0.0 to 1.0)
    """
    lines = text.split("\n")
    result = []
    
    for line in lines:
        if random.random() < density:
            # Insert dim scanline characters
            scanline_overlay = "".join(
                f"{DIM}{DARK_GRAY}{char if random.random() < 0.5 else ' '}{RESET}"
                for _ in range(len(line))
            )
            result.append(line)
            result.append(scanline_overlay)
        else:
            result.append(line)
    
    return "\n".join(result)

def scanline_simple(lines: List[str]) -> List[str]:
    """Add single-char scanline between lines"""
    result = []
    for line in lines:
        result.append(line)
        if random.random() < 0.2:
            result.append(f"{DIM}{DARK_GRAY}{'─' * len(line)}{RESET}")
    return result

# ═══════════════════════════════════════════════════════════════
# PULSE ANIMATION
# ═══════════════════════════════════════════════════════════════

def pulse(text: str, cycles: int = 3, delay: float = 0.1) -> None:
    """
    Animate text with pulsing glow effect.
    Prints directly to terminal with color oscillation.
    """
    colors = [DEEP_VIOLET, NEON_PURPLE, BRIGHT_MAGENTA, ELECTRIC_CYAN]
    
    for _ in range(cycles):
        for color in colors:
            print(f"\r{BOLD}{color}{text}{RESET}", end="", flush=True)
            time.sleep(delay)
        for color in reversed(colors):
            print(f"\r{BOLD}{color}{text}{RESET}", end="", flush=True)
            time.sleep(delay)
    
    print()  # Final newline

def pulse_static(text: str, frame: int = 0) -> str:
    """
    Return static pulse frame (for frame-by-frame animation).
    frame: 0-7 for 8-frame pulse cycle
    """
    colors = [
        DEEP_VIOLET, NEON_PURPLE, BRIGHT_MAGENTA, 
        ELECTRIC_CYAN, BRIGHT_MAGENTA, NEON_PURPLE,
        DEEP_VIOLET, DIM + NEON_PURPLE
    ]
    color = colors[frame % len(colors)]
    return f"{color}{text}{RESET}"

# ═══════════════════════════════════════════════════════════════
# SHAKE EFFECT
# ═══════════════════════════════════════════════════════════════

def shake(text: str, intensity: int = 2) -> str:
    """
    Add random spacing/positioning distortion.
    """
    spacing = " " * random.randint(0, intensity)
    return spacing + text

def shake_lines(lines: List[str], intensity: int = 3) -> List[str]:
    """Apply shake to each line independently"""
    return [shake(line, intensity) for line in lines]

# ═══════════════════════════════════════════════════════════════
# TYPEWRITER EFFECT
# ═══════════════════════════════════════════════════════════════

def typewriter(text: str, delay: float = 0.03, color: str = NEON_PURPLE) -> None:
    """
    Print text character-by-character with delay.
    """
    for char in text:
        print(f"{color}{char}{RESET}", end="", flush=True)
        time.sleep(delay)
    print()

def typewriter_lines(lines: List[str], delay: float = 0.05, color: str = NEON_PURPLE) -> None:
    """Print lines with typewriter effect"""
    for line in lines:
        typewriter(line, delay, color)

# ═══════════════════════════════════════════════════════════════
# COMPOSITE EFFECTS
# ═══════════════════════════════════════════════════════════════

def cyberpunk_effect(text: str, intensity: float = 0.2) -> str:
    """
    Apply full cyberpunk effect stack:
    - Glitch distortion
    - Color corruption
    - Random flicker
    """
    text = glitch_line(text, intensity, color=True)
    text = flicker(text, NEON_PURPLE)
    if random.random() < 0.15:
        text = corrupt_burst(text, 2)
    return text

def apply_effects(lines: List[str], 
                  glitch: bool = True,
                  flicker_enabled: bool = True,
                  shake_enabled: bool = False,
                  intensity: float = 0.15) -> List[str]:
    """
    Apply multiple effects to line array.
    Returns processed lines.
    """
    result = lines.copy()
    
    if glitch:
        result = [glitch_line(line, intensity, color=True) for line in result]
    
    if flicker_enabled:
        result = multi_flicker(result, NEON_PURPLE)
    
    if shake_enabled:
        result = shake_lines(result, 2)
    
    return result

# ═══════════════════════════════════════════════════════════════
# FRAME ANIMATION HELPER
# ═══════════════════════════════════════════════════════════════

def animate_frames(frames: List[str], delay: float = 0.1, loops: int = 1) -> None:
    """
    Play frame animation in terminal.
    Clears screen between frames.
    """
    for _ in range(loops):
        for frame in frames:
            print("\033[2J\033[H", end="")  # Clear screen + move to top
            print(frame)
            time.sleep(delay)

def glitch_animate(text: str, frames: int = 10, delay: float = 0.05) -> None:
    """
    Animate glitch effect on static text.
    """
    for i in range(frames):
        intensity = 0.1 + (i / frames) * 0.3
        glitched = glitch_line(text, intensity, color=True)
        print(f"\r{glitched}", end="", flush=True)
        time.sleep(delay)
    print()