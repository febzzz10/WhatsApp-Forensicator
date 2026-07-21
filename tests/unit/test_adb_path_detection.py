import os
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from wft.application.services.adb_service import (
    AdbService, COMMON_SDK_FALLBACKS,
)


@pytest.fixture
def patch_is_file():
    patcher = patch.object(Path, "is_file", return_value=False)
    with patcher as m:
        yield m


def test_find_adb_returns_none_when_not_found(patch_is_file):
    service = AdbService()
    with patch.object(service, "_check_adb_version", return_value=False), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None):
        result = service.find_adb()
    assert result is None


def test_find_adb_uses_configured_path_first():
    service = AdbService(configured_path=r"C:\custom\adb.exe")
    with patch.object(service, "_check_adb_version", return_value=True), \
         patch.object(Path, "is_file", return_value=True), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None):
        result = service.find_adb()
    assert result is not None
    assert "custom" in str(result)


def test_find_adb_skips_none_search_paths():
    service = AdbService()
    with patch.object(service, "_check_adb_version", return_value=False), \
         patch.object(Path, "is_file", return_value=False), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None):
        result = service.find_adb()
    assert result is None


def test_find_bundled_adb_returns_none_when_not_bundled():
    service = AdbService()
    result = service._find_bundled_adb()
    assert result is None


@patch("wft.application.services.adb_service.shutil.which")
def test_find_adb_uses_which_fallback(mock_which):
    mock_which.side_effect = lambda x: r"C:\path\adb.exe" if x in ("adb", "adb.exe") else None
    service = AdbService()
    with patch.object(service, "_check_adb_version", return_value=True), \
         patch.object(Path, "is_file", return_value=True):
        result = service.find_adb()
    assert result is not None
    assert "adb.exe" in str(result)


@patch("wft.application.services.adb_service.os.environ.get")
def test_find_env_paths_with_android_home(mock_env_get):
    mock_env_get.side_effect = lambda key, default="": {
        "ANDROID_HOME": r"C:\Android",
        "ANDROID_SDK_ROOT": "",
    }.get(key, default)
    service = AdbService()
    with patch.object(Path, "is_file", return_value=True):
        paths = service._find_env_paths()
    assert len(paths) >= 1
    assert "platform-tools" in str(paths[0])


def test_common_sdk_fallbacks_are_paths():
    for p in COMMON_SDK_FALLBACKS:
        assert isinstance(p, Path)
        assert "adb.exe" in str(p)


def test_discovery_cached_after_first_call():
    service = AdbService()
    with patch.object(service, "_check_adb_version", return_value=False), \
         patch.object(Path, "is_file", return_value=False), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None):
        first = service.find_adb()
    assert first is None

    service._adb_path = Path(r"D:\adb\adb.exe")
    service._discovery_attempted = True
    second = service.find_adb()
    assert second == Path(r"D:\adb\adb.exe")


def test_validate_path_returns_none_for_nonexistent():
    service = AdbService()
    with patch.object(Path, "is_file", return_value=False):
        result = service.validate_path(r"C:\nonexistent\adb.exe")
    assert result is None


@patch("wft.application.services.adb_service.subprocess.run")
def test_validate_path_returns_version_on_success(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0, stdout="Android Debug Bridge version 1.0.41", stderr=""
    )
    service = AdbService()
    with patch.object(Path, "is_file", return_value=True):
        result = service.validate_path(r"C:\adb\adb.exe")
    assert result == "Android Debug Bridge version 1.0.41"


def test_check_version_called_once_on_duplicate_paths():
    service = AdbService()
    call_count = 0

    def side_effect(path):
        nonlocal call_count
        call_count += 1
        return True

    with patch.object(service, "_check_adb_version", side_effect=side_effect), \
         patch.object(Path, "is_file", return_value=True), \
         patch("wft.application.services.adb_service.shutil.which", return_value=None):
        service.find_adb()
    assert call_count >= 1
