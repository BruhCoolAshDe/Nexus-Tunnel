"""UDP proxy, echo test, and connectivity utilities."""

import os
import socket
import threading
import time
import random
from typing import Callable, Optional


class UDPProxy:
    """UDP relay from local port to remote host:port."""

    def __init__(self, local_port: int, remote_host: str, remote_port: int):
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self._running = False
        self._thread = None
        self._sock = None
        self._sessions = {}
        self._lock = threading.Lock()

    def start(self) -> bool:
        """Start the proxy. Returns success."""
        if self._running:
            return True
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        time.sleep(0.2)  # Let it bind
        return self._running

    def stop(self):
        """Stop the proxy."""
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2.0)

    def is_running(self) -> bool:
        return self._running

    def _run(self):
        """Main proxy loop."""
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(('127.0.0.1', self.local_port))
            self._sock.settimeout(1.0)

            # Resolve remote host once
            remote_ip = socket.gethostbyname(self.remote_host)

            while self._running:
                try:
                    data, addr = self._sock.recvfrom(65536)
                except socket.timeout:
                    continue
                except OSError:
                    break

                # Create or reuse remote socket for this client
                with self._lock:
                    if addr not in self._sessions:
                        remote_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        remote_sock.settimeout(1.0)
                        self._sessions[addr] = remote_sock
                        # Start listener thread
                        threading.Thread(
                            target=self._listen_remote,
                            args=(remote_sock, addr),
                            daemon=True,
                        ).start()

                    remote_sock = self._sessions[addr]

                try:
                    remote_sock.sendto(data, (remote_ip, self.remote_port))
                except Exception:
                    pass
        except Exception as e:
            print(f"[proxy] Error: {e}")
        finally:
            with self._lock:
                for sock in self._sessions.values():
                    try:
                        sock.close()
                    except Exception:
                        pass
                self._sessions.clear()
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass

    def _listen_remote(self, remote_sock: socket.socket, client_addr: tuple):
        """Listen for replies from remote and send back to client."""
        while self._running:
            try:
                data, _ = remote_sock.recvfrom(65536)
                with self._lock:
                    if self._sock:
                        self._sock.sendto(data, client_addr)
            except socket.timeout:
                continue
            except Exception:
                break


class EchoServer:
    """UDP echo test server."""

    ECHO_REQ = b'NEP_TEST\x00'
    ECHO_RESP = b'NEP_ECHO\x00'

    def __init__(self):
        self._running = False
        self._thread = None
        self._sock = None
        self.port = 0
        self.echoed_count = 0
        self.clients_seen = set()
        self._lock = threading.Lock()

    def start(self, port: int) -> tuple:
        """Start the echo server. Returns (success, error_msg)."""
        if self._running:
            return True, None
        self.port = port
        self.echoed_count = 0
        self.clients_seen.clear()
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(('0.0.0.0', port))
            self._sock.settimeout(0.5)
        except OSError as e:
            return False, f"Could not bind port {port}: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True, None

    def stop(self):
        """Stop the echo server."""
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=1.0)

    def is_running(self) -> bool:
        return self._running

    def _run(self):
        """Main echo loop."""
        while self._running:
            try:
                data, addr = self._sock.recvfrom(512)
            except socket.timeout:
                continue
            except OSError:
                break

            if data.startswith(self.ECHO_REQ):
                nonce = data[len(self.ECHO_REQ):]
                try:
                    self._sock.sendto(self.ECHO_RESP + nonce, addr)
                    with self._lock:
                        self.echoed_count += 1
                        self.clients_seen.add(addr[0])
                except OSError:
                    pass


def warm_tunnel(proxy_port: int, packets: int = 8, interval: float = 0.1) -> int:
    """Send warm-up packets. Returns count sent."""
    sent = 0
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.3)
        for _ in range(packets):
            payload = bytes([0xFF, 0x00]) + os.urandom(random.randint(6, 20))
            try:
                sock.sendto(payload, ('127.0.0.1', proxy_port))
                sent += 1
            except OSError:
                break
            time.sleep(interval)
    except Exception:
        pass
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass
    return sent
