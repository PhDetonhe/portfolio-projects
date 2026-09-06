"""Centralized, environment-overridable embedded configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _optional_float(name: str) -> float | None:
    value = os.getenv(name)
    return float(value) if value else None


@dataclass(frozen=True)
class Settings:
    camera_index: int
    model_path: Path
    backend_url: str
    station_id: int
    detection_interval_seconds: int
    confidence_threshold: float
    local_storage_path: Path
    request_timeout_seconds: float
    latitude: float | None
    longitude: float | None
    camera_width: int | None
    camera_height: int | None


def load_settings() -> Settings:
    """Read values once at startup; environment variables override safe defaults."""
    return Settings(
        camera_index=int(os.getenv("AQUADETECTOR_CAMERA_INDEX", "0")),
        model_path=Path(os.getenv("AQUADETECTOR_MODEL_PATH", str(PROJECT_ROOT / "Embedded" / "models" / "yolo26n.pt"))),
        backend_url=os.getenv("AQUADETECTOR_BACKEND_URL", "http://127.0.0.1:8000/api/detections"),
        station_id=int(os.getenv("AQUADETECTOR_STATION_ID", "1")),
        detection_interval_seconds=int(os.getenv("AQUADETECTOR_DETECTION_INTERVAL", "3600")),
        confidence_threshold=float(os.getenv("AQUADETECTOR_CONFIDENCE_THRESHOLD", "0.40")),
        local_storage_path=Path(os.getenv("AQUADETECTOR_LOCAL_STORAGE_PATH", str(PROJECT_ROOT / "Embedded" / "data" / "pending_events"))),
        request_timeout_seconds=float(os.getenv("AQUADETECTOR_REQUEST_TIMEOUT", "10")),
        latitude=_optional_float("AQUADETECTOR_LATITUDE"),
        longitude=_optional_float("AQUADETECTOR_LONGITUDE"),
        camera_width=int(os.environ["AQUADETECTOR_CAMERA_WIDTH"]) if os.getenv("AQUADETECTOR_CAMERA_WIDTH") else None,
        camera_height=int(os.environ["AQUADETECTOR_CAMERA_HEIGHT"]) if os.getenv("AQUADETECTOR_CAMERA_HEIGHT") else None,
    )
