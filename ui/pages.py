"""UI pages for the application."""
from __future__ import annotations

import math
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.config import ProcessingStatus, VideoInfo
from utils.video_utils import probe_video, thumbnail_for_video


class HomePage(QWidget):
    next_clicked = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.video_info: VideoInfo | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        logo = QLabel("🔥")
        logo.setStyleSheet("font-size: 52px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Ignition AI Upscaler")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: 700;")

        self.drop_zone = QLabel("Drag & Drop one or more videos here")
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setMinimumHeight(180)
        self.drop_zone.setStyleSheet("border: 2px dashed #666; border-radius: 12px;")

        browse_button = QPushButton("Browse Video")
        browse_button.clicked.connect(self._browse)

        self.thumb = QLabel("No video selected")
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setMinimumHeight(170)

        self.meta = QLabel("Resolution: -\nDuration: -\nFPS: -\nFile size: -")
        self.meta.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_button = QPushButton("Next")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self._emit_next)

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(self.drop_zone)
        layout.addWidget(browse_button)
        layout.addWidget(self.thumb)
        layout.addWidget(self.meta)
        layout.addWidget(self.next_button)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        videos = [p for p in paths if p.suffix.lower() in {".mp4", ".mov", ".mkv", ".avi"}]
        if videos:
            self._set_video(videos[0])

    def _browse(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select video(s)",
            "",
            "Video files (*.mp4 *.mkv *.mov *.avi)",
        )
        if files:
            self._set_video(Path(files[0]))

    def _set_video(self, path: Path):
        self.video_info = probe_video(path)
        pixmap = thumbnail_for_video(path)
        self.thumb.setPixmap(pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation))
        mbytes = self.video_info.file_size_bytes / (1024 * 1024)
        self.meta.setText(
            f"Resolution: {self.video_info.width}x{self.video_info.height}\n"
            f"Duration: {self.video_info.duration_seconds:.2f}s\n"
            f"FPS: {self.video_info.fps:.2f}\n"
            f"File size: {mbytes:.2f}MB"
        )
        self.next_button.setEnabled(True)

    def _emit_next(self):
        if self.video_info:
            self.next_clicked.emit(self.video_info)

    def reset(self):
        self.video_info = None
        self.next_button.setEnabled(False)
        self.thumb.setText("No video selected")
        self.meta.setText("Resolution: -\nDuration: -\nFPS: -\nFile size: -")


class SettingsPage(QWidget):
    back_clicked = pyqtSignal()
    start_clicked = pyqtSignal()

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        grid = QGridLayout()

        video_box = QGroupBox("Video Settings")
        video_form = QFormLayout(video_box)
        self.upscale_factor = QComboBox(); self.upscale_factor.addItems(["2x", "4x", "custom"])
        self.custom_scale = QSpinBox(); self.custom_scale.setRange(1, 8); self.custom_scale.setValue(2)
        self.output_resolution = QLineEdit()
        self.fps_mode = QComboBox(); self.fps_mode.addItems(["keep", "custom"])
        self.custom_fps = QSpinBox(); self.custom_fps.setRange(1, 240); self.custom_fps.setValue(30)
        self.codec = QComboBox(); self.codec.addItems(["H264", "H265", "AV1"])
        self.bitrate = QComboBox(); self.bitrate.addItems(["Low", "Medium", "High", "Custom"])
        self.custom_bitrate = QSpinBox(); self.custom_bitrate.setRange(1000, 100000); self.custom_bitrate.setValue(8000)
        for label, widget in [
            ("Upscale factor", self.upscale_factor),
            ("Custom scale", self.custom_scale),
            ("Output resolution", self.output_resolution),
            ("Frame rate", self.fps_mode),
            ("Custom FPS", self.custom_fps),
            ("Codec", self.codec),
            ("Bitrate", self.bitrate),
            ("Custom bitrate (kbps)", self.custom_bitrate),
        ]:
            video_form.addRow(label, widget)

        model_box = QGroupBox("AI Model Settings")
        model_form = QFormLayout(model_box)
        self.model = QComboBox(); self.model.addItems([
            "Real-ESRGAN General", "Real-ESRGAN Anime", "Face Enhancement Mode"
        ])
        self.denoise = QSlider(Qt.Orientation.Horizontal); self.denoise.setRange(0, 100); self.denoise.setValue(30)
        self.sharpen = QSlider(Qt.Orientation.Horizontal); self.sharpen.setRange(0, 100); self.sharpen.setValue(20)
        self.artifact_reduction = QCheckBox("Enabled"); self.artifact_reduction.setChecked(True)
        self.face_enhance = QCheckBox("Enabled")
        model_form.addRow("Model", self.model)
        model_form.addRow("Denoise", self.denoise)
        model_form.addRow("Sharpening", self.sharpen)
        model_form.addRow("Artifact reduction", self.artifact_reduction)
        model_form.addRow("Face enhancement", self.face_enhance)

        perf_box = QGroupBox("Performance Settings")
        perf_form = QFormLayout(perf_box)
        self.processing_mode = QComboBox(); self.processing_mode.addItems(["GPU", "CPU"])
        self.vram_limit = QSpinBox(); self.vram_limit.setRange(1, 48); self.vram_limit.setValue(4)
        self.multithreading = QCheckBox("Enabled"); self.multithreading.setChecked(True)
        self.batch_mode = QCheckBox("Enabled")
        perf_form.addRow("Processing mode", self.processing_mode)
        perf_form.addRow("VRAM limit (GB)", self.vram_limit)
        perf_form.addRow("Multi-threading", self.multithreading)
        perf_form.addRow("Batch processing", self.batch_mode)

        export_box = QGroupBox("Export Settings")
        export_form = QFormLayout(export_box)
        folder_row = QHBoxLayout()
        self.output_folder = QLineEdit("output")
        choose_folder = QPushButton("Select")
        choose_folder.clicked.connect(self._choose_output_folder)
        folder_row.addWidget(self.output_folder); folder_row.addWidget(choose_folder)
        self.file_format = QComboBox(); self.file_format.addItems(["MP4", "MKV", "MOV"])
        self.rename_file = QLineEdit()
        self.auto_overwrite = QCheckBox("Enabled")
        self.preset = QComboBox(); self.preset.addItems(["Custom", "YouTube 4K", "TikTok HD", "Cinema 4K"])
        export_form.addRow("Output folder", folder_row)
        export_form.addRow("Format", self.file_format)
        export_form.addRow("Rename", self.rename_file)
        export_form.addRow("Auto overwrite", self.auto_overwrite)
        export_form.addRow("Export preset", self.preset)

        grid.addWidget(video_box, 0, 0)
        grid.addWidget(model_box, 0, 1)
        grid.addWidget(perf_box, 1, 0)
        grid.addWidget(export_box, 1, 1)

        buttons = QHBoxLayout()
        back = QPushButton("Back"); back.clicked.connect(self.back_clicked.emit)
        start = QPushButton("Start Processing"); start.clicked.connect(self.start_clicked.emit)
        buttons.addWidget(back)
        buttons.addStretch(1)
        buttons.addWidget(start)

        layout.addLayout(grid)
        layout.addLayout(buttons)
        self._load_from_settings()

    def apply_video_info(self, _video_info: VideoInfo):
        pass

    def _choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Output folder")
        if folder:
            self.output_folder.setText(folder)

    def _load_from_settings(self):
        cfg = self.settings_manager.config
        self.upscale_factor.setCurrentText(cfg.video.upscale_factor)
        self.custom_scale.setValue(int(cfg.video.custom_scale))
        self.output_resolution.setText(cfg.video.output_resolution)
        self.fps_mode.setCurrentText(cfg.video.frame_rate_mode)
        self.custom_fps.setValue(int(cfg.video.custom_fps))
        self.codec.setCurrentText(cfg.video.codec)
        self.bitrate.setCurrentText(cfg.video.bitrate)
        self.custom_bitrate.setValue(cfg.video.custom_bitrate)
        self.model.setCurrentText(cfg.ai.model_name)
        self.denoise.setValue(cfg.ai.denoise_strength)
        self.sharpen.setValue(cfg.ai.sharpening)
        self.artifact_reduction.setChecked(cfg.ai.artifact_reduction)
        self.face_enhance.setChecked(cfg.ai.face_enhancement)
        self.processing_mode.setCurrentText(cfg.performance.processing_mode)
        self.vram_limit.setValue(cfg.performance.vram_limit_gb)
        self.multithreading.setChecked(cfg.performance.multithreading)
        self.batch_mode.setChecked(cfg.performance.batch_mode)
        self.output_folder.setText(cfg.export.output_folder)
        self.file_format.setCurrentText(cfg.export.file_format)
        self.rename_file.setText(cfg.export.rename_file)
        self.auto_overwrite.setChecked(cfg.export.auto_overwrite)
        self.preset.setCurrentText(cfg.export.preset)

    def flush_to_settings(self):
        cfg = self.settings_manager.config
        cfg.video.upscale_factor = self.upscale_factor.currentText()
        cfg.video.custom_scale = float(self.custom_scale.value())
        cfg.video.output_resolution = self.output_resolution.text().strip()
        cfg.video.frame_rate_mode = self.fps_mode.currentText()
        cfg.video.custom_fps = float(self.custom_fps.value())
        cfg.video.codec = self.codec.currentText()
        cfg.video.bitrate = self.bitrate.currentText()
        cfg.video.custom_bitrate = self.custom_bitrate.value()

        cfg.ai.model_name = self.model.currentText()
        cfg.ai.denoise_strength = self.denoise.value()
        cfg.ai.sharpening = self.sharpen.value()
        cfg.ai.artifact_reduction = self.artifact_reduction.isChecked()
        cfg.ai.face_enhancement = self.face_enhance.isChecked()

        cfg.performance.processing_mode = self.processing_mode.currentText()
        cfg.performance.vram_limit_gb = self.vram_limit.value()
        cfg.performance.multithreading = self.multithreading.isChecked()
        cfg.performance.batch_mode = self.batch_mode.isChecked()

        cfg.export.output_folder = self.output_folder.text().strip() or "output"
        cfg.export.file_format = self.file_format.currentText()
        cfg.export.rename_file = self.rename_file.text().strip()
        cfg.export.auto_overwrite = self.auto_overwrite.isChecked()
        cfg.export.preset = self.preset.currentText()
        self._apply_preset()

    def _apply_preset(self):
        preset = self.preset.currentText()
        if preset == "YouTube 4K":
            self.output_resolution.setText("3840x2160")
            self.codec.setCurrentText("H265")
            self.bitrate.setCurrentText("High")
        elif preset == "TikTok HD":
            self.output_resolution.setText("1080x1920")
            self.codec.setCurrentText("H264")
            self.bitrate.setCurrentText("Medium")
        elif preset == "Cinema 4K":
            self.output_resolution.setText("4096x2160")
            self.codec.setCurrentText("AV1")
            self.bitrate.setCurrentText("High")


class ProcessingPage(QWidget):
    cancel_clicked = pyqtSignal()
    pause_resume_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.paused = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.details = QLabel("Current frame: 0/0 | ETA: -- | Usage: --")
        self.logs = QTextEdit(); self.logs.setReadOnly(True)

        controls = QHBoxLayout()
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self._toggle_pause)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancel_clicked.emit)
        controls.addWidget(self.pause_btn)
        controls.addWidget(cancel_btn)

        layout.addWidget(QLabel("Processing..."))
        layout.addWidget(self.progress)
        layout.addWidget(self.details)
        layout.addWidget(self.logs)
        layout.addLayout(controls)

    def reset(self):
        self.progress.setValue(0)
        self.details.setText("Current frame: 0/0 | ETA: -- | Usage: --")
        self.logs.clear()
        self.paused = False
        self.pause_btn.setText("Pause")

    def update_status(self, status: ProcessingStatus):
        percent = int((status.current_frame / max(status.total_frames, 1)) * 100)
        self.progress.setValue(percent)
        eta_min = math.ceil(status.eta_seconds / 60)
        self.details.setText(
            f"Current frame: {status.current_frame}/{status.total_frames} | "
            f"ETA: {eta_min} min | Usage: {status.usage_percent:.1f}%"
        )

    def append_log(self, line: str):
        self.logs.append(line)

    def _toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.setText("Resume" if self.paused else "Pause")
        self.pause_resume_clicked.emit()


class CompletionPage(QWidget):
    open_output_clicked = pyqtSignal()
    process_another_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        compare = QHBoxLayout()

        before_group = QVBoxLayout()
        before_group.addWidget(QLabel("Before"))
        self.before_video = QVideoWidget()
        before_group.addWidget(self.before_video)
        self.before_player = QMediaPlayer(self)
        self.before_audio = QAudioOutput(self)
        self.before_player.setVideoOutput(self.before_video)
        self.before_player.setAudioOutput(self.before_audio)

        after_group = QVBoxLayout()
        after_group.addWidget(QLabel("After"))
        self.after_video = QVideoWidget()
        after_group.addWidget(self.after_video)
        self.after_player = QMediaPlayer(self)
        self.after_audio = QAudioOutput(self)
        self.after_player.setVideoOutput(self.after_video)
        self.after_player.setAudioOutput(self.after_audio)

        compare.addLayout(before_group)
        compare.addLayout(after_group)

        self.stats = QLabel("Improvement stats: -")
        open_btn = QPushButton("Open Output Folder")
        open_btn.clicked.connect(self.open_output_clicked.emit)
        restart_btn = QPushButton("Process Another Video")
        restart_btn.clicked.connect(self.process_another_clicked.emit)
        play_btn = QPushButton("Play Both Videos")
        play_btn.clicked.connect(self._play)

        actions = QHBoxLayout()
        actions.addWidget(play_btn)
        actions.addStretch(1)
        actions.addWidget(open_btn)
        actions.addWidget(restart_btn)

        layout.addLayout(compare)
        layout.addWidget(self.stats)
        layout.addLayout(actions)

    def set_results(self, before: Path, after: Path):
        from PyQt6.QtCore import QUrl

        self.before_player.setSource(QUrl.fromLocalFile(str(before)))
        self.after_player.setSource(QUrl.fromLocalFile(str(after)))
        self.stats.setText(f"Improvement stats: source={before.name} -> output={after.name}")

    def _play(self):
        self.before_player.play()
        self.after_player.play()
