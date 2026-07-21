from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy


class AppHeader(QWidget):
    home_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AppHeader")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        self._logo_btn = QPushButton("WF")
        self._logo_btn.setObjectName("headerLogo")
        self._logo_btn.setCursor(Qt.PointingHandCursor)
        self._logo_btn.setFixedSize(32, 32)
        self._logo_btn.setToolTip("Go to home")
        self._logo_btn.clicked.connect(self.home_clicked.emit)
        layout.addWidget(self._logo_btn)

        self._title = QLabel("WhatsApp Forensicator")
        self._title.setObjectName("headerTitle")
        layout.addWidget(self._title)

        self._version = QLabel("v1.0.0a1")
        self._version.setObjectName("headerVersion")
        layout.addWidget(self._version)

        layout.addStretch()

        self._case_badge = QLabel()
        self._case_badge.setObjectName("headerCaseBadge")
        self._case_badge.setVisible(False)
        layout.addWidget(self._case_badge)

        self._case_name = QLabel()
        self._case_name.setObjectName("headerCaseName")
        self._case_name.setVisible(False)
        self._case_name.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self._case_name.setWordWrap(False)
        layout.addWidget(self._case_name)

    def set_case_status(self, status: str) -> None:
        self._case_badge.setText(status)
        self._case_badge.setVisible(bool(status))

    def set_case_name(self, name: str) -> None:
        self._case_name.setText(name)
        self._case_name.setVisible(bool(name))
        if name:
            self._case_name.setToolTip(name)