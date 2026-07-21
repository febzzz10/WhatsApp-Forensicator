import sys
import pytest
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from wft.ui.pages.page_id import PageId
from wft.ui.components.navigation_sidebar import NavigationSidebar


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestNavigationSidebar:
    def test_constructs_expanded(self, qapp):
        sidebar = NavigationSidebar()
        assert isinstance(sidebar, QWidget)

    def test_has_all_pages(self, qapp):
        sidebar = NavigationSidebar()
        expected_count = 17
        assert sidebar._item_count() == expected_count

    def test_page_selected_signal(self, qapp):
        sidebar = NavigationSidebar()
        received = []
        sidebar.page_selected.connect(received.append)
        sidebar._on_item_clicked(PageId.DASHBOARD)
        assert len(received) == 1
        assert received[0] == PageId.DASHBOARD

    def test_set_active_updates_selection(self, qapp):
        sidebar = NavigationSidebar()
        sidebar.set_active(PageId.CASES)
        item = sidebar._items[PageId.CASES]
        assert item.property("active") is True

    def test_set_active_none_clears_all(self, qapp):
        sidebar = NavigationSidebar()
        sidebar.set_active(PageId.CASES)
        sidebar.set_active(None)
        for item in sidebar._items.values():
            assert item.property("active") is False

    def test_collapse_toggle(self, qapp):
        sidebar = NavigationSidebar()
        sidebar.toggle_collapse()
        assert sidebar._is_collapsed
        sidebar.toggle_collapse()
        assert not sidebar._is_collapsed

    def test_collapse_hides_items(self, qapp):
        sidebar = NavigationSidebar()
        sidebar.toggle_collapse()
        for item in sidebar._items.values():
            assert item.isVisible() is False

    def test_collapse_hides_group_headers(self, qapp):
        sidebar = NavigationSidebar()
        sidebar.toggle_collapse()
        for i in range(sidebar._nav_layout.count()):
            w = sidebar._nav_layout.itemAt(i).widget()
            if isinstance(w, QLabel) and w.objectName() == "sidebarGroupHeader":
                assert w.isVisible() is False

    def test_has_collapse_button(self, qapp):
        sidebar = NavigationSidebar()
        assert sidebar._collapse_btn is not None
        assert sidebar._collapse_btn.objectName() == "sidebarCollapseBtn"

    def test_collapse_button_triggers_toggle(self, qapp):
        sidebar = NavigationSidebar()
        assert not sidebar._is_collapsed
        sidebar._collapse_btn.click()
        assert sidebar._is_collapsed

    def test_sidebar_minimum_width(self, qapp):
        sidebar = NavigationSidebar()
        assert sidebar.minimumWidth() == 56

    def test_is_collapsed_property(self, qapp):
        sidebar = NavigationSidebar()
        assert sidebar.is_collapsed is False
        sidebar.toggle_collapse()
        assert sidebar.is_collapsed is True

    def test_persistence_callback_fires(self, qapp):
        sidebar = NavigationSidebar()
        results = []
        sidebar.set_persistence_callback(lambda collapsed: results.append(collapsed))
        sidebar.toggle_collapse()
        assert len(results) == 1
        assert results[0] is True
        sidebar.toggle_collapse()
        assert len(results) == 2
        assert results[1] is False