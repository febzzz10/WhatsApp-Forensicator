from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QSplitter,
    QTabWidget, QGridLayout,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, StatisticCard, NeonButton, EmptyState
from wft.infrastructure.database.artefact_repositories import CallRepository


class CallsPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Call Analysis", "Historical call records")
        layout.addWidget(header)

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(8)
        self._kpi_cards = {}
        for i, label in enumerate(["Total", "Incoming", "Outgoing", "Missed", "Video", "Duration"]):
            card = StatisticCard(label, "0")
            self._kpi_cards[label] = card
            kpi_grid.addWidget(card, i // 3, i % 3)
        layout.addLayout(kpi_grid)

        filter_row = QHBoxLayout()
        self._type_filter = QComboBox()
        self._type_filter.addItems(["All", "VOICE", "VIDEO", "GROUP_VOICE", "GROUP_VIDEO"])
        self._direction_filter = QComboBox()
        self._direction_filter.addItems(["All", "INCOMING", "OUTGOING", "MISSED", "DECLINED"])
        self._type_filter.currentTextChanged.connect(self._on_filter)
        self._direction_filter.currentTextChanged.connect(self._on_filter)
        filter_row.addWidget(QLabel("Type:"))
        filter_row.addWidget(self._type_filter)
        filter_row.addWidget(QLabel("Direction:"))
        filter_row.addWidget(self._direction_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        splitter = QSplitter(Qt.Horizontal)

        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            "Direction", "Contact", "Peer", "Duration",
            "Timestamp", "Type", "Origin", "Confidence", "Source"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        splitter.addWidget(self._table)

        detail_tabs = QTabWidget()
        tabs = ["Details", "Participants", "Linked Chat", "Timeline", "Notes"]
        for tab_name in tabs:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(EmptyState(f"Select a call to view {tab_name.lower()}."))
            detail_tabs.addTab(tab, tab_name)
        splitter.addWidget(detail_tabs)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

    def on_activated(self) -> None:
        if self._ctx.is_active:
            self._refresh()

    def _refresh(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            from wft.application.services.statistics_service import StatisticsService
            stats = StatisticsService().get_call_stats(self._ctx.get_db(), self._ctx.case_id)
            self._kpi_cards["Total"].set_value(str(stats.get("total", 0)))
            self._kpi_cards["Incoming"].set_value(str(stats.get("incoming", 0)))
            self._kpi_cards["Outgoing"].set_value(str(stats.get("outgoing", 0)))
            self._kpi_cards["Missed"].set_value(str(stats.get("missed", 0)))
            self._kpi_cards["Video"].set_value(str(stats.get("video", 0)))
            self._kpi_cards["Duration"].set_value(stats.get("total_duration", "0:00"))
            self._load_calls()
        except Exception:
            pass

    def _load_calls(self) -> None:
        try:
            repo = CallRepository(self._ctx.get_db())
            calls = repo.list_filtered(
                self._ctx.case_id,
                self._type_filter.currentText() if self._type_filter.currentText() != "All" else "",
                self._direction_filter.currentText() if self._direction_filter.currentText() != "All" else "",
            )
            self._calls_data = calls
            self._populate_table(calls)
        except Exception:
            self._calls_data = []

    def _populate_table(self, calls: list) -> None:
        self._table.setRowCount(len(calls))
        for i, c in enumerate(calls):
            self._table.setItem(i, 0, QTableWidgetItem(c.get("direction", "")))
            self._table.setItem(i, 1, QTableWidgetItem(c.get("contact_name") or ""))
            self._table.setItem(i, 2, QTableWidgetItem(c.get("conversation_title") or ""))
            dur = c.get("duration_seconds")
            dur_str = f"{dur // 60}:{dur % 60:02d}" if dur else "\u2014"
            self._table.setItem(i, 3, QTableWidgetItem(dur_str))
            self._table.setItem(i, 4, QTableWidgetItem(c.get("started_at_utc") or ""))
            self._table.setItem(i, 5, QTableWidgetItem(c.get("call_type", "")))
            self._table.setItem(i, 6, QTableWidgetItem(c.get("origin", "")))
            self._table.setItem(i, 7, QTableWidgetItem(c.get("confidence_level", "")))
            self._table.setItem(i, 8, QTableWidgetItem(str(c.get("source_evidence_file_id", ""))))

    def _on_filter(self) -> None:
        self._load_calls()
