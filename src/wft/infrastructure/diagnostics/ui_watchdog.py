import faulthandler
import logging
import sys
import threading
import time
import traceback
from typing import Optional

from PySide6.QtCore import QObject, QTimer

logger = logging.getLogger(__name__)
faulthandler.enable()


class UIWatchdog(QObject):
    def __init__(self, interval_ms: int = 1000, threshold_ms: int = 1500) -> None:
        super().__init__()
        self._threshold = threshold_ms / 1000.0
        self._last_tick = time.monotonic()
        self._page: Optional[str] = None
        self._operation: Optional[str] = None
        self._active_workers: list[str] = []
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._check)
        self._enabled = False

    def start(self) -> None:
        self._last_tick = time.monotonic()
        self._timer.start()
        self._enabled = True

    def stop(self) -> None:
        self._timer.stop()
        self._enabled = False

    def tick(self) -> None:
        self._last_tick = time.monotonic()

    def set_page(self, page: str) -> None:
        self._page = page

    def set_operation(self, op: str) -> None:
        self._operation = op
        self.tick()

    def set_active_workers(self, names: list[str]) -> None:
        self._active_workers = names

    def _check(self) -> None:
        if not self._enabled:
            return
        elapsed = time.monotonic() - self._last_tick
        if elapsed > self._threshold:
            frames = "".join(
                traceback.format_stack(threading.current_thread())
            )
            logger.warning(
                "UI watchdog: event loop frozen for %.1fs "
                "page=%s operation=%s workers=%s\n%s",
                elapsed,
                self._page,
                self._operation,
                self._active_workers,
                frames,
            )


def dump_thread_stacks(logger: logging.Logger = logger) -> None:
    for th in threading.enumerate():
        stack = "".join(traceback.format_stack(sys._current_frames().get(th.ident, [])))
        logger.info("Thread %s (daemon=%s):\n%s", th.name, th.daemon, stack)
