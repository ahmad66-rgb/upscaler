"""Persistent settings helper."""
from __future__ import annotations

import json
from pathlib import Path

from models.config import AppConfig


class SettingsManager:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._config = AppConfig()
        self.load()

    @property
    def config(self) -> AppConfig:
        return self._config

    def load(self) -> AppConfig:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._config = AppConfig.from_dict(raw)
        return self._config

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self._config.to_dict(), indent=2),
            encoding="utf-8",
        )
