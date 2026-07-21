from typing import Any, Optional

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.repository import BaseRepository


def _now_utc() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class ContactRepository(BaseRepository):
    def create(self, case_id: int, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": case_id,
            "contact_code": data["contact_code"],
            "whatsapp_identifier": data.get("whatsapp_identifier"),
            "phone_number_raw": data.get("phone_number_raw"),
            "phone_number_normalized": data.get("phone_number_normalized"),
            "display_name": data.get("display_name"),
            "given_name": data.get("given_name"),
            "family_name": data.get("family_name"),
            "business_name": data.get("business_name"),
            "is_business": 1 if data.get("is_business") else 0,
            "is_blocked": 1 if data.get("is_blocked") else 0,
            "is_saved_contact": 1 if data.get("is_saved_contact") else 0,
            "origin": data.get("origin", "PARSED"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "profile_photo_media_id": data.get("profile_photo_media_id"),
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        return self._insert("contacts", record)

    def get_by_wa_id(self, case_id: int, wa_identifier: str) -> Optional[dict]:
        return self._get_by(
            "contacts", "whatsapp_identifier", wa_identifier
        )

    def list_for_case(self, case_id: int) -> list[dict]:
        return self._list("contacts", "case_id = ? ORDER BY display_name", (case_id,))

    def upsert_by_wa_id(self, case_id: int, data: dict) -> int:
        existing = self.get_by_wa_id(case_id, data.get("whatsapp_identifier", ""))
        if existing:
            now = _now_utc()
            self._db.execute(
                "UPDATE contacts SET display_name = ?, updated_at_utc = ? WHERE id = ?",
                (data.get("display_name", existing["display_name"]), now, existing["id"]),
            )
            return existing["id"]
        return self.create(case_id, data)

    def upsert_by_code(self, case_id: int, data: dict) -> int:
        row = self._get_by("contacts", "contact_code", data.get("contact_code", ""))
        if row:
            return row["id"]
        return self.create(case_id, data)


class GroupRepository(BaseRepository):
    def create(self, case_id: int, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": case_id,
            "group_code": data["group_code"],
            "whatsapp_group_identifier": data.get("whatsapp_group_identifier"),
            "subject": data.get("subject"),
            "description": data.get("description"),
            "creator_contact_id": data.get("creator_contact_id"),
            "created_timestamp_raw": data.get("created_timestamp_raw"),
            "created_at_source_utc": data.get("created_at_source_utc"),
            "origin": data.get("origin", "PARSED"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        return self._insert("groups", record)

    def get_by_wa_id(self, case_id: int, wa_id: str) -> Optional[dict]:
        return self._get_by("groups", "whatsapp_group_identifier", wa_id)

    def upsert_by_wa_id(self, case_id: int, data: dict) -> int:
        wa_id = data.get("whatsapp_group_identifier", "")
        existing = self.get_by_wa_id(case_id, wa_id) if wa_id else None
        if existing:
            return existing["id"]
        return self.create(case_id, data)

    def add_participant(self, data: dict) -> int:
        from wft.infrastructure.database.repository import BaseRepository
        now = _now_utc()
        record = {
            "group_id": data["group_id"],
            "contact_id": data.get("contact_id"),
            "participant_identifier": data.get("participant_identifier"),
            "role": data.get("role"),
            "joined_timestamp_raw": data.get("joined_timestamp_raw"),
            "joined_at_utc": data.get("joined_at_utc"),
            "origin": data.get("origin", "PARSED"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        from wft.infrastructure.database.repository import BaseRepository
        br = BaseRepository(self._db)
        # We use the internal _insert directly since this is a mixin pattern
        cols = ", ".join(record.keys())
        placeholders = ", ".join(f":{k}" for k in record)
        cursor = self._db.execute(
            f"INSERT INTO group_participants ({cols}) VALUES ({placeholders})",
            record,
        )
        return cursor.lastrowid


class ConversationRepository(BaseRepository):
    def create(self, case_id: int, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": case_id,
            "conversation_code": data["conversation_code"],
            "conversation_type": data.get("conversation_type", "UNKNOWN"),
            "contact_id": data.get("contact_id"),
            "group_id": data.get("group_id"),
            "title": data.get("title"),
            "source_conversation_identifier": data.get("source_conversation_identifier"),
            "first_event_at_utc": data.get("first_event_at_utc"),
            "last_event_at_utc": data.get("last_event_at_utc"),
            "message_count": data.get("message_count", 0),
            "call_count": data.get("call_count", 0),
            "origin": data.get("origin", "PARSED"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        return self._insert("conversations", record)

    def get_by_source_id(self, case_id: int, source_id: str) -> Optional[dict]:
        return self._get_by("conversations", "source_conversation_identifier", source_id)

    def upsert_by_contact(self, case_id: int, contact_id: int, title: str) -> int:
        row = self._db.execute(
            "SELECT id FROM conversations WHERE case_id = ? AND contact_id = ? AND conversation_type = 'DIRECT' LIMIT 1",
            (case_id, contact_id),
        ).fetchone()
        if row:
            return row[0]
        return self.create(case_id, {
            "conversation_code": f"DIR-{contact_id:06d}",
            "conversation_type": "DIRECT",
            "contact_id": contact_id,
            "title": title,
        })

    def upsert_by_group(self, case_id: int, group_id: int, title: str) -> int:
        row = self._db.execute(
            "SELECT id FROM conversations WHERE case_id = ? AND group_id = ? AND conversation_type = 'GROUP' LIMIT 1",
            (case_id, group_id),
        ).fetchone()
        if row:
            return row[0]
        return self.create(case_id, {
            "conversation_code": f"GRP-{group_id:06d}",
            "conversation_type": "GROUP",
            "group_id": group_id,
            "title": title,
        })

    def list_for_case(self, case_id: int) -> list[dict]:
        return self._list("conversations", "case_id = ? ORDER BY COALESCE(last_event_at_utc, created_at_utc) DESC", (case_id,))

    def list_with_stats(self, case_id: int) -> list[dict]:
        rows = self._db.execute(
            """SELECT c.*,
                      COUNT(DISTINCT m.id) AS actual_message_count,
                      COUNT(DISTINCT ca.id) AS actual_call_count
                FROM conversations c
                LEFT JOIN messages m ON m.conversation_id = c.id
                LEFT JOIN calls ca ON ca.conversation_id = c.id
                WHERE c.case_id = ?
                GROUP BY c.id
                ORDER BY COALESCE(c.last_event_at_utc, c.created_at_utc) DESC""",
            (case_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class MessageRepository(BaseRepository):
    def create(self, case_id: int, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": case_id,
            "message_code": data["message_code"],
            "conversation_id": data.get("conversation_id"),
            "sender_contact_id": data.get("sender_contact_id"),
            "sender_account_id": data.get("sender_account_id"),
            "source_message_identifier": data.get("source_message_identifier"),
            "source_record_id": data.get("source_record_id"),
            "source_table": data.get("source_table"),
            "direction": data.get("direction", "UNKNOWN"),
            "message_type": data.get("message_type", "TEXT"),
            "text_content": data.get("text_content"),
            "caption_text": data.get("caption_text"),
            "timestamp_raw": data.get("timestamp_raw"),
            "timestamp_epoch_value": data.get("timestamp_epoch_value"),
            "timestamp_epoch_unit": data.get("timestamp_epoch_unit"),
            "sent_at_utc": data.get("sent_at_utc"),
            "is_deleted_marker": 1 if data.get("is_deleted_marker") else 0,
            "is_forwarded": 1 if data.get("is_forwarded") else 0,
            "is_starred": 1 if data.get("is_starred") else 0,
            "is_view_once": 1 if data.get("is_view_once") else 0,
            "origin": data.get("origin", "PARSED"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "validation_status": data.get("validation_status", "VALIDATED"),
            "source_evidence_file_id": data.get("source_evidence_file_id"),
            "parser_run_id": data.get("parser_run_id"),
            "raw_extension_json": data.get("raw_extension_json"),
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        return self._insert("messages", record)

    def count_for_conversation(self, conversation_id: int) -> int:
        row = self._db.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conversation_id,)
        ).fetchone()
        return row[0] if row else 0

    def list_for_conversation(self, conversation_id: int, limit: int = 1000, offset: int = 0) -> list[dict]:
        rows = self._db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY sent_at_utc ASC LIMIT ? OFFSET ?",
            (conversation_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_text(self, case_id: int, query: str, limit: int = 200) -> list[dict]:
        safe = query.replace("'", "''")
        rows = self._db.execute(
            """SELECT m.*, c.display_name AS sender_name, conv.title AS conversation_title
               FROM messages m
               LEFT JOIN contacts c ON m.sender_contact_id = c.id
               LEFT JOIN conversations conv ON m.conversation_id = conv.id
               WHERE m.case_id = ?
                 AND (m.text_content LIKE ? OR m.caption_text LIKE ?)
               ORDER BY m.sent_at_utc DESC
               LIMIT ?""",
            (case_id, f"%{safe}%", f"%{safe}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_fts(self, case_id: int, query: str, limit: int = 200) -> list[dict]:
        safe = query.replace('"', '""')
        rows = self._db.execute(
            """SELECT m.*, c.display_name AS sender_name, conv.title AS conversation_title
               FROM messages m
               JOIN message_search ms ON ms.message_code = m.message_code AND ms.conversation_id = m.conversation_id
               LEFT JOIN contacts c ON m.sender_contact_id = c.id
               LEFT JOIN conversations conv ON m.conversation_id = conv.id
               WHERE m.case_id = ?
                 AND message_search MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (case_id, safe, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_timestamps(self, conversation_id: int, sent_at_utc: str) -> None:
        self._db.execute(
            "UPDATE conversations SET last_event_at_utc = ?, message_count = (SELECT COUNT(*) FROM messages WHERE conversation_id = ?) WHERE id = ?",
            (sent_at_utc, conversation_id, conversation_id),
        )


class CallRepository(BaseRepository):
    def create(self, case_id: int, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": case_id,
            "call_code": data["call_code"],
            "conversation_id": data.get("conversation_id"),
            "source_call_identifier": data.get("source_call_identifier"),
            "source_record_id": data.get("source_record_id"),
            "call_type": data.get("call_type", "UNKNOWN"),
            "direction": data.get("direction", "UNKNOWN"),
            "timestamp_raw": data.get("timestamp_raw"),
            "started_at_utc": data.get("started_at_utc"),
            "ended_at_utc": data.get("ended_at_utc"),
            "duration_seconds": data.get("duration_seconds"),
            "was_answered": 1 if data.get("was_answered") else 0,
            "origin": data.get("origin", "PARSED"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "validation_status": data.get("validation_status", "VALIDATED"),
            "source_evidence_file_id": data.get("source_evidence_file_id"),
            "parser_run_id": data.get("parser_run_id"),
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        return self._insert("calls", record)


    def list_for_case(self, case_id: int, limit: int = 5000, offset: int = 0) -> list[dict]:
        rows = self._db.execute(
            """SELECT ca.*, conv.title AS conversation_title, c.display_name AS contact_name
               FROM calls ca
               LEFT JOIN conversations conv ON ca.conversation_id = conv.id
               LEFT JOIN contacts c ON conv.contact_id = c.id
               WHERE ca.case_id = ?
               ORDER BY ca.started_at_utc DESC
               LIMIT ? OFFSET ?""",
            (case_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, case_id: int, call_type: str = "", direction: str = "", limit: int = 5000, offset: int = 0) -> list[dict]:
        where = ["ca.case_id = ?"]
        params: list[Any] = [case_id]
        if call_type and call_type != "All":
            where.append("ca.call_type = ?")
            params.append(call_type)
        if direction and direction != "All":
            where.append("ca.direction = ?")
            params.append(direction)
        rows = self._db.execute(
            f"""SELECT ca.*, conv.title AS conversation_title, c.display_name AS contact_name
                FROM calls ca
                LEFT JOIN conversations conv ON ca.conversation_id = conv.id
                LEFT JOIN contacts c ON conv.contact_id = c.id
                WHERE {' AND '.join(where)}
                ORDER BY ca.started_at_utc DESC
                LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


class MediaRepository(BaseRepository):
    def create(self, case_id: int, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": case_id,
            "media_code": data["media_code"],
            "message_id": data.get("message_id"),
            "evidence_file_id": data.get("evidence_file_id"),
            "original_filename": data.get("original_filename"),
            "stored_relative_path": data.get("stored_relative_path"),
            "declared_mime_type": data.get("declared_mime_type"),
            "detected_mime_type": data.get("detected_mime_type"),
            "file_extension": data.get("file_extension"),
            "size_bytes": data.get("size_bytes"),
            "sha256": data.get("sha256"),
            "width_pixels": data.get("width_pixels"),
            "height_pixels": data.get("height_pixels"),
            "duration_milliseconds": data.get("duration_milliseconds"),
            "is_missing": 1 if data.get("is_missing") else 0,
            "is_orphan": 1 if data.get("is_orphan") else 0,
            "origin": data.get("origin", "PARSED"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "source_evidence_file_id": data.get("source_evidence_file_id"),
            "parser_run_id": data.get("parser_run_id"),
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        return self._insert("media_items", record)


    def list_for_case(self, case_id: int, limit: int = 5000, offset: int = 0) -> list[dict]:
        rows = self._db.execute(
            """SELECT mi.*, m.text_content AS linked_message_text, m.message_code AS linked_message_code
               FROM media_items mi
               LEFT JOIN messages m ON mi.message_id = m.id
               WHERE mi.case_id = ?
               ORDER BY mi.created_at_utc DESC
               LIMIT ? OFFSET ?""",
            (case_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, case_id: int, filter_type: str = "All", limit: int = 5000, offset: int = 0) -> list[dict]:
        where = ["mi.case_id = ?"]
        params: list[Any] = [case_id]
        if filter_type == "Images":
            where.append("mi.declared_mime_type LIKE 'image/%'")
        elif filter_type == "Videos":
            where.append("mi.declared_mime_type LIKE 'video/%'")
        elif filter_type == "Audio":
            where.append("mi.declared_mime_type LIKE 'audio/%'")
        elif filter_type == "Documents":
            where.append("mi.declared_mime_type NOT LIKE 'image/%' AND mi.declared_mime_type NOT LIKE 'video/%' AND mi.declared_mime_type NOT LIKE 'audio/%' AND mi.declared_mime_type != 'application/octet-stream'")
        elif filter_type == "Orphans":
            where.append("mi.is_orphan = 1")
        elif filter_type == "Missing":
            where.append("mi.is_missing = 1")
        rows = self._db.execute(
            f"""SELECT mi.*, m.text_content AS linked_message_text, m.message_code AS linked_message_code
                FROM media_items mi
                LEFT JOIN messages m ON mi.message_id = m.id
                WHERE {' AND '.join(where)}
                ORDER BY mi.created_at_utc DESC
                LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


class ParserRunRepository(BaseRepository):
    def create(self, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": data["case_id"],
            "evidence_item_id": data["evidence_item_id"],
            "source_evidence_file_id": data.get("source_evidence_file_id"),
            "working_copy_id": data.get("working_copy_id"),
            "parser_name": data["parser_name"],
            "parser_version": data["parser_version"],
            "adapter_id": data["adapter_id"],
            "adapter_version": data["adapter_version"],
            "schema_fingerprint": data.get("schema_fingerprint"),
            "started_at_utc": now,
            "completed_at_utc": None,
            "status": data.get("status", "STARTED"),
            "parsed_record_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "error_summary": None,
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        return self._insert("parser_runs", record)

    def complete(self, run_id: int, status: str, parsed_count: int, warning_count: int, error_count: int, error_summary: str = None) -> None:
        now = _now_utc()
        self._db.execute(
            "UPDATE parser_runs SET status = ?, parsed_record_count = ?, warning_count = ?, error_count = ?, error_summary = ?, completed_at_utc = ?, updated_at_utc = ? WHERE id = ?",
            (status, parsed_count, warning_count, error_count, error_summary, now, now, run_id),
        )

    def add_warning(self, data: dict) -> int:
        now = _now_utc()
        record = {
            "parser_run_id": data["parser_run_id"],
            "evidence_file_id": data.get("evidence_file_id"),
            "warning_code": data.get("warning_code", "PARSE_WARNING"),
            "severity": data.get("severity", "WARNING"),
            "message": data["message"],
            "source_table": data.get("source_table"),
            "source_record_id": data.get("source_record_id"),
            "created_at_utc": now,
        }
        cols = ", ".join(record.keys())
        placeholders = ", ".join(f":{k}" for k in record)
        cursor = self._db.execute(
            f"INSERT INTO parser_warnings ({cols}) VALUES ({placeholders})",
            record,
        )
        return cursor.lastrowid

    def add_mapping(self, data: dict) -> int:
        now = _now_utc()
        record = {
            "parser_run_id": data["parser_run_id"],
            "source_table": data["source_table"],
            "source_column": data["source_column"],
            "internal_entity": data["internal_entity"],
            "internal_field": data["internal_field"],
            "transformation_description": data.get("transformation_description"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "created_at_utc": now,
        }
        cols = ", ".join(record.keys())
        placeholders = ", ".join(f":{k}" for k in record)
        cursor = self._db.execute(
            f"INSERT INTO schema_mappings ({cols}) VALUES ({placeholders})",
            record,
        )
        return cursor.lastrowid

    def add_timeline_event(self, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": data["case_id"],
            "event_code": data["event_code"],
            "event_type": data.get("event_type", "MESSAGE"),
            "title": data["title"],
            "description": data.get("description"),
            "occurred_at_raw": data.get("occurred_at_raw"),
            "occurred_at_utc": data.get("occurred_at_utc"),
            "display_timezone": data.get("display_timezone"),
            "artefact_type": data.get("artefact_type"),
            "artefact_id": data.get("artefact_id"),
            "conversation_id": data.get("conversation_id"),
            "contact_id": data.get("contact_id"),
            "evidence_item_id": data.get("evidence_item_id"),
            "origin": data.get("origin", "PARSED"),
            "confidence_level": data.get("confidence_level", "HIGH"),
            "created_at_utc": now,
        }
        cols = ", ".join(record.keys())
        placeholders = ", ".join(f":{k}" for k in record)
        cursor = self._db.execute(
            f"INSERT INTO timeline_events ({cols}) VALUES ({placeholders})",
            record,
        )
        return cursor.lastrowid


class TimelineEventRepository(BaseRepository):
    def list_for_case(self, case_id: int, limit: int = 10000, offset: int = 0) -> list[dict]:
        rows = self._db.execute(
            """SELECT te.*, conv.title AS conversation_title, c.display_name AS contact_name
               FROM timeline_events te
               LEFT JOIN conversations conv ON te.conversation_id = conv.id
               LEFT JOIN contacts c ON te.contact_id = c.id
               WHERE te.case_id = ?
               ORDER BY te.occurred_at_utc DESC
               LIMIT ? OFFSET ?""",
            (case_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, case_id: int, source_filter: str = "All", confidence: str = "All",
                      date_from: str = "", date_to: str = "", limit: int = 10000) -> list[dict]:
        where = ["te.case_id = ?"]
        params: list[Any] = [case_id]
        if source_filter and source_filter != "All Sources":
            event_type_map = {
                "Messages": "MESSAGE",
                "Calls": "CALL",
                "Media": "MEDIA",
                "Group Events": "GROUP_EVENT",
                "Recovered": "RECOVERED",
                "Network Events": "NETWORK",
            }
            mapped = event_type_map.get(source_filter)
            if mapped:
                where.append("te.event_type = ?")
                params.append(mapped)
        if confidence and confidence != "All Confidence" and confidence != "All":
            where.append("te.confidence_level = ?")
            params.append(confidence.upper())
        if date_from:
            where.append("te.occurred_at_utc >= ?")
            params.append(date_from)
        if date_to:
            where.append("te.occurred_at_utc <= ?")
            params.append(date_to)
        rows = self._db.execute(
            f"""SELECT te.*, conv.title AS conversation_title, c.display_name AS contact_name
                FROM timeline_events te
                LEFT JOIN conversations conv ON te.conversation_id = conv.id
                LEFT JOIN contacts c ON te.contact_id = c.id
                WHERE {' AND '.join(where)}
                ORDER BY te.occurred_at_utc DESC
                LIMIT ?""",
            (*params, limit),
        ).fetchall()
        return [dict(r) for r in rows]


class RecoveryCandidateRepository(BaseRepository):
    def list_for_case(self, case_id: int, limit: int = 5000, offset: int = 0) -> list[dict]:
        rows = self._db.execute(
            """SELECT rc.*, rr.strategy, rr.recovery_code
               FROM recovery_candidates rc
               JOIN recovery_runs rr ON rc.recovery_run_id = rr.id
               WHERE rr.case_id = ?
               ORDER BY rc.created_at_utc DESC
               LIMIT ? OFFSET ?""",
            (case_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_review(self, candidate_id: int, status: str, examiner_id: int = None) -> None:
        now = _now_utc()
        self._db.execute(
            "UPDATE recovery_candidates SET review_status = ?, reviewed_at_utc = ?, reviewed_by_examiner_id = ?, updated_at_utc = ? WHERE id = ?",
            (status, now, examiner_id, now, candidate_id),
        )


class AuditEventRepository(BaseRepository):
    def list_for_case(self, case_id: int, limit: int = 5000) -> list[dict]:
        rows = self._db.execute(
            "SELECT * FROM audit_events WHERE case_id = ? ORDER BY event_sequence DESC LIMIT ?",
            (case_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_chain(self, case_id: int) -> list[dict]:
        rows = self._db.execute(
            "SELECT * FROM audit_events WHERE case_id = ? ORDER BY event_sequence",
            (case_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class ReportRunRepository(BaseRepository):
    def create(self, data: dict) -> int:
        now = _now_utc()
        record = {
            "case_id": data["case_id"],
            "report_code": data["report_code"],
            "report_type": data.get("report_type", "CASE_SUMMARY"),
            "title": data["title"],
            "generated_by_examiner_id": data.get("generated_by_examiner_id"),
            "started_at_utc": now,
            "template_name": data.get("template_name", "default"),
            "template_version": data.get("template_version", "1.0"),
            "generator_version": data.get("generator_version", "1.0.0a1"),
            "display_timezone": data.get("display_timezone", "UTC"),
            "redaction_applied": 1 if data.get("redaction_applied") else 0,
            "status": "STARTED",
            "created_at_utc": now,
            "updated_at_utc": now,
        }
        return self._insert("report_runs", record)

    def complete(self, run_id: int, status: str, error_summary: str = None) -> None:
        now = _now_utc()
        self._db.execute(
            "UPDATE report_runs SET status = ?, completed_at_utc = ?, error_summary = ?, updated_at_utc = ? WHERE id = ?",
            (status, now, error_summary, now, run_id),
        )

    def add_file(self, data: dict) -> int:
        now = _now_utc()
        record = {
            "report_run_id": data["report_run_id"],
            "file_format": data["file_format"],
            "stored_relative_path": data["stored_relative_path"],
            "size_bytes": data["size_bytes"],
            "sha256": data["sha256"],
            "created_at_utc": now,
        }
        return self._insert("report_files", record)

    def list_for_case(self, case_id: int) -> list[dict]:
        return self._list("report_runs", "case_id = ? ORDER BY created_at_utc DESC", (case_id,))
