import shutil
import tempfile
from pathlib import Path

import pytest

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.schema import ALL_TABLE_DDL, ALL_INDEXES
from wft.application.services.search_service import SearchService
from wft.application.services.search_index_service import SearchIndexService


def _create_search_db(db_path: Path) -> DatabaseConnection:
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
        "INSERT INTO contacts (case_id, contact_code, display_name, phone_number_raw, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CONTACT-001', 'Alice Smith', '+1-555-0101', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO contacts (case_id, contact_code, display_name, phone_number_raw, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CONTACT-002', 'Bob Jones', '+1-555-0102', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO conversations (case_id, conversation_code, conversation_type, contact_id, title, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CONV-001', 'DIRECT', 1, 'Alice Chat', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO conversations (case_id, conversation_code, conversation_type, contact_id, title, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CONV-002', 'DIRECT', 2, 'Bob Chat', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO messages (case_id, message_code, conversation_id, direction, message_type, text_content, "
        "sent_at_utc, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MSG-001', 1, 'INCOMING', 'TEXT', 'Hello Alice here', "
        "'2026-01-01T12:00:00Z', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO messages (case_id, message_code, conversation_id, direction, message_type, text_content, "
        "sent_at_utc, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MSG-002', 2, 'OUTGOING', 'TEXT', 'Hi Bob how are you', "
        "'2026-01-01T12:01:00Z', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO messages (case_id, message_code, conversation_id, direction, message_type, text_content, "
        "sent_at_utc, origin, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MSG-003', 1, 'OUTGOING', 'TEXT', 'Check this link https://example.com', "
        "'2026-01-01T12:02:00Z', 'PARSED', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO calls (case_id, call_code, conversation_id, call_type, direction, started_at_utc, "
        "duration_seconds, was_answered, origin, confidence_level, validation_status, created_at_utc, updated_at_utc) "
        "VALUES (1, 'CALL-001', 1, 'VOICE', 'INCOMING', '2026-01-01T13:00:00Z', 120, 1, 'PARSED', 'HIGH', 'VALIDATED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO media_items (case_id, media_code, original_filename, sha256, declared_mime_type, "
        "origin, confidence_level, created_at_utc, updated_at_utc) "
        "VALUES (1, 'MEDIA-001', 'photo.jpg', 'abcd1234', 'image/jpeg', 'PARSED', 'HIGH', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO examiner_notes (case_id, note_text, created_at_utc, updated_at_utc) "
        "VALUES (1, 'Important finding about Alice', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    SearchIndexService().create_index(conn)
    return conn


class TestSearchServiceIntegration:
    def test_empty_query(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "")
            assert results == []
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_search_messages(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "Alice", scope="Messages")
            assert len(results) >= 1
            assert any("Alice" in r.get("text_content", "") for r in results)
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_search_contacts(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "Smith", scope="Contacts")
            assert len(results) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_search_media(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "photo", scope="Media")
            assert len(results) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_search_calls(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "CALL-001", scope="Calls")
            assert len(results) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_search_notes(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "Alice", scope="Notes")
            assert len(results) >= 1
            assert results[0].get("result_type") == "note"
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_case_isolation(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 999, "Alice", scope="Messages")
            assert len(results) == 0
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_search_all_scopes(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "Alice", scope="All")
            assert len(results) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_invalid_scope(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "Alice", scope="NonExistent")
            assert results == []
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_special_chars(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "https://", scope="Messages")
            assert len(results) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_sql_wildcard_escaping(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "%", scope="Messages")
            assert isinstance(results, list)
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_phone_number_search(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_search_db(Path(tmp) / "test.db")
            svc = SearchService()
            results = svc.search(db, 1, "0101", scope="Contacts")
            assert len(results) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
