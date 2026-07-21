from pathlib import Path
from typing import Optional, Callable

from wft.application.services.parse_service import ParseService
from wft.infrastructure.database.uow import UnitOfWork
from wft.infrastructure.database.connection import DatabaseConnection
from wft.application.services.audit_service import AuditService


class ParseEvidenceWorker:
    def __init__(self, parse_service: ParseService, audit_service: AuditService, case_dir: Path) -> None:
        self._parse_service = parse_service
        self._audit_service = audit_service
        self._case_dir = case_dir

    def run(self, case_id: int, evidence_item_id: int, source_file_id: int,
            source_path: Path, db_path: Path, display_timezone: str = "UTC",
            on_progress: Optional[Callable] = None,
            on_complete: Optional[Callable] = None,
            on_error: Optional[Callable] = None) -> dict:
        if on_progress:
            on_progress("Inspecting file...", 0, 100)

        selection = self._parse_service.select_parser(source_path)
        if not selection:
            msg = "No parser supports this file"
            if on_error:
                on_error(msg)
            return {"success": False, "status": "UNSUPPORTED", "error": msg}

        if on_progress:
            parser_id = selection[0].adapter_id
            on_progress(f"Parsing with {parser_id}...", 10, 100)

        result = self._parse_service.parse_evidence(
            case_id=case_id,
            evidence_item_id=evidence_item_id,
            source_file_id=source_file_id,
            source_path=source_path,
            db_path=db_path,
            case_dir=self._case_dir,
            display_timezone=display_timezone,
        )

        if on_progress:
            on_progress("Recording audit trail...", 80, 100)

        uow = UnitOfWork(db_path)
        with uow:
            self._audit_service.record_event(
                uow.db, case_id,
                "EVIDENCE_PARSED",
                f"Parser {result.get('parser_id', 'unknown')} completed: "
                f"{result.get('message_count', 0)} msgs, {result.get('contact_count', 0)} contacts",
                component_name="parse_worker",
                object_type="evidence_item",
                object_id=str(evidence_item_id),
            )
            uow.commit()

        if on_progress:
            on_progress("Complete", 100, 100)

        if on_complete:
            on_complete(result)

        return result


class BatchImportWorker:
    def __init__(self, evidence_service, file_store, parse_service, audit_service, log) -> None:
        self._evidence_service = evidence_service
        self._file_store = file_store
        self._parse_service = parse_service
        self._audit_service = audit_service
        self._log = log

    def import_and_parse(self, case_id: int, case_dir: Path, source_path: Path,
                         display_timezone: str = "UTC",
                         on_progress: Optional[Callable] = None,
                         on_complete: Optional[Callable] = None,
                         on_error: Optional[Callable] = None) -> dict:
        result = {
            "evidence_item_id": None,
            "parse_result": None,
            "sha256": None,
        }

        try:
            if on_progress:
                on_progress(f"Copying {source_path.name}...", 5, 100)

            from wft.infrastructure.database.uow import UnitOfWork
            db_path = case_dir / "case.db"

            uow = UnitOfWork(db_path)
            with uow:
                from wft.application.services.evidence_service import EvidenceRepository
                repo = EvidenceRepository(uow.db)
                items = repo.get_items_for_case(case_id)
                evidence_code = f"E{len(items) + 1:04d}"

                import_result = self._evidence_service.import_file(
                    db=uow.db,
                    case_id=case_id,
                    evidence_code=evidence_code,
                    title=source_path.name,
                    source_type="IMPORTED",
                    acquisition_method="USER_PROVIDED",
                    source_path=source_path,
                )

                result["evidence_item_id"] = import_result["item_id"]
                result["sha256"] = import_result["sha256"]

                self._audit_service.record_event(
                    uow.db, case_id,
                    "EVIDENCE_IMPORTED",
                    f"Imported {source_path.name} as {evidence_code}",
                    component_name="batch_import",
                    object_type="evidence_item",
                    object_id=str(import_result["item_id"]),
                )
                uow.commit()

            if on_progress:
                on_progress("Import complete, starting parse...", 40, 100)

            parse_result = self._parse_service.parse_evidence(
                case_id=case_id,
                evidence_item_id=import_result["item_id"],
                source_file_id=import_result.get("file_id", 1),
                source_path=source_path,
                db_path=db_path,
                case_dir=case_dir,
                display_timezone=display_timezone,
            )

            result["parse_result"] = parse_result

            if on_progress:
                on_progress("Complete", 100, 100)

            if on_complete:
                on_complete(result)

        except Exception as exc:
            self._log.error(f"Batch import+parse failed: {exc}")
            if on_error:
                on_error(str(exc))
            result["error"] = str(exc)

        return result
