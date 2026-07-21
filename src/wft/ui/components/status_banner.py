from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy


class StatusBanner(QFrame):
    def __init__(self, text: str = "", banner_type: str = "info", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("statusBanner")
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
        self._icon.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self._icon.setMinimumWidth(18)
        self._icon.setVisible(bool(icon_char))
        layout.addWidget(self._icon)

        self._label = QLabel(text)
        self._label.setWordWrap(True)
        layout.addWidget(self._label, 1)

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
