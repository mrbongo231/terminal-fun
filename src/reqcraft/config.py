"""Application configuration for ReqCraft."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from reqcraft.storage import _get_data_dir


@dataclass
class AppConfig:
    """Application-level configuration."""

    theme: str = "dark"
    timeout: float = 30.0
    max_history: int = 500
    follow_redirects: bool = True
    verify_ssl: bool = True
    word_wrap_response: bool = True
    show_sidebar: bool = True

    def to_dict(self) -> dict:
        return {
            "theme": self.theme,
            "timeout": self.timeout,
            "max_history": self.max_history,
            "follow_redirects": self.follow_redirects,
            "verify_ssl": self.verify_ssl,
            "word_wrap_response": self.word_wrap_response,
            "show_sidebar": self.show_sidebar,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppConfig:
        return cls(
            theme=data.get("theme", "dark"),
            timeout=data.get("timeout", 30.0),
            max_history=data.get("max_history", 500),
            follow_redirects=data.get("follow_redirects", True),
            verify_ssl=data.get("verify_ssl", True),
            word_wrap_response=data.get("word_wrap_response", True),
            show_sidebar=data.get("show_sidebar", True),
        )

    @classmethod
    def load(cls, config_dir: Path | None = None) -> AppConfig:
        """Load configuration from disk."""
        config_dir = config_dir or _get_data_dir()
        config_file = config_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return cls.from_dict(json.load(f))
            except (json.JSONDecodeError, KeyError):
                pass
        return cls()

    def save(self, config_dir: Path | None = None) -> None:
        """Save configuration to disk."""
        config_dir = config_dir or _get_data_dir()
        config_file = config_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
