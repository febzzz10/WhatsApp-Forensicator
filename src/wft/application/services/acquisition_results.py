from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ImportUserExportResult:
    evidence_id: int
    source_path: str
    stored_path: str
    hash_value: str
    imported_items: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class MediaAcquisitionResult:
    destination: str
    copied_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    total_bytes: int = 0
    evidence_ids: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DeviceMetadataResult:
    artifact_path: str
    evidence_id: int
    hash_value: str
    fields_recorded: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class WhatsAppDatabaseArtifact:
    """One acquired WhatsApp database artefact with its provenance."""

    remote_path: str
    local_path: str
    size_bytes: int
    sha256: str
    encrypted: bool
    artifact_type: str
    requires_root: bool
    evidence_file_id: Optional[int] = None


@dataclass
class WhatsAppDatabaseExtractionResult:
    """Structured WhatsApp database acquisition result.

    status is one of: ACQUIRED, PARTIAL, NO_FILES_FOUND, FAILED, CANCELLED.
    Encrypted artefacts (crypt12/14/15) are acquired byte-for-byte and
    remain decryption-pending; nothing here implies readability.
    """

    status: str
    device_serial: str
    root_access: str
    destination: str
    artifacts: list[WhatsAppDatabaseArtifact] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    unavailable_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_item_id: Optional[int] = None
    audit_event_hash: Optional[str] = None
