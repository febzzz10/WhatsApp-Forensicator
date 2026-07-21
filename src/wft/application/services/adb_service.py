import os
import subprocess
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class AdbState(Enum):
    CONNECTED = "connected"
    UNAUTHORIZED = "unauthorized"
    OFFLINE = "offline"
    NO_PERMISSIONS = "no_permissions"
    BOOTLOADER = "bootloader"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"
    NO_ADB = "no_adb"
    ADB_SERVER_ERROR = "adb_server_error"


def _now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


DEVICE_STATE_MAP: dict[str, AdbState] = {
    "device": AdbState.CONNECTED,
    "unauthorized": AdbState.UNAUTHORIZED,
    "offline": AdbState.OFFLINE,
    "no permissions": AdbState.NO_PERMISSIONS,
    "bootloader": AdbState.BOOTLOADER,
    "recovery": AdbState.RECOVERY,
}

COMMON_SDK_FALLBACKS = [
    Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"))
    / "Android" / "android-sdk" / "platform-tools" / "adb.exe",
    Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
    / "Android" / "android-sdk" / "platform-tools" / "adb.exe",
    Path(os.environ.get("LocalAppData", os.path.expanduser("~\\AppData\\Local")))
    / "Android" / "Sdk" / "platform-tools" / "adb.exe",
]


class AdbError(Exception):
    def __init__(self, message: str, returncode: Optional[int] = None, stderr: str = "") -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: AdbState
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    product: Optional[str] = None
    device_name: Optional[str] = None
    transport_id: Optional[str] = None
    android_version: Optional[str] = None
    sdk_version: Optional[str] = None
    connection_type: str = "USB"


class AdbService:
    def __init__(self, configured_path: Optional[str] = None) -> None:
        self._configured_path: Optional[str] = configured_path
        self._adb_path: Optional[Path] = None
        self._cached_version: Optional[str] = None
        self._discovery_attempted = False

    @property
    def adb_path(self) -> Optional[Path]:
        return self._adb_path

    @property
    def cached_version(self) -> Optional[str]:
        return self._cached_version

    def find_adb(self) -> Optional[Path]:
        if self._discovery_attempted:
            return self._adb_path
        self._discovery_attempted = True

        search_paths: list[Optional[Path]] = []

        if self._configured_path:
            search_paths.append(Path(self._configured_path))

        bundled = self._find_bundled_adb()
        if bundled:
            search_paths.append(bundled)

        env_paths = self._find_env_paths()
        search_paths.extend(env_paths)

        which = shutil.which("adb") or shutil.which("adb.exe")
        if which:
            search_paths.append(Path(which))

        search_paths.extend(COMMON_SDK_FALLBACKS)

        seen: set[Path] = set()
        for path in search_paths:
            if path is None:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.is_file() and self._check_adb_version(resolved):
                self._adb_path = resolved
                return resolved

        return None

    def _find_bundled_adb(self) -> Optional[Path]:
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).resolve().parent.parent.parent.parent.parent
        candidates = [
            base / "tools" / "adb" / "adb.exe",
            base / "tools" / "adb" / "adb",
        ]
        for c in candidates:
            if c.is_file():
                return c
        return None

    def _find_env_paths(self) -> list[Path]:
        paths: list[Path] = []
        for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
            val = os.environ.get(var, "")
            if val:
                p = Path(val) / "platform-tools"
                for exe in ("adb.exe", "adb"):
                    full = p / exe
                    if full.is_file():
                        paths.append(full)
                        break
        return paths

    def _check_adb_version(self, path: Path) -> bool:
        try:
            result = subprocess.run(
                [str(path), "version"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode == 0:
                self._cached_version = result.stdout.strip()
                return True
            return False
        except (subprocess.SubprocessError, OSError):
            return False

    def _run_adb_command(
        self,
        args: list[str],
        timeout: int = 15,
        serial: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        if not self._adb_path:
            raise AdbError("ADB binary not found")

        cmd = [str(self._adb_path)]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        except subprocess.TimeoutExpired:
            raise AdbError(f"ADB command timed out after {timeout}s: {' '.join(args)}")
        except OSError as exc:
            raise AdbError(f"ADB execution failed: {exc}")

        if result.returncode != 0:
            raise AdbError(
                f"ADB command failed (exit {result.returncode}): {' '.join(args)}",
                returncode=result.returncode,
                stderr=result.stderr,
            )

        return result

    def list_devices(self, timeout: int = 10) -> list[AdbDevice]:
        if not self._adb_path:
            self.find_adb()
        if not self._adb_path:
            return []

        try:
            result = self._run_adb_command(["devices", "-l"], timeout=timeout)
        except AdbError:
            return []

        devices: list[AdbDevice] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices") or line.startswith("*"):
                continue
            device = self._parse_device_line(line)
            if device is not None:
                devices.append(device)
        return devices

    def _parse_device_line(self, line: str) -> Optional[AdbDevice]:
        parts = line.split(None, 1)
        if len(parts) < 2:
            return None
        serial, rest = parts

        tokens = rest.split()
        state_tokens: list[str] = []
        in_state = True
        for token in tokens:
            if in_state and ":" in token and token.index(":") > 0:
                in_state = False
            if in_state:
                state_tokens.append(token)

        state_str = " ".join(state_tokens) if state_tokens else "unknown"
        state = DEVICE_STATE_MAP.get(state_str, AdbState.UNKNOWN)

        props: dict[str, str] = {}
        capture_props = False
        for token in tokens:
            if not capture_props and ":" in token and token.index(":") > 0:
                capture_props = True
            if capture_props and ":" in token:
                key, _, value = token.partition(":")
                props[key] = value

        return AdbDevice(
            serial=serial,
            state=state,
            product=props.get("product"),
            model=props.get("model", "").replace("_", " ") if props.get("model") else None,
            device_name=props.get("device"),
            transport_id=props.get("transport_id"),
            connection_type="USB",
        )

    def get_device_details(
        self, serial: str, timeout: int = 15,
        cached_devices: Optional[list[AdbDevice]] = None,
    ) -> AdbDevice:
        base = None
        if cached_devices:
            for d in cached_devices:
                if d.serial == serial:
                    base = d
                    break
        if base is None:
            base = self._get_base_device(serial)

        props_batch = [
            "ro.product.model",
            "ro.product.manufacturer",
            "ro.product.name",
            "ro.build.version.release",
            "ro.build.version.sdk",
        ]

        all_output: dict[str, str] = {}
        try:
            result = self._run_adb_command(
                ["shell"] + [f"getprop {p}" for p in props_batch],
                timeout=timeout, serial=serial,
            )
            lines = result.stdout.strip().splitlines()
            for i, line in enumerate(lines):
                val = line.strip()
                if i < len(props_batch) and val:
                    all_output[props_batch[i]] = val
        except (AdbError, subprocess.SubprocessError):
            pass

        return AdbDevice(
            serial=base.serial,
            state=base.state,
            model=all_output.get("ro.product.model") or base.model,
            manufacturer=all_output.get("ro.product.manufacturer") or base.manufacturer,
            product=all_output.get("ro.product.name") or base.product,
            device_name=base.device_name,
            transport_id=base.transport_id,
            android_version=all_output.get("ro.build.version.release"),
            sdk_version=all_output.get("ro.build.version.sdk"),
            connection_type=base.connection_type,
        )

    def _get_base_device(self, serial: str) -> AdbDevice:
        devices = self.list_devices()
        for d in devices:
            if d.serial == serial:
                return d
        return AdbDevice(serial=serial, state=AdbState.UNKNOWN)

    def server_version(self) -> Optional[str]:
        if self._cached_version:
            return self._cached_version
        if not self._adb_path:
            self.find_adb()
        if not self._adb_path:
            return None
        if self._cached_version:
            return self._cached_version
        try:
            result = subprocess.run(
                [str(self._adb_path), "version"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode == 0:
                self._cached_version = result.stdout.strip()
                return self._cached_version
        except (subprocess.SubprocessError, OSError):
            pass
        return None

    def start_server(self, timeout: int = 15) -> None:
        if not self._adb_path:
            self.find_adb()
        if not self._adb_path:
            raise AdbError("ADB binary not found")
        try:
            self._run_adb_command(["start-server"], timeout=timeout)
        except AdbError as exc:
            raise AdbError(
                f"Failed to start ADB server: {exc}",
                returncode=exc.returncode,
                stderr=exc.stderr,
            )

    def kill_server(self, timeout: int = 10) -> None:
        if not self._adb_path:
            return
        try:
            self._run_adb_command(["kill-server"], timeout=timeout)
        except AdbError:
            pass

    def validate_path(self, path_str: str) -> Optional[str]:
        path = Path(path_str)
        if not path.is_file():
            return None
        try:
            result = subprocess.run(
                [str(path), "version"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, OSError):
            pass
        return None

    def get_state(self) -> AdbState:
        if not self._adb_path:
            self.find_adb()
        if not self._adb_path:
            return AdbState.NO_ADB
        try:
            self._run_adb_command(["devices", "-l"], timeout=5)
            return AdbState.CONNECTED
        except AdbError:
            return AdbState.ADB_SERVER_ERROR
