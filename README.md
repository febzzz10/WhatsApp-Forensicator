# WhatsApp Forensicator

**Offline-first desktop forensic toolkit for acquiring, preserving, parsing, analysing and reporting WhatsApp-related digital evidence — through lawful, authorised workflows only.**

> **Authorised use only.** On startup the application requires acknowledgement of a legal notice: it is intended for authorised forensic examiners, cybersecurity analysts, incident responders, and supervised students. It must not be used for unauthorised surveillance. Network capture is limited to authorised networks, IP-based locations are approximate, deleted-data recovery is not guaranteed, and the application cannot decrypt call audio or video.

- **Version:** `1.0.0a1` (alpha)
- **Platform:** Windows 10/11 (primary); macOS / Linux secondary
- **Stack:** Python 3.11+, PySide6 (Qt), SQLite (one `case.db` per case), Jinja2, Pillow
- **Mode:** offline-first — no telemetry, no external services by default

---

## What works today

| Area | Capability | Status |
|---|---|---|
| **Cases** | Create / open forensic cases, examiner + authorisation records, case lifecycle (`OPEN`/`LOCKED`/`ARCHIVED`/`CLOSED`) | ✅ Working |
| **Evidence** | Import files and directories (text exports, ZIP archives, SQLite DBs); SHA-256 hash verification; originals stored read-only and never modified | ✅ Working |
| **Parsing** | WhatsApp text-export parser, ZIP-export parser, SQLite adapter with schema fingerprinting; parse runs recorded with provenance (`origin` + confidence per artefact) | ✅ Working |
| **Chat viewer** | WhatsApp-style conversation list + bubble message rendering, conversation search/filter, per-message provenance | ✅ Working |
| **Artefact viewers** | Contacts, groups, call records, media, cross-artefact timeline, statistics dashboard, 7-scope search (FTS5 + LIKE fallback) | ✅ Working |
| **ADB device detection** | USB device discovery, multi-word state parsing (`connected`/`unauthorized`/`offline`/…), device details, server start/stop, path validation | ✅ Working (USB only) |
| **ADB WhatsApp database extraction** | New **Extract WhatsApp Databases** action: probes root capability (`su` → private paths, otherwise public paths only — `adb root` is never executed), pulls `msgstore.db`, `wa.db`, `crypt12/14/15` backups, `-wal`/`-journal` sidecars and the `key` file into `originals/adb_databases/`, with per-file SHA-256, per-file evidence registration, and a `WHATSAPP_DATABASES_ACQUIRED` audit event | ✅ Working (mock-tested; **real-device validation still pending**) |
| **ADB media copy / metadata** | Copy accessible media directories; record device metadata as a hashed evidence artefact | ✅ Working |
| **Audit trail** | Hash-chained (SHA-256 linked list) audit events; tampering is detectable via chain verification | ✅ Working |
| **Recovery review** | Recovery-candidate listing with accept/reject/unresolved review | ✅ Working |
| **Reports** | HTML case-summary report with limitations disclaimer | ⚠️ HTML only — TXT/CSV/JSON exporters not yet built |
| **Theme** | Token-built dark forensic UI (`DesignTokens` → generated QSS, single theme system) | ✅ Working |

## Explicitly not yet built (UI shells exist, backends do not)

- **Backup decryption** — the Decryptor page is a UI shell. `crypt12`/`crypt14`/`crypt15` decryption is the next capability in the chain; extracted backups remain **decryption-pending** evidence.
- **Non-root legacy-backup extraction** (Android ≤ 13 backup-agent method) — not implemented.
- **Wireless / TCP-IP ADB** — USB only.
- **VoIP live capture + GeoIP mapping** — the VoIP page is a shell reading an (unpopulated) `network_endpoints` table; no capture service, no GeoIP. Note: even when built, IP geolocation identifies relays/VPNs/gateways as often as participants — the UI already carries this disclaimer.
- **Encrypted media (`.enc`) decryption** — not implemented.
- **Case encryption / locking, PDF reports, thumbnail generation, export manifests, i18n** — not implemented.

---

## Typical workflow

```
1. Create / open a case            (Cases, Home)
2. Connect Android device via USB  (ADB Extractor: scan → select authorised device)
3. Extract WhatsApp databases      (ADB Extractor → "Extract WhatsApp Databases")
4. Review acquired evidence        (Evidence page — encrypted backups stay decryption-pending)
5. Parse supported artefacts       (Evidence page → parse; msgstore/wa.db text exports)
6. Analyse                         (Chats, Contacts, Groups, Calls, Media, Timeline, Search)
7. Verify audit chain              (Audit page)
8. Export HTML report              (Reports page)
```

All pages share one `ActiveCaseContext` (active case id/path/DB connection); the KPI strip refreshes on the `case_changed` signal.

---

## Installation

Requires **Python 3.11+** (developed against 3.11–3.14).

```bash
# from the repository root
pip install -e .            # installs the `wft` console script
pip install -e ".[dev]"     # + pytest, pytest-qt, black, ruff, mypy
pip install -e ".[network]" # optional: scapy (future live capture)
pip install -e ".[geoip]"   # optional: maxminddb (future GeoIP)
pip install -e ".[pdf]"     # optional: weasyprint/reportlab (future PDF reports)
```

## Running

```bash
python -m wft.main    # or:  wft        (after pip install)
```

- Accepts the legal notice → opens the main window (`WHATSAPP FORENSICATOR`, 1366×768 default).
- Settings live in `%APPDATA%/WhatsApp Forensic Toolkit/settings.toml` on Windows
  (`~/Library/Application Support/…` on macOS, `~/.config/whatsapp-forensic-toolkit/` on Linux).
- Each case is a self-contained directory: `originals/`, `working/`, `derived/`, `reports/`, `exports/`, `logs/`, `manifests/`, `notes/`, plus a portable, independently verifiable `case.db` (SQLite, WAL mode, foreign keys on).

## Testing

```bash
python -m pytest tests/ -v --tb=short          # full suite (448 tests, ~70 s)
python -m pytest tests/ -k "whatsapp"          # extraction capability tests
python scripts/run_e2e_demo.py                 # end-to-end demo: 27/27 steps
```

- UI tests use `pytest-qt` (shared `qapp` fixture in `tests/conftest.py`).
- ADB tests are fully offline: `MagicMock(spec=AdbService)` service injection and patched `subprocess.run` — **no Android device is ever required by the test suite**.
- Dev checks: `ruff check src/` · `black --check src/` · `mypy src/` (strict). Line length: 100.

---

## Architecture ( condensed )

```
src/wft/
├── main.py, bootstrap.py            # entry point + DI container (services)
├── application/services/            # Case, Evidence, Parse, Audit, Search,
│                                    # Statistics, Recovery, AdbService
├── domain/                          # enums, dataclasses, provenance helpers
├── parsers/                         # text export, zip export, SQLite adapter
├── acquisition/                     # pure WhatsApp path planning (whatsapp_paths.py)
├── infrastructure/                  # database (schema/migrations/repos/UoW),
│                                    # hashing, file store, logging, settings
├── reports/                         # HTML report generator
└── ui/                              # main window, 18 pages, components,
                                     # token theme system, QThreadPool workers
```

Key patterns (see `AGENTS.md` for the full working guide):

- **Repository-per-query** — short-lived `RepoClass(db)` instances; services are long-lived in the container.
- **Background work on `QThreadPool`** — import/parse/ADB operations are `QRunnable` workers with progress/cancel/error signals; pages never block the UI thread.
- **Forensic integrity rules** — originals are never modified; every artefact carries `origin` + confidence; parsed / recovered / inferred data stay distinguishable; raw + normalised-UTC timestamps are both kept; most case-level foreign keys are `ON DELETE RESTRICT`.
- **Evidence states** — `REGISTERED → COPYING → VERIFIED → PARSED` (or `FAILED`/`UNSUPPORTED`/…).
- **Audit chain** — each event stores the SHA-256 of canonical JSON chained to the previous event hash.

---

## Roadmap (next in line)

1. **crypt12/14/15 backup decryption** using lawfully provided key material (completes Extract → Decrypt → Parse).
2. **Real-device validation** of the ADB extraction flow (USB, rooted + non-rooted).
3. **TXT/CSV/JSON report exporters** alongside HTML.
4. Non-root legacy-backup extraction · wireless ADB · VoIP capture + GeoIP · `.enc` media decryption.

## Known limitations

- Alpha quality: ADB extraction and backup decryption paths beyond the above are placeholders; case encryption/locking unimplemented.
- `LIKE` searches on very large message/media tables are unindexed.
- `ruff`/`mypy` availability is environment-dependent; run them where installed.

---

*For the full contributor working guide — architecture, database rules, UI/UX tokens, testing requirements, session history — see [`AGENTS.md`](AGENTS.md).*
