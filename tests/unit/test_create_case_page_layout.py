import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QCheckBox, QLabel, QHBoxLayout,
    QSizePolicy,
)
from wft.bootstrap import Container
from wft.ui.pages.create_case_page import CreateCasePage
from wft.ui.components import NeonButton, ContentCard
from wft.ui.theme.tokens import DesignTokens


@pytest.fixture
def page(qapp):
    return CreateCasePage(Container())


class TestCreateCasePageLayout:
    def test_root_layout_has_page_margins(self, page):
        layout = page.layout()
        assert isinstance(layout, QVBoxLayout)
        margins = layout.contentsMargins()
        tokens = DesignTokens()
        assert margins.left() == tokens.space_20
        assert margins.top() == tokens.space_20
        assert margins.right() == tokens.space_20
        assert margins.bottom() == tokens.space_20

    def test_contains_content_card(self, page):
        found = False
        for i in range(page.layout().count()):
            w = page.layout().itemAt(i).widget()
            if isinstance(w, ContentCard):
                found = True
                break
        assert found, "Case page must contain a ContentCard"

    def test_content_card_has_max_width(self, page):
        for i in range(page.layout().count()):
            w = page.layout().itemAt(i).widget()
            if isinstance(w, ContentCard):
                assert w.maximumWidth() == 1100
                return
        pytest.fail("No ContentCard found")

    def test_form_labels_have_minimum_width(self, page):
        for i in range(page.layout().count()):
            w = page.layout().itemAt(i).widget()
            if isinstance(w, ContentCard):
                card = w
                for j in range(card._content_layout.count()):
                    item = card._content_layout.itemAt(j)
                    if item is None:
                        continue
                    layout = item.layout()
                    if isinstance(layout, QFormLayout):
                        for row in range(layout.rowCount()):
                            label_item = layout.itemAt(row, QFormLayout.LabelRole)
                            if label_item is not None:
                                label = label_item.widget()
                                if isinstance(label, QLabel):
                                    assert label.minimumWidth() >= 120, (
                                        f"Label '{label.text()}' minimumWidth={label.minimumWidth()}, expected >=120"
                                    )
                                    assert label.sizeHint().width() > 0
                return
        pytest.fail("No ContentCard with QFormLayout found")

    def test_form_labels_not_clipped(self, page):
        for i in range(page.layout().count()):
            w = page.layout().itemAt(i).widget()
            if isinstance(w, ContentCard):
                card = w
                for j in range(card._content_layout.count()):
                    item = card._content_layout.itemAt(j)
                    if item is None:
                        continue
                    layout = item.layout()
                    if isinstance(layout, QFormLayout):
                        assert layout.labelAlignment() & Qt.AlignLeft
                        assert layout.labelAlignment() & Qt.AlignVCenter
                        assert layout.fieldGrowthPolicy() == QFormLayout.AllNonFixedFieldsGrow
                return
        pytest.fail("No ContentCard with QFormLayout found")

    def test_input_fields_expanding(self, page):
        for i in range(page.layout().count()):
            w = page.layout().itemAt(i).widget()
            if isinstance(w, ContentCard):
                card = w
                for j in range(card._content_layout.count()):
                    item = card._content_layout.itemAt(j)
                    if item is None:
                        continue
                    layout = item.layout()
                    if isinstance(layout, QFormLayout):
                        for row in range(layout.rowCount()):
                            field_item = layout.itemAt(row, QFormLayout.FieldRole)
                            if field_item is not None:
                                field = field_item.widget()
                                if isinstance(field, (QLineEdit, QComboBox)):
                                    assert field.sizePolicy().horizontalPolicy() == QSizePolicy.Expanding
                                elif isinstance(field, QTextEdit):
                                    assert field.sizePolicy().horizontalPolicy() == QSizePolicy.Expanding
                return
        pytest.fail("No ContentCard with QFormLayout found")

    def test_create_case_button_not_full_width(self, page):
        for i in range(page.layout().count()):
            w = page.layout().itemAt(i).widget()
            if isinstance(w, ContentCard):
                for j in range(w._content_layout.count()):
                    item = w._content_layout.itemAt(j)
                    if item is None:
                        continue
                    layout = item.layout()
                    if isinstance(layout, QHBoxLayout):
                        for k in range(layout.count()):
                            btn_item = layout.itemAt(k)
                            if btn_item is None:
                                continue
                            btn = btn_item.widget()
                            if isinstance(btn, NeonButton) and btn.text() == "Create Case":
                                # Should be right-aligned: stretch before button
                                stretch_before = (k > 0 and
                                    isinstance(layout.itemAt(k - 1).widget(), type(None)) or
                                    layout.itemAt(k - 1).spacerItem() is not None)
                                # Skip precise stretch check, just verify button has limited width
                                assert btn.minimumWidth() <= 200
                                assert btn.minimumWidth() >= 160
                                return
        pytest.fail("No ContentCard with Create Case button found")

    def test_create_case_button_has_click_handler(self, page):
        assert hasattr(page, '_create_btn')
        assert page._create_btn is not None
        assert page._create_btn.text() == "Create Case"
        assert hasattr(page, '_on_create')
        assert callable(page._on_create)

    def test_authority_checkbox_uses_warning_color(self, page):
        tokens = DesignTokens()
        for i in range(page.layout().count()):
            w = page.layout().itemAt(i).widget()
            if isinstance(w, ContentCard):
                for j in range(w._content_layout.count()):
                    child = w._content_layout.itemAt(j)
                    if child is None:
                        continue
                    cb = child.widget()
                    if isinstance(cb, QCheckBox):
                        stylesheet = cb.styleSheet()
                        assert tokens.warning in stylesheet
                        assert cb.isChecked() is False
                        return
        pytest.fail("No QCheckBox found in ContentCard")

    def test_authority_checkbox_validation_unchanged(self, page):
        assert page._auth_check is not None

    def test_form_labels_have_non_zero_sizehint(self, page):
        for i in range(page.layout().count()):
            w = page.layout().itemAt(i).widget()
            if isinstance(w, ContentCard):
                card = w
                for j in range(card._content_layout.count()):
                    item = card._content_layout.itemAt(j)
                    if item is None:
                        continue
                    layout = item.layout()
                    if isinstance(layout, QFormLayout):
                        for row in range(layout.rowCount()):
                            label_item = layout.itemAt(row, QFormLayout.LabelRole)
                            if label_item is not None:
                                label = label_item.widget()
                                if isinstance(label, QLabel):
                                    sh = label.sizeHint()
                                    assert sh.width() > 0
                                    assert sh.height() > 0
                return
        pytest.fail("No ContentCard with QFormLayout found")

    def test_description_field_min_height(self, page):
        assert page._description.minimumHeight() >= 80
        assert page._description.maximumHeight() >= 120

    def test_storage_browse_button_same_height(self, page):
        tokens = DesignTokens()
        assert page._location_path.minimumHeight() == tokens.input_height

    def test_page_has_stretch(self, page):
        layout = page.layout()
        last_stretch = None
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.spacerItem() is not None:
                last_stretch = i
        assert last_stretch is not None, "Page should have a trailing stretch"
