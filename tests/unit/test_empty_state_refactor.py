import sys
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QSizePolicy
from wft.ui.components.empty_state import EmptyState


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestEmptyStateNewAPI:
    def test_constructs_with_defaults(self, qapp):
        state = EmptyState()
        assert state._title.text() == "No data available"

    def test_constructs_with_custom_title(self, qapp):
        state = EmptyState("Custom title")
        assert state._title.text() == "Custom title"

    def test_constructs_with_title_and_description(self, qapp):
        state = EmptyState("Title", "Description text")
        assert state._title.text() == "Title"
        assert state._desc.text() == "Description text"

    def test_set_title(self, qapp):
        state = EmptyState("Old")
        state.set_title("New")
        assert state._title.text() == "New"

    def test_icon_object_name(self, qapp):
        state = EmptyState()
        assert state._icon.objectName() == "emptyStateIcon"

    def test_title_object_name(self, qapp):
        state = EmptyState()
        assert state._title.objectName() == "emptyStateTitle"

    def test_description_object_name(self, qapp):
        state = EmptyState("T", "D")
        assert state._desc.objectName() == "emptyStateDescription"

    def test_title_word_wrap(self, qapp):
        state = EmptyState("Long title")
        assert state._title.wordWrap() is True

    def test_size_policy_expanding(self, qapp):
        state = EmptyState()
        policy = state.sizePolicy()
        assert policy.horizontalPolicy() == QSizePolicy.Expanding
        assert policy.verticalPolicy() == QSizePolicy.Expanding

    def test_icon_alignment_center(self, qapp):
        state = EmptyState()
        assert state._icon.alignment() & Qt.AlignCenter

    def test_title_alignment_center(self, qapp):
        state = EmptyState()
        assert state._title.alignment() & Qt.AlignCenter

    def test_no_hardcoded_stylesheet(self, qapp):
        state = EmptyState()
        assert state._icon.styleSheet() == ""
        assert state._title.styleSheet() == ""


class TestEmptyStateDeprecatedCompat:
    def test_no_description_has_no_desc_label(self, qapp):
        state = EmptyState("Title")
        assert not hasattr(state, "_desc") or state._desc is None