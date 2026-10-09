"""Pure WhatsApp acquisition path planning.

Describes WhatsApp acquisition candidates on an Android device and decides
which candidates should be attempted for a given root-access state.

This module is intentionally free of ADB, subprocess, database, filesystem,
and UI dependencies: it answers "what should we try to acquire?" and nothing
else. Encrypted artifacts (crypt12/14/15) are always acquired verbatim;
decryption is out of scope here and in the acquisition worker.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from wft.application.services.adb_service import RootAccess

WHATSAPP_PACKAGE = "com.whatsapp"

# Public (non-root) accessible WhatsApp database locations.
PUBLIC_DATABASE_PATHS: tuple[str, ...] = (
    "/sdcard/Android/media/com.whatsapp/WhatsApp/Databases",
    "/sdcard/WhatsApp/Databases",
)

# Private (root-required) database and key-material locations.
PRIVATE_DATABASE_PATHS: tuple[str, ...] = (
    "/data/data/com.whatsapp/databases",
)
PRIVATE_KEY_PATHS: tuple[str, ...] = (
    "/data/data/com.whatsapp/files/key",
)

# Filenames known to be WhatsApp database/backup artefacts (aligned with the
# ZIP export parser's _DB_PATTERNS convention).
KNOWN_DATABASE_FILENAMES: frozenset[str] = frozenset(
    {"msgstore.db", "wa.db", "calls.db", "axolotl.db"}
)
KNOWN_ENCRYPTED_SUFFIXES: tuple[str, ...] = (".crypt12", ".crypt14", ".crypt15")
SQLITE_SIDECAR_SUFFIXES: tuple[str, ...] = ("-wal", "-journal", "-shm")
KEY_FILENAME = "key"

ACQUIRE_VERBATIM = "ACQUIRE_VERBATIM"


@dataclass(frozen=True)
class PathCandidate:
    """A single remote acquisition candidate for a WhatsApp artefact set."""

    remote_path: str
    artifact_type: str
    requires_root: bool
    expected_handling: str
    description: str


def plan_database_paths(root_access: RootAccess) -> list[PathCandidate]:
    """Return the deterministic ordered candidate list for a root-access state.

    SU:                public + private database paths + private key material.
    ADB_ROOT_CAPABLE:  public paths only — capability is not access, and v1
                       never executes `adb root`.
    NONE:              public paths only.
    """
    candidates: list[PathCandidate] = [
        PathCandidate(
            remote_path=path,
            artifact_type="WHATSAPP_DATABASE",
            requires_root=False,
            expected_handling=ACQUIRE_VERBATIM,
            description="Public WhatsApp database directory",
        )
        for path in PUBLIC_DATABASE_PATHS
    ]

    if root_access == RootAccess.SU:
        candidates.extend(
            PathCandidate(
                remote_path=path,
                artifact_type="WHATSAPP_DATABASE",
                requires_root=True,
                expected_handling=ACQUIRE_VERBATIM,
                description="Private WhatsApp database directory (requires su)",
            )
            for path in PRIVATE_DATABASE_PATHS
        )
        candidates.extend(
            PathCandidate(
                remote_path=path,
                artifact_type="WHATSAPP_KEY_MATERIAL",
                requires_root=True,
                expected_handling=ACQUIRE_VERBATIM,
                description="WhatsApp encryption key file (requires su)",
            )
            for path in PRIVATE_KEY_PATHS
        )

    return candidates


def is_encrypted_artifact(filename: str) -> bool:
    """True when the filename denotes an encrypted WhatsApp backup database."""
    return any(filename.endswith(suffix) for suffix in KNOWN_ENCRYPTED_SUFFIXES)


def is_eligible_artifact(filename: str, candidate: Optional[PathCandidate] = None) -> bool:
    """Whether a discovered filename should be acquired from a candidate path.

    Key-material candidates only match the key filename itself. Database
    candidates match known database names, their encrypted backup variants
    (crypt12/14/15), and SQLite sidecar files (-wal/-journal/-shm), which are
    forensically relevant parts of the database set.
    """
    if not filename or filename.startswith("."):
        return False

    if candidate is not None and candidate.artifact_type == "WHATSAPP_KEY_MATERIAL":
        return filename == KEY_FILENAME

    if filename == KEY_FILENAME:
        return False
    if is_encrypted_artifact(filename):
        return True
    if filename in KNOWN_DATABASE_FILENAMES:
        return True
    if filename.startswith("msgstore.db"):
        return filename.endswith(SQLITE_SIDECAR_SUFFIXES)
    return False
