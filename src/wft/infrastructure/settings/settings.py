import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SETTINGS_FILENAME = "settings.toml"


@dataclass
class SecuritySettings:
    telemetry: bool = False
    allow_external_services: bool = False
    require_authorisation_acknowledgement: bool = True
    auto_lock_minutes: int = 15


@dataclass
class HashingSettings:
    primary: str = "sha256"
    secondary: str = "sha512"


@dataclass
class ParsingSettings:
    open_source_databases_read_only: bool = True
    preserve_unknown_columns: bool = True
    store_raw_timestamp_values: bool = True


@dataclass
class NetworkSettings:
    enabled: bool = False
    active_interception: bool = False
    offline_geoip_only: bool = True
    geoip_database_path: Optional[str] = None


@dataclass
class ReportSettings:
    include_limitations: bool = True
    include_tool_versions: bool = True
    include_manifest_hash: bool = True


@dataclass
class AdbSettings:
    adb_path: str = ""
    auto_detect: bool = True
    poll_interval_seconds: int = 3


@dataclass
class UiSettings:
    theme: str = "dark_forensic"
    sidebar_expanded: bool = True


@dataclass
class AppSettings:
    security: SecuritySettings = field(default_factory=SecuritySettings)
    hashing: HashingSettings = field(default_factory=HashingSettings)
    parsing: ParsingSettings = field(default_factory=ParsingSettings)
    network: NetworkSettings = field(default_factory=NetworkSettings)
    reports: ReportSettings = field(default_factory=ReportSettings)
    adb: AdbSettings = field(default_factory=AdbSettings)
    ui: UiSettings = field(default_factory=UiSettings)

    data_dir: str = ""
    default_case_dir: str = ""
    log_level: str = "INFO"

    def get(self, section: str, key: str) -> object:
        if section == "ui":
            return getattr(self.ui, key, None)
        return None

    def set(self, section: str, key: str, value: object) -> None:
        if section == "ui":
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)

    @classmethod
    def load(cls, path: Path) -> "AppSettings":
        if not path.exists():
            return cls()
        with path.open("rb") as f:
            data = tomllib.load(f)
        s = cls()
        sec = data.get("security", {})
        s.security.telemetry = sec.get("telemetry", False)
        s.security.allow_external_services = sec.get("allow_external_services", False)
        s.security.require_authorisation_acknowledgement = sec.get("require_authorisation_acknowledgement", True)
        s.security.auto_lock_minutes = sec.get("auto_lock_minutes", 15)

        h = data.get("hashing", {})
        s.hashing.primary = h.get("primary", "sha256")
        s.hashing.secondary = h.get("secondary", "sha512")

        p = data.get("parsing", {})
        s.parsing.open_source_databases_read_only = p.get("open_source_databases_read_only", True)
        s.parsing.preserve_unknown_columns = p.get("preserve_unknown_columns", True)
        s.parsing.store_raw_timestamp_values = p.get("store_raw_timestamp_values", True)

        n = data.get("network", {})
        s.network.enabled = n.get("enabled", False)
        s.network.active_interception = n.get("active_interception", False)
        s.network.offline_geoip_only = n.get("offline_geoip_only", True)
        s.network.geoip_database_path = n.get("geoip_database_path")

        r = data.get("reports", {})
        s.reports.include_limitations = r.get("include_limitations", True)
        s.reports.include_tool_versions = r.get("include_tool_versions", True)
        s.reports.include_manifest_hash = r.get("include_manifest_hash", True)

        a = data.get("adb", {})
        s.adb.adb_path = a.get("adb_path", "")
        s.adb.auto_detect = a.get("auto_detect", True)
        s.adb.poll_interval_seconds = max(2, min(30, a.get("poll_interval_seconds", 3)))

        u = data.get("ui", {})
        s.ui.theme = u.get("theme", "dark_forensic")
        s.ui.sidebar_expanded = u.get("sidebar_expanded", True)

        s.data_dir = data.get("data_dir", "")
        s.default_case_dir = data.get("default_case_dir", "")
        s.log_level = data.get("log_level", "INFO")
        return s
