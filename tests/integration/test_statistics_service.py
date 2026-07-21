import tempfile
from pathlib import Path

import pytest

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.schema import ALL_TABLE_DDL, ALL_INDEXES
from wft.application.services.statistics_service import StatisticsService


def _create_empty_db(db_path: Path) -> DatabaseConnection:
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
    conn.commit()
    return conn


def _populated_db(db_path: Path) -> DatabaseConnection:
    conn = _create_empty_db(db_path)
    conn.execute(
        "INSERT INTO contacts (case_id, contact_code, display_name, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CONTACT-001', 'Alice', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO contacts (case_id, contact_code, display_name, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CONTACT-002', 'Bob', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO conversations (case_id, conversation_code, conversation_type, contact_id, title, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CONV-001', 'DIRECT', 1, 'Alice Chat', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO messages (case_id, message_code, conversation_id, direction, message_type, text_content, "
        "sent_at_utc, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MSG-001', 1, 'INCOMING', 'TEXT', 'Hello', '2026-01-01T12:00:00Z', 'PARSED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO messages (case_id, message_code, conversation_id, direction, message_type, text_content, "
        "sent_at_utc, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MSG-002', 1, 'OUTGOING', 'TEXT', 'Hi', '2026-01-01T12:01:00Z', 'PARSED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO calls (case_id, call_code, conversation_id, call_type, direction, started_at_utc, "
        "duration_seconds, was_answered, origin, confidence_level, validation_status, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CALL-001', 1, 'VOICE', 'INCOMING', '2026-01-01T13:00:00Z', 120, 1, 'PARSED', 'HIGH', 'VALIDATED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO calls (case_id, call_code, conversation_id, call_type, direction, started_at_utc, "
        "duration_seconds, was_answered, origin, confidence_level, validation_status, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CALL-002', 1, 'VIDEO', 'OUTGOING', '2026-01-01T14:00:00Z', 300, 1, 'PARSED', 'HIGH', 'VALIDATED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO media_items (case_id, media_code, declared_mime_type, size_bytes, origin, confidence_level, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MEDIA-001', 'image/jpeg', 1024, 'PARSED', 'HIGH', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO media_items (case_id, media_code, declared_mime_type, size_bytes, origin, confidence_level, is_orphan, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MEDIA-002', 'video/mp4', 2048, 'PARSED', 'HIGH', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO media_items (case_id, media_code, declared_mime_type, size_bytes, origin, confidence_level, is_missing, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MEDIA-003', 'audio/mp3', 512, 'PARSED', 'HIGH', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO groups (case_id, group_code, subject, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'GROUP-001', 'Test Group', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO evidence_items (case_id, evidence_code, title, source_type, acquisition_method, "
        "state, imported_at_utc, created_at_utc, updated_at_utc) "
        "VALUES (1, 'E001', 'test.txt', 'TEST', 'IMPORT', 'VERIFIED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO audit_events (case_id, event_sequence, event_type, event_description, component_name, "
        "component_version, event_hash, occurred_at_utc, created_at_utc) "
        "VALUES (1, 1, 'CASE_CREATED', 'Case created', 'test', '1.0.0', 'a'*64, "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO timeline_events (case_id, event_code, event_type, title, origin, confidence_level, created_at_utc) "
        "VALUES (1, 'TL-001', 'MESSAGE', 'Hello', 'PARSED', 'HIGH', '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    return conn


class TestStatisticsServiceIntegration:
    def _run(self, fn, *args, **kwargs):
        tmp = tempfile.mkdtemp()
        try:
            db_path = Path(tmp) / "test.db"
            return fn(db_path, *args, **kwargs)
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_empty_case_stats(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_empty_db(Path(tmp) / "test.db")
            svc = StatisticsService()
            stats = svc.get_case_stats(db, 1)
            for key in ["evidence", "messages", "contacts", "calls", "media", "groups", "conversations"]:
                assert stats[key] == 0, f"{key} should be 0"
            db.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_populated_case_stats(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _populated_db(Path(tmp) / "test.db")
            svc = StatisticsService()
            stats = svc.get_case_stats(db, 1)
            assert stats["messages"] == 2
            assert stats["contacts"] == 2
            assert stats["calls"] == 2
            assert stats["media"] == 3
            assert stats["groups"] == 1
            assert stats["evidence"] == 1
            assert stats["conversations"] == 1
            assert stats["timeline"] == 1
            assert stats["audit"] == 1
            db.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_case_isolation(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _populated_db(Path(tmp) / "test.db")
            svc = StatisticsService()
            stats = svc.get_case_stats(db, 999)
            for key in ["messages", "contacts", "calls", "media"]:
                assert stats[key] == 0, f"{key} should be 0 for different case"
            db.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_call_stats(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _populated_db(Path(tmp) / "test.db")
            svc = StatisticsService()
            stats = svc.get_call_stats(db, 1)
            assert stats["total"] == 2
            assert stats["incoming"] == 1
            assert stats["outgoing"] == 1
            assert stats["missed"] == 0
            assert stats["video"] == 1
            assert stats["total_duration"] == "7:00"
            db.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_call_stats_empty(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_empty_db(Path(tmp) / "test.db")
            svc = StatisticsService()
            stats = svc.get_call_stats(db, 1)
            assert stats["total"] == 0
            db.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_media_stats(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _populated_db(Path(tmp) / "test.db")
            svc = StatisticsService()
            stats = svc.get_media_stats(db, 1)
            assert stats["total"] == 3
            assert stats["images"] == 1
            assert stats["videos"] == 1
            assert stats["audio"] == 1
            assert stats["orphans"] == 1
            assert stats["missing"] == 1
            db.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_audit_stats(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _populated_db(Path(tmp) / "test.db")
            svc = StatisticsService()
            stats = svc.get_audit_stats(db, 1)
            assert stats["total"] == 1
            db.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_recovery_stats_empty(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_empty_db(Path(tmp) / "test.db")
            svc = StatisticsService()
            stats = svc.get_recovery_stats(db, 1)
            assert stats["total"] == 0
            db.close()
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
