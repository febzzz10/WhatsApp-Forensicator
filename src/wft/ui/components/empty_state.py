from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget, QSizePolicy


class EmptyState(QWidget):
    def __init__(
        self,
        title: str = "No data available",
        description: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        icon = QLabel("\u24D8")
        icon.setStyleSheet("color: #6E9278; font-size: 32px;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        self._title = QLabel(title)
        self._title.setStyleSheet("color: #A9C7B2; font-size: 16px; font-weight: 600;")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        if description:
            self._desc = QLabel(description)
            self._desc.setStyleSheet("color: #6E9278; font-size: 13px;")
            self._desc.setAlignment(Qt.AlignCenter)
            self._desc.setWordWrap(True)
            layout.addWidget(self._desc)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_title(self, title: str) -> None:
        self._title.setText(title)
