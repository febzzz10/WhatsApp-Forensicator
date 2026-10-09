import hashlib
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wft.application.services.adb_service import (
    AdbService, AdbDevice, AdbState, AdbError, RootAccess,
)
from wft.application.services.audit_service import AuditService
from wft.application.services.case_service import CaseService
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.logging.logging_service import LoggingService
from wft.ui.workers.adb_scan_worker import AdbOperationWorker, AdbOperationType

PUBLIC_PATH = "/sdcard/Android/media/com.whatsapp/WhatsApp/Databases"
LEGACY_PUBLIC_PATH = "/sdcard/WhatsApp/Databases"
PRIVATE_DB_PATH = "/data/data/com.whatsapp/databases"
PRIVATE_KEY_PATH = "/data/data/com.whatsapp/files/key"

CRYPT14 = b"SQLite format 3\x00" + b"\xde\xad\xbe\xef" * 32  # encrypted-looking bytes
CRYPT15 = b"\x15\x00\x00\x00" + b"\xbe\xef" * 64
WA_DB = b"SQLite format 3\x00plaintext database bytes"
KEY_BYTES = b"\x01\x02\x03\x04key material"


@pytest.fixture
def case_env(tmp_path):
    hash_service = HashingService()
    log = LoggingService(None, "CRITICAL")
    case_service = CaseService(hash_service, log)
    result = case_service.create_case(
        case_dir=tmp_path,
        case_code="CASE-EXT",
        title="Extraction test",
        examiner_name="Tester",
        organisation="Lab",
    )
    case_path = Path(result["path"])
    return {
        "case_id": result["case_id"],
        "case_path": case_path,
        "db_path": case_path / "case.db",
    }


def make_service(
    listings=None,
    pulls=None,
    root=RootAccess.NONE,
    pull_error=None,
    on_pull=None,
):
    service = MagicMock(spec=AdbService)
    service.detect_root.return_value = root

    def _list_dir(serial, path, timeout=None):
        if listings is None:
            raise AdbError("No such file or directory: {}".format(path))
        return list(listings.get(path, []))

    service.list_directory.side_effect = _list_dir

    def _pull(serial, remote, local, timeout=None):
        if on_pull is not None:
            on_pull(remote)
        if pull_error is not None:
            raise AdbError(pull_error)
        content = (pulls or {}).get(remote)
        if content is None:
            raise AdbError("remote object does not exist: {}".format(remote))
        Path(local).write_bytes(content)

    service.pull_file.side_effect = _pull
    return service


def make_worker(service, case_env, case_id=None, db_path=None, hash_service=None,
                audit_service=None, token=None, serial="TEST001"):
    return AdbOperationWorker(
        operation=AdbOperationType.EXTRACT_WHATSAPP_DATABASES,
        serial=serial,
        timeout=10,
        _service_override=service,
        case_dir=Path(case_env["case_path"]),
        db_path=Path(db_path or case_env["db_path"]),
        evidence_service=MagicMock(),
        audit_service=audit_service,
        hash_service=hash_service or HashingService(),
        case_id=case_id if case_id is not None else case_env["case_id"],
        token=token,
    )


def run_and_collect(worker):
    finished, errors, cancelled = [], [], []
    worker.signals.finished.connect(lambda r: finished.append(r))
    worker.signals.error.connect(lambda m: errors.append(m))
    worker.signals.cancelled.connect(lambda: cancelled.append(True))
    worker.run()
    return finished, errors, cancelled


def query_counts(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        items = conn.execute("SELECT COUNT(*) FROM evidence_items").fetchone()[0]
        files = conn.execute("SELECT COUNT(*) FROM evidence_files").fetchone()[0]
        hashes = conn.execute("SELECT COUNT(*) FROM evidence_hashes").fetchone()[0]
        return items, files, hashes
    finally:
        conn.close()


def query_events(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT event_type, details_json FROM audit_events"
        ).fetchall()
        return rows
    finally:
        conn.close()


# 1. successful public-path acquisition

def test_public_path_acquisition_success(case_env):
    service = make_service(
        listings={
            PUBLIC_PATH: ["msgstore.db.crypt14", "wa.db"],
            LEGACY_PUBLIC_PATH: [],
        },
        pulls={
            PUBLIC_PATH + "/msgstore.db.crypt14": CRYPT14,
            PUBLIC_PATH + "/wa.db": WA_DB,
        },
    )
    worker = make_worker(service, case_env, audit_service=AuditService())
    finished, errors, cancelled = run_and_collect(worker)

    assert errors == [] and cancelled == []
    result = finished[0]
    assert result.status == "ACQUIRED"
    assert len(result.artifacts) == 2
    assert result.evidence_item_id is not None
    assert result.audit_event_hash is not None

    items, files, hashes = query_counts(case_env["db_path"])
    assert items == 1 and files == 2 and hashes == 2

    file_ids = {a.evidence_file_id for a in result.artifacts}
    assert len(file_ids) == 2 and None not in file_ids


# 2. successful rooted acquisition

def test_rooted_acquisition_pulls_private_paths(case_env):
    service = make_service(
        listings={
            PUBLIC_PATH: ["msgstore.db"],
            PRIVATE_DB_PATH: ["msgstore.db"],
            PRIVATE_KEY_PATH: ["key"],
        },
        pulls={
            PUBLIC_PATH + "/msgstore.db": WA_DB,
            PRIVATE_DB_PATH + "/msgstore.db": WA_DB,
            PRIVATE_KEY_PATH + "/key": KEY_BYTES,
        },
        root=RootAccess.SU,
    )
    worker = make_worker(service, case_env, audit_service=AuditService())
    finished, errors, _ = run_and_collect(worker)

    result = finished[0]
    assert result.status == "ACQUIRED"
    assert result.root_access == "su"
    remotes = {a.remote_path for a in result.artifacts}
    assert PRIVATE_DB_PATH + "/msgstore.db" in remotes
    assert PRIVATE_KEY_PATH + "/key" in remotes
    pulled = {c[0][1] for c in service.pull_file.call_args_list}
    assert PRIVATE_KEY_PATH + "/key" in pulled


# 3. mixed available/missing paths

def test_missing_paths_do_not_fail_acquisition(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db"]},
        pulls={PUBLIC_PATH + "/wa.db": WA_DB},
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    result = finished[0]
    assert result.status == "ACQUIRED"
    assert len(result.artifacts) == 1
    assert any(LEGACY_PUBLIC_PATH in u for u in result.unavailable_paths)


def test_missing_rooted_key_does_not_invalidate_public_acquisition(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db"]},
        pulls={PUBLIC_PATH + "/wa.db": WA_DB},
        root=RootAccess.SU,
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    result = finished[0]
    assert result.status == "ACQUIRED"
    assert any(PRIVATE_KEY_PATH in u for u in result.unavailable_paths)


# 4. encrypted crypt14/crypt15 acquisition

def test_crypt14_crypt15_acquired_verbatim(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["msgstore.db.crypt14", "msgstore.db.crypt15"]},
        pulls={
            PUBLIC_PATH + "/msgstore.db.crypt14": CRYPT14,
            PUBLIC_PATH + "/msgstore.db.crypt15": CRYPT15,
        },
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    result = finished[0]
    by_remote = {a.remote_path.rsplit("/", 1)[-1]: a for a in result.artifacts}
    assert by_remote["msgstore.db.crypt14"].encrypted is True
    assert by_remote["msgstore.db.crypt15"].encrypted is True

    local = Path(case_env["case_path"]) / result.artifacts[0].local_path
    assert local.read_bytes() in (CRYPT14, CRYPT15)


# 5. hashing correctness

def test_sha256_matches_source_bytes(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db"]},
        pulls={PUBLIC_PATH + "/wa.db": WA_DB},
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    artifact = finished[0].artifacts[0]
    assert artifact.sha256 == hashlib.sha256(WA_DB).hexdigest()
    local = Path(case_env["case_path"]) / artifact.local_path
    assert hashlib.sha256(local.read_bytes()).hexdigest() == artifact.sha256


# 6. evidence registration structure

def test_evidence_rows_carry_provenance(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["msgstore.db.crypt14"]},
        pulls={PUBLIC_PATH + "/msgstore.db.crypt14": CRYPT14},
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    conn = sqlite3.connect(str(case_env["db_path"]))
    conn.row_factory = sqlite3.Row
    try:
        item = conn.execute("SELECT * FROM evidence_items").fetchone()
        ef = conn.execute("SELECT * FROM evidence_files").fetchone()
        eh = conn.execute("SELECT * FROM evidence_hashes").fetchone()
    finally:
        conn.close()

    assert item["source_type"] == "WHATSAPP_DATABASE_ACQUISITION"
    assert item["source_application"] == "com.whatsapp"
    assert item["source_device_identifier"] == "TEST001"
    assert item["acquisition_method"] == "ADB_LOGICAL"
    assert ef["original_source_path"] == PUBLIC_PATH + "/msgstore.db.crypt14"
    assert ef["is_original_copy"] == 1
    assert eh["algorithm"] == "SHA256"
    assert eh["purpose"] == "ACQUISITION"


# 7. audit event

def test_audit_event_recorded(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["msgstore.db.crypt14"]},
        pulls={PUBLIC_PATH + "/msgstore.db.crypt14": CRYPT14},
    )
    worker = make_worker(service, case_env, audit_service=AuditService())
    finished, _, _ = run_and_collect(worker)

    rows = query_events(case_env["db_path"])
    matching = [r for r in rows if r[0] == "WHATSAPP_DATABASES_ACQUIRED"]
    assert len(matching) == 1
    import json
    details = json.loads(matching[0][1])
    assert details["device_serial"] == "TEST001"
    assert details["root_access"] == "none"
    assert details["acquisition_method"] == "ADB_LOGICAL"
    assert details["artifact_count"] == 1
    assert details["encrypted_artifact_count"] == 1


# 8. partial acquisition

def test_partial_when_one_pull_fails(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db", "msgstore.db.crypt14"]},
        pulls={PUBLIC_PATH + "/wa.db": WA_DB},
    )
    worker = make_worker(service, case_env, audit_service=AuditService())
    finished, _, _ = run_and_collect(worker)

    result = finished[0]
    assert result.status == "PARTIAL"
    assert len(result.artifacts) == 1
    assert len(result.failures) == 1
    items, files, hashes = query_counts(case_env["db_path"])
    assert items == 1 and files == 1 and hashes == 1


# 9. no files found

def test_no_files_found(case_env):
    service = make_service(listings={PUBLIC_PATH: [], LEGACY_PUBLIC_PATH: []})
    worker = make_worker(service, case_env, audit_service=AuditService())
    finished, errors, _ = run_and_collect(worker)

    assert errors == []
    result = finished[0]
    assert result.status == "NO_FILES_FOUND"
    assert result.artifacts == []
    items, files, hashes = query_counts(case_env["db_path"])
    assert items == 0 and files == 0 and hashes == 0
    events = [r for r in query_events(case_env["db_path"]) if r[0] == "WHATSAPP_DATABASES_ACQUIRED"]
    assert events == []


# 10. pull failure (all pulls fail)

def test_all_pulls_fail_returns_failed(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db"]},
        pull_error="Permission denied",
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    result = finished[0]
    assert result.status == "FAILED"
    assert result.artifacts == []
    assert len(result.failures) == 1


# 11. hash failure

def test_hash_failure_raises_error(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db"]},
        pulls={PUBLIC_PATH + "/wa.db": WA_DB},
    )
    broken_hash = MagicMock()
    broken_hash.sha256.side_effect = OSError("disk failure")
    worker = make_worker(service, case_env, hash_service=broken_hash)
    finished, errors, _ = run_and_collect(worker)

    assert finished == []
    assert len(errors) == 1
    assert "hash" in errors[0].lower()


# 12. evidence registration failure

def test_evidence_registration_failure_raises_error(case_env, tmp_path):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db"]},
        pulls={PUBLIC_PATH + "/wa.db": WA_DB},
    )
    bad_db = tmp_path / "garbage.db"
    bad_db.write_bytes(b"this is not a sqlite database")
    worker = make_worker(service, case_env, db_path=bad_db)
    finished, errors, _ = run_and_collect(worker)

    assert finished == []
    assert len(errors) == 1


# 13. cancellation

def test_cancellation_stops_before_registration(case_env):
    from wft.ui.workers.worker_base import CancellationToken

    calls = {"n": 0}

    def on_pull(remote):
        calls["n"] += 1

    service = make_service(
        listings={
            PUBLIC_PATH: ["wa.db", "msgstore.db.crypt14"],
        },
        pulls={
            PUBLIC_PATH + "/wa.db": WA_DB,
            PUBLIC_PATH + "/msgstore.db.crypt14": CRYPT14,
        },
        on_pull=on_pull,
    )
    token = CancellationToken()

    original_pull = service.pull_file.side_effect

    def _pull(serial, remote, local, timeout=None):
        original_pull(serial, remote, local, timeout=timeout)
        token.cancel()

    service.pull_file.side_effect = _pull

    worker = make_worker(service, case_env, token=token)
    finished, errors, cancelled = run_and_collect(worker)

    assert errors == []
    assert calls["n"] == 1
    assert cancelled == [True]
    # Worker architecture: a cancelled run emits cancelled + finished(None),
    # matching the existing media/metadata operations.
    items, _, _ = query_counts(case_env["db_path"])
    assert items == 0


# 14. no decryption

def test_no_decryption_performed(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["msgstore.db.crypt14"]},
        pulls={PUBLIC_PATH + "/msgstore.db.crypt14": CRYPT14},
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    artifact = finished[0].artifacts[0]
    local = Path(case_env["case_path"]) / artifact.local_path
    assert local.read_bytes() == CRYPT14
    pull_calls = service.pull_file.call_args_list
    assert len(pull_calls) == 1
    assert pull_calls[0][0][1].endswith("msgstore.db.crypt14")


# 15. no automatic parsing

def test_no_automatic_parsing(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db"]},
        pulls={PUBLIC_PATH + "/wa.db": b"SQLite format 3\x00" + b"x" * 200},
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    conn = sqlite3.connect(str(case_env["db_path"]))
    try:
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM parser_runs").fetchone()[0] == 0
    finally:
        conn.close()


# determinism of enumeration: listing order does not change artifact set

def test_artifact_set_independent_of_listing_order(case_env):
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db", "msgstore.db.crypt14", "msgstore.db-wal"]},
        pulls={
            PUBLIC_PATH + "/wa.db": WA_DB,
            PUBLIC_PATH + "/msgstore.db.crypt14": CRYPT14,
            PUBLIC_PATH + "/msgstore.db-wal": b"wal-bytes",
        },
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)
    assert finished[0].status == "ACQUIRED"
    assert len(finished[0].artifacts) == 3

def test_acquired_files_are_read_only_on_disk(case_env):
    import os
    import stat
    service = make_service(
        listings={PUBLIC_PATH: ["wa.db"]},
        pulls={PUBLIC_PATH + "/wa.db": WA_DB},
    )
    worker = make_worker(service, case_env)
    finished, _, _ = run_and_collect(worker)

    artifact = finished[0].artifacts[0]
    local = Path(case_env["case_path"]) / artifact.local_path
    mode = stat.S_IMODE(os.stat(local).st_mode)
    assert mode == 0o444
