from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from wft.ui.components.neon_button import NeonButton


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        details: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        destructive: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        if details:
            details_edit = QTextEdit()
            details_edit.setPlainText(details)
            details_edit.setReadOnly(True)
            details_edit.setMaximumHeight(100)
            layout.addWidget(details_edit)

        layout.addStretch()

        btn_box = QDialogButtonBox()
        cancel = QPushButton(cancel_text)
        confirm = NeonButton(confirm_text, "danger" if destructive else "primary")

        btn_box.addButton(cancel, QDialogButtonBox.RejectRole)
        btn_box.addButton(confirm, QDialogButtonBox.AcceptRole)

        if destructive:
            cancel.setDefault(True)
            cancel.setAutoDefault(True)
            confirm.setDefault(False)
            confirm.setAutoDefault(False)
            cancel.setFocus()

        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)