from PySide6.QtWidgets import QApplication, QWidget
from wft.ui.components.app_header import AppHeader
from wft.ui.pages.page_id import PageId


class TestAppHeader:
    def test_constructs(self, qapp):
        header = AppHeader()
        assert isinstance(header, QWidget)

    def test_logo_clickable(self, qapp):
        header = AppHeader()
        received = []
        header.home_clicked.connect(lambda: received.append(True))
        header._logo_btn.click()
        assert len(received) == 1

    def test_case_badge_updates(self, qapp):
        header = AppHeader()
        header.set_case_status("OPEN")
        assert "OPEN" in header._case_badge.text()

    def test_case_name_elided(self, qapp):
        header = AppHeader()
        header.set_case_name("Test Case 123")
        assert header._case_name.text() == "Test Case 123"

    def test_case_badge_hidden_by_default(self, qapp):
        header = AppHeader()
        assert header._case_badge.isVisible() is False

    def test_case_name_hidden_by_default(self, qapp):
        header = AppHeader()
        assert header._case_name.isVisible() is False

    def test_header_title_text(self, qapp):
        header = AppHeader()
        assert header._title.text() == "WhatsApp Forensicator"

    def test_version_label(self, qapp):
        header = AppHeader()
        assert "v1.0.0a1" in header._version.text()

    def test_logo_button_has_tooltip(self, qapp):
        header = AppHeader()
        assert header._logo_btn.toolTip() == "Go to home"

    def test_logo_button_has_fixed_size(self, qapp):
        header = AppHeader()
        assert header._logo_btn.width() == 32
        assert header._logo_btn.height() == 32

    def test_case_name_sets_tooltip(self, qapp):
        header = AppHeader()
        header.set_case_name("Long Case Name")
        assert header._case_name.toolTip() == "Long Case Name"
