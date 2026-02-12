"""Main window and page routing."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from models.config import VideoInfo
from processing.pipeline import ProcessingController
from ui.pages import CompletionPage, HomePage, ProcessingPage, SettingsPage
from utils.system import check_for_updates


class MainWindow(QMainWindow):
    VERSION = "1.0.0"

    def __init__(self, settings_manager, theme_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.video_info: VideoInfo | None = None
        self.controller: ProcessingController | None = None
        self.output_path: Path | None = None

        self.setWindowTitle("Ignition AI Upscaler")
        self.resize(1280, 820)
        self._build_ui()
        self.theme_manager.apply(QApplication.instance())
        self._check_updates()

    def _build_ui(self) -> None:
        container = QWidget()
        root_layout = QVBoxLayout(container)

        top = QHBoxLayout()
        top.addWidget(QLabel("🔥 Ignition AI Upscaler"))
        top.addStretch(1)
        mode_button = QPushButton("Toggle Theme")
        mode_button.clicked.connect(lambda: self.theme_manager.toggle(QApplication.instance()))
        top.addWidget(mode_button)
        root_layout.addLayout(top)

        self.stack = QStackedWidget()
        self.home_page = HomePage()
        self.settings_page = SettingsPage(self.settings_manager)
        self.processing_page = ProcessingPage()
        self.completion_page = CompletionPage()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.processing_page)
        self.stack.addWidget(self.completion_page)

        self.home_page.next_clicked.connect(self._on_home_next)
        self.settings_page.back_clicked.connect(lambda: self._switch_to(0))
        self.settings_page.start_clicked.connect(self._start_processing)
        self.processing_page.cancel_clicked.connect(self._cancel_processing)
        self.processing_page.pause_resume_clicked.connect(self._pause_resume)
        self.completion_page.process_another_clicked.connect(self._reset_to_home)
        self.completion_page.open_output_clicked.connect(self._open_output_folder)

        root_layout.addWidget(self.stack)
        self.setCentralWidget(container)

    def _on_home_next(self, video_info: VideoInfo) -> None:
        self.video_info = video_info
        self.settings_page.apply_video_info(video_info)
        self._switch_to(1)

    def _start_processing(self) -> None:
        if not self.video_info:
            QMessageBox.warning(self, "Video required", "Please select a video first.")
            return
        self.settings_page.flush_to_settings()
        self.settings_manager.save()

        self.controller = ProcessingController(self.settings_manager.config, self.video_info)
        self.controller.worker.progress.connect(self.processing_page.update_status)
        self.controller.worker.log.connect(self.processing_page.append_log)
        self.controller.worker.finished.connect(self._on_processing_finished)
        self.controller.worker.failed.connect(self._on_processing_failed)
        self.processing_page.reset()
        self._switch_to(2)
        self.controller.start()

    def _on_processing_finished(self, output_path: Path):
        self.output_path = output_path
        self.completion_page.set_results(self.video_info.path, output_path)
        self._switch_to(3)

    def _on_processing_failed(self, error: str):
        QMessageBox.critical(self, "Processing failed", error)
        self._switch_to(1)

    def _cancel_processing(self):
        if self.controller:
            self.controller.stop()
            self.processing_page.append_log("Cancellation requested...")

    def _pause_resume(self):
        if self.controller:
            self.controller.pause_resume()

    def _reset_to_home(self):
        self.video_info = None
        self.output_path = None
        self.home_page.reset()
        self._switch_to(0)

    def _open_output_folder(self):
        if not self.output_path:
            return
        folder = self.output_path.parent
        import subprocess

        subprocess.run(["xdg-open", str(folder)], check=False)

    def _check_updates(self):
        latest = check_for_updates(self.VERSION, "https://example.com/ignition/version.json")
        if latest:
            QMessageBox.information(self, "Update available", f"Version {latest} is available.")

    def _switch_to(self, index: int) -> None:
        self._animate_transition(self.stack.currentIndex(), index)
        self.stack.setCurrentIndex(index)

    def _animate_transition(self, _from: int, _to: int) -> None:
        animation = QPropertyAnimation(self.stack, b"windowOpacity")
        animation.setDuration(220)
        animation.setStartValue(0.65)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        self._animation = animation
