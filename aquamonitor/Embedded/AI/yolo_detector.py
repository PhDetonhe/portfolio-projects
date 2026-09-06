"""YOLO inference adapter kept independent from camera hardware."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SUPPORTED_CLASSES = ("bottle", "can", "carton", "paper", "plastic")


@dataclass(frozen=True)
class Detection:
    """One object found in a frame, in pixel coordinates (x1, y1, x2, y2)."""

    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    class_id: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class YoloDetector:
    """Lazy wrapper around Ultralytics YOLO.

    Loading happens only on the first detection. This lets startup and camera
    diagnostics run without allocating model memory, while the loaded model
    remains available for later scheduled executions.
    """

    def __init__(self, model_path: str | Path, confidence_threshold: float) -> None:
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is None:
            if not self.model_path.is_file():
                raise FileNotFoundError(f"YOLO model was not found: {self.model_path}")
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError(
                    "Ultralytics is required for inference. Install Embedded/requirements.txt."
                ) from exc
            self._model = YOLO(str(self.model_path))
        return self._model

    def detect(self, frame: Any) -> list[Detection]:
        """Run inference for one OpenCV/Numpy frame."""
        model = self._load_model()
        results = model.predict(frame, conf=self.confidence_threshold, verbose=False)
        detections: list[Detection] = []

        for result in results:
            names = result.names
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                label = str(names[class_id])
                if label not in SUPPORTED_CLASSES:
                    continue
                confidence = float(box.conf[0].item())
                x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
                detections.append(Detection(label, confidence, (x1, y1, x2, y2), class_id))
        return detections
