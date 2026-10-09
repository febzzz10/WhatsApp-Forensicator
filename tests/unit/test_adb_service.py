from pathlib import Path
from subprocess import TimeoutExpired
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from wft.application.services.adb_service import (
    AdbService, AdbDevice, AdbState, AdbError, RootAccess,
)


@pytest.fixture
def mock_adb_path():
    service = AdbService()
    service._adb_path = Path(r"C:\adb\adb.exe")
    service._discovery_attempted = True
    return service


def test_list_devices_empty_when_no_adb():
    service = AdbService()
    with patch.object(Path, "is_file", return_value=False), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None):
        devices = service.list_devices()
    assert devices == []


def test_list_devices_returns_parsed_devices(mock_adb_path):
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = (
        "List of devices attached\n"
        "0123456789ABCDEF\tdevice product:razor model:Nexus_7\n"
        "DEADBEEF\tunauthorized\n"
    )
    mock_run.stderr = ""

    with patch("wft.application.services.adb_service.subprocess.run", return_value=mock_run):
        devices = mock_adb_path.list_devices()

    assert len(devices) == 2
    assert devices[0].serial == "0123456789ABCDEF"
    assert devices[0].state == AdbState.CONNECTED
    assert devices[1].serial == "DEADBEEF"
    assert devices[1].state == AdbState.UNAUTHORIZED


def test_list_devices_returns_empty_on_adb_error(mock_adb_path):
    with patch("wft.application.services.adb_service.subprocess.run", side_effect=OSError("No such file")):
        devices = mock_adb_path.list_devices()
    assert devices == []


def test_get_state_no_adb():
    service = AdbService()
    with patch.object(Path, "is_file", return_value=False), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None):
        assert service.get_state() == AdbState.NO_ADB


def test_get_state_connected(mock_adb_path):
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "List of devices attached\n0123456789ABCDEF\tdevice\n"

    with patch("wft.application.services.adb_service.subprocess.run", return_value=mock_run):
        state = mock_adb_path.get_state()
    assert state == AdbState.CONNECTED


def test_get_state_server_error(mock_adb_path):
    with patch("wft.application.services.adb_service.subprocess.run", side_effect=OSError("Connection refused")):
        state = mock_adb_path.get_state()
    assert state == AdbState.ADB_SERVER_ERROR


def test_start_server_success(mock_adb_path):
    mock_run = MagicMock()
    mock_run.returncode = 0

    with patch("wft.application.services.adb_service.subprocess.run", return_value=mock_run):
        mock_adb_path.start_server()


def test_start_server_raises_on_failure(mock_adb_path):
    mock_run = MagicMock()
    mock_run.returncode = 1
    mock_run.stdout = ""
    mock_run.stderr = "failed to start"

    with patch("wft.application.services.adb_service.subprocess.run", return_value=mock_run):
        with pytest.raises(AdbError):
            mock_adb_path.start_server()


def test_start_server_raises_when_no_adb():
    service = AdbService()
    with patch.object(Path, "is_file", return_value=False), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None), \
         pytest.raises(AdbError, match="ADB binary not found"):
        service.start_server()


def test_kill_server_does_not_raise(mock_adb_path):
    mock_run = MagicMock()
    mock_run.returncode = 0

    with patch("wft.application.services.adb_service.subprocess.run", return_value=mock_run):
        mock_adb_path.kill_server()


def test_kill_server_no_adb():
    service = AdbService()
    with patch.object(Path, "is_file", return_value=False), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None):
        service.kill_server()


def test_run_adb_command_raises_without_path():
    service = AdbService()
    with patch.object(Path, "is_file", return_value=False), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None), \
         pytest.raises(AdbError, match="ADB binary not found"):
        service._run_adb_command(["devices"])


def test_run_adb_command_uses_serial(mock_adb_path):
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "running"
    mock_run.stderr = ""

    with patch("wft.application.services.adb_service.subprocess.run", return_value=mock_run) as m:
        mock_adb_path._run_adb_command(["shell", "getprop", "ro.product.model"], serial="SERIAL1")
    call_args = m.call_args[0][0]
    assert "-s" in call_args
    assert "SERIAL1" in call_args


def test_server_version_returns_string(mock_adb_path):
    mock_adb_path._cached_version = None
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "Android Debug Bridge version 1.0.41\n"

    with patch("wft.application.services.adb_service.subprocess.run", return_value=mock_run):
        ver = mock_adb_path.server_version()
    assert ver is not None
    assert "1.0.41" in ver


def test_run_adb_command_timeout_raises_adb_error(mock_adb_path):
    with patch("wft.application.services.adb_service.subprocess.run", side_effect=TimeoutExpired("cmd", 15)):
        with pytest.raises(AdbError, match="timed out"):
            mock_adb_path._run_adb_command(["devices"])


def test_parse_device_line_returns_none_for_empty():
    service = AdbService()
    assert service._parse_device_line("") is None
    assert service._parse_device_line("   ") is None


def test_get_device_details_returns_unknown_for_missing():
    service = AdbService()
    service._adb_path = Path(r"C:\adb\adb.exe")
    service._discovery_attempted = True

    with patch("wft.application.services.adb_service.subprocess.run") as mock_run:
        mock_list = MagicMock()
        mock_list.returncode = 0
        mock_list.stdout = "List of devices attached\n"
        mock_list.stderr = ""
        mock_run.return_value = mock_list

        device = service._get_base_device("MISSING_SERIAL")
    assert device.serial == "MISSING_SERIAL"
    assert device.state == AdbState.UNKNOWN

class TestDetectRoot:
    def _mock_run(self, stdout="", returncode=0, stderr=""):
        mock = MagicMock()
        mock.returncode = returncode
        mock.stdout = stdout
        mock.stderr = stderr
        return mock

    def test_su_success_returns_su(self, mock_adb_path):
        mock_run = self._mock_run(stdout="uid=0(root) gid=0(root) groups=0(root)\n")
        with patch(
            "wft.application.services.adb_service.subprocess.run", return_value=mock_run
        ) as run:
            access = mock_adb_path.detect_root("SERIAL1")
        assert access == RootAccess.SU
        args = run.call_args[0][0]
        assert "root" not in args
        assert "su -c id" in args
        assert "-s" in args and "SERIAL1" in args

    def test_su_failure_userdebug_build_is_capable_only(self, mock_adb_path):
        su_fail = self._mock_run(returncode=1, stderr="su: not found")
        build_type = self._mock_run(stdout="userdebug\n")
        with patch(
            "wft.application.services.adb_service.subprocess.run",
            side_effect=[su_fail, build_type],
        ) as run:
            access = mock_adb_path.detect_root("SERIAL1")
        assert access == RootAccess.ADB_ROOT_CAPABLE
        assert run.call_count == 2

    def test_su_failure_user_build_returns_none(self, mock_adb_path):
        su_fail = self._mock_run(returncode=1, stderr="su: permission denied")
        build_type = self._mock_run(stdout="user\n")
        with patch(
            "wft.application.services.adb_service.subprocess.run",
            side_effect=[su_fail, build_type],
        ):
            access = mock_adb_path.detect_root("SERIAL1")
        assert access == RootAccess.NONE

    def test_getprop_failure_returns_none(self, mock_adb_path):
        su_fail = self._mock_run(returncode=1)
        prop_fail = self._mock_run(returncode=1)
        with patch(
            "wft.application.services.adb_service.subprocess.run",
            side_effect=[su_fail, prop_fail],
        ):
            access = mock_adb_path.detect_root("SERIAL1")
        assert access == RootAccess.NONE

    def test_detect_root_survives_non_root_su_output(self, mock_adb_path):
        su_ok_nonroot = self._mock_run(stdout="uid=2000(shell) gid=2000(shell)\n")
        build_type = self._mock_run(stdout="eng\n")
        with patch(
            "wft.application.services.adb_service.subprocess.run",
            side_effect=[su_ok_nonroot, build_type],
        ):
            access = mock_adb_path.detect_root("SERIAL1")
        assert access == RootAccess.ADB_ROOT_CAPABLE

    def test_detect_root_no_adb_binary_returns_none(self):
        service = AdbService()
        with patch.object(Path, "is_file", return_value=False), \
             patch("wft.application.services.adb_service.shutil.which", return_value=None):
            access = service.detect_root("SERIAL1")
        assert access == RootAccess.NONE

    def test_detect_root_unexpected_output_returns_none(self, mock_adb_path):
        su_ok_garbage = self._mock_run(stdout="totally unexpected output\n")
        build_type = self._mock_run(stdout="\n")
        with patch(
            "wft.application.services.adb_service.subprocess.run",
            side_effect=[su_ok_garbage, build_type],
        ):
            access = mock_adb_path.detect_root("SERIAL1")
        assert access == RootAccess.NONE

    def test_detect_root_oserror_returns_none(self, mock_adb_path):
        with patch(
            "wft.application.services.adb_service.subprocess.run",
            side_effect=OSError("adb exploded"),
        ):
            access = mock_adb_path.detect_root("SERIAL1")
        assert access == RootAccess.NONE
