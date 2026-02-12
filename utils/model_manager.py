"""Model weight management and download."""
from __future__ import annotations

from pathlib import Path

from basicsr.utils.download_util import load_file_from_url

MODEL_URLS = {
    "RealESRGAN_x4plus.pth": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    "realesr-animevideov3.pth": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth",
}


def ensure_model_weight(filename: str, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename
    if target_path.exists():
        return target_path

    url = MODEL_URLS.get(filename)
    if not url:
        raise RuntimeError(f"No download URL configured for {filename}.")

    load_file_from_url(url=url, model_dir=str(target_dir), progress=True, file_name=filename)
    if not target_path.exists():
        raise RuntimeError(f"Model download failed for {filename}.")
    return target_path
