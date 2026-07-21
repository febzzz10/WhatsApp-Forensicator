from dataclasses import dataclass, field
from typing import Optional

from wft.domain.provenance.provenance import utc_now


@dataclass
class Contact:
    id: int = 0
    case_id: int = 0
    contact_code: str = ""
    whatsapp_identifier: Optional[str] = None
    phone_number_raw: Optional[str] = None
    phone_number_normalized: Optional[str] = None
    display_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    business_name: Optional[str] = None
    profile_photo_media_id: Optional[int] = None
    is_business: bool = False
    is_blocked: Optional[int] = None
    is_saved_contact: Optional[int] = None
    origin: str = "PARSED"
    confidence_level: str = "HIGH"
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)


@dataclass
class Group:
    id: int = 0
    case_id: int = 0
    group_code: str = ""
    whatsapp_group_identifier: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    creator_contact_id: Optional[int] = None
    created_timestamp_raw: Optional[str] = None
    created_at_source_utc: Optional[str] = None
    origin: str = "PARSED"
    confidence_level: str = "HIGH"
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)


@dataclass
class Conversation:
    id: int = 0
    case_id: int = 0
    conversation_code: str = ""
    conversation_type: str = ""
    contact_id: Optional[int] = None
    group_id: Optional[int] = None
    title: Optional[str] = None
    source_conversation_identifier: Optional[str] = None
    first_event_at_utc: Optional[str] = None
    last_event_at_utc: Optional[str] = None
    message_count: int = 0
    call_count: int = 0
    origin: str = "PARSED"
    confidence_level: str = "HIGH"
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)


@dataclass
class Message:
    id: int = 0
    case_id: int = 0
    message_code: str = ""
    conversation_id: int = 0
    sender_contact_id: Optional[int] = None
    sender_account_id: Optional[int] = None
    source_message_identifier: Optional[str] = None
    source_record_id: Optional[str] = None
    source_table: Optional[str] = None
    direction: str = "UNKNOWN"
    message_type: str = "TEXT"
    text_content: Optional[str] = None
    caption_text: Optional[str] = None
    timestamp_raw: Optional[str] = None
    timestamp_epoch_value: Optional[int] = None
    timestamp_epoch_unit: Optional[str] = None
    sent_at_utc: Optional[str] = None
    delivered_at_utc: Optional[str] = None
    read_at_utc: Optional[str] = None
    deleted_at_utc: Optional[str] = None
    edited_at_utc: Optional[str] = None
    is_deleted_marker: bool = False
    is_forwarded: bool = False
    is_starred: bool = False
    is_view_once: bool = False
    raw_extension_json: Optional[str] = None
    origin: str = "PARSED"
    confidence_level: str = "HIGH"
    validation_status: str = "VALIDATED"
    source_evidence_file_id: Optional[int] = None
    parser_run_id: Optional[int] = None
    source_page_number: Optional[int] = None
    source_byte_offset: Optional[int] = None
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)


@dataclass
class Call:
    id: int = 0
    case_id: int = 0
    call_code: str = ""
    conversation_id: Optional[int] = None
    source_call_identifier: Optional[str] = None
    source_record_id: Optional[str] = None
    call_type: str = "UNKNOWN"
    direction: str = "UNKNOWN"
    timestamp_raw: Optional[str] = None
    started_at_utc: Optional[str] = None
    ended_at_utc: Optional[str] = None
    duration_seconds: Optional[int] = None
    was_answered: Optional[int] = None
    origin: str = "PARSED"
    confidence_level: str = "HIGH"
    validation_status: str = "VALIDATED"
    source_evidence_file_id: Optional[int] = None
    parser_run_id: Optional[int] = None
    source_page_number: Optional[int] = None
    source_byte_offset: Optional[int] = None
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)


@dataclass
class MediaItem:
    id: int = 0
    case_id: int = 0
    media_code: str = ""
    message_id: Optional[int] = None
    evidence_file_id: Optional[int] = None
    parent_media_id: Optional[int] = None
    original_filename: Optional[str] = None
    stored_relative_path: Optional[str] = None
    preview_relative_path: Optional[str] = None
    declared_mime_type: Optional[str] = None
    detected_mime_type: Optional[str] = None
    file_extension: Optional[str] = None
    size_bytes: Optional[int] = None
    sha256: Optional[str] = None
    width_pixels: Optional[int] = None
    height_pixels: Optional[int] = None
    duration_milliseconds: Optional[int] = None
    media_role: Optional[str] = None
    is_missing: bool = False
    is_orphan: bool = False
    origin: str = "PARSED"
    confidence_level: str = "HIGH"
    source_evidence_file_id: Optional[int] = None
    parser_run_id: Optional[int] = None
    created_at_utc: str = field(default_factory=utc_now)
    updated_at_utc: str = field(default_factory=utc_now)
