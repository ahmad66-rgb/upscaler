"""Video processing pipeline using FFmpeg + Real-ESRGAN."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
import psutil
import torch
from PyQt6.QtCore import QMutex, QObject, QThread, pyqtSignal

from models.config import AppConfig, ProcessingStatus, VideoInfo
from utils.model_manager import ensure_model_weight
from utils.system import detect_hardware


class ProcessingWorker(QObject):
    progress = pyqtSignal(object)
    log = pyqtSignal(str)
    finished = pyqtSignal(Path)
    failed = pyqtSignal(str)

    def __init__(self, config: AppConfig, video_info: VideoInfo):
        super().__init__()
        self.config = config
        self.video_info = video_info
        self._cancelled = False
        self._paused = False
        self._mutex = QMutex()

    def cancel(self) -> None:
        self._cancelled = True

    def toggle_pause(self) -> None:
        self._mutex.lock()
        self._paused = not self._paused
        self._mutex.unlock()

    def run(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="ignition_upscale_"))
        frames_dir = temp_dir / "frames"
        upscaled_dir = temp_dir / "upscaled"
        frames_dir.mkdir(parents=True, exist_ok=True)
        upscaled_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.log.emit("Extracting frames with FFmpeg...")
            self._extract_frames(frames_dir)

            frame_paths = sorted(frames_dir.glob("*.png"))
            if not frame_paths:
                raise RuntimeError("No frames extracted. Check video source/ffmpeg installation.")

            self.log.emit("Loading Real-ESRGAN model...")
            upsampler = self._build_upsampler()

            start = time.time()
            for idx, frame_path in enumerate(frame_paths, start=1):
                while self._paused and not self._cancelled:
                    time.sleep(0.2)

                if self._cancelled:
                    self.log.emit("Processing cancelled by user.")
                    return

                img = cv2.imread(str(frame_path), cv2.IMREAD_COLOR)
                if img is None:
                    raise RuntimeError(f"Unable to read frame: {frame_path.name}")

                enhanced = self._upscale_frame(img, upsampler)
                output_frame = upscaled_dir / frame_path.name
                cv2.imwrite(str(output_frame), enhanced)

                elapsed = time.time() - start
                rate = idx / elapsed if elapsed > 0 else 0.1
                remaining = (len(frame_paths) - idx) / max(rate, 0.1)
                status = ProcessingStatus(
                    current_frame=idx,
                    total_frames=len(frame_paths),
                    eta_seconds=remaining,
                    usage_percent=self._resource_usage(),
                    message=f"Upscaled frame {idx}/{len(frame_paths)}",
                )
                self.progress.emit(status)

            output_path = self._render_video(upscaled_dir)
            self.finished.emit(output_path)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_frames(self, frames_dir: Path) -> None:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(self.video_info.path),
            str(frames_dir / "%08d.png"),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    def _render_video(self, upscaled_dir: Path) -> Path:
        export_dir = Path(self.config.export.output_folder)
        export_dir.mkdir(parents=True, exist_ok=True)

        stem = self.config.export.rename_file.strip() or f"{self.video_info.path.stem}_upscaled"
        ext = self.config.export.file_format.lower()
        output_path = export_dir / f"{stem}.{ext}"
        if output_path.exists() and not self.config.export.auto_overwrite:
            output_path = export_dir / f"{stem}_{int(time.time())}.{ext}"

        codec_map = {"H264": "libx264", "H265": "libx265", "AV1": "libaom-av1"}
        codec = codec_map[self.config.video.codec]

        fps = self.video_info.fps if self.config.video.frame_rate_mode == "keep" else self.config.video.custom_fps
        bitrate = self._bitrate_value()

        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(upscaled_dir / "%08d.png"),
            "-c:v",
            codec,
            "-b:v",
            bitrate,
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
        self.log.emit("Rendering upscaled video...")
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def _bitrate_value(self) -> str:
        mapping = {"Low": "4M", "Medium": "8M", "High": "16M", "Custom": f"{self.config.video.custom_bitrate}k"}
        return mapping[self.config.video.bitrate]

    def _resource_usage(self) -> float:
        if torch.cuda.is_available() and self.config.performance.processing_mode == "GPU":
            return float(torch.cuda.utilization(0)) if hasattr(torch.cuda, "utilization") else 0.0
        return float(psutil.cpu_percent(interval=0.0))

    def _build_upsampler(self):
        # Lazy imports keep startup fast and allow CPU-only execution.
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        model_name = self.config.ai.model_name
        scale = 4 if self.config.video.upscale_factor == "4x" else 2
        if self.config.video.upscale_factor == "custom":
            scale = int(max(2, round(self.config.video.custom_scale)))

        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale)

        weights_dir = Path("models/weights")
        weights_dir.mkdir(parents=True, exist_ok=True)
        selected = "realesr-animevideov3.pth" if "Anime" in model_name else "RealESRGAN_x4plus.pth"
        model_file = ensure_model_weight(selected, weights_dir)

        hardware = detect_hardware()
        half = hardware.cuda_available and self.config.performance.processing_mode == "GPU"
        return RealESRGANer(
            scale=scale,
            model_path=str(model_file),
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=half,
            gpu_id=0 if half else None,
        )

    def _upscale_frame(self, img: np.ndarray, upsampler) -> np.ndarray:
        output, _ = upsampler.enhance(img, outscale=self._output_scale())
        if self.config.ai.sharpening > 0:
            amount = self.config.ai.sharpening / 100.0
            kernel = np.array([[0, -1, 0], [-1, 5 + amount, -1], [0, -1, 0]])
            output = cv2.filter2D(output, -1, kernel)
        return output

    def _output_scale(self) -> float:
        if self.config.video.upscale_factor == "2x":
            return 2.0
        if self.config.video.upscale_factor == "4x":
            return 4.0
        return max(1.0, self.config.video.custom_scale)


class ProcessingController:
    def __init__(self, config: AppConfig, video_info: VideoInfo):
        self.thread = QThread()
        self.worker = ProcessingWorker(config, video_info)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

    def start(self):
        self.thread.start()

    def stop(self):
        self.worker.cancel()

    def pause_resume(self):
        self.worker.toggle_pause()
