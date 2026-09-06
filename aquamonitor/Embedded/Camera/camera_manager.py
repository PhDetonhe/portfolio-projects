"""OpenCV webcam lifecycle management."""

from __future__ import annotations

from typing import Any


class CameraError(RuntimeError):
    """Raised when a camera cannot be opened or provide a frame."""


class CameraManager:
    def __init__(self, camera_index: int, width: int | None = None, height: int | None = None) -> None:
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._capture: Any | None = None

    def open(self) -> None:
        if self._capture is not None:
            return
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for camera capture.") from exc
        capture = cv2.VideoCapture(self.camera_index)
        if not capture.isOpened():
            capture.release()
            raise CameraError(f"Camera {self.camera_index} is unavailable")
        if self.width:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if self.height:
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._capture = capture

    def capture_frame(self) -> Any:
        self.open()
        assert self._capture is not None
        ok, frame = self._capture.read()
        if not ok or frame is None:
            raise CameraError(f"Could not capture a frame from camera {self.camera_index}")
        return frame

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def __enter__(self) -> "CameraManager":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
