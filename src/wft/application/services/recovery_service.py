from typing import Any

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.artefact_repositories import RecoveryCandidateRepository


class RecoveryService:
    def __init__(self) -> None:
        self._repo_cls = RecoveryCandidateRepository

    def get_candidates(self, db: DatabaseConnection, case_id: int, strategy: str = "All",
                       confidence: str = "All", limit: int = 5000, offset: int = 0) -> list[dict]:
        repo = self._repo_cls(db)
        where = ["rr.case_id = ?"]
        params: list[Any] = [case_id]
        if strategy and strategy != "All Strategies":
            strat_map = {
                "WAL Parsing": "WAL",
                "Journal Parsing": "JOURNAL",
                "Freelist Scan": "FREELIST",
                "Page Carving": "PAGE_CARVING",
            }
            mapped = strat_map.get(strategy)
            if mapped:
                where.append("rr.strategy = ?")
                params.append(mapped)
        if confidence and confidence != "All":
            where.append("rc.confidence_level = ?")
            params.append(confidence.upper())
        rows = db.execute(
            f"""SELECT rc.*, rr.strategy, rr.recovery_code
                FROM recovery_candidates rc
                JOIN recovery_runs rr ON rc.recovery_run_id = rr.id
                WHERE {' AND '.join(where)}
                ORDER BY rc.created_at_utc DESC
                LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def accept(self, db: DatabaseConnection, candidate_id: int, examiner_id: int = None) -> None:
        repo = self._repo_cls(db)
        repo.update_review(candidate_id, "ACCEPTED", examiner_id)

    def reject(self, db: DatabaseConnection, candidate_id: int, examiner_id: int = None) -> None:
        repo = self._repo_cls(db)
        repo.update_review(candidate_id, "REJECTED", examiner_id)

    def leave_unresolved(self, db: DatabaseConnection, candidate_id: int, examiner_id: int = None) -> None:
        repo = self._repo_cls(db)
        repo.update_review(candidate_id, "UNRESOLVED", examiner_id)
