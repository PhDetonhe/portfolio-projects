"""Build event payloads and safely persist unsent events locally."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from Embedded.AI.yolo_detector import Detection, SUPPORTED_CLASSES


class EventManager:
    def __init__(self, station_id: int, latitude: float | None = None, longitude: float | None = None) -> None:
        self.station_id = station_id
        self.latitude = latitude
        self.longitude = longitude

    def create_event(self, detections: Iterable[Detection], water_level: float | None = None) -> dict[str, Any]:
        objects = list(detections)
        residues = {label: 0 for label in SUPPORTED_CLASSES}
        for detection in objects:
            if detection.label in residues:
                residues[detection.label] += 1
        average_confidence = sum(item.confidence for item in objects) / len(objects) if objects else 0.0
        return {
            "event_id": str(uuid.uuid4()),
            "horario": datetime.now(timezone.utc).isoformat(),
            "station_id": self.station_id,
            "estacao": f"AquaDetector-{self.station_id:02d}",
            "latitude": self.latitude,
            "longitude": self.longitude,
            "residuos": residues,
            "quantidade_total": sum(residues.values()),
            "confianca_media": round(average_confidence, 4),
            "nivel_agua": water_level,
            "detections": [item.to_dict() for item in objects],
        }


class LocalEventStorage:
    """One JSON file per event; failed sends remain available after reboot."""

    def __init__(self, storage_path: str | Path) -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save(self, event: dict[str, Any]) -> Path:
        event_id = event.get("event_id") or str(uuid.uuid4())
        path = self.storage_path / f"{event_id}.json"
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(event, file, ensure_ascii=False, separators=(",", ":"))
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
        return path

    def pending_events(self) -> Iterable[tuple[Path, dict[str, Any]]]:
        for path in sorted(self.storage_path.glob("*.json")):
            try:
                with path.open(encoding="utf-8") as file:
                    yield path, json.load(file)
            except (OSError, json.JSONDecodeError):
                # Preserve malformed data for inspection instead of silently losing it.
                continue

    @staticmethod
    def mark_synced(path: Path) -> None:
        path.unlink(missing_ok=True)
