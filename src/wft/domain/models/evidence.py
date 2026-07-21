from dataclasses import dataclass, field
from typing import Optional

from wft.domain.provenance.provenance import utc_now


@dataclass
class EvidenceItem:
    id: int = 0
    case_id: int = 0
    evidence_code: str = ""
    title: str = ""
    description: Optional[str] = None
    source_type: str = ""
    acquisition_method: str = ""
    source_device_name: Optional[str] = None
    source_device_identifier: Optional[str] = None
    source_application: Optional[str] = None
    source_application_version: Optional[str] = None
    source_operating_system: Optional[str] = None
    source_timezone: Optional[str] = None
    state: str = "REGISTERED"
    imported_by_examiner_id: Optional[int] = None
    imported_at_utc: str = field(default_factory=utc_now)
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)


@dataclass
class EvidenceFile:
    id: int = 0
    evidence_item_id: int = 0
    file_code: str = ""
    original_filename: str = ""
    original_source_path: Optional[str] = None
    stored_relative_path: str = ""
    media_type: Optional[str] = None
    detected_file_type: Optional[str] = None
    size_bytes: int = 0
    source_created_at_raw: Optional[str] = None
    source_modified_at_raw: Optional[str] = None
    source_accessed_at_raw: Optional[str] = None
    imported_at_utc: str = field(default_factory=utc_now)
    is_original_copy: bool = True
    is_read_only: bool = True
    verification_status: str = "UNVERIFIED"
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)


@dataclass
class EvidenceHash:
    id: int = 0
    evidence_file_id: int = 0
    algorithm: str = "SHA256"
    hash_value: str = ""
    purpose: str = "IMPORT"
    calculated_at_utc: str = field(default_factory=utc_now)
    calculated_by_tool_version: str = ""
    verified_against_hash_id: Optional[int] = None
    verification_result: Optional[str] = None
    created_at_utc: str = field(default_factory=utc_now)


@dataclass
class WorkingCopy:
    id: int = 0
    source_evidence_file_id: int = 0
    working_code: str = ""
    stored_relative_path: str = ""
    purpose: str = ""
    size_bytes: int = 0
    sha256: str = ""
    created_by_process: str = ""
    is_temporary: bool = False
    deletion_due_at_utc: Optional[str] = None
    state: str = "READY"
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)
