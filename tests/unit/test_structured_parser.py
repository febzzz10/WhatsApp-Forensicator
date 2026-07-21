import tempfile
from pathlib import Path

import pytest

from wft.parsers.exports.text_export_parser import TextExportParser
from wft.parsers.exports.zip_export_parser import ZipExportParser
from wft.parsers.adapters.whatsapp_sqlite_adapter import WhatsAppSQLiteAdapter


class TestTextExportStructuredOutput:
    def test_parse_returns_contacts_list(self):
        content = (
            "1/15/26, 10:30 AM - Alice: Hello there\n"
            "1/15/26, 10:31 AM - Bob: Hi Alice!\n"
            "1/15/26, 10:32 AM - Alice: How are you?\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_chat.txt"
            path.write_text(content, encoding="utf-8")

            parser = TextExportParser()
            context = DummyContext()
            result = parser.parse(path, context)

            assert result["message_count"] == 3
            assert result["contact_count"] == 2
            assert len(result["contacts"]) == 2
            assert len(result["messages"]) == 3

            contact_codes = {c["display_name"] for c in result["contacts"]}
            assert "Alice" in contact_codes
            assert "Bob" in contact_codes

    def test_parse_marks_direction(self):
        content = (
            "1/15/26, 10:30 AM - You: Hello\n"
            "1/15/26, 10:31 AM - Alice: Hi\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_chat.txt"
            path.write_text(content, encoding="utf-8")

            parser = TextExportParser()
            result = parser.parse(path, DummyContext())

            msgs = result["messages"]
            assert msgs[0]["direction"] == "OUTGOING"
            assert msgs[1]["direction"] == "INCOMING"

    def test_parse_system_events(self):
        content = (
            "1/15/26, 10:30 AM - Alice joined the group\n"
            "1/15/26, 10:31 AM - Messages are end-to-end encrypted\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_chat.txt"
            path.write_text(content, encoding="utf-8")

            parser = TextExportParser()
            result = parser.parse(path, DummyContext())

            assert result["message_count"] == 2
            for m in result["messages"]:
                assert m["direction"] == "SYSTEM"
                assert m["message_type"] == "SYSTEM_EVENT"

    def test_parse_media_references(self):
        content = (
            "1/15/26, 10:30 AM - Alice: <Media omitted>\n"
            "1/15/26, 10:31 AM - Bob: Nice photo!\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_chat.txt"
            path.write_text(content, encoding="utf-8")

            parser = TextExportParser()
            result = parser.parse(path, DummyContext())

            assert result["message_count"] == 2
            assert result["media_count"] == 1
            assert len(result["media_refs"]) == 1
            assert result["media_refs"][0]["is_media"] is True

    def test_parse_timestamp_conversion(self):
        content = "1/15/26, 10:30:15 AM - Alice: Timestamp test\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_chat.txt"
            path.write_text(content, encoding="utf-8")

            parser = TextExportParser()
            result = parser.parse(path, DummyContext())

            m = result["messages"][0]
            assert m["timestamp_raw"] is not None
            assert m["sent_at_utc"] is not None
            assert "T" in m["sent_at_utc"]


class TestWhatsAppSQLiteAdapter:
    def test_inspect_rejects_nonexistent(self):
        adapter = WhatsAppSQLiteAdapter()
        result = adapter.inspect(Path("/nonexistent.db"))
        assert result["is_valid"] is False

    def test_capabilities_returns_expected(self):
        adapter = WhatsAppSQLiteAdapter()
        caps = adapter.capabilities()
        assert "Messages" in caps["supported"]
        assert "Contacts" in caps["supported"]
        assert "Calls" in caps["supported"]

    def test_supports_negative_case(self):
        adapter = WhatsAppSQLiteAdapter()
        assert adapter.supports({"is_valid": False}) is False
        assert adapter.supports({"is_valid": True}) is True


class TestZipExportParser:
    def test_inspect_non_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "not_a_zip.txt"
            path.write_text("hello", encoding="utf-8")
            parser = ZipExportParser()
            result = parser.inspect(path)
            assert result["is_valid"] is False

    def test_inspect_missing_file(self):
        parser = ZipExportParser()
        result = parser.inspect(Path("/nonexistent.zip"))
        assert result["is_valid"] is False

    def test_capabilities(self):
        parser = ZipExportParser()
        caps = parser.capabilities()
        assert "ZIP extraction" in caps["supported"]


class DummyContext:
    case_id = 1
    evidence_item_id = 1
    source_file_id = 1
    working_copy_path = Path("/tmp")
    timezone = "UTC"
