import sqlite3
import tempfile
from pathlib import Path

import pytest


def _create_test_db(db_path: Path) -> sqlite3.Connection:
    """Create a fully initialised case DB with required FK rows."""
    from wft.infrastructure.database.schema import ALL_TABLE_DDL, ALL_INDEXES

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = OFF")
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
        "VALUES (1, 'E001', 'Test Evidence', 'TEST', 'IMPORT', 'VERIFIED', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO evidence_files (evidence_item_id, file_code, original_filename, stored_relative_path, "
        "size_bytes, imported_at_utc, created_at_utc, updated_at_utc) "
        "VALUES (1, 'F001', 'test.txt', 'originals/E0001/test.txt', 100, "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    return conn


@pytest.fixture
def db_conn():
    """Yield an open connection; test recvs the DB path and manages conn."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        conn = _create_test_db(db_path)
        yield db_path, conn
        conn.close()


class TestContactRepository:
    def test_create_and_get(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ContactRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ContactRepository(db)

        cid = repo.create(1, {
            "contact_code": "CONTACT-TEST",
            "whatsapp_identifier": "1234567890@s.whatsapp.net",
            "display_name": "Test Contact",
            "origin": "PARSED",
        })
        assert cid > 0

        row = db.execute("SELECT * FROM contacts WHERE id = ?", (cid,)).fetchone()
        assert row is not None
        assert dict(row)["display_name"] == "Test Contact"

    def test_get_by_wa_id(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ContactRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ContactRepository(db)
        repo.create(1, {
            "contact_code": "CONTACT-ONE",
            "whatsapp_identifier": "wa_id_001",
            "display_name": "One",
        })
        found = repo.get_by_wa_id(1, "wa_id_001")
        assert found is not None
        assert found["display_name"] == "One"

    def test_upsert_by_wa_id_creates_new(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ContactRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ContactRepository(db)
        cid = repo.upsert_by_wa_id(1, {
            "contact_code": "CONTACT-NEW",
            "whatsapp_identifier": "wa_new",
            "display_name": "New Contact",
        })
        assert cid > 0

    def test_upsert_by_wa_id_updates_existing(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ContactRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ContactRepository(db)
        cid1 = repo.upsert_by_wa_id(1, {
            "contact_code": "CONTACT-EXISTING",
            "whatsapp_identifier": "wa_existing",
            "display_name": "Old Name",
        })
        cid2 = repo.upsert_by_wa_id(1, {
            "contact_code": "CONTACT-EXISTING",
            "whatsapp_identifier": "wa_existing",
            "display_name": "New Name",
        })
        assert cid1 == cid2
        row = db.execute("SELECT * FROM contacts WHERE id = ?", (cid1,)).fetchone()
        assert dict(row)["display_name"] == "New Name"

    def test_list_for_case(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ContactRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ContactRepository(db)
        repo.create(1, {"contact_code": "C-A", "display_name": "Alpha"})
        repo.create(1, {"contact_code": "C-B", "display_name": "Beta"})
        items = repo.list_for_case(1)
        assert len(items) >= 2


class TestMessageRepository:
    def test_create_and_count(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import (
            ContactRepository, ConversationRepository, MessageRepository,
        )

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row

        crepo = ContactRepository(db)
        cid = crepo.create(1, {
            "contact_code": "CONTACT-MSG-SENDER",
            "display_name": "Sender",
        })

        conv_repo = ConversationRepository(db)
        conv_id = conv_repo.create(1, {
            "conversation_code": "CONV-MSG-TEST",
            "conversation_type": "DIRECT",
            "contact_id": cid,
            "title": "Test Conversation",
        })

        mrepo = MessageRepository(db)
        msg_id = mrepo.create(1, {
            "message_code": "MSG-00000001",
            "conversation_id": conv_id,
            "sender_contact_id": cid,
            "direction": "INCOMING",
            "message_type": "TEXT",
            "text_content": "Hello, world!",
            "sent_at_utc": "2026-01-01T12:00:00Z",
            "origin": "PARSED",
        })
        assert msg_id > 0
        assert mrepo.count_for_conversation(conv_id) == 1


class TestParserRunRepository:
    def test_create_and_complete(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ParserRunRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ParserRunRepository(db)

        rid = repo.create({
            "case_id": 1,
            "evidence_item_id": 1,
            "source_evidence_file_id": 1,
            "parser_name": "test_parser",
            "parser_version": "1.0.0",
            "adapter_id": "test_adapter",
            "adapter_version": "1.0.0",
        })
        assert rid > 0

        repo.complete(rid, "COMPLETED", 100, 2, 0)
        row = db.execute("SELECT * FROM parser_runs WHERE id = ?", (rid,)).fetchone()
        assert row is not None
        assert dict(row)["status"] == "COMPLETED"
        assert dict(row)["parsed_record_count"] == 100

    def test_add_warning(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ParserRunRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ParserRunRepository(db)

        rid = repo.create({
            "case_id": 1, "evidence_item_id": 1, "source_evidence_file_id": 1,
            "parser_name": "test", "parser_version": "1.0",
            "adapter_id": "t", "adapter_version": "1.0",
        })
        wid = repo.add_warning({
            "parser_run_id": rid,
            "warning_code": "PARSE_WARNING",
            "severity": "WARNING",
            "message": "Test warning",
        })
        assert wid > 0

    def test_add_mapping(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ParserRunRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ParserRunRepository(db)

        rid = repo.create({
            "case_id": 1, "evidence_item_id": 1, "source_evidence_file_id": 1,
            "parser_name": "test", "parser_version": "1.0",
            "adapter_id": "t", "adapter_version": "1.0",
        })
        mid = repo.add_mapping({
            "parser_run_id": rid,
            "source_table": "wa_contacts",
            "source_column": "display_name",
            "internal_entity": "contact",
            "internal_field": "display_name",
        })
        assert mid > 0

    def test_add_timeline_event(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import ParserRunRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = ParserRunRepository(db)

        eid = repo.add_timeline_event({
            "case_id": 1,
            "event_code": "TL-001",
            "event_type": "MESSAGE",
            "title": "Test event",
            "occurred_at_utc": "2026-01-01T12:00:00Z",
            "origin": "PARSED",
        })
        assert eid > 0


class TestMediaRepository:
    def test_create(self, db_conn):
        db_path, conn = db_conn
        from wft.infrastructure.database.connection import DatabaseConnection
        from wft.infrastructure.database.artefact_repositories import MediaRepository

        db = DatabaseConnection(db_path)
        db._conn = conn
        db._conn.row_factory = sqlite3.Row
        repo = MediaRepository(db)

        mid = repo.create(1, {
            "media_code": "MEDIA-00000001",
            "original_filename": "photo.jpg",
            "declared_mime_type": "image/jpeg",
            "size_bytes": 1024,
            "origin": "PARSED",
        })
        assert mid > 0
        row = db.execute("SELECT * FROM media_items WHERE id = ?", (mid,)).fetchone()
        assert dict(row)["media_code"] == "MEDIA-00000001"
