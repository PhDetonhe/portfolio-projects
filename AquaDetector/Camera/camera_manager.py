"""
camera_manager.py

Responsabilidade única: gerenciar o acesso à câmera.

Não faz inferência (YOLO), não faz tracking e não gera eventos.
Apenas abre a câmera, entrega frames e controla a taxa de
processamento (para que nem todo frame capturado seja enviado
ao YOLO).
"""

import time

import cv2

from config import config


class CameraManager:
    """Encapsula a captura de vídeo de uma câmera local (webcam/USB/CSI)."""

    def __init__(
        self,
        camera_index: int = config.CAMERA_INDEX,
        width: int = config.CAMERA_WIDTH,
        height: int = config.CAMERA_HEIGHT,
        detection_fps: float = config.DETECTION_FPS,
    ):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.detection_fps = detection_fps

        # Intervalo mínimo (em segundos) entre dois frames processados
        self._min_interval = 1.0 / self.detection_fps if self.detection_fps > 0 else 0
        self._last_processed_time = 0.0

        self._cap = None

    def start(self) -> None:
        """Abre a câmera e configura a resolução desejada."""
        self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir a câmera de índice {self.camera_index}."
            )

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self):
        """
        Captura um único frame da câmera.

        Retorna:
            frame (numpy.ndarray) em caso de sucesso, ou None se a
            captura falhar.
        """
        if self._cap is None:
            raise RuntimeError("A câmera não foi iniciada. Chame start() antes de read().")

        success, frame = self._cap.read()
        if not success:
            return None

        return frame

    def should_process_frame(self) -> bool:
        """
        Decide se o frame atual deve ser enviado para processamento
        (YOLO), com base no DETECTION_FPS configurado.

        Retorna True aproximadamente 1x a cada (1 / detection_fps)
        segundos; caso contrário, retorna False, permitindo que o
        frame seja simplesmente descartado.
        """
        now = time.time()

        if now - self._last_processed_time >= self._min_interval:
            self._last_processed_time = now
            return True

        return False

    def release(self) -> None:
        """Libera o recurso da câmera."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
