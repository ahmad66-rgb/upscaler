"""System capability and app update helpers."""
from __future__ import annotations

from dataclasses import dataclass

import requests
import torch


@dataclass
class HardwareInfo:
    cuda_available: bool
    device_name: str


def detect_hardware() -> HardwareInfo:
    if torch.cuda.is_available():
        return HardwareInfo(True, torch.cuda.get_device_name(0))
    return HardwareInfo(False, "CPU")


def check_for_updates(current_version: str, endpoint: str) -> str | None:
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
        latest = response.json().get("version")
        if latest and latest != current_version:
            return latest
    except Exception:
        return None
    return None
