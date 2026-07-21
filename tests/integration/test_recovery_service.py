import shutil
import tempfile
from pathlib import Path

import pytest

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.schema import ALL_TABLE_DDL, ALL_INDEXES
from wft.application.services.recovery_service import RecoveryService
from wft.infrastructure.database.artefact_repositories import RecoveryCandidateRepository


def _create_recovery_db(db_path: Path) -> DatabaseConnection:
    conn = DatabaseConnection(db_path)
    for ddl in ALL_TABLE_DDL:
        conn.execute(ddl)
    for idx in ALL_INDEXES:
        conn.execute(idx)
    conn.execute(
        "INSERT INTO cases (case_code, title, status, display_timezone, created_at_utc, updated_at_utc) "
        "VALUES ('TEST-CASE', 'Test Case', 'OPEN', 'UTC', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO examiners (case_id, examiner_code, full_name, is_primary, created_at_utc, updated_at_utc) "
        "VALUES (1, 'EXAM-001', 'Test Examiner', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO evidence_items (case_id, evidence_code, title, source_type, acquisition_method, "
        "state, imported_at_utc, created_at_utc, updated_at_utc) "
        "VALUES (1, 'E001', 'test.db', 'SQLITE', 'IMPORT', 'VERIFIED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO evidence_files (evidence_item_id, file_code, original_filename, stored_relative_path, "
        "size_bytes, imported_at_utc, created_at_utc, updated_at_utc) "
        "VALUES (1, 'F001', 'test.db', 'originals/E0001/test.db', 100, "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO recovery_runs (case_id, recovery_code, strategy, source_evidence_file_id, "
        "started_at_utc, status, tool_component_version, created_at_utc, updated_at_utc) "
        "VALUES (1, 'REC-001', 'WAL', 1, '2026-01-01T00:00:00Z', 'COMPLETED', '1.0.0', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO recovery_runs (case_id, recovery_code, strategy, source_evidence_file_id, "
        "started_at_utc, status, tool_component_version, created_at_utc, updated_at_utc) "
        "VALUES (1, 'REC-002', 'PAGE_CARVING', 1, '2026-01-01T00:00:00Z', 'COMPLETED', '1.0.0', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO recovery_candidates (recovery_run_id, candidate_code, candidate_type, "
        "confidence_level, review_status, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CAND-001', 'MESSAGE', 'HIGH', 'UNRESOLVED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO recovery_candidates (recovery_run_id, candidate_code, candidate_type, "
        "confidence_level, review_status, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CAND-002', 'CONTACT', 'MEDIUM', 'UNRESOLVED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO recovery_candidates (recovery_run_id, candidate_code, candidate_type, "
        "confidence_level, review_status, created_at_utc, updated_at_utc) "
        "VALUES (2, 'CAND-003', 'MESSAGE', 'LOW', 'UNRESOLVED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    return conn


class TestRecoveryServiceIntegration:
    def test_get_candidates(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            candidates = svc.get_candidates(db, 1)
            assert len(candidates) == 3
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_case_isolation(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            candidates = svc.get_candidates(db, 999)
            assert len(candidates) == 0
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_confidence_filter(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            high = svc.get_candidates(db, 1, confidence="HIGH")
            assert len(high) == 1
            medium = svc.get_candidates(db, 1, confidence="MEDIUM")
            assert len(medium) == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_pagination(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            page1 = svc.get_candidates(db, 1, limit=2)
            assert len(page1) == 2
            page2 = svc.get_candidates(db, 1, limit=2, offset=2)
            assert len(page2) == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_accept_candidate(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            svc.accept(db, 1, examiner_id=1)
            repo = RecoveryCandidateRepository(db)
            candidates = repo.list_for_case(1)
            accepted = [c for c in candidates if c["review_status"] == "ACCEPTED"]
            assert len(accepted) == 1
            assert accepted[0]["id"] == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_reject_candidate(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            svc.reject(db, 1, examiner_id=1)
            repo = RecoveryCandidateRepository(db)
            candidates = repo.list_for_case(1)
            rejected = [c for c in candidates if c["review_status"] == "REJECTED"]
            assert len(rejected) == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_leave_unresolved(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            svc.leave_unresolved(db, 1, examiner_id=1)
            repo = RecoveryCandidateRepository(db)
            candidate = repo.list_for_case(1)
            c = next(c for c in candidate if c["id"] == 1)
            assert c["review_status"] == "UNRESOLVED"
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_invalid_candidate(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            svc.accept(db, 999)
            repo = RecoveryCandidateRepository(db)
            candidates = repo.list_for_case(1)
            accepted = [c for c in candidates if c["review_status"] == "ACCEPTED"]
            assert len(accepted) == 0
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_review_timestamp_set(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_recovery_db(Path(tmp) / "test.db")
            svc = RecoveryService()
            svc.accept(db, 1, examiner_id=1)
            row = db.execute("SELECT reviewed_at_utc, reviewed_by_examiner_id FROM recovery_candidates WHERE id = 1").fetchone()
            assert row["reviewed_at_utc"] is not None
            assert row["reviewed_by_examiner_id"] == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
