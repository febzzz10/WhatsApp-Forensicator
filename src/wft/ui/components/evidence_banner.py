from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy


class EvidenceBanner(QFrame):
    BANNER_STYLES = {
        "verified": (
            "background-color: #061108; border: 1px solid #00C853;"
            " border-radius: 4px; padding: 10px 16px;"
        ),
        "warning": (
            "background-color: #061108; border: 1px solid #FFB300;"
            " border-radius: 4px; padding: 10px 16px;"
        ),
        "hash_mismatch": (
            "background-color: #061108; border: 1px solid #FF1744;"
            " border-radius: 4px; padding: 10px 16px;"
        ),
        "unsupported": (
            "background-color: #061108; border: 1px solid #42604A;"
            " border-radius: 4px; padding: 10px 16px;"
        ),
        "info": (
            "background-color: #061108; border: 1px solid #18C8FF;"
            " border-radius: 4px; padding: 10px 16px;"
        ),
    }

    TEXT_STYLES = {
        "verified": "color: #00C853; font-weight: 600;",
        "warning": "color: #FFB300; font-weight: 600;",
        "hash_mismatch": "color: #FF1744; font-weight: 600;",
        "unsupported": "color: #6E9278; font-weight: 600;",
        "info": "color: #18C8FF; font-weight: 600;",
    }

    def __init__(self, text: str = "", banner_type: str = "info", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("evidenceBanner")
        self._banner_type = banner_type
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)

        icon_map = {
            "verified": "\u2713",
            "warning": "\u26A0",
            "hash_mismatch": "\u2717",
            "unsupported": "\u24D8",
            "info": "\u2139",
        }
        icon_char = icon_map.get(banner_type, "")
        self._icon = QLabel(icon_char)
        self._icon.setStyleSheet(self.TEXT_STYLES.get(banner_type, "color: #EAF7EE;"))
        self._icon.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self._icon.setMinimumWidth(18)
        self._icon.setVisible(bool(icon_char))
        layout.addWidget(self._icon)

        self._label = QLabel(text)
        self._label.setWordWrap(True)
        layout.addWidget(self._label, 1)

        self._apply_style(banner_type)

    def _apply_style(self, banner_type: str) -> None:
        frame_css = self.BANNER_STYLES.get(banner_type, self.BANNER_STYLES["info"])
        self.setStyleSheet(frame_css)
        text_css = self.TEXT_STYLES.get(banner_type, "color: #EAF7EE;")
        self._label.setStyleSheet(text_css)

    def set_text(self, text: str) -> None:
        self._label.setText(text)

    def set_banner_type(self, banner_type: str) -> None:
        self._banner_type = banner_type
        icon_map = {
            "verified": "\u2713",
            "warning": "\u26A0",
            "hash_mismatch": "\u2717",
            "unsupported": "\u24D8",
            "info": "\u2139",
        }
        icon_char = icon_map.get(banner_type, "")
        self._icon.setText(icon_char)
        self._icon.setVisible(bool(icon_char))
        self._apply_style(banner_type)
