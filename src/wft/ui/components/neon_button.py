from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy
from wft.ui.theme.style_helpers import set_dynamic_property

_LEGACY_STYLE_MAP: dict[str, str] = {
    "primary": "primary",
    "secondary": "secondary",
    "destructive": "danger",
    "warning": "secondary",
}

_VARIANT_ALIASES: dict[str, str] = {
    "destructive": "danger",
    "warning": "secondary",
}

_VALID_VARIANTS: set[str] = {"primary", "secondary", "danger", "ghost"}


class NeonButton(QPushButton):
    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        parent=None,
        style: Optional[str] = None,
    ) -> None:
        super().__init__(text, parent)
        if style is not None:
            variant = _LEGACY_STYLE_MAP.get(style, "secondary")
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.set_variant(variant)
        self.setMinimumHeight(36)

    def set_variant(self, variant: str) -> None:
        resolved = _VARIANT_ALIASES.get(variant, variant)
        set_dynamic_property(
            self, "variant", resolved,
            allowed_values=_VALID_VARIANTS,
            default_value="secondary",
        )

    def set_style(self, style: str) -> None:
        variant = _LEGACY_STYLE_MAP.get(style, "secondary")
        self.set_variant(variant)
