from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QSplitter,
    QTabWidget,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, EmptyState
from wft.infrastructure.database.artefact_repositories import GroupRepository


class GroupsPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Groups", "View and analyse WhatsApp groups")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)

        search_layout = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search groups...")
        self._search.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search)
        list_layout.addLayout(search_layout)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Subject", "Group ID", "Participants", "Messages",
            "Calls", "Origin", "Date Range"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        list_layout.addWidget(self._table, 1)

        splitter.addWidget(list_panel)

        detail_tabs = QTabWidget()
        tabs = ["Details", "Participants", "Chat", "Calls", "Media", "Timeline"]
        for tab_name in tabs:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.addWidget(EmptyState(f"No {tab_name.lower()} data."))
            detail_tabs.addTab(tab, tab_name)
        splitter.addWidget(detail_tabs)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, 1)

    def on_activated(self) -> None:
        if self._ctx.is_active:
            self._refresh()

    def _refresh(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            repo = GroupRepository(self._ctx.get_db())
            groups = repo._list("groups", "case_id = ? ORDER BY subject", (self._ctx.case_id,))
            self._groups_data = groups
            self._populate_table(groups)
        except Exception:
            self._groups_data = []

    def _populate_table(self, groups: list) -> None:
        self._table.setRowCount(len(groups))
        for i, g in enumerate(groups):
            self._table.setItem(i, 0, QTableWidgetItem(g.get("subject") or ""))
            self._table.setItem(i, 1, QTableWidgetItem(g.get("whatsapp_group_identifier") or ""))
            self._table.setItem(i, 2, QTableWidgetItem(str(g.get("participant_count", ""))))
            self._table.setItem(i, 3, QTableWidgetItem(str(g.get("message_count", ""))))
            self._table.setItem(i, 4, QTableWidgetItem(str(g.get("call_count", ""))))
            self._table.setItem(i, 5, QTableWidgetItem(g.get("origin", "PARSED")))
            created = g.get("created_at_source_utc") or g.get("created_at_utc", "")
            self._table.setItem(i, 6, QTableWidgetItem(created))

    def _on_search(self, text: str) -> None:
        if not hasattr(self, "_groups_data") or not self._groups_data:
            return
        filtered = [g for g in self._groups_data
                    if text.lower() in (g.get("subject") or "").lower()]
        self._populate_table(filtered)
