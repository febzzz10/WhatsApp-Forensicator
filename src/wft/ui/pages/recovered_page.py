from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView,
    QPushButton, QSplitter, QTabWidget, QGridLayout,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, StatisticCard, StatusBadge, EmptyState


class RecoveredPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Recovered Artefacts", "Review and manage recovered data candidates")
        layout.addWidget(header)

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(8)
        self._kpi_cards = {}
        kpi_defs = [
            ("Total", "0"), ("High", "0"), ("Medium", "0"),
            ("Low", "0"), ("Accepted", "0"), ("Rejected", "0"), ("Unresolved", "0"),
        ]
        for i, (label, val) in enumerate(kpi_defs):
            card = StatisticCard(label, val)
            self._kpi_cards[label] = card
            kpi_grid.addWidget(card, 0, i)
        layout.addLayout(kpi_grid)

        controls = QHBoxLayout()
        self._strategy_filter = QComboBox()
        self._strategy_filter.addItems([
            "All Strategies", "WAL Parsing", "Journal Parsing",
            "Freelist Scan", "Page Carving",
        ])
        self._confidence_filter = QComboBox()
        self._confidence_filter.addItems(["All", "HIGH", "MEDIUM", "LOW", "UNRESOLVED"])
        self._strategy_filter.currentTextChanged.connect(self._on_filter)
        self._confidence_filter.currentTextChanged.connect(self._on_filter)
        controls.addWidget(QLabel("Strategy:"))
        controls.addWidget(self._strategy_filter)
        controls.addWidget(QLabel("Confidence:"))
        controls.addWidget(self._confidence_filter)
        controls.addStretch()
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Horizontal)

        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            "Candidate", "Type", "Strategy", "Page",
            "Offset", "Confidence", "Review State", "Source", "Duplicate"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        splitter.addWidget(self._table)

        detail_tabs = QTabWidget()
        tabs = ["Parsed Fields", "Raw Fragment", "Validation Checks", "Provenance", "Duplicate Comparison", "Notes"]
        for tab_name in tabs:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(EmptyState(f"Select a recovered candidate to view {tab_name.lower()}."))
            detail_tabs.addTab(tab, tab_name)
        splitter.addWidget(detail_tabs)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        action_row = QHBoxLayout()
        accept_btn = NeonButton("Accept", "primary")
        accept_btn.clicked.connect(self._on_accept)
        reject_btn = NeonButton("Reject", "destructive")
        reject_btn.clicked.connect(self._on_reject)
        action_row.addWidget(accept_btn)
        action_row.addWidget(reject_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

    def on_activated(self) -> None:
        if self._ctx.is_active:
            self._refresh()

    def _refresh(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            from wft.application.services.statistics_service import StatisticsService
            stats = StatisticsService().get_recovery_stats(self._ctx.get_db(), self._ctx.case_id)
            self._kpi_cards["Total"].set_value(str(stats.get("total", 0)))
            self._kpi_cards["High"].set_value(str(stats.get("high", 0)))
            self._kpi_cards["Medium"].set_value(str(stats.get("medium", 0)))
            self._kpi_cards["Low"].set_value(str(stats.get("low", 0)))
            self._kpi_cards["Accepted"].set_value(str(stats.get("accepted", 0)))
            self._kpi_cards["Rejected"].set_value(str(stats.get("rejected", 0)))
            self._kpi_cards["Unresolved"].set_value(str(stats.get("unresolved", 0)))

            from wft.application.services.recovery_service import RecoveryService
            svc = RecoveryService()
            candidates = svc.get_candidates(
                self._ctx.get_db(), self._ctx.case_id,
                strategy=self._strategy_filter.currentText(),
                confidence=self._confidence_filter.currentText(),
            )
            self._candidates = candidates
            self._populate_table(candidates)
        except Exception:
            self._candidates = []

    def _populate_table(self, candidates: list) -> None:
        self._table.setRowCount(len(candidates))
        for i, c in enumerate(candidates):
            self._table.setItem(i, 0, QTableWidgetItem(c.get("candidate_code", "")))
            self._table.setItem(i, 1, QTableWidgetItem(c.get("candidate_type", "")))
            self._table.setItem(i, 2, QTableWidgetItem(c.get("strategy", "")))
            self._table.setItem(i, 3, QTableWidgetItem(str(c.get("source_page_number", ""))))
            self._table.setItem(i, 4, QTableWidgetItem(str(c.get("source_byte_offset", ""))))
            self._table.setItem(i, 5, QTableWidgetItem(c.get("confidence_level", "")))
            self._table.setItem(i, 6, QTableWidgetItem(c.get("review_status", "UNRESOLVED")))
            self._table.setItem(i, 7, QTableWidgetItem(c.get("recovery_code", "")))
            self._table.setItem(i, 8, QTableWidgetItem(c.get("duplicate_group_key") or ""))

    def _on_filter(self) -> None:
        self._refresh()

    def _on_accept(self) -> None:
        self._update_review("ACCEPTED")

    def _on_reject(self) -> None:
        self._update_review("REJECTED")

    def _update_review(self, status: str) -> None:
        row = self._table.currentRow()
        if row < 0 or not self._ctx.is_active or not hasattr(self, "_candidates") or row >= len(self._candidates):
            return
        try:
            candidate = self._candidates[row]
            from wft.application.services.recovery_service import RecoveryService
            svc = RecoveryService()
            if status == "ACCEPTED":
                svc.accept(self._ctx.get_db(), candidate["id"])
            else:
                svc.reject(self._ctx.get_db(), candidate["id"])
            self._refresh()
        except Exception:
            pass
