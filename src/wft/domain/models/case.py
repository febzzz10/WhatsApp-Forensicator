from dataclasses import dataclass, field
from typing import Optional

from wft.domain.enums import CaseStatus
from wft.domain.provenance.provenance import utc_now


@dataclass
class Case:
    id: int = 0
    case_code: str = ""
    title: str = ""
    description: Optional[str] = None
    organisation: Optional[str] = None
    status: str = CaseStatus.OPEN.value
    display_timezone: str = "UTC"
    case_encryption_enabled: bool = False
    external_services_enabled: bool = False
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)
    closed_at_utc: Optional[str] = None


@dataclass
class Examiner:
    id: int = 0
    case_id: int = 0
    examiner_code: str = ""
    full_name: str = ""
    organisation: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    credentials: Optional[str] = None
    is_primary: bool = False
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)


@dataclass
class Authorisation:
    id: int = 0
    case_id: int = 0
    authorisation_type: str = ""
    authority_name: Optional[str] = None
    authority_reference: Optional[str] = None
    scope_description: str = ""
    valid_from_utc: Optional[str] = None
    valid_until_utc: Optional[str] = None
    acknowledged_by_examiner_id: Optional[int] = None
    acknowledged_at_utc: str = field(default_factory=utc_now)
    document_relative_path: Optional[str] = None
    document_sha256: Optional[str] = None
    notes: Optional[str] = None
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)
