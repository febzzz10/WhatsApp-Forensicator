import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.schema import ALL_TABLE_DDL, ALL_INDEXES, SCHEMA_VERSION, CREATE_SCHEMA_MIGRATIONS


class MigrationError(Exception):
    pass


class Migrator:
    def __init__(self, db: DatabaseConnection, db_path: Path) -> None:
        self._db = db
        self._db_path = db_path
        self._app_version = "1.0.0a1"

    def initialize(self) -> None:
        backup_path: Optional[Path] = None
        if self._db_path.exists():
            backup_path = self._db_path.with_suffix(".db.bak")
            self._backup(self._db_path, backup_path)

        self._db.execute(CREATE_SCHEMA_MIGRATIONS)
        self._db.commit()

        current = self._current_version()
        if current == 0:
            for ddl in ALL_TABLE_DDL:
                self._db.execute(ddl)
            for idx in ALL_INDEXES:
                self._db.execute(idx)
            self._db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            self._record_migration(SCHEMA_VERSION, "initial_schema")
            self._db.commit()
            self._verify()

    def _current_version(self) -> int:
        row = self._db.execute("PRAGMA user_version").fetchone()
        return row[0] if row else 0

    def _record_migration(self, version: int, name: str) -> None:
        checksum = hashlib.sha256(f"{version}:{name}".encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        self._db.execute(
            "INSERT INTO schema_migrations (version, migration_name, applied_at_utc, application_version, checksum) VALUES (?, ?, ?, ?, ?)",
            (version, name, now, self._app_version, checksum),
        )

    def _verify(self) -> None:
        issues = self._db.check_integrity()
        if issues:
            raise MigrationError(f"Database integrity check failed after migration: {issues}")
        fk_issues = self._db.check_foreign_keys()
        if fk_issues:
            raise MigrationError(f"Foreign key check failed after migration: {fk_issues}")

    def _backup(self, source: Path, dest: Path) -> None:
        import shutil
        shutil.copy2(source, dest)
