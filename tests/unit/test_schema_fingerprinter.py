import sqlite3
import tempfile
from pathlib import Path

import pytest

from wft.parsers.sqlite.schema_fingerprinter import (
    SchemaFingerprinter,
    SchemaFingerprint,
    SchemaRegistry,
    SchemaRegistryEntry,
    build_default_registry,
)


class TestSchemaFingerprinter:
    def test_fingerprint_returns_none_for_missing_file(self):
        fp = SchemaFingerprinter()
        result = fp.fingerprint(Path("/nonexistent/foo.db"))
        assert result is None

    def test_fingerprint_captures_tables_and_ddl(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            path = Path(tmp.name) / "test.db"
            conn = sqlite3.connect(str(path))
            conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, text TEXT)")
            conn.execute("CREATE TABLE wa_contacts (jid TEXT, display_name TEXT)")
            conn.execute("CREATE INDEX idx_messages_id ON messages(id)")
            conn.close()

            fp = SchemaFingerprinter()
            result = fp.fingerprint(path)
            assert result is not None
            assert isinstance(result, SchemaFingerprint)
            assert result.table_count == 2
            assert result.index_count == 1
            assert "messages" in result.tables
            assert "wa_contacts" in result.tables
            assert len(result.fingerprint_sha256) == 64
        finally:
            tmp.cleanup()

    def test_fingerprint_deterministic(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            def make_db(name: str):
                p = Path(tmp.name) / name
                c = sqlite3.connect(str(p))
                c.execute("CREATE TABLE t1 (a INTEGER)")
                c.execute("CREATE TABLE t2 (b TEXT)")
                c.close()
                return p

            p1 = make_db("a.db")
            p2 = make_db("b.db")

            fp1 = SchemaFingerprinter().fingerprint(p1)
            fp2 = SchemaFingerprinter().fingerprint(p2)
            assert fp1 is not None
            assert fp2 is not None
            assert fp1.fingerprint_sha256 == fp2.fingerprint_sha256
        finally:
            tmp.cleanup()

    def test_fingerprint_empty_db(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            path = Path(tmp.name) / "empty.db"
            conn = sqlite3.connect(str(path))
            conn.close()

            result = SchemaFingerprinter().fingerprint(path)
            assert result is not None
            assert result.table_count == 0
        finally:
            tmp.cleanup()


class TestSchemaRegistry:
    def test_register_and_lookup(self):
        reg = SchemaRegistry()
        entry = SchemaRegistryEntry(
            fingerprint_sha256="abc123",
            whatsapp_version_min="2.22.0",
            whatsapp_version_max="2.24.x",
            adapter_id="whatsapp_sqlite_v1",
            description="Test entry",
            tables_expected=["messages", "wa_contacts"],
        )
        reg.register(entry)

        fp = SchemaFingerprint(fingerprint_sha256="abc123", table_count=2, index_count=0, tables=["messages", "wa_contacts"])
        found = reg.lookup(fp)
        assert found is not None
        assert found.adapter_id == "whatsapp_sqlite_v1"

    def test_lookup_nonexistent(self):
        reg = SchemaRegistry()
        fp = SchemaFingerprint(fingerprint_sha256="nope", table_count=0, index_count=0, tables=[])
        assert reg.lookup(fp) is None

    def test_build_default_registry(self):
        reg = SchemaRegistry()
        build_default_registry(reg)
        assert len(reg.entries()) >= 2

    def test_match_partial(self):
        reg = SchemaRegistry()
        reg.register(SchemaRegistryEntry(
            fingerprint_sha256="",
            whatsapp_version_min="1.0",
            whatsapp_version_max="2.0",
            adapter_id="test_adapter",
            description="",
            tables_expected=["messages", "wa_contacts", "calls_table"],
        ))

        fp = SchemaFingerprint(fingerprint_sha256="", table_count=3, index_count=0,
                                tables=["messages", "wa_contacts", "calls_table"])
        matches = reg.match_partial(fp)
        assert len(matches) >= 1
        assert matches[0].adapter_id == "test_adapter"
