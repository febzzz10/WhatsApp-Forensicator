import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from wft.infrastructure.database.connection import DatabaseConnection


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class AuditService:
    def __init__(self, app_version: str = "1.0.0a1") -> None:
        self._app_version = app_version

    def _canonical_json(self, data: dict) -> str:
        return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def _hash_chain(self, previous_hash: Optional[str], event_json: str) -> str:
        raw = (previous_hash or "") + event_json
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def record_event(
        self,
        db: DatabaseConnection,
        case_id: int,
        event_type: str,
        description: str,
        examiner_id: Optional[int] = None,
        component_name: str = "case_service",
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> str:
        now = _now_utc()
        row = db.execute(
            "SELECT MAX(event_sequence) FROM audit_events WHERE case_id = ?",
            (case_id,),
        ).fetchone()
        next_seq = (row[0] or 0) + 1

        row2 = db.execute(
            "SELECT event_hash FROM audit_events WHERE case_id = ? ORDER BY event_sequence DESC LIMIT 1",
            (case_id,),
        ).fetchone()
        previous_hash = row2[0] if row2 else None

        canonical = self._canonical_json({
            "sequence": next_seq,
            "type": event_type,
            "description": description,
            "component": component_name,
            "version": self._app_version,
            "object_type": object_type,
            "object_id": object_id,
            "details": details or {},
            "timestamp": now,
        })
        event_hash = self._hash_chain(previous_hash, canonical)

        db.execute(
            """INSERT INTO audit_events
               (case_id, event_sequence, event_type, event_description, examiner_id,
                component_name, component_version, object_type, object_id, details_json,
                previous_event_hash, event_hash, occurred_at_utc, created_at_utc)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (case_id, next_seq, event_type, description, examiner_id,
             component_name, self._app_version, object_type, object_id,
             self._canonical_json(details or {}),
             previous_hash, event_hash, now, now),
        )
        return event_hash

    def verify_chain(self, db: DatabaseConnection, case_id: int) -> list[str]:
        rows = db.execute(
            "SELECT event_sequence, event_hash, previous_event_hash, event_type, event_description, "
            "component_name, component_version, object_type, object_id, details_json, occurred_at_utc "
            "FROM audit_events WHERE case_id = ? ORDER BY event_sequence",
            (case_id,),
        ).fetchall()

        issues: list[str] = []
        prev_hash: Optional[str] = None
        for row in rows:
            seq = row["event_sequence"]
            canonical = self._canonical_json({
                "sequence": seq,
                "type": row["event_type"],
                "description": row["event_description"],
                "component": row["component_name"],
                "version": row["component_version"],
                "object_type": row["object_type"],
                "object_id": row["object_id"],
                "details": json.loads(row["details_json"]) if row["details_json"] else {},
                "timestamp": row["occurred_at_utc"],
            })
            expected = self._hash_chain(prev_hash, canonical)
            if expected != row["event_hash"]:
                issues.append(f"Sequence {seq}: hash mismatch")
            if prev_hash != row["previous_event_hash"]:
                issues.append(f"Sequence {seq}: chain broken at event")
            prev_hash = row["event_hash"]

        return issues
