"""Low-resource periodic job scheduler."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable


LOGGER = logging.getLogger(__name__)


class DetectionScheduler:
    def __init__(self, interval_seconds: int, run_immediately: bool = True) -> None:
        if interval_seconds <= 0:
            raise ValueError("Detection interval must be greater than zero")
        self.interval_seconds = interval_seconds
        self.run_immediately = run_immediately

    def run_forever(self, task: Callable[[], None]) -> None:
        """Run task periodically, sleeping between jobs without busy waiting."""
        next_run = time.monotonic() if self.run_immediately else time.monotonic() + self.interval_seconds
        while True:
            delay = next_run - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            try:
                task()
            except Exception:
                LOGGER.exception("Scheduled detection failed; retrying at next interval")
            next_run += self.interval_seconds
            if next_run < time.monotonic():
                next_run = time.monotonic() + self.interval_seconds
