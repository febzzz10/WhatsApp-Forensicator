from datetime import datetime, timezone
import os
import stat
from pathlib import Path
from typing import Callable, Optional

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.repository import BaseRepository
from wft.infrastructure.filesystem.file_store import FileStore
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.logging.logging_service import LoggingService


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class EvidenceRepository(BaseRepository):
    def create_item(self, data: dict) -> int:
        return self._insert("evidence_items", data)

    def get_item(self, item_id: int) -> Optional[dict]:
        return self._get("evidence_items", item_id)

    def add_file(self, data: dict) -> int:
        return self._insert("evidence_files", data)

    def add_hash(self, data: dict) -> int:
        return self._insert("evidence_hashes", data)

    def get_items_for_case(self, case_id: int) -> list[dict]:
        return self._list("evidence_items", "case_id = ?", (case_id,))

    def update_item_state(self, item_id: int, state: str) -> None:
        now = _now_utc()
        self._db.execute(
            "UPDATE evidence_items SET state = ?, updated_at_utc = ? WHERE id = ?",
            (state, now, item_id),
        )


class EvidenceService:
    def __init__(self, store: FileStore, hash_service: HashingService, log: LoggingService) -> None:
        self._store = store
        self._hash = hash_service
        self._log = log

    def import_file(
        self,
        db: DatabaseConnection,
        case_id: int,
        evidence_code: str,
        title: str,
        source_type: str,
        acquisition_method: str,
        source_path: Path,
        examiner_id: Optional[int] = None,
        case_dir: Optional[Path] = None,
    ) -> dict:
        repo = EvidenceRepository(db)
        store = FileStore(case_dir, self._hash) if case_dir is not None else self._store

        item_data = {
            "case_id": case_id,
            "evidence_code": evidence_code,
            "title": title,
            "source_type": source_type,
            "acquisition_method": acquisition_method,
            "state": "COPYING",
            "imported_at_utc": _now_utc(),
            "created_at_utc": _now_utc(),
            "updated_at_utc": _now_utc(),
        }
        item_id = repo.create_item(item_data)
        if not source_path.is_file():
            repo.update_item_state(item_id, "FAILED")
            raise FileNotFoundError(
                f"Source path is not a file or does not exist: {source_path}"
            )

        relative_dir = f"originals/E{item_id:04d}"
        store.ensure_dir(relative_dir)

        dest_filename = source_path.name
        relative_path = f"{relative_dir}/{dest_filename}"

        try:
            sha256 = store.copy_to_store(source_path, relative_path)
            store.set_read_only(relative_path)

            file_data = {
                "evidence_item_id": item_id,
                "file_code": "F001",
                "original_filename": dest_filename,
                "original_source_path": str(source_path.resolve()),
                "stored_relative_path": relative_path,
                "size_bytes": store.size(relative_path),
                "imported_at_utc": _now_utc(),
                "is_original_copy": 1,
                "is_read_only": 1,
                "verification_status": "VALIDATED",
                "created_at_utc": _now_utc(),
                "updated_at_utc": _now_utc(),
            }
            file_id = repo.add_file(file_data)

            hash_data = {
                "evidence_file_id": file_id,
                "algorithm": "SHA256",
                "hash_value": sha256,
                "purpose": "IMPORT",
                "calculated_at_utc": _now_utc(),
                "calculated_by_tool_version": "1.0.0a1",
                "created_at_utc": _now_utc(),
            }
            repo.add_hash(hash_data)

            repo.update_item_state(item_id, "VERIFIED")

            self._log.info(f"Evidence imported: {evidence_code} ({source_path.name})")

            return {
                "item_id": item_id,
                "file_id": file_id,
                "sha256": sha256,
                "stored_path": relative_path,
            }

        except Exception as exc:
            repo.update_item_state(item_id, "FAILED")
            self._log.error(f"Evidence import failed for {evidence_code}: {exc}")
            raise

    def import_directory(
        self,
        db: DatabaseConnection,
        case_id: int,
        evidence_code: str,
        title: str,
        source_type: str,
        acquisition_method: str,
        source_path: Path,
        case_dir: Path,
        examiner_id: Optional[int] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
    ) -> dict:
        """Copy a directory into one logical evidence item with per-file provenance."""
        source_root = source_path.resolve()
        case_root = case_dir.resolve()
        store = FileStore(case_root, self._hash)
        if not source_root.is_dir() or source_root.is_symlink():
            raise ValueError(f"Evidence source is not a safe directory: {source_path}")
        if self._contained_path(case_root, source_root):
            raise ValueError("Evidence source cannot be inside the active case directory")

        warnings: list[str] = []
        source_files: list[tuple[Path, Path]] = []
        for current_root, directory_names, file_names in os.walk(
            source_root, topdown=True, followlinks=False
        ):
            if is_cancelled and is_cancelled():
                return {
                    "item_id": None,
                    "file_ids": [],
                    "stored_paths": [],
                    "sha256_values": {},
                    "imported_file_count": 0,
                    "skipped_file_count": len(warnings),
                    "parsed_file_count": 0,
                    "unsupported_file_count": 0,
                    "failed_file_count": 0,
                    "warnings": warnings + ["Directory import cancelled"],
                    "status": "CANCELLED",
                }
            directory_names.sort()
            file_names.sort()
            current = Path(current_root).resolve()
            if not self._contained_path(source_root, current):
                raise ValueError(f"Directory traversal detected: {current}")
            safe_directories: list[str] = []
            for name in directory_names:
                candidate = Path(current_root) / name
                if self._unsafe_entry(candidate, source_root):
                    warnings.append(f"Skipped unsafe directory: {candidate.name}")
                else:
                    safe_directories.append(name)
            directory_names[:] = safe_directories
            for name in file_names:
                candidate = Path(current_root) / name
                if self._unsafe_entry(candidate, source_root):
                    warnings.append(f"Skipped unsafe file: {candidate.name}")
                    continue
                resolved = candidate.resolve()
                relative = resolved.relative_to(source_root)
                source_files.append((resolved, relative))

        repo = EvidenceRepository(db)
        item_id = repo.create_item({
            "case_id": case_id,
            "evidence_code": evidence_code,
            "title": title,
            "source_type": source_type,
            "acquisition_method": acquisition_method,
            "state": "COPYING",
            "imported_at_utc": _now_utc(),
            "created_at_utc": _now_utc(),
            "updated_at_utc": _now_utc(),
        })
        db.commit()

        if not source_files:
            repo.update_item_state(item_id, "FAILED")
            db.commit()
            return {
                "item_id": item_id,
                "file_ids": [],
                "stored_paths": [],
                "sha256_values": {},
                "imported_file_count": 0,
                "skipped_file_count": len(warnings),
                "parsed_file_count": 0,
                "unsupported_file_count": 0,
                "failed_file_count": 0,
                "warnings": warnings + ["Directory contains no safe regular files"],
                "status": "FAILED",
            }

        copied: list[tuple[Path, Path, str, int]] = []
        try:
            total = len(source_files)
            for index, (source_file, relative) in enumerate(source_files, start=1):
                if is_cancelled and is_cancelled():
                    raise _DirectoryImportCancelled("Directory import cancelled")
                relative_text = relative.as_posix()
                destination_relative = f"originals/E{item_id:04d}/{relative_text}"
                destination = store.resolve(destination_relative)
                destination_root = store.resolve(f"originals/E{item_id:04d}")
                if not self._contained_path(destination_root, destination):
                    raise ValueError(f"Destination path escapes evidence directory: {relative_text}")
                if on_progress:
                    on_progress(f"Copying {relative_text} ({index}/{total})", index, total)
                digest = store.copy_to_store(source_file, destination_relative)
                store.set_read_only(destination_relative)
                copied.append((source_file, relative, digest, destination.stat().st_size))

            if is_cancelled and is_cancelled():
                raise _DirectoryImportCancelled("Directory import cancelled")

            file_ids: list[int] = []
            stored_paths: list[str] = []
            sha256_values: dict[str, str] = {}
            with db.transaction():
                for index, (source_file, relative, digest, size) in enumerate(copied, start=1):
                    stored_path = f"originals/E{item_id:04d}/{relative.as_posix()}"
                    file_id = repo.add_file({
                        "evidence_item_id": item_id,
                        "file_code": f"F{index:04d}",
                        "original_filename": relative.name,
                        "original_source_path": str(source_file),
                        "stored_relative_path": stored_path,
                        "size_bytes": size,
                        "imported_at_utc": _now_utc(),
                        "is_original_copy": 1,
                        "is_read_only": 1,
                        "verification_status": "VALIDATED",
                        "created_at_utc": _now_utc(),
                        "updated_at_utc": _now_utc(),
                    })
                    repo.add_hash({
                        "evidence_file_id": file_id,
                        "algorithm": "SHA256",
                        "hash_value": digest,
                        "purpose": "IMPORT",
                        "calculated_at_utc": _now_utc(),
                        "calculated_by_tool_version": "1.0.0a1",
                        "created_at_utc": _now_utc(),
                    })
                    file_ids.append(file_id)
                    stored_paths.append(stored_path)
                    sha256_values[stored_path] = digest
                repo.update_item_state(item_id, "VERIFIED")

            return {
                "item_id": item_id,
                "file_ids": file_ids,
                "stored_paths": stored_paths,
                "sha256_values": sha256_values,
                "imported_file_count": len(file_ids),
                "skipped_file_count": len(warnings),
                "parsed_file_count": 0,
                "unsupported_file_count": 0,
                "failed_file_count": 0,
                "warnings": warnings,
                "status": "VERIFIED",
            }
        except _DirectoryImportCancelled as exc:
            repo.update_item_state(item_id, "FAILED")
            db.commit()
            return {
                "item_id": item_id,
                "file_ids": [],
                "stored_paths": [],
                "sha256_values": {},
                "imported_file_count": 0,
                "skipped_file_count": len(warnings),
                "parsed_file_count": 0,
                "unsupported_file_count": 0,
                "failed_file_count": 0,
                "warnings": warnings + [str(exc)],
                "status": "CANCELLED",
            }
        except Exception:
            repo.update_item_state(item_id, "FAILED")
            db.commit()
            raise

    @staticmethod
    def _contained_path(root: Path, candidate: Path) -> bool:
        try:
            return os.path.commonpath((str(root), str(candidate))) == str(root)
        except ValueError:
            return False

    @classmethod
    def _unsafe_entry(cls, entry: Path, source_root: Path) -> bool:
        try:
            if entry.is_symlink():
                return True
            attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
            reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            if reparse_point and attributes & reparse_point:
                return True
            resolved = entry.resolve()
        except (OSError, RuntimeError, AttributeError):
            return True
        return not cls._contained_path(source_root, resolved)


class _DirectoryImportCancelled(Exception):
    pass
