from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame,
)
from PySide6.QtCore import Qt

from wft.bootstrap import Container
from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, StatisticCard, EmptyState


class DashboardPage(QWidget):
    def __init__(self, container: Container, ctx: ActiveCaseContext, main_window=None) -> None:
        super().__init__()
        self._container = container
        self._ctx = ctx
        self._main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = PageHeader("Dashboard", "Case overview and statistics")
        layout.addWidget(header)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        import_btn = NeonButton("Import Evidence", "primary")
        import_btn.clicked.connect(self._on_import_evidence)
        verify_btn = NeonButton("Verify Integrity", "secondary")
        parse_btn = NeonButton("Continue Parsing", "secondary")
        action_row.addWidget(import_btn)
        action_row.addWidget(verify_btn)
        action_row.addWidget(parse_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        grid = QGridLayout()
        grid.setSpacing(8)

        self._evidence_card = StatisticCard("Evidence Items", "0")
        self._message_card = StatisticCard("Messages", "0")
        self._contact_card = StatisticCard("Contacts", "0")
        self._call_card = StatisticCard("Calls", "0")
        self._media_card = StatisticCard("Media Files", "0")
        self._recovered_card = StatisticCard("Recovered", "0")

        grid.addWidget(self._evidence_card, 0, 0)
        grid.addWidget(self._message_card, 0, 1)
        grid.addWidget(self._contact_card, 0, 2)
        grid.addWidget(self._call_card, 1, 0)
        grid.addWidget(self._media_card, 1, 1)
        grid.addWidget(self._recovered_card, 1, 2)
        layout.addLayout(grid)

        self._empty_state = EmptyState(
            "No evidence imported",
            "Import and parse a supported WhatsApp export or database to begin analysis."
        )
        layout.addWidget(self._empty_state)

        layout.addStretch()

    def on_activated(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            stats = self._container.statistics_service.get_case_stats(self._ctx.get_db(), self._ctx.case_id)
            self._evidence_card.set_value(str(stats.get("evidence", 0)))
            self._message_card.set_value(str(stats.get("messages", 0)))
            self._contact_card.set_value(str(stats.get("contacts", 0)))
            self._call_card.set_value(str(stats.get("calls", 0)))
            self._media_card.set_value(str(stats.get("media", 0)))
            total = stats.get("evidence", 0)
            self._recovered_card.set_value(str(stats.get("recovered_candidates", 0)))
            self._empty_state.setVisible(total == 0)
        except Exception:
            pass

    def _on_import_evidence(self) -> None:
        if self._main_window:
            self._main_window.navigate_to("evidence")
