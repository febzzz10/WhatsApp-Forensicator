import zipfile
from pathlib import Path
from typing import Optional

from wft.parsers.exports.text_export_parser import TextExportParser
from wft.parsers.sqlite.sqlite_parser import SQLiteValidator


class ZipExportParser:
    adapter_id = "whatsapp_zip_export"
    adapter_version = "1.0.0"

    _TEXT_PATTERNS = {"_chat.txt", "wa_chat.txt", "chat.txt", "WhatsApp Chat.txt"}
    _DB_PATTERNS = {"msgstore.db", "msgstore.db.crypt12", "msgstore.db.crypt14",
                    "wa.db", "calls.db", "axolotl.db"}

    def __init__(self) -> None:
        self._text_parser = TextExportParser()
        self._sqlite_validator = SQLiteValidator()

    def inspect(self, source: Path) -> dict:
        warnings: list[str] = []
        found_text = False
        found_db = False
        found_media = False
        file_count = 0

        if not source.exists() or not zipfile.is_zipfile(source):
            return {
                "source_type": "WHATSAPP_ZIP_EXPORT",
                "is_valid": False,
                "file_count": 0,
                "warnings": ["Not a valid ZIP file"],
                "schema_fingerprint": None,
            }

        try:
            with zipfile.ZipFile(source, "r") as zf:
                names = zf.namelist()
                file_count = len(names)
                for name in names:
                    lower = name.lower()
                    if any(p in lower for p in self._TEXT_PATTERNS):
                        found_text = True
                    elif any(p in lower for p in self._DB_PATTERNS):
                        found_db = True
                    if lower.endswith((".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3", ".ogg", ".webp", ".opus")):
                        found_media = True
        except Exception as exc:
            warnings.append(f"Cannot read ZIP: {exc}")

        is_valid = found_text or found_db
        if not is_valid:
            warnings.append("No recognised WhatsApp content found in ZIP")

        return {
            "source_type": "WHATSAPP_ZIP_EXPORT",
            "is_valid": is_valid,
            "file_count": file_count,
            "warnings": warnings,
            "schema_fingerprint": None,
            "has_text_export": found_text,
            "has_database": found_db,
            "has_media": found_media,
        }

    def supports(self, inspection: dict) -> bool:
        return inspection.get("is_valid", False)

    def parse(self, source: Path, context: ParseContext) -> dict:
        warnings: list[str] = []
        contacts: list[dict] = []
        messages: list[dict] = []
        media_refs: list[dict] = []
        calls: list[dict] = []
        extracted_files: list[str] = []

        if not zipfile.is_zipfile(source):
            return {"message_count": 0, "contact_count": 0, "group_count": 0,
                    "call_count": 0, "media_count": 0, "warnings": ["Not a valid ZIP"],
                    "parser_version": self.adapter_version, "adapter_id": self.adapter_id,
                    "contacts": [], "messages": [], "media_refs": [], "calls": []}

        with zipfile.ZipFile(source, "r") as zf:
            names = zf.namelist()

            text_file = None
            for name in names:
                lower = name.lower()
                if any(p in lower for p in self._TEXT_PATTERNS):
                    text_file = name
                    break

            if text_file:
                try:
                    text_data = zf.read(text_file)
                    import tempfile
                    tmp = Path(context.working_copy_path) / "_chat.txt"
                    tmp.write_bytes(text_data)
                    result = self._text_parser.parse(tmp, context)
                    contacts = result.get("contacts", [])
                    messages = result.get("messages", [])
                    media_refs = result.get("media_refs", [])
                except Exception as exc:
                    warnings.append(f"Failed to parse text export in ZIP: {exc}")

            for name in names:
                lower = name.lower()
                if lower.endswith((".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3", ".ogg", ".webp", ".opus")):
                    extracted_files.append(name)

        return {
            "message_count": len(messages),
            "contact_count": len(contacts),
            "group_count": 0,
            "call_count": 0,
            "media_count": len(extracted_files) + len(media_refs),
            "warnings": warnings,
            "parser_version": self.adapter_version,
            "adapter_id": self.adapter_id,
            "contacts": contacts,
            "messages": messages,
            "media_refs": media_refs,
            "calls": [],
            "extracted_files": extracted_files,
        }

    def capabilities(self) -> dict:
        return {
            "adapter_id": self.adapter_id,
            "version": self.adapter_version,
            "supported": ["Messages", "System events", "ZIP extraction"],
            "partially_supported": ["Media references"],
            "unsupported": ["Contacts", "Groups", "Calls", "Reactions", "Edits"],
        }
