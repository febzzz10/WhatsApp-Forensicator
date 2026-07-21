# WhatsApp Forensic Toolkit — Database Design

**Document version:** 1.0  
**Project:** WhatsApp Forensic Toolkit  
**Database engine:** SQLite 3  
**Primary database:** One `case.db` per forensic case  
**Architecture:** Case-isolated relational database with strict provenance and evidence separation  
**Primary language:** Python 3.11+  
**ORM/query approach:** SQLAlchemy 2.x or parameterised `sqlite3`  
**Search:** SQLite FTS5  
**Migration strategy:** Versioned transactional migrations  

---

## 1. Purpose

This document defines the database architecture for the WhatsApp Forensic Toolkit.

The database stores:

- case metadata;
- examiner and authorisation records;
- evidence inventory;
- file hashes;
- acquisition sessions;
- contacts and groups;
- parsed messages;
- recovered message candidates;
- call records;
- media metadata;
- timeline events;
- network metadata;
- examiner notes;
- tags and bookmarks;
- audit events;
- report history;
- parser and tool versions.

The database must not replace or modify original evidence. Original evidence remains in the case repository under the `originals/` directory. The database stores metadata, provenance, parsed records, recovered records and analysis results.

---

## 2. Database Principles

The database design follows these principles:

1. One database per forensic case.
2. Original evidence is stored outside the database.
3. Evidence files are referenced by hash and immutable identifiers.
4. Every artefact must retain provenance.
5. Parsed, recovered and inferred data remain distinguishable.
6. Raw source values are preserved where practical.
7. Normalised values are stored separately.
8. Timestamps are stored in UTC without discarding source values.
9. Unsupported or partially parsed data must not be silently discarded.
10. Schema changes use transactional migrations.
11. Destructive cascading is limited.
12. Large binary media files are not stored as database BLOBs by default.
13. Search indexes contain derived data only.
14. Case databases must be portable and independently verifiable.

---

## 3. Case Repository Relationship

Recommended case structure:

```text
cases/
└── CASE-2026-0001/
    ├── case.toml
    ├── originals/
    ├── working/
    ├── derived/
    ├── reports/
    ├── exports/
    ├── logs/
    ├── manifests/
    └── case.db
```

The database references files through relative case paths.

Example:

```text
originals/E001/msgstore.db
working/W001/msgstore-working.db
derived/thumbnails/M000045.webp
reports/R000012/report.pdf
```

Absolute source paths may be stored for acquisition documentation, but application processing should use case-relative paths.

---

## 4. SQLite Configuration

Every database connection must enable:

```sql
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
PRAGMA temp_store = MEMORY;
PRAGMA trusted_schema = OFF;
```

For the application-owned `case.db`:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
```

For source evidence databases:

```text
Open read-only.
Do not change journal mode.
Do not run VACUUM.
Do not create indexes.
Do not update SQLite metadata.
```

### 4.1 Integrity Checks

Run during:

- case open;
- backup;
- migration;
- restore;
- release validation.

```sql
PRAGMA quick_check;
PRAGMA foreign_key_check;
```

Run `PRAGMA integrity_check` for deeper verification when requested.

---

## 5. Naming Conventions

### Tables

Use plural snake_case names:

```text
evidence_items
message_reactions
network_endpoints
```

### Columns

Use snake_case:

```text
created_at_utc
source_record_id
confidence_level
```

### Primary Keys

Use `id` as an integer primary key unless a public identifier is also required.

### Public Identifiers

Human-readable or export-safe identifiers:

```text
CASE-2026-0001
E000001
M000000123
RPT-000042
```

Store them in explicit columns such as:

```text
case_code
evidence_code
message_code
report_code
```

### Foreign Keys

Use singular table concept followed by `_id`:

```text
case_id
evidence_item_id
conversation_id
```

### Boolean Values

Store SQLite booleans as integers constrained to `0` or `1`.

---

## 6. Common Column Standards

Most operational tables should contain:

```sql
id                INTEGER PRIMARY KEY
created_at_utc    TEXT NOT NULL
updated_at_utc    TEXT NOT NULL
```

Recommended UTC format:

```text
2026-07-19T14:25:00.123456Z
```

Where provenance is required:

```text
source_file_id
source_record_id
source_table
source_page_number
source_byte_offset
parser_run_id
confidence_level
```

---

## 7. Enumerations

SQLite has no native enum type. Use `TEXT` with `CHECK` constraints.

### 7.1 Case Status

```text
OPEN
LOCKED
ARCHIVED
CLOSED
```

### 7.2 Evidence State

```text
REGISTERED
COPYING
VERIFIED
HASH_MISMATCH
QUARANTINED
UNSUPPORTED
PARSED
PARTIALLY_PARSED
FAILED
```

### 7.3 Artefact Origin

```text
PARSED
RECOVERED
INFERRED
MANUAL
IMPORTED
```

### 7.4 Confidence Level

```text
HIGH
MEDIUM
LOW
UNRESOLVED
NOT_APPLICABLE
```

### 7.5 Validation Status

```text
VALIDATED
PARTIAL
UNVERIFIED
REJECTED
UNSUPPORTED
```

### 7.6 Message Direction

```text
INCOMING
OUTGOING
SYSTEM
UNKNOWN
```

### 7.7 Message Type

```text
TEXT
IMAGE
VIDEO
AUDIO
VOICE_NOTE
DOCUMENT
STICKER
GIF
LOCATION
LIVE_LOCATION
CONTACT
POLL
CALL_EVENT
SYSTEM
UNKNOWN
```

### 7.8 Call Type

```text
VOICE
VIDEO
GROUP_VOICE
GROUP_VIDEO
UNKNOWN
```

### 7.9 Call Direction

```text
INCOMING
OUTGOING
MISSED
DECLINED
UNKNOWN
```

### 7.10 Endpoint Classification

```text
PROBABLE_PEER
WHATSAPP_RELAY
TURN_SERVER
CLOUD_INFRASTRUCTURE
MOBILE_CARRIER_GATEWAY
VPN_OR_PROXY
LOCAL_GATEWAY
UNKNOWN
```

---

## 8. Entity Relationship Overview

```text
cases
 ├── examiners
 ├── authorisations
 ├── evidence_items
 │    ├── evidence_files
 │    │    ├── evidence_hashes
 │    │    ├── working_copies
 │    │    └── provenance_links
 │    ├── acquisition_sessions
 │    └── parser_runs
 ├── contacts
 ├── groups
 ├── conversations
 │    ├── messages
 │    │    ├── message_revisions
 │    │    ├── message_reactions
 │    │    ├── message_quotes
 │    │    └── media_items
 │    └── calls
 ├── recovery_runs
 │    └── recovery_candidates
 ├── timeline_events
 ├── network_capture_sessions
 │    ├── network_flows
 │    ├── network_endpoints
 │    └── stun_turn_events
 ├── audit_events
 └── report_runs
```

---

# 9. Core Case Tables

## 9.1 `cases`

Stores one row for the active case.

```sql
CREATE TABLE cases (
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
```

### Constraints

- `case_code` must be immutable after evidence is registered.
- `display_timezone` affects display only.
- UTC values remain unchanged when the display time zone changes.

---

## 9.2 `examiners`

```sql
CREATE TABLE examiners (
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
```

Personally identifiable data in this table should be optional and protected through case encryption.

---

## 9.3 `authorisations`

```sql
CREATE TABLE authorisations (
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
```

---

# 10. Evidence Tables

## 10.1 `evidence_items`

Represents a logical evidence source.

```sql
CREATE TABLE evidence_items (
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
        CHECK (
            state IN (
                'REGISTERED',
                'COPYING',
                'VERIFIED',
                'HASH_MISMATCH',
                'QUARANTINED',
                'UNSUPPORTED',
                'PARSED',
                'PARTIALLY_PARSED',
                'FAILED'
            )
        ),
    imported_by_examiner_id INTEGER,
    imported_at_utc TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (imported_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, evidence_code)
);
```

Example `source_type` values:

```text
WHATSAPP_TEXT_EXPORT
WHATSAPP_EXPORT_ZIP
SQLITE_DATABASE
SQLITE_DATABASE_PACKAGE
MEDIA_DIRECTORY
DESKTOP_ARTIFACTS
DECRYPTED_BACKUP
PCAP
PCAPNG
THIRD_PARTY_FORENSIC_EXPORT
GENERIC_FILES
```

---

## 10.2 `evidence_files`

```sql
CREATE TABLE evidence_files (
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
    is_original_copy INTEGER NOT NULL DEFAULT 1
        CHECK (is_original_copy IN (0, 1)),
    is_read_only INTEGER NOT NULL DEFAULT 1
        CHECK (is_read_only IN (0, 1)),
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (
            verification_status IN (
                'VALIDATED',
                'PARTIAL',
                'UNVERIFIED',
                'REJECTED',
                'UNSUPPORTED'
            )
        ),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (evidence_item_id)
        REFERENCES evidence_items(id) ON DELETE RESTRICT,
    UNIQUE (evidence_item_id, file_code),
    UNIQUE (stored_relative_path)
);
```

---

## 10.3 `evidence_hashes`

```sql
CREATE TABLE evidence_hashes (
    id INTEGER PRIMARY KEY,
    evidence_file_id INTEGER NOT NULL,
    algorithm TEXT NOT NULL
        CHECK (algorithm IN ('SHA256', 'SHA512', 'MD5')),
    hash_value TEXT NOT NULL,
    purpose TEXT NOT NULL DEFAULT 'IMPORT',
    calculated_at_utc TEXT NOT NULL,
    calculated_by_tool_version TEXT NOT NULL,
    verified_against_hash_id INTEGER,
    verification_result TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE RESTRICT,
    FOREIGN KEY (verified_against_hash_id)
        REFERENCES evidence_hashes(id) ON DELETE SET NULL,
    UNIQUE (evidence_file_id, algorithm, purpose)
);
```

MD5 may be stored for compatibility, but SHA-256 must be the primary integrity hash.

---

## 10.4 `working_copies`

```sql
CREATE TABLE working_copies (
    id INTEGER PRIMARY KEY,
    source_evidence_file_id INTEGER NOT NULL,
    working_code TEXT NOT NULL UNIQUE,
    stored_relative_path TEXT NOT NULL UNIQUE,
    purpose TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    sha256 TEXT NOT NULL,
    created_by_process TEXT NOT NULL,
    is_temporary INTEGER NOT NULL DEFAULT 0
        CHECK (is_temporary IN (0, 1)),
    deletion_due_at_utc TEXT,
    state TEXT NOT NULL DEFAULT 'READY'
        CHECK (state IN ('CREATING', 'READY', 'IN_USE', 'FAILED', 'DELETED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (source_evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE RESTRICT
);
```

---

## 10.5 `acquisition_sessions`

```sql
CREATE TABLE acquisition_sessions (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    evidence_item_id INTEGER,
    acquisition_code TEXT NOT NULL UNIQUE,
    acquisition_type TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL
        CHECK (status IN ('STARTED', 'COMPLETED', 'CANCELLED', 'FAILED')),
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
    FOREIGN KEY (evidence_item_id)
        REFERENCES evidence_items(id) ON DELETE SET NULL,
    FOREIGN KEY (examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL
);
```

---

## 10.6 `chain_of_custody`

```sql
CREATE TABLE chain_of_custody (
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
    FOREIGN KEY (evidence_item_id)
        REFERENCES evidence_items(id) ON DELETE RESTRICT,
    FOREIGN KEY (performed_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL
);
```

---

# 11. Tool and Parser Metadata

## 11.1 `tool_versions`

```sql
CREATE TABLE tool_versions (
    id INTEGER PRIMARY KEY,
    component_name TEXT NOT NULL,
    component_version TEXT NOT NULL,
    package_hash TEXT,
    build_identifier TEXT,
    recorded_at_utc TEXT NOT NULL,
    UNIQUE (component_name, component_version, build_identifier)
);
```

---

## 11.2 `parser_runs`

```sql
CREATE TABLE parser_runs (
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
    status TEXT NOT NULL
        CHECK (
            status IN (
                'STARTED',
                'COMPLETED',
                'PARTIAL',
                'UNSUPPORTED',
                'CANCELLED',
                'FAILED'
            )
        ),
    parsed_record_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (evidence_item_id)
        REFERENCES evidence_items(id) ON DELETE RESTRICT,
    FOREIGN KEY (source_evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (working_copy_id)
        REFERENCES working_copies(id) ON DELETE SET NULL
);
```

---

## 11.3 `schema_mappings`

```sql
CREATE TABLE schema_mappings (
    id INTEGER PRIMARY KEY,
    parser_run_id INTEGER NOT NULL,
    source_table TEXT NOT NULL,
    source_column TEXT NOT NULL,
    internal_entity TEXT NOT NULL,
    internal_field TEXT NOT NULL,
    transformation_description TEXT,
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'UNRESOLVED')),
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (parser_run_id)
        REFERENCES parser_runs(id) ON DELETE CASCADE
);
```

---

## 11.4 `parser_warnings`

```sql
CREATE TABLE parser_warnings (
    id INTEGER PRIMARY KEY,
    parser_run_id INTEGER NOT NULL,
    evidence_file_id INTEGER,
    warning_code TEXT NOT NULL,
    severity TEXT NOT NULL
        CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    source_table TEXT,
    source_record_id TEXT,
    source_page_number INTEGER,
    source_byte_offset INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (parser_run_id)
        REFERENCES parser_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL
);
```

---

# 12. Identity and Contact Tables

## 12.1 `accounts`

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    account_identifier TEXT,
    phone_number_raw TEXT,
    phone_number_normalized TEXT,
    display_name TEXT,
    account_type TEXT,
    is_device_owner INTEGER NOT NULL DEFAULT 0
        CHECK (is_device_owner IN (0, 1)),
    origin TEXT NOT NULL
        CHECK (origin IN ('PARSED', 'RECOVERED', 'INFERRED', 'MANUAL', 'IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (
            confidence_level IN (
                'HIGH',
                'MEDIUM',
                'LOW',
                'UNRESOLVED',
                'NOT_APPLICABLE'
            )
        ),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT
);
```

---

## 12.2 `contacts`

```sql
CREATE TABLE contacts (
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
    is_business INTEGER NOT NULL DEFAULT 0
        CHECK (is_business IN (0, 1)),
    is_blocked INTEGER,
    is_saved_contact INTEGER,
    origin TEXT NOT NULL
        CHECK (origin IN ('PARSED', 'RECOVERED', 'INFERRED', 'MANUAL', 'IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (
            confidence_level IN (
                'HIGH',
                'MEDIUM',
                'LOW',
                'UNRESOLVED',
                'NOT_APPLICABLE'
            )
        ),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    UNIQUE (case_id, contact_code)
);
```

The `profile_photo_media_id` foreign key may be added after the `media_items` table is created, or managed at application level to avoid cyclic migration complexity.

---

## 12.3 `contact_aliases`

```sql
CREATE TABLE contact_aliases (
    id INTEGER PRIMARY KEY,
    contact_id INTEGER NOT NULL,
    alias_type TEXT NOT NULL,
    alias_value TEXT NOT NULL,
    valid_from_utc TEXT,
    valid_until_utc TEXT,
    source_file_id INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
    FOREIGN KEY (source_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL
);
```

---

# 13. Group and Conversation Tables

## 13.1 `groups`

```sql
CREATE TABLE groups (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    group_code TEXT NOT NULL,
    whatsapp_group_identifier TEXT,
    subject TEXT,
    description TEXT,
    creator_contact_id INTEGER,
    created_timestamp_raw TEXT,
    created_at_source_utc TEXT,
    origin TEXT NOT NULL
        CHECK (origin IN ('PARSED', 'RECOVERED', 'INFERRED', 'MANUAL', 'IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (
            confidence_level IN (
                'HIGH',
                'MEDIUM',
                'LOW',
                'UNRESOLVED',
                'NOT_APPLICABLE'
            )
        ),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (creator_contact_id)
        REFERENCES contacts(id) ON DELETE SET NULL,
    UNIQUE (case_id, group_code)
);
```

---

## 13.2 `group_participants`

```sql
CREATE TABLE group_participants (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL,
    contact_id INTEGER,
    participant_identifier TEXT,
    role TEXT,
    joined_timestamp_raw TEXT,
    joined_at_utc TEXT,
    left_timestamp_raw TEXT,
    left_at_utc TEXT,
    origin TEXT NOT NULL
        CHECK (origin IN ('PARSED', 'RECOVERED', 'INFERRED', 'MANUAL', 'IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'UNRESOLVED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL
);
```

---

## 13.3 `conversations`

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    conversation_code TEXT NOT NULL,
    conversation_type TEXT NOT NULL
        CHECK (conversation_type IN ('DIRECT', 'GROUP', 'BROADCAST', 'UNKNOWN')),
    contact_id INTEGER,
    group_id INTEGER,
    title TEXT,
    source_conversation_identifier TEXT,
    first_event_at_utc TEXT,
    last_event_at_utc TEXT,
    message_count INTEGER NOT NULL DEFAULT 0,
    call_count INTEGER NOT NULL DEFAULT 0,
    origin TEXT NOT NULL
        CHECK (origin IN ('PARSED', 'RECOVERED', 'INFERRED', 'MANUAL', 'IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'UNRESOLVED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL,
    UNIQUE (case_id, conversation_code),
    CHECK (
        (conversation_type = 'DIRECT' AND contact_id IS NOT NULL)
        OR (conversation_type = 'GROUP' AND group_id IS NOT NULL)
        OR conversation_type IN ('BROADCAST', 'UNKNOWN')
    )
);
```

---

# 14. Message Tables

## 14.1 `messages`

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    message_code TEXT NOT NULL,
    conversation_id INTEGER NOT NULL,
    sender_contact_id INTEGER,
    sender_account_id INTEGER,
    source_message_identifier TEXT,
    source_record_id TEXT,
    source_table TEXT,
    direction TEXT NOT NULL
        CHECK (direction IN ('INCOMING', 'OUTGOING', 'SYSTEM', 'UNKNOWN')),
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
    is_deleted_marker INTEGER NOT NULL DEFAULT 0
        CHECK (is_deleted_marker IN (0, 1)),
    is_forwarded INTEGER NOT NULL DEFAULT 0
        CHECK (is_forwarded IN (0, 1)),
    is_starred INTEGER NOT NULL DEFAULT 0
        CHECK (is_starred IN (0, 1)),
    is_view_once INTEGER NOT NULL DEFAULT 0
        CHECK (is_view_once IN (0, 1)),
    raw_extension_json TEXT,
    origin TEXT NOT NULL
        CHECK (origin IN ('PARSED', 'RECOVERED', 'INFERRED', 'MANUAL', 'IMPORTED')),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH'
        CHECK (
            confidence_level IN (
                'HIGH',
                'MEDIUM',
                'LOW',
                'UNRESOLVED',
                'NOT_APPLICABLE'
            )
        ),
    validation_status TEXT NOT NULL DEFAULT 'VALIDATED'
        CHECK (
            validation_status IN (
                'VALIDATED',
                'PARTIAL',
                'UNVERIFIED',
                'REJECTED',
                'UNSUPPORTED'
            )
        ),
    source_evidence_file_id INTEGER,
    parser_run_id INTEGER,
    source_page_number INTEGER,
    source_byte_offset INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE RESTRICT,
    FOREIGN KEY (sender_contact_id)
        REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (sender_account_id)
        REFERENCES accounts(id) ON DELETE SET NULL,
    FOREIGN KEY (source_evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (parser_run_id)
        REFERENCES parser_runs(id) ON DELETE SET NULL,
    UNIQUE (case_id, message_code)
);
```

---

## 14.2 `message_revisions`

```sql
CREATE TABLE message_revisions (
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
    FOREIGN KEY (source_evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL,
    UNIQUE (message_id, revision_number)
);
```

---

## 14.3 `message_reactions`

```sql
CREATE TABLE message_reactions (
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
    FOREIGN KEY (reactor_contact_id)
        REFERENCES contacts(id) ON DELETE SET NULL
);
```

---

## 14.4 `message_quotes`

```sql
CREATE TABLE message_quotes (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL UNIQUE,
    quoted_message_id INTEGER,
    quoted_source_identifier TEXT,
    quoted_sender_identifier TEXT,
    quoted_text_snapshot TEXT,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (quoted_message_id)
        REFERENCES messages(id) ON DELETE SET NULL
);
```

---

## 14.5 `message_mentions`

```sql
CREATE TABLE message_mentions (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    mentioned_contact_id INTEGER,
    mentioned_identifier TEXT NOT NULL,
    character_start INTEGER,
    character_end INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (mentioned_contact_id)
        REFERENCES contacts(id) ON DELETE SET NULL
);
```

---

## 14.6 `system_events`

```sql
CREATE TABLE system_events (
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
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (related_message_id)
        REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (actor_contact_id)
        REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (target_contact_id)
        REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (source_evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL
);
```

---

# 15. Shared Content Tables

## 15.1 `locations`

```sql
CREATE TABLE locations (
    id INTEGER PRIMARY KEY,
    message_id INTEGER,
    latitude REAL,
    longitude REAL,
    accuracy_meters REAL,
    place_name TEXT,
    address_text TEXT,
    is_live_location INTEGER NOT NULL DEFAULT 0
        CHECK (is_live_location IN (0, 1)),
    live_duration_seconds INTEGER,
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180)
);
```

---

## 15.2 `shared_contacts`

```sql
CREATE TABLE shared_contacts (
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
```

---

## 15.3 `links`

```sql
CREATE TABLE links (
    id INTEGER PRIMARY KEY,
    message_id INTEGER,
    url_raw TEXT NOT NULL,
    url_normalized TEXT,
    scheme TEXT,
    domain TEXT,
    title TEXT,
    description TEXT,
    is_suspicious INTEGER NOT NULL DEFAULT 0
        CHECK (is_suspicious IN (0, 1)),
    scan_status TEXT,
    scan_provider TEXT,
    scan_result_json TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);
```

External malware scanning must only run when explicitly enabled.

---

# 16. Media Tables

## 16.1 `media_items`

```sql
CREATE TABLE media_items (
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
    is_missing INTEGER NOT NULL DEFAULT 0
        CHECK (is_missing IN (0, 1)),
    is_orphan INTEGER NOT NULL DEFAULT 0
        CHECK (is_orphan IN (0, 1)),
    origin TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    source_evidence_file_id INTEGER,
    parser_run_id INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_media_id)
        REFERENCES media_items(id) ON DELETE SET NULL,
    FOREIGN KEY (source_evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (parser_run_id)
        REFERENCES parser_runs(id) ON DELETE SET NULL,
    UNIQUE (case_id, media_code)
);
```

---

## 16.2 `media_metadata`

```sql
CREATE TABLE media_metadata (
    id INTEGER PRIMARY KEY,
    media_item_id INTEGER NOT NULL,
    metadata_namespace TEXT NOT NULL,
    metadata_key TEXT NOT NULL,
    metadata_value_text TEXT,
    metadata_value_number REAL,
    metadata_value_json TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (media_item_id)
        REFERENCES media_items(id) ON DELETE CASCADE,
    UNIQUE (media_item_id, metadata_namespace, metadata_key)
);
```

---

## 16.3 `exif_records`

```sql
CREATE TABLE exif_records (
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
    FOREIGN KEY (media_item_id)
        REFERENCES media_items(id) ON DELETE CASCADE,
    CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180)
);
```

---

## 16.4 `media_correlations`

```sql
CREATE TABLE media_correlations (
    id INTEGER PRIMARY KEY,
    media_item_id INTEGER NOT NULL,
    candidate_message_id INTEGER,
    correlation_method TEXT NOT NULL,
    score REAL NOT NULL CHECK (score BETWEEN 0 AND 1),
    explanation TEXT NOT NULL,
    accepted_by_examiner_id INTEGER,
    accepted_at_utc TEXT,
    status TEXT NOT NULL DEFAULT 'UNRESOLVED'
        CHECK (status IN ('ACCEPTED', 'REJECTED', 'UNRESOLVED')),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (media_item_id)
        REFERENCES media_items(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_message_id)
        REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (accepted_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL
);
```

---

# 17. Call Tables

## 17.1 `calls`

```sql
CREATE TABLE calls (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    call_code TEXT NOT NULL,
    conversation_id INTEGER,
    source_call_identifier TEXT,
    source_record_id TEXT,
    call_type TEXT NOT NULL
        CHECK (
            call_type IN (
                'VOICE',
                'VIDEO',
                'GROUP_VOICE',
                'GROUP_VIDEO',
                'UNKNOWN'
            )
        ),
    direction TEXT NOT NULL
        CHECK (
            direction IN (
                'INCOMING',
                'OUTGOING',
                'MISSED',
                'DECLINED',
                'UNKNOWN'
            )
        ),
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
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (source_evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE SET NULL,
    FOREIGN KEY (parser_run_id)
        REFERENCES parser_runs(id) ON DELETE SET NULL,
    UNIQUE (case_id, call_code)
);
```

---

## 17.2 `call_participants`

```sql
CREATE TABLE call_participants (
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
```

---

# 18. Recovery Tables

## 18.1 `recovery_runs`

```sql
CREATE TABLE recovery_runs (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    recovery_code TEXT NOT NULL UNIQUE,
    strategy TEXT NOT NULL,
    source_evidence_file_id INTEGER NOT NULL,
    working_copy_id INTEGER,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL
        CHECK (
            status IN (
                'STARTED',
                'COMPLETED',
                'PARTIAL',
                'CANCELLED',
                'FAILED'
            )
        ),
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
    FOREIGN KEY (source_evidence_file_id)
        REFERENCES evidence_files(id) ON DELETE RESTRICT,
    FOREIGN KEY (working_copy_id)
        REFERENCES working_copies(id) ON DELETE SET NULL
);
```

---

## 18.2 `recovery_candidates`

```sql
CREATE TABLE recovery_candidates (
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
    confidence_level TEXT NOT NULL
        CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'UNRESOLVED')),
    confidence_score REAL
        CHECK (confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1),
    review_status TEXT NOT NULL DEFAULT 'UNRESOLVED'
        CHECK (review_status IN ('ACCEPTED', 'REJECTED', 'UNRESOLVED')),
    reviewed_by_examiner_id INTEGER,
    reviewed_at_utc TEXT,
    review_notes TEXT,
    duplicate_group_key TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (recovery_run_id)
        REFERENCES recovery_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (recovery_run_id, candidate_code)
);
```

---

## 18.3 `recovered_records`

Links accepted candidates to stable internal artefacts.

```sql
CREATE TABLE recovered_records (
    id INTEGER PRIMARY KEY,
    recovery_candidate_id INTEGER NOT NULL UNIQUE,
    artefact_type TEXT NOT NULL,
    artefact_id INTEGER NOT NULL,
    acceptance_reason TEXT,
    accepted_at_utc TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (recovery_candidate_id)
        REFERENCES recovery_candidates(id) ON DELETE RESTRICT
);
```

`artefact_id` is polymorphic and must be validated by the application service.

---

# 19. Network Metadata Tables

## 19.1 `network_capture_sessions`

```sql
CREATE TABLE network_capture_sessions (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    capture_code TEXT NOT NULL UNIQUE,
    evidence_item_id INTEGER,
    interface_name TEXT,
    capture_mode TEXT NOT NULL
        CHECK (capture_mode IN ('LIVE_PASSIVE', 'PCAP_IMPORT')),
    authorisation_id INTEGER,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL
        CHECK (status IN ('STARTED', 'COMPLETED', 'CANCELLED', 'FAILED')),
    pcap_relative_path TEXT,
    pcap_sha256 TEXT,
    capture_filter TEXT,
    packet_count INTEGER NOT NULL DEFAULT 0,
    bytes_captured INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (evidence_item_id)
        REFERENCES evidence_items(id) ON DELETE SET NULL,
    FOREIGN KEY (authorisation_id)
        REFERENCES authorisations(id) ON DELETE SET NULL
);
```

---

## 19.2 `network_flows`

```sql
CREATE TABLE network_flows (
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
    FOREIGN KEY (capture_session_id)
        REFERENCES network_capture_sessions(id) ON DELETE CASCADE
);
```

---

## 19.3 `network_endpoints`

```sql
CREATE TABLE network_endpoints (
    id INTEGER PRIMARY KEY,
    capture_session_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    endpoint_classification TEXT NOT NULL
        CHECK (
            endpoint_classification IN (
                'PROBABLE_PEER',
                'WHATSAPP_RELAY',
                'TURN_SERVER',
                'CLOUD_INFRASTRUCTURE',
                'MOBILE_CARRIER_GATEWAY',
                'VPN_OR_PROXY',
                'LOCAL_GATEWAY',
                'UNKNOWN'
            )
        ),
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
    FOREIGN KEY (capture_session_id)
        REFERENCES network_capture_sessions(id) ON DELETE CASCADE,
    UNIQUE (capture_session_id, ip_address),
    CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180)
);
```

The UI and reports must state that IP-derived location may represent relay, carrier, VPN or cloud infrastructure.

---

## 19.4 `stun_turn_events`

```sql
CREATE TABLE stun_turn_events (
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
    FOREIGN KEY (capture_session_id)
        REFERENCES network_capture_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (network_flow_id)
        REFERENCES network_flows(id) ON DELETE SET NULL
);
```

---

# 20. Timeline Tables

## 20.1 `timeline_events`

```sql
CREATE TABLE timeline_events (
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
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (evidence_item_id)
        REFERENCES evidence_items(id) ON DELETE SET NULL,
    UNIQUE (case_id, event_code)
);
```

Timeline rows may be regenerated from source artefacts. Store generation metadata if materialised.

---

# 21. Examiner Review Tables

## 21.1 `tags`

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_by_examiner_id INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, name)
);
```

---

## 21.2 `artefact_tags`

```sql
CREATE TABLE artefact_tags (
    id INTEGER PRIMARY KEY,
    tag_id INTEGER NOT NULL,
    artefact_type TEXT NOT NULL,
    artefact_id INTEGER NOT NULL,
    applied_by_examiner_id INTEGER,
    applied_at_utc TEXT NOT NULL,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    FOREIGN KEY (applied_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (tag_id, artefact_type, artefact_id)
);
```

---

## 21.3 `bookmarks`

```sql
CREATE TABLE bookmarks (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    artefact_type TEXT NOT NULL,
    artefact_id INTEGER NOT NULL,
    title TEXT,
    created_by_examiner_id INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, artefact_type, artefact_id)
);
```

---

## 21.4 `examiner_notes`

```sql
CREATE TABLE examiner_notes (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    artefact_type TEXT,
    artefact_id INTEGER,
    note_text TEXT NOT NULL,
    created_by_examiner_id INTEGER,
    is_private INTEGER NOT NULL DEFAULT 0
        CHECK (is_private IN (0, 1)),
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL
);
```

---

## 21.5 `saved_searches`

```sql
CREATE TABLE saved_searches (
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
    FOREIGN KEY (created_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, name)
);
```

---

# 22. Audit Tables

## 22.1 `audit_events`

```sql
CREATE TABLE audit_events (
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
    FOREIGN KEY (examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, event_sequence),
    UNIQUE (case_id, event_hash)
);
```

Hash calculation:

```text
event_hash = SHA256(
    previous_event_hash +
    canonical_event_json
)
```

The canonical JSON representation must use:

- UTF-8;
- sorted keys;
- no insignificant whitespace;
- stable timestamp format;
- explicit null handling.

---

# 23. Reporting Tables

## 23.1 `report_runs`

```sql
CREATE TABLE report_runs (
    id INTEGER PRIMARY KEY,
    case_id INTEGER NOT NULL,
    report_code TEXT NOT NULL,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    generated_by_examiner_id INTEGER,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL
        CHECK (
            status IN (
                'STARTED',
                'COMPLETED',
                'PARTIAL',
                'CANCELLED',
                'FAILED'
            )
        ),
    query_definition_json TEXT,
    filters_json TEXT,
    sort_json TEXT,
    template_name TEXT NOT NULL,
    template_version TEXT NOT NULL,
    generator_version TEXT NOT NULL,
    display_timezone TEXT NOT NULL,
    limitations_text TEXT,
    redaction_applied INTEGER NOT NULL DEFAULT 0
        CHECK (redaction_applied IN (0, 1)),
    error_summary TEXT,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (generated_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL,
    UNIQUE (case_id, report_code)
);
```

---

## 23.2 `report_files`

```sql
CREATE TABLE report_files (
    id INTEGER PRIMARY KEY,
    report_run_id INTEGER NOT NULL,
    file_format TEXT NOT NULL,
    stored_relative_path TEXT NOT NULL UNIQUE,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    signature_relative_path TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (report_run_id)
        REFERENCES report_runs(id) ON DELETE CASCADE
);
```

---

## 23.3 `redaction_rules`

```sql
CREATE TABLE redaction_rules (
    id INTEGER PRIMARY KEY,
    report_run_id INTEGER,
    case_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    pattern_text TEXT,
    replacement_text TEXT,
    target_field TEXT,
    is_enabled INTEGER NOT NULL DEFAULT 1
        CHECK (is_enabled IN (0, 1)),
    created_by_examiner_id INTEGER,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    FOREIGN KEY (report_run_id)
        REFERENCES report_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_examiner_id)
        REFERENCES examiners(id) ON DELETE SET NULL
);
```

---

## 23.4 `export_manifests`

```sql
CREATE TABLE export_manifests (
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
    FOREIGN KEY (report_run_id)
        REFERENCES report_runs(id) ON DELETE SET NULL
);
```

---

# 24. Full-Text Search

## 24.1 FTS Table

```sql
CREATE VIRTUAL TABLE message_search USING fts5(
    message_code UNINDEXED,
    conversation_id UNINDEXED,
    contact_text,
    conversation_text,
    message_text,
    caption_text,
    link_text,
    tokenize = 'unicode61'
);
```

### 24.2 Search Synchronisation

Prefer explicit application-controlled indexing over fragile triggers.

Index operations must run after:

- successful parse;
- accepted recovery;
- edit of examiner notes;
- contact-name update;
- reportable redaction changes.

### 24.3 Search Privacy

Search data remains inside the case database.

Do not upload indexes or terms to external services.

---

# 25. Index Strategy

## 25.1 Evidence Indexes

```sql
CREATE INDEX idx_evidence_items_case
    ON evidence_items(case_id);

CREATE INDEX idx_evidence_files_item
    ON evidence_files(evidence_item_id);

CREATE INDEX idx_evidence_hashes_value
    ON evidence_hashes(algorithm, hash_value);
```

## 25.2 Message Indexes

```sql
CREATE INDEX idx_messages_conversation_time
    ON messages(conversation_id, sent_at_utc);

CREATE INDEX idx_messages_case_time
    ON messages(case_id, sent_at_utc);

CREATE INDEX idx_messages_sender
    ON messages(sender_contact_id);

CREATE INDEX idx_messages_type
    ON messages(message_type);

CREATE INDEX idx_messages_origin_confidence
    ON messages(origin, confidence_level);

CREATE INDEX idx_messages_source_record
    ON messages(source_evidence_file_id, source_table, source_record_id);
```

## 25.3 Media Indexes

```sql
CREATE INDEX idx_media_message
    ON media_items(message_id);

CREATE INDEX idx_media_sha256
    ON media_items(sha256);

CREATE INDEX idx_media_orphan
    ON media_items(is_orphan);
```

## 25.4 Call Indexes

```sql
CREATE INDEX idx_calls_conversation_time
    ON calls(conversation_id, started_at_utc);

CREATE INDEX idx_calls_case_time
    ON calls(case_id, started_at_utc);

CREATE INDEX idx_calls_type_direction
    ON calls(call_type, direction);
```

## 25.5 Recovery Indexes

```sql
CREATE INDEX idx_recovery_candidates_run_status
    ON recovery_candidates(recovery_run_id, review_status);

CREATE INDEX idx_recovery_candidates_confidence
    ON recovery_candidates(confidence_level);

CREATE INDEX idx_recovery_candidates_location
    ON recovery_candidates(
        recovery_run_id,
        source_page_number,
        source_byte_offset
    );
```

## 25.6 Timeline Indexes

```sql
CREATE INDEX idx_timeline_case_time
    ON timeline_events(case_id, occurred_at_utc);

CREATE INDEX idx_timeline_conversation_time
    ON timeline_events(conversation_id, occurred_at_utc);

CREATE INDEX idx_timeline_artefact
    ON timeline_events(artefact_type, artefact_id);
```

## 25.7 Network Indexes

```sql
CREATE INDEX idx_network_flows_session_time
    ON network_flows(capture_session_id, first_seen_at_utc);

CREATE INDEX idx_network_endpoints_ip
    ON network_endpoints(ip_address);

CREATE INDEX idx_stun_turn_session_time
    ON stun_turn_events(capture_session_id, occurred_at_utc);
```

---

# 26. Uniqueness and Deduplication

## 26.1 Evidence Files

Detect duplicate evidence using:

```text
SHA-256 + size
```

Do not automatically delete duplicates. Register the relationship and let the examiner decide.

## 26.2 Messages

A source-specific unique identity may combine:

```text
source_evidence_file_id
source_table
source_record_id
parser adapter
```

Use a partial unique index when all fields are available:

```sql
CREATE UNIQUE INDEX uq_messages_source_identity
ON messages(
    source_evidence_file_id,
    source_table,
    source_record_id,
    parser_run_id
)
WHERE source_record_id IS NOT NULL;
```

Cross-source duplicate detection is analytical and must not merge records automatically.

## 26.3 Media

Media deduplication uses SHA-256.

Multiple logical references may point to the same physical content.

## 26.4 Recovery Candidates

Duplicate candidates can be grouped using:

```text
source hash
page number
offset
candidate type
normalised candidate content
```

---

# 27. Time Handling

Every timestamp-bearing artefact should preserve:

- raw value;
- numeric epoch value where available;
- source unit;
- source time zone;
- UTC-normalised value;
- clock-skew adjustment;
- confidence.

Do not overwrite raw values.

Example:

```text
timestamp_raw: 1721384105123
timestamp_epoch_value: 1721384105123
timestamp_epoch_unit: milliseconds
sent_at_utc: 2024-07-19T10:15:05.123Z
```

---

# 28. JSON Extension Fields

Use JSON fields for:

- unknown parser fields;
- adapter parameters;
- validation results;
- scan results;
- report filters;
- recovery details.

Rules:

- JSON must be valid UTF-8;
- store a schema version inside complex JSON;
- do not use JSON as a replacement for core relational fields;
- index frequently queried values as normal columns;
- redact secrets before persistence.

---

# 29. Transactions

Use transactions for:

- evidence registration;
- parser batch inserts;
- recovery-run completion;
- report completion;
- migrations;
- case archive metadata;
- audit event append.

For large parser imports:

1. Start transaction.
2. Insert in bounded batches.
3. Update counters.
4. Commit only after validation.
5. Roll back on critical failure.
6. Mark partial state when supported.

---

# 30. Deletion Policy

## 30.1 Evidence

Original evidence records must not be hard-deleted from an active case through normal UI operations.

Use state transitions:

```text
QUARANTINED
EXCLUDED
ARCHIVED
```

## 30.2 Parsed Artefacts

Parsed artefacts may be removed only when:

- rebuilding a parser run;
- reverting a failed import;
- restoring a case;
- executing a documented maintenance operation.

Deletion must be audited.

## 30.3 Examiner Data

Notes, tags and bookmarks may be deleted, but deletion must generate an audit event.

## 30.4 Temporary Working Copies

Temporary decrypted files and intermediate working copies may be deleted according to case policy. The deletion event and last known hash must be retained.

---

# 31. Migration Strategy

## 31.1 Schema Version

Use:

```sql
PRAGMA user_version;
```

Also store migrations:

```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL UNIQUE,
    migration_name TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL,
    application_version TEXT NOT NULL,
    checksum TEXT NOT NULL
);
```

## 31.2 Migration Rules

Every migration must:

- have a unique integer version;
- run in a transaction;
- create a safety backup first;
- verify available disk space;
- verify database integrity before migration;
- verify integrity after migration;
- record migration checksum;
- support rollback through backup restoration;
- be idempotent where practical.

## 31.3 Corrective Migrations

Use corrective migrations for data fixes.

Never modify an already released migration file after distribution.

---

# 32. Backup and Restore

## 32.1 Case Backup

A case backup should include:

- `case.db`;
- `case.db-wal` and `case.db-shm` after checkpoint handling;
- originals;
- working copies selected by policy;
- derived files;
- reports;
- manifests;
- logs;
- `case.toml`.

## 32.2 Safe SQLite Backup

Use SQLite’s online backup API or:

```sql
VACUUM INTO 'backup.db';
```

Do not use `VACUUM INTO` on source evidence databases.

## 32.3 Restore Workflow

```text
Validate backup archive
→ Verify manifest
→ Restore to new temporary directory
→ Verify database
→ Verify hashes
→ Rename into final case directory
→ Audit restoration
```

Never overwrite the active case without a safety backup.

---

# 33. Encryption

## 33.1 Database Encryption

SQLite does not provide transparent encryption by default.

Supported options:

- encrypted case container;
- SQLCipher where licensing and deployment permit;
- filesystem encryption;
- encrypted archive for exported cases.

## 33.2 Secret Storage

Do not store raw:

- passwords;
- private keys;
- OAuth tokens;
- backup keys.

Use the operating-system credential vault and store only a reference identifier in the database.

## 33.3 Temporary Decrypted Data

Store decrypted data only in `working/`.

Record:

- source file;
- adapter;
- adapter version;
- creation time;
- hash;
- deletion policy.

---

# 34. Data Validation

## 34.1 Message Validation

Validate:

- recognised direction;
- recognised type;
- valid conversation;
- timestamp conversion;
- source identity;
- provenance;
- confidence.

## 34.2 Media Validation

Validate:

- file existence;
- real file signature;
- size;
- SHA-256;
- path containment;
- metadata parsing status.

## 34.3 IP Validation

Use Python’s `ipaddress` library.

Reject malformed values.

Distinguish:

- IPv4;
- IPv6;
- private;
- loopback;
- link-local;
- multicast;
- public.

## 34.4 Coordinates

Latitude:

```text
-90 through 90
```

Longitude:

```text
-180 through 180
```

IP-derived coordinates must be identified as approximate.

---

# 35. Data Access Layer

Use repository interfaces.

Example:

```python
class MessageRepository(Protocol):
    def add_batch(self, messages: Sequence[Message]) -> None:
        ...

    def get_by_id(self, message_id: int) -> Message | None:
        ...

    def search(
        self,
        case_id: int,
        filters: MessageFilters,
        page: PageRequest,
    ) -> Page[Message]:
        ...
```

Repositories must:

- use parameterised queries;
- enforce case boundaries;
- support pagination;
- avoid returning unbounded datasets;
- expose transactions through a unit of work.

---

# 36. Unit of Work

```python
class UnitOfWork(Protocol):
    messages: MessageRepository
    evidence: EvidenceRepository
    contacts: ContactRepository
    calls: CallRepository
    recovery: RecoveryRepository

    def __enter__(self) -> "UnitOfWork":
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...
```

---

# 37. Large Dataset Strategy

For large cases:

- batch inserts;
- prepared statements;
- lazy models;
- pagination;
- FTS5;
- narrow select columns;
- thumbnail-on-demand;
- streamed exports;
- indexed filtering;
- periodic analysis cache;
- cancellation support.

Do not execute:

```sql
SELECT * FROM messages;
```

without pagination or strict filters.

---

# 38. Example Queries

## 38.1 Messages by Conversation

```sql
SELECT
    m.id,
    m.message_code,
    m.direction,
    m.message_type,
    m.text_content,
    m.sent_at_utc,
    m.origin,
    m.confidence_level
FROM messages AS m
WHERE m.conversation_id = :conversation_id
ORDER BY m.sent_at_utc, m.id
LIMIT :limit OFFSET :offset;
```

## 38.2 Recovered Messages Awaiting Review

```sql
SELECT
    rc.candidate_code,
    rc.candidate_type,
    rc.confidence_level,
    rc.confidence_score,
    rc.parsed_fields_json,
    rc.source_page_number,
    rc.source_byte_offset
FROM recovery_candidates AS rc
JOIN recovery_runs AS rr
    ON rr.id = rc.recovery_run_id
WHERE rr.case_id = :case_id
  AND rc.review_status = 'UNRESOLVED'
ORDER BY
    CASE rc.confidence_level
        WHEN 'HIGH' THEN 1
        WHEN 'MEDIUM' THEN 2
        WHEN 'LOW' THEN 3
        ELSE 4
    END,
    rc.id;
```

## 38.3 Call Summary

```sql
SELECT
    direction,
    call_type,
    COUNT(*) AS call_count,
    SUM(COALESCE(duration_seconds, 0)) AS total_duration_seconds
FROM calls
WHERE case_id = :case_id
GROUP BY direction, call_type
ORDER BY call_count DESC;
```

## 38.4 Live Network Endpoints

```sql
SELECT
    ip_address,
    endpoint_classification,
    classification_confidence,
    isp_name,
    asn,
    country_name,
    region_name,
    city_name,
    latitude,
    longitude,
    first_seen_at_utc,
    last_seen_at_utc,
    packet_count,
    warning_text
FROM network_endpoints
WHERE capture_session_id = :capture_session_id
ORDER BY last_seen_at_utc DESC;
```

## 38.5 Evidence Verification

```sql
SELECT
    ei.evidence_code,
    ef.file_code,
    ef.original_filename,
    eh.algorithm,
    eh.hash_value,
    ef.verification_status
FROM evidence_items AS ei
JOIN evidence_files AS ef
    ON ef.evidence_item_id = ei.id
LEFT JOIN evidence_hashes AS eh
    ON eh.evidence_file_id = ef.id
WHERE ei.case_id = :case_id
ORDER BY ei.evidence_code, ef.file_code;
```

---

# 39. Database Security

Controls:

- case-specific database path;
- strict filesystem permissions;
- no network listener;
- parameterised SQL;
- trusted schema disabled;
- external extension loading disabled;
- no dynamic SQL from imported evidence;
- no raw HTML execution;
- optional encrypted container;
- audit log verification;
- backup manifest.

Disable SQLite extension loading:

```python
connection.enable_load_extension(False)
```

---

# 40. Testing Requirements

## 40.1 Schema Tests

- every table exists;
- foreign keys pass;
- check constraints reject invalid values;
- unique constraints work;
- migrations produce expected schema.

## 40.2 Repository Tests

- create and retrieve records;
- pagination;
- transaction rollback;
- case boundary enforcement;
- duplicate detection;
- search behaviour.

## 40.3 Migration Tests

Test migration from every supported previous version.

Verify:

- no data loss;
- preserved hashes;
- preserved provenance;
- valid foreign keys;
- successful rollback through backup.

## 40.4 Performance Tests

Datasets:

- 1,000 messages;
- 50,000 messages;
- 500,000 messages;
- 2,000,000 messages;
- 1 million timeline events;
- 100 GB referenced media;
- large recovery candidate sets.

## 40.5 Corruption Tests

Test:

- truncated database;
- invalid header;
- missing WAL;
- malformed JSON extension;
- invalid foreign key;
- hash mismatch;
- interrupted migration.

---

# 41. Initial Migration Order

Recommended order:

1. `cases`
2. `examiners`
3. `authorisations`
4. `evidence_items`
5. `evidence_files`
6. `evidence_hashes`
7. `working_copies`
8. `acquisition_sessions`
9. `chain_of_custody`
10. `tool_versions`
11. `parser_runs`
12. `schema_mappings`
13. `parser_warnings`
14. `accounts`
15. `contacts`
16. `contact_aliases`
17. `groups`
18. `group_participants`
19. `conversations`
20. `messages`
21. message child tables
22. shared content tables
23. media tables
24. call tables
25. recovery tables
26. network tables
27. timeline tables
28. review tables
29. audit tables
30. report tables
31. FTS tables
32. indexes
33. triggers or counters if approved

---

# 42. Counter Management

Fields such as:

- conversation message count;
- conversation call count;
- recovery accepted count;
- evidence warning count;

are cached counters.

Preferred approach:

- update in application transactions;
- verify with maintenance queries;
- recalculate when inconsistency is detected.

Do not rely on complex triggers unless validation proves they are necessary and reliable.

---

# 43. Database Maintenance

Case maintenance tools may include:

- integrity check;
- foreign-key check;
- rebuild search index;
- recalculate counters;
- verify file paths;
- verify hashes;
- find orphaned derived files;
- compact application database.

Maintenance operations must never modify source evidence.

Run `VACUUM` only on `case.db` when:

- the case is closed;
- a verified backup exists;
- sufficient free disk space is available;
- the event is audited.

---

# 44. Data Export

Supported exports:

- CSV;
- JSON;
- HTML;
- PDF;
- evidence ZIP;
- report manifest.

Every export should include:

- case code;
- export code;
- generation time;
- applied filters;
- time zone;
- tool version;
- source hashes;
- limitations;
- export hash.

---

# 45. Database Acceptance Criteria

The database design is accepted when:

- one isolated `case.db` is created per case;
- original evidence is referenced but not modified;
- all evidence files have SHA-256 values;
- every parsed message has provenance;
- recovered records remain separately identifiable;
- timestamps preserve raw and UTC values;
- network endpoints include classification and warnings;
- FTS search works with pagination;
- audit events form a valid hash chain;
- migrations are transactional;
- backup and restore are verified;
- invalid enum and coordinate values are rejected;
- performance tests pass at the target scale;
- Windows 10 and Windows 11 builds can create and open case databases.

---

# 46. Final Database Summary

The WhatsApp Forensic Toolkit uses a case-isolated SQLite database as a forensic catalogue and analysis store.

The core data path is:

```text
Evidence file
→ SHA-256 verification
→ immutable original copy
→ verified working copy
→ parser or recovery run
→ provenance-aware artefact
→ search and timeline
→ reproducible report
```

The database does not claim that recovered records are guaranteed to be authentic, that encrypted backups can always be decrypted, or that an IP address identifies a caller’s physical location.

Reliability is achieved through:

- immutable evidence references;
- cryptographic hashes;
- explicit provenance;
- versioned parser runs;
- separate recovery candidates;
- confidence labels;
- transactional migrations;
- audit hash chaining;
- reproducible report metadata.
