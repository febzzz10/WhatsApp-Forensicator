import re
from typing import Any

from wft.infrastructure.database.connection import DatabaseConnection
from wft.application.services.search_index_service import SearchIndexService


class SearchService:
    def __init__(self) -> None:
        self._search_index_service = SearchIndexService()
        self._search_engine: str = "LIKE_FALLBACK"

    @property
    def search_engine(self) -> str:
        return self._search_engine

    def search(self, db: DatabaseConnection, case_id: int, query: str, scope: str = "All",
               date_from: str = "", date_to: str = "", limit: int = 200) -> list[dict]:
        if not query.strip():
            return []

        safe = query.replace("'", "''")

        if scope == "All" or scope == "Messages":
            results = self._search_messages(db, case_id, safe, date_from, date_to, limit)
            if scope == "Messages":
                return results
            results += self._search_contacts(db, case_id, safe, limit // 2)
            results += self._search_media(db, case_id, safe, limit // 2)
            results += self._search_calls(db, case_id, safe, limit // 2)
            results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
            return results[:limit]
        elif scope == "Contacts":
            return self._search_contacts(db, case_id, safe, limit)
        elif scope == "Media":
            return self._search_media(db, case_id, safe, limit)
        elif scope == "Calls":
            return self._search_calls(db, case_id, safe, limit)
        elif scope == "Recovered":
            return self._search_recovered(db, case_id, safe, limit)
        elif scope == "Network":
            return self._search_network(db, case_id, safe, limit)
        elif scope == "Notes":
            return self._search_notes(db, case_id, safe, limit)
        return []

    def _search_messages(self, db: DatabaseConnection, case_id: int, safe_query: str,
                         date_from: str = "", date_to: str = "", limit: int = 200) -> list[dict]:
        is_simple_query = bool(re.match(r"^[\w\s]+$", safe_query))
        use_fts = is_simple_query and self._search_index_service.check_fts_available(db)
        if use_fts:
            self._search_engine = "FTS5"
            tokens = safe_query.split()
            fts_terms = []
            for t in tokens:
                if t:
                    escaped_t = t.replace('"', '""')
                    fts_terms.append(f'"{escaped_t}"*')
            fts_query = " AND ".join(fts_terms)
            where = ["m.case_id = ?"]
            params: list[Any] = [case_id]
            if date_from:
                where.append("m.sent_at_utc >= ?")
                params.append(date_from)
            if date_to:
                where.append("m.sent_at_utc <= ?")
                params.append(date_to)
            rows = db.execute(
                f"""SELECT m.id, m.message_code, m.text_content, m.sent_at_utc AS timestamp,
                           m.message_type, m.direction, m.origin, m.confidence_level,
                           c.display_name AS sender_name, conv.title AS conversation_title,
                           'message' AS artefact_type
                    FROM messages m
                    JOIN message_search ms ON ms.message_code = m.message_code
                    LEFT JOIN contacts c ON m.sender_contact_id = c.id
                    LEFT JOIN conversations conv ON m.conversation_id = conv.id
                    WHERE {' AND '.join(where)}
                      AND "message_search" MATCH ?
                    ORDER BY rank
                    LIMIT ?""",
                (*params, fts_query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        else:
            self._search_engine = "LIKE_FALLBACK"
            where = ["m.case_id = ?"]
            params = [case_id]
            where.append("(m.text_content LIKE ? OR m.caption_text LIKE ?)")
            params.extend([f"%{safe_query}%", f"%{safe_query}%"])
            if date_from:
                where.append("m.sent_at_utc >= ?")
                params.append(date_from)
            if date_to:
                where.append("m.sent_at_utc <= ?")
                params.append(date_to)
            rows = db.execute(
                f"""SELECT m.id, m.message_code, m.text_content, m.sent_at_utc AS timestamp,
                           m.message_type, m.direction, m.origin, m.confidence_level,
                           c.display_name AS sender_name, conv.title AS conversation_title,
                           'message' AS artefact_type
                    FROM messages m
                    LEFT JOIN contacts c ON m.sender_contact_id = c.id
                    LEFT JOIN conversations conv ON m.conversation_id = conv.id
                    WHERE {' AND '.join(where)}
                    ORDER BY m.sent_at_utc DESC
                    LIMIT ?""",
                (*params, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def _search_contacts(self, db: DatabaseConnection, case_id: int, safe_query: str, limit: int = 200) -> list[dict]:
        rows = db.execute(
            """SELECT id, contact_code, display_name, phone_number_raw AS text_content,
                      whatsapp_identifier, is_business, origin, confidence_level,
                      created_at_utc AS timestamp, 'contact' AS artefact_type
               FROM contacts
               WHERE case_id = ?
                 AND (display_name LIKE ? OR phone_number_raw LIKE ? OR whatsapp_identifier LIKE ?)
               LIMIT ?""",
            (case_id, f"%{safe_query}%", f"%{safe_query}%", f"%{safe_query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def _search_media(self, db: DatabaseConnection, case_id: int, safe_query: str, limit: int = 200) -> list[dict]:
        rows = db.execute(
            """SELECT mi.id, mi.media_code, mi.original_filename AS text_content,
                      mi.declared_mime_type AS message_type, mi.size_bytes,
                      mi.sha256, mi.is_missing, mi.origin, mi.confidence_level,
                      mi.created_at_utc AS timestamp, 'media' AS artefact_type
               FROM media_items mi
               WHERE mi.case_id = ?
                 AND (mi.original_filename LIKE ? OR mi.sha256 LIKE ?)
               LIMIT ?""",
            (case_id, f"%{safe_query}%", f"%{safe_query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def _search_calls(self, db: DatabaseConnection, case_id: int, safe_query: str, limit: int = 200) -> list[dict]:
        rows = db.execute(
            """SELECT ca.id, ca.call_code, ca.call_type AS message_type, ca.direction,
                      ca.duration_seconds, ca.started_at_utc AS timestamp,
                      ca.origin, ca.confidence_level, ca.was_answered,
                      conv.title AS conversation_title, 'call' AS artefact_type
               FROM calls ca
               LEFT JOIN conversations conv ON ca.conversation_id = conv.id
               WHERE ca.case_id = ?
                 AND (ca.call_code LIKE ? OR conv.title LIKE ?)
               LIMIT ?""",
            (case_id, f"%{safe_query}%", f"%{safe_query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def _search_recovered(self, db: DatabaseConnection, case_id: int, safe_query: str, limit: int = 200) -> list[dict]:
        rows = db.execute(
            """SELECT rc.id, rc.candidate_code, rc.candidate_type, rc.confidence_level,
                      rc.review_status, rc.created_at_utc AS timestamp,
                      rr.strategy, 'recovered' AS artefact_type
               FROM recovery_candidates rc
               JOIN recovery_runs rr ON rc.recovery_run_id = rr.id
               WHERE rr.case_id = ?
                 AND (rc.candidate_code LIKE ? OR rc.parsed_fields_json LIKE ?)
               LIMIT ?""",
            (case_id, f"%{safe_query}%", f"%{safe_query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def _search_network(self, db: DatabaseConnection, case_id: int, safe_query: str, limit: int = 200) -> list[dict]:
        rows = db.execute(
            """SELECT ne.id, ne.ip_address AS text_content, ne.endpoint_classification AS message_type,
                      ne.isp_name, ne.country_name, ne.city_name,
                      ne.first_seen_at_utc AS timestamp, 'network' AS artefact_type
               FROM network_endpoints ne
               JOIN network_capture_sessions ncs ON ne.capture_session_id = ncs.id
               WHERE ncs.case_id = ?
                 AND (ne.ip_address LIKE ? OR ne.isp_name LIKE ? OR ne.country_name LIKE ?)
               LIMIT ?""",
            (case_id, f"%{safe_query}%", f"%{safe_query}%", f"%{safe_query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def _search_notes(self, db: DatabaseConnection, case_id: int, safe_query: str, limit: int = 200) -> list[dict]:
        rows = db.execute(
            """SELECT id, note_text AS text_content, artefact_type, artefact_id,
                      created_at_utc AS timestamp, 'note' AS result_type
                FROM examiner_notes
                WHERE case_id = ? AND note_text LIKE ?
                LIMIT ?""",
            (case_id, f"%{safe_query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]
