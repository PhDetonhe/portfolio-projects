"""
config.py

Centraliza todas as configurações da pipeline de visão computacional
do AquaDetector. Nenhum outro módulo deve conter valores fixos
(números mágicos) — tudo deve ser referenciado a partir daqui.
"""

# ------------------------------------------------------------------
# Modelo YOLO
# ------------------------------------------------------------------
MODEL_PATH = "models/best.pt"

# Tamanho da imagem usada na inferência do YOLO (lado do quadrado, em px)
YOLO_IMAGE_SIZE = 640

# Confiança mínima para considerar uma detecção válida
CONFIDENCE_THRESHOLD = 0.5

# ------------------------------------------------------------------
# Câmera
# ------------------------------------------------------------------
CAMERA_INDEX = 0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# Quantos frames por segundo devem ser efetivamente processados pelo YOLO.
# A câmera pode capturar mais rápido que isso; o excedente é descartado.
DETECTION_FPS = 1

# ------------------------------------------------------------------
# Classes do dataset (resíduos flutuantes)
# ------------------------------------------------------------------
CLASS_NAMES = {
    0: "bottle",
    1: "can",
    2: "carton",
    3: "paper",
    4: "plastic",
}

# ------------------------------------------------------------------
# Eventos
# ------------------------------------------------------------------
# Duração da janela de agregação de detecções, em minutos.
EVENT_INTERVAL_MINUTES = 60
