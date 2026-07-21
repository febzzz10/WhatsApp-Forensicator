from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QTextEdit, QApplication,
)


class ProgressOverlay(QDialog):
    cancelled = Signal()

    def __init__(self, title: str = "Processing", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMaximumWidth(600)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowCloseButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._operation = QLabel(title)
        self._operation.setObjectName("sectionTitle")
        layout.addWidget(self._operation)

        self._stage = QLabel("Initialising...")
        self._stage.setObjectName("mutedLabel")
        layout.addWidget(self._stage)

        self._progress = QProgressBar()
        layout.addWidget(self._progress)

        info = QHBoxLayout()
        self._count_label = QLabel("")
        self._count_label.setObjectName("mutedLabel")
        info.addWidget(self._count_label)
        self._elapsed = QLabel("")
        self._elapsed.setObjectName("mutedLabel")
        self._elapsed.setAlignment(Qt.AlignRight)
        info.addWidget(self._elapsed)
        layout.addLayout(info)

        self._details = QTextEdit()
        self._details.setReadOnly(True)
        self._details.setMaximumHeight(100)
        self._details.setObjectName("mutedLabel")
        layout.addWidget(self._details)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("destructiveButton")
        self._cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self._cancel_btn, alignment=Qt.AlignRight)

        self._cancelled = False

    def set_stage(self, stage: str) -> None:
        self._stage.setText(stage)

    def set_progress(self, value: int, maximum: int = 100) -> None:
        self._progress.setMaximum(maximum)
        self._progress.setValue(value)

    def set_count(self, text: str) -> None:
        self._count_label.setText(text)

    def set_elapsed(self, text: str) -> None:
        self._elapsed.setText(text)

    def append_detail(self, line: str) -> None:
        self._details.append(line)

    def _on_cancel(self) -> None:
        self._cancelled = True
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setText("Cancelling...")
        self.cancelled.emit()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled
