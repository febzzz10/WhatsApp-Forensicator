from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)


class StatisticCard(QFrame):
    clicked = Signal(str)

    def __init__(
        self,
        label: str = "",
        value: str = "\u2014",
        icon_text: str = "",
        warning: bool = False,
        action_key: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._action_key = action_key
        self.setObjectName("statCard")
        self.setStyleSheet(
            "QFrame#statCard {"
            "  background-color: #061108;"
            "  border: 1px solid #087A38;"
            "  border-radius: 6px;"
            "  padding: 12px;"
            "}"
            "QFrame#statCard:hover {"
            "  border: 1px solid #00F56A;"
            "}"
        )
        self.setMinimumHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(8)
        if icon_text:
            icon_label = QLabel(icon_text)
            icon_label.setStyleSheet("color: #46A568; font-size: 16px;")
            header.addWidget(icon_label)
        self._label = QLabel(label)
        self._label.setObjectName("kpiLabel")
        header.addWidget(self._label)
        header.addStretch()
        if warning:
            warn = QLabel("\u26A0")
            warn.setStyleSheet("color: #FFB300; font-size: 14px;")
            header.addWidget(warn)
        layout.addLayout(header)

        self._value = QLabel(value)
        self._value.setObjectName("kpiValue")
        layout.addWidget(self._value)

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def mousePressEvent(self, event) -> None:
        if self._action_key:
            self.clicked.emit(self._action_key)
        super().mousePressEvent(event)
