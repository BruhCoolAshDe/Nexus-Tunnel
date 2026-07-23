"""Roblox Studio detection, launching, and injection."""

import glob
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class StudioPath:
    """Find and validate Roblox Studio installation."""

    VINEGAR = '__VINEGAR__'  # Sentinel for Flatpak Vinegar

    @staticmethod
    def detect() -> Optional[str]:
        """Auto-detect Studio path. Returns path or None."""
        system = platform.system()

        if system == 'Windows':
            return StudioPath._detect_windows()
        elif system == 'Darwin':
            return StudioPath._detect_macos()
        elif system == 'Linux':
            return StudioPath._detect_linux()
        return None

    @staticmethod
    def _detect_windows() -> Optional[str]:
        base = os.environ.get('LOCALAPPDATA', '')
        pat = os.path.join(base, 'Roblox', 'Versions', '*', 'RobloxStudioBeta.exe')
        hits = sorted(glob.glob(pat))
        return hits[-1] if hits else None

    @staticmethod
    def _detect_macos() -> Optional[str]:
        candidates = [
            '/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio',
            os.path.expanduser('~/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio'),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    @staticmethod
    def _detect_linux() -> Optional[str]:
        if shutil.which('flatpak'):
            try:
                result = subprocess.run(
                    ['flatpak', 'info', 'org.vinegarhq.Vinegar'],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return StudioPath.VINEGAR
            except Exception:
                pass
        return None

    @staticmethod
    def is_valid(path: str) -> bool:
        """Check if path exists and is executable."""
        if path == StudioPath.VINEGAR:
            return True
        return os.path.isfile(path) and os.access(path, os.X_OK)


class StudioLauncher:
    """Launch Studio in server or client mode."""

    @staticmethod
    def _build_cmd(studio_path: str, args: list) -> list:
        """Build launch command based on platform."""
        if studio_path == StudioPath.VINEGAR:
            return ['flatpak', 'run', 'org.vinegarhq.Vinegar', 'studio', '--'] + args
        return [studio_path] + args

    @staticmethod
    def launch_server(
        studio_path: str,
        port: int,
        user_id: str,
        parent_guid: str,
        playtask_guid: str,
    ) -> bool:
        """Launch Studio in server mode."""
        if not StudioPath.is_valid(studio_path):
            return False
        cmd = StudioLauncher._build_cmd(
            studio_path,
            [
                '-task', 'StartServer',
                '-placeId', '0',
                '-universeId', '0',
                '-placeVersion', '1',
                '-port', str(port),
                '-creatorId', user_id,
                '-creatorType', '1',
                '-numTestServerPlayersUponStartup', '1',
                '-userid', user_id,
                '-parentSessionGuid', parent_guid,
                '-playTestSessionGuid', playtask_guid,
                '-instanceId', 'StudioServer',
            ],
        )
        try:
            subprocess.Popen(cmd)
            return True
        except Exception as e:
            print(f"[studio] Failed to launch server: {e}")
            return False

    @staticmethod
    def launch_client(
        studio_path: str,
        server_addr: str,
        server_port: int,
        parent_guid: str,
        playtask_guid: str,
        instance_id: str = 'StudioPlayer_0',
    ) -> bool:
        """Launch Studio in client mode."""
        if not StudioPath.is_valid(studio_path):
            return False
        cmd = StudioLauncher._build_cmd(
            studio_path,
            [
                '-task', 'StartClient',
                '-placeId', '0',
                '-universeId', '0',
                '-placeVersion', '1',
                '-server', server_addr,
                '-port', str(server_port),
                '-parentSessionGuid', parent_guid,
                '-playTestSessionGuid', playtask_guid,
                '-instanceId', instance_id,
            ],
        )
        try:
            subprocess.Popen(cmd)
            return True
        except Exception as e:
            print(f"[studio] Failed to launch client: {e}")
            return False


class MapInjector:
    """Inject .rbxl maps into Studio runtime cache."""

    @staticmethod
    def get_runtime_path() -> Optional[Path]:
        """Get the Studio runtime server.rbxl path per platform."""
        system = platform.system()
        if system == 'Windows':
            base = os.environ.get('LOCALAPPDATA', '')
            return Path(base) / 'Roblox' / 'server.rbxl'
        elif system == 'Darwin':
            return Path.home() / 'Library' / 'Application Support' / 'Roblox' / 'server.rbxl'
        elif system == 'Linux':
            return Path.home() / '.var' / 'app' / 'org.vinegarhq.Vinegar' / 'data' / 'Roblox' / 'server.rbxl'
        return None

    @staticmethod
    def inject(map_path: str) -> tuple:
        """Inject map. Returns (success, error_msg)."""
        if not os.path.isfile(map_path):
            return False, f"Map file not found: {map_path}"

        target = MapInjector.get_runtime_path()
        if not target:
            return False, "Could not determine runtime path"

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            shutil.copy2(map_path, target)
            return True, None
        except Exception as e:
            return False, str(e)
