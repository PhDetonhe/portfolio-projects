"""
yolo_detector.py

Responsabilidade única: executar a inferência do YOLO sobre um frame
e retornar as detecções em um formato simples e padronizado.

Não lida com câmera, tracking, eventos ou backend.
"""

import os

from ultralytics import YOLO

from config import config


class YOLODetector:
    """Encapsula o carregamento do modelo YOLO e a execução da inferência."""

    def __init__(
        self,
        model_path: str = config.MODEL_PATH,
        image_size: int = config.YOLO_IMAGE_SIZE,
        confidence_threshold: float = config.CONFIDENCE_THRESHOLD,
    ):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Modelo YOLO não encontrado em '{model_path}'. "
                "Treine o modelo ou copie o arquivo 'best.pt' para esse caminho "
                "antes de executar a detecção."
            )

        self.model_path = model_path
        self.image_size = image_size
        self.confidence_threshold = confidence_threshold

        self._model = YOLO(self.model_path)

    def detect(self, frame) -> list[dict]:
        """
        Executa a inferência do YOLO em um único frame.

        Parâmetros:
            frame (numpy.ndarray): imagem capturada pela câmera.

        Retorna:
            list[dict]: lista de detecções, cada uma no formato:
                {
                    "class_id": int,
                    "class_name": str,
                    "confidence": float,
                    "bbox": [x1, y1, x2, y2]
                }
        """
        results = self._model.predict(
            source=frame,
            imgsz=self.image_size,
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections = []

        if not results:
            return detections

        result = results[0]

        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]

            class_name = config.CLASS_NAMES.get(class_id, str(class_id))

            detections.append(
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                }
            )

        return detections
