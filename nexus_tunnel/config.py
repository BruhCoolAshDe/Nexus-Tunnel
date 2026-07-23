"""Configuration management and validation."""

import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class TunnelConfig:
    """Core tunnel configuration."""
    user_id: str
    static_port: int
    tunnel_addr: str
    studio_path: str = ""
    map_file: str = ""
    saved_maps: list = None

    def __post_init__(self):
        if self.saved_maps is None:
            self.saved_maps = []

    def validate(self) -> tuple:
        """Validate config. Returns (is_valid, error_message)."""
        if not self.user_id.strip():
            return False, "User ID cannot be empty"
        if not (0 < self.static_port < 65536):
            return False, f"Port must be 1-65535"
        if not self.tunnel_addr or ':' not in self.tunnel_addr:
            return False, "Tunnel address must be host:port"
        return True, None

    @staticmethod
    def get_script_dir() -> Path:
        """Get the directory where the script/exe lives."""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        return Path(__file__).parent.parent

    @classmethod
    def load(cls):
        """Load config from disk or return defaults."""
        config_file = cls.get_script_dir() / 'nexus_config.json'
        defaults = cls(
            user_id='<your-user-id>',
            static_port=55555,
            tunnel_addr='<host:port>'
        )
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    for key in asdict(defaults):
                        if key in data:
                            setattr(defaults, key, data[key])
        except Exception as e:
            print(f"[config] Failed to load: {e}")
        return defaults

    def save(self) -> bool:
        """Save config to disk."""
        config_file = self.get_script_dir() / 'nexus_config.json'
        try:
            with open(config_file, 'w') as f:
                json.dump(asdict(self), f, indent=2)
            return True
        except Exception as e:
            print(f"[config] Failed to save: {e}")
            return False
