import tempfile
from pathlib import Path

import pytest

from wft.parsers.exports.text_export_parser import TextExportParser


class TestTextExportParser:
    @pytest.fixture
    def parser(self) -> TextExportParser:
        return TextExportParser()

    def test_inspect_valid_export(self, parser: TextExportParser) -> None:
        content = (
            "7/19/26, 10:30 AM - Alice: Hello Bob!\n"
            "7/19/26, 10:31 AM - Bob: Hey Alice! How are you?\n"
            "7/19/26, 10:32 AM - Alice: I'm good, thanks!\n"
            "7/19/26, 10:33 AM - System: Alice created this group\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
            f.write(content)
            tmp = Path(f.name)
        try:
            result = parser.inspect(tmp)
            assert result["is_valid"] is True
            assert result["valid_lines"] >= 3
            assert result["source_type"] == "WHATSAPP_TEXT_EXPORT"
        finally:
            tmp.unlink()

    def test_inspect_invalid_file(self, parser: TextExportParser) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"this is not a whatsapp export\njust random text")
            tmp = Path(f.name)
        try:
            result = parser.inspect(tmp)
            assert result["is_valid"] is False
        finally:
            tmp.unlink()

    def test_parse_counts_messages(self, parser: TextExportParser) -> None:
        content = (
            "7/19/26, 10:30 AM - Alice: Message one\n"
            "7/19/26, 10:31 AM - Bob: Message two\n"
            "7/19/26, 10:32 AM - Alice: <Media omitted>\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
            f.write(content)
            tmp = Path(f.name)
        try:
            ctx = {
                "case_id": 1,
                "evidence_item_id": 1,
                "source_file_id": 1,
                "working_copy_path": tmp,
                "timezone": "UTC",
            }
            result = parser.parse(tmp, ctx)
            assert result["message_count"] == 3
        finally:
            tmp.unlink()

    def test_capabilities(self, parser: TextExportParser) -> None:
        caps = parser.capabilities()
        assert "Messages" in caps["supported"]
        assert "System events" in caps["supported"]
