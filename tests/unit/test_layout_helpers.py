from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout
from wft.ui.theme.tokens import DesignTokens
from wft.ui.theme.layout_helpers import (
    apply_page_layout,
    apply_card_layout,
    apply_form_layout,
    apply_toolbar_layout,
)


def test_apply_page_layout_sets_margins():
    tokens = DesignTokens()
    layout = QVBoxLayout()
    apply_page_layout(layout, tokens)
    margins = layout.contentsMargins()
    assert margins.left() == tokens.space_20
    assert margins.right() == tokens.space_20
    assert margins.top() == tokens.space_20
    assert margins.bottom() == tokens.space_20
    assert layout.spacing() == tokens.space_16


def test_apply_card_layout_sets_margins():
    tokens = DesignTokens()
    layout = QVBoxLayout()
    apply_card_layout(layout, tokens)
    margins = layout.contentsMargins()
    assert margins.left() == tokens.space_16


def test_apply_form_layout_accepts_qform():
    tokens = DesignTokens()
    layout = QFormLayout()
    apply_form_layout(layout, tokens)
    assert layout.spacing() == tokens.space_10


def test_apply_toolbar_layout_sets_margins():
    tokens = DesignTokens()
    layout = QHBoxLayout()
    apply_toolbar_layout(layout, tokens)
    margins = layout.contentsMargins()
    assert margins.left() == tokens.space_16
    assert layout.spacing() == tokens.space_8
