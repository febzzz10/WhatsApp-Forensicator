from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QApplication,
)


class ErrorPanel(QFrame):
    def __init__(
        self,
        title: str = "Error",
        message: str = "",
        error_code: str = "",
        evidence_ref: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("errorPanel")
        self.setStyleSheet(
            "QFrame#errorPanel {"
            "  background-color: #061108;"
            "  border: 1px solid #FF1744;"
            "  border-radius: 6px;"
            "  padding: 16px;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QHBoxLayout()
        icon = QLabel("\u2717")
        icon.setStyleSheet("color: #FF1744; font-size: 20px; font-weight: 700;")
        header.addWidget(icon)

        self._title = QLabel(title)
        self._title.setStyleSheet("color: #FF1744; font-size: 15px; font-weight: 600;")
        header.addWidget(self._title)
        header.addStretch()
        layout.addLayout(header)

        if error_code:
            code_label = QLabel(f"Error code: {error_code}")
            code_label.setStyleSheet("color: #6E9278; font-size: 11px;")
            layout.addWidget(code_label)

        if evidence_ref:
            ref_label = QLabel(f"Evidence: {evidence_ref}")
            ref_label.setStyleSheet("color: #6E9278; font-size: 11px;")
            layout.addWidget(ref_label)

        self._message = QLabel(message)
        self._message.setWordWrap(True)
        self._message.setStyleSheet("color: #EAF7EE; font-size: 13px; padding: 8px 0;")
        layout.addWidget(self._message)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton("Copy Diagnostic Info")
        copy_btn.setObjectName("secondaryButton")
        copy_btn.clicked.connect(self._copy_diagnostic)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _copy_diagnostic(self) -> None:
        text = f"{self._title.text()}\n{self._message.text()}"
        QApplication.clipboard().setText(text)
