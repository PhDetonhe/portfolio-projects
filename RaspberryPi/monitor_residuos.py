"""Execute este arquivo para monitorar e contabilizar resíduos na webcam."""

import json
from pathlib import Path
from typing import Dict

import cv2

from line_tracker import LineTracker
from webcam_config import WebcamConfig
from yolo_detector import EXPECTED_CLASSES, Detection, YoloDetector


COUNTS_FILE = Path("contagem_residuos.json")
LINE_Y_RATIO = 0.55  # Linha de contagem: 55% da altura da imagem.
TRACKING_DIRECTION = "both"  # Use "down" se o fluxo só passa de cima para baixo.


def load_counts(path: Path) -> Dict[str, int]:
    counts = {class_name: 0 for class_name in EXPECTED_CLASSES}
    if path.is_file():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            for class_name in counts:
                if isinstance(saved.get(class_name), int):
                    counts[class_name] = saved[class_name]
        except (json.JSONDecodeError, OSError):
            print("Aviso: JSON anterior inválido; iniciando uma nova contagem.")
    return counts


def save_counts(path: Path, counts: Dict[str, int]) -> None:
    """Substitui o arquivo de forma atômica para evitar JSON parcialmente escrito."""
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def draw_overlay(frame, detections, tracker: LineTracker, counts: Dict[str, int]) -> None:
    height, width = frame.shape[:2]
    cv2.line(frame, (0, tracker.line_y), (width, tracker.line_y), (0, 255, 255), 2)
    cv2.putText(frame, "LINHA DE CONTAGEM", (12, max(25, tracker.line_y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
    for detection in detections:
        x1, y1, x2, y2 = detection.bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 0), 2)
        label = f"{detection.class_name} {detection.confidence:.0%}"
        cv2.putText(frame, label, (x1, max(22, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 0), 2)
    y = 30
    for class_name in EXPECTED_CLASSES:
        cv2.putText(frame, f"{class_name}: {counts[class_name]}", (12, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y += 28


def main() -> None:
    config = WebcamConfig()  # Edite largura, altura, fps e device_index em webcam_config.py.
    camera = config.open_camera()
    detector = YoloDetector()
    counts = load_counts(COUNTS_FILE)
    line_y = int(config.height * LINE_Y_RATIO)
    tracker = LineTracker(line_y=line_y, direction=TRACKING_DIRECTION)

    print("Monitor iniciado. Pressione Q ou ESC para encerrar.")
    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Não foi possível ler um frame da webcam.")
                break

            detections = detector.detect(frame)
            for crossing in tracker.update(detections):
                counts[crossing.class_name] += 1
                save_counts(COUNTS_FILE, counts)
                print(f"Contabilizado: {crossing.class_name} (track #{crossing.track_id})")

            draw_overlay(frame, detections, tracker, counts)
            cv2.imshow("Monitoramento de residuos", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        save_counts(COUNTS_FILE, counts)
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
