from typing import Any, Optional

from wft.infrastructure.database.connection import DatabaseConnection, row_to_dict


class BaseRepository:
    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    def _insert(self, table: str, data: dict[str, Any]) -> int:
        cols = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data)
        cursor = self._db.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
            data,
        )
        return cursor.lastrowid

    def _update(self, table: str, data: dict[str, Any], where_id: int) -> None:
        sets = ", ".join(f"{k} = :{k}" for k in data if k != "id")
        data["_id"] = where_id
        self._db.execute(
            f"UPDATE {table} SET {sets} WHERE id = :_id",
            data,
        )

    def _get(self, table: str, id: int) -> Optional[dict]:
        row = self._db.execute(
            f"SELECT * FROM {table} WHERE id = ?", (id,)
        ).fetchone()
        return row_to_dict(row)

    def _get_by(self, table: str, column: str, value: Any) -> Optional[dict]:
        row = self._db.execute(
            f"SELECT * FROM {table} WHERE {column} = ?", (value,)
        ).fetchone()
        return row_to_dict(row)

    def _list(self, table: str, where: str = "", params: tuple = ()) -> list[dict]:
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return [dict(r) for r in self._db.execute(sql, params).fetchall()]

    def _exists(self, table: str, column: str, value: Any) -> bool:
        cursor = self._db.execute(
            f"SELECT 1 FROM {table} WHERE {column} = ? LIMIT 1", (value,)
        )
        return cursor.fetchone() is not None
