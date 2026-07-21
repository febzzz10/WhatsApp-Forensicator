from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QSplitter,
    QTabWidget,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, EmptyState
from wft.infrastructure.database.artefact_repositories import ContactRepository


class ContactsPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Contacts", "View and analyse parsed contacts")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)

        search_layout = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search contacts...")
        self._search.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search)
        list_layout.addLayout(search_layout)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Name", "Phone", "WhatsApp ID", "Type",
            "Origin", "Confidence", "Messages"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setVisible(False)
        list_layout.addWidget(self._table, 1)

        splitter.addWidget(list_panel)

        detail_tabs = QTabWidget()
        self._detail_tabs_map = {}
        tabs = ["Overview", "Conversations", "Calls", "Shared Media", "Aliases", "Timeline", "Provenance", "Notes"]
        for tab_name in tabs:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            empty = EmptyState(f"No {tab_name.lower()} data available. Select a contact to view details.")
            tab_layout.addWidget(empty)
            detail_tabs.addTab(tab, tab_name)
            self._detail_tabs_map[tab_name] = empty
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
            repo = ContactRepository(self._ctx.get_db())
            contacts = repo.list_for_case(self._ctx.case_id)
            self._contacts_data = contacts
            self._populate_table(contacts)
        except Exception:
            self._contacts_data = []

    def _populate_table(self, contacts: list) -> None:
        self._table.setRowCount(len(contacts))
        for i, c in enumerate(contacts):
            self._table.setItem(i, 0, QTableWidgetItem(c.get("display_name") or ""))
            self._table.setItem(i, 1, QTableWidgetItem(c.get("phone_number_raw") or ""))
            self._table.setItem(i, 2, QTableWidgetItem(c.get("whatsapp_identifier") or ""))
            self._table.setItem(i, 3, QTableWidgetItem("Business" if c.get("is_business") else "Personal"))
            self._table.setItem(i, 4, QTableWidgetItem(c.get("origin", "PARSED")))
            self._table.setItem(i, 5, QTableWidgetItem(c.get("confidence_level", "HIGH")))
            self._table.setItem(i, 6, QTableWidgetItem(str(c.get("message_count", ""))))

    def _on_search(self, text: str) -> None:
        if not hasattr(self, "_contacts_data") or not self._contacts_data:
            return
        filtered = [c for c in self._contacts_data
                    if text.lower() in (c.get("display_name") or "").lower()
                    or text.lower() in (c.get("phone_number_raw") or "").lower()]
        self._populate_table(filtered)
