from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class ContentCard(QFrame):
    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ContentCard")
        self._title: QLabel | None = None
        self._subtitle: QLabel | None = None
        self._header_layout: QHBoxLayout | None = None
        self._footer_layout: QHBoxLayout | None = None

        self._content_layout = QVBoxLayout(self)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(12)

        if title or subtitle:
            self._header_layout = QHBoxLayout()
            self._header_layout.setContentsMargins(0, 0, 0, 0)
            self._header_layout.setSpacing(8)

            if title:
                self._title = QLabel(title)
                self._title.setObjectName("contentCardTitle")
                self._header_layout.addWidget(self._title)

            if subtitle:
                self._subtitle = QLabel(subtitle)
                self._subtitle.setObjectName("contentCardSubtitle")
                self._header_layout.addWidget(self._subtitle)

            self._header_layout.addStretch()
            self._content_layout.addLayout(self._header_layout)

    def set_title(self, title: str) -> None:
        if self._title is None:
            if self._header_layout is None:
                self._header_layout = QHBoxLayout()
                self._header_layout.setContentsMargins(0, 0, 0, 0)
                self._header_layout.setSpacing(8)
                self._content_layout.insertLayout(0, self._header_layout)
            self._title = QLabel(title)
            self._title.setObjectName("contentCardTitle")
            self._header_layout.insertWidget(0, self._title)
        self._title.setText(title)

    def set_subtitle(self, subtitle: str) -> None:
        if self._subtitle is None:
            if self._header_layout is None:
                self._header_layout = QHBoxLayout()
                self._header_layout.setContentsMargins(0, 0, 0, 0)
                self._header_layout.setSpacing(8)
                self._content_layout.insertLayout(0, self._header_layout)
            self._subtitle = QLabel(subtitle)
            self._subtitle.setObjectName("contentCardSubtitle")
            if self._title is not None:
                self._header_layout.insertWidget(1, self._subtitle)
            else:
                self._header_layout.insertWidget(0, self._subtitle)
        self._subtitle.setText(subtitle)