import tempfile
from pathlib import Path

import pytest

from wft.infrastructure.hashing.hashing_service import HashingService


class TestHashingService:
    def setup_method(self) -> None:
        self.service = HashingService()

    def test_sha256_known_value(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"hello world")
            tmp = Path(f.name)
        try:
            result = self.service.sha256(tmp)
            expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
            assert result == expected
        finally:
            tmp.unlink()

    def test_sha256_stream(self) -> None:
        import io
        stream = io.BytesIO(b"test data")
        result = self.service.sha256_stream(stream)
        assert len(result) == 64

    def test_sha256_with_copy(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as src_f:
            src_f.write(b"copy test")
            src_path = Path(src_f.name)
        dest_path = Path(tempfile.mktemp(suffix=".copy"))
        try:
            result = self.service.sha256_with_copy(src_path, dest_path)
            assert len(result) == 64
            assert dest_path.read_bytes() == b"copy test"
        finally:
            src_path.unlink()
            if dest_path.exists():
                dest_path.unlink()

    def test_verify_match(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"verify me")
            tmp = Path(f.name)
        try:
            expected = self.service.sha256(tmp)
            assert self.service.verify(tmp, expected)
        finally:
            tmp.unlink()

    def test_verify_mismatch(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"data")
            tmp = Path(f.name)
        try:
            assert not self.service.verify(tmp, "0" * 64)
        finally:
            tmp.unlink()
