import zipfile
from pathlib import Path

import pytest

from wft.application.services.evidence_service import EvidenceService
from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.migrations import Migrator
from wft.infrastructure.filesystem.file_store import FileStore, FileStoreError, QuarantineError
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.logging.logging_service import LoggingService


def _database(path: Path) -> DatabaseConnection:
    db = DatabaseConnection(path)
    Migrator(db, path).initialize()
    return db


def test_import_file_registers_item_before_copy(tmp_path: Path) -> None:
    db = _database(tmp_path / "case.db")
    now = "2026-01-01T00:00:00Z"
    db.execute(
        "INSERT INTO cases (case_code, title, status, display_timezone, created_at_utc, updated_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("TEST-CASE", "Test Case", "OPEN", "UTC", now, now),
    )
    db.commit()
    source = tmp_path / "chat.txt"
    source.write_text("hello", encoding="utf-8")
    service = EvidenceService(FileStore(tmp_path, HashingService()), HashingService(), LoggingService(None))

    result = service.import_file(
        db=db,
        case_id=1,
        evidence_code="E001",
        title="Chat",
        source_type="WHATSAPP_TEXT_EXPORT",
        acquisition_method="USER_PROVIDED",
        source_path=source,
    )

    assert result["item_id"] > 0
    assert db.execute("SELECT state FROM evidence_items WHERE id = ?", (result["item_id"],)).fetchone()[0] == "VERIFIED"


def test_file_store_does_not_accept_prefix_path_escape(tmp_path: Path) -> None:
    store = FileStore(tmp_path / "case", HashingService())
    with pytest.raises(FileStoreError):
        store.resolve("../case-escape/file.txt")


def test_zip_extraction_rejects_backslash_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "malicious.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("..\\outside.txt", "unsafe")

    with pytest.raises(QuarantineError):
        FileStore(tmp_path / "case", HashingService()).safe_extract_zip(
            archive, tmp_path / "extract"
        )


def test_unsupported_parse_marks_evidence_state(tmp_path: Path) -> None:
    db_path = tmp_path / "case.db"
    db = _database(db_path)
    now = "2026-01-01T00:00:00Z"
    db.execute(
        "INSERT INTO cases (case_code, title, status, display_timezone, created_at_utc, updated_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("TEST-CASE", "Test Case", "OPEN", "UTC", now, now),
    )
    db.execute(
        "INSERT INTO evidence_items (case_id, evidence_code, title, source_type, acquisition_method, "
        "state, imported_at_utc, created_at_utc, updated_at_utc) VALUES (1, 'E001', 'Unknown', "
        "'GENERIC_FILES', 'USER_PROVIDED', 'VERIFIED', ?, ?, ?)",
        (now, now, now),
    )
    db.commit()

    from wft.application.services.parse_service import ParseService

    result = ParseService(LoggingService(None)).parse_evidence(
        case_id=1,
        evidence_item_id=1,
        source_file_id=1,
        source_path=tmp_path / "unknown.bin",
        db_path=db_path,
        case_dir=tmp_path,
    )

    assert result["status"] == "UNSUPPORTED"
    assert db.execute("SELECT state FROM evidence_items WHERE id = 1").fetchone()[0] == "UNSUPPORTED"
