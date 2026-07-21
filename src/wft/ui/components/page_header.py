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
            self._subtitle = QLabel(subtitle)
            self._subtitle.setObjectName("subtitleLabel")
            layout.addWidget(self._subtitle)

        layout.addStretch()

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def set_subtitle(self, subtitle: str) -> None:
        if not hasattr(self, "_subtitle"):
            self._subtitle = QLabel(subtitle)
            self._subtitle.setObjectName("subtitleLabel")
            self.layout().insertWidget(1, self._subtitle)
        self._subtitle.setText(subtitle)
