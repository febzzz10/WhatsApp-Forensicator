from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from wft.domain.enums import ArtefactOrigin, ConfidenceLevel, ValidationStatus


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class Provenance:
    case_id: int
    evidence_item_id: int
    source_file_id: Optional[int] = None
    source_hash: Optional[str] = None
    source_table: Optional[str] = None
    source_record_id: Optional[str] = None
    source_page_number: Optional[int] = None
    source_byte_offset: Optional[int] = None
    parser_name: Optional[str] = None
    parser_version: Optional[str] = None
    adapter_id: Optional[str] = None
    adapter_version: Optional[str] = None
    acquisition_method: Optional[str] = None
    origin: ArtefactOrigin = ArtefactOrigin.PARSED
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    validation: ValidationStatus = ValidationStatus.VALIDATED
    parse_timestamp: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class RecoveredProvenance(Provenance):
    recovery_method: Optional[str] = None
    wal_frame_number: Optional[int] = None
    journal_offset: Optional[int] = None
    carving_signature: Optional[str] = None
    validation_checks: Optional[str] = None
    competing_interpretations: Optional[str] = None


@dataclass(frozen=True)
class AuditEntry:
    event_type: str
    event_description: str
    component_name: str
    component_version: str
    examiner_id: Optional[int] = None
    object_type: Optional[str] = None
    object_id: Optional[str] = None
    details_json: Optional[str] = None
    previous_event_hash: Optional[str] = None
    occurred_at_utc: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class Confidence:
    level: ConfidenceLevel
    score: Optional[float] = None

    def __post_init__(self) -> None:
        if self.score is not None and not (0 <= self.score <= 1):
            raise ValueError(f"Confidence score must be between 0 and 1, got {self.score}")
