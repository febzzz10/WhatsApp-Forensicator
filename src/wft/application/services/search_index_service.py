import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from wft.infrastructure.database.connection import DatabaseConnection


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class SearchIndexService:
    def __init__(self) -> None:
        self._fts_available: Optional[bool] = None
        self._last_rebuild: Optional[str] = None

    def check_fts_available(self, db: DatabaseConnection) -> bool:
        if self._fts_available is not None:
            return self._fts_available
        try:
            db.execute("SELECT 1 FROM message_search LIMIT 1")
            self._fts_available = True
        except Exception:
            self._fts_available = False
        return self._fts_available

    def create_index(self, db: DatabaseConnection) -> bool:
        if not self.check_fts_available(db):
            return False
        try:
            db.execute("DELETE FROM message_search")
            db.commit()
            row = db.execute("SELECT COUNT(*) FROM messages").fetchone()
            total = row[0] if row else 0
            if total == 0:
                self._last_rebuild = _now_utc()
                return True
            batch_size = 500
            offset = 0
            while offset < total:
                rows = db.execute(
                    """SELECT m.message_code, m.id, m.case_id, m.conversation_id,
                              COALESCE(c.display_name, '') AS contact_text,
                              COALESCE(conv.title, '') AS conversation_text,
                              COALESCE(m.text_content, '') AS message_text,
                              COALESCE(m.caption_text, '') AS caption_text,
                              COALESCE(
                                  (SELECT GROUP_CONCAT(l.url_raw, ' ') FROM links l WHERE l.message_id = m.id),
                                  ''
                              ) AS link_text
                       FROM messages m
                       LEFT JOIN contacts c ON m.sender_contact_id = c.id
                       LEFT JOIN conversations conv ON m.conversation_id = conv.id
                       ORDER BY m.id
                       LIMIT ? OFFSET ?""",
                    (batch_size, offset),
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    db.execute(
                        "INSERT INTO message_search (message_code, conversation_id, contact_text, conversation_text, message_text, caption_text, link_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (r["message_code"], r["conversation_id"], r["contact_text"], r["conversation_text"], r["message_text"], r["caption_text"], r["link_text"]),
                    )
                db.commit()
                offset += batch_size
            self._last_rebuild = _now_utc()
            return True
        except Exception:
            return False

    def add_message(self, db: DatabaseConnection, message_code: str, conversation_id: int,
                    contact_text: str = "", conversation_text: str = "",
                    message_text: str = "", caption_text: str = "",
                    link_text: str = "") -> bool:
        if not self.check_fts_available(db):
            return False
        try:
            db.execute(
                "INSERT INTO message_search (message_code, conversation_id, contact_text, conversation_text, message_text, caption_text, link_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (message_code, conversation_id, contact_text, conversation_text, message_text, caption_text, link_text),
            )
            return True
        except Exception:
            return False

    def add_messages_batch(self, db: DatabaseConnection, messages: list[dict]) -> bool:
        if not self.check_fts_available(db):
            return False
        try:
            for m in messages:
                self.add_message(
                    db,
                    message_code=m.get("message_code", ""),
                    conversation_id=m.get("conversation_id", 0),
                    contact_text=m.get("contact_text", ""),
                    conversation_text=m.get("conversation_text", ""),
                    message_text=m.get("text_content", ""),
                    caption_text=m.get("caption_text", ""),
                    link_text=m.get("link_text", ""),
                )
            db.commit()
            return True
        except Exception:
            return False

    def remove_messages(self, db: DatabaseConnection, message_codes: list[str]) -> bool:
        if not self.check_fts_available(db):
            return False
        try:
            for code in message_codes:
                db.execute("DELETE FROM message_search WHERE message_code = ?", (code,))
            db.commit()
            return True
        except Exception:
            return False

    def get_index_health(self, db: DatabaseConnection) -> dict:
        result = {
            "fts_available": self.check_fts_available(db),
            "index_present": False,
            "indexed_count": 0,
            "eligible_count": 0,
            "last_rebuild": self._last_rebuild,
            "search_engine": "LIKE_FALLBACK",
        }
        if result["fts_available"]:
            try:
                row = db.execute("SELECT COUNT(*) FROM message_search").fetchone()
                result["indexed_count"] = row[0] if row else 0
                result["index_present"] = result["indexed_count"] > 0
            except Exception:
                pass
        try:
            row = db.execute("SELECT COUNT(*) FROM messages").fetchone()
            result["eligible_count"] = row[0] if row else 0
        except Exception:
            pass
        if result["index_present"]:
            result["search_engine"] = "FTS5"
        return result
