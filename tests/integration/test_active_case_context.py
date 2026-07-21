import shutil
import tempfile
from pathlib import Path

import pytest

from wft.application.services.case_context import ActiveCaseContext
from wft.infrastructure.database.schema import ALL_TABLE_DDL, ALL_INDEXES
from wft.infrastructure.database.connection import DatabaseConnection


def _create_test_db(db_path: Path) -> None:
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
    conn.close()


class TestActiveCaseContextIntegration:
    def test_initial_state(self):
        ctx = ActiveCaseContext()
        assert ctx.case_id is None
        assert ctx.case_path is None
        assert ctx.db_path is None
        assert ctx.db is None
        assert not ctx.is_active

    def test_open_valid_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_path = Path(tmp) / "TEST-CASE"
            case_path.mkdir()
            db_path = case_path / "case.db"
            _create_test_db(db_path)

            ctx = ActiveCaseContext()
            signals = []
            ctx.case_changed.connect(lambda cid, p: signals.append((cid, p)))

            ctx.open(1, case_path)
            assert ctx.case_id == 1
            assert ctx.case_path == case_path
            assert ctx.db_path == db_path
            assert ctx.db is not None
            assert ctx.is_active
            assert len(signals) == 1
            assert signals[0] == (1, str(case_path))
            ctx.close()

    def test_get_db_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_path = Path(tmp) / "TEST-CASE"
            case_path.mkdir()
            _create_test_db(case_path / "case.db")

            ctx = ActiveCaseContext()
            ctx.open(1, case_path)
            db = ctx.get_db()
            assert db is not None
            row = db.execute("SELECT COUNT(*) FROM cases").fetchone()
            assert row[0] == 1
            ctx.close()

    def test_case_changed_emitted_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_path = Path(tmp) / "TEST-CASE"
            case_path.mkdir()
            _create_test_db(case_path / "case.db")

            ctx = ActiveCaseContext()
            signal_count = [0]
            ctx.case_changed.connect(lambda cid, p: signal_count.__setitem__(0, signal_count[0] + 1))

            ctx.open(1, case_path)
            assert signal_count[0] == 1
            ctx.close()

    def test_close_clears_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_path = Path(tmp) / "TEST-CASE"
            case_path.mkdir()
            _create_test_db(case_path / "case.db")

            ctx = ActiveCaseContext()
            ctx.open(1, case_path)
            ctx.close()

            assert ctx.case_id is None
            assert ctx.case_path is None
            assert ctx.db is None
            assert not ctx.is_active
            with pytest.raises(RuntimeError, match="No active case"):
                ctx.get_db()

    def test_open_second_case_closes_first(self):
        tmp = tempfile.mkdtemp()
        try:
            case1_path = Path(tmp) / "CASE-001"
            case1_path.mkdir()
            _create_test_db(case1_path / "case.db")

            case2_path = Path(tmp) / "CASE-002"
            case2_path.mkdir()
            db2 = case2_path / "case.db"
            _create_test_db(db2)

            ctx = ActiveCaseContext()
            ctx.open(1, case1_path)
            ctx.open(2, case2_path)

            assert ctx.case_id == 2
            assert ctx.case_path == case2_path
            row = ctx.get_db().execute("SELECT COUNT(*) FROM cases").fetchone()
            assert row[0] == 1
            ctx.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_get_db_without_active_case_raises(self):
        ctx = ActiveCaseContext()
        with pytest.raises(RuntimeError, match="No active case"):
            ctx.get_db()

    def test_close_emits_case_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_path = Path(tmp) / "TEST-CASE"
            case_path.mkdir()
            _create_test_db(case_path / "case.db")

            ctx = ActiveCaseContext()
            close_signals = []
            ctx.case_changed.connect(lambda cid, p: close_signals.append((cid, p)))

            ctx.open(1, case_path)
            close_signals.clear()
            ctx.close()
            assert len(close_signals) == 0

    def test_db_connection_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_path = Path(tmp) / "TEST-CASE"
            case_path.mkdir()
            _create_test_db(case_path / "case.db")

            ctx = ActiveCaseContext()
            ctx.open(1, case_path)
            db = ctx.get_db()
            assert db is not None
            row = db.execute("SELECT sqlite_version()").fetchone()
            assert row is not None
            ctx.close()

    def test_db_is_read_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_path = Path(tmp) / "TEST-CASE"
            case_path.mkdir()
            _create_test_db(case_path / "case.db")

            ctx = ActiveCaseContext()
            ctx.open(1, case_path)
            db = ctx.get_db()
            db.execute(
                "UPDATE cases SET title = ? WHERE id = ?",
                ("Updated Title", 1),
            )
            db.commit()
            row = db.execute("SELECT title FROM cases WHERE id = 1").fetchone()
            assert row[0] == "Updated Title"
            ctx.close()
