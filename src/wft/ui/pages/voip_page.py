from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QSplitter, QTabWidget, QFrame, QTextEdit,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, StatusBadge, EvidenceBanner, EmptyState



class VoIPPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("VoIP Analysis", "Live Network Metadata")
        layout.addWidget(header)

        warning_banner = EvidenceBanner(
            "IP-based location is approximate and may identify a relay, VPN, carrier gateway or cloud server "
            "rather than the call participant.",
            "warning",
        )
        layout.addWidget(warning_banner)

        action_row = QHBoxLayout()
        self._start_btn = NeonButton("Start Passive Capture", "primary")
        self._stop_btn = NeonButton("Stop Capture", "destructive")
        self._stop_btn.setEnabled(False)
        action_row.addWidget(self._start_btn)
        action_row.addWidget(self._stop_btn)
        action_row.addWidget(NeonButton("Import PCAP", "secondary"))

        self._capture_status = QLabel("Capture Status: Inactive")
        self._capture_status.setObjectName("mutedLabel")
        action_row.addWidget(self._capture_status)
        layout.addLayout(action_row)

        splitter = QSplitter(Qt.Vertical)

        top_splitter = QSplitter(Qt.Horizontal)

        endpoint_panel = QWidget()
        endpoint_layout = QVBoxLayout(endpoint_panel)

        endpoint_header = QHBoxLayout()
        endpoint_header.addWidget(QLabel("Captured Endpoints"))
        endpoint_header.addStretch()
        endpoint_panel.setLayout(endpoint_layout)

        self._endpoint_table = QTableWidget()
        self._endpoint_table.setColumnCount(11)
        self._endpoint_table.setHorizontalHeaderLabels([
            "First Seen", "Last Seen", "Source", "Destination",
            "Ports", "Protocol", "ISP", "ASN",
            "Classification", "Approx Region", "Confidence",
        ])
        self._endpoint_table.horizontalHeader().setStretchLastSection(True)
        self._endpoint_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._endpoint_table.verticalHeader().setVisible(False)
        endpoint_layout.addWidget(self._endpoint_table, 1)

        top_splitter.addWidget(endpoint_panel)

        map_panel = QWidget()
        map_layout = QVBoxLayout(map_panel)
        map_layout.addWidget(QLabel("Approximate Endpoint Map"))
        map_placeholder = EmptyState(
            "No active capture session.",
            "Start a passive capture or import a PCAP file to view endpoints.",
        )
        map_layout.addWidget(map_placeholder, 1)
        top_splitter.addWidget(map_panel)

        top_splitter.setStretchFactor(0, 2)
        top_splitter.setStretchFactor(1, 1)

        splitter.addWidget(top_splitter)

        bottom_splitter = QSplitter(Qt.Horizontal)

        event_panel = QWidget()
        event_layout = QVBoxLayout(event_panel)
        event_layout.addWidget(QLabel("Event Feed"))
        self._event_feed = QTextEdit()
        self._event_feed.setReadOnly(True)
        self._event_feed.setPlaceholderText("Events will appear here...")
        event_layout.addWidget(self._event_feed, 1)
        bottom_splitter.addWidget(event_panel)

        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        details_layout.addWidget(QLabel("Endpoint Details"))
        details_placeholder = EmptyState("Select an endpoint to view details.")
        details_layout.addWidget(details_placeholder, 1)
        bottom_splitter.addWidget(details_panel)

        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 1)

        splitter.addWidget(bottom_splitter)
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
            rows = self._ctx.get_db().execute(
                """SELECT ne.*, ncs.capture_code
                   FROM network_endpoints ne
                   JOIN network_capture_sessions ncs ON ne.capture_session_id = ncs.id
                   WHERE ncs.case_id = ?
                   ORDER BY ne.first_seen_at_utc DESC
                   LIMIT 500""",
                (self._ctx.case_id,),
            ).fetchall()
            endpoints = [dict(r) for r in rows]
            self._populate_endpoints(endpoints)
        except Exception:
            pass

    def _populate_endpoints(self, endpoints: list) -> None:
        self._endpoint_table.setRowCount(len(endpoints))
        for i, e in enumerate(endpoints):
            self._endpoint_table.setItem(i, 0, QTableWidgetItem(e.get("first_seen_at_utc", "")))
            self._endpoint_table.setItem(i, 1, QTableWidgetItem(e.get("last_seen_at_utc", "")))
            self._endpoint_table.setItem(i, 2, QTableWidgetItem(e.get("ip_address", "")))
            self._endpoint_table.setItem(i, 3, QTableWidgetItem(""))
            self._endpoint_table.setItem(i, 4, QTableWidgetItem(""))
            self._endpoint_table.setItem(i, 5, QTableWidgetItem(""))
            self._endpoint_table.setItem(i, 6, QTableWidgetItem(e.get("isp_name") or ""))
            self._endpoint_table.setItem(i, 7, QTableWidgetItem(e.get("asn") or ""))
            self._endpoint_table.setItem(i, 8, QTableWidgetItem(e.get("endpoint_classification", "")))
            region = ", ".join(filter(None, [e.get("city_name"), e.get("country_name")]))
            self._endpoint_table.setItem(i, 9, QTableWidgetItem(region))
            self._endpoint_table.setItem(i, 10, QTableWidgetItem(e.get("classification_confidence", "")))
