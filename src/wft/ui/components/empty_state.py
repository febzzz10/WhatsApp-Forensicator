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

        self._icon = QLabel("\u24D8")
        self._icon.setObjectName("emptyStateIcon")
        self._icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon)

        self._title = QLabel(title)
        self._title.setObjectName("emptyStateTitle")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        if description:
            self._desc = QLabel(description)
            self._desc.setObjectName("emptyStateDescription")
            self._desc.setAlignment(Qt.AlignCenter)
            self._desc.setWordWrap(True)
            layout.addWidget(self._desc)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_title(self, title: str) -> None:
        self._title.setText(title)
