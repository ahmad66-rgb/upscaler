"""Video probing and thumbnail generation helpers."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
from PyQt6.QtGui import QImage, QPixmap

from models.config import VideoInfo


def probe_video(path: Path) -> VideoInfo:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,nb_frames",
        "-show_entries",
        "format=duration,size",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)

    stream = payload["streams"][0]
    fmt = payload["format"]
    fps_parts = stream["r_frame_rate"].split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(stream["r_frame_rate"])
    duration = float(fmt.get("duration", 0.0))
    total_frames = int(stream.get("nb_frames") or int(duration * fps))

    return VideoInfo(
        path=path,
        width=int(stream["width"]),
        height=int(stream["height"]),
        duration_seconds=duration,
        fps=fps,
        file_size_bytes=int(fmt.get("size", path.stat().st_size)),
        total_frames=total_frames,
    )


def thumbnail_for_video(path: Path) -> QPixmap:
    capture = cv2.VideoCapture(str(path))
    ok, frame = capture.read()
    capture.release()
    if not ok:
        return QPixmap()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, c = frame.shape
    qimg = QImage(frame.data, w, h, c * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)
