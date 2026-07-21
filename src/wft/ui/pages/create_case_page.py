from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QLabel, QMessageBox, QFileDialog,
    QCheckBox, QGroupBox, QHBoxLayout, QSizePolicy,
)
from PySide6.QtCore import Qt

from wft.bootstrap import Container
from wft.ui.components import PageHeader, NeonButton, ContentCard
from wft.ui.theme.layout_helpers import apply_page_layout, apply_form_layout
from wft.ui.theme.tokens import DesignTokens

_FORM_LABEL_MIN_WIDTH = 140


class CreateCasePage(QWidget):
    def __init__(self, container: Container, main_window=None) -> None:
        super().__init__()
        self._tokens = DesignTokens()
        self._container = container
        self._main_window = main_window
        self._case_dir: Path = Path.home() / "wft_cases"
        self._build_ui()

    def _build_ui(self) -> None:
        page_layout = QVBoxLayout(self)
        apply_page_layout(page_layout, self._tokens)

        header = PageHeader("New Case Wizard", "Create a new forensic investigation case")
        page_layout.addWidget(header)

        # ContentCard wrapper for the form
        card = ContentCard()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMaximumWidth(1100)
        card_layout = card._content_layout

        form = QFormLayout()
        apply_form_layout(form, self._tokens)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(self._tokens.space_12)

        self._case_code = QLineEdit()
        self._case_code.setPlaceholderText("e.g. CASE-2026-0001")
        self._case_code.setMinimumHeight(self._tokens.input_height)
        self._case_code.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form.addRow(self._make_label("Case Code:"), self._case_code)

        self._title = QLineEdit()
        self._title.setPlaceholderText("e.g. Authorised WhatsApp Examination")
        self._title.setMinimumHeight(self._tokens.input_height)
        self._title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form.addRow(self._make_label("Title:"), self._title)

        self._description = QTextEdit()
        self._description.setPlaceholderText("Short description of the case")
        self._description.setMinimumHeight(90)
        self._description.setMaximumHeight(160)
        self._description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form.addRow(self._make_label("Description:"), self._description)

        self._examiner_name = QLineEdit()
        self._examiner_name.setPlaceholderText("Your full name")
        self._examiner_name.setMinimumHeight(self._tokens.input_height)
        self._examiner_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form.addRow(self._make_label("Examiner Name:"), self._examiner_name)

        self._organisation = QLineEdit()
        self._organisation.setMinimumHeight(self._tokens.input_height)
        self._organisation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form.addRow(self._make_label("Organisation:"), self._organisation)

        self._timezone = QComboBox()
        self._timezone.addItems(["UTC", "Asia/Kolkata", "America/New_York", "Europe/London", "Asia/Dubai"])
        self._timezone.setMinimumHeight(self._tokens.input_height)
        self._timezone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form.addRow(self._make_label("Display Time Zone:"), self._timezone)

        card_layout.addLayout(form)

        # Storage location group box
        location_group = QGroupBox("Case Storage Location")
        loc_layout = QVBoxLayout()
        loc_layout.setContentsMargins(12, 16, 12, 12)
        loc_layout.setSpacing(8)
        loc_row = QHBoxLayout()
        loc_row.setSpacing(8)
        self._location_path = QLineEdit(str(self._case_dir))
        self._location_path.setMinimumHeight(self._tokens.input_height)
        self._location_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setMinimumHeight(self._tokens.input_height)
        browse_btn.clicked.connect(self._on_browse_location)
        loc_row.addWidget(self._location_path, 1)
        loc_row.addWidget(browse_btn)
        loc_layout.addLayout(loc_row)
        location_group.setLayout(loc_layout)
        card_layout.addWidget(location_group)

        # Authority checkbox
        self._auth_check = QCheckBox("I have lawful authority to conduct this examination")
        self._auth_check.setStyleSheet(
            f"color: {self._tokens.warning}; font-weight: {self._tokens.font_weight_semibold};"
        )
        card_layout.addWidget(self._auth_check)

        # Action row: right-aligned Create Case button
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.addStretch()
        self._create_btn = NeonButton("Create Case", "primary")
        self._create_btn.setMinimumWidth(180)
        self._create_btn.setMinimumHeight(self._tokens.button_height)
        self._create_btn.clicked.connect(self._on_create)
        action_row.addWidget(self._create_btn)
        card_layout.addLayout(action_row)

        page_layout.addWidget(card)
        page_layout.addStretch()

    def _make_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setMinimumWidth(_FORM_LABEL_MIN_WIDTH)
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        label.setObjectName("formLabel")
        return label

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
