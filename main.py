"""Application entry point for Ignition AI Upscaler."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from utils.settings_manager import SettingsManager
from utils.theme import ThemeManager


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ignition AI Upscaler")
    app.setOrganizationName("Ignition AI")

    settings_manager = SettingsManager(Path("config/settings.json"))
    theme_manager = ThemeManager(settings_manager)

    window = MainWindow(settings_manager=settings_manager, theme_manager=theme_manager)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
