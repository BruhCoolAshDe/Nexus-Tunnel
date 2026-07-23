"""Custom GUI widgets and utilities."""

import tkinter as tk
from tkinter import scrolledtext
import customtkinter as ctk
from PIL import Image, ImageDraw
import platform
from typing import Callable


class ColorPalette:
    """Dark theme colors."""
    BG = "#050505"
    CARD = "#111111"
    CARD2 = "#1B1B1B"
    BORDER = "#7A0000"
    ACCENT = "#C40000"
    GLOW = "#FF3A3A"
    TEXT = "#FFFFFF"
    MUTED = "#9A9A9A"
    OK = "#22C55E"
    ERR = "#FF3B3B"
    WARN = "#FF9800"
    BLUE = "#B00000"
    TEAL = "#8A0000"


class Fonts:
    """Font definitions."""
    def __init__(self):
        ff = ('Segoe UI' if platform.system() == 'Windows'
              else 'Helvetica Neue' if platform.system() == 'Darwin'
              else 'DejaVu Sans')
        fm = ('Consolas' if platform.system() == 'Windows'
              else 'Menlo' if platform.system() == 'Darwin'
              else 'DejaVu Sans Mono')
        self.title = (ff, 22, 'bold')
        self.heading = (ff, 15, 'bold')
        self.label = (ff, 13, 'bold')
        self.body = (ff, 12)
        self.small = (ff, 10)
        self.mono = (fm, 10)


def hex_lerp(a: str, b: str, t: float) -> str:
    """Interpolate between two hex colors."""
    t = max(0.0, min(1.0, t))
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    return f'#{int(ar+(br-ar)*t):02x}{int(ag+(bg-ag)*t):02x}{int(ab+(bb-ab)*t):02x}'


def styled_entry(parent, text: str = '', width: int = 260) -> ctk.CTkEntry:
    """Create a styled input field."""
    e = ctk.CTkEntry(
        parent,
        fg_color=ColorPalette.CARD2,
        text_color=ColorPalette.TEXT,
        font=Fonts().body,
        width=width,
        corner_radius=8,
        border_color=ColorPalette.BORDER,
        border_width=1,
    )
    if text:
        e.insert(0, text)
    return e


def card_frame(parent, padx: int = 20, pady: int = 16) -> ctk.CTkFrame:
    """Create a styled card container."""
    return ctk.CTkFrame(
        parent,
        fg_color=ColorPalette.CARD,
        corner_radius=12,
        border_color=ColorPalette.BORDER,
        border_width=1,
    )


def log_box(parent, height: int = 8) -> scrolledtext.ScrolledText:
    """Create a styled log display."""
    t = scrolledtext.ScrolledText(
        parent,
        bg='#060210',
        fg='#b39ddb',
        font=Fonts().mono,
        insertbackground=ColorPalette.GLOW,
        relief='flat',
        height=height,
        wrap='word',
        highlightthickness=1,
        highlightbackground=ColorPalette.BORDER,
        state='disabled',
    )
    for tag, col in [
        ('ok', ColorPalette.OK),
        ('err', ColorPalette.ERR),
        ('warn', ColorPalette.WARN),
        ('info', ColorPalette.GLOW),
        ('dim', ColorPalette.MUTED),
    ]:
        t.tag_config(tag, foreground=col)
    return t


def log_append(widget, msg: str, tag: str = ''):
    """Append a line to the log box."""
    def _do():
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return
        import time
        ts = time.strftime('%H:%M:%S')
        widget.config(state='normal')
        widget.insert(tk.END, f'[{ts}]  ', 'dim')
        widget.insert(tk.END, msg + '\n', tag)
        widget.see(tk.END)
        widget.config(state='disabled')
    widget.after(0, _do)


def icon_button(
    parent,
    text: str,
    icon_name: str,
    fg_color: str,
    command: Callable,
    padx: int = 18,
    pady: int = 8,
    icon_size: int = 20,
) -> ctk.CTkButton:
    """Create a button with icon."""
    icon = _make_icon(icon_name, icon_size, ColorPalette.TEXT)
    return ctk.CTkButton(
        parent,
        text=text,
        image=icon,
        compound='left',
        fg_color=fg_color,
        hover_color=hex_lerp(fg_color, '#ffffff', 0.18),
        text_color=ColorPalette.TEXT,
        font=Fonts().label,
        corner_radius=12,
        bg_color=_parent_bg(parent),
        command=command,
    )


def _parent_bg(parent) -> str:
    """Get parent background color."""
    try:
        return str(parent.cget('bg'))
    except Exception:
        try:
            return str(parent.cget('fg_color'))
        except Exception:
            return ColorPalette.BG


_icon_cache = {}


def _make_icon(name: str, size: int = 16, fg: str = '#f0e6ff') -> ctk.CTkImage:
    """Generate a small icon by name."""
    key = (name, size, fg)
    if key in _icon_cache:
        return _icon_cache[key]

    s2 = size * 2
    r_, g_, b_ = int(fg[1:3], 16), int(fg[3:5], 16), int(fg[5:7], 16)
    c = (r_, g_, b_, 255)
    img = Image.new('RGBA', (s2, s2), (r_, g_, b_, 0))
    d = ImageDraw.Draw(img)
    m = s2

    if name == 'host':
        d.rectangle([m*2//8, m*3//8, m*6//8, m*7//8], outline=c, width=max(2, m//10))
        d.line([m//2, m*1//8, m//2, m*5//8], fill=c, width=max(2, m//10))
        d.polygon([(m*3//8, m*3//8), (m//2, m*1//8), (m*5//8, m*3//8)], fill=c)
    elif name == 'join':
        d.arc([m*1//8, m*2//8, m//2, m*6//8], 90, 270, fill=c, width=max(2, m//8))
        d.arc([m//2, m*2//8, m*7//8, m*6//8], 270, 90, fill=c, width=max(2, m//8))
    elif name == 'back':
        d.polygon([(m*6//8, m*2//8), (m*2//8, m//2), (m*6//8, m*6//8)], fill=c)
    elif name == 'stop':
        w = max(3, m//6)
        d.line([m*2//8, m*2//8, m*6//8, m*6//8], fill=c, width=w)
        d.line([m*6//8, m*2//8, m*2//8, m*6//8], fill=c, width=w)
    elif name == 'echo':
        d.polygon([(m*5//8, m*3//8), (m*7//8, m//2), (m*5//8, m*5//8)], fill=c)
        d.line([m*2//8, m//2, m*7//8, m//2], fill=c, width=max(2, m//8))
    elif name == 'map':
        bw = max(2, m//10)
        d.rectangle([m*1//8, m*1//8, m*7//8, m*7//8], outline=c, width=bw)
        d.line([m//2, m*1//8, m//2, m*7//8], fill=c, width=bw)
        d.line([m*1//8, m//2, m*7//8, m//2], fill=c, width=bw)
    img_sm = img.resize((size, size), Image.LANCZOS)
    ctkimg = ctk.CTkImage(light_image=img_sm, dark_image=img_sm, size=(size, size))
    _icon_cache[key] = ctkimg
    return ctkimg
