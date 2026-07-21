from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QComboBox,
    QGroupBox, QCheckBox, QDateEdit, QPushButton,
    QSplitter, QTextBrowser,
)
from PySide6.QtCore import Qt, QDate

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, EmptyState, StatusBadge


class SearchPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Search", "Search across all case artefacts")
        layout.addWidget(header)

        search_row = QHBoxLayout()
        self._query = QLineEdit()
        self._query.setPlaceholderText("Search messages, contacts, URLs, hashes, source IDs...")
        self._query.setMinimumHeight(40)
        self._query.returnPressed.connect(self._on_search)
        search_btn = NeonButton("Search", "primary")
        search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self._query, 1)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        filters_group = QGroupBox("Filters")
        filters_layout = QVBoxLayout()
        filters_layout.setSpacing(8)

        top_row = QHBoxLayout()
        self._scope = QComboBox()
        self._scope.addItems([
            "All", "Messages", "Contacts", "Media", "Calls",
            "Recovered", "Network",
        ])
        top_row.addWidget(QLabel("Scope:"))
        top_row.addWidget(self._scope)
        top_row.addStretch()
        filters_layout.addLayout(top_row)

        splitter = QSplitter(Qt.Horizontal)

        self._results = QListWidget()
        self._results.setMinimumWidth(350)
        self._results.currentRowChanged.connect(self._on_result_selected)
        splitter.addWidget(self._results)

        self._result_detail = QTextBrowser()
        self._result_detail.setOpenExternalLinks(False)
        splitter.addWidget(self._result_detail)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        layout.addWidget(splitter, 1)

    def on_activated(self) -> None:
        pass

    def _on_search(self) -> None:
        query = self._query.text().strip()
        if not query or not self._ctx.is_active:
            return

        self._results.clear()
        self._result_detail.setHtml("")

        try:
            from wft.application.services.search_service import SearchService
            svc = SearchService()
            results = svc.search(
                self._ctx.get_db(),
                self._ctx.case_id,
                query,
                scope=self._scope.currentText(),
            )
            self._search_results = results
            for r in results:
                artefact_type = r.get("artefact_type", "unknown")
                text = r.get("text_content") or r.get("display_name") or r.get("title", "")
                timestamp = r.get("timestamp", "")
                label = f"[{artefact_type.upper()}] {text[:60]} \u2014 {timestamp}"
                QListWidgetItem(label, self._results)
        except Exception:
            self._result_detail.setHtml("<p style='color:#c00'>Search failed.</p>")

    def _on_result_selected(self, row: int) -> None:
        if row < 0 or not hasattr(self, "_search_results") or row >= len(self._search_results):
            return
        r = self._search_results[row]
        html = "<table>"
        for k, v in r.items():
            if v:
                html += f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>"
        html += "</table>"
        self._result_detail.setHtml(html)
