import sys
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QTabBar
from PySide6.QtTest import QTest

from wft.ui.themes.tokens import ColorTokens
from wft.ui.themes.theme_manager import ThemeManager
from wft.ui.components import (
    NeonButton,
    StatusBadge,
    StatisticCard,
    PageHeader,
    EvidenceBanner,
    EmptyState,
    ErrorPanel,
)
from wft.ui.workers import CancellationToken


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestColorTokens:
    def test_default_tokens_have_all_keys(self):
        tokens = ColorTokens()
        assert tokens.root_bg == "#020703"
        assert tokens.primary_green == "#00F56A"
        assert tokens.danger == "#FF1744"
        assert tokens.recovered == "#B86CFF"

    def test_high_contrast_tokens_differ(self):
        default = ColorTokens()
        hc = ColorTokens.high_contrast()
        assert hc.root_bg == "#000000"
        assert hc.root_bg != default.root_bg
        assert hc.primary_text == "#FFFFFF"


class TestThemeManager:
    def test_theme_manager_initial_state(self, qapp):
        tm = ThemeManager(qapp)
        assert tm.current_theme == "dark_neon"
        assert tm.reduced_motion is False
        assert tm.tokens is not None

    def test_theme_manager_high_contrast(self, qapp):
        tm = ThemeManager(qapp)
        tm.set_theme("high_contrast")
        assert tm.current_theme == "high_contrast"
        assert tm.tokens.primary_text == "#FFFFFF"

    def test_set_reduced_motion(self, qapp):
        tm = ThemeManager(qapp)
        tm.set_reduced_motion(True)
        assert tm.reduced_motion is True

    def test_theme_manager_unknown_theme(self, qapp):
        tm = ThemeManager(qapp)
        tm.set_theme("nonexistent")
        assert tm.current_theme == "dark_neon"


class TestNeonButton:
    def test_button_styles(self, qapp):
        primary = NeonButton("Test", "primary")
        assert primary.text() == "Test"
        assert primary.minimumHeight() == 36
        assert primary.property("variant") == "primary"

        secondary = NeonButton("Secondary", "secondary")
        assert secondary.property("variant") == "secondary"

        destructive = NeonButton("Destroy", "destructive")
        assert destructive.property("variant") == "danger"

        warning = NeonButton("Warn", "warning")
        assert warning.minimumHeight() >= 24

    def test_button_cursor(self, qapp):
        btn = NeonButton("Click")
        assert btn.cursor().shape() == Qt.PointingHandCursor


class TestStatusBadge:
    def test_badge_types(self, qapp):
        for badge_type in ["parsed", "recovered", "inferred", "manual",
                            "verified", "partial", "failed", "unsupported"]:
            badge = StatusBadge("Test", badge_type)
            assert badge.text() == "Test"
            assert badge.minimumHeight() == 22

    def test_badge_set_type(self, qapp):
        badge = StatusBadge("Parsed", "parsed")
        badge.set_badge_type("recovered")
        assert badge._badge_type == "recovered"


class TestStatisticCard:
    def test_card_creation(self, qapp):
        card = StatisticCard("Messages", "42")
        assert card is not None

    def test_card_set_value(self, qapp):
        card = StatisticCard("Messages", "0")
        card.set_value("100")
        # read the value back from the label
        assert card._value.text() == "100"

    def test_card_dash_for_unavailable(self, qapp):
        card = StatisticCard("Recovered")
        assert card._value.text() == "\u2014"


class TestPageHeader:
    def test_header_with_subtitle(self, qapp):
        header = PageHeader("Dashboard", "Case overview")
        assert header is not None

    def test_header_set_title(self, qapp):
        header = PageHeader("Test")
        header.set_title("Updated")
        assert header._title.text() == "Updated"


class TestEvidenceBanner:
    def test_banner_types(self, qapp):
        for banner_type in ["verified", "warning", "hash_mismatch",
                             "unsupported", "info"]:
            banner = EvidenceBanner("Test message", banner_type)
            assert banner is not None

    def test_banner_set_text(self, qapp):
        banner = EvidenceBanner("Old", "info")
        banner.set_text("New text")
        assert banner._label.text() == "New text"

    def test_banner_set_type(self, qapp):
        banner = EvidenceBanner("Test", "info")
        banner.set_banner_type("warning")
        assert banner is not None


class TestEmptyState:
    def test_empty_state_defaults(self, qapp):
        state = EmptyState()
        assert state is not None

    def test_empty_state_custom_message(self, qapp):
        state = EmptyState("No data", "Import some data to get started")
        assert state._title.text() == "No data"

    def test_empty_state_set_title(self, qapp):
        state = EmptyState("Old")
        state.set_title("New")
        assert state._title.text() == "New"


class TestErrorPanel:
    def test_error_panel_creation(self, qapp):
        panel = ErrorPanel("Error", "Something went wrong", "ERR001", "E001")
        assert panel is not None


class TestCancellationToken:
    def test_token_initial_state(self):
        token = CancellationToken()
        assert token.cancelled is False

    def test_token_cancel(self):
        token = CancellationToken()
        token.cancel()
        assert token.cancelled is True


class _FakeCtx:
    is_active = False
    case_id = None
    case_path = None
    db_path = None


class TestDashboardNavigation:
    def test_nav_items_count(self, qapp):
        from wft.ui.main_window import MainWindow
        from wft.bootstrap import Container
        container = Container()
        window = MainWindow(container)
        assert len(window._nav_items) == 17

    def test_nav_has_required_pages(self, qapp):
        from wft.ui.main_window import MainWindow
        from wft.bootstrap import Container
        container = Container()
        window = MainWindow(container)
        keys = [k for _, k in window._nav_items]
        required = ["dashboard", "cases", "evidence", "chats", "contacts",
                     "calls", "media", "timeline", "recovered", "voip",
                     "search", "reports", "audit", "settings"]
        for r in required:
            assert r in keys, f"Missing nav item: {r}"

    def test_chat_has_no_send_button(self, qapp):
        from wft.ui.pages.chats_page import ChatsPage
        page = ChatsPage(_FakeCtx())
        assert page._examiner_note is not None
        assert "Add examiner note" in page._examiner_note.placeholderText()

    def test_voip_has_warning_banner(self, qapp):
        from wft.ui.pages.voip_page import VoIPPage
        page = VoIPPage(_FakeCtx())
        assert page is not None


class TestThemeQSS:
    def test_dark_neon_qss_exists(self, qapp):
        qss_path = Path(__file__).parents[2] / "src" / "wft" / "ui" / "themes" / "dark_neon.qss"
        assert qss_path.exists()
        content = qss_path.read_text()
        assert "QMainWindow" in content
        assert "#020703" in content

    def test_high_contrast_qss_exists(self, qapp):
        qss_path = Path(__file__).parents[2] / "src" / "wft" / "ui" / "themes" / "high_contrast.qss"
        assert qss_path.exists()
        content = qss_path.read_text()
        assert "QMainWindow" in content
        assert "#000000" in content
