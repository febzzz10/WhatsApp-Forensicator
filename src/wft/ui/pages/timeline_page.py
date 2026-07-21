from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox,
    QHeaderView, QDateEdit, QPushButton,
)
from PySide6.QtCore import Qt, QDate

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, EmptyState
from wft.infrastructure.database.artefact_repositories import TimelineEventRepository


class TimelinePage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Timeline", "Event timeline across all evidence")
        layout.addWidget(header)

        controls = QHBoxLayout()

        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())

        self._source_filter = QComboBox()
        self._source_filter.addItems([
            "All Sources", "MESSAGE", "CALL", "MEDIA",
            "GROUP_EVENT", "RECOVERED", "NETWORK",
        ])
        self._confidence_filter = QComboBox()
        self._confidence_filter.addItems(["All Confidence", "HIGH", "MEDIUM", "LOW"])

        self._source_filter.currentTextChanged.connect(self._on_filter)
        self._confidence_filter.currentTextChanged.connect(self._on_filter)

        controls.addWidget(QLabel("From:"))
        controls.addWidget(self._date_from)
        controls.addWidget(QLabel("To:"))
        controls.addWidget(self._date_to)
        controls.addWidget(QLabel("Type:"))
        controls.addWidget(self._source_filter)
        controls.addWidget(QLabel("Confidence:"))
        controls.addWidget(self._confidence_filter)
        controls.addStretch()
        layout.addLayout(controls)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Timestamp", "Event", "Type", "Source",
            "Conversation", "Contact", "Origin", "Confidence"
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
            repo = TimelineEventRepository(self._ctx.get_db())
            events = repo.list_filtered(
                self._ctx.case_id,
                source_filter=self._source_filter.currentText(),
                confidence=self._confidence_filter.currentText(),
                date_from=self._date_from.date().toString(Qt.ISODate),
                date_to=self._date_to.date().toString(Qt.ISODate),
            )
            self._populate_table(events)
        except Exception:
            pass

    def _populate_table(self, events: list) -> None:
        self._table.setRowCount(len(events))
        for i, e in enumerate(events):
            self._table.setItem(i, 0, QTableWidgetItem(e.get("occurred_at_utc") or ""))
            self._table.setItem(i, 1, QTableWidgetItem(e.get("title", "")[:80]))
            self._table.setItem(i, 2, QTableWidgetItem(e.get("event_type", "")))
            self._table.setItem(i, 3, QTableWidgetItem(e.get("artefact_type", "")))
            self._table.setItem(i, 4, QTableWidgetItem(e.get("conversation_title") or ""))
            self._table.setItem(i, 5, QTableWidgetItem(e.get("contact_name") or ""))
            self._table.setItem(i, 6, QTableWidgetItem(e.get("origin", "")))
            self._table.setItem(i, 7, QTableWidgetItem(e.get("confidence_level", "")))

    def _on_filter(self) -> None:
        self._refresh()
