# WhatsApp Forensicator — UI/UX Specification

**Version:** 1.0  
**Application:** WhatsApp Forensicator / WhatsApp Forensic Toolkit  
**Primary platform:** Windows 10/11 desktop  
**UI framework:** PySide6  
**Visual direction:** Dark neon cyber-forensics command center  
**Reference:** Supplied ADB Extractor, Decryptor, Chat Viewer, Call Analysis, VoIP Analysis, Live Call Trace, and Export screenshots  

---

## 1. Design Objective

Create one consistent interface for the complete WhatsApp forensic application using the visual language shown in the reference screenshots:

- near-black backgrounds;
- dark green panels;
- thin neon-green borders;
- bright emerald active controls;
- red stop and destructive actions;
- technical monospace details;
- statistic cards;
- compact module tabs;
- WhatsApp-inspired chat rendering;
- live endpoint tables and maps;
- forensic status indicators.

The final interface must look advanced without becoming difficult to read. It must improve the reference design’s text size, spacing, contrast, accessibility, table usability, and error communication.

The application should feel like a professional digital-forensics workstation, not a fake hacking dashboard.

---

## 2. Design Principles

1. **Evidence first:** Case, evidence, hash, parser, and integrity states must always be visible.
2. **One visual system:** Every module must use the same shell, spacing, buttons, borders, badges, and typography.
3. **Honest capability:** Never use wording such as “caller located,” “encryption broken,” or “all deleted messages restored.”
4. **Readable density:** Dense data is acceptable, but text must remain legible and tables must support resizing and pagination.
5. **Fast navigation:** Major modules must be reachable in one click.
6. **Safe long operations:** Imports, hashing, parsing, recovery, reports, and captures must never freeze the UI.
7. **Accessible status:** Never communicate state using color alone.
8. **Offline-first:** External services must be clearly indicated and disabled by default.

---

## 3. Visual Identity

### 3.1 Brand Lockup

Primary title:

> **WHATSAPP FORENSICATOR**

Extended title:

> **WHATSAPP FORENSICATOR — BY CYBER OCTOPUS**

Subtitle:

> **COMPLETE FORENSICS SUITE**

Use the full title in the main header, splash screen, About dialog, and report cover. Use shorter page titles elsewhere.

### 3.2 Color Tokens

| Token | Hex | Usage |
|---|---|---|
| Root background | `#020703` | Main application |
| Deep background | `#030A05` | Header and title bar |
| Panel | `#061108` | Cards and page containers |
| Raised panel | `#09180D` | Dialogs and selected cards |
| Input/table background | `#020805` | Inputs and dense data |
| Hover surface | `#0B2413` | Hovered rows |
| Selected surface | `#0D3219` | Selected item |
| Primary green | `#00F56A` | Active controls |
| Bright green | `#1CFF7A` | Focus and key values |
| Medium green | `#00C853` | Primary buttons |
| Green border | `#087A38` | Panel borders |
| Muted green | `#46A568` | Secondary labels |
| Dim green | `#1D5C34` | Dividers and disabled borders |
| Information | `#18C8FF` | Informational state |
| Warning | `#FFB300` | Partial or caution |
| Danger | `#FF1744` | Stop, delete, failure |
| Recovered | `#B86CFF` | Recovered artefacts |
| Inferred | `#00C2D7` | Inferred artefacts |
| Manual | `#F5D547` | Examiner-created data |
| Primary text | `#EAF7EE` | Main readable text |
| Secondary text | `#A9C7B2` | Supporting text |
| Muted text | `#6E9278` | Metadata |
| Disabled text | `#42604A` | Disabled controls |

### 3.3 Typography

**Brand and page headings**

- Orbitron, Oxanium, Rajdhani SemiBold, or Segoe UI Semibold.

**Technical values**

- JetBrains Mono, IBM Plex Mono, Cascadia Mono, or Consolas.

**Normal UI text**

- Inter, Segoe UI, Noto Sans, or Arial.

| Role | Size |
|---|---:|
| Product title | 22–28 px |
| Page title | 20–24 px |
| Section title | 15–18 px |
| KPI value | 22–30 px |
| Body | 13–15 px |
| Table | 12–14 px |
| Metadata | 11–12 px |

Do not use text below 10 px.

### 3.4 Borders and Corners

- Standard panel border: 1 px green border.
- Active border: 1 px bright green.
- Warning border: 1 px amber.
- Critical border: 1 px red.
- Panel radius: 6 px.
- Button/input radius: 4 px.
- Badge radius: 12 px.
- Avoid thick permanent glow.

### 3.5 Spacing

Use a 4 px base grid:

`4, 8, 12, 16, 20, 24, 32, 40`

Main page padding: 12–16 px.  
Card padding: 12–16 px.  
Minimum button height: 36 px.  
Recommended table row height: 34–40 px.

---

## 4. Shared Application Shell

```text
┌─────────────────────────────────────────────────────────────┐
│ Window controls  Current module                 Case status │
├─────────────────────────────────────────────────────────────┤
│ Logo + Product title                     Examiner / DB / ADB│
├─────────────────────────────────────────────────────────────┤
│ Conversations | Messages | Recovered | Media | Calls | ... │
├─────────────────────────────────────────────────────────────┤
│ Horizontal module navigation                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                      Active page                            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Case ID | Integrity | Jobs | Time zone | Version | Offline │
└─────────────────────────────────────────────────────────────┘
```

### 4.1 Custom Title Bar

Follow the reference screenshot:

- dark title strip;
- three circular controls on the left;
- small logo;
- current module name.

Requirements:

- functional close, minimize, and maximize actions;
- accessible names and tooltips;
- title-bar dragging;
- double-click maximize/restore;
- optional native Windows title bar in accessibility mode.

### 4.2 Main Header

Left:

- circular logo;
- product title;
- subtitle;
- optional case classification badge.

Right:

- examiner name;
- role;
- ADB status;
- database/case status;
- lock case;
- account menu;
- close case/logout.

Do not show fake authentication states when no authentication system exists.

### 4.3 KPI Strip

Default KPI cards:

- Conversations
- Messages
- Recovered
- Media
- Calls
- Contacts

Each card contains:

- small icon;
- label;
- large value;
- optional warning;
- click navigation.

Display `—` when data has not been parsed. Do not show `0` for unavailable data.

### 4.4 Module Navigation

Recommended modules:

- Dashboard
- Cases
- Evidence
- ADB Extractor
- Decryptor
- Chat Viewer
- Contacts
- Groups
- Call Analysis
- Media
- Timeline
- Recovered
- VoIP Analysis
- Search
- Export
- Audit

The active module uses a filled bright-green tab. Inactive tabs use a dark background and muted green text.

For smaller screens:

- horizontal scrolling;
- a `More` menu;
- no clipped labels;
- keyboard navigation.

### 4.5 Status Bar

Show:

- case code;
- evidence integrity;
- active jobs;
- selected time zone;
- application version;
- offline/online state.

Example:

```text
CASE-2026-0001 • EVIDENCE VERIFIED • 2 JOBS RUNNING
ASIA/KOLKATA • VERSION 1.0.0 • OFFLINE MODE
```

---

## 5. Shared Components

### 5.1 Primary Button

- bright green fill;
- very dark text;
- leading icon;
- subtle hover glow;
- 36–40 px height.

Examples:

- Import Evidence
- Load Database
- Start Parse
- Generate Report

### 5.2 Secondary Button

- transparent dark background;
- green border;
- green text.

Examples:

- Browse
- Verify
- View Details
- Export Log

### 5.3 Destructive Button

- red fill;
- white text;
- confirmation when destructive.

Examples:

- Stop Capture
- Delete Temporary Copy
- Reject Candidate

### 5.4 Warning Button

- dark background;
- amber border and text.

Examples:

- Legacy Compatibility Check
- Continue with Partial Data

### 5.5 Input Fields

- dark field background;
- visible green border;
- bright focus ring;
- optional browse icon;
- validation text below;
- monospace for paths, hashes, IPs, ports, and source IDs.

### 5.6 Tables

All forensic tables must support:

- sticky headers;
- sorting;
- column resizing;
- horizontal scrolling;
- pagination or virtual scrolling;
- selected-row state;
- copy cell;
- context menu;
- tooltips for truncated values;
- keyboard row navigation.

Use `QTableView` and data models instead of `QTableWidget` for large datasets.

### 5.7 Badges

| Data/state | Badge |
|---|---|
| Parsed | Green outline |
| Recovered | Purple outline |
| Inferred | Cyan outline |
| Manual | Amber outline |
| Verified | Green fill |
| Partial | Amber fill |
| Failed | Red fill |
| Unsupported | Gray outline |
| Relay | Cyan-gray |
| Probable peer | Bright green outline |
| VPN/proxy | Purple outline |

### 5.8 Dialogs

Dialogs must:

- fit within 90% of the screen;
- scroll when required;
- keep action buttons visible;
- preserve keyboard focus;
- explain consequences;
- never hide the primary action below the viewport.

---

## 6. Splash and Unlock

### Splash Screen

- centered logo;
- title and subtitle;
- application version;
- short integrity message;
- small loading progress.

### Unlock Screen

Use only when local authentication or case locking is enabled.

Contains:

- examiner selector;
- password or OS authentication;
- case code;
- offline status;
- unlock action.

Preferred message:

> Case unlocked for Examiner Name

Avoid:

> Access granted to target.

---

## 7. Home and Cases

### 7.1 Home Screen

Actions:

- New Case
- Open Case
- Recent Cases
- Import Case Package
- Verify Case Package
- Documentation
- Settings

### 7.2 Case Card

Displays:

- case code;
- title;
- examiner;
- status;
- integrity;
- evidence count;
- last opened.

Actions:

- Open
- Verify
- Archive
- Remove from Recent

Removing from Recent must not delete the case.

### 7.3 New Case Wizard

Steps:

1. Case Details
2. Examiner
3. Authorisation
4. Storage
5. Security
6. Review

Use a visible step indicator and keep Back/Next buttons fixed at the bottom.

---

## 8. Dashboard

### Layout

```text
┌───────────────────────┬───────────────────────────────────┐
│ Evidence integrity    │ Activity timeline                 │
├───────────────────────┼───────────────────────────────────┤
│ Parser/recovery state │ Top contacts and conversations    │
├───────────────────────┼───────────────────────────────────┤
│ Recent evidence       │ Warnings and active jobs          │
└───────────────────────┴───────────────────────────────────┘
```

Cards:

- Evidence Integrity
- Case Statistics
- Parsing Progress
- Recovery Summary
- Recent Activity
- Warnings
- Top Contacts
- Data Date Range

Primary actions:

- Import Evidence
- Verify Case
- Continue Parsing
- Run Recovery
- Generate Summary
- Start Passive Capture

---

## 9. Evidence Page

### Layout

Left:

- evidence list.

Right:

- selected evidence details.

Tabs:

- Overview
- Files
- Hashes
- Acquisition
- Parsing
- Recovery
- Chain of Custody
- Notes
- Audit

### Evidence Card

Show:

- evidence code;
- source type;
- size;
- SHA-256 status;
- parser state;
- warning count;
- import time.

### Integrity Banner

States:

- Verified
- Verified with Warnings
- Hash Mismatch
- Missing Files
- Unsupported
- Not Verified

A hash mismatch uses a red banner and disables parsing.

---

## 10. ADB Extractor

Use the supplied two-column design but make its limitations clear.

```text
┌──────────────────────────┬──────────────────────────────┐
│ USB / TCP-IP Connection  │ Authorised Actions           │
├──────────────────────────┼──────────────────────────────┤
│ Device Information       │ Acquisition Log              │
└──────────────────────────┴──────────────────────────────┘
```

### Connection Area

Tabs:

- USB
- TCP/IP
- Device Information

USB controls:

- device selector;
- refresh;
- connect;
- authorisation state.

TCP/IP controls:

- IP;
- port;
- pairing code when required;
- connect.

### Authorised Actions

Supported:

- Import User Export
- Copy Accessible Media
- Import Forensic Tool Output
- Record Device Metadata

Conditional:

- Legacy ADB Backup Compatibility Check
- Existing Backup Import

Do not show a universal “non-root extract private database” action.

---

## 11. Decryptor

Use the supplied left/right layout.

### Left: Decrypt Backup

Fields:

- encrypted backup;
- detected format;
- lawful key material;
- key source;
- adapter;
- output working folder.

Actions:

- Validate Inputs
- Start Decryption
- View Adapter Details

### Right: Load Existing Database

Fields:

- message database;
- contacts database;
- media folder;
- WAL file;
- SHM file.

Action:

- Load and Validate Database

### Safety Banner

> Decryption is available only for supported formats when lawful key material is provided. The application does not crack passwords or bypass account security.

Progress:

- Identify Format
- Validate Input
- Decrypt
- Verify Integrity
- Validate SQLite
- Register Working Copy

---

## 12. Chat Viewer

Use a dark forensic outer shell with a light inner chat surface, similar to the supplied screenshot.

```text
┌──────────────┬──────────────────────────────────────────┐
│ Conversations│ Chat header                              │
│              ├──────────────────────────────────────────┤
│              │ Message timeline                         │
│              │                                          │
│              ├──────────────────────────────────────────┤
│              │ Search / examiner-note bar               │
└──────────────┴──────────────────────────────────────────┘
```

### Conversation Sidebar

- search;
- All / Unread / Groups;
- source filter;
- recovered-only filter;
- paginated conversation list.

Each row includes:

- avatar placeholder;
- name or identifier;
- date;
- preview;
- unread count;
- recovered count;
- warning badge.

### Chat Header

- contact/group;
- message count;
- evidence source;
- date range;
- Select Date;
- Search;
- Export;
- Call History;
- Provenance.

### Message Bubbles

- Sent: light green, right aligned.
- Received: white, left aligned.
- Recovered: purple border and badge.
- Inferred: cyan border and badge.
- System event: centered chip.

Each message can expose:

- raw timestamp;
- UTC timestamp;
- source file;
- parser;
- confidence;
- source record;
- evidence hash.

### Bottom Bar

Do not provide a message sender.

Replace the visual composer with:

- Search within conversation
- Add Examiner Note
- Add Bookmark
- Add Tag

Placeholder:

> Add examiner note to this conversation…

---

## 13. Contacts and Groups

### Contacts

Layout:

- searchable contact list;
- contact details;
- provenance panel.

Tabs:

- Overview
- Conversations
- Calls
- Shared Media
- Aliases
- Timeline
- Provenance
- Notes

Clearly distinguish:

- parsed name;
- saved-contact name;
- WhatsApp identifier;
- examiner alias;
- inferred identity.

### Groups

Group list columns:

- Group
- Identifier
- Participants
- Messages
- Calls
- Recovered
- Date Range

Group details:

- subject;
- description;
- creator;
- creation time;
- participant history;
- membership changes;
- chat;
- calls;
- media.

---

## 14. Call Analysis

Follow the supplied layout.

### KPI Cards

- Total
- Incoming
- Outgoing
- Missed
- Video
- Total Duration

### Filters

- All
- Incoming
- Outgoing
- Missed
- Video
- Voice
- Recovered

### Table Columns

- Direction
- Contact / Identifier
- Peer
- Duration
- Timestamp
- Call Type
- Origin
- Confidence
- Source

Use distinct icons for incoming, outgoing, missed, voice, and video.

### Detail Drawer

- call code;
- participants;
- start/end;
- duration;
- source table;
- source record;
- parser;
- linked chat;
- timeline;
- notes.

---

## 15. Media

### KPI Cards

- Total
- Images
- Videos
- Audio
- Documents
- Orphans
- Missing

### Views

- Grid
- Table
- Duplicate Groups
- Orphan Review

### Media Card

- thumbnail;
- filename;
- type;
- hash state;
- linked/recovered/orphan badge;
- timestamp.

### Detail Drawer

- safe preview;
- SHA-256;
- MIME;
- size;
- dimensions;
- duration;
- EXIF;
- GPS metadata;
- linked message;
- correlation score;
- verified export action.

Original media must never be changed.

---

## 16. Timeline

Controls:

- date range;
- event type;
- conversation;
- contact;
- evidence;
- origin;
- confidence;
- UTC/local toggle;
- clock-skew indicator.

Event colors:

| Event | Color |
|---|---|
| Message | Green |
| Call | Pink/red |
| Media | Amber |
| Recovered | Purple |
| Network | Cyan |
| Examiner note | Yellow |
| Acquisition | Gray-green |

Selecting an event opens its source artefact and provenance.

---

## 17. Recovered Artefacts

### KPI Cards

- Total Candidates
- High Confidence
- Medium Confidence
- Low Confidence
- Accepted
- Rejected
- Unresolved

### Layout

- left filters;
- center candidate table;
- right detail panel.

Candidate columns:

- Candidate
- Type
- Strategy
- Page
- Offset
- Confidence
- Review State
- Source

Detail tabs:

- Parsed Fields
- Raw Fragment
- Validation Checks
- Provenance
- Duplicate Comparison
- Notes

Actions:

- Accept
- Reject
- Leave Unresolved
- Add Note
- Add to Report

---

## 18. VoIP Analysis and Live Endpoint Map

Page title:

> **VOIP ANALYSIS — LIVE NETWORK METADATA**

Do not use “exact caller tracker.”

### Action Bar

- Start Passive Capture
- Stop Capture
- Import PCAP
- Export Log
- Capture Status
- Authorisation Status

Stop uses red.

### Layout

```text
┌────────────────────────────┬─────────────────────────────┐
│ Captured endpoints         │ Approximate endpoint map    │
├────────────────────────────┼─────────────────────────────┤
│ Live event feed            │ Selected endpoint details   │
└────────────────────────────┴─────────────────────────────┘
```

### Endpoint Table

Columns:

- First Seen
- Last Seen
- Source
- Destination
- Ports
- Protocol
- ISP
- ASN
- Classification
- Approximate Region
- Confidence

### Map Markers

| Classification | Marker |
|---|---|
| Probable peer | Green |
| WhatsApp relay | Cyan |
| TURN server | Blue |
| VPN/proxy | Purple |
| Carrier gateway | Amber |
| Cloud infrastructure | Gray |
| Unknown | White |

### Permanent Warning

> **Approximate network location only. The endpoint may be a relay, VPN, carrier gateway, or cloud server and may not represent the participant’s physical location.**

When traffic is detected, show:

> Probable call-related network activity detected

Never show:

> Caller located

### No-Traffic State

> No probable WhatsApp call-related UDP/STUN/TURN activity is visible on the selected interface.

Actions:

- Change Interface
- Import PCAP
- View Capture Guide

---

## 19. Search

Large primary search field.

Supported input:

- keyword;
- exact phrase;
- regular expression;
- phone number;
- URL;
- hash;
- source record ID.

Scopes:

- All
- Messages
- Contacts
- Groups
- Calls
- Media
- Recovered
- Notes
- Network

Each result shows:

- matched text;
- timestamp;
- origin badge;
- confidence;
- evidence source;
- open action.

---

## 20. Export and Reports

Use the reference screenshot’s centered export style, expanded into grouped report cards.

### Categories

**Conversation**

- Chat PDF
- Chat HTML
- Chat CSV
- Chat JSON

**Forensic**

- Case Summary
- Evidence Inventory
- Hash Verification
- Recovery Report
- Call Report
- Media Report
- Timeline Report
- Network Metadata
- Chain of Custody

**Packages**

- Selected Evidence ZIP
- Complete Case Package
- Redacted Review Package

### Report Wizard

1. Report Type
2. Scope
3. Filters
4. Redaction
5. Branding
6. Preview
7. Generate

Completion view:

- report code;
- file path;
- SHA-256;
- manifest;
- signature;
- generation time.

---

## 21. Audit Log

### KPI Cards

- Total Events
- Verified Chain
- Warnings
- Critical Events
- Last Verification

### Table

- Sequence
- Time
- Examiner
- Action
- Component
- Object
- Verification
- Hash

### Chain View

```text
Event 001 ✓
    │
Event 002 ✓
    │
Event 003 ✕
```

A broken chain uses a critical red banner.

---

## 22. Settings

Sections:

- General
- Appearance
- Examiner
- Storage
- Security
- Parsing
- Recovery
- Network
- Reports
- Plugins
- Diagnostics

Appearance options:

- Dark Neon
- High Contrast
- Reduced Glow
- Light Chat Surface
- Font Size
- Density
- Reduced Motion
- Native Title Bar

Network options:

- Enable Passive Capture
- Offline GeoIP Database
- Default Interface
- Capture Storage Limit
- External Lookup Permission
- Mandatory Disclaimer

Do not include active interception settings.

---

## 23. Loading and Background Jobs

Long operations must use a job system.

Progress dialog:

- operation;
- current stage;
- percentage;
- processed count;
- elapsed time;
- cancel;
- details.

Background Job Center:

- Active
- Queued
- Completed
- Failed
- Retry
- Cancel

Use skeleton rows for chat, tables, and media while loading.

---

## 24. Notifications and Errors

### Toasts

- Success
- Information
- Warning
- Error

Critical errors remain until dismissed.

### Critical Banners

Use for:

- hash mismatch;
- database corruption;
- audit-chain failure;
- invalid authorisation;
- unsupported schema risk.

### Error Panel

Must show:

- error code;
- readable explanation;
- evidence reference;
- recommended action;
- retry;
- technical details;
- copy diagnostic summary.

Never silently discard records.

---

## 25. Accessibility

The UI must support:

- keyboard navigation;
- logical tab order;
- visible focus;
- screen-reader names;
- high contrast;
- reduced motion;
- scalable text;
- color-independent status;
- scrollable dialogs;
- minimum 36 × 36 px targets.

### Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+N | New Case |
| Ctrl+O | Open Case |
| Ctrl+I | Import Evidence |
| Ctrl+F | Search |
| Ctrl+Shift+F | Advanced Search |
| Ctrl+R | Reports |
| Ctrl+L | Lock Case |
| Ctrl+Shift+V | Verify Case |
| Esc | Close dialog or cancel safe action |

---

## 26. Responsive Desktop Layout

Primary target:

- 1920 × 1080

Minimum:

- 1366 × 768

Behavior:

- KPI cards wrap;
- navigation scrolls;
- side panels collapse;
- detail panels become drawers;
- map and endpoint table stack below 1450 px;
- dialogs remain scrollable;
- actions remain visible.

Test at:

- 100%
- 125%
- 150%
- 175% Windows scaling.

---

## 27. Motion

Use:

- 120–180 ms hover;
- 180–220 ms drawer transitions;
- gentle pulse for active capture;
- smooth progress.

Do not use:

- flashing text;
- permanent scan lines;
- constant neon flickering;
- distracting animated backgrounds.

Reduced Motion disables pulsing, glow animation, and sliding.

---

## 28. PySide6 Implementation

Recommended widgets:

- `QMainWindow`
- `QStackedWidget`
- `QTabBar`
- `QTableView`
- `QTreeView`
- `QListView`
- `QSplitter`
- `QDockWidget`
- `QWebEngineView`
- `QSortFilterProxyModel`
- custom `QStyledItemDelegate`

Use:

```text
ui/
├── themes/
│   ├── tokens.py
│   ├── dark_neon.qss
│   ├── high_contrast.qss
│   └── light_chat.qss
├── components/
├── pages/
├── dialogs/
└── resources/
```

Rules:

- central QSS;
- no duplicated inline styles;
- model/view tables;
- paginated database queries;
- background workers;
- local-only WebEngine resources by default;
- strict Content Security Policy;
- sanitised chat and evidence content;
- JavaScript disabled unless required.

---

## 29. Required Screen Checklist

- [ ] Splash
- [ ] Legal Notice
- [ ] Examiner Profile
- [ ] Unlock
- [ ] Home
- [ ] Dashboard
- [ ] Cases
- [ ] New Case Wizard
- [ ] Evidence
- [ ] Import Wizard
- [ ] ADB Extractor
- [ ] Decryptor
- [ ] Parser Progress
- [ ] Chat Viewer
- [ ] Contacts
- [ ] Groups
- [ ] Call Analysis
- [ ] Media
- [ ] Timeline
- [ ] Recovered
- [ ] VoIP Analysis
- [ ] Live Endpoint Map
- [ ] Search
- [ ] Reports
- [ ] Report Wizard
- [ ] Audit Log
- [ ] Chain of Custody
- [ ] Settings
- [ ] Background Jobs
- [ ] Integrity Verification
- [ ] Archive and Restore
- [ ] Error and Empty States
- [ ] About

---

## 30. Acceptance Criteria

The UI is complete when:

1. Every module uses the same design system.
2. Critical text is readable at 1366 × 768.
3. Dialog actions remain visible.
4. Large tables remain responsive.
5. Parsed, recovered, inferred, and manual artefacts are visually distinct.
6. Evidence integrity is visible throughout the application.
7. Live mapping always displays the limitation warning.
8. The chat screen cannot send WhatsApp messages.
9. Long operations never block the UI.
10. Keyboard navigation works.
11. High Contrast and Reduced Motion are available.
12. Unsupported evidence never shows fabricated results.
13. Red is reserved for failure, stop, and destructive actions.
14. Reports preserve the brand while remaining readable.
15. Windows 10 and Windows 11 visual tests pass.
16. Layout works at 100–175% scaling.

---

## 31. Final Design Direction

Preserve the reference interface’s strongest visual qualities:

- black forensic shell;
- neon-green identity;
- technical statistics;
- compact tabs;
- bordered dark panels;
- bright active controls;
- red stop controls;
- light WhatsApp-inspired chat surface;
- endpoint table and map;
- centered export options.

Improve:

- text size;
- spacing;
- hierarchy;
- contrast;
- accessibility;
- table behavior;
- error states;
- responsive layouts;
- forensic wording;
- consistency.

The final product should look like:

> **A polished cyber-forensics command center that is visually advanced, technically honest, evidence-safe, and comfortable for long professional investigations.**
