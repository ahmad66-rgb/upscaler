"""Theme manager and styles."""
from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette


class ThemeManager:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager

    def apply(self, app):
        theme = self.settings_manager.config.theme
        if theme == "dark":
            self._apply_dark(app)
        else:
            self._apply_light(app)

    def toggle(self, app):
        self.settings_manager.config.theme = (
            "light" if self.settings_manager.config.theme == "dark" else "dark"
        )
        self.settings_manager.save()
        self.apply(app)

    @staticmethod
    def glass_panel_stylesheet() -> str:
        return """
        QWidget#glassPanel {
            background: rgba(30, 30, 40, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
        }
        """

    def _apply_dark(self, app):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(18, 18, 22))
        palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 35))
        palette.setColor(QPalette.ColorRole.Text, QColor(238, 238, 238))
        palette.setColor(QPalette.ColorRole.Button, QColor(44, 44, 52))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(245, 245, 245))
        app.setPalette(palette)

    def _apply_light(self, app):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 246, 250))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 35))
        palette.setColor(QPalette.ColorRole.Button, QColor(232, 235, 242))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 35))
        app.setPalette(palette)
