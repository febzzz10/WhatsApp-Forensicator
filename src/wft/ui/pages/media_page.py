from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView,
    QPushButton, QGridLayout, QSplitter, QTabWidget,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, StatisticCard, EmptyState, NeonButton
from wft.infrastructure.database.artefact_repositories import MediaRepository


class MediaPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Media", "View and analyse media files")
        layout.addWidget(header)

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(8)
        self._kpi_cards = {}
        kpi_labels = ["Total", "Images", "Videos", "Audio", "Documents", "Orphans", "Missing"]
        for i, label in enumerate(kpi_labels):
            card = StatisticCard(label, "0")
            self._kpi_cards[label] = card
            kpi_grid.addWidget(card, i // 4, i % 4)
        layout.addLayout(kpi_grid)

        controls = QHBoxLayout()
        self._filter = QComboBox()
        self._filter.addItems(["All", "Images", "Videos", "Audio", "Documents", "Orphans", "Missing"])
        self._filter.currentTextChanged.connect(self._on_filter)
        controls.addWidget(QLabel("Filter:"))
        controls.addWidget(self._filter)
        controls.addStretch()
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Horizontal)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Filename", "Type", "Size", "SHA-256",
            "Status", "Linked Message", "Origin", "Timestamp"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        splitter.addWidget(self._table)

        detail_tabs = QTabWidget()
        tabs = ["Preview", "Metadata", "EXIF", "Correlation", "Provenance", "Notes"]
        for tab_name in tabs:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(EmptyState(f"Select media to view {tab_name.lower()}."))
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
            stats = StatisticsService().get_media_stats(self._ctx.get_db(), self._ctx.case_id)
            self._kpi_cards["Total"].set_value(str(stats.get("total", 0)))
            self._kpi_cards["Images"].set_value(str(stats.get("images", 0)))
            self._kpi_cards["Videos"].set_value(str(stats.get("videos", 0)))
            self._kpi_cards["Audio"].set_value(str(stats.get("audio", 0)))
            self._kpi_cards["Documents"].set_value(str(stats.get("documents", 0)))
            self._kpi_cards["Orphans"].set_value(str(stats.get("orphans", 0)))
            self._kpi_cards["Missing"].set_value(str(stats.get("missing", 0)))
            self._load_media()
        except Exception:
            pass

    def _load_media(self) -> None:
        try:
            repo = MediaRepository(self._ctx.get_db())
            filter_text = self._filter.currentText()
            if filter_text == "All":
                items = repo.list_for_case(self._ctx.case_id)
            else:
                items = repo.list_filtered(self._ctx.case_id, filter_text)
            self._media_data = items
            self._populate_table(items)
        except Exception:
            self._media_data = []

    def _populate_table(self, items: list) -> None:
        self._table.setRowCount(len(items))
        for i, m in enumerate(items):
            self._table.setItem(i, 0, QTableWidgetItem(m.get("original_filename") or ""))
            self._table.setItem(i, 1, QTableWidgetItem(m.get("declared_mime_type") or ""))
            size = m.get("size_bytes")
            size_str = f"{size // 1024}KB" if size else "\u2014"
            self._table.setItem(i, 2, QTableWidgetItem(size_str))
            sha = m.get("sha256", "")
            self._table.setItem(i, 3, QTableWidgetItem(sha[:16] + "..." if sha else ""))
            status = "Missing" if m.get("is_missing") else ("Orphan" if m.get("is_orphan") else "OK")
            self._table.setItem(i, 4, QTableWidgetItem(status))
            self._table.setItem(i, 5, QTableWidgetItem(m.get("linked_message_code") or ""))
            self._table.setItem(i, 6, QTableWidgetItem(m.get("origin", "")))
            self._table.setItem(i, 7, QTableWidgetItem(m.get("created_at_utc") or ""))

    def _on_filter(self) -> None:
        self._load_media()
