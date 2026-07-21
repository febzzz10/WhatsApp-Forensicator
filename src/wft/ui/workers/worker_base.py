from typing import Optional, Callable, Any

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool


class CancellationToken:
    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled


class WorkerSignals(QObject):
    started = Signal()
    progress = Signal(str, int, int)
    finished = Signal(object)
    error = Signal(str)
    cancelled = Signal()


class AsyncWorker(QRunnable):
    def __init__(
        self,
        fn: Callable[..., Any],
        token: Optional[CancellationToken] = None,
        on_progress: Optional[Callable] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._fn = fn
        self._token = token or CancellationToken()
        self._on_progress = on_progress
        self._kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:
        if self._token.cancelled:
            self.signals.cancelled.emit()
            self.signals.finished.emit(None)
            return
        self.signals.started.emit()
        try:
            if self._on_progress:

                def progress_callback(msg: str, current: int, total: int) -> None:
                    self.signals.progress.emit(msg, current, total)

                result = self._fn(
                    self._token, progress_callback, **self._kwargs
                )
            else:
                result = self._fn(self._token, **self._kwargs)
            if self._token.cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(result)
        except Exception as exc:
            if self._token.cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.error.emit(str(exc))

    def cancel(self) -> None:
        self._token.cancel()


class BackgroundWorker(QRunnable):
    def __init__(
        self,
        fn: Callable,
        token: Optional[CancellationToken] = None,
        on_progress: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self._fn = fn
        self._token = token or CancellationToken()
        self._on_progress = on_progress

    def run(self) -> None:
        if self._token.cancelled:
            return
        try:
            if self._on_progress:
                self._fn(self._token, self._on_progress)
            else:
                self._fn(self._token)
        except Exception:
            pass


thread_pool = QThreadPool()
