# AquaDetector-core

Fundação da pipeline de visão computacional do **AquaDetector**: detecção de
resíduos flutuantes na superfície da água usando YOLO.

Esta etapa contém **somente** a base da pipeline (câmera → YOLO → tracking →
eventos). Backend, banco de dados, comunicação com ESP32, GPS, dashboard e
integração completa serão implementados em etapas futuras.

## Estrutura

```
AquaDetector-core/
├── config/
│   └── config.py
├── camera/
│   └── camera_manager.py
├── detection/
│   └── yolo_detector.py
├── tracking/
│   └── object_tracker.py
└── events/
    └── event_manager.py
```

## Pré-requisitos


pip install ultralytics opencv-python


## Onde colocar o modelo

O `YOLODetector` espera encontrar o modelo treinado em:

```
models/best.pt
```

(caminho configurável em `config/config.py`, variável `MODEL_PATH`).

Enquanto o modelo específico do AquaDetector ainda não está treinado, você
pode testar a pipeline com um modelo genérico do YOLO (ex.: `yolov8n.pt`,
baixado automaticamente pela Ultralytics). Os nomes de classe exibidos serão
diferentes dos nomes definidos em `config.CLASS_NAMES`, mas isso serve apenas
para validar que o encadeamento dos módulos está funcionando.

## Teste rápido com uma única imagem

Este teste não usa a câmera — serve só para confirmar que o `YOLODetector`
consegue carregar um modelo e gerar detecções a partir de uma imagem
qualquer.

1. Coloque uma imagem de teste na raiz do projeto, por exemplo `teste.jpg`.

2. (Opcional, se ainda não tiver `models/best.pt`) Baixe um modelo genérico
   só para validar o fluxo:

   ```bash
   python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
   mkdir -p models
   cp yolov8n.pt models/best.pt
   ```

3. Crie um script temporário `teste_deteccao.py` na raiz do projeto
   (fora dos 5 módulos, só para teste manual):

   ```python
   import cv2

   from detection.yolo_detector import YOLODetector

   # Carrega a imagem de teste como se fosse um frame de câmera
   frame = cv2.imread("teste.jpg")

   if frame is None:
       raise FileNotFoundError("Não foi possível abrir 'teste.jpg'.")

   detector = YOLODetector()
   detections = detector.detect(frame)

   print(f"{len(detections)} detecção(ões) encontrada(s):\n")
   for det in detections:
       print(det)
   ```

4. Execute:

   ```bash
   python teste_deteccao.py
   ```

5. Saída esperada (exemplo):

   ```
   2 detecção(ões) encontrada(s):

   {'class_id': 0, 'class_name': 'bottle', 'confidence': 0.91, 'bbox': [120.0, 45.0, 260.0, 310.0]}
   {'class_id': 4, 'class_name': 'plastic', 'confidence': 0.67, 'bbox': [400.0, 200.0, 480.0, 260.0]}
   ```

Se o arquivo do modelo não existir, o `YOLODetector` levanta um
`FileNotFoundError` claro, em vez de falhar silenciosamente.

## Teste do fluxo completo (câmera → YOLO → tracking → eventos)

Também fora dos 5 módulos (script manual só para validação), um teste
simples do encadeamento completo:

```python
from camera.camera_manager import CameraManager
from detection.yolo_detector import YOLODetector
from tracking.object_tracker import ObjectTracker
from events.event_manager import EventManager

camera = CameraManager()
detector = YOLODetector()
tracker = ObjectTracker()
events = EventManager()

camera.start()

try:
    while True:
        frame = camera.read()
        if frame is None:
            break

        if not camera.should_process_frame():
            continue

        detections = detector.detect(frame)
        tracker.update(detections)

        for new_object in tracker.get_new_objects():
            events.register_detection(new_object)

        print(events.get_summary())

        if events.should_finalize():
            print("Janela de eventos encerrada:", events.get_summary())
            events.reset()
finally:
    camera.release()
```

Interrompa com `Ctrl+C` para encerrar o teste manualmente.

## Próximos passos (fora do escopo desta etapa)

1. Integração formal dos módulos em um `main.py`
2. Teste com webcam em tempo real
3. Treinamento do modelo YOLO com o dataset de resíduos
4. Tracking real (via `model.track()` da Ultralytics)
5. Geração de eventos completa
6. Exportação em JSON
7. Backend
