# AGENTS.md — Project Memory & Working Guide

# Instruction Priority

This file contains permanent repository-level instructions.

Before every task:

1. Read this file completely.
2. Read the relevant project documentation.
3. Inspect the existing implementation.
4. Preserve completed work and passing tests.
5. Never assume a feature is missing without checking the code.
6. Never claim that a feature works without testing it.

## 1. Project Overview

- **Name:** WhatsApp Forensic Toolkit (WHATSAPP FORENSICATOR)
- **Purpose:** Offline-first desktop forensic application for acquiring, preserving, parsing, analysing and reporting WhatsApp-related digital evidence through lawful and authorised workflows.
- **Target users:** Authorised forensic examiners, cybersecurity analysts, incident responders, supervised students.
- **Current status:** Alpha (v1.0.0a1) — core case/evidence/parse/audit/report loop works. ADB extraction and backup decryption are placeholders.
- **Main features:** Create/open forensic cases, import evidence (text exports, ZIP archives, SQLite databases), hash-verify evidence, parse artefacts (messages, contacts, groups, calls, media), hash-chained audit trail, multi-scope search, HTML report generation, token-built dark theme, recovery candidate review, timeline viewer.

## 2. Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ (target), currently runs on Python 3.14 |
| UI Framework | PySide6 (Qt for Python) >=6.6 |
| Database | SQLite 3 (WAL mode, foreign keys, one `case.db` per case) |
| Parsers | Native Python (TextExportParser, ZipExportParser, WhatsAppSQLiteAdapter) |
| Templates | Jinja2 >=3.1 (for reports) |
| Image processing | Pillow >=10.0 |
| File type detection | python-magic >=0.4 |
| Data validation | Pydantic >=2.0 |
| Cryptography | cryptography >=41.0 |
| Config serialization | tomllib (stdlib) + tomli_w |
| Testing | pytest >=7.4, pytest-qt >=4.2 |
| Packaging | setuptools (build), pyproject.toml |
| Optional deps | weasyprint/reportlab (PDF), scapy (network), maxminddb (GeoIP), yara-python, ExifRead |
| Linting/formatting | ruff, black, mypy (strict mode) |

## 3. Project Architecture

### Directory Structure

```
whatsapp-forensic-toolkit/
├── pyproject.toml
├── AGENTS.md                          # THIS FILE
├── architecture.md                    # Detailed architecture docs
├── appflow.md                         # Application flow docs
├── database.md                        # Database design docs
├── ui-ux.md                           # UI/UX design docs
├── whatsapp_forensic_toolkit_corrected_merged_plan.md
├── docs/                              # (empty, future doc storage)
├── packaging/                         # (empty, future packaging scripts)
├── scripts/                           # (empty, future build scripts)
├── src/
│   └── wft/
│       ├── main.py                    # App entry point, QApplication init, legal notice
│       ├── bootstrap.py               # Container (DI) — instantiates all services
│       ├── application/
│       │   ├── services/
│       │   │   ├── __init__.py        # Exports all services
│       │   │   ├── case_service.py    # CaseService + CaseRepository
│       │   │   ├── evidence_service.py # EvidenceService + EvidenceRepository
│       │   │   ├── audit_service.py   # AuditService (hash-chained events)
│       │   │   ├── parse_service.py   # ParseService (parser orchestration)
│       │   │   ├── case_context.py    # ActiveCaseContext (QObject, case state signal)
│       │   │   ├── statistics_service.py  # KPI aggregation SQL queries
│       │   │   ├── search_service.py  # Multi-scope search (7 scopes)
│       │   │   └── recovery_service.py # Recovery candidate review
│       │   ├── dto/                   # (empty)
│       │   ├── commands/              # (empty)
│       │   └── queries/               # (empty)
│       ├── domain/
│       │   ├── enums.py              # CaseStatus, EvidenceState, ConfidenceLevel, etc.
│       │   ├── models/
│       │   │   ├── case.py           # Case, Examiner, Authorisation
│       │   │   ├── evidence.py       # EvidenceItem, EvidenceFile, EvidenceHash, WorkingCopy
│       │   │   └── artefacts.py      # Contact, Group, Conversation, Message, Call, MediaItem
│       │   ├── provenance/provenance.py
│       │   └── policies/             # (empty)
│       ├── parsers/
│       │   ├── contracts/interfaces.py  # ParserAdapter, ParseContext, InspectionResult protocols
│       │   ├── exports/text_export_parser.py    # WhatsApp text export parser
│       │   ├── exports/zip_export_parser.py     # ZIP export parser
│       │   ├── adapters/whatsapp_sqlite_adapter.py  # SQLite adapter
│       │   ├── sqlite/schema_fingerprinter.py   # Schema detection + fingerprinting
│       │   └── sqlite/sqlite_parser.py          # Generic SQLite parser
│       ├── infrastructure/
│       │   ├── database/
│       │   │   ├── schema.py         # All DDL (54 statements), indexes, FTS5
│       │   │   ├── connection.py     # DatabaseConnection (PRAGMAs, transaction, Repository protocol)
│       │   │   ├── migrations.py     # Migrator (initialize, backup, verify)
│       │   │   ├── repository.py     # BaseRepository (generic CRUD)
│       │   │   ├── artefact_repositories.py  # 10 specific repository classes
│       │   │   └── uow.py            # UnitOfWork (context manager)
│       │   ├── hashing/hashing_service.py  # SHA256, SHA512, MD5 with copy
│       │   ├── filesystem/file_store.py    # FileStore (copy, read-only, ZIP extract)
│       │   ├── logging/logging_service.py  # JSON-structured logging
│       │   └── settings/settings.py  # AppSettings (TOML-based config)
│       ├── ui/
│       │   ├── main_window.py        # MainWindow — header, KPI strip, nav tabs, 18 pages
│       │   ├── components/           # NeonButton, StatusBadge, StatisticCard, PageHeader, EvidenceBanner, EmptyState, ErrorPanel, ProgressOverlay
│       │   ├── pages/                # 18 page widgets (see below)
│       │   ├── theme/                # DesignTokens, qss_builder, ThemeManager, layout/style helpers
│       │   ├── workers/              # CancellationToken, BackgroundWorker, WorkerSignals, ParseEvidenceWorker, BatchImportWorker
│       │   ├── widgets/              # (empty)
│       │   ├── dialogs/              # (empty)
│       │   ├── models/               # (empty)
│       │   └── resources/            # (empty)
│       ├── reports/
│       │   ├── html_report.py        # HtmlReportGenerator (simple case summary)
│       │   ├── templates/            # (empty)
│       │   ├── generators/           # (empty)
│       │   ├── redaction/            # (empty)
│       │   └── manifests/            # (empty)
│       ├── acquisition/              # (empty — importers, android_assistant, desktop)
│       ├── recovery/                 # (empty — wal, journal, carving, scoring, correlation)
│       ├── analysis/                 # (empty — timeline, media, links)
│       └── network/                  # (empty — protocols, pcap, geoip, passive_capture)
└── tests/
    ├── unit/
    │   ├── test_hashing.py           # HashingService (5 tests)
    │   ├── test_artefact_repositories.py  # Contact, Message, ParserRun, Media repos (12 tests)
    │   ├── test_audit.py             # AuditService chain verification (2 tests)
    │   ├── test_confidence_scorer.py # ConfidenceScorer (5 tests)
    │   ├── test_schema_fingerprinter.py  # Schema detection + registry (8 tests)
    │   ├── test_text_export_parser.py    # TextExportParser (4 tests)
    │   ├── test_structured_parser.py     # Structured parse output, SQLite adapter, ZIP (8 tests)
    │   └── test_ui_components.py     # UI components, nav (22 tests)
    └── integration/                  # (empty)
```

### 18 UI Pages

| Key | Class | Purpose | Backend Connected |
|-----|-------|---------|-------------------|
| (home) | HomePage | Recent cases, open/new | CaseService |
| cases | CreateCasePage | Create new case | CaseService |
| dashboard | DashboardPage | KPI overview | StatisticsService |
| evidence | EvidencePage | Import/parse evidence | EvidenceService, ParseService |
| chats | ChatsPage | View conversations | Conversation/Message repos |
| contacts | ContactsPage | Contact list | ContactRepository |
| groups | GroupsPage | Group list | GroupRepository |
| calls | CallsPage | Call records | CallRepository |
| media | MediaPage | Media items | MediaRepository |
| timeline | TimelinePage | Timeline events | TimelineEventRepository |
| search | SearchPage | Multi-scope search | SearchService |
| reports | ReportsPage | Generate reports | HtmlReportGenerator, ReportRunRepository |
| audit | AuditPage | Audit trail | AuditEventRepository, AuditService |
| settings | SettingsPage | App settings | AppSettings (TOML) |
| adb | ADBExtractorPage | ADB extraction | *placeholder* |
| decrypt | DecryptorPage | Backup decryption | *placeholder* |
| recovered | RecoveredPage | Recovered candidates | RecoveryService |
| voip | VoIPPage | VoIP endpoints | Raw SQL on network_endpoints |

### Data Flow

```
User clicks nav tab
  → MainWindow.navigate_to(key)
    → page = _page_map[key]
      → page.on_activated()  # each page reads from its service/repo
      → page calls service.method(db=ctx.get_db(), case_id=ctx.case_id)
        → service calls repository method
        → repository runs SQL via DatabaseConnection
```

Service objects are long-lived (in Container). Repositories are instantiated per-call: `RepoClass(ctx.get_db())`.

All pages receive `ctx: ActiveCaseContext` via constructor. `ctx.get_db()` returns a `DatabaseConnection`, `ctx.case_id` returns `int`, `ctx.case_path` returns `Path`.

### Key Entry Points

- `src/wft/main.py` `main()` — application start
- `src/wft/bootstrap.py` `Container.__init__()` — service wiring
- `src/wft/ui/main_window.py` `MainWindow.__init__()` — UI construction
- `src/wft/application/services/parse_service.py` `parse_evidence()` — main parse orchestration
- `src/wft/infrastructure/database/migrations.py` `Migrator.initialize()` — schema setup

## 4. Coding Standards

- **Naming:** snake_case for modules, functions, methods, variables. PascalCase for classes. UPPER_CASE for constants.
- **Type hints:** Required on all function signatures (mypy strict mode).
- **Line length:** 100 characters (ruff + black config).
- **Target Python:** 3.11+ (though currently tested on 3.14).
- **Imports:** stdlib first, then third-party, then local. Absolute imports preferred (`from wft.xxx `).
- **Repositories:** All extend `BaseRepository`. Instantiated with `repo = RepoClass(db)` where `db` is a `DatabaseConnection`.
- **Services:** Receive dependencies via constructor (manual DI through Container).
- **Error handling:** Services raise exceptions; UI pages catch them in `on_activated()` and show `ErrorPanel`. Worker callbacks (`on_error`, `on_complete`) propagate results.
- **Logging:** Use `self._log` (LoggingService) with JSON formatting. Redacted keys: password, secret, key, token, authorization.
- **Validation:** Pydantic models in domain layer for data validation.
- **Datetime format:** ISO 8601 UTC with 'Z' suffix: `datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")`.
- **DAO pattern:** Domain dataclass objects are used for typed representation; actual persistence is via dict-based repository methods.
- **Page pattern:** Each page class has `on_activated()` method called by MainWindow on navigation — this is where data refreshing happens.

## 5. Database Rules

### Schema (SCHEMA_VERSION = 1)

54 DDL statements covering 40+ tables. Key tables:
- `cases` — case metadata (status: OPEN/LOCKED/ARCHIVED/CLOSED)
- `examiners` — per-case examiners
- `evidence_items`, `evidence_files`, `evidence_hashes` — evidence inventory
- `contacts`, `groups`, `group_participants` — contacts
- `conversations`, `messages`, `message_revisions`, `message_reactions`, `message_quotes`, `message_mentions` — chat data
- `calls`, `call_participants` — call records
- `media_items`, `media_metadata`, `exif_records`, `media_correlations` — media
- `system_events`, `locations`, `shared_contacts`, `links` — additional artefacts
- `parser_runs`, `parser_warnings`, `schema_mappings` — parsing provenance
- `recovery_runs`, `recovery_candidates`, `recovered_records` — recovery
- `timeline_events` — cross-artefact timeline
- `audit_events` — hash-chained audit trail (SHA256 linked list)
- `report_runs`, `report_files`, `redaction_rules` — reports
- `tags`, `artefact_tags`, `bookmarks`, `examiner_notes`, `saved_searches` — annotations
- `network_capture_sessions`, `network_flows`, `network_endpoints`, `stun_turn_events` — network
- `schema_migrations` — migration tracking
- `message_search` — FTS5 virtual table

### Migrations

- `Migrator.initialize()` runs on case creation/open.
- `PRAGMA user_version` tracks current schema version.
- Schema is applied linearly (version 0 → current). No incremental migration functions exist yet.
- Backup is created at `case.db.bak` before migration.

### Connection PRAGMAs

```sql
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
PRAGMA temp_store = MEMORY;
PRAGMA trusted_schema = OFF;
PRAGMA journal_mode = WAL;       -- writable (case.db)
PRAGMA synchronous = FULL;       -- writable (case.db)
```

### File storage

Files stored in case directory: `originals/`, `working/`, `derived/`, `reports/`, `exports/`, `logs/`, `manifests/`, `notes/`.

### Rules that must never be violated

1. **Original evidence is never modified** — original files are stored read-only.
2. **Every artefact must retain provenance** — `origin` and `confidence_level` columns required.
3. **Parsed, recovered, and inferred data remain distinguishable** — by `origin` column values.
4. **Raw source values preserved** alongside normalised UTC values.
5. **Case databases are portable and independently verifiable.**
6. **`ON DELETE RESTRICT`** on most case-level foreign keys prevents orphaned records.
7. **Evidence files referenced by hash and immutable identifiers.**

## 6. UI/UX Rules

### Design System

- **Theme:** Dark forensic (default, token-built). High Contrast is spec-deferred, not implemented.
- **Primary color:** `#00C853` (green). Background: `#020703`. Text: `#EAF7EE`.
- **Color tokens** defined in `wft/ui/theme/tokens.py` (frozen dataclass `DesignTokens`).
- **QSS** is generated from tokens by `wft/ui/theme/qss_builder.py` (`build_full_qss`); there are NO static .qss files.
- **ThemeManager** (`wft/ui/theme/theme_manager.py`) applies generated QSS and swaps tokens. Signal `theme_changed(str)`. Applied at startup by `Container.__init__` via `load_saved_theme()`.
- **Window:** 1366x768 default, 1024x600 minimum.
- **App title:** "WHATSAPP FORENSICATOR" (all caps).
- **Status bar:** Shows case code, integrity, UTC, version, "OFFLINE MODE".

### Component Conventions

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| NeonButton | Primary/secondary/destructive/warning | `text`, `button_type` |
| StatusBadge | Origin/status label | `text`, `badge_type` |
| StatisticCard | KPI display with click | `label`, `value`, `action_key` |
| PageHeader | Page title + subtitle | `title`, `subtitle` |
| EvidenceBanner | Status banner | `text`, `banner_type` |
| EmptyState | No-data placeholder | `title`, `message` |
| ErrorPanel | Error display | `title`, `message`, `code`, `details` |

### Tables and Forms

- Tables use QTableWidget or QTreeWidget styled with QSS.
- Evidence page has a "Manual Parse" button (triggers `ParseEvidenceWorker`).
- Auto-parse runs after evidence import (via `ParseEvidenceWorker`).
- Settings page saves to `~/.wft/settings.toml` (or platform equivalent).
- Search page shows results grouped by scope in a splitter layout.

### Accessibility and Responsiveness

- Reduced motion available as `DesignTokens.reduced_motion` (consumed by `NavigationSidebar`); no runtime toggle API yet.
- Minimum window size: 1024x600. (High-contrast theme is spec-deferred, not implemented.)

## 7. Important Business Logic

### Case Lifecycle

1. Create case → `CaseService.create_case()` creates directory structure, `case.db` (with schema), `case.toml`, examiner record.
2. Open case → `CaseService.open_case()` validates `case.toml` and `case.db`, runs migration.
3. `ActiveCaseContext.open()` emits `case_changed(int, str)` signal → MainWindow refreshes KPI strip.
4. Cases can be OPEN, LOCKED, ARCHIVED, CLOSED (enum `CaseStatus`).

### Evidence Workflow

1. Import → `EvidenceService.import_file()` copies file to `originals/`, SHA256-hashes, registers in `evidence_items`, `evidence_files`, `evidence_hashes`.
2. State machine: `REGISTERED → COPYING → VERIFIED → PARSED`.
3. Parse runs automatically after import via `ParseEvidenceWorker`.
4. Manual re-parse button available.

### Parse Logic

- `ParseService.select_parser(source_path)` tries each parser's `inspect()` + `supports()`.
- Parser adapters: `TextExportParser`, `ZipExportParser`, `WhatsAppSQLiteAdapter`.
- Parsed artefacts: contacts, groups, conversations, messages, calls, media, timeline events, schema mappings, parser warnings.
- Each parse run records in `parser_runs` with status (STARTED/COMPLETED/PARTIAL/FAILED).
- Case-level upsert for contacts/groups by ID; conversation upsert by contact or group.

### Duplicate Detection

- Messages: unique constraint on `(source_evidence_file_id, source_table, source_record_id, parser_run_id)` — partial unique index (only when `source_record_id IS NOT NULL`).
- Contacts: unique on `(case_id, contact_code)`.
- Groups: unique on `(case_id, group_code)`.
- Conversations: unique on `(case_id, conversation_code)`.
- Calls: unique on `(case_id, call_code)`.
- Media: unique on `(case_id, media_code)`.
- Audit events: unique on `(case_id, event_sequence)` and `(case_id, event_hash)`.

### Audit Chain

- `AuditService.record_event()` inserts sequential events linked by SHA256 hash of canonical JSON.
- `previous_event_hash` field creates a hash chain.
- `AuditService.verify_chain()` re-computes hashes and detects any tampering.
- Used by: parse worker (records EVIDENCE_PARSED event), batch import (EVIDENCE_IMPORTED).

### Search

- `SearchService.search()` dispatches by scope (All, Messages, Contacts, Media, Calls, Recovered, Network, Notes).
- Messages: LIKE search on `text_content` and `caption_text` (FTS5 is defined but not populated).
- Contacts: LIKE on `display_name`, `phone_number_raw`, `whatsapp_identifier`.
- Media: LIKE on `original_filename`, `sha256`.
- Others: scope-specific LIKE queries.
- Date range filtering for Messages scope.

### Recovery Review

- `RecoveryService.get_candidates()` lists candidates per case with optional strategy/confidence filtering.
- Accept/Reject/Leave Unresolved calls `RecoveryCandidateRepository.update_review()`.

### Reports

- `HtmlReportGenerator.generate_case_summary()` creates a simple HTML table with case stats + limitations disclaimer.
- Report runs recorded in `report_runs` and `report_files` tables.

## 8. Testing Requirements

### How to Run

```bash
cd path\to\whatsapp_v1
python -m pytest tests/ -v --tb=short
python -m pytest tests/ -v --tb=short -k "test_name"  # single test
```

### Test Configuration

- `pyproject.toml` configures pytest: `testpaths = ["tests"]`, `python_files = ["test_*.py"]`.
- Markers: `slow`, `security`, `integration`.
- Shared `tests/conftest.py` provides one session-scoped `qapp` fixture.

### Current Coverage (409 tests)

| Test file | Tests | What it covers |
|-----------|-------|----------------|
| `test_hashing.py` | 5 | SHA256, SHA256 stream, SHA256 with copy, verify match/mismatch |
| `test_artefact_repositories.py` | 12 | Contact CRUD, message create/count, parser run lifecycle, media create |
| `test_audit.py` | 2 | Chain recording and verification, tamper detection |
| `test_confidence_scorer.py` | 5 | Score levels (HIGH/MEDIUM/LOW/UNRESOLVED), numeric scores |
| `test_schema_fingerprinter.py` | 8 | Fingerprint capture, determinism, empty DB, registry/match |
| `test_text_export_parser.py` | 4 | Inspect valid/invalid, parse count, capabilities |
| `test_structured_parser.py` | 8 | Structured output, direction, system events, media refs, timestamps, adapters |
| `test_ui_components.py` | 22 | All 8 components, cancellation token, nav |
| `test_active_case_context.py` | 10 | ActiveCaseContext state, open/close, signal emission, error handling |
| `test_statistics_service.py` | 8 | Empty/populated stats, isolation, call/media/audit/recovery KPIs |
| `test_search_service.py` | 11 | All 7 scopes, date filter, isolation, special chars, FTS5+LIKE |
| `test_recovery_service.py` | 8 | List, filter, pagination, accept/reject/unresolved, isolation |
| `test_repository_integration.py` | 15 | Conversation, Call, Media, Timeline, Audit, ReportRun repos |

### Required Verification After Changes

1. Run full test suite: `python -m pytest tests/ -v --tb=short`
2. If UI changes made, verify pytest-qt tests pass (requires Windows GUI session or Xvfb).
3. If database schema changes, recreate test fixtures in `_create_test_db()`.
4. If new service added, verify `Container` (bootstrap.py) instantiates it and `services/__init__.py` exports it.
5. If new repository added, verify it extends `BaseRepository` and is importable.
6. If repository method signatures change, update all callers in both services and UI pages.
7. If parser changes, verify `_INSTALLED_PARSERS` in `parse_service.py` includes it.

### Regression Areas

- UI page tests that construct pages with `_FakeCtx()` mock.
- Repository tests that use `_create_test_db()` with the full schema.
- Audit chain verification — must never break hash chain logic.
- Any change to duplicate-detection logic (unique constraints).

## 9. Build and Deployment

### Development Commands

```bash
python -m pytest tests/ -v --tb=short   # Run all tests
ruff check src/                           # Lint (ruff >=0.1)
black --check src/                        # Formatting check
mypy src/                                 # Type check (strict)
```

### Running the App

```bash
python -m wft.main                        # Direct execution
python src/wft/main.py                    # Alternative
wft                                       # If installed via pip
```

### Entry Points

- Console script: `wft = "wft.main:main"` (in `[project.scripts]`).
- `MainWindow.APP_VERSION = "1.0.0a1"`.

### Packaging

```bash
pip install build
python -m build                           # Creates sdist + wheel in dist/
```

- `[tool.setuptools.packages.find]` with `where = ["src"]`, `include = ["wft*"]`.
- Package data includes `**/*.html`, `**/*.css`, `**/*.svg`, `**/*.png`.

### Platform Notes

- **Windows 10/11** is primary target. Settings path: `%APPDATA%/WhatsApp Forensic Toolkit/settings.toml`.
- **macOS** secondary. Settings: `~/Library/Application Support/WhatsApp Forensic Toolkit/settings.toml`.
- **Linux** tertiary. Settings: `~/.config/whatsapp-forensic-toolkit/settings.toml`.
- App icon, .desktop file, .spec file: not yet created.

### Dependencies

All in `pyproject.toml` `[project.dependencies]`. Optional dependency groups: `pdf`, `network`, `geoip`, `yara`, `exif`, `dev`.

Note: `tomli_w` is imported by `case_service.py` but NOT listed in `pyproject.toml` dependencies. This must be added.

## 10. Known Issues and Limitations

### Issues


### Performance Concerns

- LIKE searches on large tables (messages, media) are unindexed — no `text_content` index exists.
- Repository methods that fetch all records without pagination may be slow for large cases.

### Unsupported Behavior

- ADB extraction (placeholder page only).
- Backup decryption (placeholder page only).
- Network capture (schema exists, no integration).
- Media file thumbnail generation (schema has `preview_relative_path` column, no code).
- Export manifests (schema exists, no UI integration).
- PDF report generation (requires optional `weasyprint`/`reportlab`).
- Case encryption.
- Case locking.

### Technical Debt

- `ui/workers/` — legacy synchronous worker APIs remain for scripts/tests; `EvidencePage` uses `EvidenceImportWorker` and `EvidenceParseWorker` through `QThreadPool`.
- `_create_test_db()` turns off foreign keys — should use proper migration.

## 11. Completed Decisions

- **One database per case** — case.db is standalone; no global/shared database. Cases are isolated.
- **ActiveCaseContext as shared state** — all pages receive `ctx: ActiveCaseContext` rather than accessing Container or using signals directly. This keeps pages decoupled from MainWindow.
- **Repository-per-query pattern** — repositories are instantiated per-call (`RepoClass(db)`) rather than being long-lived singletons. Services are long-lived in the Container.
- **No ORM** — direct `sqlite3` parameterized queries with `sqlite3.Row` factory. Pydantic used at domain boundary only.
- **Offline-first** — no telemetry, no external services by default. Network capture disabled by default.
- **Hash-chained audit** — SHA256-linked list of canonical JSON events. Any tampering is detectable.
- **Case directory structure** — `originals/`, `working/`, `derived/parsed/`, `derived/recovered/`, `derived/thumbnails/`, `derived/indexes/`, `reports/`, `exports/`, `logs/`, `manifests/`, `notes/`.
- **App version in multiple places** — `pyproject.toml` version, `MainWindow.APP_VERSION`, `Migrator._app_version`, `AuditService._app_version`, `ReportRunRepository.generator_version`, `EvidenceService hash calculated_by_tool_version`. Must keep in sync.
- **Fonts:** `Consolas, 'Courier New', monospace` for code/mono (QSS). Noto Sans / Segoe UI for body.
- **Deployment tool:** py-to-exe or Nuitka (planned, not implemented).

## 12. Pending Work

### High Priority

1. Add `tomli_w` to `pyproject.toml` `[project.dependencies]`.

### Medium Priority

2. Build actual `packaging/` scripts (PyInstaller spec, NSIS installer, etc.).
3. Write integration tests for E2E workflow (scripts/run_e2e_demo.py exists).

### Low Priority

11. Implement ADB extraction via `adb-extractor` or `adb_shell`.
12. Implement backup decryption (crypt12/crypt14/crypt15 support).
13. Network capture integration (PCAP import + live capture with scapy).
14. Media thumbnail generation (Pillow-based preview).
15. PDF report generation via weasyprint or reportlab.
16. Case encryption and locking functionality.
17. Export manifest creation and verification.
18. i18n support.

## 13. Agent Working Instructions

1. **Read `AGENTS.md` before making changes** — understand architecture, patterns, and known issues.
2. **Inspect existing implementations before creating new ones** — check for similar patterns in services, repositories, and pages.
3. **Do not duplicate services, helpers, components, or database queries** — reuse existing code paths.
4. **Preserve existing business logic unless explicitly instructed** — especially provenance tracking, unique constraint handling, and audit chain logic.
5. **Do not make unrelated changes** — scope changes to the specific task.
6. **Update tests when behavior changes** — add/modify tests in the appropriate test file.
7. **Run relevant tests after every modification** — `python -m pytest tests/ -v --tb=short`.
8. **Update `AGENTS.md`** whenever architecture, major features, commands, known issues, or project decisions change.
9. **Never mark a task complete without verifying the implementation** — run tests, check imports, verify the code compiles/runs.
10. **Check pyproject.toml dependencies before using a new library** — add to `[project.dependencies]` or `[project.optional-dependencies]` as appropriate.
11. **When adding a new service:** add it to `bootstrap.py` Container, export from `services/__init__.py`.
12. **When adding a new page:** add it to `MainWindow._build_page_area()` + `_page_map`, add nav item in `_nav_items`.
13. **When adding a new repository:** extend `BaseRepository`, add it to `artefact_repositories.py`.
14. **Never hardcode secrets** — all secrets go through settings or environment variables.
15. **Use `_now_utc()` helper pattern** for timestamp generation (reuse existing pattern, don't create new variants).
16. **Keep app version in sync** across `pyproject.toml`, `main.py`, `migrations.py`, `audit_service.py`, `artefact_repositories.py`.

## 14. Session Memory Log

### 2026-07-20
- Change: Connected all 18 UI pages to real backend services and repositories.
- Files affected: All 18 `ui/pages/*.py`, `ui/main_window.py`, `bootstrap.py`, `application/services/*.py`, `infrastructure/database/artefact_repositories.py`
- Reason: Pages were using placeholder/inline data; needed database-backed operation.
- Verification: All 76 existing tests pass.
- Important follow-up: Integration tests planned for new services (ActiveCaseContext, StatisticsService, SearchService, RecoveryService).

### 2026-07-20
- Change: Created ActiveCaseContext (QObject with case_changed signal).
- Files affected: `application/services/case_context.py` (new)
- Reason: All pages need shared case state (case_id, case_path, db_path, DatabaseConnection).
- Verification: Container instantiates it; MainWindow connects to case_changed signal.
- Important follow-up: None.

### 2026-07-20
- Change: Created StatisticsService, SearchService, RecoveryService.
- Files affected: `application/services/statistics_service.py`, `search_service.py`, `recovery_service.py` (all new)
- Reason: Dashboard KPIs, multi-scope search, and recovery candidate review needed dedicated services.
- Verification: Services import correctly and are wired in Container.
- Important follow-up: No integration tests yet for these services.

### 2026-07-20
- Change: Extended artefact_repositories with list/query methods + 4 new classes (TimelineEventRepository, RecoveryCandidateRepository, AuditEventRepository, ReportRunRepository).
- Files affected: `infrastructure/database/artefact_repositories.py`
- Reason: UI pages need to query data with filters, joins, and pagination.
- Verification: All 76 tests pass.
- Important follow-up: ConversationRepository.list_for_case() and list_with_stats() are on the wrong class (defined in MessageRepository instead of ConversationRepository).

### 2026-07-20
- Change: Created ParseEvidenceWorker and BatchImportWorker.
- Files affected: `ui/workers/parse_worker.py` (new)
- Reason: Evidence page needs background parsing and combined import+parse workflow.
- Verification: Both workers tested via unit imports.
- Important follow-up: Workers are synchronous; should be ported to QThread/QRunnable.

### 2026-07-20 (Phase 4.1: Integration Testing & FTS5)
- Change: Created SearchIndexService for FTS5 index population and management (`src/wft/application/services/search_index_service.py`).
- Change: Updated SearchService to use FTS5 prefix matching for simple queries, LIKE fallback for queries with special chars; fixed `_search_notes` SQL bug.
- Change: Updated ParseService to call SearchIndexService.create_index() after successful parse commits.
- Change: Fixed 3 bugs from AGENTS.md: duplicate `update_item_state` removed, conversation methods moved to ConversationRepository, `_search_notes` SQL fixed.
- Change: Created 5 integration test files (50 tests): ActiveCaseContext (10), StatisticsService (8), SearchService (11), RecoveryService (8), Repository Integration (15).
- Change: Created `scripts/run_e2e_demo.py` — full workflow E2E demo (27 steps: create case, import, parse, verify artefacts, search FTS5, stats, notes, report, audit chain, reopen persistence).
- Verification: All 133 tests pass (57 unit + 50 integration + 26 UI). E2E demo: 27/27 steps pass.
- Files affected: `services/search_index_service.py` (new), `services/search_service.py` (updated), `services/parse_service.py` (updated), `services/evidence_service.py` (fix), `database/artefact_repositories.py` (fix), `scripts/run_e2e_demo.py` (new), `tests/integration/*.py` (5 new files).
- Important follow-up: Integration tests use tempfile.mkdtemp()+shutil.rmtree on Windows; FTS5 queries use prefix matching via `"term"*` for alphanumeric queries only.

### 2026-07-20 (ADB Device Detection)
- Change: Created complete ADB detection subsystem for USB-connected Android device recognition.
- Change: Created `src/wft/application/services/adb_service.py` — AdbService with 6-step ADB binary discovery, `subprocess.run()`-based execution (`CREATE_NO_WINDOW`, 15s timeout, `-s SERIAL` for device commands), `AdbDevice`/`AdbState`/`AdbError` data model, `list_devices()`/`get_device_details()`/`server_version()`/`start_server()`/`kill_server()`/`validate_path()` methods, multi-word state token parsing.
- Change: Added `AdbSettings` dataclass to `settings.py` (adb_path, auto_detect, poll_interval_seconds clamped 2-30).
- Change: Created `src/wft/ui/workers/adb_scan_worker.py` — AdbScanWorker with AdbScanWorkerSignals (started/finished/error), CancellationToken support, NO_ADB short-circuit.
- Change: Rewrote `adb_extractor_page.py` — device selector, state-aware EvidenceBanners (9 state banners), device info form, polling QTimer (start/stop on activate/deactivate), auto-detect toggle, skip-if-scanning guard, Start Server/Kill Server/Troubleshoot buttons, log area, authorized actions disabled when not CONNECTED.
- Change: Extended `settings_page.py` with ADB path browse/test, auto-detect toggle, poll interval spinbox.
- Change: Updated `bootstrap.py` Container to instantiate AdbService with configured_path from settings. Updated `main_window.py` to pass Container to ADB page.
- Change: Created 47 new tests (11 path detection, 13 output parsing, 15 service, 7 worker). All use `unittest.mock.patch(subprocess.run) — no real phone required.
- Change: Created `scripts/test_adb_device.py` for manual hardware validation.
- Verification: All 180 tests pass (133 existing + 47 new).
- Files affected: `services/adb_service.py` (new), `workers/adb_scan_worker.py` (new), `pages/adb_extractor_page.py` (rewrite), `pages/settings_page.py` (extended), `settings/settings.py` (extended), `bootstrap.py` (extended), `main_window.py` (updated), `ui/workers/__init__.py` (extended), `application/services/__init__.py` (extended), `tests/unit/test_adb_*.py` (4 new files), `scripts/test_adb_device.py` (new), `docs/superpowers/specs/2026-07-20-adb-detection-design.md` (new).
- Important follow-up: Manual hardware validation required — run `python scripts/test_adb_device.py` with real Android device connected via USB. Must not declare issue fixed until real device detection confirmed.

### 2026-07-20 (ADB Extractor UI Fixes — Phase 2)
- Change: Fixed all 10 ADB Extractor page UI problems.
- Root cause (unreadable device details): `_make_info_field()` used `setFixedWidth(120)` — labels like "Authorisation State:" (18 chars at 13px) needed ~126px minimum. Combined with `setSpacing(4)` on the grid, content clipped at high DPI. Replaced with `setMinimumWidth(130)`, `QGridLayout` with `setHorizontalSpacing(24)`, `setVerticalSpacing(8)`, individual named widget attributes (`_manufacturer_value`, `_model_value`, etc.) instead of dict-only lookup.
- Root cause (empty banner rectangle): `setFixedWidth(20)` on icon label always allocated space even when icon text was empty. Replaced with `setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)` and `setMinimumWidth(18)` — icon now takes only needed space and collapses when hidden.
- Root cause (compressed controls): 4px grid spacing and 8px layout margins were too tight. Changed to 24px horizontal spacing, 8px vertical spacing, 16px group box margins. Content margins 0/8/0/8 on info grid, 16px all sides on device group.
- Root cause (auto-detect overlap): Poll interval was a `QLabel` next to checkbox without a spinbox. Replaced with `QSpinBox` (2–30s range, suffix " s", 80px fixed width) on its own `auto_row` with clear 12px separator from button row.
- Root cause (font warnings): No font size validation anywhere. Added `ensure_valid_font_size()` helper that checks `pointSize() <= 0` and falls back to minimum 10pt. Applied to all info labels and values via `_make_info_label()` and `_make_info_field()`.
- Change: Rebuilt page layout with proper QGridLayout for device info (8 named fields), splitter 60/40 stretch with `left_panel.minimumWidth=620`, `right_panel.minimumWidth=320`.
- Change: Device selector now `minWidth=320`, `maxWidth=760`, displays "Model — RedactedSerial — State".
- Change: Status badge on its own row below selector, not mixed with detail grid.
- Change: Serial value shows redacted text (`_redact_serial`), full serial in tooltip.
- Change: EvidenceBanner no longer uses `setFixedWidth(20)` for icon — uses `QSizePolicy.Minimum` with `setMinimumWidth(18)`.
- Files affected: `pages/adb_extractor_page.py` (full rewrite — layout, font safety, spinbox, individual value attrs), `components/evidence_banner.py` (icon width fix).
- Tests: Added 41 tests in `tests/unit/test_adb_page_layout.py` — font safety, device detail rendering, device selector dimensions, auto-detect controls, case state, EvidenceBanner icon visibility/size policy, splitter layout, poll interval spinbox.
- Verification: All 221 tests pass (180 existing + 41 new).
- Important follow-up: Manual hardware validation still required — run `python scripts/test_adb_device.py` with real Android device. Test at Windows display scaling 100%, 125%, 150%, 175%.

### 2026-07-20 (UI Freeze Fix — Phase 2: Async Infrastructure)
- **Root cause (UI freezing):** All `on_activated()` methods ran synchronous SQL/file I/O on the UI thread, blocking Qt event loop for 100ms-15s. ADB subprocess calls blocked up to 15s. Navigation remained unresponsive until all data loaded.
- **Change:** Created `src/wft/ui/utils/font_utils.py` — shared `ensure_valid_font_size()` and `safe_font()` utilities that handle both `pointSize() <= 0` (QSS-set fonts) and `pixelSize()` fallback.
- **Change:** Fixed `MainWindow.navigate_to()` — page activation is now deferred to `QTimer.singleShot(0, page.on_activated)`, letting the UI switch pages immediately before data loads.
- **Change:** Fixed `MainWindow._on_case_changed()` — KPI strip refresh is now deferred to `QTimer.singleShot(0, ...)`, preventing case-open freeze.
- **Change:** Fixed ADB page log widget from `QTextEdit` to `QPlainTextEdit` — `QTextEdit` lacks `setMaximumBlockCount()` which caused `AttributeError` on page construction.
- **Change:** Added `_service_override` parameter to `AdbOperationWorker.__init__()` for test injection.
- **Change:** Moved `ensure_valid_font_size` from `adb_extractor_page.py` to shared `font_utils.py`; ADB page now imports it.
- **Change:** Updated `ui/workers/__init__.py` to export `AdbOperationWorker`/`AdbOperationSignals` instead of old `AdbScanWorker`/`AdbScanWorkerSignals`.
- **Change:** Rewrote `tests/unit/test_adb_scan_worker.py` — 8 tests for `AdbOperationWorker` with all 5 operation types (SCAN, START_SERVER, KILL_SERVER, DEVICE_DETAILS, VALIDATE_PATH).
- **Files affected:** `ui/utils/font_utils.py` (new), `ui/utils/__init__.py` (new), `ui/main_window.py` (async navigation + KPI), `ui/pages/adb_extractor_page.py` (QPlainTextEdit + imported font_utils), `ui/workers/adb_scan_worker.py` (_service_override param), `ui/workers/__init__.py` (updated exports), `tests/unit/test_adb_scan_worker.py` (rewritten).
- **Verification:** All 222 tests pass (197 existing + 25 updated).
- **Important follow-up:** Remaining pages (14/16 with on_activated) still run synchronous work. Full async page activation planned for next phase.

### 2026-09-18 (End-to-End Audit)
- Fixed evidence import registration ordering so imports no longer fail before the evidence row exists.
- Fixed evidence-page and worker parse flows to use verified case-stored copies and actual evidence-file IDs.
- Committed parser evidence-state updates on success and failure paths.
- Hardened case-relative and ZIP extraction path checks against prefix escapes, backslash traversal, and symlink entries.
- Declared `tomli-w` as a runtime dependency in `pyproject.toml`.
- Verification: full suite 408 passed; E2E demo 27/27 passed; `compileall` passed. `ruff` and `mypy` were unavailable in the environment.
- Remaining limitations: ADB hardware validation requires an authorized device.

### 2026-09-18 (Async Evidence UI and Test Infrastructure)
- Evidence-page import and manual/automatic parse now run through `QThreadPool` QRunnable workers with queued Qt signals for progress, completion, cancellation, and errors.
- Workers create their own `UnitOfWork`/SQLite connections and parse only the verified case-local copy using the actual `evidence_files.id`.
- Active evidence operations reject duplicates, support cancellation, and are invalidated when the active case changes or the page closes.
- Added `reduced_glow.qss` and made missing theme resources fail clearly instead of silently falling back.
- Centralized the QApplication fixture in `tests/conftest.py` and removed duplicate per-module fixtures.
- Fixed sidebar animation cleanup to disconnect the exact connected slots; the previous PySide signal-disconnect warnings no longer occur.
- Verification: full suite 418 passed with 1 pytest-asyncio deprecation warning; E2E demo 27/27 passed; `compileall` and `git diff --check` passed.
- Remaining limitations: legacy synchronous worker APIs remain for non-UI callers; ADB hardware validation requires an authorized device; `ruff` and `mypy` availability remains environment-dependent.

### 2026-09-18 (Asynchronous Directory Evidence Import)
- Directory sources selected on the Evidence page now use the existing `QThreadPool`/`QRunnable` import path.
- One logical evidence item is created per directory and one `evidence_files`/hash record per safe regular file, preserving relative paths and actual file IDs.
- Directory traversal rejects symlinks/reparse points, resolves containment with `commonpath`, rejects sources inside the active case, and never modifies source files.
- Cancellation and partial/unsupported directory results remain durable and cannot be reported as fully verified imports.
- Verification: targeted directory tests passed; full suite and E2E verification recorded after implementation.

### 2026-09-18 (Directory Import Production Hardening)
- Fixed directory-parse cancellation so a cancellation requested during parser inspection durably marks the evidence item `FAILED` and never reports successful completion.
- Fixed worker transaction lifetime so directory import registration commits before directory parsing begins, avoiding nested SQLite UnitOfWork usage.
- Made directory progress monotonic across copy and parse phases.
- Verification: full suite 418 passed with 1 pytest-asyncio deprecation warning; E2E demo 27/27 passed; compileall and git diff --check passed.
- Remaining limitations: ruff and mypy are unavailable; external code-review agents are unavailable; ADB hardware validation still requires an authorized device.

### 2026-10-08 (Legacy Theme System Removal)
- Change: Deleted the entire legacy theme system (`src/wft/ui/themes/`: old `ColorTokens`, old `ThemeManager`, and the 3 static `.qss` files). The surviving token system (`src/wft/ui/theme/`: `DesignTokens` + `qss_builder.py` + `ThemeManager`) is now the only implementation. `main.py` no longer pre-applies a stylesheet — `Container.__init__` applies the built QSS via `load_saved_theme()`. Removed the unused `MainWindow.set_theme_manager()` hook and repointed `wft.ui` package exports to the new classes (`ThemeManager`, `DesignTokens`). Removed the 10 tests that locked the legacy system in place (`TestColorTokens`, `TestThemeManager`, `TestThemeQSS` in `test_ui_components.py`; `test_reduced_glow_theme_resource_exists` in `test_evidence_async.py`) and added one wiring test asserting the `wft.ui` exports resolve to the new classes.
- Reason: architecture-scan found two full theme systems; the old one applied `dark_neon.qss` at `main.py:49`, which was immediately overwritten by `bootstrap.py:52` — dead at runtime, with drifting token definitions (`ColorTokens` vs `DesignTokens`) and 10 tests locking it in.
- Verification: full suite 409 passed (418 − 10 legacy + 1 wiring); E2E demo 27/27; `python -c "import wft.main"` clean. Work executed on branch `refactor/remove-legacy-theme-system` per the plan at `docs/superpowers/plans/2026-10-08-remove-legacy-theme-system.md`.
- Deviations from spec: `docs/superpowers/specs/2026-07-21-phase1-ui-redesign.md` had marked the legacy `.qss` files "PRESERVE for rollback" — deleted instead (git history serves rollback; in-tree derived QSS invites drift from `qss_builder.py`). `high_contrast`, previously advertised in AGENTS.md, was spec-deferred and unreachable at runtime, so removing it is a docs correction, not a feature removal. Follow-up: add `high_contrast` as a real `DesignTokens` preset + `_THEME_REGISTRY` entry when wanted. The "Current Coverage" table above remains stale for other (older) test files and should be reconciled in a separate docs pass.

### 2026-10-08 (ADB WhatsApp Database Acquisition)
- Change: Implemented "Extract WhatsApp Databases" as a real acquisition workflow. New pure module `src/wft/acquisition/whatsapp_paths.py` (PathCandidate + `plan_database_paths()`; public `/sdcard/Android/media/com.whatsapp/WhatsApp/Databases` + `/sdcard/WhatsApp/Databases`, private `/data/data/com.whatsapp/databases` + `files/key` for SU only). `AdbService.detect_root(serial)` added with `RootAccess` enum (SU / ADB_ROOT_CAPABLE / NONE) — probes `su -c id` then `getprop ro.build.type`; never invokes `adb root`. `AdbOperationWorker` gained `EXTRACT_WHATSAPP_DATABASES` operation: enumerate → pull → per-file SHA-256 → per-file evidence_files/hashes rows under one evidence_items row → `WHATSAPP_DATABASES_ACQUIRED` audit event → structured result (ACQUIRED/PARTIAL/NO_FILES_FOUND/FAILED/CANCELLED). ADB page gained the button + tooltip in the authorised-actions area, reusing existing preconditions/progress/cancel machinery.
- Rules honoured: encrypted crypt12/14/15 acquired byte-for-byte (decryption pending, no decryption code); no automatic parsing; no wireless ADB; ADB_ROOT_CAPABLE never grants private-path access.
- Deviation from spec literal: `acquisition_method="ADB_LOGICAL"` used instead of the spec's `"adb"` to match existing sibling acquisitions (media/metadata).
- Verification: full suite 448 passed (409 + 39 new); E2E demo 27/27; `compileall` clean; diff audited for com.whatsupport/adb-root/parse/decrypt — zero hits. ruff/black/pyflakes unavailable in this environment (pre-existing limitation).
- Follow-ups: real-device validation with a USB-connected Android device remains untested; crypt12/14/15 decryption is the next capability; `SettingsPage` save-path bug (`~/.wft/` vs platform path) still open; `_now_utc()` duplication (bottleneck #2) still open.
