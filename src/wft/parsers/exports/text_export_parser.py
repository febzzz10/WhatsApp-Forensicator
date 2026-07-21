import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from wft.parsers.contracts.interfaces import InspectionResult, ParseContext, ParseResult


class TextExportParser:
    adapter_id = "whatsapp_text_export"
    adapter_version = "1.0.0"

    _LINE_PATTERN = re.compile(
        r"^(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\s*-\s*(.+?):\s*(.+)$"
    )
    _SYSTEM_PATTERN = re.compile(
        r"^(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\s*-\s*(.+)$"
    )
    _MEDIA_PATTERN = re.compile(r"<Media omitted>", re.IGNORECASE)
    _PHONE_PATTERN = re.compile(r"^\+?\d{7,15}$")
    _TIMESTAMP_FORMATS = [
        "%m/%d/%y, %I:%M:%S %p",
        "%m/%d/%y, %I:%M %p",
        "%m/%d/%y, %H:%M:%S",
        "%m/%d/%y, %H:%M",
        "%m/%d/%Y, %I:%M:%S %p",
        "%m/%d/%Y, %I:%M %p",
        "%m/%d/%Y, %H:%M:%S",
        "%m/%d/%Y, %H:%M",
    ]

    def __init__(self) -> None:
        self._seen_senders: dict[str, str] = {}

    def _parse_timestamp(self, raw: str) -> Optional[str]:
        for fmt in self._TIMESTAMP_FORMATS:
            try:
                dt = datetime.strptime(raw.strip(), fmt)
                return dt.replace(tzinfo=timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
            except ValueError:
                continue
        return None

    def inspect(self, source: Path) -> dict:
        warnings: list[str] = []
        line_count = 0
        valid_lines = 0
        try:
            text = source.read_text("utf-8", errors="replace")
            lines = text.splitlines()
            line_count = len(lines)
            for line in lines[:100]:
                if self._LINE_PATTERN.match(line) or self._SYSTEM_PATTERN.match(line):
                    valid_lines += 1
        except Exception as exc:
            warnings.append(f"Cannot read file: {exc}")

        return {
            "source_type": "WHATSAPP_TEXT_EXPORT",
            "is_valid": valid_lines > 0,
            "file_count": 1,
            "warnings": warnings,
            "schema_fingerprint": None,
            "total_lines": line_count,
            "valid_lines": valid_lines,
        }

    def supports(self, inspection: dict) -> bool:
        return inspection.get("is_valid", False) and inspection.get("valid_lines", 0) > 0

    def parse(self, source: Path, context: ParseContext) -> dict:
        warnings: list[str] = []
        contacts: dict[str, dict] = {}
        messages: list[dict] = []
        media_refs: list[dict] = []
        calls: list[dict] = []

        text = source.read_text("utf-8", errors="replace")
        lines = text.splitlines()
        self._seen_senders = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            m = self._LINE_PATTERN.match(line)
            if m:
                ts_raw = m.group(1)
                sender = m.group(2).strip()
                text_content = m.group(3).strip()
                ts_utc = self._parse_timestamp(ts_raw)

                sender_code = f"CONTACT-{sender.replace(' ', '_').upper()}"
                if sender and sender not in self._seen_senders:
                    is_phone = bool(self._PHONE_PATTERN.match(sender))
                    contacts[sender_code] = {
                        "contact_code": sender_code,
                        "display_name": sender,
                        "whatsapp_identifier": sender if is_phone else None,
                        "phone_number_raw": sender if is_phone else None,
                        "origin": "PARSED",
                    }
                    self._seen_senders[sender] = sender_code

                is_media = bool(self._MEDIA_PATTERN.match(text_content))
                if is_media:
                    media_refs.append({
                        "message_code": f"MSG-{len(messages)+1:08d}",
                        "sender_code": sender_code,
                        "sender_name": sender,
                        "text_content": text_content,
                        "timestamp_raw": ts_raw,
                        "sent_at_utc": ts_utc,
                        "is_media": True,
                    })

                messages.append({
                    "message_code": f"MSG-{len(messages)+1:08d}",
                    "sender_code": sender_code,
                    "sender_name": sender,
                    "text_content": text_content,
                    "timestamp_raw": ts_raw,
                    "sent_at_utc": ts_utc,
                    "direction": "OUTGOING" if sender.lower() == "you" else "INCOMING",
                    "message_type": "TEXT",
                    "origin": "PARSED",
                    "is_media": is_media,
                })
                continue

            m = self._SYSTEM_PATTERN.match(line)
            if m:
                ts_raw = m.group(1)
                text_content = m.group(2).strip()
                ts_utc = self._parse_timestamp(ts_raw)

                messages.append({
                    "message_code": f"MSG-{len(messages)+1:08d}",
                    "sender_code": None,
                    "sender_name": None,
                    "text_content": text_content,
                    "timestamp_raw": ts_raw,
                    "sent_at_utc": ts_utc,
                    "direction": "SYSTEM",
                    "message_type": "SYSTEM_EVENT",
                    "origin": "PARSED",
                    "is_media": False,
                })

        return {
            "message_count": len(messages),
            "contact_count": len(contacts),
            "group_count": 0,
            "call_count": 0,
            "media_count": len(media_refs),
            "warnings": warnings,
            "parser_version": self.adapter_version,
            "adapter_id": self.adapter_id,
            "contacts": list(contacts.values()),
            "messages": messages,
            "media_refs": media_refs,
            "calls": [],
        }

    def capabilities(self) -> dict:
        return {
            "adapter_id": self.adapter_id,
            "version": self.adapter_version,
            "supported": ["Messages", "System events"],
            "partially_supported": ["Media references"],
            "unsupported": ["Contacts", "Groups", "Calls", "Reactions", "Edits"],
        }
