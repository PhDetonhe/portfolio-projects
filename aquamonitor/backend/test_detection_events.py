"""Unit tests for the public detection event payload contract."""

import unittest

from pydantic import ValidationError

from backend.app import DetectionPayload


class DetectionPayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = {
            "event_id": "event-1",
            "station_id": 1,
            "detection_type": "bottle",
            "confidence": 0.92,
            "track_id": 7,
            "detected_at": "2026-09-17T12:00:00Z",
        }

    def test_accepts_timezone_aware_raspberry_timestamp(self) -> None:
        event = DetectionPayload.model_validate(self.payload)
        self.assertEqual(event.station_id, 1)
        self.assertEqual(event.detected_at.utcoffset().total_seconds(), 0)

    def test_accepts_supported_directions(self) -> None:
        for direction in ("positive", "negative", None):
            event = DetectionPayload.model_validate({**self.payload, "direction": direction})
            self.assertEqual(event.direction, direction)

    def test_rejects_timestamp_without_timezone(self) -> None:
        with self.assertRaises(ValidationError):
            DetectionPayload.model_validate({**self.payload, "detected_at": "2026-09-17T12:00:00"})

    def test_rejects_unsupported_direction(self) -> None:
        with self.assertRaises(ValidationError):
            DetectionPayload.model_validate({**self.payload, "direction": "sideways"})


if __name__ == "__main__":
    unittest.main()
