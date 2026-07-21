from enum import Enum
from typing import Optional, Callable

from PySide6.QtCore import Signal, QObject, QRunnable

from wft.ui.workers.worker_base import CancellationToken, thread_pool
from wft.application.services.adb_service import (
    AdbService, AdbDevice, AdbState, AdbError,
)


class AdbOperationType(Enum):
    SCAN = "scan"
    START_SERVER = "start_server"
    KILL_SERVER = "kill_server"
    DEVICE_DETAILS = "device_details"
    VALIDATE_PATH = "validate_path"


class AdbOperationSignals(QObject):
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    cancelled = Signal()


def _make_adb_service(configured_path: Optional[str] = None) -> AdbService:
    svc = AdbService(configured_path=configured_path)
    svc.find_adb()
    return svc


class AdbOperationWorker(QRunnable):
    def __init__(
        self,
        operation: AdbOperationType,
        configured_path: Optional[str] = None,
        serial: Optional[str] = None,
        timeout: int = 10,
        token: Optional[CancellationToken] = None,
        _service_override: Optional[AdbService] = None,
    ) -> None:
        super().__init__()
        self._operation = operation
        self._configured_path = configured_path
        self._serial = serial
        self._timeout = timeout
        self._token = token or CancellationToken()
        self._service_override = _service_override
        self.signals = AdbOperationSignals()

    def run(self) -> None:
        if self._token.cancelled:
            self.signals.cancelled.emit()
            self.signals.finished.emit(None)
            return
        self.signals.started.emit()
        try:
            svc = self._service_override or _make_adb_service(self._configured_path)
            result = self._do_operation(svc)
            if self._token.cancelled:
                self.signals.cancelled.emit()
                self.signals.finished.emit(None)
            else:
                self.signals.finished.emit(result)
        except Exception as exc:
            if self._token.cancelled:
                self.signals.cancelled.emit()
                self.signals.finished.emit(None)
            else:
                self.signals.error.emit(str(exc))

    def _do_operation(self, svc: AdbService) -> object:
        if self._operation == AdbOperationType.SCAN:
            return self._scan(svc)
        elif self._operation == AdbOperationType.START_SERVER:
            svc.start_server(timeout=self._timeout)
            return True
        elif self._operation == AdbOperationType.KILL_SERVER:
            svc.kill_server(timeout=self._timeout)
            return True
        elif self._operation == AdbOperationType.DEVICE_DETAILS:
            if not self._serial:
                raise AdbError("Serial required for device details")
            return svc.get_device_details(self._serial, timeout=self._timeout)
        elif self._operation == AdbOperationType.VALIDATE_PATH:
            return svc.validate_path(self._configured_path or "")
        return None

    def _scan(self, svc: AdbService) -> tuple:
        adb_state = svc.get_state()
        devices: list[AdbDevice] = []
        if adb_state == AdbState.CONNECTED and not self._token.cancelled:
            devices = svc.list_devices(timeout=self._timeout)
        return (adb_state, devices)

    def cancel(self) -> None:
        self._token.cancel()


def run_adb_operation(
    operation: AdbOperationType,
    configured_path: Optional[str] = None,
    serial: Optional[str] = None,
    timeout: int = 10,
    token: Optional[CancellationToken] = None,
    on_finished: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
) -> AdbOperationWorker:
    worker = AdbOperationWorker(
        operation=operation,
        configured_path=configured_path,
        serial=serial,
        timeout=timeout,
        token=token,
    )
    if on_finished:
        worker.signals.finished.connect(on_finished)
    if on_error:
        worker.signals.error.connect(on_error)
    thread_pool.start(worker)
    return worker
