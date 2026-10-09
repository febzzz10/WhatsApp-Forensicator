from pathlib import Path
from unittest.mock import MagicMock

from wft.ui.workers.import_export_worker import EvidenceImportWorker
from wft.ui.workers.worker_base import CancellationToken


def test_evidence_import_worker_exposes_progress_and_completion_signals() -> None:
    worker = EvidenceImportWorker(
        evidence_service=MagicMock(),
        audit_service=MagicMock(),
        parse_service=MagicMock(),
        case_id=1,
        case_dir=Path("case"),
        db_path=Path("case/case.db"),
        source_path=Path("source.txt"),
        source_type="WHATSAPP_TEXT_EXPORT",
        acquisition_method="USER_PROVIDED",
        token=CancellationToken(),
    )

    assert hasattr(worker.signals, "progress")
    assert hasattr(worker.signals, "cancelled")
    assert hasattr(worker, "cancel")


def test_evidence_import_worker_cancellation_emits_cancelled() -> None:
    token = CancellationToken()
    worker = EvidenceImportWorker(
        evidence_service=MagicMock(),
        audit_service=MagicMock(),
        parse_service=MagicMock(),
        case_id=1,
        case_dir=Path("case"),
        db_path=Path("case/case.db"),
        source_path=Path("source.txt"),
        source_type="WHATSAPP_TEXT_EXPORT",
        acquisition_method="USER_PROVIDED",
        token=token,
    )
    cancelled = []
    worker.signals.cancelled.connect(lambda: cancelled.append(True))

    worker.cancel()
    worker.run()

    assert cancelled == [True]
