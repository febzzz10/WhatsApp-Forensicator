from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal

from wft.infrastructure.database.connection import DatabaseConnection


class ActiveCaseContext(QObject):
    case_changed = Signal(int, str)

    def __init__(self) -> None:
        super().__init__()
        self._case_id: Optional[int] = None
        self._case_path: Optional[Path] = None
        self._db_path: Optional[Path] = None
        self._db: Optional[DatabaseConnection] = None

    @property
    def case_id(self) -> Optional[int]:
        return self._case_id

    @property
    def case_path(self) -> Optional[Path]:
        return self._case_path

    @property
    def db_path(self) -> Optional[Path]:
        return self._db_path

    @property
    def db(self) -> Optional[DatabaseConnection]:
        return self._db

    @property
    def is_active(self) -> bool:
        return self._case_id is not None

    def open(self, case_id: int, case_path: Path) -> None:
        self._case_id = case_id
        self._case_path = case_path
        self._db_path = case_path / "case.db"
        self._db = DatabaseConnection(self._db_path)
        self._db.execute("PRAGMA foreign_keys = ON;")
        self.case_changed.emit(case_id, str(case_path))

    def close(self) -> None:
        if self._db:
            self._db.close()
        self._case_id = None
        self._case_path = None
        self._db_path = None
        self._db = None

    def get_db(self) -> DatabaseConnection:
        if self._db is None:
            raise RuntimeError("No active case")
        return self._db
