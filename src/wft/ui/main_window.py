from pathlib import Path
from typing import Optional, Union

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame,
    QMessageBox, QStatusBar, QSizePolicy,
)

from wft.bootstrap import Container
from wft.application.services.case_context import ActiveCaseContext
from wft.ui.themes.theme_manager import ThemeManager
from wft.ui.components import (
    AppHeader, NavigationSidebar,
)
from wft.ui.pages.page_id import PageId
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

        self._app_header = AppHeader()
        self._app_header.home_clicked.connect(lambda: self.navigate_to(PageId.HOME))
        root.addWidget(self._app_header)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        self._sidebar = NavigationSidebar()
        self._sidebar.page_selected.connect(self._on_sidebar_nav)
        self._sidebar.set_persistence_callback(
            lambda collapsed: self._container.settings.set(
                "ui", "sidebar_expanded", not collapsed,
            )
        )
        content.addWidget(self._sidebar)

        self._pages = QStackedWidget()
        self._pages.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build_page_area()
        content.addWidget(self._pages, 1)

        root.addLayout(content, 1)
        self._build_status_bar()

    def _build_page_area(self) -> None:
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

        self._page_map: dict[PageId, QWidget] = {
            PageId.HOME: self._home_page,
            PageId.DASHBOARD: self._dashboard_page,
            PageId.CASES: self._create_case_page,
            PageId.EVIDENCE: self._evidence_page,
            PageId.CHATS: self._chats_page,
            PageId.CONTACTS: self._contacts_page,
            PageId.GROUPS: self._groups_page,
            PageId.CALLS: self._calls_page,
            PageId.MEDIA: self._media_page,
            PageId.TIMELINE: self._timeline_page,
            PageId.SEARCH: self._search_page,
            PageId.REPORTS: self._reports_page,
            PageId.AUDIT: self._audit_page,
            PageId.SETTINGS: self._settings_page,
            PageId.ADB_EXTRACTOR: self._adb_page,
            PageId.DECRYPTOR: self._decrypt_page,
            PageId.RECOVERED: self._recovered_page,
            PageId.VOIP: self._voip_page,
        }

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
            ("Ctrl+N", lambda: self.navigate_to(PageId.CASES)),
            ("Ctrl+O", lambda: self._on_open_case()),
            ("Ctrl+I", lambda: self.navigate_to(PageId.EVIDENCE)),
            ("Ctrl+F", lambda: self.navigate_to(PageId.SEARCH)),
            ("Ctrl+R", lambda: self.navigate_to(PageId.REPORTS)),
            ("Ctrl+L", lambda: self._on_lock_case()),
        ]
        for shortcut, callback in actions:
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)

    def navigate_to(self, key: Union[str, PageId]) -> None:
        if isinstance(key, str):
            try:
                key = PageId(key)
            except ValueError:
                return
        if key == PageId.CASES:
            self._create_case_page.reset()
        page = self._page_map.get(key)
        if page:
            self._pages.setCurrentWidget(page)
            self._sidebar.set_active(key)
        else:
            self._sidebar.set_active(None)
        if page and hasattr(page, "on_activated"):
            QTimer.singleShot(0, page.on_activated)

    def _on_sidebar_nav(self, page_id: PageId) -> None:
        self.navigate_to(page_id)

    def _on_kpi_click(self, key: str) -> None:
        kpi_to_page = {
            "conversations": PageId.CHATS,
            "messages": PageId.CHATS,
            "recovered": PageId.RECOVERED,
            "media": PageId.MEDIA,
            "calls": PageId.CALLS,
            "contacts": PageId.CONTACTS,
        }
        page_key = kpi_to_page.get(key)
        if page_key:
            self.navigate_to(page_key)

    def _on_case_changed(self, case_id: int, case_path: str) -> None:
        code_label = Path(case_path).name
        self.setWindowTitle(f"WHATSAPP FORENSICATOR \u2014 {code_label}")
        self._app_header.set_case_status("OPEN")
        self._app_header.set_case_name(code_label)
        self._status_case.setText(f"{code_label} \u2022 CASE OPEN")
        self._status_integrity.setText("INTEGRITY: VERIFIED")
        QTimer.singleShot(0, self._refresh_kpi_strip)

    def _refresh_kpi_strip(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            stats = self._container.statistics_service.get_case_stats(
                self._ctx.get_db(), self._ctx.case_id
            )
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
        QMessageBox.information(
            self, "Lock Case",
            "Case locking will be available in a future update.",
        )

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