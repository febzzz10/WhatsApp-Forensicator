from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from PySide6.QtCore import QObject, QRunnable, Signal

from wft.application.services.acquisition_results import ImportUserExportResult
from wft.application.services.evidence_service import EvidenceService
from wft.application.services.audit_service import AuditService
from wft.application.services.parse_service import ParseService
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.ui.workers.worker_base import CancellationToken


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class ImportUserExportSignals(QObject):
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    cancelled = Signal()


class EvidenceOperationSignals(QObject):
    started = Signal()
    progress = Signal(str, int, int)
    finished = Signal(object)
    error = Signal(str)
    cancelled = Signal()


class EvidenceImportWorker(QRunnable):
    """Import and parse evidence without sharing UI-thread database connections."""

    def __init__(
        self,
        evidence_service: EvidenceService,
        audit_service: AuditService,
        parse_service: ParseService,
        case_id: int,
        case_dir: Path,
        db_path: Path,
        source_path: Path,
        source_type: str,
        acquisition_method: str,
        token: Optional[CancellationToken] = None,
        source_is_directory: bool = False,
    ) -> None:
        super().__init__()
        self._evidence_service = evidence_service
        self._audit_service = audit_service
        self._parse_service = parse_service
        self._case_id = case_id
        self._case_dir = case_dir
        self._db_path = db_path
        self._source_path = source_path
        self._source_type = source_type
        self._acquisition_method = acquisition_method
        self._token = token or CancellationToken()
        self._source_is_directory = source_is_directory
        self.signals = EvidenceOperationSignals()

    def run(self) -> None:
        if self._token.cancelled:
            self.signals.cancelled.emit()
            return
        self.signals.started.emit()
        try:
            result = self._do_import()
            if self._token.cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(result)
        except Exception as exc:
            if self._token.cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.error.emit(str(exc))

    def _do_import(self) -> dict:
        from wft.infrastructure.database.uow import UnitOfWork
        from wft.application.services.evidence_service import EvidenceRepository

        directory_import_result = None
        with UnitOfWork(self._db_path) as uow:
            repo = EvidenceRepository(uow.db)
            items = repo.get_items_for_case(self._case_id)
            evidence_code = f"E{len(items) + 1:04d}"
            if self._source_is_directory:
                directory_import_result = self._evidence_service.import_directory(
                    db=uow.db,
                    case_id=self._case_id,
                    evidence_code=evidence_code,
                    title=self._source_path.name,
                    source_type=self._source_type,
                    acquisition_method=self._acquisition_method,
                    source_path=self._source_path,
                    case_dir=self._case_dir,
                    is_cancelled=lambda: self._token.cancelled,
                    on_progress=self.signals.progress.emit,
                )
                if directory_import_result["status"] in {"CANCELLED", "FAILED"}:
                    return directory_import_result
                self._audit_service.record_event(
                    uow.db,
                    self._case_id,
                    "EVIDENCE_IMPORTED",
                    f"Imported directory {self._source_path.name} as {evidence_code}",
                    component_name="evidence_import_worker",
                    object_type="evidence_item",
                    object_id=str(directory_import_result["item_id"]),
                )
                uow.commit()
            else:
                self.signals.progress.emit("Registering evidence...", 5, 100)
                import_result = self._evidence_service.import_file(
                    db=uow.db,
                    case_id=self._case_id,
                    evidence_code=evidence_code,
                    title=self._source_path.name,
                    source_type=self._source_type,
                    acquisition_method=self._acquisition_method,
                    source_path=self._source_path,
                    case_dir=self._case_dir,
                )
                self._audit_service.record_event(
                    uow.db,
                    self._case_id,
                    "EVIDENCE_IMPORTED",
                    f"Imported {self._source_path.name} as {evidence_code}",
                    component_name="evidence_import_worker",
                    object_type="evidence_item",
                    object_id=str(import_result["item_id"]),
                )
                uow.commit()

        if directory_import_result is not None:
            return self._parse_directory(directory_import_result)

        self.signals.progress.emit("Parsing verified case copy...", 40, 100)
        parse_result = self._parse_service.parse_evidence(
            case_id=self._case_id,
            evidence_item_id=import_result["item_id"],
            source_file_id=import_result["file_id"],
            source_path=self._case_dir / import_result["stored_path"],
            db_path=self._db_path,
            case_dir=self._case_dir,
        )
        self.signals.progress.emit("Complete", 100, 100)
        return {"import": import_result, "parse": parse_result, "evidence_code": evidence_code}

    def _parse_directory(self, import_result: dict) -> dict:
        parsed = 0
        unsupported = 0
        failed = 0
        warnings = list(import_result["warnings"])
        total_files = len(import_result["file_ids"])
        for index, (file_id, stored_path) in enumerate(
            zip(import_result["file_ids"], import_result["stored_paths"]), start=1
        ):
            if self._token.cancelled:
                self._mark_directory_failed(import_result["item_id"])
                return {**import_result, "status": "CANCELLED"}
            self.signals.progress.emit(
                f"Parsing {Path(stored_path).name} ({index}/{len(import_result['file_ids'])})",
                total_files + index,
                total_files * 2,
            )
            path = self._case_dir / stored_path
            selection = self._parse_service.select_parser(path)
            if self._token.cancelled:
                self._mark_directory_failed(import_result["item_id"])
                return {**import_result, "status": "CANCELLED"}
            if selection is None:
                unsupported += 1
                continue
            result = self._parse_service.parse_evidence(
                case_id=self._case_id,
                evidence_item_id=import_result["item_id"],
                source_file_id=file_id,
                source_path=path,
                db_path=self._db_path,
                case_dir=self._case_dir,
            )
            if result.get("success"):
                parsed += 1
            else:
                failed += 1
                warnings.extend(result.get("warnings", []))
        status = "PARSED" if not unsupported and not failed else "PARTIALLY_PARSED"
        from wft.infrastructure.database.uow import UnitOfWork
        with UnitOfWork(self._db_path) as uow:
            uow.db.execute(
                "UPDATE evidence_items SET state = ?, updated_at_utc = ? WHERE id = ?",
                (status, _now_utc(), import_result["item_id"]),
            )
            uow.commit()
        return {
            **import_result,
            "parsed_file_count": parsed,
            "unsupported_file_count": unsupported,
            "failed_file_count": failed,
            "warnings": warnings,
            "status": status,
        }

    def _mark_directory_failed(self, item_id: int) -> None:
        from wft.infrastructure.database.uow import UnitOfWork

        with UnitOfWork(self._db_path) as uow:
            uow.db.execute(
                "UPDATE evidence_items SET state = 'FAILED', updated_at_utc = ? WHERE id = ?",
                (_now_utc(), item_id),
            )
            uow.commit()

    def cancel(self) -> None:
        self._token.cancel()


class EvidenceParseWorker(QRunnable):
    """Parse one registered evidence file on a worker thread."""

    def __init__(
        self,
        parse_service: ParseService,
        audit_service: AuditService,
        case_id: int,
        evidence_item_id: int,
        source_file_id: int,
        source_path: Path,
        case_dir: Path,
        db_path: Path,
        display_timezone: str = "UTC",
        token: Optional[CancellationToken] = None,
    ) -> None:
        super().__init__()
        self._parse_service = parse_service
        self._audit_service = audit_service
        self._case_id = case_id
        self._evidence_item_id = evidence_item_id
        self._source_file_id = source_file_id
        self._source_path = source_path
        self._case_dir = case_dir
        self._db_path = db_path
        self._display_timezone = display_timezone
        self._token = token or CancellationToken()
        self.signals = EvidenceOperationSignals()

    def run(self) -> None:
        if self._token.cancelled:
            self.signals.cancelled.emit()
            return
        self.signals.started.emit()
        try:
            self.signals.progress.emit("Parsing verified case copy...", 10, 100)
            result = self._parse_service.parse_evidence(
                case_id=self._case_id,
                evidence_item_id=self._evidence_item_id,
                source_file_id=self._source_file_id,
                source_path=self._source_path,
                db_path=self._db_path,
                case_dir=self._case_dir,
                display_timezone=self._display_timezone,
            )
            if self._token.cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.progress.emit("Complete", 100, 100)
                self.signals.finished.emit(result)
        except Exception as exc:
            if self._token.cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.error.emit(str(exc))

    def cancel(self) -> None:
        self._token.cancel()


class ImportUserExportWorker(QRunnable):
    def __init__(
        self,
        evidence_service: EvidenceService,
        audit_service: AuditService,
        parse_service: ParseService,
        hash_service: HashingService,
        case_id: int,
        case_dir: Path,
        db_path: Path,
        source_path: Path,
        examiner_id: Optional[int] = None,
        token: Optional[CancellationToken] = None,
    ) -> None:
        super().__init__()
        self._evidence_service = evidence_service
        self._audit_service = audit_service
        self._parse_service = parse_service
        self._hash_service = hash_service
        self._case_id = case_id
        self._case_dir = case_dir
        self._db_path = db_path
        self._source_path = source_path
        self._examiner_id = examiner_id
        self._token = token or CancellationToken()
        self.signals = ImportUserExportSignals()

    def run(self) -> None:
        if self._token.cancelled:
            self.signals.cancelled.emit()
            self.signals.finished.emit(None)
            return
        self.signals.started.emit()
        try:
            result = self._do_import()
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

    def _do_import(self) -> ImportUserExportResult:
        from wft.infrastructure.database.uow import UnitOfWork
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.application.services.evidence_service import EvidenceRepository

        uow = UnitOfWork(self._db_path)
        with uow:
            repo = EvidenceRepository(uow.db)
            items = repo.get_items_for_case(self._case_id)
            evidence_code = "ADB-IMP-{:04d}".format(len(items) + 1)

            import_result = self._evidence_service.import_file(
                db=uow.db,
                case_id=self._case_id,
                evidence_code=evidence_code,
                title=self._source_path.name,
                source_type="WHATSAPP_TEXT_EXPORT",
                acquisition_method="USER_EXPORT",
                source_path=self._source_path,
                examiner_id=self._examiner_id,
                case_dir=self._case_dir,
            )

            self._audit_service.record_event(
                uow.db, self._case_id,
                "EVIDENCE_IMPORTED",
                "Imported user export: {}".format(self._source_path.name),
                component_name="import_export_worker",
                object_type="evidence_item",
                object_id=str(import_result["item_id"]),
                examiner_id=self._examiner_id,
            )
            uow.commit()

        parse_result = self._parse_service.parse_evidence(
            case_id=self._case_id,
            evidence_item_id=import_result["item_id"],
            source_file_id=import_result["file_id"],
            source_path=self._case_dir / import_result["stored_path"],
            db_path=self._db_path,
            case_dir=self._case_dir,
        )

        warnings: list[str] = parse_result.get("warnings", [])
        if not parse_result.get("success", False):
            warnings.append(
                "Parsing reported status: {}".format(parse_result.get("status", "FAILED"))
            )

        return ImportUserExportResult(
            evidence_id=import_result["item_id"],
            source_path=str(self._source_path.resolve()),
            stored_path=import_result["stored_path"],
            hash_value=import_result["sha256"],
            imported_items=parse_result.get("message_count", 0),
            warnings=warnings,
        )

    def cancel(self) -> None:
        self._token.cancel()
