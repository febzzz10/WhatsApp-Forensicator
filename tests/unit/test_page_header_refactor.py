from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from wft.ui.components.page_header import PageHeader


class TestPageHeaderNewAPI:
    def test_constructs_with_title_only(self, qapp):
        header = PageHeader("Dashboard")
        assert header._title.text() == "Dashboard"

    def test_constructs_with_title_and_subtitle(self, qapp):
        header = PageHeader("Dashboard", "Case overview")
        assert header._title.text() == "Dashboard"
        assert header._subtitle.text() == "Case overview"

    def test_set_title(self, qapp):
        header = PageHeader("Old")
        header.set_title("New")
        assert header._title.text() == "New"

    def test_set_subtitle(self, qapp):
        header = PageHeader("Dashboard")
        header.set_subtitle("New subtitle")
        assert header._subtitle.text() == "New subtitle"

    def test_page_title_object_name(self, qapp):
        header = PageHeader("Test")
        assert header._title.objectName() == "pageTitle"

    def test_subtitle_object_name(self, qapp):
        header = PageHeader("Test", "Sub")
        assert header._subtitle.objectName() == "subtitleLabel"

    def test_layout_margins(self, qapp):
        header = PageHeader("Test")
        margins = header.layout().contentsMargins()
        assert margins.left() == 0
        assert margins.top() == 0
        assert margins.right() == 0
        assert margins.bottom() == 4

    def test_stretch_exists(self, qapp):
        header = PageHeader("Test")
        count = header.layout().count()
        last = header.layout().itemAt(count - 1)
        assert last is not None
        assert last.widget() is None


class TestPageHeaderDeprecatedCompat:
    def test_no_subtitle_has_no_subtitle_label(self, qapp):
        header = PageHeader("Test")
        assert not hasattr(header, "_subtitle") or header._subtitle is None
