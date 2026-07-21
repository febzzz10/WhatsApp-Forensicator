from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QGroupBox, QComboBox, QSplitter,
    QTextEdit, QTabWidget, QFrame,
)
from PySide6.QtCore import Qt, QThread

from wft.bootstrap import Container
from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, StatusBadge, EvidenceBanner, EmptyState
from wft.ui.workers.parse_worker import ParseEvidenceWorker
from wft.ui.workers.worker_base import BackgroundWorker, CancellationToken, WorkerSignals
from wft.infrastructure.database.uow import UnitOfWork
from wft.application.services.evidence_service import EvidenceRepository
from wft.application.services.audit_service import AuditService


class EvidencePage(QWidget):
    def __init__(self, container: Container, ctx: ActiveCaseContext, main_window=None) -> None:
        super().__init__()
        self._container = container
        self._ctx = ctx
        self._main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = PageHeader("Evidence", "Import, verify and manage evidence sources")
        layout.addWidget(header)

        import_group = QGroupBox("Import New Evidence")
        import_layout = QVBoxLayout()
        import_layout.setSpacing(8)

        type_row = QHBoxLayout()
        self._source_type = QComboBox()
        self._source_type.addItems([
            "WhatsApp chat export ZIP",
            "WhatsApp text export",
            "SQLite database",
            "SQLite database with WAL/SHM",
            "Media directory",
            "Generic evidence folder",
        ])
        type_row.addWidget(QLabel("Source Type:"))
        type_row.addWidget(self._source_type, 1)
        import_layout.addLayout(type_row)

        self._parse_after_import = QLabel("\u2713 Will attempt to parse after import")
        self._parse_after_import.setStyleSheet("color: #46A568; font-size: 11px; padding: 2px 8px;")
        import_layout.addWidget(self._parse_after_import)

        select_btn = NeonButton("Select and Import", "primary")
        select_btn.clicked.connect(self._on_select_source)
        import_layout.addWidget(select_btn)

        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

        self._banner = EvidenceBanner("No evidence imported yet.", "info")
        self._banner.setVisible(False)
        layout.addWidget(self._banner)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Imported Evidence:"))
        self._evidence_list = QListWidget()
        self._evidence_list.setMinimumWidth(300)
        self._evidence_list.currentRowChanged.connect(self._on_evidence_selected)
        left_layout.addWidget(self._evidence_list, 1)

        self._parse_btn = NeonButton("Parse Selected", "secondary")
        self._parse_btn.clicked.connect(self._on_parse_selected)
        self._parse_btn.setEnabled(False)
        left_layout.addWidget(self._parse_btn)

        splitter.addWidget(left_panel)

        self._detail_tabs = QTabWidget()
        self._detail_tabs.setVisible(False)
        details_config = [
            ("Overview", "Select an evidence item to view details."),
            ("Files", "No files registered."),
            ("Hashes", "No hashes recorded."),
            ("Parser Runs", "No parser runs."),
            ("Provenance", "Provenance metadata."),
        ]
        self._detail_labels = {}
        for tab_name, placeholder in details_config:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            label = EmptyState(placeholder)
            tab_layout.addWidget(label)
            self._detail_tabs.addTab(tab, tab_name)
            self._detail_labels[tab_name] = label
        splitter.addWidget(self._detail_tabs)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, 1)

    def on_activated(self) -> None:
        if self._ctx.is_active:
            self._refresh_list()

    def _refresh_list(self) -> None:
        self._evidence_list.clear()
        if not self._ctx.is_active:
            self._banner.setVisible(True)
            return
        try:
            repo = EvidenceRepository(self._ctx.get_db())
            items = repo.get_items_for_case(self._ctx.case_id)
            for item in items:
                text = f"[{item['evidence_code']}] {item['title']} \u2014 {item['state']}"
                QListWidgetItem(text, self._evidence_list)
            self._banner.setVisible(len(items) == 0)
            self._detail_tabs.setVisible(len(items) > 0)
        except Exception as exc:
            self._container.log.error(f"Evidence list error: {exc}")

    def _on_evidence_selected(self, row: int) -> None:
        self._parse_btn.setEnabled(row >= 0)
        if row < 0:
            return
        try:
            repo = EvidenceRepository(self._ctx.get_db())
            items = repo.get_items_for_case(self._ctx.case_id)
            if row < len(items):
                item = items[row]
                overview = self._detail_labels.get("Overview")
                if overview:
                    overview.set_title(
                        f"Code: {item['evidence_code']}\n"
                        f"Title: {item['title']}\n"
                        f"State: {item['state']}\n"
                        f"Source: {item['source_type']}\n"
                        f"Acquisition: {item['acquisition_method']}\n"
                        f"Imported: {item['imported_at_utc']}"
                    )
        except Exception:
            pass

    def _on_select_source(self) -> None:
        if not self._ctx.is_active:
            QMessageBox.warning(self, "No Case", "Open a case first.")
            return

        source_path = QFileDialog.getExistingDirectory(self, "Select Evidence Source")
        if not source_path:
            return

        source_path_obj = Path(source_path)
        src_type = self._source_type.currentText()
        source_type_map = {
            "WhatsApp chat export ZIP": "WHATSAPP_EXPORT_ZIP",
            "WhatsApp text export": "WHATSAPP_TEXT_EXPORT",
            "SQLite database": "SQLITE_DATABASE",
            "SQLite database with WAL/SHM": "SQLITE_DATABASE_PACKAGE",
            "Media directory": "MEDIA_DIRECTORY",
            "Generic evidence folder": "GENERIC_FILES",
        }

        try:
            db = self._ctx.get_db()
            repo = EvidenceRepository(db)
            items = repo.get_items_for_case(self._ctx.case_id)
            evidence_code = f"E{len(items)+1:04d}"

            result = self._container.evidence_service.import_file(
                db=db,
                case_id=self._ctx.case_id,
                evidence_code=evidence_code,
                title=source_path_obj.name,
                source_type=source_type_map.get(src_type, "GENERIC_FILES"),
                acquisition_method="USER_PROVIDED",
                source_path=source_path_obj,
            )

            audit = AuditService()
            audit.record_event(
                db, self._ctx.case_id,
                "EVIDENCE_IMPORTED",
                f"Imported {source_path_obj.name} as {evidence_code}",
            )
            db.commit()

            QMessageBox.information(
                self, "Success",
                f"Evidence {evidence_code} imported.\nSHA-256: {result['sha256'][:16]}..."
            )
            self._refresh_list()

            self._try_auto_parse(source_path_obj, result["item_id"], result.get("file_id", 1))

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Import failed:\n{exc}")

    def _try_auto_parse(self, source_path: Path, evidence_item_id: int, source_file_id: int) -> None:
        try:
            worker = ParseEvidenceWorker(
                self._container.parse_service,
                AuditService(),
                self._ctx.case_path,
            )
            result = worker.run(
                case_id=self._ctx.case_id,
                evidence_item_id=evidence_item_id,
                source_file_id=source_file_id,
                source_path=source_path,
                db_path=self._ctx.db_path,
                display_timezone="UTC",
            )
            if result.get("success"):
                QMessageBox.information(
                    self, "Parse Complete",
                    f"Parsed {result.get('message_count', 0)} messages, "
                    f"{result.get('contact_count', 0)} contacts, "
                    f"{result.get('call_count', 0)} calls."
                )
            else:
                QMessageBox.information(
                    self, "Parse Note",
                    f"Auto-parse: {result.get('status', 'UNSUPPORTED')}. "
                    f"{result.get('error', 'No parser available')}"
                )
            self._refresh_list()
        except Exception as exc:
            self._container.log.warning(f"Auto-parse failed: {exc}")

    def _on_parse_selected(self) -> None:
        row = self._evidence_list.currentRow()
        if row < 0 or not self._ctx.is_active:
            return
        try:
            repo = EvidenceRepository(self._ctx.get_db())
            items = repo.get_items_for_case(self._ctx.case_id)
            if row >= len(items):
                return
            item = items[row]
            from wft.infrastructure.database.artefact_repositories import ParserRunRepository

            run_repo = ParserRunRepository(self._ctx.get_db())
            file_path = self._ctx.case_path / item.get("stored_relative_path", "")
            if not file_path.exists():
                QMessageBox.warning(self, "File Not Found", f"Cannot locate evidence file at {file_path}")
                return

            worker = ParseEvidenceWorker(
                self._container.parse_service,
                AuditService(),
                self._ctx.case_path,
            )
            result = worker.run(
                case_id=self._ctx.case_id,
                evidence_item_id=item["id"],
                source_file_id=1,
                source_path=file_path,
                db_path=self._ctx.db_path,
                display_timezone="UTC",
            )
            if result.get("success"):
                QMessageBox.information(
                    self, "Parse Complete",
                    f"Parser: {result.get('parser_id', 'unknown')}\n"
                    f"Messages: {result.get('message_count', 0)}\n"
                    f"Contacts: {result.get('contact_count', 0)}\n"
                    f"Calls: {result.get('call_count', 0)}"
                )
            else:
                QMessageBox.warning(
                    self, "Parse Failed",
                    result.get("error", "Unknown error")
                )
            self._refresh_list()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Parse failed:\n{exc}")
