from typing import Optional

from wft.infrastructure.database.connection import DatabaseConnection


class StatisticsService:
    def get_case_stats(self, db: DatabaseConnection, case_id: int) -> dict:
        evidence = db.execute(
            "SELECT COUNT(*) FROM evidence_items WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        messages = db.execute(
            "SELECT COUNT(*) FROM messages WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        contacts = db.execute(
            "SELECT COUNT(*) FROM contacts WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        calls = db.execute(
            "SELECT COUNT(*) FROM calls WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        media = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        groups = db.execute(
            "SELECT COUNT(*) FROM groups WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        conversations = db.execute(
            "SELECT COUNT(*) FROM conversations WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        timeline = db.execute(
            "SELECT COUNT(*) FROM timeline_events WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        audit = db.execute(
            "SELECT COUNT(*) FROM audit_events WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        recovered_candidates = db.execute(
            "SELECT COUNT(*) FROM recovery_candidates rc JOIN recovery_runs rr ON rc.recovery_run_id = rr.id WHERE rr.case_id = ?",
            (case_id,),
        ).fetchone()[0]

        return {
            "evidence": evidence,
            "messages": messages,
            "contacts": contacts,
            "calls": calls,
            "media": media,
            "groups": groups,
            "conversations": conversations,
            "timeline": timeline,
            "audit": audit,
            "recovered_candidates": recovered_candidates,
        }

    def get_call_stats(self, db: DatabaseConnection, case_id: int) -> dict:
        total = db.execute(
            "SELECT COUNT(*) FROM calls WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        incoming = db.execute(
            "SELECT COUNT(*) FROM calls WHERE case_id = ? AND direction = 'INCOMING'", (case_id,)
        ).fetchone()[0]
        outgoing = db.execute(
            "SELECT COUNT(*) FROM calls WHERE case_id = ? AND direction = 'OUTGOING'", (case_id,)
        ).fetchone()[0]
        missed = db.execute(
            "SELECT COUNT(*) FROM calls WHERE case_id = ? AND direction = 'MISSED'", (case_id,)
        ).fetchone()[0]
        video = db.execute(
            "SELECT COUNT(*) FROM calls WHERE case_id = ? AND call_type IN ('VIDEO','GROUP_VIDEO')", (case_id,)
        ).fetchone()[0]
        duration_row = db.execute(
            "SELECT COALESCE(SUM(duration_seconds), 0) FROM calls WHERE case_id = ? AND duration_seconds IS NOT NULL",
            (case_id,),
        ).fetchone()[0]
        minutes = duration_row // 60
        seconds = duration_row % 60
        return {
            "total": total,
            "incoming": incoming,
            "outgoing": outgoing,
            "missed": missed,
            "video": video,
            "total_duration": f"{minutes}:{seconds:02d}",
        }

    def get_media_stats(self, db: DatabaseConnection, case_id: int) -> dict:
        total = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        images = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ? AND declared_mime_type LIKE 'image/%'",
            (case_id,),
        ).fetchone()[0]
        videos = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ? AND declared_mime_type LIKE 'video/%'",
            (case_id,),
        ).fetchone()[0]
        audio = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ? AND declared_mime_type LIKE 'audio/%'",
            (case_id,),
        ).fetchone()[0]
        docs = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ? AND declared_mime_type NOT LIKE 'image/%' AND declared_mime_type NOT LIKE 'video/%' AND declared_mime_type NOT LIKE 'audio/%' AND declared_mime_type != 'application/octet-stream'",
            (case_id,),
        ).fetchone()[0]
        orphans = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ? AND is_orphan = 1", (case_id,)
        ).fetchone()[0]
        missing = db.execute(
            "SELECT COUNT(*) FROM media_items WHERE case_id = ? AND is_missing = 1", (case_id,)
        ).fetchone()[0]
        return {
            "total": total,
            "images": images,
            "videos": videos,
            "audio": audio,
            "documents": docs,
            "orphans": orphans,
            "missing": missing,
        }

    def get_audit_stats(self, db: DatabaseConnection, case_id: int) -> dict:
        total = db.execute(
            "SELECT COUNT(*) FROM audit_events WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        critical = db.execute(
            "SELECT COUNT(*) FROM audit_events WHERE case_id = ? AND event_type LIKE '%CRITICAL%' OR event_type LIKE '%ERROR%'",
            (case_id,),
        ).fetchone()[0]
        last_row = db.execute(
            "SELECT MAX(event_sequence) FROM audit_events WHERE case_id = ?", (case_id,)
        ).fetchone()[0]
        return {
            "total": total,
            "critical": critical,
            "last_sequence": last_row or 0,
        }

    def get_recovery_stats(self, db: DatabaseConnection, case_id: int) -> dict:
        total = db.execute(
            "SELECT COUNT(*) FROM recovery_candidates rc JOIN recovery_runs rr ON rc.recovery_run_id = rr.id WHERE rr.case_id = ?",
            (case_id,),
        ).fetchone()[0]
        high = db.execute(
            "SELECT COUNT(*) FROM recovery_candidates rc JOIN recovery_runs rr ON rc.recovery_run_id = rr.id WHERE rr.case_id = ? AND rc.confidence_level = 'HIGH'",
            (case_id,),
        ).fetchone()[0]
        medium = db.execute(
            "SELECT COUNT(*) FROM recovery_candidates rc JOIN recovery_runs rr ON rc.recovery_run_id = rr.id WHERE rr.case_id = ? AND rc.confidence_level = 'MEDIUM'",
            (case_id,),
        ).fetchone()[0]
        low = db.execute(
            "SELECT COUNT(*) FROM recovery_candidates rc JOIN recovery_runs rr ON rc.recovery_run_id = rr.id WHERE rr.case_id = ? AND rc.confidence_level = 'LOW'",
            (case_id,),
        ).fetchone()[0]
        accepted = db.execute(
            "SELECT COUNT(*) FROM recovery_candidates rc JOIN recovery_runs rr ON rc.recovery_run_id = rr.id WHERE rr.case_id = ? AND rc.review_status = 'ACCEPTED'",
            (case_id,),
        ).fetchone()[0]
        rejected = db.execute(
            "SELECT COUNT(*) FROM recovery_candidates rc JOIN recovery_runs rr ON rc.recovery_run_id = rr.id WHERE rr.case_id = ? AND rc.review_status = 'REJECTED'",
            (case_id,),
        ).fetchone()[0]
        unresolved = db.execute(
            "SELECT COUNT(*) FROM recovery_candidates rc JOIN recovery_runs rr ON rc.recovery_run_id = rr.id WHERE rr.case_id = ? AND rc.review_status = 'UNRESOLVED'",
            (case_id,),
        ).fetchone()[0]
        return {
            "total": total,
            "high": high,
            "medium": medium,
            "low": low,
            "accepted": accepted,
            "rejected": rejected,
            "unresolved": unresolved,
        }
