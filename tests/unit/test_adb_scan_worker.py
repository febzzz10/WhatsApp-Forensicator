from unittest.mock import MagicMock, patch

import pytest

from wft.application.services.adb_service import AdbService, AdbDevice, AdbState
from wft.ui.workers.adb_scan_worker import (
    AdbOperationWorker, AdbOperationType,
)


@pytest.fixture
def mock_service_factory():
    def _factory(**overrides):
        service = MagicMock(spec=AdbService)
        service.get_state.return_value = overrides.get("state", AdbState.CONNECTED)
        service.list_devices.return_value = overrides.get(
            "devices",
            [AdbDevice(serial="TEST001", state=AdbState.CONNECTED, model="Pixel 9")],
        )
        return service
    return _factory


def test_scan_worker_fires_finished_on_success(mock_service_factory):
    service = mock_service_factory()
    worker = AdbOperationWorker(
        operation=AdbOperationType.SCAN,
        serial=None,
        timeout=10,
        _service_override=service,
    )
    finished_called = []
    worker.signals.finished.connect(lambda d: finished_called.append(d))
    worker.run()
    assert len(finished_called) == 1
    state, devices = finished_called[0]
    assert state == AdbState.CONNECTED
    assert len(devices) == 1
    assert devices[0].serial == "TEST001"


def test_scan_worker_fires_error_on_exception(mock_service_factory):
    service = mock_service_factory()
    service.list_devices.side_effect = RuntimeError("ADB crash")
    worker = AdbOperationWorker(
        operation=AdbOperationType.SCAN,
        serial=None,
        timeout=10,
        _service_override=service,
    )
    error_called = []
    worker.signals.error.connect(lambda msg: error_called.append(msg))
    worker.run()
    assert len(error_called) == 1
    assert "ADB crash" in error_called[0]


def test_scan_worker_cancelled_before_run_emits_cancelled(mock_service_factory):
    service = mock_service_factory()
    worker = AdbOperationWorker(
        operation=AdbOperationType.SCAN,
        serial=None,
        timeout=10,
        _service_override=service,
    )
    worker._token.cancel()
    cancelled_called = []
    worker.signals.cancelled.connect(lambda: cancelled_called.append(True))
    worker.run()
    assert len(cancelled_called) == 1


def test_scan_worker_fires_finished_with_empty_list(mock_service_factory):
    service = mock_service_factory(devices=[])
    worker = AdbOperationWorker(
        operation=AdbOperationType.SCAN,
        serial=None,
        timeout=10,
        _service_override=service,
    )
    finished_called = []
    worker.signals.finished.connect(lambda d: finished_called.append(d))
    worker.run()
    assert len(finished_called) == 1
    state, devices = finished_called[0]
    assert state == AdbState.CONNECTED
    assert devices == []


def test_scan_worker_fires_started_signal(mock_service_factory):
    service = mock_service_factory()
    worker = AdbOperationWorker(
        operation=AdbOperationType.SCAN,
        serial=None,
        timeout=10,
        _service_override=service,
    )
    started_called = []
    worker.signals.started.connect(lambda: started_called.append(True))
    worker.run()
    assert len(started_called) == 1


def test_scan_worker_handles_no_adb_state(mock_service_factory):
    service = mock_service_factory(state=AdbState.NO_ADB)
    worker = AdbOperationWorker(
        operation=AdbOperationType.SCAN,
        serial=None,
        timeout=10,
        _service_override=service,
    )
    finished_called = []
    worker.signals.finished.connect(lambda d: finished_called.append(d))
    worker.run()
    assert len(finished_called) == 1
    state, devices = finished_called[0]
    assert state == AdbState.NO_ADB
    assert devices == []
    service.list_devices.assert_not_called()


def test_validate_path_worker(mock_service_factory):
    service = mock_service_factory()
    service.validate_path.return_value = True
    worker = AdbOperationWorker(
        operation=AdbOperationType.VALIDATE_PATH,
        serial=None,
        configured_path="C:\\adb.exe",
        timeout=10,
        _service_override=service,
    )
    finished_called = []
    worker.signals.finished.connect(lambda d: finished_called.append(d))
    worker.run()
    assert len(finished_called) == 1
    assert finished_called[0] is True
    service.validate_path.assert_called_once_with("C:\\adb.exe")


def test_device_details_worker(mock_service_factory):
    service = mock_service_factory()
    device = AdbDevice(
        serial="TEST001",
        state=AdbState.CONNECTED,
        model="Pixel 9",
        manufacturer="Google",
        product="example",
    )
    service.get_device_details.return_value = device
    worker = AdbOperationWorker(
        operation=AdbOperationType.DEVICE_DETAILS,
        serial="TEST001",
        timeout=10,
        _service_override=service,
    )
    finished_called = []
    worker.signals.finished.connect(lambda d: finished_called.append(d))
    worker.run()
    assert len(finished_called) == 1
    data = finished_called[0]
    assert data.serial == "TEST001"
    assert data.model == "Pixel 9"
    service.get_device_details.assert_called_once_with("TEST001", timeout=10)
