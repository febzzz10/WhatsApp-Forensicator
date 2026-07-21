from pathlib import Path
from typing import Optional
import sqlite3


class SQLiteValidator:
    def validate_header(self, path: Path) -> bool:
        try:
            with path.open("rb") as f:
                header = f.read(16)
            return header[:16] == b"SQLite format 3\0"
        except Exception:
            return False

    def get_pragma_info(self, path: Path) -> dict:
        if not self.validate_header(path):
            return {"valid": False}
        conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
        try:
            return {
                "valid": True,
                "schema_version": conn.execute("PRAGMA schema_version").fetchone()[0],
                "user_version": conn.execute("PRAGMA user_version").fetchone()[0],
                "page_size": conn.execute("PRAGMA page_size").fetchone()[0],
                "page_count": conn.execute("PRAGMA page_count").fetchone()[0],
                "encoding": conn.execute("PRAGMA encoding").fetchone()[0],
                "application_id": conn.execute("PRAGMA application_id").fetchone()[0],
            }
        finally:
            conn.close()

    def get_table_list(self, path: Path) -> list[dict]:
        conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
        try:
            cursor = conn.execute(
                "SELECT name, type, sql FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name"
            )
            return [{"name": r[0], "type": r[1], "sql": r[2]} for r in cursor.fetchall()]
        finally:
            conn.close()

    def fingerprint_schema(self, path: Path) -> Optional[str]:
        tables = self.get_table_list(path)
        if not tables:
            return None
        names = sorted(t["name"] for t in tables)
        return ",".join(names)
