"""HTTP JSON client; no embedded component accesses MongoDB directly."""

from __future__ import annotations

import logging
from typing import Any

import requests


LOGGER = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, backend_url: str, timeout_seconds: float = 10) -> None:
        self.backend_url = backend_url
        self.timeout_seconds = timeout_seconds

    def send_event(self, event: dict[str, Any]) -> bool:
        try:
            response = requests.post(self.backend_url, json=event, timeout=self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning("Could not send event to backend: %s", exc)
            return False
        return True
