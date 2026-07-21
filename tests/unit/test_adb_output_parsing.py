from wft.application.services.adb_service import (
    AdbService, AdbState, AdbDevice, DEVICE_STATE_MAP,
)


def test_device_state_map_has_expected_keys():
    assert AdbState.CONNECTED == DEVICE_STATE_MAP["device"]
    assert AdbState.UNAUTHORIZED == DEVICE_STATE_MAP["unauthorized"]
    assert AdbState.OFFLINE == DEVICE_STATE_MAP["offline"]
    assert AdbState.NO_PERMISSIONS == DEVICE_STATE_MAP["no permissions"]
    assert AdbState.BOOTLOADER == DEVICE_STATE_MAP["bootloader"]
    assert AdbState.RECOVERY == DEVICE_STATE_MAP["recovery"]


def test_parse_connected_device_line():
    service = AdbService()
    line = "0123456789ABCDEF	device product:razor model:Nexus_7 device:flo transport_id:1"
    device = service._parse_device_line(line)
    assert device is not None
    assert device.serial == "0123456789ABCDEF"
    assert device.state == AdbState.CONNECTED
    assert device.product == "razor"
    assert device.model == "Nexus 7"
    assert device.device_name == "flo"
    assert device.transport_id == "1"
    assert device.manufacturer is None


def test_parse_unauthorized_device():
    service = AdbService()
    line = "ABCDEF123456	unauthorized"
    device = service._parse_device_line(line)
    assert device is not None
    assert device.serial == "ABCDEF123456"
    assert device.state == AdbState.UNAUTHORIZED
    assert device.model is None


def test_parse_offline_device():
    service = AdbService()
    line = "dead0000dead	offline"
    device = service._parse_device_line(line)
    assert device is not None
    assert device.serial == "dead0000dead"
    assert device.state == AdbState.OFFLINE


def test_parse_no_permissions_device():
    service = AdbService()
    line = "XYZ789	no permissions"
    device = service._parse_device_line(line)
    assert device is not None
    assert device.serial == "XYZ789"
    assert device.state == AdbState.NO_PERMISSIONS


def test_parse_bootloader_device():
    service = AdbService()
    line = "FASTBOOT001	bootloader"
    device = service._parse_device_line(line)
    assert device is not None
    assert device.state == AdbState.BOOTLOADER


def test_parse_recovery_device():
    service = AdbService()
    line = "RECOVERY001	recovery"
    device = service._parse_device_line(line)
    assert device is not None
    assert device.state == AdbState.RECOVERY


def test_parse_unknown_state_defaults_unknown():
    service = AdbService()
    line = "SERIAL999	weird_state"
    device = service._parse_device_line(line)
    assert device is not None
    assert device.state == AdbState.UNKNOWN


def test_parse_empty_line_returns_none():
    service = AdbService()
    assert service._parse_device_line("") is None
    assert service._parse_device_line("   ") is None


def test_parse_header_line_returns_device():
    service = AdbService()
    device = service._parse_device_line("List of devices attached")
    assert device is not None
    assert device.state == AdbState.UNKNOWN


def test_parse_line_without_properties():
    service = AdbService()
    line = "abcdef	device"
    device = service._parse_device_line(line)
    assert device is not None
    assert device.serial == "abcdef"
    assert device.state == AdbState.CONNECTED
    assert device.product is None
    assert device.model is None


def test_adb_device_frozen_dataclass():
    device = AdbDevice(serial="test", state=AdbState.CONNECTED)
    with pytest.raises(Exception):
        device.serial = "changed"


import pytest
