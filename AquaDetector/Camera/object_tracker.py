"""
object_tracker.py

Responsabilidade única: manter IDs persistentes entre frames para que
o mesmo objeto físico não seja contado múltiplas vezes.

Não lida com câmera, inferência do YOLO ou geração de eventos —
apenas recebe detecções já prontas e informa quais objetos são novos.
"""


class ObjectTracker:
    """
    Tracker simples baseado em IDs persistentes.

    Esta primeira versão espera que cada detecção já venha com um
    'track_id' (por exemplo, gerado pelo modo de tracking nativo da
    Ultralytics — model.track(...) — que usa ByteTrack/BoT-SORT).
    Se não houver track_id disponível, o tracker atribui um ID novo
    a cada detecção, o que equivale a "sem tracking real" até que a
    integração com model.track() seja feita na próxima etapa.
    """

    def __init__(self):
        self._known_ids: set[int] = set()
        self._next_fallback_id = 0
        self._new_objects: list[dict] = []

    def update(self, detections: list[dict]) -> None:
        """
        Atualiza o estado do tracker com as detecções do frame atual.

        Parâmetros:
            detections (list[dict]): detecções vindas do YOLODetector,
                opcionalmente contendo a chave "track_id".
        """
        self._new_objects = []

        for detection in detections:
            track_id = detection.get("track_id")

            if track_id is None:
                track_id = self._next_fallback_id
                self._next_fallback_id += 1

            if track_id not in self._known_ids:
                self._known_ids.add(track_id)

                tracked_object = dict(detection)
                tracked_object["track_id"] = track_id
                self._new_objects.append(tracked_object)

    def get_new_objects(self) -> list[dict]:
        """
        Retorna os objetos identificados como novos na última chamada
        a update().
        """
        return self._new_objects
