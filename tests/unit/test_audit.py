import tempfile
from pathlib import Path

import pytest

from wft.application.services.audit_service import AuditService
from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.schema import CREATE_AUDIT_EVENTS, CREATE_CASES, CREATE_EXAMINERS


class TestAuditService:
    @pytest.fixture
    def db(self) -> DatabaseConnection:
        tmp = Path(tempfile.mktemp(suffix=".db"))
        conn = DatabaseConnection(tmp)
        conn.execute(CREATE_CASES)
        conn.execute(CREATE_EXAMINERS)
        conn.execute(CREATE_AUDIT_EVENTS)
        conn.execute(
            "INSERT INTO cases (case_code, title, status, display_timezone, created_at_utc, updated_at_utc) "
            "VALUES ('TEST-001', 'Test Case', 'OPEN', 'UTC', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO examiners (case_id, examiner_code, full_name, is_primary, created_at_utc, updated_at_utc) "
            "VALUES (1, 'EXAM-001', 'Test Examiner', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
        )
        conn.commit()
        return conn

    def test_record_and_verify_chain(self, db: DatabaseConnection) -> None:
        audit = AuditService()
        h1 = audit.record_event(db, 1, "CASE_CREATED", "Test case created", component_name="test")
        h2 = audit.record_event(db, 1, "EVIDENCE_IMPORTED", "Imported test file", component_name="test")
        h3 = audit.record_event(db, 1, "PARSER_RUN", "Parsed evidence", component_name="test")

        assert h1 != h2
        assert h2 != h3
        assert len(h1) == 64
        assert len(h2) == 64
        assert len(h3) == 64

        issues = audit.verify_chain(db, 1)
        assert issues == []

    def test_tampered_chain_detected(self, db: DatabaseConnection) -> None:
        audit = AuditService()
        audit.record_event(db, 1, "CASE_CREATED", "Test case", component_name="test")
        audit.record_event(db, 1, "EVIDENCE_IMPORTED", "Imported", component_name="test")

        db.execute("UPDATE audit_events SET event_description = 'TAMPERED' WHERE event_sequence = 1")
        db.commit()

        issues = audit.verify_chain(db, 1)
        assert len(issues) > 0
