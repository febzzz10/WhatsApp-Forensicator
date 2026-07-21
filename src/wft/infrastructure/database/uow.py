from pathlib import Path
from typing import Optional

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.migrations import Migrator


class UnitOfWork:
    def __init__(self, db_path: Path) -> None:
        self._db = DatabaseConnection(db_path)
        self._path = db_path

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self._db.rollback()
        self._db.close()

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    @property
    def db(self) -> DatabaseConnection:
        return self._db

    def initialize_schema(self) -> None:
        migrator = Migrator(self._db, self._path)
        migrator.initialize()
