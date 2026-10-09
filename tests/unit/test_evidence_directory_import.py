from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wft.application.services.evidence_service import EvidenceService
from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.migrations import Migrator
from wft.infrastructure.filesystem.file_store import FileStore
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.logging.logging_service import LoggingService
from wft.ui.workers.import_export_worker import EvidenceImportWorker
from wft.ui.workers.worker_base import CancellationToken


def _case_db(path: Path) -> DatabaseConnection:
    db = DatabaseConnection(path)
    Migrator(db, path).initialize()
    now = "2026-01-01T00:00:00Z"
    db.execute(
        "INSERT INTO cases (case_code, title, status, display_timezone, created_at_utc, updated_at_utc) "
        "VALUES ('TEST-CASE', 'Test Case', 'OPEN', 'UTC', ?, ?)",
        (now, now),
    )
    db.commit()
    return db


def test_directory_import_registers_one_item_and_each_file(tmp_path: Path) -> None:
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    source = tmp_path / "source"
    (source / "nested").mkdir(parents=True)
    (source / "_chat.txt").write_text("chat", encoding="utf-8")
    (source / "nested" / "report.txt").write_text("report", encoding="utf-8")
    db = _case_db(case_dir / "case.db")
    service = EvidenceService(FileStore(case_dir, HashingService()), HashingService(), LoggingService(None))

    result = service.import_directory(
        db=db,
        case_id=1,
        evidence_code="E0001",
        title="source",
        source_type="GENERIC_FILES",
        acquisition_method="USER_PROVIDED",
        source_path=source,
        case_dir=case_dir,
    )

    assert result["imported_file_count"] == 2
    assert len(result["file_ids"]) == 2
    assert len(set(result["file_ids"])) == 2
    assert result["stored_paths"] == [
        "originals/E0001/_chat.txt",
        "originals/E0001/nested/report.txt",
    ]
    assert all((case_dir / path).is_file() for path in result["stored_paths"])
    assert db.execute("SELECT state FROM evidence_items WHERE id = 1").fetchone()[0] == "VERIFIED"


def test_directory_import_rejects_symlink_without_following(tmp_path: Path) -> None:
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (source / "safe.txt").write_text("safe", encoding="utf-8")
    link = source / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are unavailable in this environment")
    db = _case_db(case_dir / "case.db")
    service = EvidenceService(FileStore(case_dir, HashingService()), HashingService(), LoggingService(None))

    result = service.import_directory(
        db=db,
        case_id=1,
        evidence_code="E0001",
        title="source",
        source_type="GENERIC_FILES",
        acquisition_method="USER_PROVIDED",
        source_path=source,
        case_dir=case_dir,
    )

    assert result["imported_file_count"] == 1
    assert result["skipped_file_count"] == 1
    assert not (case_dir / "originals/E0001/link.txt").exists()


def test_directory_import_empty_directory_is_not_verified(tmp_path: Path) -> None:
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    source = tmp_path / "empty"
    source.mkdir()
    db = _case_db(case_dir / "case.db")
    service = EvidenceService(FileStore(case_dir, HashingService()), HashingService(), LoggingService(None))

    result = service.import_directory(
        db=db,
        case_id=1,
        evidence_code="E0001",
        title="empty",
        source_type="GENERIC_FILES",
        acquisition_method="USER_PROVIDED",
        source_path=source,
        case_dir=case_dir,
    )

    assert result["imported_file_count"] == 0
    assert result["status"] == "FAILED"
    assert db.execute("SELECT state FROM evidence_items WHERE id = 1").fetchone()[0] == "FAILED"


def test_directory_worker_cancellation_does_not_finish(tmp_path: Path) -> None:
    token = CancellationToken()
    worker = EvidenceImportWorker(
        evidence_service=MagicMock(),
        audit_service=MagicMock(),
        parse_service=MagicMock(),
        case_id=1,
        case_dir=tmp_path,
        db_path=tmp_path / "case.db",
        source_path=tmp_path,
        source_type="GENERIC_FILES",
        acquisition_method="USER_PROVIDED",
        token=token,
        source_is_directory=True,
    )
    cancelled = []
    finished = []
    worker.signals.cancelled.connect(lambda: cancelled.append(True))
    worker.signals.finished.connect(lambda value: finished.append(value))

    worker.cancel()
    worker.run()

    assert cancelled == [True]
    assert finished == []


def test_directory_worker_cancellation_during_parse_marks_item_failed(tmp_path: Path) -> None:
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    source = tmp_path / "source"
    source.mkdir()
    (source / "chat.txt").write_text("chat", encoding="utf-8")
    db_path = case_dir / "case.db"
    db = _case_db(db_path)
    token = CancellationToken()

    parse_service = MagicMock()
    parse_service.select_parser.return_value = (object(), {})

    def cancel_after_select(_path: Path):
        token.cancel()
        return (object(), {})

    parse_service.select_parser.side_effect = cancel_after_select
    worker = EvidenceImportWorker(
        evidence_service=EvidenceService(
            FileStore(case_dir, HashingService()), HashingService(), LoggingService(None)
        ),
        audit_service=MagicMock(),
        parse_service=parse_service,
        case_id=1,
        case_dir=case_dir,
        db_path=db_path,
        source_path=source,
        source_type="GENERIC_FILES",
        acquisition_method="USER_PROVIDED",
        token=token,
        source_is_directory=True,
    )
    worker._token._cancelled = False
    result = worker._do_import()

    assert result["status"] == "CANCELLED"
    assert db.execute("SELECT state FROM evidence_items WHERE id = 1").fetchone()[0] == "FAILED"


def test_directory_worker_progress_is_monotonic(tmp_path: Path) -> None:
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    source = tmp_path / "source"
    source.mkdir()
    (source / "chat.txt").write_text("chat", encoding="utf-8")
    db_path = case_dir / "case.db"
    _case_db(db_path)
    parse_service = MagicMock()
    parse_service.select_parser.return_value = None
    worker = EvidenceImportWorker(
        evidence_service=EvidenceService(
            FileStore(case_dir, HashingService()), HashingService(), LoggingService(None)
        ),
        audit_service=MagicMock(),
        parse_service=parse_service,
        case_id=1,
        case_dir=case_dir,
        db_path=db_path,
        source_path=source,
        source_type="GENERIC_FILES",
        acquisition_method="USER_PROVIDED",
        source_is_directory=True,
    )
    progress = []
    worker.signals.progress.connect(lambda _message, current, total: progress.append((current, total)))

    worker._do_import()

    assert progress
    assert all(current <= progress[index + 1][0] for index, (current, _total) in enumerate(progress[:-1]))
