"""Run one AquaDetector inference from an image and publish its event.

Usage:
    python -m Embedded.analyze_image path\\to\\photo.jpg
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from Embedded.AI.yolo_detector import YoloDetector
from Embedded.API.api_client import ApiClient
from Embedded.Config.config import load_settings
from Embedded.Events.event_manager import EventManager, LocalEventStorage


def read_image(path: Path):
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python is required. Install Embedded/requirements.txt.") from exc

    frame = cv2.imread(str(path))
    if frame is None:
        raise ValueError(f"Could not read an image from: {path}")
    return frame


def publish_pending_events(storage: LocalEventStorage, api: ApiClient) -> bool:
    """Publish the durable queue in order, retaining events after a failure."""
    for path, event in storage.pending_events():
        if not api.send_event(event):
            return False
        storage.mark_synced(path)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect recyclable objects in one image and publish an AquaDetector event."
    )
    parser.add_argument("image", type=Path, help="Path to a JPEG, PNG, or other OpenCV-readable image")
    parser.add_argument(
        "--no-send",
        action="store_true",
        help="Create and display the JSON event, but keep it in the local queue without publishing it",
    )
    args = parser.parse_args()

    image_path = args.image.expanduser().resolve()
    if not image_path.is_file():
        parser.error(f"Image file was not found: {image_path}")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    frame = read_image(image_path)
    detector = YoloDetector(settings.model_path, settings.confidence_threshold)
    detections = detector.detect(frame)

    events = EventManager(settings.station_id, settings.latitude, settings.longitude)
    event = events.create_event(detections)
    storage = LocalEventStorage(settings.local_storage_path)
    saved_path = storage.save(event)

    print(json.dumps(event, ensure_ascii=False, indent=2))
    print(f"\nEvento salvo em: {saved_path}")

    if args.no_send:
        print("Envio não solicitado; o evento ficou na fila local.")
        return

    api = ApiClient(settings.backend_url, settings.request_timeout_seconds)
    if publish_pending_events(storage, api):
        print(f"Evento enviado ao backend: {settings.backend_url}")
    else:
        print("O backend não respondeu; o evento permanece salvo na fila local.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
