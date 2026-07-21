import sys
import pytest
from PySide6.QtWidgets import QApplication, QFrame, QLabel
from wft.ui.components.content_card import ContentCard


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestContentCard:
    def test_default_construction(self, qapp):
        card = ContentCard()
        assert isinstance(card, QFrame)

    def test_title_set(self, qapp):
        card = ContentCard(title="My Card")
        assert card._title is not None
        assert card._title.text() == "My Card"

    def test_no_title_no_header(self, qapp):
        card = ContentCard()
        assert card._title is None

    def test_subtitle_set(self, qapp):
        card = ContentCard(title="T", subtitle="S")
        assert card._subtitle is not None
        assert card._subtitle.text() == "S"

    def test_content_layout_has_margins(self, qapp):
        card = ContentCard()
        margins = card._content_layout.contentsMargins()
        assert margins.left() > 0

    def test_set_title_late(self, qapp):
        card = ContentCard()
        card.set_title("Late")
        assert card._title is not None
        assert card._title.text() == "Late"

    def test_set_subtitle_late(self, qapp):
        card = ContentCard()
        card.set_subtitle("Late Sub")
        assert card._subtitle is not None
        assert card._subtitle.text() == "Late Sub"

    def test_title_object_name(self, qapp):
        card = ContentCard(title="T")
        assert card._title.objectName() == "contentCardTitle"

    def test_subtitle_object_name(self, qapp):
        card = ContentCard(title="T", subtitle="S")
        assert card._subtitle.objectName() == "contentCardSubtitle"

    def test_header_not_created_when_no_title_subtitle(self, qapp):
        card = ContentCard()
        assert card._header_layout is None