from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QLabel, QMessageBox, QFileDialog,
    QCheckBox, QGroupBox, QHBoxLayout,
)
from PySide6.QtCore import Qt

from wft.bootstrap import Container
from wft.ui.components import PageHeader, NeonButton


class CreateCasePage(QWidget):
    def __init__(self, container: Container, main_window=None) -> None:
        super().__init__()
        self._container = container
        self._main_window = main_window
        self._case_dir: Path = Path.home() / "wft_cases"
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = PageHeader("New Case Wizard", "Create a new forensic investigation case")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(8)

        self._case_code = QLineEdit()
        self._case_code.setPlaceholderText("e.g. CASE-2026-0001")
        form.addRow("Case Code:", self._case_code)

        self._title = QLineEdit()
        self._title.setPlaceholderText("e.g. Authorised WhatsApp Examination")
        form.addRow("Title:", self._title)

        self._description = QTextEdit()
        self._description.setMaximumHeight(80)
        self._description.setPlaceholderText("Short description of the case")
        form.addRow("Description:", self._description)

        self._examiner_name = QLineEdit()
        self._examiner_name.setPlaceholderText("Your full name")
        form.addRow("Examiner Name:", self._examiner_name)

        self._organisation = QLineEdit()
        form.addRow("Organisation:", self._organisation)

        self._timezone = QComboBox()
        self._timezone.addItems(["UTC", "Asia/Kolkata", "America/New_York", "Europe/London", "Asia/Dubai"])
        form.addRow("Display Time Zone:", self._timezone)

        layout.addLayout(form)

        location_group = QGroupBox("Case Storage Location")
        loc_layout = QVBoxLayout()
        loc_row = QHBoxLayout()
        self._location_path = QLineEdit(str(self._case_dir))
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.clicked.connect(self._on_browse_location)
        loc_row.addWidget(self._location_path, 1)
        loc_row.addWidget(browse_btn)
        loc_layout.addLayout(loc_row)
        location_group.setLayout(loc_layout)
        layout.addWidget(location_group)

        self._auth_check = QCheckBox("I have lawful authority to conduct this examination")
        self._auth_check.setStyleSheet("color: #FFB300; font-weight: 600;")
        layout.addWidget(self._auth_check)

        self._create_btn = NeonButton("Create Case", "primary")
        self._create_btn.clicked.connect(self._on_create)
        layout.addWidget(self._create_btn)

        layout.addStretch()

    def _on_browse_location(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Select Case Storage Directory")
        if dir_path:
            self._location_path.setText(dir_path)
            self._case_dir = Path(dir_path)

    def _on_create(self) -> None:
        case_code = self._case_code.text().strip()
        title = self._title.text().strip()
        examiner = self._examiner_name.text().strip()

        if not case_code or not title or not examiner:
            QMessageBox.warning(self, "Validation Error", "Case code, title, and examiner name are required.")
            return
        if not self._auth_check.isChecked():
            QMessageBox.warning(self, "Authorisation Required", "You must acknowledge lawful authority.")
            return

        case_dir = Path(self._location_path.text().strip())
        try:
            result = self._container.case_service.create_case(
                case_dir=case_dir,
                case_code=case_code,
                title=title,
                examiner_name=examiner,
                organisation=self._organisation.text().strip(),
                display_timezone=self._timezone.currentText(),
            )
            QMessageBox.information(self, "Success", f"Case {case_code} created successfully.")
            if self._main_window:
                self._main_window.on_case_created(result["case_id"], case_dir / case_code)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to create case:\n{exc}")

    def reset(self) -> None:
        self._case_code.clear()
        self._title.clear()
        self._description.clear()
        self._examiner_name.clear()
        self._organisation.clear()
        self._auth_check.setChecked(False)
