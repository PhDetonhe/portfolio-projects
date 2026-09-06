"""Entrypoint that only coordinates the embedded AquaDetector modules."""

from __future__ import annotations

import logging

from Embedded.AI.yolo_detector import YoloDetector
from Embedded.API.api_client import ApiClient
from Embedded.Camera.camera_manager import CameraManager
from Embedded.Config.config import load_settings
from Embedded.Detection.detection_scheduler import DetectionScheduler
from Embedded.Events.event_manager import EventManager, LocalEventStorage


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> None:
    configure_logging()
    settings = load_settings()
    detector = YoloDetector(settings.model_path, settings.confidence_threshold)
    events = EventManager(settings.station_id, settings.latitude, settings.longitude)
    storage = LocalEventStorage(settings.local_storage_path)
    api = ApiClient(settings.backend_url, settings.request_timeout_seconds)

    def synchronize_pending_events() -> None:
        for path, event in storage.pending_events():
            if not api.send_event(event):
                break  # Network is likely still unavailable; avoid unnecessary requests.
            storage.mark_synced(path)

    def execute_detection() -> None:
        # The camera is opened for this one capture and promptly released.
        with CameraManager(settings.camera_index, settings.camera_width, settings.camera_height) as camera:
            frame = camera.capture_frame()
        event = events.create_event(detector.detect(frame))
        storage.save(event)
        synchronize_pending_events()

    synchronize_pending_events()
    DetectionScheduler(settings.detection_interval_seconds, run_immediately=True).run_forever(execute_detection)


if __name__ == "__main__":
    main()
