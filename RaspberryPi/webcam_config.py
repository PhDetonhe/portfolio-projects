"""Configurações centralizadas para uma webcam USB genérica."""

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2


@dataclass(frozen=True)
class WebcamConfig:
    """Altere estes valores para adequar a captura à câmera instalada."""

    device_index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    # No Windows, CAP_DSHOW costuma diminuir o tempo de abertura de webcams USB.
    backend: Optional[int] = cv2.CAP_DSHOW

    @property
    def resolution(self) -> Tuple[int, int]:
        return self.width, self.height

    def open_camera(self) -> cv2.VideoCapture:
        """Abre a câmera e pede ao driver a resolução e FPS configurados."""
        if self.backend is None:
            camera = cv2.VideoCapture(self.device_index)
        else:
            camera = cv2.VideoCapture(self.device_index, self.backend)

        if not camera.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir a webcam no índice {self.device_index}. "
                "Verifique a conexão ou altere device_index em webcam_config.py."
            )

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        camera.set(cv2.CAP_PROP_FPS, self.fps)
        return camera
