import hashlib
from pathlib import Path
from typing import BinaryIO


class HashingService:
    CHUNK_SIZE = 65536

    def sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(self.CHUNK_SIZE):
                h.update(chunk)
        return h.hexdigest()

    def sha256_stream(self, stream: BinaryIO) -> str:
        h = hashlib.sha256()
        while chunk := stream.read(self.CHUNK_SIZE):
            h.update(chunk)
        return h.hexdigest()

    def sha256_with_copy(self, source: Path, dest: Path) -> str:
        h = hashlib.sha256()
        with source.open("rb") as src, dest.open("wb") as dst:
            while chunk := src.read(self.CHUNK_SIZE):
                h.update(chunk)
                dst.write(chunk)
        return h.hexdigest()

    def sha512(self, path: Path) -> str:
        h = hashlib.sha512()
        with path.open("rb") as f:
            while chunk := f.read(self.CHUNK_SIZE):
                h.update(chunk)
        return h.hexdigest()

    def md5(self, path: Path) -> str:
        h = hashlib.md5()
        with path.open("rb") as f:
            while chunk := f.read(self.CHUNK_SIZE):
                h.update(chunk)
        return h.hexdigest()

    def verify(self, path: Path, expected: str, algorithm: str = "sha256") -> bool:
        if algorithm == "sha256":
            actual = self.sha256(path)
        elif algorithm == "sha512":
            actual = self.sha512(path)
        elif algorithm == "md5":
            actual = self.md5(path)
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        return actual.lower() == expected.lower()
