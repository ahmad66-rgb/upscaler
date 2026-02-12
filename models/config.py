"""Configuration models for the app."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VideoSettings:
    upscale_factor: str = "2x"
    custom_scale: float = 2.0
    output_resolution: str = ""
    frame_rate_mode: str = "keep"
    custom_fps: float = 30.0
    codec: str = "H264"
    bitrate: str = "Medium"
    custom_bitrate: int = 8000


@dataclass
class AIModelSettings:
    model_name: str = "Real-ESRGAN General"
    denoise_strength: int = 30
    sharpening: int = 20
    artifact_reduction: bool = True
    face_enhancement: bool = False


@dataclass
class PerformanceSettings:
    processing_mode: str = "GPU"
    vram_limit_gb: int = 4
    multithreading: bool = True
    batch_mode: bool = False


@dataclass
class ExportSettings:
    output_folder: str = "output"
    file_format: str = "MP4"
    rename_file: str = ""
    auto_overwrite: bool = False
    preset: str = "Custom"


@dataclass
class AppConfig:
    video: VideoSettings = field(default_factory=VideoSettings)
    ai: AIModelSettings = field(default_factory=AIModelSettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    theme: str = "dark"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        return cls(
            video=VideoSettings(**data.get("video", {})),
            ai=AIModelSettings(**data.get("ai", {})),
            performance=PerformanceSettings(**data.get("performance", {})),
            export=ExportSettings(**data.get("export", {})),
            theme=data.get("theme", "dark"),
        )


@dataclass
class VideoInfo:
    path: Path
    width: int
    height: int
    duration_seconds: float
    fps: float
    file_size_bytes: int
    total_frames: int


@dataclass
class ProcessingStatus:
    current_frame: int
    total_frames: int
    eta_seconds: float
    usage_percent: float
    message: str
