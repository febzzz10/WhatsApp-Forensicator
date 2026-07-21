from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.repository import BaseRepository
from wft.infrastructure.filesystem.file_store import FileStore
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.logging.logging_service import LoggingService


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class EvidenceRepository(BaseRepository):
    def create_item(self, data: dict) -> int:
        return self._insert("evidence_items", data)

    def get_item(self, item_id: int) -> Optional[dict]:
        return self._get("evidence_items", item_id)

    def add_file(self, data: dict) -> int:
        return self._insert("evidence_files", data)

    def add_hash(self, data: dict) -> int:
        return self._insert("evidence_hashes", data)

    def get_items_for_case(self, case_id: int) -> list[dict]:
        return self._list("evidence_items", "case_id = ?", (case_id,))

    def update_item_state(self, item_id: int, state: str) -> None:
        now = _now_utc()
        self._db.execute(
            "UPDATE evidence_items SET state = ?, updated_at_utc = ? WHERE id = ?",
            (state, now, item_id),
        )


class EvidenceService:
    def __init__(self, store: FileStore, hash_service: HashingService, log: LoggingService) -> None:
        self._store = store
        self._hash = hash_service
        self._log = log

    def import_file(
        self,
        db: DatabaseConnection,
        case_id: int,
        evidence_code: str,
        title: str,
        source_type: str,
        acquisition_method: str,
        source_path: Path,
        examiner_id: Optional[int] = None,
    ) -> dict:
        repo = EvidenceRepository(db)

        item_data = {
            "case_id": case_id,
            "evidence_code": evidence_code,
            "title": title,
            "source_type": source_type,
            "acquisition_method": acquisition_method,
            "state": "COPYING",
            "imported_at_utc": _now_utc(),
            "created_at_utc": _now_utc(),
            "updated_at_utc": _now_utc(),
        }
        item_id = repo.create_item(item_data)

        relative_dir = f"originals/E{item_id:04d}"
        self._store.ensure_dir(relative_dir)

        dest_filename = source_path.name
        relative_path = f"{relative_dir}/{dest_filename}"

        try:
            sha256 = self._store.copy_to_store(source_path, relative_path)
            self._store.set_read_only(relative_path)

            file_data = {
                "evidence_item_id": item_id,
                "file_code": "F001",
                "original_filename": dest_filename,
                "original_source_path": str(source_path.resolve()),
                "stored_relative_path": relative_path,
                "size_bytes": self._store.size(relative_path),
                "imported_at_utc": _now_utc(),
                "is_original_copy": 1,
                "is_read_only": 1,
                "verification_status": "VALIDATED",
                "created_at_utc": _now_utc(),
                "updated_at_utc": _now_utc(),
            }
            file_id = repo.add_file(file_data)

            hash_data = {
                "evidence_file_id": file_id,
                "algorithm": "SHA256",
                "hash_value": sha256,
                "purpose": "IMPORT",
                "calculated_at_utc": _now_utc(),
                "calculated_by_tool_version": "1.0.0a1",
                "created_at_utc": _now_utc(),
            }
            repo.add_hash(hash_data)

            repo.update_item_state(item_id, "VERIFIED")

            self._log.info(f"Evidence imported: {evidence_code} ({source_path.name})")

            return {
                "item_id": item_id,
                "file_id": file_id,
                "sha256": sha256,
                "stored_path": relative_path,
            }

        except Exception as exc:
            repo.update_item_state(item_id, "FAILED")
            self._log.error(f"Evidence import failed for {evidence_code}: {exc}")
            raise
