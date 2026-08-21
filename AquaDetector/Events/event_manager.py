"""
event_manager.py

Responsabilidade única: agregar as detecções (objetos novos) dentro
de uma janela de tempo configurável e disponibilizar um resumo.

Não salva em arquivo, não envia para backend — apenas monta e retorna
a estrutura de dados em memória.
"""

from datetime import datetime, timedelta

from config import config


class EventManager:
    """Agrega contagens de resíduos detectados durante uma janela de tempo."""

    def __init__(self, interval_minutes: int = config.EVENT_INTERVAL_MINUTES):
        self.interval_minutes = interval_minutes
        self.reset()

    def reset(self) -> None:
        """Reinicia a janela de eventos (zera contagens e reinicia o horário inicial)."""
        self._start_time = datetime.now()
        self._last_detection_time = None

        self._residues = {name: 0 for name in config.CLASS_NAMES.values()}
        self._total = 0

    def register_detection(self, detection: dict) -> None:
        """
        Registra um novo objeto detectado dentro da janela atual.

        Parâmetros:
            detection (dict): objeto com pelo menos a chave "class_name".
        """
        class_name = detection.get("class_name")

        if class_name not in self._residues:
            # Classe desconhecida: registra mesmo assim, para não perder a contagem.
            self._residues[class_name] = 0

        self._residues[class_name] += 1
        self._total += 1
        self._last_detection_time = datetime.now()

    def should_finalize(self) -> bool:
        """Indica se a janela de tempo atual já se encerrou."""
        elapsed = datetime.now() - self._start_time
        return elapsed >= timedelta(minutes=self.interval_minutes)

    def get_summary(self) -> dict:
        """
        Retorna um resumo da janela atual (ou já encerrada), no formato:

            {
                "start": "...",
                "end": "...",
                "residues": {"bottle": 2, "can": 1, ...},
                "total": 7
            }
        """
        end_time = self._last_detection_time or datetime.now()

        return {
            "start": self._start_time.isoformat(),
            "end": end_time.isoformat(),
            "residues": dict(self._residues),
            "total": self._total,
        }
