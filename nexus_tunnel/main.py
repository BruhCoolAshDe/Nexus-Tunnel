"""Main entry point and application state management."""

import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import uuid

import customtkinter as ctk
from nexus_tunnel.config import TunnelConfig
from nexus_tunnel.studio import StudioPath, StudioLauncher, MapInjector
from nexus_tunnel.networking import UDPProxy, EchoServer, warm_tunnel
from nexus_tunnel.gui import (
    ColorPalette, Fonts, log_append, log_box, styled_entry,
    card_frame, icon_button
)


class AppState:
    """Shared application state."""
    def __init__(self):
        self.config = TunnelConfig.load()
        self.studio_path = StudioPath.detect() or self.config.studio_path
        self.proxy = None
        self.echo_server = EchoServer()


class NexusTunnelApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title('Nexus Tunnel')
        self.geometry('720x660')
        self.minsize(580, 520)
        self.configure(bg=ColorPalette.BG)
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

    def _show_menu(self):
        """Show main menu."""
        if self._current_page:
            self._current_page.destroy()

        frame = tk.Frame(self, bg=ColorPalette.BG)
        frame.pack(fill='both', expand=True)
        self._current_page = frame

        tk.Label(frame, text='NEXUS TUNNEL', font=self.fonts.title,
                 bg=ColorPalette.BG, fg=ColorPalette.TEXT).pack(pady=(16, 4))
        tk.Label(frame, text='Roblox Studio Local Test', font=self.fonts.body,
                 bg=ColorPalette.BG, fg=ColorPalette.MUTED).pack(pady=(0, 20))

        # Buttons
        btn_frame = tk.Frame(frame, bg=ColorPalette.BG)
        btn_frame.pack(pady=10)
        icon_button(btn_frame, '  HOST', 'host', ColorPalette.ACCENT,
                   self._go_host_config).pack(side='left', padx=8)
        icon_button(btn_frame, '  JOIN', 'join', ColorPalette.BLUE,
                   self._go_join_config).pack(side='left', padx=8)
        icon_button(btn_frame, '  ECHO TEST', 'echo', ColorPalette.TEAL,
                   self._go_echo_test).pack(side='left', padx=8)

        # Info
        tk.Label(frame, text=f"Studio: {self.state.studio_path or 'Not found'}",
                 font=self.fonts.small, bg=ColorPalette.BG,
                 fg=ColorPalette.OK if self.state.studio_path else ColorPalette.ERR).pack(pady=(20, 0))

    def _go_host_config(self):
        """Show host configuration screen."""
        if self._current_page:
            self._current_page.destroy()
        frame = tk.Frame(self, bg=ColorPalette.BG)
        frame.pack(fill='both', expand=True)
        self._current_page = frame

        tk.Label(frame, text='HOST SESSION', font=self.fonts.heading,
                 bg=ColorPalette.BG, fg=ColorPalette.TEXT).pack(pady=(12, 4))

        card = card_frame(frame)
        card.pack(fill='x', padx=24, pady=(0, 12))

        entries = {}
        for label, val, key in [
            ('User ID', self.state.config.user_id, 'user_id'),
            ('Port', str(self.state.config.static_port), 'static_port'),
            ('Tunnel Address', self.state.config.tunnel_addr, 'tunnel_addr'),
        ]:
            tk.Label(card, text=label, font=self.fonts.small,
                     bg=ColorPalette.CARD, fg=ColorPalette.MUTED).pack(anchor='w', padx=12, pady=(8, 2))
            e = styled_entry(card, val, width=300)
            e.pack(anchor='w', padx=12, pady=(0, 4), fill='x')
            entries[key] = e

        btn_frame = tk.Frame(frame, bg=ColorPalette.BG)
        btn_frame.pack(pady=16)
        icon_button(btn_frame, '  Back', 'back', ColorPalette.CARD,
                   self._show_menu).pack(side='left', padx=8)
        icon_button(btn_frame, '  Launch', 'host', ColorPalette.ACCENT,
                   lambda: self._launch_server(entries)).pack(side='left', padx=8)

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
            messagebox.showerror('Invalid Input', 'Check your entries')

    def _go_host_running(self, uid, port, addr):
        """Show running host console."""
        if self._current_page:
            self._current_page.destroy()
        frame = tk.Frame(self, bg=ColorPalette.BG)
        frame.pack(fill='both', expand=True)
        self._current_page = frame

        tk.Label(frame, text='SERVER CONSOLE', font=self.fonts.heading,
                 bg=ColorPalette.BG, fg=ColorPalette.TEXT).pack(pady=(8, 2))

        logw = log_box(frame, height=12)
        logw.pack(fill='both', expand=True, padx=18, pady=(4, 6))

        def _log(msg, tag=''):
            log_append(logw, msg, tag)

        def run():
            pg = str(uuid.uuid4()).upper()
            tg = str(uuid.uuid4()).upper()
            _log(f'Parent GUID: {pg}', 'dim')
            _log(f'PlayTest GUID: {tg}', 'dim')
            _log(f'Server port: {port}', 'info')
            _log('Launching server...', 'warn')
            if not self.state.studio_path:
                _log('Studio path not set!', 'err')
                return
            ok = StudioLauncher.launch_server(self.state.studio_path, port, uid, pg, tg)
            _log('✓ Server launched!' if ok else '✗ Failed to launch', 'ok' if ok else 'err')

        threading.Thread(target=run, daemon=True).start()

        btn_frame = tk.Frame(frame, bg=ColorPalette.BG)
        btn_frame.pack(pady=12)
        icon_button(btn_frame, '  Back', 'back', ColorPalette.CARD,
                   self._show_menu).pack(side='left', padx=8)

    def _go_join_config(self):
        """Show join configuration screen."""
        if self._current_page:
            self._current_page.destroy()
        frame = tk.Frame(self, bg=ColorPalette.BG)
        frame.pack(fill='both', expand=True)
        self._current_page = frame

        tk.Label(frame, text='JOIN SESSION', font=self.fonts.heading,
                 bg=ColorPalette.BG, fg=ColorPalette.TEXT).pack(pady=(12, 4))

        card = card_frame(frame)
        card.pack(fill='x', padx=24, pady=(0, 12))
        tk.Label(card, text='Tunnel Address (host:port)', font=self.fonts.small,
                 bg=ColorPalette.CARD, fg=ColorPalette.MUTED).pack(anchor='w', padx=12, pady=(8, 2))
        addr_e = styled_entry(card, '', width=300)
        addr_e.pack(anchor='w', padx=12, pady=(0, 12), fill='x')

        btn_frame = tk.Frame(frame, bg=ColorPalette.BG)
        btn_frame.pack(pady=16)
        icon_button(btn_frame, '  Back', 'back', ColorPalette.CARD,
                   self._show_menu).pack(side='left', padx=8)
        icon_button(btn_frame, '  Connect', 'join', ColorPalette.BLUE,
                   lambda: self._join_server(addr_e.get())).pack(side='left', padx=8)

    def _join_server(self, addr):
        """Join a server via proxy."""
        if ':' not in addr:
            messagebox.showerror('Invalid', 'Format: host:port')
            return
        host, port = addr.rsplit(':', 1)
        self._go_join_running(host, int(port))

    def _go_join_running(self, host, port):
        """Show join console."""
        if self._current_page:
            self._current_page.destroy()
        frame = tk.Frame(self, bg=ColorPalette.BG)
        frame.pack(fill='both', expand=True)
        self._current_page = frame

        tk.Label(frame, text='CONNECTION CONSOLE', font=self.fonts.heading,
                 bg=ColorPalette.BG, fg=ColorPalette.TEXT).pack(pady=(8, 2))

        logw = log_box(frame, height=12)
        logw.pack(fill='both', expand=True, padx=18, pady=(4, 6))

        def _log(msg, tag=''):
            log_append(logw, msg, tag)

        def run():
            _log(f'Target: {host}:{port}', 'info')
            _log('Starting proxy...', 'warn')
            proxy = UDPProxy(55555, host, port)
            if not proxy.start():
                _log('Failed to start proxy', 'err')
                return
            self.state.proxy = proxy
            _log('✓ Proxy active', 'ok')
            _log('Warming tunnel...', 'warn')
            warm_tunnel(55555)
            _log('✓ Tunnel warmed', 'ok')
            if not self.state.studio_path:
                _log('Studio path not set!', 'err')
                return
            pg = str(uuid.uuid4()).upper()
            tg = str(uuid.uuid4()).upper()
            ok = StudioLauncher.launch_client(self.state.studio_path, '127.0.0.1', 55555, pg, tg)
            _log('✓ Client launched!' if ok else '✗ Failed', 'ok' if ok else 'err')

        threading.Thread(target=run, daemon=True).start()

        btn_frame = tk.Frame(frame, bg=ColorPalette.BG)
        btn_frame.pack(pady=12)
        icon_button(btn_frame, '  Disconnect', 'stop', ColorPalette.ERR,
                   self._disconnect).pack(side='left', padx=8)

    def _disconnect(self):
        """Disconnect and return to menu."""
        if self.state.proxy:
            self.state.proxy.stop()
            self.state.proxy = None
        self._show_menu()

    def _go_echo_test(self):
        """Show echo test screen."""
        if self._current_page:
            self._current_page.destroy()
        frame = tk.Frame(self, bg=ColorPalette.BG)
        frame.pack(fill='both', expand=True)
        self._current_page = frame

        tk.Label(frame, text='ECHO TEST', font=self.fonts.heading,
                 bg=ColorPalette.BG, fg=ColorPalette.TEXT).pack(pady=(12, 4))

        logw = log_box(frame, height=12)
        logw.pack(fill='both', expand=True, padx=18, pady=(4, 6))

        def _log(msg, tag=''):
            log_append(logw, msg, tag)

        btn_frame = tk.Frame(frame, bg=ColorPalette.BG)
        btn_frame.pack(pady=12)
        icon_button(btn_frame, '  Back', 'back', ColorPalette.CARD,
                   self._show_menu).pack(side='left', padx=8)
        icon_button(btn_frame, '  Start Server', 'echo', ColorPalette.TEAL,
                   lambda: self._start_echo(_log)).pack(side='left', padx=8)

    def _start_echo(self, _log):
        """Start the echo server."""
        ok, err = self.state.echo_server.start(55555)
        if ok:
            _log('✓ Echo server started', 'ok')
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
    ctk.set_appearance_mode('dark')
    app = NexusTunnelApp()
    app.mainloop()


if __name__ == '__main__':
    main()
