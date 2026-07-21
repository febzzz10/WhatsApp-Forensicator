# WhatsApp Forensic Toolkit — Application Flow

**Document version:** 1.0  
**Project:** WhatsApp Forensic Toolkit  
**Application type:** Offline-first forensic desktop application  
**Primary UI:** PySide6  
**Primary platform:** Windows 10/11  
**Primary users:** Authorised forensic examiners, cybersecurity analysts, incident responders and supervised students  

---

## 1. Purpose

This document defines the complete application flow for the WhatsApp Forensic Toolkit.

It explains:

- how users enter and navigate the application;
- how forensic cases are created and opened;
- how evidence is imported and verified;
- how parsers and recovery modules run;
- how chats, calls, media and timelines are reviewed;
- how live authorised network metadata is captured and mapped;
- how reports are generated;
- how errors, unsupported formats and incomplete evidence are handled;
- how the application protects original evidence at every stage.

The application must never present inaccessible or uncertain evidence as guaranteed. Every flow must preserve the distinction between:

- **Parsed data**
- **Recovered data**
- **Inferred data**
- **Manual examiner notes**
- **Unsupported or unverified data**

---

# 2. Core Application Flow

```text
Launch Application
    ↓
Read Legal and Authorisation Notice
    ↓
Unlock Application or Continue in Local Mode
    ↓
Open Existing Case or Create New Case
    ↓
Confirm Case Authorisation
    ↓
Import Evidence
    ↓
Hash and Verify Evidence
    ↓
Create Working Copy
    ↓
Detect Source Type and Schema
    ↓
Parse Supported Artefacts
    ↓
Run Optional Recovery
    ↓
Review Chats, Calls, Media and Timeline
    ↓
Add Notes, Tags and Bookmarks
    ↓
Generate Report or Export Package
    ↓
Verify Report Manifest
    ↓
Archive or Close Case
```

---

# 3. Application States

The application can be in one of the following top-level states:

| State | Description |
|---|---|
| No Case Open | Application is running, but no case is active |
| Case Loading | Case database, manifest and files are being verified |
| Case Open | User can review and process evidence |
| Case Locked | Case requires password or examiner unlock |
| Importing | Evidence is being copied and hashed |
| Parsing | Supported evidence is being processed |
| Recovering | Deleted or unallocated artefacts are being examined |
| Capturing | Authorised passive network capture is active |
| Reporting | Report or export is being generated |
| Case Closing | Jobs are stopped, files are verified and state is saved |
| Error Recovery | Application is resolving or reporting a failed operation |

---

# 4. First Launch Flow

## 4.1 First Launch

```text
Start Application
    ↓
Load Global Settings
    ↓
Check Application Data Directories
    ↓
Check Database and Migration Components
    ↓
Show Legal Use Notice
    ↓
Accept or Exit
    ↓
Configure Examiner Profile
    ↓
Configure Default Case Location
    ↓
Configure Security Preferences
    ↓
Open Home Screen
```

## 4.2 First-Launch Screens

### Screen 1: Welcome

Displays:

- application name;
- version;
- offline-first statement;
- forensic integrity statement;
- legal-use warning;
- links to documentation.

Actions:

- Continue
- Exit

### Screen 2: Legal and Ethical Use

The user must acknowledge that:

- they have lawful authority;
- they will not use the tool for unauthorised surveillance;
- network capture is limited to authorised networks;
- IP-based locations are approximate;
- deleted-data recovery is not guaranteed;
- the application cannot decrypt call audio or video.

Actions:

- I Understand and Agree
- Exit

### Screen 3: Examiner Profile

Fields:

- examiner name;
- organisation;
- job title;
- credentials;
- optional email;
- optional phone.

Actions:

- Save and Continue
- Skip Optional Fields
- Back

### Screen 4: Storage and Security

Options:

- default case location;
- enable case encryption by default;
- automatic lock duration;
- allow external services;
- offline GeoIP database location;
- logging level.

External services must be disabled by default.

---

# 5. Home Screen Flow

The home screen appears when no case is open.

## 5.1 Home Screen Content

Displays:

- New Case
- Open Case
- Recent Cases
- Import Existing Case
- Verify Case Package
- Documentation
- Settings
- Application Status

## 5.2 Recent Case Card

Each case card displays:

- case code;
- title;
- examiner;
- last opened time;
- status;
- evidence count;
- integrity status;
- locked or unlocked state.

Actions:

- Open
- Verify
- Archive
- Remove from Recent List

Removing from the recent list must not delete the case.

---

# 6. Create Case Flow

```text
Click New Case
    ↓
Enter Case Information
    ↓
Select Examiner
    ↓
Enter Authorisation Details
    ↓
Select Case Storage Location
    ↓
Configure Time Zone and Encryption
    ↓
Review Case Summary
    ↓
Create Case
    ↓
Initialise Folder Structure and case.db
    ↓
Write Initial Audit Event
    ↓
Open Case Dashboard
```

## 6.1 Case Information

Required fields:

- case code;
- case title;
- short description;
- organisation;
- examiner;
- display time zone.

Optional fields:

- reference number;
- department;
- client;
- jurisdiction;
- notes.

## 6.2 Authorisation

Required fields:

- authorisation type;
- scope;
- acknowledgement checkbox;
- acknowledged time.

Optional fields:

- authority name;
- court or internal reference;
- valid-from date;
- valid-until date;
- supporting document.

## 6.3 Case Location

The user selects a secure folder.

Validation:

- folder is writable;
- enough free space exists;
- folder is not inside the application installation directory;
- folder does not already contain an unrelated case;
- path length is supported;
- case code does not conflict.

## 6.4 Case Creation Result

On success:

- create case folder;
- create evidence subfolders;
- create `case.db`;
- create `case.toml`;
- initialise schema;
- write audit event;
- display dashboard.

On failure:

- roll back incomplete files;
- preserve diagnostic log;
- show actionable error;
- do not create a partially usable case.

---

# 7. Open Case Flow

```text
Click Open Case
    ↓
Select Case Folder or Case Package
    ↓
Read case.toml
    ↓
Verify case.db
    ↓
Verify Manifest
    ↓
Check Schema Version
    ↓
Run Migration if Required
    ↓
Check Case Lock
    ↓
Open Dashboard
```

## 7.1 Case Verification

Checks:

- case folder structure;
- database presence;
- database integrity;
- schema version;
- manifest hash;
- audit hash chain;
- missing evidence files;
- missing derived files;
- unexpected file changes.

## 7.2 Case Verification Outcomes

### Verified

Open normally.

### Warnings

Open with a warning banner.

Examples:

- derived thumbnail missing;
- report file missing;
- optional working copy removed;
- external GeoIP database unavailable.

### Critical Failure

Open in read-only recovery mode or reject opening.

Examples:

- `case.db` corrupt;
- evidence hash mismatch;
- manifest altered;
- migration failed;
- case folder inaccessible.

---

# 8. Main Case Navigation

Once a case is open, the sidebar contains:

1. Dashboard
2. Evidence
3. Chats
4. Contacts
5. Groups
6. Calls
7. Media
8. Timeline
9. Recovered
10. Live Capture
11. Search
12. Reports
13. Audit Log
14. Case Settings

The top bar contains:

- case code;
- case title;
- global search;
- active job indicator;
- integrity status;
- examiner profile;
- lock case;
- close case.

---

# 9. Dashboard Flow

## 9.1 Dashboard Purpose

The dashboard provides an overview of the current case.

Displays:

- evidence items;
- verified files;
- failed verifications;
- total messages;
- recovered records;
- contacts;
- groups;
- calls;
- media;
- date range;
- parser warnings;
- active jobs;
- recent examiner actions.

## 9.2 Dashboard Actions

- Import Evidence
- Continue Parsing
- Run Recovery
- Open Latest Chat
- Review Warnings
- Start Authorised Live Capture
- Generate Case Summary
- Verify Case Integrity

## 9.3 Empty Dashboard

When the case has no evidence:

```text
No evidence imported
    ↓
Show Import Evidence action
    ↓
Show supported source types
    ↓
Explain evidence-preservation workflow
```

---

# 10. Evidence Import Flow

```text
Open Evidence Page
    ↓
Click Import Evidence
    ↓
Choose Source Type
    ↓
Select File or Folder
    ↓
Review Source Information
    ↓
Select Acquisition Method
    ↓
Confirm Authorisation
    ↓
Copy and Hash Source
    ↓
Verify Copy
    ↓
Register Evidence
    ↓
Create Working Copy
    ↓
Offer Parsing
```

## 10.1 Source Types

The wizard may offer:

- WhatsApp chat export ZIP
- WhatsApp text export
- SQLite database
- SQLite database with WAL/SHM
- Media directory
- WhatsApp Desktop artefacts
- Previously decrypted backup
- Third-party forensic export
- PCAP/PCAPNG
- Generic evidence folder

## 10.2 Source Review

Displays:

- selected path;
- detected type;
- size;
- file count;
- timestamps;
- archive details;
- warnings;
- required free space.

## 10.3 Acquisition Method

Options:

- User-provided export
- Logical acquisition
- File-system acquisition
- Physical acquisition
- Desktop snapshot
- Third-party tool output
- Existing network capture
- Other authorised source

## 10.4 Import Progress

Progress stages:

```text
Inspecting source
Copying
Calculating SHA-256
Verifying destination
Registering evidence
Creating working copy
Finalising
```

Controls:

- Cancel
- View Details
- Minimise Progress

Cancellation must:

- stop safely;
- remove incomplete working copies;
- retain incomplete import logs;
- mark the evidence attempt as cancelled.

## 10.5 Duplicate Evidence

When the same SHA-256 already exists:

- show existing evidence reference;
- do not delete either source automatically;
- offer:
  - Link as duplicate reference
  - Import as separate evidence item
  - Cancel

---

# 11. Evidence Page Flow

Each evidence item displays:

- evidence code;
- title;
- source type;
- acquisition method;
- file count;
- total size;
- SHA-256 status;
- parser status;
- warnings;
- import time.

Actions:

- View Details
- Verify Hashes
- Create New Working Copy
- Parse
- Run Recovery
- Add Chain-of-Custody Event
- Add Note
- Exclude from Analysis
- Export Manifest

## 11.1 Evidence Detail Tabs

- Overview
- Files
- Hashes
- Acquisition
- Parsing
- Recovery
- Chain of Custody
- Notes
- Audit Events

---

# 12. Parser Flow

```text
Select Evidence
    ↓
Click Parse
    ↓
Inspect Source
    ↓
Detect File Type
    ↓
Fingerprint Schema
    ↓
Score Parser Adapters
    ↓
Run Compatibility Checks
    ↓
Show Planned Capabilities
    ↓
Start Parser
    ↓
Store Parsed Artefacts
    ↓
Build Search Index
    ↓
Build Timeline
    ↓
Show Parse Summary
```

## 12.1 Parser Capability Preview

Before parsing, show:

- selected adapter;
- adapter version;
- supported artefacts;
- unsupported artefacts;
- expected source tables;
- known limitations.

Example:

```text
Supported:
- Messages
- Contacts
- Groups
- Calls
- Media references

Partially supported:
- Reactions
- Edited messages

Unsupported:
- Poll votes
- Some business metadata
```

## 12.2 Parse Progress

Stages:

- source validation;
- schema inspection;
- contact parsing;
- group parsing;
- conversation parsing;
- message parsing;
- media linking;
- call parsing;
- validation;
- index creation;
- timeline generation.

## 12.3 Parse Completion

Display:

- parsed messages;
- contacts;
- groups;
- calls;
- media;
- warnings;
- unsupported records;
- duration;
- adapter version.

Actions:

- Open Chats
- Review Warnings
- Run Recovery
- Generate Parse Report
- Return to Evidence

## 12.4 Unsupported Schema

```text
Schema not recognised
    ↓
Store Fingerprint
    ↓
Show Unsupported Result
    ↓
Offer Structural Export
    ↓
Offer Generic Table Inspection
    ↓
Do Not Guess Field Meanings
```

---

# 13. Conditional Decryption Flow

This flow is available only for supported formats and lawful key material.

```text
Select Encrypted Backup
    ↓
Identify Format
    ↓
Show Required Inputs
    ↓
Enter or Select Lawful Key Material
    ↓
Validate Inputs
    ↓
Create Isolated Working Destination
    ↓
Run Adapter
    ↓
Verify Cryptographic Integrity
    ↓
Verify Output Structure
    ↓
Register Decrypted Working Copy
    ↓
Offer Parsing
```

## 13.1 Required Safeguards

- no brute-force option;
- no account-password harvesting;
- no token theft;
- no transmission of keys;
- secrets stored only in the OS vault;
- unsupported formats fail clearly;
- decrypted output remains in `working/`.

## 13.2 Failure Results

- Unsupported Format
- Missing Required Key
- Invalid Key Material
- Integrity Verification Failed
- Output Is Not a Supported Database
- Operation Cancelled

---

# 14. Chat Viewer Flow

```text
Open Chats
    ↓
Load Conversation List
    ↓
Select Conversation
    ↓
Load Paginated Messages
    ↓
Review Message Content and Provenance
    ↓
Filter, Search, Tag or Export
```

## 14.1 Conversation List

Displays:

- contact or group name;
- last message preview;
- message count;
- date range;
- recovered count;
- warning count.

Filters:

- direct chats;
- group chats;
- conversations with calls;
- conversations with media;
- conversations with recovered records;
- evidence source.

## 14.2 Message Bubble

Each message displays:

- sender;
- direction;
- text or media;
- source timestamp;
- display timestamp;
- delivery/read state when available;
- origin badge;
- confidence badge;
- deleted marker;
- edited marker;
- source warning.

## 14.3 Message Detail Panel

Displays:

- message code;
- source record ID;
- source table;
- source file;
- source hash;
- parser adapter;
- raw timestamp;
- normalised UTC;
- page or offset;
- quote relationship;
- reactions;
- media linkage;
- validation status;
- examiner notes.

Actions:

- Bookmark
- Add Tag
- Add Note
- Open Source Details
- Add to Report
- Export Selected Message
- Copy Text with Provenance

## 14.4 Chat Filters

- date range;
- keyword;
- regular expression;
- message type;
- sender;
- incoming/outgoing;
- media present;
- deleted marker;
- parsed/recovered;
- confidence.

---

# 15. Contacts Flow

```text
Open Contacts
    ↓
Load Paginated Contacts
    ↓
Search or Filter
    ↓
Select Contact
    ↓
Review Identity, Chats, Calls and Media
```

Contact detail tabs:

- Overview
- Aliases
- Conversations
- Calls
- Shared Media
- Timeline
- Source Records
- Notes

The UI must distinguish:

- parsed display name;
- saved contact name;
- account identifier;
- examiner-assigned alias;
- inferred identity.

---

# 16. Groups Flow

```text
Open Groups
    ↓
Select Group
    ↓
Review Group Metadata
    ↓
Review Participant History
    ↓
Open Group Chat or Timeline
```

Displays:

- subject;
- group identifier;
- creator;
- creation time;
- participant count;
- membership changes;
- messages;
- calls;
- recovered records.

---

# 17. Calls Flow

```text
Open Calls
    ↓
Load Historical Call Records
    ↓
Filter or Search
    ↓
Select Call
    ↓
Review Participants and Provenance
    ↓
Correlate with Timeline or Chat
```

## 17.1 Call List Fields

- call type;
- direction;
- participant;
- start time;
- duration;
- answered/missed;
- origin;
- confidence;
- source.

## 17.2 Call Detail

Displays:

- call code;
- participants;
- conversation;
- raw timestamp;
- UTC timestamp;
- duration;
- source table and row;
- evidence file;
- parser version;
- recovery status.

Actions:

- Jump to Conversation
- Open Timeline
- Add Tag
- Add Note
- Include in Report

---

# 18. Media Flow

```text
Open Media
    ↓
Load Media Grid or Table
    ↓
Filter by Type or Status
    ↓
Open Safe Preview
    ↓
Review Hash, Metadata and Linkage
```

Filters:

- image;
- video;
- audio;
- document;
- sticker;
- orphan;
- missing;
- duplicate;
- EXIF location present;
- recovered;
- evidence source.

## 18.1 Media Detail

Displays:

- file name;
- SHA-256;
- size;
- detected MIME type;
- dimensions;
- duration;
- source evidence;
- linked message;
- EXIF;
- correlation status;
- preview path.

Actions:

- Open Linked Message
- Compare Duplicates
- Review EXIF
- Add to Report
- Export Verified Copy
- Add Note

---

# 19. Deleted-Recovery Flow

```text
Select Evidence
    ↓
Open Recovery
    ↓
Choose Recovery Strategies
    ↓
Review Requirements
    ↓
Start Recovery Run
    ↓
Scan Working Copy
    ↓
Generate Candidates
    ↓
Validate and Score
    ↓
Deduplicate
    ↓
Examiner Review
    ↓
Accept, Reject or Leave Unresolved
```

## 19.1 Recovery Strategies

- WAL parsing
- Rollback-journal parsing
- Freelist scan
- Unallocated-page carving
- Orphan-media correlation
- Thumbnail correlation
- Desktop/mobile comparison

## 19.2 Recovery Progress

Displays:

- active strategy;
- pages or frames scanned;
- candidates discovered;
- high/medium/low confidence counts;
- elapsed time;
- warnings.

## 19.3 Recovery Candidate Review

Each candidate displays:

- candidate code;
- candidate type;
- parsed fields;
- raw fragment;
- source page;
- byte offset;
- WAL frame;
- confidence;
- validation checks;
- duplicate group.

Actions:

- Accept
- Reject
- Mark Unresolved
- Add Note
- View Hex Context
- Compare Candidate
- Add to Report

## 19.4 Accepted Candidate

When accepted:

- create stable recovered artefact;
- retain recovery candidate;
- link artefact to candidate;
- keep origin as `RECOVERED`;
- keep confidence label;
- write audit event;
- update search index and timeline.

---

# 20. Timeline Flow

```text
Open Timeline
    ↓
Select Sources
    ↓
Choose Date Range
    ↓
Load Paginated Events
    ↓
Filter and Correlate
    ↓
Bookmark or Export
```

Sources:

- messages;
- calls;
- media;
- group events;
- recovered records;
- network events;
- examiner notes;
- acquisition events.

Timeline controls:

- UTC/local time toggle;
- source toggles;
- confidence filter;
- evidence filter;
- conversation filter;
- zoom level;
- clock-skew indicator.

Selecting an event opens its source artefact.

---

# 21. Global Search Flow

```text
Enter Search Query
    ↓
Select Search Scope
    ↓
Apply Filters
    ↓
Execute Case-Local Search
    ↓
Display Grouped Results
    ↓
Open Artefact or Save Search
```

Search scopes:

- all artefacts;
- messages;
- contacts;
- groups;
- media;
- calls;
- recovered records;
- notes;
- URLs;
- hashes.

Result groups display:

- messages;
- contacts;
- media;
- calls;
- timeline events;
- examiner notes.

Actions:

- Open
- Bookmark
- Tag
- Add to Report
- Save Search
- Export Results

---

# 22. Live Call Network Metadata Flow

This module is optional, passive and disabled by default.

## 22.1 Entry Flow

```text
Open Live Capture
    ↓
Read Network-Capture Warning
    ↓
Select Authorisation Record
    ↓
Confirm Network Ownership or Authority
    ↓
Select Capture Interface
    ↓
Review Capture Configuration
    ↓
Start Passive Capture
```

## 22.2 Live Capture Flow

```text
Passive Capture Starts
    ↓
Monitor Visible UDP Flows
    ↓
Detect Probable STUN/TURN/ICE Events
    ↓
Extract Visible Endpoints
    ↓
Classify Peer, Relay, Carrier, VPN or Cloud
    ↓
Perform Offline GeoIP Lookup
    ↓
Update Live Endpoint Map
    ↓
Add Events to Live Timeline
    ↓
Save PCAP/PCAPNG
    ↓
Stop and Hash Capture
```

## 22.3 Live Capture Screen

Panels:

### Capture Status

- interface;
- capture duration;
- packets;
- bytes;
- active flows;
- possible call activity;
- capture file status.

### Endpoint Table

- IP address;
- port;
- classification;
- ISP;
- ASN;
- country;
- region;
- approximate city;
- first seen;
- last seen;
- confidence.

### Live Map

Markers may represent:

- probable peer;
- WhatsApp relay;
- TURN server;
- carrier gateway;
- VPN;
- cloud infrastructure;
- unknown endpoint.

### Event Feed

- new UDP flow;
- STUN binding request;
- mapped address observed;
- relay address observed;
- endpoint classification changed;
- endpoint no longer active.

## 22.4 Mandatory Disclaimer

The screen must always show:

> The displayed location is an approximate IP registration or network location. It may represent a relay, VPN, carrier gateway or cloud server instead of the call participant.

## 22.5 Stop Capture Flow

```text
Click Stop
    ↓
Stop Packet Collection
    ↓
Flush Capture File
    ↓
Calculate SHA-256
    ↓
Register Capture as Evidence
    ↓
Finalise Endpoint Records
    ↓
Generate Capture Summary
```

## 22.6 Live Capture Failure States

- no capture permission;
- interface unavailable;
- no visible traffic;
- packet driver missing;
- GeoIP database unavailable;
- suspected relay only;
- capture storage full;
- capture cancelled.

The application must never claim that a failed or relay-only capture located the caller.

---

# 23. Reporting Flow

```text
Open Reports
    ↓
Select Report Type
    ↓
Select Artefacts
    ↓
Configure Filters
    ↓
Choose Time Zone
    ↓
Configure Redaction
    ↓
Review Limitations
    ↓
Generate Preview
    ↓
Generate Final Output
    ↓
Create Manifest and Hash
    ↓
Verify Output
```

## 23.1 Report Types

- Case Summary
- Evidence Inventory
- Hash Verification
- Chat Transcript
- Contact Report
- Group Report
- Call Report
- Media Report
- Timeline Report
- Deleted-Recovery Report
- Network Metadata Report
- Chain-of-Custody Report
- Examiner Notes
- Full Evidence Package

## 23.2 Report Configuration

Options:

- date range;
- conversations;
- contacts;
- groups;
- calls;
- media;
- parsed/recovered;
- confidence;
- include source details;
- include raw timestamps;
- include thumbnails;
- include examiner notes;
- include limitations;
- redaction rules.

## 23.3 Report Preview

The preview must show:

- selected artefact count;
- excluded artefacts;
- redactions;
- warnings;
- estimated file size;
- report limitations;
- template version.

## 23.4 Report Completion

Displays:

- report code;
- output path;
- format;
- size;
- SHA-256;
- manifest path;
- signature status;
- generation time.

Actions:

- Open Report
- Verify Report
- Open Folder
- Export Copy
- Generate Redacted Variant

---

# 24. Redaction Flow

```text
Open Redaction Settings
    ↓
Choose Redaction Type
    ↓
Preview Matches
    ↓
Approve Rules
    ↓
Apply to Derived Report Data
    ↓
Generate Redacted Report
```

Redaction targets:

- phone numbers;
- contact names;
- profile photos;
- message text;
- media;
- IP addresses;
- locations;
- examiner notes.

Redaction must never modify original evidence or source artefacts.

---

# 25. Audit Log Flow

```text
Open Audit Log
    ↓
Verify Hash Chain
    ↓
Load Events
    ↓
Filter by Type, Examiner or Date
    ↓
Open Event Details
    ↓
Export Audit Report
```

Each event displays:

- sequence;
- time;
- examiner;
- component;
- action;
- object;
- previous hash;
- event hash;
- verification state.

A broken chain must show a critical warning.

---

# 26. Chain-of-Custody Flow

```text
Open Evidence
    ↓
Select Chain of Custody
    ↓
Add Event
    ↓
Enter Transfer or Action Details
    ↓
Confirm Examiner
    ↓
Save
    ↓
Write Audit Event
```

Event types may include:

- received;
- transferred;
- copied;
- verified;
- stored;
- examined;
- returned;
- archived.

---

# 27. Case Integrity Verification Flow

```text
Open Case Menu
    ↓
Select Verify Integrity
    ↓
Verify case.db
    ↓
Verify Foreign Keys
    ↓
Verify Evidence Hashes
    ↓
Verify Report Hashes
    ↓
Verify Manifest
    ↓
Verify Audit Chain
    ↓
Show Integrity Summary
```

Outcomes:

- Verified
- Verified with Warnings
- Critical Failure

A critical failure must not be hidden.

---

# 28. Case Lock Flow

```text
Click Lock
    ↓
Stop Sensitive Previews
    ↓
Pause or Continue Approved Jobs
    ↓
Clear Secrets from Memory
    ↓
Show Unlock Screen
```

Unlock methods:

- case password;
- operating-system authentication;
- examiner credential.

---

# 29. Close Case Flow

```text
Click Close Case
    ↓
Check Active Jobs
    ↓
Stop or Complete Jobs
    ↓
Flush Database Transactions
    ↓
Checkpoint case.db
    ↓
Verify Database
    ↓
Save Settings
    ↓
Clear Secrets
    ↓
Return to Home
```

If active capture is running, the application must require it to stop and finalise before closing.

---

# 30. Archive Case Flow

```text
Open Case Settings
    ↓
Select Archive
    ↓
Verify Case Integrity
    ↓
Select Included Working and Derived Files
    ↓
Create Archive Package
    ↓
Generate Manifest
    ↓
Hash Archive
    ↓
Optional Encryption
    ↓
Mark Case Archived
```

The archive flow must not delete the source case automatically.

---

# 31. Restore Case Flow

```text
Select Import Existing Case
    ↓
Choose Archive
    ↓
Verify Archive Hash
    ↓
Verify Manifest
    ↓
Select Restore Location
    ↓
Extract to Temporary Folder
    ↓
Verify case.db and Evidence
    ↓
Rename to Final Case Folder
    ↓
Open Restored Case
```

---

# 32. Settings Flow

## 32.1 Global Settings

Categories:

- General
- Appearance
- Security
- Storage
- Parsing
- Recovery
- Network
- Reporting
- Updates
- Diagnostics

## 32.2 Network Settings

- module enabled;
- offline GeoIP database;
- default capture filter;
- packet storage limit;
- automatic report disclaimer;
- external GeoIP disabled by default.

Active interception must remain unavailable.

## 32.3 Security Settings

- auto-lock;
- case encryption default;
- clipboard timeout;
- log redaction;
- external service permissions;
- plugin trust policy.

---

# 33. Background Job Flow

```text
User Starts Long Operation
    ↓
Create Job Record
    ↓
Queue Worker
    ↓
Show Progress
    ↓
Worker Reports Status
    ↓
User May Cancel
    ↓
Commit or Roll Back
    ↓
Show Completion Summary
```

Job types:

- import;
- hashing;
- parsing;
- recovery;
- media scan;
- search indexing;
- report generation;
- PCAP processing;
- integrity verification.

---

# 34. Notification Flow

Notification levels:

- Information
- Success
- Warning
- Error
- Critical

Examples:

### Success

- Evidence verified
- Parser completed
- Report generated
- Capture finalised

### Warning

- Unsupported fields found
- Missing media
- GeoIP unavailable
- Only relay endpoints detected

### Critical

- Hash mismatch
- Database corruption
- Audit-chain failure
- Case manifest modified

Critical notifications remain visible until acknowledged.

---

# 35. Error Recovery Flows

## 35.1 Evidence Copy Failure

```text
Copy Fails
    ↓
Stop Import
    ↓
Remove Incomplete Destination
    ↓
Retain Import Log
    ↓
Mark Attempt Failed
    ↓
Show Retry Guidance
```

## 35.2 Hash Mismatch

```text
Hash Verification Fails
    ↓
Mark Evidence HASH_MISMATCH
    ↓
Prevent Parsing
    ↓
Show Source and Destination Hash
    ↓
Offer Recopy
```

## 35.3 Parser Failure

```text
Parser Fails
    ↓
Roll Back Current Batch
    ↓
Preserve Completed Safe Batches if Partial Mode Allowed
    ↓
Store Parser Warning
    ↓
Show Failure Summary
    ↓
Offer Retry or Structural Inspection
```

## 35.4 Recovery Failure

```text
Recovery Strategy Fails
    ↓
Stop Failed Strategy
    ↓
Keep Results from Completed Independent Strategies
    ↓
Mark Run Partial
    ↓
Show Strategy-Level Errors
```

## 35.5 Report Failure

```text
Report Generation Fails
    ↓
Delete Incomplete Final Output
    ↓
Retain Temporary Diagnostic Data
    ↓
Mark Report Failed
    ↓
Show Error and Retry Options
```

## 35.6 Database Migration Failure

```text
Create Safety Backup
    ↓
Attempt Migration
    ↓
Migration Fails
    ↓
Roll Back Transaction
    ↓
Restore Backup if Necessary
    ↓
Open Previous Version Read-Only or Abort
```

---

# 36. Role-Based Flow

The first version may use a simple examiner model.

Potential roles:

### Lead Examiner

- manage case;
- import evidence;
- run parsers;
- accept recovered records;
- generate final reports;
- archive case.

### Examiner

- analyse evidence;
- add notes;
- tag artefacts;
- generate working reports.

### Reviewer

- read evidence and reports;
- verify audit trail;
- approve findings;
- cannot modify evidence.

### Student or Training Mode

- operates only on demonstration datasets;
- live network capture disabled unless supervised;
- clear training watermark;
- no production signing.

---

# 37. Keyboard and Accessibility Flow

The application must support:

- full keyboard navigation;
- visible focus;
- screen-reader names;
- scalable text;
- high-contrast mode;
- reduced motion;
- colour-independent status;
- accessible report HTML.

Common shortcuts:

| Shortcut | Action |
|---|---|
| Ctrl+N | New case |
| Ctrl+O | Open case |
| Ctrl+I | Import evidence |
| Ctrl+F | Search |
| Ctrl+Shift+F | Advanced search |
| Ctrl+R | Reports |
| Ctrl+L | Lock case |
| Ctrl+S | Save note or settings |
| Esc | Close dialog or cancel safe operation |

---

# 38. Mobile and Small-Screen Behaviour

The primary target is desktop, but the UI should remain usable on lower-resolution displays.

Rules:

- collapsible sidebar;
- scrollable dialogs;
- minimum 1366×768 target;
- responsive evidence cards;
- resizable detail panels;
- no hidden action buttons;
- tables support horizontal scrolling;
- progress dialogs remain accessible.

---

# 39. Empty States

Every major page must have a useful empty state.

Examples:

### No Messages

> No messages have been parsed for this case. Import and parse a supported export or database.

### No Recovered Records

> No recovery run has been completed, or no recoverable records were found.

### No Calls

> No call records were found in the selected evidence.

### No Live Endpoints

> No probable call-related endpoints are visible on the selected interface.

### No Reports

> No reports have been generated for this case.

---

# 40. Confirmation Rules

Require confirmation for:

- excluding evidence;
- deleting temporary working copies;
- cancelling capture;
- rejecting high-confidence recovery candidate;
- archiving case;
- restoring over an existing case;
- enabling external services;
- clearing decrypted temporary data.

Do not require repetitive confirmation for safe read-only navigation.

---

# 41. Audit Requirements by Flow

The following actions must generate audit events:

- case created;
- case opened;
- case locked or unlocked;
- authorisation added;
- evidence imported;
- evidence verified;
- hash mismatch;
- parser started and completed;
- recovery started and completed;
- recovered candidate accepted or rejected;
- live capture started and stopped;
- report generated;
- redaction applied;
- case integrity verified;
- case archived;
- case restored;
- schema migrated.

---

# 42. App Flow Acceptance Criteria

The application flow is complete when:

- a user can create and open a case;
- legal authorisation is recorded;
- evidence can be imported without modifying the source;
- evidence is hashed and verified;
- unsupported sources fail safely;
- parser capabilities are shown before execution;
- parsed artefacts retain provenance;
- recovery candidates require examiner review;
- chat, call, media and timeline views are paginated;
- live capture shows only authorised passive metadata;
- the live map displays an IP-location disclaimer;
- reports record filters, versions and hashes;
- audit events are created for critical actions;
- active jobs can be cancelled safely;
- closing a case finalises all transactions;
- case integrity can be verified at any time;
- Windows 10 and Windows 11 workflows pass user-acceptance testing.

---

# 43. Final Flow Summary

The central user journey is:

```text
Create authorised case
→ Import evidence
→ Hash and verify
→ Preserve original
→ Parse verified working copy
→ Review chats, calls and media
→ Run optional recovery
→ Review confidence and provenance
→ Analyse timeline
→ Optionally capture authorised live network metadata
→ Generate reproducible report
→ Verify and archive case
```

For live calls, the application may detect visible UDP/STUN/TURN endpoints and update an approximate map while the call is active. The endpoint may belong to a relay, VPN, carrier gateway or cloud provider. It must never be described as guaranteed caller location or exact route tracing.

The application flow is designed to make every important action:

- visible;
- reversible where practical;
- audited;
- evidence-safe;
- transparent about limitations.
