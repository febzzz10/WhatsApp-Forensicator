from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QPushButton, QScrollArea, QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from wft.bootstrap import Container
from wft.application.services.case_context import ActiveCaseContext
from wft.application.services.adb_service import AdbService
from wft.ui.components import PageHeader, NeonButton


class SettingsPage(QWidget):
    def __init__(self, container: Optional[Container] = None, ctx: Optional[ActiveCaseContext] = None) -> None:
        super().__init__()
        self._container = container
        self._ctx = ctx
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        header = PageHeader("Settings", "Configure application and case preferences")
        layout.addWidget(header)

        general_group = QGroupBox("General")
        general_layout = QFormLayout()
        general_layout.setSpacing(8)
        self._data_dir = QLineEdit()
        self._data_dir.setPlaceholderText("Default data directory for cases")
        general_layout.addRow("Data Directory:", self._data_dir)
        self._timezone = QComboBox()
        self._timezone.addItems(["UTC", "Asia/Kolkata", "America/New_York", "Europe/London", "Asia/Dubai"])
        general_layout.addRow("Display Time Zone:", self._timezone)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        security_group = QGroupBox("Security")
        security_layout = QFormLayout()
        security_layout.setSpacing(8)
        self._encryption = QCheckBox("Enable case encryption by default")
        self._auto_lock = QSpinBox()
        self._auto_lock.setRange(0, 120)
        self._auto_lock.setValue(15)
        self._auto_lock.setSuffix(" minutes")
        self._auto_lock.setSpecialValueText("Disabled")
        security_layout.addRow(self._encryption)
        security_layout.addRow("Auto-lock after:", self._auto_lock)
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        diagnostics_group = QGroupBox("Diagnostics")
        diagnostics_layout = QFormLayout()
        self._log_level = QComboBox()
        self._log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        diagnostics_layout.addRow("Log Level:", self._log_level)
        diagnostics_group.setLayout(diagnostics_layout)
        layout.addWidget(diagnostics_group)

        adb_group = QGroupBox("ADB (Android Debug Bridge)")
        adb_layout = QFormLayout()
        adb_layout.setSpacing(8)
        adb_path_row = QHBoxLayout()
        self._adb_path = QLineEdit()
        self._adb_path.setPlaceholderText("Path to adb.exe (leave empty for auto-detect)")
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.clicked.connect(self._on_adb_browse)
        test_btn = QPushButton("Test")
        test_btn.setObjectName("secondaryButton")
        test_btn.clicked.connect(self._on_adb_test)
        adb_path_row.addWidget(self._adb_path, 1)
        adb_path_row.addWidget(browse_btn)
        adb_path_row.addWidget(test_btn)
        adb_layout.addRow("ADB Path:", adb_path_row)
        self._adb_auto_detect = QCheckBox("Auto-detect ADB binary")
        self._adb_auto_detect.setChecked(True)
        adb_layout.addRow(self._adb_auto_detect)
        self._adb_poll_interval = QSpinBox()
        self._adb_poll_interval.setRange(2, 30)
        self._adb_poll_interval.setValue(3)
        self._adb_poll_interval.setSuffix(" seconds")
        adb_layout.addRow("Poll interval:", self._adb_poll_interval)
        adb_group.setLayout(adb_layout)
        layout.addWidget(adb_group)

        save_btn = NeonButton("Save Settings", "primary")
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

        layout.addStretch()
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.addWidget(scroll)

    def _load_settings(self) -> None:
        if not self._container:
            return
        s = self._container.settings
        self._data_dir.setText(s.data_dir or "")
        self._log_level.setCurrentText(s.log_level or "INFO")
        self._auto_lock.setValue(s.security.auto_lock_minutes)
        self._adb_path.setText(s.adb.adb_path or "")
        self._adb_auto_detect.setChecked(s.adb.auto_detect)
        self._adb_poll_interval.setValue(s.adb.poll_interval_seconds)

    def _on_adb_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select ADB Binary", "", "ADB (adb.exe adb);;All Files (*)"
        )
        if path:
            self._adb_path.setText(path)

    def _on_adb_test(self) -> None:
        path_str = self._adb_path.text().strip()
        if not path_str:
            QMessageBox.information(self, "ADB Test", "No path entered. Auto-detect will search PATH and SDK locations.")
            return
        test_service = AdbService(configured_path=path_str)
        version = test_service.validate_path(path_str)
        if version:
            QMessageBox.information(
                self, "ADB Test",
                f"ADB binary validated successfully.\n\n{version.split(chr(10))[0]}"
            )
        else:
            QMessageBox.warning(
                self, "ADB Test",
                "ADB binary not found or not responding at the specified path."
            )

    def _on_save(self) -> None:
        if not self._container:
            QMessageBox.warning(self, "Error", "Container not available.")
            return
        try:
            s = self._container.settings
            s.data_dir = self._data_dir.text().strip()
            s.log_level = self._log_level.currentText()
            s.security.auto_lock_minutes = self._auto_lock.value()
            s.adb.adb_path = self._adb_path.text().strip()
            s.adb.auto_detect = self._adb_auto_detect.isChecked()
            s.adb.poll_interval_seconds = self._adb_poll_interval.value()

            settings_path = Path.home() / ".wft" / "settings.toml"
            settings_path.parent.mkdir(parents=True, exist_ok=True)

            import tomli_w
            data = {
                "data_dir": s.data_dir,
                "log_level": s.log_level,
                "adb": {
                    "adb_path": s.adb.adb_path,
                    "auto_detect": s.adb.auto_detect,
                    "poll_interval_seconds": s.adb.poll_interval_seconds,
                },
                "security": {
                    "auto_lock_minutes": s.security.auto_lock_minutes,
                    "require_authorisation_acknowledgement": s.security.require_authorisation_acknowledgement,
                    "telemetry": s.security.telemetry,
                    "allow_external_services": s.security.allow_external_services,
                },
                "hashing": {"primary": s.hashing.primary, "secondary": s.hashing.secondary},
                "parsing": {
                    "open_source_databases_read_only": s.parsing.open_source_databases_read_only,
                    "preserve_unknown_columns": s.parsing.preserve_unknown_columns,
                    "store_raw_timestamp_values": s.parsing.store_raw_timestamp_values,
                },
                "reports": {
                    "include_limitations": s.reports.include_limitations,
                    "include_tool_versions": s.reports.include_tool_versions,
                    "include_manifest_hash": s.reports.include_manifest_hash,
                },
            }
            with settings_path.open("wb") as f:
                tomli_w.dump(data, f)

            QMessageBox.information(self, "Settings", "Settings saved successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{exc}")
