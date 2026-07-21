from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy
from wft.ui.theme.style_helpers import set_dynamic_property

_LEGACY_BADGE_MAP = {
    "parsed": "success",
    "recovered": "warning",
    "inferred": "neutral",
    "manual": "warning",
    "verified": "success",
    "partial": "warning",
    "failed": "error",
    "unsupported": "neutral",
    "unverified": "warning",
    "relay": "neutral",
    "probable_peer": "neutral",
    "vpn_proxy": "neutral",
}

_VALID_STATUSES = {"success", "warning", "error", "information", "neutral"}


class StatusBadge(QLabel):
    def __init__(
        self,
        text: str = "",
        status: str = "neutral",
        parent=None,
        badge_type: Optional[str] = None,
    ) -> None:
        super().__init__(text, parent)
        if badge_type is not None:
            status = _LEGACY_BADGE_MAP.get(badge_type, "neutral")
        self._badge_type = badge_type or status
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setMinimumHeight(22)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        set_dynamic_property(
            self, "status", status,
            allowed_values=_VALID_STATUSES,
            default_value="neutral",
        )

    def set_badge_type(self, badge_type: str) -> None:
        self._badge_type = badge_type
        status = _LEGACY_BADGE_MAP.get(badge_type, "neutral")
        self.set_status(status)
