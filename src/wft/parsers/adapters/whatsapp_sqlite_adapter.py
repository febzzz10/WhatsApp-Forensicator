from pathlib import Path
from typing import Optional

import sqlite3


class WhatsAppSQLiteAdapter:
    adapter_id = "whatsapp_sqlite_v1"
    adapter_version = "1.0.0"

    _EPOCH_GOOGLE = 10957

    def _google_to_utc(self, google_ts: int) -> Optional[str]:
        if google_ts < self._EPOCH_GOOGLE:
            return None
        from datetime import datetime, timezone
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        try:
            dt = epoch + (google_ts - self._EPOCH_GOOGLE) * 86400
            return dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
        except Exception:
            return None

    def _epoch_to_utc(self, epoch_ms: int) -> Optional[str]:
        from datetime import datetime, timezone, timedelta
        try:
            dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=epoch_ms)
            return dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
        except Exception:
            return None

    def inspect(self, source: Path) -> dict:
        warnings: list[str] = []
        tables: list[str] = []
        is_valid = False
        schema_fingerprint = None

        if not source.exists():
            return {"source_type": "WHATSAPP_SQLITE", "is_valid": False,
                    "file_count": 0, "warnings": ["File not found"], "schema_fingerprint": None}

        try:
            conn = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
            try:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [r[0] for r in cursor.fetchall()]

                table_set = set(t.lower() for t in tables)
                expected = {"messages", "wa_contacts", "chat_view", "calls_table",
                            "message_thumbnails", "message_links", "message_location"}
                has_expected = table_set & expected
                if has_expected:
                    is_valid = True

                ddl_rows = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
                ).fetchall()
                if ddl_rows:
                    import hashlib
                    ddl_text = "\n".join(r[0] for r in ddl_rows)
                    schema_fingerprint = hashlib.sha256(ddl_text.encode("utf-8")).hexdigest()

            finally:
                conn.close()
        except Exception as exc:
            warnings.append(f"Cannot open SQLite: {exc}")

        return {
            "source_type": "WHATSAPP_SQLITE",
            "is_valid": is_valid,
            "file_count": 1,
            "warnings": warnings,
            "schema_fingerprint": schema_fingerprint,
            "tables": tables,
        }

    def supports(self, inspection: dict) -> bool:
        return inspection.get("is_valid", False)

    def parse(self, source: Path, context: ParseContext) -> dict:
        warnings: list[str] = []
        contacts: list[dict] = []
        messages: list[dict] = []
        groups: list[dict] = []
        group_participants: list[dict] = []
        calls: list[dict] = []
        media: list[dict] = []

        conn = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            table_set = set(t.lower() for t in tables)

            if "wa_contacts" in table_set:
                try:
                    for row in conn.execute("SELECT * FROM wa_contacts"):
                        wa_id = row.get("wa_id") or row.get("jid") or ""
                        contacts.append({
                            "contact_code": f"CONTACT-{wa_id.replace('@s.whatsapp.net', '')[:20]}" if wa_id else f"CONTACT-{row.get('display_name', 'UNKNOWN')[:20]}",
                            "whatsapp_identifier": wa_id,
                            "phone_number_raw": row.get("phone_number") or row.get("number"),
                            "display_name": row.get("display_name") or row.get("name"),
                            "given_name": row.get("given_name"),
                            "family_name": row.get("family_name"),
                            "is_business": row.get("is_business", 0) if isinstance(row.get("is_business"), bool) else bool(row.get("is_business", 0)),
                            "is_blocked": row.get("is_blocked", 0),
                            "is_saved_contact": row.get("is_contact", 0) or row.get("is_wa_contact", 0),
                            "origin": "PARSED",
                        })
                except Exception as exc:
                    warnings.append(f"wa_contacts error: {exc}")

            if "messages" in table_set:
                try:
                    msg_cols = [d[1] for d in conn.execute("PRAGMA table_info(messages)").fetchall()]
                    col_set = set(c.lower() for c in msg_cols)

                    query = "SELECT rowid as _rid, * FROM messages ORDER BY _rid ASC"
                    for row in conn.execute(query):
                        key = row.get("key_from_me") or row.get("from_me")
                        direction = "OUTGOING" if (key == 1 or key is True) else "INCOMING"
                        if key is None and ("key_remote_jid" not in col_set):
                            direction = "UNKNOWN"

                        ts_raw = row.get("timestamp")
                        sent_at_utc = None
                        if ts_raw is not None:
                            if isinstance(ts_raw, (int, float)) and ts_raw < 100000000000:
                                sent_at_utc = self._google_to_utc(int(ts_raw))
                            elif isinstance(ts_raw, (int, float)):
                                sent_at_utc = self._epoch_to_utc(int(ts_raw))

                        data = row.get("data") or row.get("message_data") or row.get("text_data") or ""
                        msg_type = row.get("message_type") or row.get("m_type") or "TEXT"

                        msg_code = f"MSG-{row['_rid']:08d}"
                        messages.append({
                            "message_code": msg_code,
                            "source_record_id": str(row["_rid"]),
                            "source_table": "messages",
                            "direction": direction,
                            "message_type": str(msg_type),
                            "text_content": str(data) if data else None,
                            "timestamp_raw": str(ts_raw) if ts_raw is not None else None,
                            "timestamp_epoch_value": int(ts_raw) if ts_raw is not None else None,
                            "timestamp_epoch_unit": "GOOGLE_EPOCH_DAYS" if (ts_raw and ts_raw < 100000000000) else "EPOCH_MS",
                            "sent_at_utc": sent_at_utc,
                            "origin": "PARSED",
                            "sender_wa_id": row.get("key_remote_jid") if direction == "INCOMING" else None,
                        })
                except Exception as exc:
                    warnings.append(f"messages table error: {exc}")

            if "calls_table" in table_set:
                try:
                    for row in conn.execute("SELECT * FROM calls_table"):
                        ts_raw = row.get("timestamp")
                        started_at_utc = None
                        if ts_raw is not None:
                            if isinstance(ts_raw, (int, float)) and ts_raw < 100000000000:
                                started_at_utc = self._google_to_utc(int(ts_raw))
                            elif isinstance(ts_raw, (int, float)):
                                started_at_utc = self._epoch_to_utc(int(ts_raw))

                        call_type_raw = row.get("call_type") or row.get("type") or "UNKNOWN"
                        direction_raw = row.get("call_direction") or row.get("direction") or "UNKNOWN"

                        calls.append({
                            "call_code": f"CALL-{row['rowid'] if hasattr(row, 'keys') and 'rowid' in row.keys() else row.get('_id', 0):08d}",
                            "source_record_id": str(row.get("_id", row.get("rowid", ""))),
                            "call_type": str(call_type_raw),
                            "direction": str(direction_raw),
                            "timestamp_raw": str(ts_raw) if ts_raw is not None else None,
                            "started_at_utc": started_at_utc,
                            "duration_seconds": row.get("duration"),
                            "was_answered": row.get("answered", 0) or row.get("call_result") == 1,
                            "origin": "PARSED",
                        })
                except Exception as exc:
                    warnings.append(f"calls_table error: {exc}")

            if "wa_groups" in table_set:
                try:
                    for row in conn.execute("SELECT * FROM wa_groups"):
                        gid = row.get("gjid") or row.get("group_jid") or ""
                        groups.append({
                            "group_code": f"GROUP-{gid[:20]}" if gid else "GROUP-UNKNOWN",
                            "whatsapp_group_identifier": gid,
                            "subject": row.get("subject") or row.get("name"),
                            "origin": "PARSED",
                        })
                except Exception as exc:
                    warnings.append(f"wa_groups error: {exc}")

            if "group_participants" in table_set:
                try:
                    for row in conn.execute("SELECT * FROM group_participants"):
                        group_participants.append({
                            "group_identifier": row.get("gjid") or row.get("group_jid"),
                            "participant_identifier": row.get("jid") or row.get("member"),
                            "role": row.get("role") or row.get("admin") and "ADMIN" or "MEMBER",
                            "origin": "PARSED",
                        })
                except Exception as exc:
                    warnings.append(f"group_participants error: {exc}")

            if "message_thumbnails" in table_set:
                try:
                    has_dimensions = "width" in [d[1] for d in conn.execute("PRAGMA table_info(message_thumbnails)").fetchall()]
                    cols = "*"
                    for row in conn.execute(f"SELECT {cols} FROM message_thumbnails"):
                        media.append({
                            "media_code": f"MEDIA-{row.get('_id', row.get('rowid', 0)):08d}",
                            "original_filename": row.get("file_name"),
                            "declared_mime_type": row.get("mime_type") or "image/jpeg",
                            "width_pixels": row.get("width"),
                            "height_pixels": row.get("height"),
                            "size_bytes": row.get("file_size"),
                            "sha256": row.get("file_hash") or row.get("sha256"),
                            "source_record_id": str(row.get("_id", row.get("rowid", ""))),
                            "origin": "PARSED",
                        })
                except Exception as exc:
                    warnings.append(f"message_thumbnails error: {exc}")

            contact_code_map: dict[str, int] = {}
            for idx, c in enumerate(contacts):
                contact_code_map[c["contact_code"]] = idx

            message_contact_map: dict[str, str] = {}
            for m in messages:
                sender_wa = m.pop("sender_wa_id", None)
                if sender_wa:
                    for c in contacts:
                        if c.get("whatsapp_identifier") == sender_wa:
                            m["sender_contact_code"] = c["contact_code"]
                            break

        finally:
            conn.close()

        total_parsed = len(contacts) + len(messages) + len(groups) + len(calls) + len(media)

        return {
            "message_count": len(messages),
            "contact_count": len(contacts),
            "group_count": len(groups),
            "call_count": len(calls),
            "media_count": len(media),
            "warnings": warnings,
            "parser_version": self.adapter_version,
            "adapter_id": self.adapter_id,
            "contacts": contacts,
            "messages": messages,
            "groups": groups,
            "group_participants": group_participants,
            "calls": calls,
            "media": media,
        }

    def capabilities(self) -> dict:
        return {
            "adapter_id": self.adapter_id,
            "version": self.adapter_version,
            "supported": [
                "Messages", "Contacts", "Calls", "Groups",
                "Group participants", "Media thumbnails",
            ],
            "partially_supported": ["Message reactions", "Message quotes"],
            "unsupported": ["Edited messages", "Locations", "Links", "Business metadata"],
        }
