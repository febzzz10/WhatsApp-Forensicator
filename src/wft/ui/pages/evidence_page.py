from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QGroupBox, QComboBox, QSplitter,
    QTabWidget,
)
from PySide6.QtCore import Qt, QThreadPool

from wft.bootstrap import Container
from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, StatusBadge, EvidenceBanner, EmptyState
from wft.ui.workers.import_export_worker import (
    EvidenceImportWorker,
    EvidenceParseWorker,
)
from wft.ui.workers.worker_base import CancellationToken
from wft.application.services.evidence_service import EvidenceRepository


class EvidencePage(QWidget):
    def __init__(self, container: Container, ctx: ActiveCaseContext, main_window=None) -> None:
        super().__init__()
        self._container = container
        self._ctx = ctx
        self._main_window = main_window
        self._thread_pool = QThreadPool.globalInstance()
        self._active_worker = None
        self._active_token: Optional[CancellationToken] = None
        self._operation_case_id: Optional[int] = None
        self._closed = False
        self._ctx.case_changed.connect(self._on_case_changed)
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

        self._cancel_btn = NeonButton("Cancel Operation", "danger")
        self._cancel_btn.setAccessibleName("Cancel Evidence Import")
        self._cancel_btn.setToolTip("Cancel Evidence Import")
        self._cancel_btn.clicked.connect(self._cancel_operation)
        self._cancel_btn.setVisible(False)
        left_layout.addWidget(self._cancel_btn)

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
        self._closed = False
        if self._ctx.is_active:
            self._refresh_list()

    def closeEvent(self, event) -> None:
        self._closed = True
        self._cancel_operation()
        super().closeEvent(event)

    def _on_case_changed(self, _case_id: int, _case_path: str) -> None:
        self._cancel_operation()

    def _operation_is_current(self) -> bool:
        return (
            not self._closed
            and
            self._ctx.is_active
            and self._operation_case_id == self._ctx.case_id
            and self._ctx.case_path is not None
        )

    def _begin_operation(self, worker, case_id: int) -> None:
        if self._active_worker is not None:
            QMessageBox.information(self, "Operation Active", "An evidence operation is already running.")
            return
        self._active_worker = worker
        self._active_token = worker._token
        self._operation_case_id = case_id
        worker.signals.started.connect(self._on_worker_started)
        worker.signals.progress.connect(self._on_worker_progress)
        worker.signals.finished.connect(self._on_worker_finished)
        worker.signals.error.connect(self._on_worker_error)
        worker.signals.cancelled.connect(self._on_worker_cancelled)
        self._cancel_btn.setVisible(True)
        self._parse_btn.setEnabled(False)
        self._thread_pool.start(worker)

    def _finish_operation(self) -> None:
        self._active_worker = None
        self._active_token = None
        self._operation_case_id = None
        self._cancel_btn.setVisible(False)
        self._parse_btn.setEnabled(self._evidence_list.currentRow() >= 0)

    def _cancel_operation(self) -> None:
        if self._active_worker is not None:
            self._active_worker.cancel()

    def _on_worker_started(self) -> None:
        if self._operation_is_current():
            self._banner.setText("Evidence operation in progress...")
            self._banner.setVisible(True)

    def _on_worker_progress(self, message: str, _current: int, _total: int) -> None:
        if self._operation_is_current():
            self._banner.setText(message)
            self._banner.setVisible(True)

    def _on_worker_finished(self, result: object) -> None:
        current = self._operation_is_current()
        self._finish_operation()
        if not current:
            return
        self._refresh_list()
        if isinstance(result, dict) and "imported_file_count" in result:
            if result.get("status") in {"FAILED", "CANCELLED"}:
                QMessageBox.warning(
                    self,
                    "Directory Import Incomplete",
                    "; ".join(result.get("warnings", [])) or "The directory import did not complete.",
                )
                return
            QMessageBox.information(
                self,
                "Directory Import Complete",
                f"Imported {result['imported_file_count']} files; "
                f"parsed {result.get('parsed_file_count', 0)}; "
                f"unsupported {result.get('unsupported_file_count', 0)}; "
                f"skipped {result.get('skipped_file_count', 0)}.",
            )
            return
        if isinstance(result, dict) and "parse" in result:
            parse_result = result["parse"]
            import_result = result["import"]
            QMessageBox.information(
                self,
                "Import Complete",
                f"Imported and parsed {parse_result.get('message_count', 0)} messages.",
            )
        elif isinstance(result, dict) and result.get("success"):
            QMessageBox.information(
                self,
                "Parse Complete",
                f"Parsed {result.get('message_count', 0)} messages, "
                f"{result.get('contact_count', 0)} contacts, "
                f"{result.get('call_count', 0)} calls.",
            )

    def _on_worker_error(self, message: str) -> None:
        current = self._operation_is_current()
        self._finish_operation()
        if current:
            QMessageBox.critical(self, "Evidence Operation Failed", message)
            self._refresh_list()

    def _on_worker_cancelled(self) -> None:
        current = self._operation_is_current()
        self._finish_operation()
        if current:
            self._refresh_list()
            QMessageBox.information(self, "Operation Cancelled", "The evidence operation was cancelled.")

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

        source_type = self._source_type.currentText()
        if source_type in ("Media directory", "Generic evidence folder"):
            source_path = QFileDialog.getExistingDirectory(self, "Select Evidence Source")
        else:
            source_path, _ = QFileDialog.getOpenFileName(self, "Select Evidence Source")
        if not source_path:
            return

        source_path_obj = Path(source_path)
        src_type = source_type
        source_type_map = {
            "WhatsApp chat export ZIP": "WHATSAPP_EXPORT_ZIP",
            "WhatsApp text export": "WHATSAPP_TEXT_EXPORT",
            "SQLite database": "SQLITE_DATABASE",
            "SQLite database with WAL/SHM": "SQLITE_DATABASE_PACKAGE",
            "Media directory": "MEDIA_DIRECTORY",
            "Generic evidence folder": "GENERIC_FILES",
        }

        worker = EvidenceImportWorker(
            evidence_service=self._container.evidence_service,
            audit_service=self._container.audit_service,
            parse_service=self._container.parse_service,
            case_id=self._ctx.case_id,
            case_dir=self._ctx.case_path,
            db_path=self._ctx.db_path,
            source_path=source_path_obj,
            source_type=source_type_map.get(src_type, "GENERIC_FILES"),
            acquisition_method="USER_PROVIDED",
            source_is_directory=source_type in ("Media directory", "Generic evidence folder"),
        )
        self._begin_operation(worker, self._ctx.case_id)

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
            file_row = self._ctx.get_db().execute(
                "SELECT id, stored_relative_path FROM evidence_files "
                "WHERE evidence_item_id = ? ORDER BY id LIMIT 1",
                (item["id"],),
            ).fetchone()
            if file_row is None:
                raise ValueError(f"No evidence file registered for item {item['id']}")
            source_file_id = int(file_row[0])
            file_path = self._ctx.case_path / str(file_row[1])
            if not file_path.exists():
                QMessageBox.warning(self, "File Not Found", f"Cannot locate evidence file at {file_path}")
                return

            worker = EvidenceParseWorker(
                parse_service=self._container.parse_service,
                audit_service=self._container.audit_service,
                case_id=self._ctx.case_id,
                evidence_item_id=item["id"],
                source_file_id=source_file_id,
                source_path=file_path,
                db_path=self._ctx.db_path,
                case_dir=self._ctx.case_path,
            )
            self._begin_operation(worker, self._ctx.case_id)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Parse failed:\n{exc}")
