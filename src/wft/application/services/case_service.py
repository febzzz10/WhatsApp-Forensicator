import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import tomli_w

from wft.domain.enums import CaseStatus
from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.repository import BaseRepository
from wft.infrastructure.database.uow import UnitOfWork
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.logging.logging_service import LoggingService


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class CaseRepository(BaseRepository):
    def create_case(self, case_code: str, title: str, examiner_name: str, organisation: str, display_timezone: str) -> int:
        now = _now_utc()
        data = {
            "case_code": case_code,
            "title": title,
            "organisation": organisation,
            "status": CaseStatus.OPEN.value,
            "display_timezone": display_timezone,
            "case_encryption_enabled": 0,
            "external_services_enabled": 0,
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        case_id = self._insert("cases", data)

        examiner_data = {
            "case_id": case_id,
            "examiner_code": "EXAM-001",
            "full_name": examiner_name,
            "organisation": organisation,
            "is_primary": 1,
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        self._insert("examiners", examiner_data)

        return case_id

    def get_case(self, case_id: int) -> Optional[dict]:
        return self._get("cases", case_id)

    def get_case_by_code(self, case_code: str) -> Optional[dict]:
        return self._get_by("cases", "case_code", case_code)

    def update_case_status(self, case_id: int, status: str) -> None:
        now = _now_utc()
        self._db.execute(
            "UPDATE cases SET status = ?, updated_at_utc = ? WHERE id = ?",
            (status, now, case_id),
        )

    def get_primary_examiner(self, case_id: int) -> Optional[dict]:
        rows = self._db.execute(
            "SELECT * FROM examiners WHERE case_id = ? AND is_primary = 1 LIMIT 1",
            (case_id,),
        ).fetchone()
        return dict(rows) if rows else None


class CaseService:
    def __init__(self, hash_service: HashingService, log: LoggingService) -> None:
        self._hash = hash_service
        self._log = log

    def create_case(
        self,
        case_dir: Path,
        case_code: str,
        title: str,
        examiner_name: str,
        organisation: str,
        display_timezone: str = "UTC",
    ) -> dict:
        case_path = case_dir / case_code
        if case_path.exists():
            raise FileExistsError(f"Case directory already exists: {case_path}")

        case_path.mkdir(parents=True, exist_ok=True)
        for sub in ["originals", "working", "derived/parsed", "derived/recovered", "derived/thumbnails", "derived/indexes",
                     "reports", "exports", "logs", "manifests", "notes"]:
            (case_path / sub).mkdir(parents=True, exist_ok=True)

        db_path = case_path / "case.db"
        uow = UnitOfWork(db_path)
        with uow:
            uow.initialize_schema()
            repo = CaseRepository(uow.db)
            case_id = repo.create_case(case_code, title, examiner_name, organisation, display_timezone)
            uow.commit()

        self._write_case_toml(case_path, case_code, title, examiner_name, organisation, display_timezone)

        self._log.info(f"Case created: {case_code}")
        return {"case_id": case_id, "case_code": case_code, "path": str(case_path)}

    def open_case(self, case_dir: Path) -> dict:
        case_toml = case_dir / "case.toml"
        if not case_toml.exists():
            raise FileNotFoundError(f"case.toml not found in {case_dir}")
        db_path = case_dir / "case.db"
        if not db_path.exists():
            raise FileNotFoundError(f"case.db not found in {case_dir}")

        uow = UnitOfWork(db_path)
        with uow:
            uow.initialize_schema()
            repo = CaseRepository(uow.db)
            case = repo.get_case_by_code(case_dir.name)
            if not case:
                raise ValueError(f"Case {case_dir.name} not found in database")
            examiner = repo.get_primary_examiner(case["id"])
            self._log.info(f"Case opened: {case['case_code']}")
            return {
                "case": case,
                "examiner": examiner,
                "path": str(case_dir),
            }

    def get_dashboard(self, case_id: int, db: DatabaseConnection) -> dict:
        repo = CaseRepository(db)
        case = repo.get_case(case_id)
        if not case:
            return {}

        evidence_count = db.execute(
            "SELECT COUNT(*) FROM evidence_items WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        message_count = db.execute(
            "SELECT COUNT(*) FROM messages WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        contact_count = db.execute(
            "SELECT COUNT(*) FROM contacts WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        call_count = db.execute(
            "SELECT COUNT(*) FROM calls WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        media_count = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ?", (case_id,)
        ).fetchone()[0]

        return {
            "case_code": case["case_code"],
            "title": case["title"],
            "status": case["status"],
            "display_timezone": case["display_timezone"],
            "evidence_count": evidence_count,
            "message_count": message_count,
            "contact_count": contact_count,
            "call_count": call_count,
            "media_count": media_count,
        }

    def _write_case_toml(self, case_path: Path, case_code: str, title: str, examiner: str, org: str, tz: str) -> None:
        data = {
            "case_id": case_code,
            "title": title,
            "examiner": examiner,
            "organisation": org,
            "created_utc": _now_utc(),
            "display_timezone": tz,
            "case_encryption_enabled": False,
            "external_services_enabled": False,
        }
        with (case_path / "case.toml").open("wb") as f:
            tomli_w.dump(data, f)
