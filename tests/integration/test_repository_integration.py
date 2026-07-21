import shutil
import tempfile
from pathlib import Path

import pytest

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.schema import ALL_TABLE_DDL, ALL_INDEXES
from wft.infrastructure.database.artefact_repositories import (
    ContactRepository,
    ConversationRepository,
    MessageRepository,
    CallRepository,
    MediaRepository,
    TimelineEventRepository,
    AuditEventRepository,
    ReportRunRepository,
)


def _create_db(db_path: Path) -> DatabaseConnection:
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
        "VALUES (1, 'E001', 'test.txt', 'TEST', 'IMPORT', 'VERIFIED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO evidence_files (evidence_item_id, file_code, original_filename, stored_relative_path, "
        "size_bytes, imported_at_utc, created_at_utc, updated_at_utc) "
        "VALUES (1, 'F001', 'test.txt', 'originals/E0001/test.txt', 100, "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    return conn


class TestConversationRepository:
    def test_create_and_list(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            contact_repo = ContactRepository(db)
            contact_id = contact_repo.create(1, {
                "contact_code": "CONTACT-CONV", "display_name": "Alice", "origin": "PARSED",
            })
            repo = ConversationRepository(db)
            cid = repo.create(1, {
                "conversation_code": "CONV-001",
                "conversation_type": "DIRECT",
                "contact_id": contact_id,
                "title": "Test Chat",
                "origin": "PARSED",
            })
            assert cid > 0
            items = repo.list_for_case(1)
            assert len(items) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_list_with_stats(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            contact_repo = ContactRepository(db)
            cid = contact_repo.create(1, {
                "contact_code": "CONTACT-001", "display_name": "Alice", "origin": "PARSED",
            })
            conv_repo = ConversationRepository(db)
            conv_id = conv_repo.create(1, {
                "conversation_code": "CONV-STATS", "conversation_type": "DIRECT",
                "contact_id": cid, "title": "Stats Test", "origin": "PARSED",
            })
            msg_repo = MessageRepository(db)
            msg_repo.create(1, {
                "message_code": "MSG-STATS-1", "conversation_id": conv_id,
                "direction": "INCOMING", "message_type": "TEXT", "text_content": "Hi",
                "sent_at_utc": "2026-01-01T12:00:00Z", "origin": "PARSED",
            })
            msg_repo.create(1, {
                "message_code": "MSG-STATS-2", "conversation_id": conv_id,
                "direction": "OUTGOING", "message_type": "TEXT", "text_content": "Hello",
                "sent_at_utc": "2026-01-01T12:01:00Z", "origin": "PARSED",
            })
            stats = conv_repo.list_with_stats(1)
            assert len(stats) >= 1
            s = stats[0]
            assert s.get("actual_message_count", 0) >= 2
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_case_isolation(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = ConversationRepository(db)
            items = repo.list_for_case(999)
            assert len(items) == 0
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_get_by_source_id(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            contact_repo = ContactRepository(db)
            contact_id = contact_repo.create(1, {
                "contact_code": "CONTACT-SRC", "display_name": "Bob", "origin": "PARSED",
            })
            repo = ConversationRepository(db)
            cid = repo.create(1, {
                "conversation_code": "CONV-SRC", "conversation_type": "DIRECT",
                "contact_id": contact_id,
                "source_conversation_identifier": "abc123", "origin": "PARSED",
            })
            found = repo.get_by_source_id(1, "abc123")
            assert found is not None
            assert found["id"] == cid
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestCallRepository:
    def test_list_for_case(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = CallRepository(db)
            cid = repo.create(1, {
                "call_code": "CALL-001", "call_type": "VOICE", "direction": "INCOMING",
                "started_at_utc": "2026-01-01T12:00:00Z", "duration_seconds": 60,
                "origin": "PARSED", "validation_status": "VALIDATED",
            })
            assert cid > 0
            calls = repo.list_for_case(1)
            assert len(calls) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_list_filtered_by_type(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = CallRepository(db)
            repo.create(1, {"call_code": "CALL-V", "call_type": "VOICE", "direction": "INCOMING",
                           "started_at_utc": "2026-01-01T12:00:00Z", "origin": "PARSED", "validation_status": "VALIDATED"})
            repo.create(1, {"call_code": "CALL-VD", "call_type": "VIDEO", "direction": "OUTGOING",
                           "started_at_utc": "2026-01-01T13:00:00Z", "origin": "PARSED", "validation_status": "VALIDATED"})
            voice = repo.list_filtered(1, call_type="VOICE")
            assert len(voice) == 1
            incoming = repo.list_filtered(1, direction="INCOMING")
            assert len(incoming) == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_case_isolation(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = CallRepository(db)
            calls = repo.list_for_case(999)
            assert len(calls) == 0
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestMediaRepository:
    def test_list_for_case(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = MediaRepository(db)
            mid = repo.create(1, {
                "media_code": "MEDIA-001", "original_filename": "test.jpg",
                "declared_mime_type": "image/jpeg", "size_bytes": 1024, "origin": "PARSED",
            })
            assert mid > 0
            items = repo.list_for_case(1)
            assert len(items) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_list_filtered(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = MediaRepository(db)
            repo.create(1, {"media_code": "MEDIA-IMG", "original_filename": "img.jpg",
                           "declared_mime_type": "image/jpeg", "origin": "PARSED"})
            repo.create(1, {"media_code": "MEDIA-VID", "original_filename": "vid.mp4",
                           "declared_mime_type": "video/mp4", "origin": "PARSED", "is_orphan": 1})
            images = repo.list_filtered(1, "Images")
            assert len(images) == 1
            orphans = repo.list_filtered(1, "Orphans")
            assert len(orphans) == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_media(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = MediaRepository(db)
            repo.create(1, {"media_code": "MEDIA-MISS", "original_filename": "lost.jpg",
                           "declared_mime_type": "image/jpeg", "origin": "PARSED", "is_missing": 1})
            missing = repo.list_filtered(1, "Missing")
            assert len(missing) == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestTimelineEventRepository:
    def test_list_for_case(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = TimelineEventRepository(db)
            db.execute(
                "INSERT INTO timeline_events (case_id, event_code, event_type, title, origin, confidence_level, created_at_utc) "
                "VALUES (1, 'TL-001', 'MESSAGE', 'Test event', 'PARSED', 'HIGH', '2026-01-01T00:00:00Z')"
            )
            db.commit()
            events = repo.list_for_case(1)
            assert len(events) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestAuditEventRepository:
    def test_list_for_case(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = AuditEventRepository(db)
            db.execute(
                "INSERT INTO audit_events (case_id, event_sequence, event_type, event_description, "
                "component_name, component_version, event_hash, occurred_at_utc, created_at_utc) "
                "VALUES (1, 1, 'TEST', 'Test event', 'test', '1.0.0', 'a'*64, "
                "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
            )
            db.commit()
            events = repo.list_for_case(1)
            assert len(events) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_get_chain(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = AuditEventRepository(db)
            db.execute(
                "INSERT INTO audit_events (case_id, event_sequence, event_type, event_description, "
                "component_name, component_version, event_hash, previous_event_hash, occurred_at_utc, created_at_utc) "
                "VALUES (1, 1, 'TEST', 'First', 'test', '1.0.0', 'aaaa', NULL, "
                "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
            )
            db.execute(
                "INSERT INTO audit_events (case_id, event_sequence, event_type, event_description, "
                "component_name, component_version, event_hash, previous_event_hash, occurred_at_utc, created_at_utc) "
                "VALUES (1, 2, 'TEST', 'Second', 'test', '1.0.0', 'bbbb', 'aaaa', "
                "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
            )
            db.commit()
            chain = repo.get_chain(1)
            assert len(chain) == 2
            assert chain[0]["event_hash"] == "aaaa"
            assert chain[1]["previous_event_hash"] == "aaaa"
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestReportRunRepository:
    def test_create_and_complete(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = ReportRunRepository(db)
            rid = repo.create({
                "case_id": 1, "report_code": "R-001", "title": "Test Report",
                "report_type": "CASE_SUMMARY",
            })
            assert rid > 0
            repo.complete(rid, "COMPLETED")
            row = db.execute("SELECT * FROM report_runs WHERE id = ?", (rid,)).fetchone()
            assert row["status"] == "COMPLETED"
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_add_file(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = ReportRunRepository(db)
            rid = repo.create({
                "case_id": 1, "report_code": "R-FILE", "title": "Test",
                "report_type": "CASE_SUMMARY",
            })
            fid = repo.add_file({
                "report_run_id": rid, "file_format": "html",
                "stored_relative_path": "reports/test.html", "size_bytes": 100, "sha256": "abcd",
            })
            assert fid > 0
            files = db.execute("SELECT * FROM report_files WHERE report_run_id = ?", (rid,)).fetchall()
            assert len(files) == 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_list_for_case(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = ReportRunRepository(db)
            repo.create({
                "case_id": 1, "report_code": "R-LIST", "title": "List Test",
                "report_type": "CASE_SUMMARY",
            })
            reports = repo.list_for_case(1)
            assert len(reports) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_incomplete_handling(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = ReportRunRepository(db)
            repo.create({
                "case_id": 1, "report_code": "R-INCOMPLETE", "title": "Incomplete",
                "report_type": "CASE_SUMMARY",
            })
            reports = repo.list_for_case(1)
            started = [r for r in reports if r["status"] == "STARTED"]
            assert len(started) >= 1
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_fail_report(self):
        tmp = tempfile.mkdtemp()
        try:
            db = _create_db(Path(tmp) / "test.db")
            repo = ReportRunRepository(db)
            rid = repo.create({
                "case_id": 1, "report_code": "R-FAIL", "title": "Fail Test",
                "report_type": "CASE_SUMMARY",
            })
            repo.complete(rid, "FAILED", "Something went wrong")
            row = db.execute("SELECT * FROM report_runs WHERE id = ?", (rid,)).fetchone()
            assert row["status"] == "FAILED"
            assert row["error_summary"] == "Something went wrong"
            db.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
