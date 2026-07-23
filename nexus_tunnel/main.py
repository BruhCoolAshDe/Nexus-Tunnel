"""Main entry point and application state management."""

import sys
import tkinter as tk
from tkinter import messagebox
import threading
import uuid

import customtkinter as ctk
from nexus_tunnel.config import TunnelConfig
from nexus_tunnel.studio import StudioPath, StudioLauncher, MapInjector
from nexus_tunnel.networking import UDPProxy, EchoServer, warm_tunnel
from nexus_tunnel.gui import (
    ColorPalette, Fonts, log_append, log_box, styled_entry,
    card_frame, modern_button, section_title, status_badge
)


class AppState:
    """Shared application state."""
    def __init__(self):
        self.config = TunnelConfig.load()
        self.studio_path = StudioPath.detect() or self.config.studio_path
        self.proxy = None
        self.echo_server = EchoServer()


class NexusTunnelApp(ctk.CTk):
    """Modern main application window."""

    def __init__(self):
        super().__init__()
        self.title('Nexus Tunnel v2.0')
        self.geometry('800x700')
        self.minsize(640, 560)
        ctk.set_appearance_mode('dark')
        self.configure(fg_color=ColorPalette.BG)
        self.protocol('WM_DELETE_WINDOW', self._quit)

        self.state = AppState()
        self.fonts = Fonts()
        self._current_page = None
        self._setup_dpi()
        self._show_menu()

    def _setup_dpi(self):
        """Configure DPI awareness on Windows."""
        if sys.platform == 'win32':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                pass

    def _clear_page(self):
        """Clear current page."""
        if self._current_page:
            self._current_page.destroy()
            self._current_page = None

    def _show_menu(self):
        """Show modern main menu."""
        self._clear_page()
        frame = ctk.CTkFrame(self, fg_color=ColorPalette.BG)
        frame.pack(fill='both', expand=True, padx=0, pady=0)
        self._current_page = frame

        # Header with branding
        header = ctk.CTkFrame(frame, fg_color=ColorPalette.CARD, corner_radius=0)
        header.pack(fill='x', padx=0, pady=0)
        
        ctk.CTkLabel(
            header, text='⚡ NEXUS TUNNEL',
            font=self.fonts.title, text_color=ColorPalette.ACCENT,
            fg_color='transparent'
        ).pack(pady=(20, 4))
        
        ctk.CTkLabel(
            header, text='Roblox Studio Local Testing Platform',
            font=self.fonts.body, text_color=ColorPalette.MUTED,
            fg_color='transparent'
        ).pack(pady=(0, 20))

        # Main content
        content = ctk.CTkFrame(frame, fg_color=ColorPalette.BG)
        content.pack(fill='both', expand=True, padx=24, pady=24)

        # Info card
        info_card = card_frame(content)
        info_card.pack(fill='x', pady=(0, 20))
        
        status = self.state.studio_path is not None
        status_col = ColorPalette.OK if status else ColorPalette.ERR
        status_txt = f"✓ Found" if status else "✗ Not found"
        
        ctk.CTkLabel(
            info_card, text='Studio Status',
            font=self.fonts.subhead, text_color=ColorPalette.TEXT,
            fg_color='transparent'
        ).pack(anchor='w', padx=16, pady=(12, 6))
        
        ctk.CTkLabel(
            info_card, text=status_txt,
            font=self.fonts.body, text_color=status_col,
            fg_color='transparent'
        ).pack(anchor='w', padx=16, pady=(0, 12))

        # Action buttons grid
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='both', expand=True, pady=20)
        
        modern_button(btn_frame, 'HOST', 'host', ColorPalette.ACCENT,
                     self._go_host_config, width=200, height=48, icon_size=24).pack(pady=8, fill='x')
        modern_button(btn_frame, 'JOIN', 'join', ColorPalette.ACCENT_ALT,
                     self._go_join_config, width=200, height=48, icon_size=24).pack(pady=8, fill='x')
        modern_button(btn_frame, 'ECHO TEST', 'echo', ColorPalette.ACCENT_DARK,
                     self._go_echo_test, width=200, height=48, icon_size=24).pack(pady=8, fill='x')

    def _go_host_config(self):
        """Show host configuration screen."""
        self._clear_page()
        frame = ctk.CTkFrame(self, fg_color=ColorPalette.BG)
        frame.pack(fill='both', expand=True, padx=0, pady=0)
        self._current_page = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color=ColorPalette.CARD, corner_radius=0)
        header.pack(fill='x', padx=0, pady=0)
        ctk.CTkLabel(header, text='📡 HOST SESSION', font=self.fonts.heading,
                     text_color=ColorPalette.ACCENT, fg_color='transparent').pack(pady=16)

        # Form
        content = ctk.CTkFrame(frame, fg_color=ColorPalette.BG)
        content.pack(fill='both', expand=True, padx=24, pady=24)

        card = card_frame(content)
        card.pack(fill='x', pady=(0, 20))

        entries = {}
        for label, val, key in [
            ('User ID', self.state.config.user_id, 'user_id'),
            ('Port', str(self.state.config.static_port), 'static_port'),
            ('Tunnel Address', self.state.config.tunnel_addr, 'tunnel_addr'),
        ]:
            ctk.CTkLabel(card, text=label, font=self.fonts.label,
                        text_color=ColorPalette.TEXT, fg_color='transparent').pack(anchor='w', padx=16, pady=(12, 6))
            e = styled_entry(card, val, width=600, label=label)
            e.pack(anchor='w', padx=16, pady=(0, 12), fill='x')
            entries[key] = e

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(pady=16)
        modern_button(btn_frame, 'BACK', 'back', ColorPalette.CARD_HOVER,
                     self._show_menu, width=120, height=40).pack(side='left', padx=6)
        modern_button(btn_frame, 'LAUNCH', 'host', ColorPalette.ACCENT,
                     lambda: self._launch_server(entries), width=120, height=40).pack(side='left', padx=6)

    def _launch_server(self, entries):
        """Launch server with config from entries."""
        try:
            uid = entries['user_id'].get().strip()
            port = int(entries['static_port'].get().strip())
            addr = entries['tunnel_addr'].get().strip()
            self.state.config.user_id = uid
            self.state.config.static_port = port
            self.state.config.tunnel_addr = addr
            self.state.config.save()
            self._go_host_running(uid, port, addr)
        except ValueError:
            messagebox.showerror('Invalid Input', 'Check your entries (port must be a number)')

    def _go_host_running(self, uid, port, addr):
        """Show running host console."""
        self._clear_page()
        frame = ctk.CTkFrame(self, fg_color=ColorPalette.BG)
        frame.pack(fill='both', expand=True, padx=0, pady=0)
        self._current_page = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color=ColorPalette.CARD, corner_radius=0)
        header.pack(fill='x', padx=0, pady=0)
        ctk.CTkLabel(header, text='🖥️ SERVER CONSOLE', font=self.fonts.heading,
                     text_color=ColorPalette.OK, fg_color='transparent').pack(pady=16)

        # Log
        content = ctk.CTkFrame(frame, fg_color=ColorPalette.BG)
        content.pack(fill='both', expand=True, padx=20, pady=20)

        logw = log_box(content, height=14)
        logw.pack(fill='both', expand=True, pady=(0, 16))

        def _log(msg, tag=''):
            log_append(logw, msg, tag)

        def run():
            pg = str(uuid.uuid4()).upper()
            tg = str(uuid.uuid4()).upper()
            _log(f'UID: {uid}', 'dim')
            _log(f'Port: {port}', 'info')
            _log(f'Tunnel: {addr}', 'dim')
            _log('─' * 50, 'dim')
            _log('Launching server...', 'warn')
            if not self.state.studio_path:
                _log('✗ Studio path not configured', 'err')
                return
            ok = StudioLauncher.launch_server(self.state.studio_path, port, uid, pg, tg)
            _log('✓ Server launched successfully!' if ok else '✗ Failed to launch', 'ok' if ok else 'err')

        threading.Thread(target=run, daemon=True).start()

        # Footer buttons
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='x')
        modern_button(btn_frame, 'BACK', 'back', ColorPalette.CARD_HOVER,
                     self._show_menu, width=150, height=40).pack(side='left', padx=6)

    def _go_join_config(self):
        """Show join configuration screen."""
        self._clear_page()
        frame = ctk.CTkFrame(self, fg_color=ColorPalette.BG)
        frame.pack(fill='both', expand=True, padx=0, pady=0)
        self._current_page = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color=ColorPalette.CARD, corner_radius=0)
        header.pack(fill='x', padx=0, pady=0)
        ctk.CTkLabel(header, text='🔗 JOIN SESSION', font=self.fonts.heading,
                     text_color=ColorPalette.ACCENT_ALT, fg_color='transparent').pack(pady=16)

        # Form
        content = ctk.CTkFrame(frame, fg_color=ColorPalette.BG)
        content.pack(fill='both', expand=True, padx=24, pady=24)

        card = card_frame(content)
        card.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(card, text='Tunnel Address', font=self.fonts.label,
                    text_color=ColorPalette.TEXT, fg_color='transparent').pack(anchor='w', padx=16, pady=(12, 6))
        addr_e = styled_entry(card, '', width=600, label='host:port')
        addr_e.pack(anchor='w', padx=16, pady=(0, 16), fill='x')

        ctk.CTkLabel(card, text='Example: proxy.example.com:7777', font=self.fonts.small,
                    text_color=ColorPalette.MUTED, fg_color='transparent').pack(anchor='w', padx=16, pady=(0, 12))

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(pady=16)
        modern_button(btn_frame, 'BACK', 'back', ColorPalette.CARD_HOVER,
                     self._show_menu, width=120, height=40).pack(side='left', padx=6)
        modern_button(btn_frame, 'CONNECT', 'join', ColorPalette.ACCENT_ALT,
                     lambda: self._join_server(addr_e.get()), width=120, height=40).pack(side='left', padx=6)

    def _join_server(self, addr):
        """Join a server via proxy."""
        if ':' not in addr:
            messagebox.showerror('Invalid', 'Format: host:port\nExample: proxy.example.com:7777')
            return
        try:
            host, port = addr.rsplit(':', 1)
            self._go_join_running(host, int(port))
        except ValueError:
            messagebox.showerror('Invalid', 'Port must be a number')

    def _go_join_running(self, host, port):
        """Show join console."""
        self._clear_page()
        frame = ctk.CTkFrame(self, fg_color=ColorPalette.BG)
        frame.pack(fill='both', expand=True, padx=0, pady=0)
        self._current_page = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color=ColorPalette.CARD, corner_radius=0)
        header.pack(fill='x', padx=0, pady=0)
        ctk.CTkLabel(header, text='📡 CONNECTION CONSOLE', font=self.fonts.heading,
                     text_color=ColorPalette.OK, fg_color='transparent').pack(pady=16)

        # Log
        content = ctk.CTkFrame(frame, fg_color=ColorPalette.BG)
        content.pack(fill='both', expand=True, padx=20, pady=20)

        logw = log_box(content, height=14)
        logw.pack(fill='both', expand=True, pady=(0, 16))

        def _log(msg, tag=''):
            log_append(logw, msg, tag)

        def run():
            _log(f'Target: {host}:{port}', 'info')
            _log('─' * 50, 'dim')
            _log('Initializing proxy...', 'warn')
            proxy = UDPProxy(55555, host, port)
            if not proxy.start():
                _log('✗ Failed to start proxy', 'err')
                return
            self.state.proxy = proxy
            _log('✓ Proxy active', 'ok')
            _log('Warming tunnel...', 'warn')
            warm_tunnel(55555)
            _log('✓ Tunnel ready', 'ok')
            if not self.state.studio_path:
                _log('✗ Studio path not configured', 'err')
                return
            pg = str(uuid.uuid4()).upper()
            tg = str(uuid.uuid4()).upper()
            _log('Launching client...', 'warn')
            ok = StudioLauncher.launch_client(self.state.studio_path, '127.0.0.1', 55555, pg, tg)
            _log('✓ Client launched!' if ok else '✗ Failed to launch', 'ok' if ok else 'err')

        threading.Thread(target=run, daemon=True).start()

        # Footer buttons
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='x')
        modern_button(btn_frame, 'DISCONNECT', 'stop', ColorPalette.ERR,
                     self._disconnect, width=180, height=40).pack(side='left', padx=6)

    def _disconnect(self):
        """Disconnect and return to menu."""
        if self.state.proxy:
            self.state.proxy.stop()
            self.state.proxy = None
        self._show_menu()

    def _go_echo_test(self):
        """Show echo test screen."""
        self._clear_page()
        frame = ctk.CTkFrame(self, fg_color=ColorPalette.BG)
        frame.pack(fill='both', expand=True, padx=0, pady=0)
        self._current_page = frame

        # Header
        header = ctk.CTkFrame(frame, fg_color=ColorPalette.CARD, corner_radius=0)
        header.pack(fill='x', padx=0, pady=0)
        ctk.CTkLabel(header, text='📶 ECHO TEST', font=self.fonts.heading,
                     text_color=ColorPalette.ACCENT_DARK, fg_color='transparent').pack(pady=16)

        # Log
        content = ctk.CTkFrame(frame, fg_color=ColorPalette.BG)
        content.pack(fill='both', expand=True, padx=20, pady=20)

        logw = log_box(content, height=14)
        logw.pack(fill='both', expand=True, pady=(0, 16))

        def _log(msg, tag=''):
            log_append(logw, msg, tag)

        # Footer buttons
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='x')
        modern_button(btn_frame, 'BACK', 'back', ColorPalette.CARD_HOVER,
                     self._show_menu, width=120, height=40).pack(side='left', padx=6)
        modern_button(btn_frame, 'START', 'play', ColorPalette.ACCENT_DARK,
                     lambda: self._start_echo(_log), width=120, height=40).pack(side='left', padx=6)

    def _start_echo(self, _log):
        """Start the echo server."""
        _log('Initializing echo server...', 'warn')
        ok, err = self.state.echo_server.start(55555)
        if ok:
            _log('✓ Echo server started on port 55555', 'ok')
            _log('Ready to receive echo requests', 'dim')
        else:
            _log(f'✗ {err}', 'err')

    def _quit(self):
        """Clean up and exit."""
        if self.state.proxy:
            self.state.proxy.stop()
        if self.state.echo_server:
            self.state.echo_server.stop()
        self.destroy()


def main():
    """Entry point."""
    app = NexusTunnelApp()
    app.mainloop()


if __name__ == '__main__':
    main()
