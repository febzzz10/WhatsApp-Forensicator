import shutil
import zipfile
import os
from pathlib import Path
from typing import Optional

from wft.infrastructure.hashing.hashing_service import HashingService


class FileStoreError(Exception):
    pass


class QuarantineError(FileStoreError):
    pass


class FileStore:
    def __init__(self, base_path: Path, hash_service: HashingService) -> None:
        self._base = base_path.resolve()
        self._hash = hash_service

    def resolve(self, relative_path: str) -> Path:
        p = (self._base / relative_path).resolve()
        try:
            outside_base = os.path.commonpath((str(self._base), str(p))) != str(self._base)
        except ValueError:
            outside_base = True
        if outside_base:
            raise FileStoreError(f"Path traversal detected: {relative_path}")
        return p

    def copy_to_store(self, source: Path, relative_dest: str) -> str:
        dest = self.resolve(relative_dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        return self._hash.sha256_with_copy(source, dest)

    def copy_within_store(self, source_rel: str, dest_rel: str) -> str:
        return self.copy_to_store(self.resolve(source_rel), dest_rel)

    def safe_extract_zip(self, archive: Path, dest_dir: Path, max_size: int = 500 * 1024 * 1024, max_files: int = 10000) -> list[Path]:
        extracted: list[Path] = []
        total_size = 0
        with zipfile.ZipFile(archive, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or Path(name).drive or any(
                    part == ".." for part in Path(name).parts
                ):
                    raise QuarantineError(f"Path traversal in ZIP: {name}")
                dest_path = (dest_dir / name).resolve()
                try:
                    outside_target = os.path.commonpath(
                        (str(dest_dir.resolve()), str(dest_path))
                    ) != str(dest_dir.resolve())
                except ValueError:
                    outside_target = True
                if outside_target:
                    raise QuarantineError(f"ZIP entry outside target: {name}")
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise QuarantineError(f"Unsupported ZIP entry type: {name}")
                total_size += info.file_size
                if total_size > max_size:
                    raise QuarantineError("Archive expansion exceeds size limit")
                if len(extracted) >= max_files:
                    raise QuarantineError("Archive contains too many files")
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, dest_path.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted.append(dest_path)
        return extracted

    def set_read_only(self, relative_path: str) -> None:
        p = self.resolve(relative_path)
        try:
            p.chmod(0o444)
        except Exception:
            pass

    def remove(self, relative_path: str) -> None:
        p = self.resolve(relative_path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)

    def ensure_dir(self, relative_path: str) -> Path:
        p = self.resolve(relative_path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def size(self, relative_path: str) -> int:
        p = self.resolve(relative_path)
        return p.stat().st_size if p.exists() else 0

    def exists(self, relative_path: str) -> bool:
        return self.resolve(relative_path).exists()

    def list_dir(self, relative_path: str) -> list[Path]:
        p = self.resolve(relative_path)
        if not p.is_dir():
            return []
        return list(p.iterdir())
