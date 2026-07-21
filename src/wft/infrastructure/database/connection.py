import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional


class DatabaseConnection:
    def __init__(self, db_path: Path, read_only: bool = False) -> None:
        self._db_path = db_path
        self._read_only = read_only
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            uri = self._db_path.as_uri()
            if self._read_only:
                uri += "?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.execute("PRAGMA busy_timeout = 5000;")
            self._conn.execute("PRAGMA temp_store = MEMORY;")
            self._conn.execute("PRAGMA trusted_schema = OFF;")
            if not self._read_only:
                self._conn.execute("PRAGMA journal_mode = WAL;")
                self._conn.execute("PRAGMA synchronous = FULL;")
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute(self, sql: str, params: dict | tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, param_list: list[dict | tuple]) -> sqlite3.Cursor:
        return self.conn.executemany(sql, param_list)

    def commit(self) -> None:
        if self._conn:
            self._conn.commit()

    def rollback(self) -> None:
        if self._conn:
            self._conn.rollback()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self.conn
        conn.execute("BEGIN;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def check_integrity(self) -> list[str]:
        cursor = self.execute("PRAGMA quick_check;")
        row = cursor.fetchone()
        if row and row[0] != "ok":
            return [str(row[0])]
        return []

    def check_foreign_keys(self) -> list[str]:
        cursor = self.execute("PRAGMA foreign_key_check;")
        return [str(row) for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Repository helpers
# ---------------------------------------------------------------------------
from typing import Any, Protocol

class Repository(Protocol):
    def add(self, obj: Any) -> None: ...
    def get(self, id: int) -> Any | None: ...
    def update(self, obj: Any) -> None: ...


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)
