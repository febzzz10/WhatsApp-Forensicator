from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)

        self._title = QLabel(title)
        self._title.setObjectName("pageTitle")
        layout.addWidget(self._title)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("subtitleLabel")
            layout.addWidget(sub)

        layout.addStretch()

    def set_title(self, title: str) -> None:
        self._title.setText(title)
