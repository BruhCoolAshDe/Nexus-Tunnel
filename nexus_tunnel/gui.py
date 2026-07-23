"""Modern GUI widgets and utilities with glassmorphism effects."""

import tkinter as tk
from tkinter import scrolledtext
import customtkinter as ctk
from PIL import Image, ImageDraw
import platform
from typing import Callable, Optional
import threading


class ColorPalette:
    """Modern vibrant color theme."""
    # Base
    BG = "#0a0e27"           # Deep navy
    CARD = "#0f1629"         # Slightly lighter navy
    CARD_HOVER = "#151d3a"   # Card hover state
    BORDER = "#1a4d7a"       # Soft blue border
    
    # Accents - Neon vibrancy
    ACCENT = "#00d9ff"       # Cyan
    ACCENT_DARK = "#0099cc"  # Darker cyan
    ACCENT_ALT = "#ff006e"   # Pink accent
    
    # Status
    GLOW = "#ff3366"         # Neon pink glow
    TEXT = "#f5f7ff"         # Light text
    MUTED = "#8892b0"        # Muted secondary text
    OK = "#00ff88"           # Bright green
    ERR = "#ff3333"          # Bright red
    WARN = "#ffaa00"         # Bright orange
    
    # Gradients
    PRIMARY_START = "#00d9ff"
    PRIMARY_END = "#0099cc"


class Fonts:
    """Modern font definitions."""
    def __init__(self):
        ff = ('Segoe UI' if platform.system() == 'Windows'
              else 'Helvetica Neue' if platform.system() == 'Darwin'
              else 'DejaVu Sans')
        fm = ('Consolas' if platform.system() == 'Windows'
              else 'Menlo' if platform.system() == 'Darwin'
              else 'DejaVu Sans Mono')
        self.title = (ff, 28, 'bold')
        self.heading = (ff, 16, 'bold')
        self.subhead = (ff, 13, 'bold')
        self.label = (ff, 12, 'bold')
        self.body = (ff, 11)
        self.small = (ff, 9)
        self.mono = (fm, 10)


def hex_lerp(a: str, b: str, t: float) -> str:
    """Interpolate between two hex colors."""
    t = max(0.0, min(1.0, t))
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    return f'#{int(ar+(br-ar)*t):02x}{int(ag+(bg-ag)*t):02x}{int(ab+(bb-ab)*t):02x}'


def styled_entry(parent, text: str = '', width: int = 260, label: str = '') -> ctk.CTkEntry:
    """Create a modern input field with optional label."""
    e = ctk.CTkEntry(
        parent,
        fg_color=ColorPalette.CARD,
        text_color=ColorPalette.TEXT,
        font=Fonts().body,
        width=width,
        height=36,
        corner_radius=10,
        border_color=ColorPalette.BORDER,
        border_width=1.5,
        placeholder_text=label if label else '',
        placeholder_text_color=ColorPalette.MUTED,
    )
    if text:
        e.insert(0, text)
    return e


def card_frame(parent, bg_color: str = None) -> ctk.CTkFrame:
    """Create a modern card with glassmorphism effect."""
    return ctk.CTkFrame(
        parent,
        fg_color=bg_color or ColorPalette.CARD,
        corner_radius=16,
        border_color=ColorPalette.BORDER,
        border_width=1.5,
    )


def log_box(parent, height: int = 10) -> scrolledtext.ScrolledText:
    """Create a modern log display with syntax highlighting."""
    t = scrolledtext.ScrolledText(
        parent,
        bg=ColorPalette.BG,
        fg=ColorPalette.TEXT,
        font=Fonts().mono,
        insertbackground=ColorPalette.ACCENT,
        relief='flat',
        height=height,
        wrap='word',
        highlightthickness=0,
        state='disabled',
        bd=0,
    )
    # Configure tags with modern colors
    tag_config = [
        ('ok', ColorPalette.OK, 'bold'),
        ('err', ColorPalette.ERR, 'bold'),
        ('warn', ColorPalette.WARN, 'bold'),
        ('info', ColorPalette.ACCENT, 'normal'),
        ('dim', ColorPalette.MUTED, 'normal'),
    ]
    for tag, col, weight in tag_config:
        t.tag_config(tag, foreground=col, font=(Fonts().mono[0], Fonts().mono[1], weight))
    return t


def log_append(widget, msg: str, tag: str = '', with_time: bool = True):
    """Append a styled line to the log box."""
    def _do():
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return
        import time
        widget.config(state='normal')
        if with_time:
            ts = time.strftime('%H:%M:%S')
            widget.insert(tk.END, f'[{ts}]  ', 'dim')
        widget.insert(tk.END, msg + '\n', tag)
        widget.see(tk.END)
        widget.config(state='disabled')
    widget.after(0, _do)


def modern_button(
    parent,
    text: str,
    icon_name: str,
    fg_color: str,
    command: Callable,
    width: int = 140,
    height: int = 40,
    icon_size: int = 20,
) -> ctk.CTkButton:
    """Create a modern pill-shaped button."""
    icon = _make_icon(icon_name, icon_size, '#ffffff')
    hover_color = hex_lerp(fg_color, '#ffffff', 0.25)
    return ctk.CTkButton(
        parent,
        text=text,
        image=icon,
        compound='left',
        fg_color=fg_color,
        hover_color=hover_color,
        text_color='#ffffff',
        font=Fonts().label,
        corner_radius=20,  # Pill shape
        height=height,
        width=width,
        border_width=0,
        command=command,
    )


def status_badge(parent, text: str, status: str = 'info', font_size: int = 10) -> ctk.CTkLabel:
    """Create a modern status badge."""
    color_map = {
        'ok': ColorPalette.OK,
        'err': ColorPalette.ERR,
        'warn': ColorPalette.WARN,
        'info': ColorPalette.ACCENT,
        'dim': ColorPalette.MUTED,
    }
    color = color_map.get(status, ColorPalette.ACCENT)
    return ctk.CTkLabel(
        parent,
        text=text,
        font=(Fonts().body[0], font_size, 'bold'),
        text_color=color,
        fg_color='transparent',
    )


def section_title(parent, text: str) -> ctk.CTkLabel:
    """Create a modern section title with accent line."""
    return ctk.CTkLabel(
        parent,
        text=text,
        font=Fonts().heading,
        text_color=ColorPalette.TEXT,
        fg_color='transparent',
    )


_icon_cache = {}


def _make_icon(name: str, size: int = 20, fg: str = '#00d9ff') -> ctk.CTkImage:
    """Generate modern icons with better styling."""
    key = (name, size, fg)
    if key in _icon_cache:
        return _icon_cache[key]

    s2 = size * 2
    r_, g_, b_ = int(fg[1:3], 16), int(fg[3:5], 16), int(fg[5:7], 16)
    c = (r_, g_, b_, 255)
    img = Image.new('RGBA', (s2, s2), (r_, g_, b_, 0))
    d = ImageDraw.Draw(img)
    m = s2
    sw = max(2, m // 8)  # Stroke width

    if name == 'host':
        # Server icon - improved
        d.rectangle([m*2//8, m*3//8, m*6//8, m*7//8], outline=c, width=sw, fill=(r_, g_, b_, 30))
        d.line([m//2, m*1//8, m//2, m*2//8], fill=c, width=sw)
        d.polygon([(m*3//8, m*2//8), (m//2, m*1//8), (m*5//8, m*2//8)], fill=c)
        # Add dots
        for i in range(3):
            y = m*4//8 + i*m//6
            d.ellipse([m*3//8, y, m*3//8+sw*2, y+sw*2], fill=c)
    elif name == 'join':
        # Connection icon
        d.arc([m*1//8, m*2//8, m//2, m*6//8], 90, 270, fill=c, width=sw)
        d.arc([m//2, m*2//8, m*7//8, m*6//8], 270, 90, fill=c, width=sw)
        d.ellipse([m*4//8-sw, m*3//8-sw, m*4//8+sw, m*3//8+sw], fill=c)
    elif name == 'back':
        # Back arrow - modern
        points = [(m*6//8, m*2//8), (m*2//8, m//2), (m*6//8, m*6//8)]
        d.polygon(points, fill=c)
        d.line([(m*6//8, m*2//8), (m*6//8, m*6//8)], fill=c, width=sw//2)
    elif name == 'stop':
        # Stop icon - rounded square
        d.rectangle([m*2//8, m*2//8, m*6//8, m*6//8], outline=c, width=sw)
    elif name == 'echo':
        # Echo/Wave icon
        for i in range(1, 4):
            r = m * i // 12
            d.arc([m//2-r, m//2-r, m//2+r, m//2+r], 0, 360, fill=c, width=sw//2)
        d.ellipse([m//2-sw, m//2-sw, m//2+sw, m//2+sw], fill=c)
    elif name == 'map':
        # Map/location icon
        d.rectangle([m*1//8, m*1//8, m*7//8, m*7//8], outline=c, width=sw)
        d.line([m//2, m*1//8, m//2, m*7//8], fill=c, width=sw//2)
        d.line([m*1//8, m//2, m*7//8, m//2], fill=c, width=sw//2)
        r = m // 6
        d.ellipse([m*5//8-r, m*3//8-r, m*5//8+r, m*3//8+r], fill=c)
    elif name == 'play':
        # Play icon
        d.polygon([(m*2//8, m*1//8), (m*7//8, m//2), (m*2//8, m*7//8)], fill=c)
    elif name == 'settings':
        # Settings/gear icon
        d.ellipse([m*3//8, m*3//8, m*5//8, m*5//8], outline=c, width=sw)
        for angle in range(0, 360, 45):
            x1 = m//2 + int((m*3.5//8) * (1 if angle % 90 == 0 else 0.7) * (1 if angle < 180 else -1))
            y1 = m//2 + int((m*3.5//8) * (1 if angle % 90 == 45 else 0.7) * (1 if angle < 90 or angle > 270 else -1))
            d.line([m//2, m//2, x1, y1], fill=c, width=sw//2)
    
    img_sm = img.resize((size, size), Image.LANCZOS)
    ctkimg = ctk.CTkImage(light_image=img_sm, dark_image=img_sm, size=(size, size))
    _icon_cache[key] = ctkimg
    return ctkimg
