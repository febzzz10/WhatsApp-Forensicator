from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QFormLayout, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QFileDialog, QSplitter,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, EvidenceBanner, EmptyState


class DecryptorPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = PageHeader("Decryptor", "Decrypt WhatsApp backups and load databases")
        layout.addWidget(header)

        banner = EvidenceBanner(
            "Decryption is available only for supported formats when lawful key material is provided. "
            "The application does not crack passwords or bypass account security.",
            "warning",
        )
        layout.addWidget(banner)

        self._case_status = QLabel("")
        self._case_status.setObjectName("mutedLabel")
        layout.addWidget(self._case_status)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        decrypt_group = QGroupBox("Decrypt Backup")
        decrypt_form = QFormLayout()
        decrypt_form.setSpacing(8)

        self._encrypted_path = QLineEdit()
        self._encrypted_path.setPlaceholderText("Select encrypted backup file...")
        browse_enc = QPushButton("Browse")
        browse_enc.setObjectName("secondaryButton")

        enc_row = QHBoxLayout()
        enc_row.addWidget(self._encrypted_path, 1)
        enc_row.addWidget(browse_enc)
        decrypt_form.addRow("Encrypted Backup:", enc_row)

        self._detected_format = QLabel("No file selected")
        self._detected_format.setObjectName("mutedLabel")
        decrypt_form.addRow("Detected Format:", self._detected_format)

        self._key_material = QLineEdit()
        self._key_material.setPlaceholderText("Enter or select lawful key material")
        self._key_material.setEchoMode(QLineEdit.Password)
        decrypt_form.addRow("Key Material:", self._key_material)

        decrypt_group.setLayout(decrypt_form)
        left_layout.addWidget(decrypt_group)

        left_layout.addWidget(NeonButton("Start Decryption", "primary"))

        left_layout.addStretch()
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        load_group = QGroupBox("Load Existing Database")
        load_form = QFormLayout()
        load_form.setSpacing(8)

        self._msg_db = QLineEdit()
        msg_browse = QPushButton("Browse")
        msg_browse.setObjectName("secondaryButton")
        msg_row = QHBoxLayout()
        msg_row.addWidget(self._msg_db, 1)
        msg_row.addWidget(msg_browse)
        load_form.addRow("Message DB:", msg_row)

        self._contacts_db = QLineEdit()
        cont_browse = QPushButton("Browse")
        cont_browse.setObjectName("secondaryButton")
        cont_row = QHBoxLayout()
        cont_row.addWidget(self._contacts_db, 1)
        cont_row.addWidget(cont_browse)
        load_form.addRow("Contacts DB:", cont_row)

        load_group.setLayout(load_form)
        right_layout.addWidget(load_group)

        right_layout.addWidget(NeonButton("Load and Validate Database", "primary"))

        right_layout.addStretch()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

    def on_activated(self) -> None:
        if self._ctx.is_active:
            self._case_status.setText(f"Active Case: {self._ctx.case_path.name} (ID: {self._ctx.case_id})")
        else:
            self._case_status.setText("No case open.")
