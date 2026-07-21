from pathlib import Path
from typing import Optional

from wft.infrastructure.filesystem.file_store import FileStore
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.logging.logging_service import LoggingService
from wft.infrastructure.settings.settings import AppSettings
from wft.application.services.case_service import CaseService
from wft.application.services.evidence_service import EvidenceService
from wft.application.services.audit_service import AuditService
from wft.application.services.parse_service import ParseService
from wft.application.services.case_context import ActiveCaseContext
from wft.application.services.statistics_service import StatisticsService
from wft.application.services.search_service import SearchService
from wft.application.services.recovery_service import RecoveryService
from wft.application.services.adb_service import AdbService


class Container:
    def __init__(self, settings_path: Optional[Path] = None) -> None:
        if settings_path and settings_path.exists():
            self.settings = AppSettings.load(settings_path)
        else:
            self.settings = AppSettings()

        log_dir = Path(self.settings.data_dir) / "logs" if self.settings.data_dir else None
        self.log = LoggingService(log_dir, self.settings.log_level)

        self.hash_service = HashingService()

        if self.settings.data_dir:
            self.file_store = FileStore(Path(self.settings.data_dir), self.hash_service)
        else:
            self.file_store = FileStore(Path.home() / ".wft", self.hash_service)

        self.case_service = CaseService(self.hash_service, self.log)
        self.evidence_service = EvidenceService(self.file_store, self.hash_service, self.log)
        self.audit_service = AuditService()
        self.parse_service = ParseService(self.log)

        self.case_context = ActiveCaseContext()
        self.statistics_service = StatisticsService()
        self.search_service = SearchService()
        self.recovery_service = RecoveryService()

        self.adb_service = AdbService(
            configured_path=self.settings.adb.adb_path if self.settings.adb.adb_path else None
        )

        self.log.info("Application container initialised")
