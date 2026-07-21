# WhatsApp Forensic Toolkit

## Corrected, Merged and Implementation-Ready Project Plan

**Document version:** 2.0  
**Project status:** Proposed  
**Primary implementation language:** Python  
**Primary delivery model:** Offline desktop application    
**Target host platforms:** Windows 10/11 initially; Linux and macOS in later releases  
**Target evidence sources:** User-provided WhatsApp exports, Android artefacts, supported device backups, WhatsApp Desktop artefacts and previously decrypted SQLite databases  

---

## 1. Executive Summary

The WhatsApp Forensic Toolkit is an offline-first digital-forensics application for acquiring, preserving, parsing, analysing and reporting WhatsApp-related evidence.


The first production release should focus on capabilities that are technically realistic and testable:

1. Create and manage forensic cases.
2. Import user-provided WhatsApp chat exports and media.
3. Import lawfully acquired SQLite databases, WAL files, journal files and media folders.
4. Acquire accessible WhatsApp Desktop artefacts without modifying the source.
5. Calculate and verify cryptographic hashes.
6. Parse multiple WhatsApp schema versions through versioned adapters.
7. Recover recoverable records from WAL, journal, freelist and unallocated SQLite areas on a best-effort basis.
8. Display chats, calls, contacts, groups and media in a forensic viewer.
9. Build searchable timelines and analytical dashboards.
10. Export reproducible HTML, PDF, CSV and evidence-package reports.
11. Maintain chain-of-custody and audit logs.

Advanced features such as encrypted-backup decryption, cloud-backup retrieval and live network metadata analysis must be implemented as optional, capability-gated modules. They must never be described as guaranteed features.

---

## 2. Product Vision

Create a reliable, transparent and defensible WhatsApp evidence-analysis platform that:

- Preserves original evidence.
- Clearly separates original, derived and recovered data.
- Records every transformation.
- Supports reproducible analysis.
- Communicates uncertainty instead of hiding it.
- Produces reports suitable for technical review.
- Remains usable for students while following professional DFIR principles.
- Works locally without sending case data to third-party servers by default.

---

## 3. Core Principles

### 3.1 Lawful Use

The application must only be used when the operator has:

- Consent from the device or account owner;
- Organisational authority;
- A court order, warrant or other valid legal basis; or
- Ownership of the device, account and network being examined.

The application must display an authorisation declaration before creating or opening a case.

### 3.2 Evidence Preservation

Original evidence must never be parsed directly when a working copy can be created.

The toolkit must:

- Mount or open source evidence read-only whenever possible.
- Copy evidence into an immutable evidence area.
- Hash evidence before and after copying.
- Analyse only verified working copies.
- Prevent silent overwriting of source files.
- Record the source path, acquisition method and timestamps.

### 3.3 Transparency

Every displayed artefact must show its origin and confidence:

- **Parsed:** obtained through a documented database field or export format.
- **Recovered:** carved or reconstructed from WAL, journal, freelist or unallocated data.
- **Inferred:** derived from correlation and not directly stored.
- **Unverified:** present but not yet validated.
- **Unsupported:** detected but not understood by the active parser.

### 3.4 No Guaranteed Recovery

Deleted-message and deleted-media recovery must be described as best-effort.

Recovery depends on:

- Whether the relevant bytes remain on disk;
- Whether a WAL or journal file is available;
- Whether pages were overwritten;
- Whether the schema is understood;
- Whether the database was vacuumed or checkpointed;
- Whether media files still exist;
- Whether encryption keys were obtained.

### 3.5 Privacy by Default

Case data must remain on the analyst’s machine unless the analyst deliberately enables an external integration.

External services must be disabled by default, including:

- IP geolocation services;
- Malware scanning APIs;
- Cloud-storage APIs;
- Online translation;
- Remote AI analysis;
- Telemetry and analytics.

---

## 4. Scope

## 4.1 In Scope for Version 1.0

### Case Management

- Create, open, archive and duplicate cases.
- Case number, title, examiner, organisation and notes.
- Evidence inventory.
- Chain-of-custody records.
- Audit trail.
- Time-zone configuration.
- Case-level encryption option.
- Report branding and analyst details.

### Evidence Import

- WhatsApp text exports.
- WhatsApp export ZIP archives containing media.
- SQLite databases supplied by the analyst.
- Associated `-wal`, `-shm` and rollback-journal files.
- Media directories.
- Contacts databases when lawfully acquired.
- Call databases or tables when available.
- WhatsApp Desktop working copies.
- Existing forensic images or mounted evidence paths.
- Previously decrypted backup databases.

### Parsing and Analysis

- Chats.
- Messages.
- Contacts.
- Groups.
- Group participants.
- Calls.
- Attachments and media references.
- Locations.
- Shared contacts.
- Documents.
- Links.
- Reactions where supported.
- Message edits where supported.
- Deleted markers where supported.
- Quoted and replied-to messages.
- System messages.
- Timeline generation.
- Keyword, regular-expression and date filtering.

### Reporting

- HTML report.
- PDF report.
- CSV exports.
- JSON export for interoperability.
- Evidence manifest.
- Hash manifest.
- Chain-of-custody report.
- Recovery-method appendix.
- Examiner notes.
- Redacted report mode.

## 4.2 Scope

These features available:

- Decryption of supported backup formats using a user-supplied key, password or extracted key material.
- Device acquisition through approved forensic tools.
- Cloud backup import using an official export or authorised API flow.
- Passive network metadata capture on a network owned or administered by the examiner.
- IP classification and approximate geolocation.
- Malware or phishing-link scanning using a user-configured API key.

## 5. Technical Reality and Corrected Assumptions

## 5.1 Modern Android Access

Modern Android versions isolate app-private data. A normal desktop application, ADB session or companion APK cannot generally read WhatsApp’s private internal database on a non-rooted device.

Supported non-root approaches should therefore be limited to:

- User-initiated WhatsApp chat export;
- User-selected files exposed through Android’s document picker;
- Accessible shared media;
- Approved device-backup sources;
- Manufacturer or enterprise-management exports;
- Data exported by a recognised forensic acquisition tool;
- Previously decrypted databases supplied by the analyst.

The UI must show the difference between:

- **Logical acquisition**;
- **File-system acquisition**;
- **Physical acquisition**;
- **User export**;
- **Third-party-tool import**.

## 5.2 ADB Limitations

ADB may help with:

- Device identification;
- Capturing device metadata with permission;
- Copying files that are actually accessible;
- Coordinating a user-authorised export workflow;
- Collecting logs in a test environment.

ADB must not be presented as a universal method for copying `/data/data/com.whatsapp/`.

Legacy `adb backup` support varies and is frequently unavailable or ineffective for modern applications. It may be offered only as an experimental compatibility check and must never be the primary acquisition strategy.

## 5.3 Encrypted Backup Formats

WhatsApp encrypted backup formats change over time. The implementation must use version-specific adapters rather than one hard-coded decryptor.

Each adapter must:

1. Identify the format from the file structure.
2. Validate that the supplied key material matches the format.
3. Verify integrity before accepting the result.
4. Write decrypted output only to a controlled working directory.
5. Confirm that the result is a valid SQLite database or recognised container.
6. Record the tool version, adapter version and cryptographic parameters.
7. Fail safely when the format is unknown.
8. Avoid guessing keys or silently returning corrupted output.

A backup must only be decrypted when the analyst supplies lawful key material or a supported export produced by an authorised acquisition process.

## 5.4 Cloud Backups

Cloud-backup access is a stretch capability.

The toolkit must not:

- Ask for raw account passwords;
- Capture browser cookies;
- Reuse stolen OAuth tokens;
- Reverse-engineer account authentication in production;
- Bypass provider controls.

Preferred workflows:

- Import an official account export;
- Import a backup exported by an authorised forensic platform;
- Use an official OAuth flow where a documented API supports the required action;
- Import an already downloaded and lawfully decrypted database.

## 5.5 Deleted Data

Deleted records may remain in:

- SQLite WAL frames;
- Rollback journals;
- Freelist pages;
- Unallocated portions of database pages;
- Cached thumbnails;
- Orphaned media files;
- Desktop caches;
- Exported notification or log artefacts.

The toolkit must preserve the distinction between a normal parsed record and a carved record. Recovered records must never be silently inserted into the normal message table without provenance metadata.

## 5.6 Call and Network Analysis

WhatsApp call content is encrypted. The toolkit must not claim to decrypt voice or video.

An authorised passive capture may reveal:

- IP addresses;
- Ports;
- packet timing;
- packet sizes;
- STUN, TURN or ICE metadata;
- relay infrastructure;
- traffic duration and volume.

An observed IP address may belong to:

- A peer;
- A TURN relay;
- A cloud provider;
- A carrier-grade NAT gateway;
- A VPN;
- A proxy;
- A content-delivery or signalling service.

The report must describe IP geolocation as approximate network-location intelligence, not proof of a person’s physical location.

---

## 6. Recommended Technology Stack

## 6.1 Core

- **Python:** 3.11 or newer.
- **GUI:** PySide6.
- **Embedded web rendering:** Qt WebEngine for chat and report previews.
- **Case database:** SQLite.
- **Schema migrations:** Alembic or an internal migration runner.
- **Validation:** Pydantic.
- **Dataframes and export:** pandas where appropriate.
- **Background work:** `QThreadPool` and `QRunnable`, or a controlled worker-process layer.
- **Configuration:** TOML.
- **Logging:** Python `logging` with structured JSON logs.

## 6.2 Forensic Processing

- Standard `sqlite3` for read-only database access.
- Dedicated SQLite page and WAL parsers for forensic recovery.
- `hashlib` for SHA-256 and optional SHA-512.
- `python-magic` or platform-safe MIME detection.
- Pillow for safe image metadata extraction.
- ExifRead or Pillow EXIF support.
- `ffprobe` for media metadata when bundled or installed.
- `yara-python` as an optional local scanning module.
- `maxminddb` as an optional offline IP-classification module.

## 6.3 Cryptography

- `cryptography` for supported encryption, key derivation and authenticated-encryption operations.
- custom cryptographic primitive implementations.
- Secrets stored using the operating-system credential vault where possible.
- Temporary decrypted material securely deleted on case closure where the file system allows it.

## 6.4 Reporting

- HTML templates with Jinja2.
- WeasyPrint for PDF output where platform packaging is stable.
- ReportLab as a fallback for selected report types.
- ZIP64 evidence packages.
- CSV and JSON exports.
- Optional digital signing of report manifests.

## 6.5 Packaging

- PyInstaller one-folder build for the first Windows release.
- Inno Setup or WiX Toolset for the installer.
- Code signing for production builds.
- Reproducible build instructions.
- Software bill of materials.
- Pinned dependency lock file.

---

## 7. High-Level Architecture

```text
┌───────────────────────────────────────────────────────────┐
│                      PySide6 Desktop UI                   │
│ Cases | Evidence | Chats | Calls | Timeline | Reports    │
└──────────────────────────┬────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────┐
│                    Application Services                   │
│ Case | Acquisition | Parsing | Search | Export | Audit   │
└──────────────┬───────────────┬───────────────┬────────────┘
               │               │               │
┌──────────────▼──────┐ ┌──────▼────────┐ ┌────▼────────────┐
│ Evidence Repository │ │ Parser Adapters│ │ Analysis Engine │
│ Originals/Working   │ │ Export/SQLite │ │ Timeline/Search │
│ Hashes/Manifests    │ │ Desktop/Crypt │ │ Correlation     │
└──────────────┬──────┘ └──────┬────────┘ └────┬────────────┘
               │               │               │
┌──────────────▼───────────────▼───────────────▼────────────┐
│                     Forensic Case Store                   │
│ Provenance | Parsed Artefacts | Recovered Artefacts      │
│ Notes | Tags | Audit Events | Report Metadata            │
└───────────────────────────────────────────────────────────┘
```

---

## 8. Evidence Repository Design

Each case uses a controlled directory:

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
    ├── notes/
    └── case.db
```

### 8.1 Original Evidence

The `originals` directory contains immutable copies.

Controls:

- Read-only file permissions where supported.
- No parser writes.
- SHA-256 manifest.
- Original filename preserved.
- Source path recorded separately.
- Import timestamp stored in UTC.
- Size and file-system timestamps recorded.
- Optional examiner signature.

### 8.2 Working Copies

Working copies are created for:

- SQLite validation;
- WAL replay experiments;
- Schema inspection;
- Decryption output;
- Thumbnail generation;
- Media transcoding for preview;
- Text indexing.

Every working copy must reference its parent evidence item.

### 8.3 Derived Artefacts

Derived artefacts include:

- Parsed rows;
- Recovered rows;
- thumbnails;
- extracted EXIF;
- OCR output when enabled;
- timeline events;
- report files;
- search indexes.

Derived data must never be confused with original evidence.

---

## 9. Case Database Model

The case database should contain at least the following logical tables.

### 9.1 Case and Evidence

- `cases`
- `examiners`
- `evidence_items`
- `evidence_files`
- `evidence_hashes`
- `acquisition_sessions`
- `chain_of_custody`
- `audit_events`
- `tool_versions`

### 9.2 Identity and Conversation

- `accounts`
- `contacts`
- `contact_aliases`
- `groups`
- `group_participants`
- `conversations`

### 9.3 Message Artefacts

- `messages`
- `message_revisions`
- `message_reactions`
- `message_quotes`
- `message_mentions`
- `system_events`
- `locations`
- `shared_contacts`
- `links`

### 9.4 Media

- `media_items`
- `media_locations`
- `media_hashes`
- `thumbnails`
- `media_metadata`
- `exif_records`
- `orphan_media`

### 9.5 Calls and Network Events

- `calls`
- `call_participants`
- `network_capture_sessions`
- `network_endpoints`
- `stun_turn_events`
- `ip_classifications`

### 9.6 Recovery and Provenance

- `recovery_runs`
- `recovered_records`
- `recovery_sources`
- `parser_warnings`
- `schema_mappings`
- `provenance_links`
- `confidence_assessments`

### 9.7 Analysis

- `timeline_events`
- `tags`
- `artefact_tags`
- `bookmarks`
- `examiner_notes`
- `saved_searches`
- `correlations`

### 9.8 Reporting

- `report_runs`
- `report_sections`
- `redaction_rules`
- `export_manifests`
- `digital_signatures`

---

## 10. Provenance Requirements

Every parsed or recovered artefact must store:

- Case ID.
- Evidence item ID.
- Source filename.
- Source hash.
- Source table or file region.
- Source row ID when available.
- Parser name and version.
- Schema adapter version.
- Acquisition method.
- Parse timestamp.
- Original timestamp value.
- Normalised UTC timestamp.
- Display time zone.
- Recovery method, if applicable.
- Confidence level.
- Validation status.
- Warning flags.
- Parent artefact references.

For carved data, also store:

- Page number;
- byte offset;
- WAL frame number;
- journal location;
- carving signature;
- validation checks;
- competing interpretations.

---

## 11. Module Breakdown

## 11.1 Case Manager

Responsibilities:

- Create and validate case directories.
- Record examiner information.
- Enforce authorisation acknowledgement.
- Manage case locking.
- Configure time zone.
- Encrypt sensitive case settings.
- Archive and restore cases.
- Verify manifests.
- Detect accidental evidence modification.

## 11.2 Evidence Importer

Supported import modes:

1. WhatsApp export ZIP.
2. WhatsApp text export.
3. SQLite database package.
4. Database plus WAL and SHM.
5. Media directory.
6. Desktop artefact directory.
7. Third-party forensic export.
8. Previously decrypted backup.
9. PCAP or PCAPNG from an authorised capture.
10. Generic evidence folder.

The importer must:

- Copy instead of move.
- Hash during streaming copy.
- Verify the copied hash.
- Detect duplicates.
- Avoid following unsafe symbolic links.
- Reject path traversal in ZIP files.
- Limit archive expansion.
- Quarantine malformed files.
- Record import errors without modifying originals.

## 11.3 Android Acquisition Assistant

This is a guided assistant, bypass module.

Allowed workflows:

- Display steps for a user-initiated chat export.
- Import files selected through the phone’s document picker.
- Detect an authorised ADB device.
- Record non-sensitive device metadata.
- Copy accessible files.
- Import output from an approved forensic acquisition tool.
- Document the acquisition method.

The assistant must never claim successful private-database acquisition unless the file was actually provided and verified.

## 11.4 Desktop Acquisition Module

Responsibilities:

- Detect supported WhatsApp Desktop installations.
- Identify candidate artefact directories.
- Warn when the application is running.
- Create a snapshot copy before parsing.
- Hash copied files.
- Preserve LevelDB, IndexedDB, SQLite and cache structures.
- Use version-specific parsers.
- Record unsupported versions.
- Avoid terminating or modifying the source application unless the analyst explicitly performs that action outside the toolkit.

## 11.5 Backup Decryption Adapter

The adapter framework must support plugins such as:

```text
DecryptAdapter
├── can_identify(file) -> confidence
├── required_inputs(file) -> list
├── validate_inputs(inputs) -> result
├── decrypt(source, destination, inputs) -> result
├── verify_output(destination) -> result
└── describe_method() -> metadata
```

## 11.6 Schema Detection and Parsing

WhatsApp schemas change. The parser must not depend on one fixed table layout.

Workflow:

1. Open the working copy read-only.
2. Verify the SQLite header.
3. Record `PRAGMA` values.
4. Enumerate tables, indexes, triggers and views.
5. Fingerprint the schema.
6. Select the most appropriate adapter.
7. Run compatibility probes.
8. Parse known artefacts.
9. Preserve unknown columns.
10. Record warnings and unsupported structures.
11. Never modify the evidence database.

Adapter output must map source fields into a stable internal schema.

## 11.7 Deleted-Record Recovery

Recovery should be separated into independent strategies:

### Strategy A: WAL Parsing

- Parse valid WAL frames.
- Verify frame checksums.
- Associate frames with database pages.
- Identify committed and uncommitted states.
- Reconstruct historical row variants when possible.
- Preserve frame and offset provenance.

### Strategy B: Rollback-Journal Parsing

- Detect journal format.
- Extract valid page images.
- Reconstruct previous page states where possible.
- Record transaction context.

### Strategy C: Freelist and Unallocated-Page Carving

- Parse SQLite page structure.
- Search candidate cells.
- Validate serial types and record headers.
- Score candidate records.
- Avoid presenting low-confidence byte strings as confirmed messages.

### Strategy D: Orphan-Media Correlation

- Hash all media files.
- Match database hashes, filenames and timestamps.
- Detect files not referenced by parsed rows.
- Correlate by thumbnail, size, MIME type and nearby timestamps.
- Label correlations as inferred unless directly proven.

### Recovery Confidence

- **High:** full record structure, valid fields and direct provenance.
- **Medium:** mostly valid structure with one or more missing fields.
- **Low:** partial carving or correlation only.
- **Rejected:** invalid, contradictory or duplicate candidate.

## 11.8 Media Processor

Functions:

- file-type detection.
- Hash calculation.
- Thumbnail generation.
- Metadata extraction.
- EXIF display.
- Audio and video duration extraction.
- Orphan detection.
- Duplicate detection.
- Preview generation.
- Optional local malware scanning.
- Optional redaction of faces or metadata in exported copies.

The original media file must never be altered.

## 11.9 Call Analysis

Historical call analysis may include:

- Voice or video type.
- Incoming, outgoing or missed direction.
- Participants.
- Start time.
- End time.
- Duration.
- Conversation linkage.
- Source record provenance.
- Recovered status.
- Confidence and warning flags.

Analytical views:

- Calls per day.
- Calls per contact.
- Total duration.
- Missed-call frequency.
- Time-of-day distribution.
- Timeline correlation with messages.

## 11.10 Passive Network Metadata Module

This module is optional and disabled by default.

Prerequisites:

- The examiner owns or administers the capture point.
- The case contains written authority.
- The user confirms local legal requirements.
- The capture interface is explicitly selected.
- The application records capture start and stop events.

Permitted functions:

- Import an existing PCAP/PCAPNG.
- Capture traffic visible to the authorised host interface.
- Filter probable STUN, TURN and UDP flows.
- Extract non-content metadata.
- Classify endpoints.
- Use an offline GeoIP database.
- Mark cloud and relay infrastructure.
- Export packet references and timestamps.

 functions:

- ARP spoofing automation.
- Credential interception.
- TLS interception.
- Call-content extraction.
- Decryption-key theft.
- Covert network persistence.
- Claims of exact caller location.

## 11.11 Timeline and Correlation Engine

The timeline combines:

- Messages.
- Calls.
- Group events.
- Media creation times.
- Export times.
- Recovered artefacts.
- Network events.
- Examiner notes.

Features:

- UTC-normalised storage.
- User-selected display time zone.
- Original timestamp preservation.
- Clock-skew notes.
- Multiple source comparison.
- Duplicate suppression.
- Source toggles.
- Confidence filters.
- Bookmarking.
- Exportable timeline.

## 11.12 Search Engine

Search capabilities:

- Exact phrase.
- Keyword.
- Boolean operators.
- Regular expressions with safe limits.
- Date range.
- Contact.
- Group.
- Message type.
- Media type.
- Calls.
- Recovered-only.
- Confidence level.
- Tags and bookmarks.
- Hash search.
- Phone-number normalisation.
- URL and domain search.

For performance, use SQLite FTS5 or a case-local index. The original evidence remains untouched.

## 11.13 Reporting Engine

Report types:

1. Case summary.
2. Evidence inventory.
3. Hash-verification report.
4. Chat transcript.
5. Call report.
6. Timeline report.
7. Deleted-recovery report.
8. Media report.
9. Network-metadata report.
10. Chain-of-custody report.
11. Examiner-notes report.
12. Full evidence package.

Every report must state:

- Tool name and version.
- Parser versions.
- Case number.
- Examiner.
- Report generation date.
- Display time zone.
- Evidence hashes.
- Filters applied.
- Recovery methods used.
- Limitations.
- Confidence labels.
- Redactions.
- Page numbers.
- Report-manifest hash.

---

## 12. User Interface

## 12.1 Main Navigation

- Dashboard
- Cases
- Evidence
- Chats
- Contacts
- Groups
- Calls
- Media
- Timeline
- Recovered
- Network
- Search
- Reports
- Audit Log
- Settings

## 12.2 Dashboard

Display:

- Evidence-item count.
- Parsed-message count.
- Recovered-message count.
- Contact and group totals.
- Media totals.
- Call totals and duration.
- Date range.
- Parser warnings.
- Hash-verification status.
- Unsupported artefacts.
- Recent examiner activity.

## 12.3 Chat Viewer

Features:

- WhatsApp-inspired but clearly forensic visual design.
- Sent and received message distinction.
- Original and normalised timestamps.
- Source and confidence badges.
- Recovered-record banner.
- Message details panel.
- Media preview.
- Reply and quote linkage.
- Reactions.
- Edit history.
- Keyword highlighting.
- Bookmark and note actions.
- Export selected range.

The interface must not imply that visual similarity to WhatsApp proves authenticity. Provenance details must remain accessible.

## 12.4 Evidence View

Each evidence card displays:

- Evidence ID.
- Description.
- Source.
- Acquisition method.
- Original size.
- SHA-256.
- Import time.
- Verification result.
- Parser status.
- Warnings.
- Child working copies.
- Reports using the evidence.

## 12.5 Recovery View

The recovery workspace includes:

- Recovery strategy.
- Source file.
- Candidate count.
- Accepted, rejected and unresolved counts.
- Confidence filters.
- Hex and page preview.
- Parsed-field preview.
- Duplicate comparison.
- Examiner acceptance note.
- Export with provenance.

## 12.6 Accessibility

- Keyboard navigation.
- Screen-reader labels.
- High-contrast mode.
- Scalable typography.
- Colour-independent status indicators.
- Focus indicators.
- Reduced-motion option.
- Minimum touch/click targets.
- Exported reports with selectable text.
- Accessible HTML reports.

---

## 13. Security Design

## 13.1 Threat Model

Protect against:

- Unauthorised access to case data.
- Malicious evidence files.
- Archive bombs.
- Path traversal.
- SQL injection in internal queries.
- Unsafe HTML in chat exports.
- Media parser vulnerabilities.
- Dependency compromise.
- Accidental evidence modification.
- Credential leakage.
- Debug logs containing private content.
- Report tampering.
- Case-directory substitution.

## 13.2 Controls

- Sanitise imported HTML.
- Disable JavaScript in evidence previews unless strictly required.
- Use content-security policies.
- Open databases read-only.
- Parameterise SQL.
- Limit regex execution.
- Use worker-process isolation for risky parsers.
- Apply archive size and file-count limits.
- Validate file signatures.
- Store secrets in the OS keychain.
- Encrypt optional case vaults with authenticated encryption.
- Sign manifests.
- Redact sensitive values in logs.
- Do not collect telemetry by default.
- Maintain dependency allowlists.
- Generate an SBOM for releases.
- Verify application updates cryptographically.

## 13.3 Audit Logging

Audit events include:

- Case creation and opening.
- Evidence import.
- Hash calculation and verification.
- Parser execution.
- Decryption attempt.
- Recovery run.
- Search execution when configured.
- Artefact tagging.
- Examiner notes.
- Export generation.
- Report redaction.
- Case archive.
- Application version change.

Audit records should be append-only and chained by hash:

```text
event_hash = SHA256(previous_event_hash + canonical_event_json)
```

This detects modification but does not make the log physically immutable. Reports must describe the exact protection used.

---

## 14. Time Handling

Time is critical in forensic analysis.

The toolkit must:

- Preserve raw timestamp values.
- Preserve source units.
- Record detected epoch type.
- Convert to UTC for internal comparison.
- Display in the selected case time zone.
- Show daylight-saving offsets where relevant.
- Allow per-source time-zone correction.
- Record examiner-applied clock-skew adjustments.
- Never overwrite the original timestamp.
- Include time-zone assumptions in reports.

---

## 15. Error Handling and Uncertainty

Errors must be visible and actionable.

Example classifications:

- Unsupported schema.
- Corrupt database.
- Missing WAL dependency.
- Hash mismatch.
- Unknown crypt format.
- Invalid key material.
- Partial parse.
- Timestamp ambiguity.
- Media missing.
- Duplicate artefact.
- Recovery false-positive risk.
- External service unavailable.

The application must never silently discard a failed record. It should store parser warnings with sufficient context for review.

---

## 16. Performance Requirements

Initial targets:

- Open a case containing 500,000 parsed messages without loading all rows into memory.
- Paginate chat and search results.
- Stream evidence copies and hashing.
- Process media in batches.
- Run parsing, hashing and report generation outside the UI thread.
- Cancel long-running operations safely.
- Resume interrupted imports where practical.
- Use database indexes for timestamp, conversation, contact, hash and source.
- Generate thumbnails lazily.
- Cache only derived data.
- Show progress and current operation.
- Avoid UI freezes.

Recommended test datasets:

- 1,000 messages.
- 50,000 messages.
- 500,000 messages.
- 2,000,000 messages.
- 100 GB media directory.
- Corrupt database.
- Database with WAL.
- Unknown schema.
- Duplicate evidence package.

---

## 17. Validation and Testing

## 17.1 Unit Tests

- Hash calculation.
- Manifest generation.
- Timestamp conversion.
- Phone-number normalisation.
- Safe ZIP extraction.
- Schema fingerprinting.
- Parser field mapping.
- WAL checksum validation.
- Recovery scoring.
- Report filtering.
- Redaction rules.
- Audit hash chaining.
- Encryption and decryption adapters using legal test vectors.

## 17.2 Integration Tests

- Import export ZIP to report.
- Import DB plus WAL to timeline.
- Desktop acquisition to parsed chats.
- Decryption adapter to verified SQLite.
- Recovery run to provenance display.
- Media folder to orphan-media report.
- PCAP import to endpoint report.
- Case archive and restore.
- Application upgrade with schema migration.

## 17.3 Forensic Validation

For each supported parser:

- Create a controlled WhatsApp test dataset.
- Record known messages, calls and media.
- Export or acquire the test artefacts lawfully.
- Compare expected and parsed values.
- Delete selected test records.
- Compare recovery results.
- Document false positives and false negatives.
- Repeat across supported versions.
- Store test hashes and expected outputs.

## 17.4 Security Tests

- Malicious ZIP path traversal.
- Archive bomb.
- Embedded script in exported HTML.
- Crafted SQLite file.
- Oversized media metadata.
- Regex denial of service.
- SQL injection attempts.
- Symlink attacks.
- Case-directory permission failure.
- Tampered manifest.
- Tampered audit log.
- Dependency vulnerability scan.

## 17.5 User-Acceptance Tests

- Create a case.
- Import evidence.
- Verify hashes.
- Find a chat.
- Filter messages.
- Add an examiner note.
- Review recovered records.
- Export a redacted report.
- Verify report manifest.
- Archive the case.

---

## 18. Development Roadmap

## Phase 0: Research, Governance and Test Data

**Deliverables:**

- Legal-use policy.
- Authorisation acknowledgement.
- Threat model.
- Supported-source matrix.
- Controlled test datasets.
- Evidence-directory specification.
- Coding standards.
- CI pipeline.
- Dependency policy.

**Exit criteria:**

- Scope approved.
- Unsafe features excluded.
- Test data available.
- Case and evidence terminology finalised.

## Phase 1: Case and Evidence Foundation

**Deliverables:**

- PySide6 shell.
- Case manager.
- Evidence importer.
- Streaming SHA-256.
- Evidence manifest.
- Audit log.
- SQLite case database.
- Background-job framework.

**Exit criteria:**

- A case can be created.
- Evidence can be copied and verified.
- No original file is modified.
- Imports remain responsive.

## Phase 2: Export and SQLite Parsing

**Deliverables:**

- WhatsApp text-export parser.
- ZIP and media importer.
- SQLite validator.
- Schema fingerprinting.
- First versioned parser adapter.
- Contacts, groups, messages and media mapping.

**Exit criteria:**

- Controlled datasets parse accurately.
- Unsupported schemas fail safely.
- Provenance is present for every artefact.

## Phase 3: Chat, Search and Timeline UI

**Deliverables:**

- Chat viewer.
- Evidence detail panel.
- FTS search.
- Timeline.
- Tags, bookmarks and notes.
- Paginated data models.

**Exit criteria:**

- Large datasets do not freeze the UI.
- Search and filters are reproducible.
- Timestamps and source details are visible.

## Phase 4: Recovery Engine

**Deliverables:**

- WAL parser.
- Rollback-journal parser.
- Page carver.
- Recovery confidence model.
- Recovery-review UI.
- Orphan-media correlation.

**Exit criteria:**

- Known deleted test records produce documented results.
- False positives are measured.
- Recovered data is never presented as normal parsed data.

## Phase 5: Reporting

**Deliverables:**

- HTML and PDF reports.
- CSV and JSON exports.
- Evidence and hash manifests.
- Chain-of-custody report.
- Redaction rules.
- Report-manifest signing.

**Exit criteria:**

- Reports reproduce selected filters.
- Reports state limitations.
- Manifest verification succeeds.

## Phase 6: Desktop Acquisition

**Deliverables:**

- Windows artefact discovery.
- Safe snapshot copy.
- Desktop schema adapters.
- Version detection.
- Parser-warning system.

**Exit criteria:**

- Source files remain unchanged.
- Supported desktop versions are documented.
- Unsupported versions are clearly reported.

## Phase 7: Conditional Decryption Support

**Deliverables:**

- Adapter interface.
- Key-input workflow.
- Secure secret handling.
- Format detection.
- Output validation.
- Test vectors.
- Failure reporting.

**Exit criteria:**

- Only supported formats are accepted.
- No brute-force capability.
- Invalid keys fail safely.
- Decrypted output is verified before parsing.

## Phase 8: Optional Network Metadata

**Deliverables:**

- PCAP import.
- Passive authorised capture.
- STUN/TURN detection.
- Endpoint classification.
- Offline GeoIP.
- Limitations report.

**Exit criteria:**

- active interception function.
- content-decryption claim.
- Relay and VPN ambiguity is clearly displayed.

## Phase 9: Hardening and Release

**Deliverables:**

- Installer.
- Code signing.
- Dependency lock.
- SBOM.
- Security review.
- Performance benchmarks.
- User manual.
- Examiner manual.
- Validation report.
- Known-limitations document.

**Exit criteria:**

- Release checklist passes.
- Test suite passes on Windows 10 and 11.
- No critical security findings.
- Validation report published with the release.

---

## 19. Suggested Repository Structure

```text
whatsapp-forensic-toolkit/
├── pyproject.toml
├── README.md
├── LICENSE
├── SECURITY.md
├── docs/
│   ├── architecture.md
│   
│   
│   
│ 
│   
├── src/
│   └── wft/
│       ├── __init__.py
│       ├── main.py
│       ├── application/
│       │   ├── case_service.py
│       │   ├── evidence_service.py
│       │   ├── parse_service.py
│       │   ├── recovery_service.py
│       │   ├── search_service.py
│       │   └── report_service.py
│       ├── domain/
│       │   ├── models.py
│       │   ├── enums.py
│       │   ├── provenance.py
│       │   └── confidence.py
│       ├── infrastructure/
│       │   ├── database/
│       │   ├── filesystem/
│       │   ├── hashing/
│       │   ├── crypto/
│       │   └── logging/
│       ├── acquisition/
│       │   ├── importers/
│       │   ├── android_assistant/
│       │   └── desktop/
│       ├── parsers/
│       │   ├── exports/
│       │   ├── sqlite/
│       │   ├── desktop/
│       │   └── adapters/
│       ├── recovery/
│       │   ├── wal/
│       │   ├── journal/
│       │   ├── carving/
│       │   └── correlation/
│       ├── analysis/
│       │   ├── timeline.py
│       │   ├── calls.py
│       │   ├── links.py
│       │   └── media.py
│       ├── network/
│       │   ├── pcap_import.py
│       │   ├── passive_capture.py
│       │   ├── stun_turn.py
│       │   └── geoip.py
│       ├── reports/
│       │   ├── templates/
│       │   ├── html.py
│       │   ├── pdf.py
│       │   ├── csv_export.py
│       │   └── manifests.py
│       └── ui/
│           ├── main_window.py
│           ├── pages/
│           ├── widgets/
│           ├── models/
│           ├── workers/
│           └── resources/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── validation/
│   ├── security/
│   └── fixtures/
├── scripts/
│   ├── build_windows.ps1
│   ├── verify_release.py
│   └── generate_sbom.py
└── packaging/
    ├── pyinstaller/
    └── installer/
```

---

## 20. Configuration

Example `case.toml`:

```toml
case_id = "CASE-2026-0001"
title = "Authorised WhatsApp Examination"
examiner = "Examiner Name"
organisation = "Organisation"
created_utc = "2026-07-19T12:00:00Z"
display_timezone = "Asia/Kolkata"
case_encryption_enabled = true
external_services_enabled = false
```

Example application settings:

```toml
[security]
telemetry = false
allow_external_services = false
require_authorisation_acknowledgement = true
auto_lock_minutes = 15

[hashing]
primary = "sha256"
secondary = "sha512"

[parsing]
open_source_databases_read_only = true
preserve_unknown_columns = true
store_raw_timestamp_values = true

[network]
enabled = false
active_interception = false
offline_geoip_only = true

[reports]
include_limitations = true
include_tool_versions = true
include_manifest_hash = true
```

---

## 21. Acceptance Criteria for Version 1.0

Version 1.0 is ready only when:

- The app creates a valid forensic case.
- Imported evidence is hashed and verified.
- Original evidence remains unchanged.
- WhatsApp text and ZIP exports are parsed.
- At least one controlled SQLite schema is fully supported.
- Schema mismatches are clearly reported.
- Messages, calls, contacts, groups and media retain provenance.
- Recovery results are labelled and scored.
- Large datasets do not freeze the interface.
- Reports include hashes, filters, time zones and limitations.
- Audit logs detect modification.
- Security tests pass.
- Windows 10 and Windows 11 builds pass.
- The limitations document matches actual capabilities.
- The application does not advertise unsupported decryption or acquisition.

---

## 22. Release Capability Matrix

Every release must publish a matrix similar to:

| Capability | Status | Conditions | Validation |
|---|---|---|---|
| Text export import | Supported | User-provided export | Fully tested |
| Export ZIP media linking | Supported | Media present in archive | Fully tested |
| SQLite parsing | Version-specific | Recognised schema | Adapter validation |
| WAL recovery | Best effort | WAL present and valid | Measured |
| Freelist carving | Experimental | Bytes not overwritten | False positives documented |
| Desktop artefact parsing | Version-specific | Supported client build | Adapter validation |
| Encrypted-backup decryption | Conditional | Supported format and lawful key material | Test vectors |
| Cloud backup | Not in v1 | Official or authorised export only | Not applicable |
| Live network metadata | Optional | Owned or authorised capture point | Lab tested |
| Call-content decryption | Not supported | Technically and legally excluded | Not applicable |
| Exact caller location | Not supported | IP data is approximate | Not applicable |

---

## 23. Documentation Deliverables

Required documentation:

- README.
- Installation guide.
- User manual.
- Examiner workflow.
- Evidence-handling guide.
- Supported-source matrix.
- Parser compatibility matrix.
- Validation report.
- Known limitations.
- Security policy.
- Privacy policy.
- Legal-use policy.
- Developer architecture.
- Plugin-development guide.
- Release and rollback guide.
- Dependency and SBOM documentation.

---

## 24. Future Enhancements

Future features may include:

- Additional schema adapters.
- iOS backup imports through lawful backup sources.
- Multi-device comparison.
- Mobile and desktop discrepancy analysis.
- Enhanced media correlation.
- Local language detection.
- Offline entity extraction.
- Advanced graph analysis.
- Case-to-case hash matching.
- STIX-compatible export.
- Integration with established forensic suites through documented formats.
- Digital-signature verification.
- Team review with encrypted case bundles.
- Automated validation-dataset generation.
- Parser plugin marketplace with signed plugins.

Any future feature must preserve the project’s legal, forensic and privacy requirements.

---

## 25. Final Recommendation

Build the project incrementally.

The correct first milestone is not universal Android extraction or live caller tracking. The correct first milestone is a defensible evidence-processing pipeline:

```text
Create case
→ Import authorised evidence
→ Hash and verify
→ Preserve originals
→ Parse a working copy
→ Record provenance
→ Search and review
→ Export a reproducible report
```

After this foundation is tested, add:

1. Versioned SQLite parsing.
2. WAL and journal recovery.
3. Desktop artefact support.
4. Conditional decryption adapters.
5. Optional passive network metadata analysis.

This approach produces a useful, realistic and professionally defensible forensic toolkit without making claims that modern Android security, evolving WhatsApp formats or encrypted network traffic cannot support.
