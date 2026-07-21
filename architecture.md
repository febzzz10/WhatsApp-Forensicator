# WhatsApp Forensic Toolkit — Architecture

**Document version:** 1.0  
**Project:** WhatsApp Forensic Toolkit  
**Primary language:** Python 3.11+  
**Primary UI:** PySide6 desktop application  
**Primary host target:** Windows 10/11  
**Secondary targets:** Linux and macOS  
**Architecture style:** Layered modular desktop architecture with versioned parser plugins and strict forensic evidence separation  

---

## 1. Purpose

This document defines the technical architecture of the WhatsApp Forensic Toolkit.

The toolkit is intended to acquire, preserve, parse, analyse and report WhatsApp-related evidence obtained through lawful and authorised workflows. It must preserve forensic integrity, record provenance, distinguish normal parsed records from recovered or inferred records, and communicate technical limitations clearly.

The system is offline-first. Original evidence is never modified. Parsing, recovery, media processing and reporting operate on verified working copies.

---

## 2. Architectural Goals

The architecture must:

1. Preserve original evidence as immutable files.
2. Calculate and verify cryptographic hashes.
3. Separate original, working and derived data.
4. Record provenance for every artefact.
5. Support changing WhatsApp schemas through versioned adapters.
6. Perform deleted-data recovery as a separate best-effort process.
7. Keep long operations outside the UI thread.
8. Scale to large databases and media collections.
9. Generate reproducible reports with limitations.
10. Keep external services disabled by default.
11. Fail safely when a source or schema is unsupported.
12. support Windows 10/11 first, with later Linux and macOS releases.

### 2.1 Non-Goals

The architecture does not provide:

- unauthorised account access;
- authentication-token theft;
- password or two-factor-authentication bypass;
- Android or iOS exploitation;
- rooting or jailbreaking automation;
- call-content decryption;
- covert surveillance;
- active ARP spoofing or credential interception;
- exact physical location from an IP address;
- guaranteed deletion recovery;
- guaranteed crypt12, crypt14 or crypt15 decryption.

---

## 3. High-Level Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│ PySide6 Pages | Dialogs | Models | Widgets | Web Views      │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                    Application Layer                         │
│ Case | Evidence | Parse | Recovery | Search | Report        │
└───────────────┬────────────────┬────────────────┬────────────┘
                │                │                │
┌───────────────▼──────┐ ┌───────▼────────┐ ┌────▼────────────┐
│    Domain Layer      │ │ Processing      │ │ Integrations    │
│ Models | Policies    │ │ Parsers         │ │ Desktop Sources │
│ Provenance | Events  │ │ Recovery        │ │ Optional PCAP   │
│ Confidence | Rules   │ │ Analysis        │ │ Optional APIs   │
└───────────────┬──────┘ └───────┬────────┘ └────┬────────────┘
                │                │               │
┌───────────────▼────────────────▼───────────────▼────────────┐
│                   Infrastructure Layer                      │
│ SQLite | Filesystem | Hashing | Crypto | Logging | Workers │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                    Forensic Repository                       │
│ Originals | Working Copies | Derived Data | Reports | Logs  │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Layer Responsibilities

### 4.1 Presentation Layer

Responsibilities:

- render the user interface;
- collect user input;
- display progress and warnings;
- display provenance and confidence;
- initiate application services;
- never parse evidence directly;
- never write to original evidence.

### 4.2 Application Layer

Responsibilities:

- coordinate use cases;
- enforce preconditions;
- validate authorisation;
- schedule background jobs;
- manage application transactions;
- translate domain results into UI responses;
- send important actions to the audit service.

### 4.3 Domain Layer

Responsibilities:

- define cases, evidence, artefacts and reports;
- define evidence-state rules;
- define provenance and confidence models;
- define parser and recovery contracts;
- remain independent of PySide6, SQLite and operating-system APIs.

### 4.4 Processing Layer

Responsibilities:

- inspect sources;
- fingerprint schemas;
- parse exports and databases;
- recover deleted records;
- extract media metadata;
- build timelines;
- correlate messages, calls, media and network events.

### 4.5 Infrastructure Layer

Responsibilities:

- case database access;
- evidence filesystem management;
- hashing;
- secure configuration;
- structured logging;
- report rendering;
- operating-system integration;
- background workers.

---

## 5. Recommended Repository Structure

```text
whatsapp-forensic-toolkit/
├── pyproject.toml
├── README.md
├── LICENSE
├── SECURITY.md
├── CHANGELOG.md
├── docs/
│   ├── architecture.md
│   ├── acquisition.md
│   ├── database.md
│   ├── validation.md
│   ├── limitations.md
│   └── legal-use.md
├── src/
│   └── wft/
│       ├── main.py
│       ├── bootstrap.py
│       ├── application/
│       │   ├── services/
│       │   ├── commands/
│       │   ├── queries/
│       │   └── dto/
│       ├── domain/
│       │   ├── models/
│       │   ├── enums/
│       │   ├── policies/
│       │   ├── provenance/
│       │   └── events/
│       ├── acquisition/
│       │   ├── importers/
│       │   ├── android_assistant/
│       │   └── desktop/
│       ├── parsers/
│       │   ├── contracts/
│       │   ├── exports/
│       │   ├── sqlite/
│       │   ├── desktop/
│       │   └── adapters/
│       ├── recovery/
│       │   ├── wal/
│       │   ├── journal/
│       │   ├── carving/
│       │   ├── correlation/
│       │   └── scoring/
│       ├── analysis/
│       │   ├── timeline/
│       │   ├── calls/
│       │   ├── media/
│       │   └── links/
│       ├── network/
│       │   ├── pcap/
│       │   ├── passive_capture/
│       │   ├── protocols/
│       │   └── geoip/
│       ├── reports/
│       │   ├── generators/
│       │   ├── templates/
│       │   ├── redaction/
│       │   └── manifests/
│       ├── infrastructure/
│       │   ├── database/
│       │   ├── filesystem/
│       │   ├── hashing/
│       │   ├── crypto/
│       │   ├── logging/
│       │   ├── workers/
│       │   └── settings/
│       └── ui/
│           ├── main_window.py
│           ├── pages/
│           ├── dialogs/
│           ├── widgets/
│           ├── models/
│           └── resources/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── validation/
│   ├── performance/
│   └── security/
├── scripts/
└── packaging/
```

---

## 6. Core Domain Model

### 6.1 Case

A case is the top-level investigation container.

Required fields:

- case ID;
- title;
- examiner;
- organisation;
- authorisation record;
- display time zone;
- creation time;
- case status;
- case encryption setting.

### 6.2 Evidence Item

An evidence item represents one logical source.

Examples:

- chat export ZIP;
- text export;
- SQLite package;
- database plus WAL and SHM;
- media folder;
- desktop artefact snapshot;
- previously decrypted backup;
- PCAP or PCAPNG.

### 6.3 Evidence File

Each evidence file stores:

- evidence ID;
- original filename;
- original path;
- stored path;
- file size;
- MIME type;
- source timestamps;
- import timestamp;
- SHA-256;
- optional SHA-512;
- verification status.

### 6.4 Working Copy

A working copy is a verified duplicate used for processing.

It references:

- parent evidence file;
- creation method;
- hash;
- parser or recovery run;
- processing state.

### 6.5 Derived Artefact

Examples:

- parsed message;
- recovered message;
- call record;
- media metadata;
- timeline event;
- network endpoint;
- examiner note;
- report.

### 6.6 Provenance

Every derived artefact must store:

- case ID;
- evidence item ID;
- source file ID;
- source hash;
- source table or section;
- source row ID;
- page, frame or byte offset when applicable;
- parser name and version;
- adapter version;
- recovery method;
- confidence;
- validation status;
- processing timestamp.

---

## 7. Evidence Repository

```text
cases/
└── CASE-2026-0001/
    ├── case.toml
    ├── originals/
    │   ├── E001/
    │   └── E002/
    ├── working/
    │   ├── W001/
    │   └── W002/
    ├── derived/
    │   ├── parsed/
    │   ├── recovered/
    │   ├── thumbnails/
    │   └── indexes/
    ├── reports/
    ├── exports/
    ├── logs/
    ├── manifests/
    └── case.db
```

### 7.1 Originals

The `originals` area:

- contains immutable copies;
- is never used for parser writes;
- is read-only where supported;
- has a hash manifest;
- preserves original names and metadata.

### 7.2 Working Copies

The `working` area contains:

- parser input copies;
- validated database copies;
- reconstructed snapshots;
- temporary decrypted output;
- media preview sources;
- extraction staging files.

### 7.3 Derived Data

The `derived` area contains:

- parsed snapshots;
- recovered fragments;
- thumbnails;
- indexes;
- correlation results;
- temporary analytical output.

### 7.4 Reports and Exports

Reports and exports are stored separately from evidence and include their own manifests and hashes.

---

## 8. Case Database

### 8.1 Database Engine

Use SQLite with:

- foreign keys enabled;
- explicit schema version;
- transactional migrations;
- backup before migration;
- post-migration integrity check;
- WAL mode for the case database only.

### 8.2 Logical Tables

#### Case and Evidence

- `cases`
- `examiners`
- `authorisations`
- `evidence_items`
- `evidence_files`
- `evidence_hashes`
- `working_copies`
- `acquisition_sessions`
- `chain_of_custody`
- `audit_events`
- `tool_versions`

#### Contacts and Conversations

- `accounts`
- `contacts`
- `contact_aliases`
- `groups`
- `group_participants`
- `conversations`

#### Messages

- `messages`
- `message_revisions`
- `message_reactions`
- `message_quotes`
- `message_mentions`
- `system_events`
- `locations`
- `shared_contacts`
- `links`

#### Media

- `media_items`
- `media_locations`
- `media_hashes`
- `media_metadata`
- `thumbnails`
- `exif_records`
- `orphan_media`

#### Calls and Network

- `calls`
- `call_participants`
- `network_capture_sessions`
- `network_flows`
- `network_endpoints`
- `stun_turn_events`
- `ip_classifications`

#### Recovery

- `recovery_runs`
- `recovery_candidates`
- `recovered_records`
- `recovery_sources`
- `parser_warnings`
- `schema_mappings`
- `confidence_assessments`

#### Analysis and Reporting

- `timeline_events`
- `tags`
- `artefact_tags`
- `bookmarks`
- `examiner_notes`
- `saved_searches`
- `correlations`
- `report_runs`
- `redaction_rules`
- `export_manifests`

---

## 9. Application Services

### 9.1 Case Service

- create and open cases;
- enforce authorisation acknowledgement;
- manage case locks;
- verify case integrity;
- archive and restore cases;
- manage case settings.

### 9.2 Evidence Service

- validate and import sources;
- stream-copy files;
- calculate hashes;
- verify copies;
- detect duplicates;
- register evidence;
- create working copies;
- prevent source modification.

### 9.3 Parse Service

- inspect source;
- determine source type;
- fingerprint schema;
- choose adapter;
- run parser;
- persist artefacts;
- record warnings and provenance.

### 9.4 Recovery Service

- create recovery runs;
- execute selected strategies;
- store candidates;
- calculate confidence;
- deduplicate;
- support examiner review.

### 9.5 Search Service

- create case-local indexes;
- execute full-text and structured search;
- paginate results;
- expose provenance-aware results;
- store saved searches.

### 9.6 Report Service

- build reproducible datasets;
- apply redaction;
- render HTML and PDF;
- create CSV and JSON exports;
- generate manifest;
- hash report output.

### 9.7 Audit Service

- append events;
- calculate hash chain;
- verify chain;
- redact secrets;
- expose audit history.

---

## 10. Evidence Import Flow

```text
User selects source
    ↓
Authorisation validated
    ↓
Source inspected
    ↓
Evidence record created
    ↓
Source stream-copied
    ↓
SHA-256 calculated
    ↓
Destination hash verified
    ↓
Original copy made read-only
    ↓
Working copy created
    ↓
Parser inspection queued
```

### 10.1 Import Protections

- copy instead of move;
- reject path traversal;
- reject unsafe symbolic links;
- limit archive expansion;
- limit extracted file count;
- validate file signatures;
- quarantine malformed files;
- preserve failed imports for review;
- never overwrite existing evidence.

---

## 11. Acquisition Architecture

### 11.1 Supported Sources

- user-provided export;
- SQLite package;
- media directory;
- desktop artefact snapshot;
- output from an approved forensic tool;
- previously decrypted backup;
- existing PCAP or PCAPNG;
- authorised passive capture.

### 11.2 Android Assistant

The Android assistant may:

- detect an authorised ADB device;
- record non-sensitive device metadata;
- guide a user-initiated export;
- copy genuinely accessible files;
- import third-party forensic output.

It must not:

- claim universal access to private WhatsApp storage;
- bypass scoped storage;
- exploit the device;
- steal credentials or tokens;
- install covert components.

### 11.3 Desktop Acquisition

The desktop module:

- discovers candidate locations;
- detects a running client;
- warns the examiner;
- creates a snapshot copy;
- hashes all copied artefacts;
- preserves SQLite, LevelDB, IndexedDB and cache files;
- invokes version-specific adapters.

---

## 12. Parser Architecture

### 12.1 Adapter Contract

```python
class ParserAdapter(Protocol):
    adapter_id: str
    adapter_version: str

    def inspect(self, source: Path) -> InspectionResult:
        ...

    def supports(self, inspection: InspectionResult) -> bool:
        ...

    def parse(
        self,
        source: Path,
        context: ParseContext,
    ) -> ParseResult:
        ...

    def capabilities(self) -> CapabilityDescriptor:
        ...
```

### 12.2 Parser Selection

```text
Source registered
    ↓
File signature inspection
    ↓
Source-type detection
    ↓
Schema fingerprinting
    ↓
Adapter scoring
    ↓
Compatibility probes
    ↓
Parse or unsupported result
```

### 12.3 Schema Fingerprint

A fingerprint may include:

- table names;
- columns and types;
- indexes;
- triggers;
- views;
- SQLite `user_version`;
- source application version;
- export patterns;
- selected non-sensitive structural samples.

### 12.4 Stable Internal Model

Adapters map changing source fields into stable internal entities.

Unknown fields should be preserved in extension metadata when practical and must not be silently discarded when potentially relevant.

---

## 13. Decryption Adapter Architecture

Decryption is conditional and only runs when lawful key material is supplied.

```python
class DecryptAdapter(Protocol):
    adapter_id: str
    adapter_version: str

    def identify(self, source: Path) -> float:
        ...

    def required_inputs(self, source: Path) -> list[str]:
        ...

    def validate_inputs(self, inputs: dict) -> ValidationResult:
        ...

    def decrypt(
        self,
        source: Path,
        destination: Path,
        inputs: dict,
    ) -> DecryptResult:
        ...

    def verify_output(self, destination: Path) -> ValidationResult:
        ...
```

Rules:

- no brute-force mode;
- no default passwords;
- no universal crypt-format assumptions;
- no transmission of keys;
- output must be validated before parsing;
- unsupported formats fail clearly;
- adapter version and parameters are recorded.

---

## 14. Recovery Architecture

### 14.1 Recovery Strategies

- WAL parsing;
- rollback-journal parsing;
- freelist analysis;
- unallocated-page carving;
- orphan-media correlation;
- thumbnail correlation;
- mobile/desktop cross-source comparison.

### 14.2 Recovery Flow

```text
Create recovery run
    ↓
Select verified working copies
    ↓
Execute independent strategies
    ↓
Generate candidates
    ↓
Validate candidate structure
    ↓
Assign confidence
    ↓
Deduplicate candidates
    ↓
Persist candidates
    ↓
Examiner accepts, rejects or leaves unresolved
```

### 14.3 Candidate Data

A recovery candidate contains:

- source file;
- page number;
- byte offset;
- WAL frame or journal location;
- raw fragment;
- parsed fields;
- recovery method;
- validation checks;
- confidence;
- duplicate group;
- examiner status;
- examiner note.

### 14.4 Confidence Levels

- **High:** complete structure with direct provenance.
- **Medium:** mostly valid structure with missing fields.
- **Low:** partial carving or weak correlation.
- **Rejected:** invalid, contradictory or duplicate.
- **Unresolved:** requires examiner review.

Recovered records remain separate from normal parsed records.

---

## 15. Media Architecture

```text
Register media
    ↓
Calculate hash
    ↓
Detect actual file type
    ↓
Extract metadata
    ↓
Generate derived preview
    ↓
Link to message where possible
    ↓
Classify as linked, duplicate or orphan
```

Original media is never modified.

Supported derived metadata may include:

- MIME type;
- dimensions;
- duration;
- codec;
- EXIF;
- embedded GPS metadata;
- device model;
- document metadata;
- thumbnails.

---

## 16. Historical Call Analysis

Parsed call data may include:

- voice or video;
- incoming, outgoing or missed;
- start time;
- duration;
- participants;
- conversation link;
- source record;
- recovered status;
- confidence.

Analytical views may include:

- calls per day;
- calls per contact;
- total duration;
- missed-call frequency;
- voice/video ratio;
- time-of-day patterns;
- message and call timeline correlation.

---

## 17. Live Network Metadata Module

This module is optional and disabled by default.

### 17.1 Purpose

During an authorised WhatsApp call, the module may analyse visible network metadata and update an approximate live endpoint map.

It may:

- capture UDP traffic visible to an authorised interface;
- detect probable STUN, TURN and ICE activity;
- extract visible IP addresses and ports;
- classify peer, relay, carrier or cloud infrastructure;
- identify ISP and ASN;
- estimate broad IP region;
- update the map while the call is active;
- save PCAP/PCAPNG and derived metadata.

### 17.2 Live Processing Flow

```text
Authorisation confirmed
    ↓
Capture interface selected
    ↓
Passive capture started
    ↓
UDP flow table updated
    ↓
Probable STUN/TURN events detected
    ↓
Visible endpoints extracted
    ↓
Endpoint classification
    ↓
Offline GeoIP lookup
    ↓
Map and timeline updated
    ↓
Capture stopped
    ↓
Capture file hashed and registered
```

### 17.3 Endpoint Classifications

- probable peer;
- WhatsApp relay;
- TURN server;
- cloud provider;
- mobile carrier gateway;
- VPN or proxy;
- local gateway;
- unknown.

### 17.4 Live Map Fields

- endpoint IP;
- classification;
- confidence;
- ISP;
- ASN;
- country;
- region;
- approximate city;
- first seen;
- last seen;
- packet count;
- relay warning.

### 17.5 Mandatory Limitations

The module cannot:

- decrypt audio or video;
- guarantee visibility of the remote peer;
- bypass WhatsApp IP protection;
- prove a caller’s physical location;
- treat IP geolocation as GPS evidence;
- reliably trace the complete media route.

Every map must show:

> IP-based location is approximate and may identify a relay, VPN, carrier gateway or cloud server rather than the call participant.

---

## 18. Timeline Architecture

Timeline sources:

- messages;
- calls;
- media;
- group events;
- recovered records;
- network events;
- examiner notes;
- acquisition actions.

Every event stores:

- raw timestamp;
- source epoch;
- source time zone if known;
- normalised UTC;
- display time zone;
- clock-skew adjustment;
- confidence;
- provenance.

```text
Collect events
    ↓
Normalise timestamps
    ↓
Apply documented clock correction
    ↓
Deduplicate
    ↓
Sort
    ↓
Persist
    ↓
Render paginated timeline
```

---

## 19. Search Architecture

Use SQLite FTS5 for:

- message text;
- contact names;
- group names;
- URLs;
- filenames;
- examiner notes.

Structured filters:

- date range;
- contact;
- group;
- message type;
- media type;
- call type;
- recovered-only;
- confidence;
- evidence source;
- tags;
- bookmarks;
- hash.

Controls:

- parameterised SQL;
- bounded regular expressions;
- pagination;
- cancellation;
- result limits;
- no external indexing.

---

## 20. Reporting Architecture

### 20.1 Report Flow

```text
Select report
    ↓
Validate artefact selection
    ↓
Store reproducible query
    ↓
Load paginated data
    ↓
Apply redactions
    ↓
Render HTML
    ↓
Render PDF if requested
    ↓
Generate manifest
    ↓
Hash report
    ↓
Record audit event
```

### 20.2 Report Requirements

Reports may include:

- case details;
- examiner;
- evidence inventory;
- evidence hashes;
- methodology;
- selected chats, calls, media or network events;
- provenance;
- confidence labels;
- recovery warnings;
- time-zone assumptions;
- parser versions;
- tool version;
- redactions;
- limitations;
- report-manifest hash.

### 20.3 Reproducibility

Store:

- filters;
- sort order;
- selected evidence;
- template version;
- parser versions;
- redaction rules;
- report-generator version;
- generation timestamp;
- output hash.

---

## 21. Audit Architecture

Important events:

- case created or opened;
- evidence imported;
- hash verified;
- parser run;
- recovery run;
- decryption attempt;
- report generated;
- redaction applied;
- case archived;
- application upgraded.

Hash-chain formula:

```text
event_hash = SHA256(previous_event_hash + canonical_event_json)
```

A hash chain detects modification but does not make a file physically immutable.

---

## 22. Background Processing

Use:

- `QThreadPool`;
- `QRunnable`;
- cancellation tokens;
- progress callbacks;
- bounded concurrency;
- isolated worker processes for risky parsers when needed.

Run outside the UI thread:

- evidence copy;
- hashing;
- archive extraction;
- database parsing;
- WAL recovery;
- media scanning;
- search indexing;
- report generation;
- PCAP processing.

---

## 23. Security Architecture

### 23.1 Threats

- malicious evidence;
- path traversal;
- archive bombs;
- crafted SQLite;
- unsafe HTML;
- media parser exploits;
- SQL injection;
- regex denial of service;
- secret leakage;
- report tampering;
- dependency compromise.

### 23.2 Controls

- file-signature validation;
- archive limits;
- HTML sanitisation;
- JavaScript disabled in evidence previews;
- content-security policy;
- parameterised SQL;
- read-only source access;
- worker isolation;
- bounded regular expressions;
- secrets stored in OS credential vault;
- optional case encryption;
- redacted logs;
- dependency pinning;
- SBOM;
- signed builds;
- manifest verification.

---

## 24. Error Architecture

Error categories:

- unsupported source;
- unsupported schema;
- corrupt database;
- hash mismatch;
- invalid archive;
- incomplete evidence;
- missing WAL;
- partial parse;
- recovery ambiguity;
- invalid key material;
- unsupported crypt format;
- report failure;
- case-lock failure.

```python
@dataclass(frozen=True)
class ToolError:
    code: str
    message: str
    severity: str
    recoverable: bool
    evidence_id: str | None
    source_path: str | None
    technical_details: str | None
    user_action: str | None
```

Rules:

- never silently discard records;
- never present partial output as complete;
- persist parser warnings;
- preserve failed working copies;
- provide an actionable message;
- audit important failures.

---

## 25. Performance Architecture

Use:

- paginated queries;
- lazy UI table models;
- indexed timestamps, conversations, contacts and hashes;
- streamed hashing and copies;
- batch database inserts;
- deferred thumbnails;
- bounded caches;
- background jobs.

Target scale:

- 500,000 messages with responsive interaction;
- 2,000,000 messages through pagination;
- 100 GB media directories;
- large WAL files;
- cancellable recovery jobs.

---

## 26. Dependency Injection

```python
class EvidenceService:
    def __init__(
        self,
        evidence_repository: EvidenceRepository,
        file_store: EvidenceFileStore,
        hash_service: HashService,
        audit_service: AuditService,
    ) -> None:
        ...
```

Bootstrap sequence:

```text
Load settings
    ↓
Initialise logging
    ↓
Create dependency container
    ↓
Register repositories
    ↓
Register application services
    ↓
Register parser adapters
    ↓
Register recovery strategies
    ↓
Register report generators
    ↓
Launch PySide6
```

---

## 27. Extension Architecture

### 27.1 Parser Plugins

A parser plugin contains:

- detector;
- schema fingerprint;
- adapter;
- capability metadata;
- compatibility matrix;
- validation fixtures.

### 27.2 Recovery Plugins

A recovery plugin contains:

- source requirements;
- scan strategy;
- candidate extractor;
- validation rules;
- confidence scorer;
- provenance builder.

### 27.3 Report Plugins

A report plugin contains:

- report definition;
- dataset query;
- template;
- redaction rules;
- manifest rules;
- validation tests.

### 27.4 Plugin Safety

Production plugins must:

- be signed;
- declare permissions;
- operate on working copies;
- report version and hash;
- avoid silent network access;
- run in isolation where appropriate.

---

## 28. Deployment Architecture

### 28.1 Windows Packaging

- PyInstaller one-folder build;
- Inno Setup or WiX installer;
- signed executable and installer;
- application files separate from cases;
- uninstall does not remove case data by default.

### 28.2 Suggested Paths

```text
Application:
%LOCALAPPDATA%\WhatsApp Forensic Toolkit\App
Settings:
%APPDATA%\WhatsApp Forensic Toolkit
Logs:
%LOCALAPPDATA%\WhatsApp Forensic Toolkit\Logs
Cases:
Examiner-selected secure directory
```

### 28.3 Portable Mode

Portable mode should:

- show a permanent portable indicator;
- avoid unencrypted local secrets;
- disable automatic external communication;
- document all runtime paths;
- use an examiner-selected case directory.

---

## 29. Build and Release Pipeline

```text
Checkout
    ↓
Install locked dependencies
    ↓
Format and lint
    ↓
Type check
    ↓
Unit tests
    ↓
Integration tests
    ↓
Security scan
    ↓
Generate SBOM
    ↓
Build executable
    ↓
Sign executable
    ↓
Create installer
    ↓
Generate checksums
    ↓
Publish compatibility and validation documents
```

Release artefacts:

- installer;
- portable package;
- checksums;
- SBOM;
- release notes;
- compatibility matrix;
- validation report;
- known limitations;
- signatures.

---

## 30. Testing Architecture

### Unit Tests

- hashing;
- safe copying;
- archive extraction;
- timestamp conversion;
- schema detection;
- parser mapping;
- recovery scoring;
- audit hash chain;
- report filtering;
- redaction.

### Integration Tests

- export ZIP to report;
- database plus WAL to recovered timeline;
- desktop snapshot to parsed chat;
- PCAP import to endpoint map;
- case archive and restore;
- schema migration.

### Forensic Validation

For each parser:

- controlled dataset;
- source hashes;
- expected parsed values;
- known deleted records;
- recovery comparison;
- false-positive measurements;
- false-negative measurements;
- supported-version record.

### Security Tests

- path traversal;
- archive bomb;
- malicious HTML;
- crafted SQLite;
- regex abuse;
- symlink attack;
- tampered manifest;
- tampered audit chain;
- dependency vulnerability scan.

---

## 31. Critical Data Flows

### 31.1 Evidence Import

```text
UI
→ EvidenceService
→ SourceValidator
→ EvidenceFileStore
→ HashService
→ EvidenceRepository
→ AuditService
```

### 31.2 Parsing

```text
UI
→ ParseService
→ SourceInspector
→ SchemaDetector
→ ParserRegistry
→ ParserAdapter
→ ArtefactRepository
→ ProvenanceRepository
→ AuditService
```

### 31.3 Recovery

```text
UI
→ RecoveryService
→ RecoveryStrategyRegistry
→ WAL / Journal / Carver
→ CandidateValidator
→ ConfidenceScorer
→ RecoveryRepository
→ Review UI
```

### 31.4 Reporting

```text
UI
→ ReportService
→ Query Builder
→ Redaction Engine
→ Template Renderer
→ PDF Generator
→ Manifest Generator
→ HashService
→ Report Repository
```

---

## 32. Key Architecture Decisions

### ADR-001: PySide6 Desktop Application

Chosen for:

- offline use;
- local evidence access;
- Windows distribution;
- native widgets;
- controlled background processing;
- embedded HTML chat and map views.

### ADR-002: SQLite Case Store

Chosen for:

- portability;
- transactions;
- FTS5;
- simple backup;
- no external database server.

### ADR-003: Immutable Originals

Original evidence is copied, hashed and protected before processing.

### ADR-004: Versioned Parser Adapters

WhatsApp schemas and export formats change, so one universal parser is not reliable.

### ADR-005: Separate Recovery Store

Recovered data has different certainty and provenance from normally parsed data.

### ADR-006: Passive Network Metadata Only

The toolkit may process authorised visible traffic but does not automate active interception.

### ADR-007: External Services Disabled by Default

Case content stays local unless the examiner explicitly enables a documented integration.

---

## 33. Final Architecture Summary

The architecture follows this controlled processing path:

```text
Authorise case
→ Import evidence
→ Hash and verify
→ Preserve original
→ Create working copy
→ Detect source and schema
→ Parse or recover
→ Store provenance
→ Search and analyse
→ Generate reproducible report
```

For live WhatsApp calls, the optional network module may detect visible UDP/STUN/TURN endpoints and plot approximate infrastructure regions while the call is active. It cannot guarantee the other participant’s IP, exact route or physical location, and it cannot decrypt call content.

The system’s reliability comes from:

- immutable original evidence;
- verified working copies;
- stable internal models;
- versioned adapters;
- separate recovery results;
- explicit confidence;
- complete provenance;
- controlled background processing;
- reproducible reporting;
- documented limitations.
