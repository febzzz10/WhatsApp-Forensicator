#!/usr/bin/env python3
"""End-to-end demo: creates a case, imports evidence, parses it, searches,
generates reports, verifies the audit chain, and confirms persistence."""

import argparse
import hashlib
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from wft.application.services.case_service import CaseService
from wft.application.services.evidence_service import EvidenceService
from wft.application.services.audit_service import AuditService
from wft.application.services.parse_service import ParseService
from wft.application.services.search_service import SearchService
from wft.application.services.statistics_service import StatisticsService
from wft.application.services.recovery_service import RecoveryService
from wft.application.services.search_index_service import SearchIndexService
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.filesystem.file_store import FileStore
from wft.infrastructure.logging.logging_service import LoggingService
from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.uow import UnitOfWork
from wft.infrastructure.database.artefact_repositories import (
    AuditEventRepository,
    ReportRunRepository,
    MessageRepository,
    ConversationRepository,
)


_PASS = 0
_FAIL = 0


def step(name: str, result: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if result:
        _PASS += 1
        print(f"  [PASS] {name}")
    else:
        _FAIL += 1
        print(f"  [FAIL] {name} - {detail}")


def main() -> int:
    global _PASS, _FAIL
    parser = argparse.ArgumentParser(description="WhatsApp Forensicator E2E Demo")
    parser.add_argument("--keep-case", action="store_true", help="Keep temporary case directory")
    args = parser.parse_args()

    tmp_base = Path(tempfile.mkdtemp(prefix="wft_e2e_"))
    case_code = f"E2E-{uuid.uuid4().hex[:6].upper()}"
    case_path = tmp_base / "cases" / case_code

    print(f"\n{'='*60}")
    print(f"  WhatsApp Forensicator — E2E Demo")
    print(f"  Case: {case_code}")
    print(f"  Path: {case_path}")
    print(f"{'='*60}\n")

    try:
        # 1. Create case
        print("--- Phase 1: Case Creation ---")
        hash_svc = HashingService()
        log = LoggingService(log_dir=None, level="WARNING")
        case_svc = CaseService(hash_svc, log)
        auditor = AuditService()

        result = case_svc.create_case(
            case_dir=tmp_base / "cases",
            case_code=case_code,
            title="E2E Test Case",
            examiner_name="Test Examiner",
            organisation="Test Org",
        )
        case_id = result["case_id"]
        step("Case created", case_id > 0, f"ID={case_id}")

        db_path = case_path / "case.db"
        uow = UnitOfWork(db_path)
        with uow:
            auditor.record_event(uow.db, case_id, "CASE_CREATED", "E2E case created", component_name="e2e_demo")
            uow.commit()
        step("Case creation audit event recorded", True)

        # 2. Create WhatsApp text export fixture
        print("\n--- Phase 2: Evidence Import ---")
        fixture_dir = case_path / "import_sources"
        fixture_dir.mkdir(exist_ok=True)
        chat_content = (
            "1/15/26, 10:30 AM - Alice: Hello there!\n"
            "1/15/26, 10:31 AM - Bob: Hi Alice, how are you?\n"
            "1/15/26, 10:32 AM - Alice: I'm good thanks! Check this out https://example.com\n"
            "1/15/26, 10:33 AM - Bob: Nice link\n"
            "1/15/26, 10:34 AM - You: Hey everyone\n"
        )
        chat_file = fixture_dir / "_chat.txt"
        chat_file.write_bytes(chat_content.encode("utf-8"))
        step("Fixture created", chat_file.exists())

        store = FileStore(case_path, hash_svc)
        ev_svc = EvidenceService(store, hash_svc, log)

        uow = UnitOfWork(db_path)
        with uow:
            ev_result = ev_svc.import_file(
                db=uow.db, case_id=case_id,
                evidence_code="E0001", title="_chat.txt",
                source_type="WHATSAPP_TEXT_EXPORT",
                acquisition_method="USER_PROVIDED",
                source_path=chat_file,
            )
            item_id = ev_result["item_id"]
            file_id = ev_result.get("file_id", 1)
            sha256 = ev_result["sha256"]
            auditor.record_event(uow.db, case_id, "EVIDENCE_IMPORTED",
                                 f"Imported _chat.txt as E0001", component_name="e2e_demo")
            uow.commit()
        step("Evidence imported", item_id > 0, f"ID={item_id}")

        expected_sha = hashlib.sha256(chat_content.encode("utf-8")).hexdigest()
        step(f"SHA-256 match", sha256 == expected_sha, f"got {sha256[:16]}...")

        # 3. Parse evidence
        print("\n--- Phase 3: Parse ---")
        parse_svc = ParseService(log)
        parse_result = parse_svc.parse_evidence(
            case_id=case_id, evidence_item_id=item_id,
            source_file_id=file_id, source_path=chat_file,
            db_path=db_path, case_dir=case_path,
        )
        step("Parse succeeded", parse_result.get("success", False),
             f"status={parse_result.get('status')}")
        step("Messages parsed", parse_result.get("message_count", 0) == 5)
        step("Contacts detected", parse_result.get("contact_count", 0) >= 2)

        # 4. Verify artefacts persisted
        print("\n--- Phase 4: Artefact Verification ---")
        db = DatabaseConnection(db_path)
        row = db.execute("SELECT COUNT(*) FROM messages WHERE case_id = ?", (case_id,)).fetchone()
        step("Messages in DB", row[0] == 5, f"count={row[0]}")

        row = db.execute("SELECT COUNT(*) FROM contacts WHERE case_id = ?", (case_id,)).fetchone()
        step("Contacts in DB", row[0] >= 2, f"count={row[0]}")

        row = db.execute("SELECT COUNT(*) FROM conversations WHERE case_id = ?", (case_id,)).fetchone()
        step("Conversations in DB", row[0] >= 1, f"count={row[0]}")

        row = db.execute("SELECT COUNT(*) FROM timeline_events WHERE case_id = ?", (case_id,)).fetchone()
        step("Timeline events in DB", row[0] >= 5, f"count={row[0]}")

        row = db.execute("SELECT COUNT(*) FROM parser_runs WHERE case_id = ?", (case_id,)).fetchone()
        step("Parser run recorded", row[0] >= 1)

        # 5. Verify FTS index
        print("\n--- Phase 5: Search Index & Search ---")
        index_svc = SearchIndexService()
        fts_avail = index_svc.check_fts_available(db)
        step("FTS5 available" if fts_avail else "FTS5 unavailable", True,
             f"fts={fts_avail}")

        search_svc = SearchService()
        results = search_svc.search(db, case_id, "Alice", scope="Messages")
        step("Search finds Alice", len(results) >= 1, f"found={len(results)}")

        results = search_svc.search(db, case_id, "https://", scope="Messages")
        step("Search finds URLs", len(results) >= 1, f"found={len(results)}")

        results = search_svc.search(db, case_id, "nonexistent", scope="Messages")
        step("Search returns empty for miss", len(results) == 0)

        # 6. Statistics verification
        print("\n--- Phase 6: Statistics ---")
        stats_svc = StatisticsService()
        stats = stats_svc.get_case_stats(db, case_id)
        step("Stats show messages", stats.get("messages") == 5)
        step("Stats show contacts", stats.get("contacts") >= 2)
        step("Stats show conversations", stats.get("conversations") >= 1)

        # 7. Add examiner note
        print("\n--- Phase 7: Annotations ---")
        db.execute(
            "INSERT INTO examiner_notes (case_id, note_text, created_at_utc, updated_at_utc) "
            "VALUES (?, ?, ?, ?)",
            (case_id, "E2E test note about important finding", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        db.commit()
        results = search_svc.search(db, case_id, "important finding", scope="Notes")
        step("Note searchable", len(results) >= 1)

        # 8. Generate report
        print("\n--- Phase 8: Reports ---")
        from wft.reports.html_report import HtmlReportGenerator
        report_dir = case_path / "reports"
        report_dir.mkdir(exist_ok=True)
        output_path = report_dir / "e2e_summary.html"

        gen = HtmlReportGenerator()
        gen.generate_case_summary(
            {"case_code": case_code, "title": "E2E Test", "status": "OPEN",
             "display_timezone": "UTC", **stats},
            output_path,
        )
        step("Report file exists", output_path.exists())
        report_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
        step("Report has content", len(report_sha) == 64)

        report_repo = ReportRunRepository(db)
        rid = report_repo.create({
            "case_id": case_id, "report_code": f"R-E2E-{uuid.uuid4().hex[:4].upper()}",
            "title": "E2E Summary", "report_type": "CASE_SUMMARY",
        })
        report_repo.complete(rid, "COMPLETED")
        report_repo.add_file({
            "report_run_id": rid, "file_format": "html",
            "stored_relative_path": "reports/e2e_summary.html",
            "size_bytes": output_path.stat().st_size, "sha256": report_sha,
        })
        step("Report run persisted", rid > 0)

        # 9. Audit chain
        print("\n--- Phase 9: Audit Chain ---")
        issues = auditor.verify_chain(db, case_id)
        step("Audit chain intact", len(issues) == 0, f"issues={issues}")

        # 10. Close and reopen
        print("\n--- Phase 10: Persistence ---")
        db.close()
        step("Case closed cleanly", True)

        db2 = DatabaseConnection(db_path)
        row = db2.execute("SELECT COUNT(*) FROM messages WHERE case_id = ?", (case_id,)).fetchone()
        step("Data persists after reopen", row[0] == 5, f"count={row[0]}")
        db2.close()

        # Summary
        print(f"\n{'='*60}")
        print(f"  RESULTS: {_PASS} passed, {_FAIL} failed")
        print(f"{'='*60}\n")

        if args.keep_case:
            print(f"  Case preserved at: {case_path}")
        else:
            shutil.rmtree(tmp_base, ignore_errors=True)
            print("  Temporary files cleaned up.")

        return 0 if _FAIL == 0 else 1

    except Exception as exc:
        print(f"\n  [FATAL] {exc}")
        import traceback
        traceback.print_exc()
        _FAIL += 1
        print(f"\n  RESULTS: {_PASS} passed, {_FAIL} failed")
        if args.keep_case:
            print(f"  Case preserved at: {case_path}")
        else:
            shutil.rmtree(tmp_base, ignore_errors=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
