from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLayout
from wft.ui.theme.tokens import DesignTokens


def apply_page_layout(layout: QLayout, tokens: DesignTokens) -> None:
    layout.setContentsMargins(
        tokens.space_20, tokens.space_20,
        tokens.space_20, tokens.space_20,
    )
    layout.setSpacing(tokens.space_16)


def apply_card_layout(layout: QLayout, tokens: DesignTokens) -> None:
    layout.setContentsMargins(
        tokens.space_16, tokens.space_16,
        tokens.space_16, tokens.space_16,
    )
    layout.setSpacing(tokens.space_12)


def apply_form_layout(layout: QFormLayout, tokens: DesignTokens) -> None:
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(tokens.space_10)
    layout.setVerticalSpacing(tokens.space_10)


def apply_toolbar_layout(layout: QHBoxLayout, tokens: DesignTokens) -> None:
    layout.setContentsMargins(
        tokens.space_16, tokens.space_8,
        tokens.space_16, tokens.space_8,
    )
    layout.setSpacing(tokens.space_8)
