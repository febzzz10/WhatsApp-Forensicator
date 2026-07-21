# ADB Device Detection — Design Specification

## Problem
Connected Android phones are not detected by the WhatsApp Forensicator ADB Extractor
page. The page is a placeholder: no ADB binary discovery, no subprocess execution,
no device state parsing, no background scanning, and no settings integration.

## Solution
Create a layered ADB detection subsystem:

```
UI Layer:     adb_extractor_page.py (rewrite) + settings_page.py (extend)
Worker Layer: adb_scan_worker.py (new — QRunnable async scanner)
Service Layer: adb_service.py (new — discovery, commands, parsing)
Settings:     AdbSettings dataclass in settings.py
```

## ADB Discovery Order
1. User-configured path from `AdbSettings.adb_path`
2. Bundled `<app>/tools/adb/adb.exe` (plus DLLs)
3. `ANDROID_HOME/platform-tools/adb.exe`
4. `ANDROID_SDK_ROOT/platform-tools/adb.exe`
5. `shutil.which("adb")` / `shutil.which("adb.exe")`
6. Common Windows SDK fallback paths

## Data Models
`AdbDevice(frozen dataclass)`: serial, state, model, manufacturer, product,
device_name, transport_id, android_version, sdk_version, connection_type.

`AdbState(str Enum)`: CONNECTED, UNAUTHORIZED, OFFLINE, NO_PERMISSIONS,
BOOTLOADER, RECOVERY, UNKNOWN, NO_ADB, ADB_SERVER_ERROR.

## Subprocess Runner
Single `_run_adb_command(args, timeout=15)` method. Uses `subprocess.run()` with
`shell=False`, `capture_output=True`, `text=True`, `creationflags=CREATE_NO_WINDOW`
on Windows. Raises `AdbError` on non-zero exit or timeout.

## UI States
- **ADB Missing** banner with instructions
- **ADB Found** with version info + status
- **Authorised** device info panel (manufacturer, model, Android, SDK, serial, transport)
- **Unauthorized** banner with accept-prompt guidance + Refresh/Restart/Troubleshoot buttons
- **Offline** banner with reconnect guidance
- **No Device** guidance banner
- **Scanning** — Refresh disabled, spinner/status text

## Polling
QTimer at user-configurable interval (2-5s, default 3s). Starts in `on_activated()`,
stops when page hidden. Guard against overlapping scans. Auto Detect toggle in
settings and on page.

## Device-Specific Commands
Always use `adb -s SERIAL shell getprop ...` for device properties.

## Files Created
- `src/wft/application/services/adb_service.py`
- `src/wft/ui/workers/adb_scan_worker.py`
- `tests/unit/test_adb_service.py`
- `tests/unit/test_adb_path_detection.py`
- `tests/unit/test_adb_output_parsing.py`
- `tests/unit/test_adb_scan_worker.py`
- `scripts/test_adb_device.py`

## Files Modified
- `src/wft/infrastructure/settings/settings.py` +AdbSettings
- `src/wft/application/services/__init__.py` +AdbService
- `src/wft/bootstrap.py` +AdbService
- `src/wft/ui/pages/adb_extractor_page.py` (rewrite)
- `src/wft/ui/pages/settings_page.py` +ADB section
- `src/wft/ui/workers/__init__.py` +AdbScanWorker

## Testing
- All unit tests use `unittest.mock.patch` over `subprocess.run`
- No real phone required in automated tests
- Manual script `scripts/test_adb_device.py` for hardware verification
- Each test file covers: path discovery (6), output parsing (9), service (10), worker safety (7)
