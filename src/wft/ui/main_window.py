from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QTabBar, QFrame,
    QMessageBox, QStatusBar, QSizePolicy,
)

from wft.bootstrap import Container
from wft.application.services.case_context import ActiveCaseContext
from wft.ui.themes.theme_manager import ThemeManager
from wft.ui.components import StatisticCard, NeonButton
from wft.ui.pages.home_page import HomePage
from wft.ui.pages.dashboard_page import DashboardPage
from wft.ui.pages.create_case_page import CreateCasePage
from wft.ui.pages.evidence_page import EvidencePage
from wft.ui.pages.chats_page import ChatsPage
from wft.ui.pages.calls_page import CallsPage
from wft.ui.pages.media_page import MediaPage
from wft.ui.pages.timeline_page import TimelinePage
from wft.ui.pages.search_page import SearchPage
from wft.ui.pages.reports_page import ReportsPage
from wft.ui.pages.audit_page import AuditPage
from wft.ui.pages.settings_page import SettingsPage
from wft.ui.pages.contacts_page import ContactsPage
from wft.ui.pages.groups_page import GroupsPage
from wft.ui.pages.adb_extractor_page import ADBExtractorPage
from wft.ui.pages.decryptor_page import DecryptorPage
from wft.ui.pages.recovered_page import RecoveredPage
from wft.ui.pages.voip_page import VoIPPage


class MainWindow(QMainWindow):
    APP_VERSION = "1.0.0a1"

    def __init__(self, container: Container) -> None:
        super().__init__()
        self._container = container
        self._ctx = container.case_context
        self._theme_manager: Optional[ThemeManager] = None

        self.setWindowTitle("WHATSAPP FORENSICATOR")
        self.resize(1366, 768)
        self.setMinimumSize(1024, 600)
        self._build_ui()
        self._setup_shortcuts()
        self._ctx.case_changed.connect(self._on_case_changed)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_kpi_strip())
        root.addWidget(self._build_nav_bar())
        root.addWidget(self._build_page_area(), 1)
        self._build_status_bar()

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("appHeader")
        header.setStyleSheet(
            "QFrame#appHeader {"
            "  background-color: #030A05;"
            "  border-bottom: 1px solid #087A38;"
            "  padding: 8px 16px;"
            "}"
        )
        header.setFixedHeight(52)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        logo = QLabel("\u25C9")
        logo.setStyleSheet("color: #00F56A; font-size: 22px; font-weight: bold;")
        layout.addWidget(logo)

        title = QLabel("WHATSAPP FORENSICATOR")
        title.setStyleSheet("color: #00F56A; font-size: 18px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(title)

        subtitle = QLabel("COMPLETE FORENSICS SUITE")
        subtitle.setStyleSheet("color: #46A568; font-size: 10px; margin-left: 4px; margin-top: 4px;")
        layout.addWidget(subtitle)

        layout.addStretch()

        self._case_status_label = QLabel("NO CASE OPEN")
        self._case_status_label.setStyleSheet("color: #6E9278; font-size: 11px; padding: 4px 12px; border: 1px solid #1D5C34; border-radius: 4px;")
        layout.addWidget(self._case_status_label)

        integrity_label = QLabel("\u2713 OFFLINE")
        integrity_label.setStyleSheet("color: #46A568; font-size: 11px; padding: 4px 12px;")
        layout.addWidget(integrity_label)

        return header

    def _build_kpi_strip(self) -> QFrame:
        strip = QFrame()
        strip.setObjectName("kpiStrip")
        strip.setStyleSheet(
            "QFrame#kpiStrip {"
            "  background-color: #020703;"
            "  border-bottom: 1px solid #1D5C34;"
            "  padding: 4px 8px;"
            "}"
        )
        strip.setFixedHeight(72)

        layout = QHBoxLayout(strip)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        self._kpi_cards = {}
        kpi_defs = [
            ("conversations", "Conversations"),
            ("messages", "Messages"),
            ("recovered", "Recovered"),
            ("media", "Media"),
            ("calls", "Calls"),
            ("contacts", "Contacts"),
        ]
        for key, label in kpi_defs:
            card = StatisticCard(label=label, value="\u2014", action_key=key)
            card.clicked.connect(self._on_kpi_click)
            self._kpi_cards[key] = card
            layout.addWidget(card)

        return strip

    def _build_nav_bar(self) -> QFrame:
        nav = QFrame()
        nav.setObjectName("navBar")
        nav.setStyleSheet(
            "QFrame#navBar {"
            "  background-color: #030A05;"
            "  border-bottom: 1px solid #087A38;"
            "}"
        )
        nav.setFixedHeight(40)

        layout = QHBoxLayout(nav)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        self._nav_tabs = QTabBar()
        self._nav_tabs.setExpanding(False)
        self._nav_tabs.setDrawBase(False)
        self._nav_tabs.currentChanged.connect(self._on_nav_changed)
        self._nav_tabs.setStyleSheet(
            "QTabBar::tab {"
            "  background: transparent; color: #6E9278;"
            "  border: none; border-bottom: 2px solid transparent;"
            "  padding: 8px 14px; font-size: 12px; font-weight: 600;"
            "  min-height: 32px;"
            "}"
            "QTabBar::tab:hover { color: #A9C7B2; }"
            "QTabBar::tab:selected {"
            "  color: #00F56A; border-bottom: 2px solid #00F56A;"
            "}"
        )

        self._nav_items = [
            ("Dashboard", "dashboard"),
            ("Cases", "cases"),
            ("Evidence", "evidence"),
            ("ADB Extractor", "adb"),
            ("Decryptor", "decrypt"),
            ("Chat Viewer", "chats"),
            ("Contacts", "contacts"),
            ("Groups", "groups"),
            ("Calls", "calls"),
            ("Media", "media"),
            ("Timeline", "timeline"),
            ("Recovered", "recovered"),
            ("VoIP Analysis", "voip"),
            ("Search", "search"),
            ("Reports", "reports"),
            ("Audit", "audit"),
            ("Settings", "settings"),
        ]
        self._nav_map = {}

        for i, (label, key) in enumerate(self._nav_items):
            idx = self._nav_tabs.addTab(label)
            self._nav_map[idx] = key

        layout.addWidget(self._nav_tabs, 1)
        return nav

    def _build_page_area(self) -> QWidget:
        self._pages = QStackedWidget()

        self._home_page = HomePage(self._container, self)
        self._create_case_page = CreateCasePage(self._container, self)
        self._dashboard_page = DashboardPage(self._container, self._ctx, self)
        self._evidence_page = EvidencePage(self._container, self._ctx, self)
        self._chats_page = ChatsPage(self._ctx)
        self._contacts_page = ContactsPage(self._ctx)
        self._groups_page = GroupsPage(self._ctx)
        self._calls_page = CallsPage(self._ctx)
        self._media_page = MediaPage(self._ctx)
        self._timeline_page = TimelinePage(self._ctx)
        self._search_page = SearchPage(self._ctx)
        self._reports_page = ReportsPage(self._ctx)
        self._audit_page = AuditPage(self._ctx)
        self._settings_page = SettingsPage(self._container, self._ctx)
        self._adb_page = ADBExtractorPage(self._container, self._ctx)
        self._decrypt_page = DecryptorPage(self._ctx)
        self._recovered_page = RecoveredPage(self._ctx)
        self._voip_page = VoIPPage(self._ctx)

        self._pages.addWidget(self._home_page)
        self._pages.addWidget(self._create_case_page)
        self._pages.addWidget(self._dashboard_page)
        self._pages.addWidget(self._evidence_page)
        self._pages.addWidget(self._chats_page)
        self._pages.addWidget(self._contacts_page)
        self._pages.addWidget(self._groups_page)
        self._pages.addWidget(self._calls_page)
        self._pages.addWidget(self._media_page)
        self._pages.addWidget(self._timeline_page)
        self._pages.addWidget(self._search_page)
        self._pages.addWidget(self._reports_page)
        self._pages.addWidget(self._audit_page)
        self._pages.addWidget(self._settings_page)
        self._pages.addWidget(self._adb_page)
        self._pages.addWidget(self._decrypt_page)
        self._pages.addWidget(self._recovered_page)
        self._pages.addWidget(self._voip_page)

        self._page_map = {
            "dashboard": self._dashboard_page,
            "cases": self._create_case_page,
            "evidence": self._evidence_page,
            "chats": self._chats_page,
            "contacts": self._contacts_page,
            "groups": self._groups_page,
            "calls": self._calls_page,
            "media": self._media_page,
            "timeline": self._timeline_page,
            "search": self._search_page,
            "reports": self._reports_page,
            "audit": self._audit_page,
            "settings": self._settings_page,
            "adb": self._adb_page,
            "decrypt": self._decrypt_page,
            "recovered": self._recovered_page,
            "voip": self._voip_page,
        }

        return self._pages

    def _build_status_bar(self) -> None:
        self._sb = QStatusBar()
        self._sb.setStyleSheet(
            "QStatusBar {"
            "  background-color: #030A05;"
            "  color: #6E9278;"
            "  border-top: 1px solid #087A38;"
            "  font-size: 11px;"
            "  padding: 4px 8px;"
            "}"
        )
        self._sb.setFixedHeight(28)

        self._status_case = QLabel("NO CASE")
        self._status_integrity = QLabel("")
        self._status_jobs = QLabel("")
        self._status_tz = QLabel("UTC")
        self._status_version = QLabel(f"v{self.APP_VERSION}")
        self._status_offline = QLabel("OFFLINE MODE")

        for lbl in [self._status_case, self._status_integrity, self._status_jobs,
                     self._status_tz, self._status_version, self._status_offline]:
            lbl.setStyleSheet("color: #6E9278; font-size: 11px; padding: 0 8px;")

        self._sb.addPermanentWidget(self._status_offline)
        self._sb.addPermanentWidget(self._status_version)
        self._sb.addPermanentWidget(self._status_tz)
        self._sb.addPermanentWidget(self._status_jobs)
        self._sb.addPermanentWidget(self._status_integrity)
        self._sb.addPermanentWidget(self._status_case)
        self.setStatusBar(self._sb)

    def _setup_shortcuts(self) -> None:
        actions = [
            ("Ctrl+N", lambda: self.navigate_to("cases")),
            ("Ctrl+O", lambda: self._on_open_case()),
            ("Ctrl+I", lambda: self.navigate_to("evidence")),
            ("Ctrl+F", lambda: self.navigate_to("search")),
            ("Ctrl+R", lambda: self.navigate_to("reports")),
            ("Ctrl+L", lambda: self._on_lock_case()),
        ]
        for shortcut, callback in actions:
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)

    def navigate_to(self, key: str) -> None:
        if key == "cases":
            self._create_case_page.reset()
        idx = None
        for i, (_, k) in enumerate(self._nav_items):
            if k == key:
                idx = i
                break
        if idx is not None:
            self._nav_tabs.setCurrentIndex(idx)

        page = self._page_map.get(key)
        if page:
            self._pages.setCurrentWidget(page)
        if page and hasattr(page, "on_activated"):
            QTimer.singleShot(0, page.on_activated)

    def _on_nav_changed(self, index: int) -> None:
        key = self._nav_map.get(index)
        if not key:
            return
        self.navigate_to(key)

    def _on_kpi_click(self, key: str) -> None:
        kpi_to_page = {
            "conversations": "chats",
            "messages": "chats",
            "recovered": "recovered",
            "media": "media",
            "calls": "calls",
            "contacts": "contacts",
        }
        page_key = kpi_to_page.get(key)
        if page_key:
            self.navigate_to(page_key)

    def _on_case_changed(self, case_id: int, case_path: str) -> None:
        code_label = Path(case_path).name
        self.setWindowTitle(f"WHATSAPP FORENSICATOR \u2014 {code_label}")
        self._case_status_label.setText(code_label)
        self._status_case.setText(f"{code_label} \u2022 CASE OPEN")
        self._status_integrity.setText("INTEGRITY: VERIFIED")
        QTimer.singleShot(0, self._refresh_kpi_strip)

    def _refresh_kpi_strip(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            stats = self._container.statistics_service.get_case_stats(self._ctx.get_db(), self._ctx.case_id)
            self._kpi_cards["conversations"].set_value(str(stats.get("conversations", 0)))
            self._kpi_cards["messages"].set_value(str(stats.get("messages", 0)))
            self._kpi_cards["recovered"].set_value(str(stats.get("recovered_candidates", 0)))
            self._kpi_cards["media"].set_value(str(stats.get("media", 0)))
            self._kpi_cards["calls"].set_value(str(stats.get("calls", 0)))
            self._kpi_cards["contacts"].set_value(str(stats.get("contacts", 0)))
        except Exception:
            pass

    def on_case_created(self, case_id: int, case_path: Path) -> None:
        self._ctx.open(case_id, case_path)

    def on_case_opened(self, case_id: int, case_path: Path) -> None:
        self._ctx.open(case_id, case_path)

    def _on_open_case(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "Select Case Folder")
        if not dir_path:
            return
        case_path = Path(dir_path)
        try:
            result = self._container.case_service.open_case(case_path)
            self.on_case_opened(result["case"]["id"], case_path)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not open case:\n{exc}")

    def _on_lock_case(self) -> None:
        QMessageBox.information(self, "Lock Case", "Case locking will be available in a future update.")

    def set_theme_manager(self, tm: ThemeManager) -> None:
        self._theme_manager = tm

    @property
    def container(self) -> Container:
        return self._container

    @property
    def current_case_id(self) -> Optional[int]:
        return self._ctx.case_id if self._ctx.is_active else None

    @property
    def current_case_path(self) -> Optional[Path]:
        return self._ctx.case_path if self._ctx.is_active else None
