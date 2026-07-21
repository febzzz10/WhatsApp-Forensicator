import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import sqlite3


@dataclass
class SchemaFingerprint:
    fingerprint_sha256: str
    table_count: int
    index_count: int
    tables: list[str]


@dataclass
class SchemaRegistryEntry:
    fingerprint_sha256: str
    whatsapp_version_min: str
    whatsapp_version_max: str
    adapter_id: str
    description: str
    tables_expected: list[str]


class SchemaFingerprinter:
    def fingerprint(self, db_path: Path) -> Optional[SchemaFingerprint]:
        if not db_path.exists():
            return None
        try:
            conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
            try:
                rows = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
                ).fetchall()

                table_rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
            finally:
                conn.close()

            ddl_statements = [r[0] for r in rows if r[0]]
            tables = [r[0] for r in table_rows]

            ddl_text = "\n".join(ddl_statements)
            index_count = sum(1 for s in ddl_statements if s.strip().upper().startswith("CREATE INDEX"))
            fp_hash = hashlib.sha256(ddl_text.encode("utf-8")).hexdigest() if ddl_text else hashlib.sha256(b"").hexdigest()

            return SchemaFingerprint(
                fingerprint_sha256=fp_hash,
                table_count=len(tables),
                index_count=index_count,
                tables=tables,
            )
        except Exception:
            return None


class SchemaRegistry:
    def __init__(self) -> None:
        self._entries: list[SchemaRegistryEntry] = []

    def register(self, entry: SchemaRegistryEntry) -> None:
        self._entries.append(entry)

    def lookup(self, fingerprint: SchemaFingerprint) -> Optional[SchemaRegistryEntry]:
        for entry in self._entries:
            if entry.fingerprint_sha256 == fingerprint.fingerprint_sha256:
                return entry
        return None

    def match_partial(self, fingerprint: SchemaFingerprint) -> list[SchemaRegistryEntry]:
        fp_tables = set(fingerprint.tables)
        matches: list[SchemaRegistryEntry] = []
        for entry in self._entries:
            expected = set(entry.tables_expected)
            intersection = fp_tables & expected
            if len(intersection) >= len(expected) * 0.6:
                matches.append(entry)
        return matches

    def entries(self) -> list[SchemaRegistryEntry]:
        return list(self._entries)


def build_default_registry(registry: SchemaRegistry) -> None:
    registry.register(SchemaRegistryEntry(
        fingerprint_sha256="",
        whatsapp_version_min="2.22.0",
        whatsapp_version_max="2.24.x",
        adapter_id="whatsapp_sqlite_v1",
        description="WhatsApp Android SQLite schema (messages + wa_contacts + call_log + gif + media)",
        tables_expected=[
            "messages", "chat_view", "wa_contacts", "calls_table",
            "message_thumbnails", "message_links", "message_location",
            "message_mentions", "message_quotes", "message_reactions",
            "message_edit_history", "group_participants", "wa_groups",
            "gif_table", "media_queue",
        ],
    ))

    registry.register(SchemaRegistryEntry(
        fingerprint_sha256="",
        whatsapp_version_min="2.24.x",
        whatsapp_version_max="2.26.x",
        adapter_id="whatsapp_sqlite_v1",
        description="WhatsApp Android SQLite schema (newer variant with messages + wa_contacts + call_log + media)",
        tables_expected=[
            "messages", "chat_view", "wa_contacts", "calls_table",
            "message_thumbnails", "message_links", "message_location",
            "message_mentions", "message_quotes", "message_reactions",
            "group_participants", "wa_groups", "media_queue",
        ],
    ))
