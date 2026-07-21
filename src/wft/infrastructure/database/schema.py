SCHEMA_VERSION = 1

CREATE_CASES = """
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY,
    case_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    organisation TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'LOCKED', 'ARCHIVED', 'CLOSED')),
    display_timezone TEXT NOT NULL DEFAULT 'UTC',
    case_encryption_enabled INTEGER NOT NULL DEFAULT 0
        CHECK (case_encryption_enabled IN (0, 1)),
    external_services_enabled INTEGER NOT NULL DEFAULT 0
        CHECK (external_services_enabled IN (0, 1)),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    closed_at_utc TEXT
);
"""

CREATE_EXAMINERS = """
CREATE TABLE IF NOT EXISTS examiners (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    examiner_code TEXT NOT NULL,
    full_name TEXT NOT NULL,
    organisation TEXT,
    job_title TEXT,
    email TEXT,
    phone TEXT,
    credentials TEXT,
    is_primary INTEGER NOT NULL DEFAULT 0
        CHECK (is_primary IN (0, 1)),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    UNIQUE (case_id, examiner_code)
);
"""

CREATE_AUTHORISATIONS = """
CREATE TABLE IF NOT EXISTS authorisations (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    authorisation_type TEXT NOT NULL,
    authority_name TEXT,
    authority_reference TEXT,
    scope_description TEXT NOT NULL,
    valid_from_utc TEXT,
    valid_until_utc TEXT,
    acknowledged_by_examiner_id INTEGER,
    acknowledged_at_utc TEXT NOT NULL,
    document_relative_path TEXT,
    document_sha256 TEXT,
    notes TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (acknowledged_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL
);
"""

CREATE_EVIDENCE_ITEMS = """
CREATE TABLE IF NOT EXISTS evidence_items (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    evidence_code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    source_type TEXT NOT NULL,
    acquisition_method TEXT NOT NULL,
    source_device_name TEXT,
    source_device_identifier TEXT,
    source_application TEXT,
    source_application_version TEXT,
    source_operating_system TEXT,
    source_timezone TEXT,
    state TEXT NOT NULL DEFAULT 'REGISTERED'
        CHECK (state IN ('REGISTERED','COPYING','VERIFIED','HASH_MISMATCH','QUARANTINED','UNSUPPORTED','PARSED','PARTIALLY_PARSED','FAILED')),
    imported_by_examiner_id INTEGER,
    imported_at_utc TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (imported_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, evidence_code)
);
"""

CREATE_EVIDENCE_FILES = """
CREATE TABLE IF NOT EXISTS evidence_files (
    id INTEGER PRIMARY KEY,
    evidence_item_id INTEGER NOT NULL,
    file_code TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    original_source_path TEXT,
    stored_relative_path TEXT NOT NULL,
    media_type TEXT,
    detected_file_type TEXT,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    source_created_at_raw TEXT,
    source_modified_at_raw TEXT,
    source_accessed_at_raw TEXT,
    imported_at_utc TEXT NOT NULL,
    is_original_copy INTEGER NOT NULL DEFAULT 1 CHECK (is_original_copy IN (0, 1)),
    is_read_only INTEGER NOT NULL DEFAULT 1 CHECK (is_read_only IN (0, 1)),
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verification_status IN ('VALIDATED','PARTIAL','UNVERIFIED','REJECTED','UNSUPPORTED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id) ON DELETE RESTRICT,
    UNIQUE (evidence_item_id, file_code),
    UNIQUE (stored_relative_path)
);
"""

CREATE_EVIDENCE_HASHES = """
CREATE TABLE IF NOT EXISTS evidence_hashes (
    id INTEGER PRIMARY KEY,
    evidence_file_id INTEGER NOT NULL,
    algorithm TEXT NOT NULL CHECK (algorithm IN ('SHA256','SHA512','MD5')),
    hash_value TEXT NOT NULL,
    purpose TEXT NOT NULL DEFAULT 'IMPORT',
    calculated_at_utc TEXT NOT NULL,
    calculated_by_tool_version TEXT NOT NULL,
    verified_against_hash_id INTEGER,
    verification_result TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (evidence_file_id) REFERENCES evidence_files(id) ON DELETE RESTRICT,
    FOREIGN KEY (verified_against_hash_id) REFERENCES evidence_hashes(id) ON DELETE SET NULL,
    UNIQUE (evidence_file_id, algorithm, purpose)
);
"""

CREATE_WORKING_COPIES = """
CREATE TABLE IF NOT EXISTS working_copies (
    id INTEGER PRIMARY KEY,
    source_evidence_file_id INTEGER NOT NULL,
    working_code TEXT NOT NULL UNIQUE,
    stored_relative_path TEXT NOT NULL UNIQUE,
    purpose TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    sha256 TEXT NOT NULL,
    created_by_process TEXT NOT NULL,
    is_temporary INTEGER NOT NULL DEFAULT 0 CHECK (is_temporary IN (0, 1)),
    deletion_due_at_utc TEXT,
    state TEXT NOT NULL DEFAULT 'READY'
        CHECK (state IN ('CREATING','READY','IN_USE','FAILED','DELETED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (source_evidence_file_id) REFERENCES evidence_files(id) ON DELETE RESTRICT
);
"""

CREATE_ACQUISITION_SESSIONS = """
CREATE TABLE IF NOT EXISTS acquisition_sessions (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    evidence_item_id INTEGER,
    acquisition_code TEXT NOT NULL UNIQUE,
    acquisition_type TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL CHECK (status IN ('STARTED','COMPLETED','CANCELLED','FAILED')),
    source_description TEXT,
    host_name TEXT,
    host_operating_system TEXT,
    tool_version TEXT NOT NULL,
    examiner_id INTEGER,
    notes TEXT,
    error_summary TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id) ON DELETE SET NULL,
    FOREIGN KEY (examiner_id) REFERENCES examiners(id) ON DELETE SET NULL
);
"""

CREATE_CHAIN_OF_CUSTODY = """
CREATE TABLE IF NOT EXISTS chain_of_custody (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    evidence_item_id INTEGER,
    event_type TEXT NOT NULL,
    event_description TEXT NOT NULL,
    from_person_or_location TEXT,
    to_person_or_location TEXT,
    performed_by_examiner_id INTEGER,
    occurred_at_utc TEXT NOT NULL,
    signature_reference TEXT,
    notes TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id) ON DELETE RESTRICT,
    FOREIGN KEY (performed_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL
);
"""

CREATE_TOOL_VERSIONS = """
CREATE TABLE IF NOT EXISTS tool_versions (
    id INTEGER PRIMARY KEY,
    component_name TEXT NOT NULL,
    component_version TEXT NOT NULL,
    package_hash TEXT,
    build_identifier TEXT,
    recorded_at_utc TEXT NOT NULL,
    UNIQUE (component_name, component_version, build_identifier)
);
"""

CREATE_PARSER_RUNS = """
CREATE TABLE IF NOT EXISTS parser_runs (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    evidence_item_id INTEGER NOT NULL,
    source_evidence_file_id INTEGER,
    working_copy_id INTEGER,
    parser_name TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    adapter_id TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    schema_fingerprint TEXT,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL CHECK (status IN ('STARTED','COMPLETED','PARTIAL','UNSUPPORTED','CANCELLED','FAILED')),
    parsed_record_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id) ON DELETE RESTRICT,
    FOREIGN KEY (source_evidence_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (working_copy_id) REFERENCES working_copies(id) ON DELETE SET NULL
);
"""

CREATE_SCHEMA_MAPPINGS = """
CREATE TABLE IF NOT EXISTS schema_mappings (
    id INTEGER PRIMARY KEY,
    parser_run_id INTEGER NOT NULL,
    source_table TEXT NOT NULL,
    source_column TEXT NOT NULL,
    internal_entity TEXT NOT NULL,
    internal_field TEXT NOT NULL,
    transformation_description TEXT,
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH','MEDIUM','LOW','UNRESOLVED')),
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (parser_run_id) REFERENCES parser_runs(id) ON DELETE CASCADE
);
"""

CREATE_PARSER_WARNINGS = """
CREATE TABLE IF NOT EXISTS parser_warnings (
    id INTEGER PRIMARY KEY,
    parser_run_id INTEGER NOT NULL,
    evidence_file_id INTEGER,
    warning_code TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('INFO','WARNING','ERROR','CRITICAL')),
    message TEXT NOT NULL,
    source_table TEXT,
    source_record_id TEXT,
    source_page_number INTEGER,
    source_byte_offset INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (parser_run_id) REFERENCES parser_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL
);
"""

CREATE_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    account_identifier TEXT,
    phone_number_raw TEXT,
    phone_number_normalized TEXT,
    display_name TEXT,
    account_type TEXT,
    is_device_owner INTEGER NOT NULL DEFAULT 0 CHECK (is_device_owner IN (0, 1)),
    origin TEXT NOT NULL CHECK (origin IN ('PARSED','RECOVERED','INFERRED','MANUAL','IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH','MEDIUM','LOW','UNRESOLVED','NOT_APPLICABLE')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT
);
"""

CREATE_CONTACTS = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    contact_code TEXT NOT NULL,
    whatsapp_identifier TEXT,
    phone_number_raw TEXT,
    phone_number_normalized TEXT,
    display_name TEXT,
    given_name TEXT,
    family_name TEXT,
    business_name TEXT,
    profile_photo_media_id INTEGER,
    is_business INTEGER NOT NULL DEFAULT 0 CHECK (is_business IN (0, 1)),
    is_blocked INTEGER,
    is_saved_contact INTEGER,
    origin TEXT NOT NULL CHECK (origin IN ('PARSED','RECOVERED','INFERRED','MANUAL','IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH','MEDIUM','LOW','UNRESOLVED','NOT_APPLICABLE')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    UNIQUE (case_id, contact_code)
);
"""

CREATE_CONTACT_ALIASES = """
CREATE TABLE IF NOT EXISTS contact_aliases (
    id INTEGER PRIMARY KEY,
    contact_id INTEGER NOT NULL,
    alias_type TEXT NOT NULL,
    alias_value TEXT NOT NULL,
    valid_from_utc TEXT,
    valid_until_utc TEXT,
    source_file_id INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
    FOREIGN KEY (source_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL
);
"""

CREATE_GROUPS = """
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    group_code TEXT NOT NULL,
    whatsapp_group_identifier TEXT,
    subject TEXT,
    description TEXT,
    creator_contact_id INTEGER,
    created_timestamp_raw TEXT,
    created_at_source_utc TEXT,
    origin TEXT NOT NULL CHECK (origin IN ('PARSED','RECOVERED','INFERRED','MANUAL','IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH','MEDIUM','LOW','UNRESOLVED','NOT_APPLICABLE')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (creator_contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    UNIQUE (case_id, group_code)
);
"""

CREATE_GROUP_PARTICIPANTS = """
CREATE TABLE IF NOT EXISTS group_participants (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL,
    contact_id INTEGER,
    participant_identifier TEXT,
    role TEXT,
    joined_timestamp_raw TEXT,
    joined_at_utc TEXT,
    left_timestamp_raw TEXT,
    left_at_utc TEXT,
    origin TEXT NOT NULL CHECK (origin IN ('PARSED','RECOVERED','INFERRED','MANUAL','IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH','MEDIUM','LOW','UNRESOLVED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL
);
"""

CREATE_CONVERSATIONS = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    conversation_code TEXT NOT NULL,
    conversation_type TEXT NOT NULL CHECK (conversation_type IN ('DIRECT','GROUP','BROADCAST','UNKNOWN')),
    contact_id INTEGER,
    group_id INTEGER,
    title TEXT,
    source_conversation_identifier TEXT,
    first_event_at_utc TEXT,
    last_event_at_utc TEXT,
    message_count INTEGER NOT NULL DEFAULT 0,
    call_count INTEGER NOT NULL DEFAULT 0,
    origin TEXT NOT NULL CHECK (origin IN ('PARSED','RECOVERED','INFERRED','MANUAL','IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH','MEDIUM','LOW','UNRESOLVED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL,
    UNIQUE (case_id, conversation_code),
    CHECK ((conversation_type='DIRECT' AND contact_id IS NOT NULL)
        OR (conversation_type='GROUP' AND group_id IS NOT NULL)
        OR conversation_type IN ('BROADCAST','UNKNOWN'))
);
"""

CREATE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    message_code TEXT NOT NULL,
    conversation_id INTEGER NOT NULL,
    sender_contact_id INTEGER,
    sender_account_id INTEGER,
    source_message_identifier TEXT,
    source_record_id TEXT,
    source_table TEXT,
    direction TEXT NOT NULL CHECK (direction IN ('INCOMING','OUTGOING','SYSTEM','UNKNOWN')),
    message_type TEXT NOT NULL,
    text_content TEXT,
    caption_text TEXT,
    timestamp_raw TEXT,
    timestamp_epoch_value INTEGER,
    timestamp_epoch_unit TEXT,
    sent_at_utc TEXT,
    delivered_at_utc TEXT,
    read_at_utc TEXT,
    deleted_at_utc TEXT,
    edited_at_utc TEXT,
    is_deleted_marker INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted_marker IN (0, 1)),
    is_forwarded INTEGER NOT NULL DEFAULT 0 CHECK (is_forwarded IN (0, 1)),
    is_starred INTEGER NOT NULL DEFAULT 0 CHECK (is_starred IN (0, 1)),
    is_view_once INTEGER NOT NULL DEFAULT 0 CHECK (is_view_once IN (0, 1)),
    raw_extension_json TEXT,
    origin TEXT NOT NULL CHECK (origin IN ('PARSED','RECOVERED','INFERRED','MANUAL','IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH','MEDIUM','LOW','UNRESOLVED','NOT_APPLICABLE')),
    validation_status TEXT NOT NULL DEFAULT 'VALIDATED'
        CHECK (validation_status IN ('VALIDATED','PARTIAL','UNVERIFIED','REJECTED','UNSUPPORTED')),
    source_evidence_file_id INTEGER,
    parser_run_id INTEGER,
    source_page_number INTEGER,
    source_byte_offset INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE RESTRICT,
    FOREIGN KEY (sender_contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (sender_account_id) REFERENCES accounts(id) ON DELETE SET NULL,
    FOREIGN KEY (source_evidence_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (parser_run_id) REFERENCES parser_runs(id) ON DELETE SET NULL,
    UNIQUE (case_id, message_code)
);
"""

CREATE_MESSAGE_REVISIONS = """
CREATE TABLE IF NOT EXISTS message_revisions (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    revision_number INTEGER NOT NULL,
    text_content TEXT,
    caption_text TEXT,
    revised_timestamp_raw TEXT,
    revised_at_utc TEXT,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    source_evidence_file_id INTEGER,
    source_record_id TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (source_evidence_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL,
    UNIQUE (message_id, revision_number)
);
"""

CREATE_MESSAGE_REACTIONS = """
CREATE TABLE IF NOT EXISTS message_reactions (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    reactor_contact_id INTEGER,
    reactor_identifier TEXT,
    reaction_value TEXT NOT NULL,
    timestamp_raw TEXT,
    reacted_at_utc TEXT,
    removed_at_utc TEXT,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (reactor_contact_id) REFERENCES contacts(id) ON DELETE SET NULL
);
"""

CREATE_MESSAGE_QUOTES = """
CREATE TABLE IF NOT EXISTS message_quotes (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL UNIQUE,
    quoted_message_id INTEGER,
    quoted_source_identifier TEXT,
    quoted_sender_identifier TEXT,
    quoted_text_snapshot TEXT,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (quoted_message_id) REFERENCES messages(id) ON DELETE SET NULL
);
"""

CREATE_MESSAGE_MENTIONS = """
CREATE TABLE IF NOT EXISTS message_mentions (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    mentioned_contact_id INTEGER,
    mentioned_identifier TEXT NOT NULL,
    character_start INTEGER,
    character_end INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (mentioned_contact_id) REFERENCES contacts(id) ON DELETE SET NULL
);
"""

CREATE_SYSTEM_EVENTS = """
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    conversation_id INTEGER,
    related_message_id INTEGER,
    event_type TEXT NOT NULL,
    event_description TEXT,
    actor_contact_id INTEGER,
    target_contact_id INTEGER,
    timestamp_raw TEXT,
    occurred_at_utc TEXT,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    source_evidence_file_id INTEGER,
    source_record_id TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (related_message_id) REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (actor_contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (target_contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (source_evidence_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL
);
"""

CREATE_LOCATIONS = """
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY,
    message_id INTEGER,
    latitude REAL,
    longitude REAL,
    accuracy_meters REAL,
    place_name TEXT,
    address_text TEXT,
    is_live_location INTEGER NOT NULL DEFAULT 0 CHECK (is_live_location IN (0, 1)),
    live_duration_seconds INTEGER,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)),
    CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180))
);
"""

CREATE_SHARED_CONTACTS = """
CREATE TABLE IF NOT EXISTS shared_contacts (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    display_name TEXT,
    phone_number_raw TEXT,
    phone_number_normalized TEXT,
    vcard_text TEXT,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);
"""

CREATE_LINKS = """
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY,
    message_id INTEGER,
    url_raw TEXT NOT NULL,
    url_normalized TEXT,
    scheme TEXT,
    domain TEXT,
    title TEXT,
    description TEXT,
    is_suspicious INTEGER NOT NULL DEFAULT 0 CHECK (is_suspicious IN (0, 1)),
    scan_status TEXT,
    scan_provider TEXT,
    scan_result_json TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);
"""

CREATE_MEDIA_ITEMS = """
CREATE TABLE IF NOT EXISTS media_items (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    media_code TEXT NOT NULL,
    message_id INTEGER,
    evidence_file_id INTEGER,
    parent_media_id INTEGER,
    original_filename TEXT,
    stored_relative_path TEXT,
    preview_relative_path TEXT,
    declared_mime_type TEXT,
    detected_mime_type TEXT,
    file_extension TEXT,
    size_bytes INTEGER CHECK (size_bytes >= 0),
    sha256 TEXT,
    width_pixels INTEGER,
    height_pixels INTEGER,
    duration_milliseconds INTEGER,
    media_role TEXT,
    is_missing INTEGER NOT NULL DEFAULT 0 CHECK (is_missing IN (0, 1)),
    is_orphan INTEGER NOT NULL DEFAULT 0 CHECK (is_orphan IN (0, 1)),
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    source_evidence_file_id INTEGER,
    parser_run_id INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (evidence_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_media_id) REFERENCES media_items(id) ON DELETE SET NULL,
    FOREIGN KEY (source_evidence_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (parser_run_id) REFERENCES parser_runs(id) ON DELETE SET NULL,
    UNIQUE (case_id, media_code)
);
"""

CREATE_MEDIA_METADATA = """
CREATE TABLE IF NOT EXISTS media_metadata (
    id INTEGER PRIMARY KEY,
    media_item_id INTEGER NOT NULL,
    metadata_namespace TEXT NOT NULL,
    metadata_key TEXT NOT NULL,
    metadata_value_text TEXT,
    metadata_value_number REAL,
    metadata_value_json TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (media_item_id) REFERENCES media_items(id) ON DELETE CASCADE,
    UNIQUE (media_item_id, metadata_namespace, metadata_key)
);
"""

CREATE_EXIF_RECORDS = """
CREATE TABLE IF NOT EXISTS exif_records (
    id INTEGER PRIMARY KEY,
    media_item_id INTEGER NOT NULL UNIQUE,
    camera_make TEXT,
    camera_model TEXT,
    software TEXT,
    captured_timestamp_raw TEXT,
    captured_at_utc TEXT,
    latitude REAL,
    longitude REAL,
    altitude_meters REAL,
    orientation INTEGER,
    raw_exif_json TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (media_item_id) REFERENCES media_items(id) ON DELETE CASCADE,
    CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)),
    CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180))
);
"""

CREATE_MEDIA_CORRELATIONS = """
CREATE TABLE IF NOT EXISTS media_correlations (
    id INTEGER PRIMARY KEY,
    media_item_id INTEGER NOT NULL,
    candidate_message_id INTEGER,
    correlation_method TEXT NOT NULL,
    score REAL NOT NULL CHECK (score BETWEEN 0 AND 1),
    explanation TEXT NOT NULL,
    accepted_by_examiner_id INTEGER,
    accepted_at_utc TEXT,
    status TEXT NOT NULL DEFAULT 'UNRESOLVED'
        CHECK (status IN ('ACCEPTED','REJECTED','UNRESOLVED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (media_item_id) REFERENCES media_items(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_message_id) REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (accepted_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL
);
"""

CREATE_CALLS = """
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    call_code TEXT NOT NULL,
    conversation_id INTEGER,
    source_call_identifier TEXT,
    source_record_id TEXT,
    call_type TEXT NOT NULL CHECK (call_type IN ('VOICE','VIDEO','GROUP_VOICE','GROUP_VIDEO','UNKNOWN')),
    direction TEXT NOT NULL CHECK (direction IN ('INCOMING','OUTGOING','MISSED','DECLINED','UNKNOWN')),
    timestamp_raw TEXT,
    started_at_utc TEXT,
    ended_at_utc TEXT,
    duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    was_answered INTEGER,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    source_evidence_file_id INTEGER,
    parser_run_id INTEGER,
    source_page_number INTEGER,
    source_byte_offset INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (source_evidence_file_id) REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (parser_run_id) REFERENCES parser_runs(id) ON DELETE SET NULL,
    UNIQUE (case_id, call_code)
);
"""

CREATE_CALL_PARTICIPANTS = """
CREATE TABLE IF NOT EXISTS call_participants (
    id INTEGER PRIMARY KEY,
    call_id INTEGER NOT NULL,
    contact_id INTEGER,
    account_id INTEGER,
    participant_identifier TEXT,
    participant_role TEXT,
    joined_at_utc TEXT,
    left_at_utc TEXT,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (call_id) REFERENCES calls(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
);
"""

CREATE_RECOVERY_RUNS = """
CREATE TABLE IF NOT EXISTS recovery_runs (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    recovery_code TEXT NOT NULL UNIQUE,
    strategy TEXT NOT NULL,
    source_evidence_file_id INTEGER NOT NULL,
    working_copy_id INTEGER,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL CHECK (status IN ('STARTED','COMPLETED','PARTIAL','CANCELLED','FAILED')),
    candidate_count INTEGER NOT NULL DEFAULT 0,
    accepted_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    unresolved_count INTEGER NOT NULL DEFAULT 0,
    tool_component_version TEXT NOT NULL,
    parameters_json TEXT,
    error_summary TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (source_evidence_file_id) REFERENCES evidence_files(id) ON DELETE RESTRICT,
    FOREIGN KEY (working_copy_id) REFERENCES working_copies(id) ON DELETE SET NULL
);
"""

CREATE_RECOVERY_CANDIDATES = """
CREATE TABLE IF NOT EXISTS recovery_candidates (
    id INTEGER PRIMARY KEY,
    recovery_run_id INTEGER NOT NULL,
    candidate_code TEXT NOT NULL,
    candidate_type TEXT NOT NULL,
    source_page_number INTEGER,
    source_byte_offset INTEGER,
    wal_frame_number INTEGER,
    journal_offset INTEGER,
    raw_fragment_relative_path TEXT,
    raw_fragment_sha256 TEXT,
    parsed_fields_json TEXT,
    validation_checks_json TEXT,
    confidence_level TEXT NOT NULL CHECK (confidence_level IN ('HIGH','MEDIUM','LOW','UNRESOLVED')),
    confidence_score REAL CHECK (confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1),
    review_status TEXT NOT NULL DEFAULT 'UNRESOLVED' CHECK (review_status IN ('ACCEPTED','REJECTED','UNRESOLVED')),
    reviewed_by_examiner_id INTEGER,
    reviewed_at_utc TEXT,
    review_notes TEXT,
    duplicate_group_key TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (recovery_run_id) REFERENCES recovery_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (recovery_run_id, candidate_code)
);
"""

CREATE_RECOVERED_RECORDS = """
CREATE TABLE IF NOT EXISTS recovered_records (
    id INTEGER PRIMARY KEY,
    recovery_candidate_id INTEGER NOT NULL UNIQUE,
    artefact_type TEXT NOT NULL,
    artefact_id INTEGER NOT NULL,
    acceptance_reason TEXT,
    accepted_at_utc TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (recovery_candidate_id) REFERENCES recovery_candidates(id) ON DELETE RESTRICT
);
"""

CREATE_NETWORK_CAPTURE_SESSIONS = """
CREATE TABLE IF NOT EXISTS network_capture_sessions (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    capture_code TEXT NOT NULL UNIQUE,
    evidence_item_id INTEGER,
    interface_name TEXT,
    capture_mode TEXT NOT NULL CHECK (capture_mode IN ('LIVE_PASSIVE','PCAP_IMPORT')),
    authorisation_id INTEGER,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL CHECK (status IN ('STARTED','COMPLETED','CANCELLED','FAILED')),
    pcap_relative_path TEXT,
    pcap_sha256 TEXT,
    capture_filter TEXT,
    packet_count INTEGER NOT NULL DEFAULT 0,
    bytes_captured INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id) ON DELETE SET NULL,
    FOREIGN KEY (authorisation_id) REFERENCES authorisations(id) ON DELETE SET NULL
);
"""

CREATE_NETWORK_FLOWS = """
CREATE TABLE IF NOT EXISTS network_flows (
    id INTEGER PRIMARY KEY,
    capture_session_id INTEGER NOT NULL,
    protocol TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    source_port INTEGER,
    destination_ip TEXT NOT NULL,
    destination_port INTEGER,
    first_seen_at_utc TEXT NOT NULL,
    last_seen_at_utc TEXT NOT NULL,
    packet_count INTEGER NOT NULL DEFAULT 0,
    byte_count INTEGER NOT NULL DEFAULT 0,
    suspected_service TEXT,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (capture_session_id) REFERENCES network_capture_sessions(id) ON DELETE CASCADE
);
"""

CREATE_NETWORK_ENDPOINTS = """
CREATE TABLE IF NOT EXISTS network_endpoints (
    id INTEGER PRIMARY KEY,
    capture_session_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    endpoint_classification TEXT NOT NULL
        CHECK (endpoint_classification IN ('PROBABLE_PEER','WHATSAPP_RELAY','TURN_SERVER','CLOUD_INFRASTRUCTURE','MOBILE_CARRIER_GATEWAY','VPN_OR_PROXY','LOCAL_GATEWAY','UNKNOWN')),
    classification_confidence TEXT NOT NULL,
    isp_name TEXT,
    asn TEXT,
    country_code TEXT,
    country_name TEXT,
    region_name TEXT,
    city_name TEXT,
    latitude REAL,
    longitude REAL,
    geoip_database_version TEXT,
    first_seen_at_utc TEXT NOT NULL,
    last_seen_at_utc TEXT NOT NULL,
    packet_count INTEGER NOT NULL DEFAULT 0,
    warning_text TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (capture_session_id) REFERENCES network_capture_sessions(id) ON DELETE CASCADE,
    UNIQUE (capture_session_id, ip_address),
    CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)),
    CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180))
);
"""

CREATE_STUN_TURN_EVENTS = """
CREATE TABLE IF NOT EXISTS stun_turn_events (
    id INTEGER PRIMARY KEY,
    capture_session_id INTEGER NOT NULL,
    network_flow_id INTEGER,
    event_type TEXT NOT NULL,
    transaction_id TEXT,
    mapped_ip TEXT,
    mapped_port INTEGER,
    relay_ip TEXT,
    relay_port INTEGER,
    server_ip TEXT,
    occurred_at_utc TEXT NOT NULL,
    packet_number INTEGER,
    parse_confidence TEXT NOT NULL,
    raw_summary_json TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (capture_session_id) REFERENCES network_capture_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (network_flow_id) REFERENCES network_flows(id) ON DELETE SET NULL
);
"""

CREATE_TIMELINE_EVENTS = """
CREATE TABLE IF NOT EXISTS timeline_events (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    event_code TEXT NOT NULL,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    occurred_at_raw TEXT,
    occurred_at_utc TEXT,
    display_timezone TEXT,
    clock_skew_seconds INTEGER NOT NULL DEFAULT 0,
    artefact_type TEXT,
    artefact_id INTEGER,
    conversation_id INTEGER,
    contact_id INTEGER,
    evidence_item_id INTEGER,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(id) ON DELETE SET NULL,
    UNIQUE (case_id, event_code)
);
"""

CREATE_TAGS = """
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_by_examiner_id INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, name)
);
"""

CREATE_ARTEFACT_TAGS = """
CREATE TABLE IF NOT EXISTS artefact_tags (
    id INTEGER PRIMARY KEY,
    tag_id INTEGER NOT NULL,
    artefact_type TEXT NOT NULL,
    artefact_id INTEGER NOT NULL,
    applied_by_examiner_id INTEGER,
    applied_at_utc TEXT NOT NULL,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    FOREIGN KEY (applied_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (tag_id, artefact_type, artefact_id)
);
"""

CREATE_BOOKMARKS = """
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    artefact_type TEXT NOT NULL,
    artefact_id INTEGER NOT NULL,
    title TEXT,
    created_by_examiner_id INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, artefact_type, artefact_id)
);
"""

CREATE_EXAMINER_NOTES = """
CREATE TABLE IF NOT EXISTS examiner_notes (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    artefact_type TEXT,
    artefact_id INTEGER,
    note_text TEXT NOT NULL,
    created_by_examiner_id INTEGER,
    is_private INTEGER NOT NULL DEFAULT 0 CHECK (is_private IN (0, 1)),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL
);
"""

CREATE_SAVED_SEARCHES = """
CREATE TABLE IF NOT EXISTS saved_searches (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    query_text TEXT,
    filters_json TEXT NOT NULL,
    sort_json TEXT,
    created_by_examiner_id INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, name)
);
"""

CREATE_AUDIT_EVENTS = """
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    event_sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_description TEXT NOT NULL,
    examiner_id INTEGER,
    component_name TEXT NOT NULL,
    component_version TEXT NOT NULL,
    object_type TEXT,
    object_id TEXT,
    details_json TEXT,
    previous_event_hash TEXT,
    event_hash TEXT NOT NULL,
    occurred_at_utc TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (examiner_id) REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, event_sequence),
    UNIQUE (case_id, event_hash)
);
"""

CREATE_REPORT_RUNS = """
CREATE TABLE IF NOT EXISTS report_runs (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    report_code TEXT NOT NULL,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    generated_by_examiner_id INTEGER,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL CHECK (status IN ('STARTED','COMPLETED','PARTIAL','CANCELLED','FAILED')),
    query_definition_json TEXT,
    filters_json TEXT,
    sort_json TEXT,
    template_name TEXT NOT NULL,
    template_version TEXT NOT NULL,
    generator_version TEXT NOT NULL,
    display_timezone TEXT NOT NULL,
    limitations_text TEXT,
    redaction_applied INTEGER NOT NULL DEFAULT 0 CHECK (redaction_applied IN (0, 1)),
    error_summary TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (generated_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, report_code)
);
"""

CREATE_REPORT_FILES = """
CREATE TABLE IF NOT EXISTS report_files (
    id INTEGER PRIMARY KEY,
    report_run_id INTEGER NOT NULL,
    file_format TEXT NOT NULL,
    stored_relative_path TEXT NOT NULL UNIQUE,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    signature_relative_path TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (report_run_id) REFERENCES report_runs(id) ON DELETE CASCADE
);
"""

CREATE_REDACTION_RULES = """
CREATE TABLE IF NOT EXISTS redaction_rules (
    id INTEGER PRIMARY KEY,
    report_run_id INTEGER,
    case_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    pattern_text TEXT,
    replacement_text TEXT,
    target_field TEXT,
    is_enabled INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0, 1)),
    created_by_examiner_id INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (report_run_id) REFERENCES report_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id) REFERENCES examiners(id) ON DELETE SET NULL
);
"""

CREATE_EXPORT_MANIFESTS = """
CREATE TABLE IF NOT EXISTS export_manifests (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    report_run_id INTEGER,
    export_code TEXT NOT NULL UNIQUE,
    manifest_relative_path TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    file_count INTEGER NOT NULL DEFAULT 0,
    total_size_bytes INTEGER NOT NULL DEFAULT 0,
    signature_relative_path TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (report_run_id) REFERENCES report_runs(id) ON DELETE SET NULL
);
"""

CREATE_SCHEMA_MIGRATIONS = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL UNIQUE,
    migration_name TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL,
    application_version TEXT NOT NULL,
    checksum TEXT NOT NULL
);
"""

CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS message_search USING fts5(
    message_code UNINDEXED,
    conversation_id UNINDEXED,
    contact_text,
    conversation_text,
    message_text,
    caption_text,
    link_text,
    tokenize = 'unicode61'
);
"""

ALL_TABLE_DDL = [
    CREATE_CASES,
    CREATE_EXAMINERS,
    CREATE_AUTHORISATIONS,
    CREATE_EVIDENCE_ITEMS,
    CREATE_EVIDENCE_FILES,
    CREATE_EVIDENCE_HASHES,
    CREATE_WORKING_COPIES,
    CREATE_ACQUISITION_SESSIONS,
    CREATE_CHAIN_OF_CUSTODY,
    CREATE_TOOL_VERSIONS,
    CREATE_PARSER_RUNS,
    CREATE_SCHEMA_MAPPINGS,
    CREATE_PARSER_WARNINGS,
    CREATE_ACCOUNTS,
    CREATE_CONTACTS,
    CREATE_CONTACT_ALIASES,
    CREATE_GROUPS,
    CREATE_GROUP_PARTICIPANTS,
    CREATE_CONVERSATIONS,
    CREATE_MESSAGES,
    CREATE_MESSAGE_REVISIONS,
    CREATE_MESSAGE_REACTIONS,
    CREATE_MESSAGE_QUOTES,
    CREATE_MESSAGE_MENTIONS,
    CREATE_SYSTEM_EVENTS,
    CREATE_LOCATIONS,
    CREATE_SHARED_CONTACTS,
    CREATE_LINKS,
    CREATE_MEDIA_ITEMS,
    CREATE_MEDIA_METADATA,
    CREATE_EXIF_RECORDS,
    CREATE_MEDIA_CORRELATIONS,
    CREATE_CALLS,
    CREATE_CALL_PARTICIPANTS,
    CREATE_RECOVERY_RUNS,
    CREATE_RECOVERY_CANDIDATES,
    CREATE_RECOVERED_RECORDS,
    CREATE_NETWORK_CAPTURE_SESSIONS,
    CREATE_NETWORK_FLOWS,
    CREATE_NETWORK_ENDPOINTS,
    CREATE_STUN_TURN_EVENTS,
    CREATE_TIMELINE_EVENTS,
    CREATE_TAGS,
    CREATE_ARTEFACT_TAGS,
    CREATE_BOOKMARKS,
    CREATE_EXAMINER_NOTES,
    CREATE_SAVED_SEARCHES,
    CREATE_AUDIT_EVENTS,
    CREATE_REPORT_RUNS,
    CREATE_REPORT_FILES,
    CREATE_REDACTION_RULES,
    CREATE_EXPORT_MANIFESTS,
    CREATE_SCHEMA_MIGRATIONS,
    CREATE_FTS,
]

ALL_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_evidence_items_case ON evidence_items(case_id);",
    "CREATE INDEX IF NOT EXISTS idx_evidence_files_item ON evidence_files(evidence_item_id);",
    "CREATE INDEX IF NOT EXISTS idx_evidence_hashes_value ON evidence_hashes(algorithm, hash_value);",
    "CREATE INDEX IF NOT EXISTS idx_messages_conversation_time ON messages(conversation_id, sent_at_utc);",
    "CREATE INDEX IF NOT EXISTS idx_messages_case_time ON messages(case_id, sent_at_utc);",
    "CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_contact_id);",
    "CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);",
    "CREATE INDEX IF NOT EXISTS idx_messages_origin_confidence ON messages(origin, confidence_level);",
    "CREATE INDEX IF NOT EXISTS idx_messages_source_record ON messages(source_evidence_file_id, source_table, source_record_id);",
    "CREATE INDEX IF NOT EXISTS idx_media_message ON media_items(message_id);",
    "CREATE INDEX IF NOT EXISTS idx_media_sha256 ON media_items(sha256);",
    "CREATE INDEX IF NOT EXISTS idx_media_orphan ON media_items(is_orphan);",
    "CREATE INDEX IF NOT EXISTS idx_calls_conversation_time ON calls(conversation_id, started_at_utc);",
    "CREATE INDEX IF NOT EXISTS idx_calls_case_time ON calls(case_id, started_at_utc);",
    "CREATE INDEX IF NOT EXISTS idx_calls_type_direction ON calls(call_type, direction);",
    "CREATE INDEX IF NOT EXISTS idx_recovery_candidates_run_status ON recovery_candidates(recovery_run_id, review_status);",
    "CREATE INDEX IF NOT EXISTS idx_recovery_candidates_confidence ON recovery_candidates(confidence_level);",
    "CREATE INDEX IF NOT EXISTS idx_recovery_candidates_location ON recovery_candidates(recovery_run_id, source_page_number, source_byte_offset);",
    "CREATE INDEX IF NOT EXISTS idx_timeline_case_time ON timeline_events(case_id, occurred_at_utc);",
    "CREATE INDEX IF NOT EXISTS idx_timeline_conversation_time ON timeline_events(conversation_id, occurred_at_utc);",
    "CREATE INDEX IF NOT EXISTS idx_timeline_artefact ON timeline_events(artefact_type, artefact_id);",
    "CREATE INDEX IF NOT EXISTS idx_network_flows_session_time ON network_flows(capture_session_id, first_seen_at_utc);",
    "CREATE INDEX IF NOT EXISTS idx_network_endpoints_ip ON network_endpoints(ip_address);",
    "CREATE INDEX IF NOT EXISTS idx_stun_turn_session_time ON stun_turn_events(capture_session_id, occurred_at_utc);",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_messages_source_identity ON messages(source_evidence_file_id, source_table, source_record_id, parser_run_id) WHERE source_record_id IS NOT NULL;",
]
