from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


class StatusBadge(QLabel):
    BADGE_STYLES = {
        "parsed": (
            "background: transparent; border: 1px solid #087A38;"
            " color: #46A568; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
        "recovered": (
            "background: transparent; border: 1px solid #B86CFF;"
            " color: #B86CFF; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
        "inferred": (
            "background: transparent; border: 1px solid #00C2D7;"
            " color: #00C2D7; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
        "manual": (
            "background: transparent; border: 1px solid #F5D547;"
            " color: #F5D547; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
        "verified": (
            "background: #00C853; border: none; color: #020703;"
            " border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 700;"
        ),
        "partial": (
            "background: #FFB300; border: none; color: #020703;"
            " border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 700;"
        ),
        "failed": (
            "background: #FF1744; border: none; color: #FFFFFF;"
            " border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 700;"
        ),
        "unsupported": (
            "background: transparent; border: 1px solid #42604A;"
            " color: #6E9278; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
        "unverified": (
            "background: transparent; border: 1px solid #FFB300;"
            " color: #FFB300; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
        "relay": (
            "background: transparent; border: 1px solid #18C8FF;"
            " color: #6E9278; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
        "probable_peer": (
            "background: transparent; border: 1px solid #00F56A;"
            " color: #00F56A; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
        "vpn_proxy": (
            "background: transparent; border: 1px solid #B86CFF;"
            " color: #B86CFF; border-radius: 10px; padding: 2px 10px;"
            " font-size: 11px; font-weight: 600;"
        ),
    }

    def __init__(self, text: str = "", badge_type: str = "parsed", parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setMinimumHeight(22)
        self._badge_type = badge_type
        self._apply_style()

    def set_badge_type(self, badge_type: str) -> None:
        self._badge_type = badge_type
        self._apply_style()

    def _apply_style(self) -> None:
        css = self.BADGE_STYLES.get(self._badge_type, self.BADGE_STYLES["parsed"])
        self.setStyleSheet(css)
