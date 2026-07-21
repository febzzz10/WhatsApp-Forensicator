from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout, QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, StatisticCard, EvidenceBanner, EmptyState
from wft.infrastructure.database.artefact_repositories import AuditEventRepository
from wft.application.services.audit_service import AuditService


class AuditPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Audit Log", "Tamper-evident audit event chain")
        layout.addWidget(header)

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(8)
        self._kpi_cards = {}
        kpi_labels = ["Total Events", "Verified Chain", "Warnings", "Critical Events", "Last Verification"]
        for i, label in enumerate(kpi_labels):
            card = StatisticCard(label, "\u2014")
            self._kpi_cards[label] = card
            kpi_grid.addWidget(card, 0, i)
        layout.addLayout(kpi_grid)

        controls = QHBoxLayout()
        verify_btn = NeonButton("Verify Hash Chain", "secondary")
        verify_btn.clicked.connect(self._on_verify)
        controls.addWidget(verify_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self._banner = EvidenceBanner("Audit chain intact", "verified")
        layout.addWidget(self._banner)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Seq", "Time", "Examiner", "Action",
            "Component", "Object", "Verification", "Hash"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table, 1)

    def on_activated(self) -> None:
        if self._ctx.is_active:
            self._refresh()

    def _refresh(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            repo = AuditEventRepository(self._ctx.get_db())
            events = repo.list_for_case(self._ctx.case_id)
            self._populate_table(events)

            from wft.application.services.statistics_service import StatisticsService
            stats = StatisticsService().get_audit_stats(self._ctx.get_db(), self._ctx.case_id)
            self._kpi_cards["Total Events"].set_value(str(stats.get("total", 0)))
            self._kpi_cards["Critical Events"].set_value(str(stats.get("critical", 0)))
        except Exception:
            pass

    def _populate_table(self, events: list) -> None:
        self._table.setRowCount(len(events))
        for i, e in enumerate(events):
            self._table.setItem(i, 0, QTableWidgetItem(str(e.get("event_sequence", ""))))
            self._table.setItem(i, 1, QTableWidgetItem(e.get("occurred_at_utc", "")))
            self._table.setItem(i, 2, QTableWidgetItem(str(e.get("examiner_id", ""))))
            self._table.setItem(i, 3, QTableWidgetItem(e.get("event_type", "")))
            self._table.setItem(i, 4, QTableWidgetItem(e.get("component_name", "")))
            obj_str = f"{e.get('object_type', '')}:{e.get('object_id', '')}"
            self._table.setItem(i, 5, QTableWidgetItem(obj_str))
            self._table.setItem(i, 6, QTableWidgetItem("\u2713" if e.get("event_hash") else "\u2717"))
            h = e.get("event_hash", "")
            self._table.setItem(i, 7, QTableWidgetItem(h[:12] + "..." if h else ""))

    def _on_verify(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            audit = AuditService()
            issues = audit.verify_chain(self._ctx.get_db(), self._ctx.case_id)
            if issues:
                self._banner.set_text("Audit chain HAS ISSUES")
                self._banner.set_banner_type("hash_mismatch")
                msg = "\n".join(issues)
                QMessageBox.warning(self, "Chain Verification", f"Issues found:\n{msg}")
            else:
                self._banner.set_text("Audit chain intact - all hashes verified")
                self._banner.set_banner_type("verified")
                QMessageBox.information(self, "Chain Verification", "Audit chain is intact.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Verification failed:\n{exc}")
