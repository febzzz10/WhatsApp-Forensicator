import pytest
from PySide6.QtWidgets import QStackedWidget
from wft.ui.pages.page_id import PageId


@pytest.fixture(scope="module")
def main_window(qapp):
    from wft.bootstrap import Container
    from wft.ui.main_window import MainWindow
    return MainWindow(Container())


class TestMainWindowShell:
    def test_has_app_header(self, main_window):
        assert hasattr(main_window, "_app_header")

    def test_has_sidebar(self, main_window):
        assert hasattr(main_window, "_sidebar")

    def test_has_page_stack(self, main_window):
        assert hasattr(main_window, "_pages")
        assert isinstance(main_window._pages, QStackedWidget)

    def test_navigate_to_home(self, main_window):
        main_window.navigate_to(PageId.HOME)

    def test_navigate_to_dashboard(self, main_window):
        main_window.navigate_to(PageId.DASHBOARD)
        assert main_window._pages.currentWidget() is not None

    def test_sidebar_nav_changes_page(self, main_window):
        main_window._sidebar._on_item_clicked(PageId.SEARCH)
        page = main_window._page_map.get(PageId.SEARCH)
        assert main_window._pages.currentWidget() == page

    def test_app_header_logo_goes_home(self, main_window):
        main_window.navigate_to(PageId.DASHBOARD)
        main_window._app_header._logo_btn.click()
        assert main_window._pages.currentWidget() == main_window._home_page

    def test_page_map_contains_all_pages(self, main_window):
        expected_pages = {
            PageId.HOME, PageId.DASHBOARD, PageId.CASES, PageId.EVIDENCE,
            PageId.CHATS, PageId.CONTACTS, PageId.GROUPS, PageId.CALLS,
            PageId.MEDIA, PageId.TIMELINE, PageId.SEARCH, PageId.REPORTS,
            PageId.AUDIT, PageId.SETTINGS, PageId.ADB_EXTRACTOR,
            PageId.DECRYPTOR, PageId.RECOVERED, PageId.VOIP,
        }
        assert set(main_window._page_map.keys()) == expected_pages

    def test_navigate_to_via_string(self, main_window):
        main_window.navigate_to("dashboard")
        assert main_window._pages.currentWidget() is not None

    def test_navigate_to_invalid_string_does_nothing(self, main_window):
        main_window.navigate_to("nonexistent")
