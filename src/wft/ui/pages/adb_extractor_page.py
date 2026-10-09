import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QRunnable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QGroupBox, QPushButton,
    QComboBox, QPlainTextEdit, QFrame, QSplitter, QMessageBox, QCheckBox,
    QSpinBox, QSizePolicy, QScrollArea,
)
from PySide6.QtGui import QFont

from wft.bootstrap import Container
from wft.application.services.case_context import ActiveCaseContext
from wft.application.services.adb_service import AdbService, AdbDevice, AdbState, AdbError
from wft.ui.components import PageHeader, NeonButton, StatusBadge, EvidenceBanner, EmptyState
from wft.ui.workers.adb_scan_worker import (
    AdbOperationWorker, AdbOperationType, run_adb_operation,
)
from wft.ui.workers.worker_base import CancellationToken, thread_pool
from wft.ui.utils.font_utils import ensure_valid_font_size

EXTRACT_DBS_READY_TOOLTIP = (
    "Acquires WhatsApp database files (msgstore, wa.db, crypt12/14/15 backups) "
    "as evidence. Acquisition only - backups are NOT decrypted here."
)


def _redact_serial(serial: str) -> str:
    if len(serial) <= 8:
        return serial
    return serial[:4] + "****" + serial[-4:]


def _make_scan_signature(devices: list[AdbDevice], adb_state: AdbState) -> tuple:
    return (
        adb_state.value,
        tuple(sorted((d.serial, d.state.value) for d in devices)),
    )


STATE_BANNER: dict[AdbState, tuple[str, str]] = {
    AdbState.NO_ADB: (
        "ADB binary not found. Install Android SDK platform-tools or configure path in Settings.",
        "warning",
    ),
    AdbState.ADB_SERVER_ERROR: (
        "ADB server is not responding. Click 'Start Server' or restart ADB.",
        "warning",
    ),
    AdbState.CONNECTED: (
        "ADB server running.",
        "verified",
    ),
}

DEVICE_BANNER: dict[AdbState, tuple[str, str]] = {
    AdbState.UNAUTHORIZED: (
        "Device is unauthorised. Accept the RSA fingerprint prompt on the device and click Refresh.",
        "warning",
    ),
    AdbState.OFFLINE: (
        "Device is offline. Check USB connection and ensure the device is unlocked.",
        "warning",
    ),
    AdbState.NO_PERMISSIONS: (
        "Insufficient permissions to access the device. Check USB debugging settings.",
        "hash_mismatch",
    ),
    AdbState.BOOTLOADER: (
        "Device is in bootloader mode. Not available for ADB commands.",
        "unsupported",
    ),
    AdbState.RECOVERY: (
        "Device is in recovery mode. Limited ADB access available.",
        "info",
    ),
    AdbState.UNKNOWN: (
        "Device is in an unknown state. Try reconnecting USB or restarting ADB server.",
        "warning",
    ),
}

MAX_LOG_ENTRIES = 500


def _make_device_details_cache_key(
    serial: str, state: AdbState, scan_signature: tuple
) -> tuple:
    return (serial, state.value)


class ADBExtractorPage(QWidget):
    def __init__(self, container: Container, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._container = container
        self._ctx = ctx
        self._configured_path: Optional[str] = container.settings.adb.adb_path
        self._worker: Optional[AdbOperationWorker] = None
        self._details_worker: Optional[AdbOperationWorker] = None
        self._pending_workers: set[QRunnable] = set()
        self._adb_operation_workers: set[AdbOperationWorker] = set()
        self._authorised_ops_in_progress: set[AdbOperationType] = set()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._on_poll_timeout)
        self._polling_active = False
        self._scan_in_progress = False
        self._server_op_in_progress = False
        self._server_intentionally_stopped = False
        self._request_counter = 0
        self._devices: list[AdbDevice] = []
        self._last_scan_signature: Optional[tuple] = None
        self._details_cache: dict[tuple, AdbDevice] = {}
        self._log_entries: list[str] = []
        self._build_ui()
        self._update_case_state()
        self._ctx.case_changed.connect(lambda _cid, _cp: self._update_case_state())

    def _make_info_label(self) -> QLabel:
        lbl = QLabel("—")
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lbl.setMinimumHeight(22)
        lbl.setWordWrap(False)
        ensure_valid_font_size(lbl, 10)
        return lbl

    def _make_info_field(self) -> QLabel:
        lbl = QLabel("")
        lbl.setObjectName("mutedLabel")
        lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        lbl.setMinimumWidth(130)
        lbl.setMinimumHeight(22)
        ensure_valid_font_size(lbl, 10)
        return lbl

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 8, 14, 8)

        header = PageHeader("ADB Extractor", "Android Debug Bridge evidence acquisition")
        root.addWidget(header)

        self._adb_banner = EvidenceBanner("Initialising ADB detection...", "info")
        root.addWidget(self._adb_banner)

        self._device_banner = EvidenceBanner("", "info")
        self._device_banner.setVisible(False)
        root.addWidget(self._device_banner)

        self._case_banner = EvidenceBanner(
            "No case is open. Open or create a case before importing or recording evidence.",
            "warning",
        )
        root.addWidget(self._case_banner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_panel.setMinimumWidth(620)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(0, 0, 0, 0)

        device_group = QGroupBox("Devices")
        device_outer = QVBoxLayout(device_group)
        device_outer.setSpacing(10)
        device_outer.setContentsMargins(12, 4, 12, 12)

        selector_row = QHBoxLayout()
        selector_row.setSpacing(8)
        selector_label = QLabel("Device:")
        selector_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self._device_selector = QComboBox()
        self._device_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._device_selector.setMinimumWidth(320)
        self._device_selector.setMaximumWidth(800)
        self._device_selector.currentIndexChanged.connect(self._on_device_selected)
        self._device_status_badge = StatusBadge("No device", "unsupported")
        self._device_status_badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        selector_row.addWidget(selector_label)
        selector_row.addWidget(self._device_selector, 1)
        selector_row.addWidget(self._device_status_badge)
        device_outer.addLayout(selector_row)

        info_grid = QGridLayout()
        info_grid.setContentsMargins(0, 8, 0, 8)
        info_grid.setHorizontalSpacing(24)
        info_grid.setVerticalSpacing(8)

        self._manufacturer_label = self._make_info_field()
        self._manufacturer_label.setText("Manufacturer:")
        self._manufacturer_value = self._make_info_label()
        self._model_label = self._make_info_field()
        self._model_label.setText("Model:")
        self._model_value = self._make_info_label()
        self._android_version_label = self._make_info_field()
        self._android_version_label.setText("Android Version:")
        self._android_version_value = self._make_info_label()
        self._sdk_version_label = self._make_info_field()
        self._sdk_version_label.setText("SDK Version:")
        self._sdk_version_value = self._make_info_label()
        self._serial_label = self._make_info_field()
        self._serial_label.setText("Serial:")
        self._serial_value = self._make_info_label()
        serial_font = self._serial_value.font()
        serial_font.setFamily("Consolas, 'Courier New', monospace")
        self._serial_value.setFont(serial_font)
        self._transport_id_label = self._make_info_field()
        self._transport_id_label.setText("Transport ID:")
        self._transport_id_value = self._make_info_label()
        tid_font = self._transport_id_value.font()
        tid_font.setFamily("Consolas, 'Courier New', monospace")
        self._transport_id_value.setFont(tid_font)
        self._connection_type_label = self._make_info_field()
        self._connection_type_label.setText("Connection Type:")
        self._connection_type_value = self._make_info_label()
        self._authorisation_label = self._make_info_field()
        self._authorisation_label.setText("Authorisation State:")
        self._authorisation_value = self._make_info_label()

        fields = [
            (self._manufacturer_label, self._manufacturer_value, 0),
            (self._model_label, self._model_value, 1),
            (self._android_version_label, self._android_version_value, 2),
            (self._sdk_version_label, self._sdk_version_value, 3),
            (self._serial_label, self._serial_value, 4),
            (self._transport_id_label, self._transport_id_value, 5),
            (self._connection_type_label, self._connection_type_value, 6),
            (self._authorisation_label, self._authorisation_value, 7),
        ]
        for lbl, val, row in fields:
            info_grid.addWidget(lbl, row, 0)
            info_grid.addWidget(val, row, 1)

        device_outer.addLayout(info_grid)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self._scan_btn = NeonButton("Refresh Devices", "primary")
        self._scan_btn.clicked.connect(self._on_refresh)
        self._start_server_btn = QPushButton("Start Server")
        self._start_server_btn.setObjectName("secondaryButton")
        self._start_server_btn.clicked.connect(self._on_start_server)
        self._kill_server_btn = QPushButton("Kill Server")
        self._kill_server_btn.setObjectName("secondaryButton")
        self._kill_server_btn.clicked.connect(self._on_kill_server)
        self._troubleshoot_btn = QPushButton("Troubleshoot")
        self._troubleshoot_btn.setObjectName("secondaryButton")
        self._troubleshoot_btn.clicked.connect(self._on_troubleshoot)

        for btn in [self._scan_btn, self._start_server_btn, self._kill_server_btn, self._troubleshoot_btn]:
            btn.setMinimumHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        action_row.addWidget(self._scan_btn)
        action_row.addWidget(self._start_server_btn)
        action_row.addWidget(self._kill_server_btn)
        action_row.addWidget(self._troubleshoot_btn)
        device_outer.addLayout(action_row)

        auto_row = QHBoxLayout()
        auto_row.setSpacing(8)

        self._auto_detect_cb = QCheckBox("Auto-detect devices")
        self._auto_detect_cb.setChecked(True)
        self._auto_detect_cb.stateChanged.connect(self._on_auto_detect_changed)
        auto_row.addWidget(self._auto_detect_cb)
        auto_row.addStretch()

        poll_label = QLabel("Poll interval:")
        poll_label.setObjectName("mutedLabel")
        auto_row.addWidget(poll_label)

        self._poll_interval_spin = QSpinBox()
        self._poll_interval_spin.setMinimum(2)
        self._poll_interval_spin.setMaximum(30)
        self._poll_interval_spin.setValue(self._container.settings.adb.poll_interval_seconds)
        self._poll_interval_spin.setSuffix(" s")
        self._poll_interval_spin.setFixedWidth(80)
        self._poll_interval_spin.valueChanged.connect(self._on_poll_interval_changed)
        auto_row.addWidget(self._poll_interval_spin)
        device_outer.addLayout(auto_row)

        left_layout.addWidget(device_group)

        authorised_group = QGroupBox("Authorised Actions")
        authorised_layout = QVBoxLayout()
        authorised_layout.setSpacing(8)
        authorised_layout.setContentsMargins(12, 4, 12, 12)

        self._import_export_btn = QPushButton("Import User Export")
        self._import_export_btn.setObjectName("secondaryButton")
        self._copy_media_btn = QPushButton("Copy Accessible Media")
        self._copy_media_btn.setObjectName("secondaryButton")
        self._record_metadata_btn = QPushButton("Record Device Metadata")
        self._record_metadata_btn.setObjectName("secondaryButton")
        self._extract_dbs_btn = QPushButton("Extract WhatsApp Databases")
        self._extract_dbs_btn.setObjectName("secondaryButton")

        for btn in [self._import_export_btn, self._copy_media_btn, self._record_metadata_btn,
                    self._extract_dbs_btn]:
            btn.setEnabled(False)
            btn.setMinimumHeight(42)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setToolTip("Open or create a forensic case before acquiring evidence.")

        self._extract_dbs_btn.setToolTip(EXTRACT_DBS_READY_TOOLTIP)

        self._import_export_btn.clicked.connect(self._on_import_user_export)
        self._copy_media_btn.clicked.connect(self._on_copy_accessible_media)
        self._record_metadata_btn.clicked.connect(self._on_record_device_metadata)
        self._extract_dbs_btn.clicked.connect(self._on_extract_whatsapp_databases)

        authorised_layout.addWidget(self._import_export_btn)
        authorised_layout.addWidget(self._copy_media_btn)
        authorised_layout.addWidget(self._record_metadata_btn)
        authorised_layout.addWidget(self._extract_dbs_btn)
        authorised_group.setLayout(authorised_layout)
        left_layout.addWidget(authorised_group)
        left_layout.addStretch()

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_panel.setMinimumWidth(320)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)

        log_group = QGroupBox("Acquisition Log")
        log_outer = QVBoxLayout(log_group)
        log_outer.setSpacing(8)
        log_outer.setContentsMargins(12, 4, 12, 12)

        log_btn_row = QHBoxLayout()
        self._clear_log_btn = QPushButton("Clear Log")
        self._clear_log_btn.setObjectName("secondaryButton")
        self._clear_log_btn.setMinimumHeight(36)
        self._clear_log_btn.clicked.connect(self._on_clear_log)
        self._clear_log_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        log_btn_row.addStretch()
        log_btn_row.addWidget(self._clear_log_btn)
        log_outer.addLayout(log_btn_row)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("ADB session log will appear here...")
        log_font = self._log.font()
        log_size = log_font.pointSize()
        if log_size <= 0:
            log_size = 10
        log_font.setPointSize(log_size)
        log_font.setFamily("Consolas, 'Courier New', monospace")
        self._log.setFont(log_font)
        self._log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._log.setMinimumWidth(280)
        self._log.verticalScrollBar().rangeChanged.connect(self._on_log_scroll_range)
        self._log_auto_scroll = True
        self._log.setMaximumBlockCount(MAX_LOG_ENTRIES)
        log_outer.addWidget(self._log, 1)

        right_layout.addWidget(log_group, 1)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([600, 400])

        scroll_layout.addWidget(splitter, 1)
        scroll.setWidget(scroll_content)
        root.addWidget(scroll, 1)

        self._field_labels: dict[str, QLabel] = {
            "Manufacturer": self._manufacturer_label,
            "Model": self._model_label,
            "Android Version": self._android_version_label,
            "SDK Version": self._sdk_version_label,
            "Serial": self._serial_label,
            "Transport ID": self._transport_id_label,
            "Connection Type": self._connection_type_label,
            "Authorisation State": self._authorisation_label,
        }
        self._field_values: dict[str, QLabel] = {
            "Manufacturer": self._manufacturer_value,
            "Model": self._model_value,
            "Android Version": self._android_version_value,
            "SDK Version": self._sdk_version_value,
            "Serial": self._serial_value,
            "Transport ID": self._transport_id_value,
            "Connection Type": self._connection_type_value,
            "Authorisation State": self._authorisation_value,
        }

    def _on_log_scroll_range(self, _min: int, _max: int) -> None:
        sb = self._log.verticalScrollBar()
        if sb.value() >= sb.maximum() - 20:
            self._log_auto_scroll = True
        else:
            self._log_auto_scroll = False

    def on_activated(self) -> None:
        self._start_polling()
        if not self._last_scan_signature:
            self._start_device_scan(manual=False)

    def on_deactivated(self) -> None:
        self._stop_polling()

    def _update_case_state(self) -> None:
        has_case = self._ctx.is_active
        self._case_banner.setVisible(not has_case)
        self._update_authorised_actions()

    def _update_authorised_actions(self) -> None:
        has_case = self._ctx.is_active
        device_connected = any(d.state == AdbState.CONNECTED for d in self._devices)
        base_enabled = has_case and device_connected
        btn_ops = [
            (self._import_export_btn, AdbOperationType.IMPORT_USER_EXPORT),
            (self._copy_media_btn, AdbOperationType.COPY_ACCESSIBLE_MEDIA),
            (self._record_metadata_btn, AdbOperationType.RECORD_DEVICE_METADATA),
            (self._extract_dbs_btn, AdbOperationType.EXTRACT_WHATSAPP_DATABASES),
        ]
        for btn, op in btn_ops:
            in_progress = op in self._authorised_ops_in_progress
            btn.setEnabled(base_enabled and not in_progress)
            if in_progress:
                btn.setToolTip("Operation in progress...")
            elif not has_case:
                btn.setToolTip("Open or create a forensic case before acquiring evidence.")
            elif not device_connected:
                btn.setToolTip("Connect and authorise a device before acquiring evidence.")
            elif btn is self._extract_dbs_btn:
                btn.setToolTip(EXTRACT_DBS_READY_TOOLTIP)
            else:
                btn.setToolTip("")

    def _start_polling(self) -> None:
        if self._polling_active:
            return
        if not self._auto_detect_cb.isChecked():
            return
        interval = max(self._poll_interval_spin.value(), 2) * 1000
        self._poll_timer.start(interval)
        self._polling_active = True
        self._log_message("Auto-detection started — interval {} seconds".format(
            self._poll_interval_spin.value()
        ))

    def _stop_polling(self) -> None:
        if not self._polling_active:
            return
        self._poll_timer.stop()
        self._polling_active = False
        self._log_message("Auto-detection stopped")

    def _on_poll_interval_changed(self, value: int) -> None:
        if self._polling_active:
            self._poll_timer.setInterval(max(value, 2) * 1000)

    def _on_poll_timeout(self) -> None:
        if not self.isVisible():
            return
        if self._scan_in_progress or self._server_op_in_progress:
            return
        if self._server_intentionally_stopped:
            return
        if not self._auto_detect_cb.isChecked():
            self._stop_polling()
            return
        self._start_device_scan(manual=False)

    def _start_device_scan(self, manual: bool = False) -> None:
        if self._scan_in_progress:
            return
        self._scan_in_progress = True
        self._scan_btn.setEnabled(False)
        if manual:
            self._log_message("Manual refresh triggered")

        token = CancellationToken()
        worker = AdbOperationWorker(
            operation=AdbOperationType.SCAN,
            configured_path=self._configured_path,
            timeout=10,
            token=token,
        )
        self._pending_workers.add(worker)

        request_id = self._request_counter
        self._request_counter += 1

        def on_finished(result: object) -> None:
            self._pending_workers.discard(worker)
            if token.cancelled:
                return
            self._on_scan_result(result, request_id)

        def on_error(error_msg: str) -> None:
            self._pending_workers.discard(worker)
            if token.cancelled:
                return
            self._on_scan_error(error_msg)

        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(on_error)
        thread_pool.start(worker)

    def _on_scan_result(self, result: object, request_id: int) -> None:
        if request_id != self._request_counter - 1:
            return
        self._scan_in_progress = False
        self._scan_btn.setEnabled(True)

        if not isinstance(result, tuple) or len(result) != 2:
            return

        adb_state, devices = result
        if not isinstance(devices, list):
            return

        new_signature = _make_scan_signature(devices, adb_state)
        old_signature = self._last_scan_signature
        self._last_scan_signature = new_signature
        self._devices = devices

        self._update_adb_banner(adb_state)
        self._update_device_selector(devices)
        self._update_authorised_actions()
        self._log_changes(old_signature, new_signature, devices, adb_state)

        if self._device_selector.count() > 0:
            self._on_device_selected(0)

    def _on_scan_error(self, error_msg: str) -> None:
        self._scan_in_progress = False
        self._scan_btn.setEnabled(True)
        self._log_message("Scan error: {}".format(error_msg))
        self._last_scan_signature = None

    def _fetch_device_details_async(self, serial: str) -> None:
        if self._details_worker is not None:
            self._details_worker.cancel()

        cache_key = _make_device_details_cache_key(
            serial, AdbState.CONNECTED, self._last_scan_signature or (),
        )
        if cache_key in self._details_cache:
            self._apply_device_details(self._details_cache[cache_key])
            return

        token = CancellationToken()
        worker = AdbOperationWorker(
            operation=AdbOperationType.DEVICE_DETAILS,
            configured_path=self._configured_path,
            serial=serial,
            timeout=10,
            token=token,
        )
        self._details_worker = worker
        self._pending_workers.add(worker)

        def on_finished(result: object) -> None:
            self._pending_workers.discard(worker)
            if self._details_worker is worker:
                self._details_worker = None
            if token.cancelled or not isinstance(result, AdbDevice):
                return
            self._details_cache[cache_key] = result
            self._apply_device_details(result)

        def on_error(error_msg: str) -> None:
            self._pending_workers.discard(worker)
            if self._details_worker is worker:
                self._details_worker = None

        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(on_error)
        thread_pool.start(worker)

    def _log_changes(
        self,
        old_sig: Optional[tuple],
        new_sig: tuple,
        devices: list[AdbDevice],
        adb_state: AdbState,
    ) -> None:
        if new_sig == old_sig:
            return

        if old_sig is None:
            if adb_state == AdbState.CONNECTED and devices:
                for d in devices:
                    self._log_message(
                        "Device connected: {} ({})".format(d.model or "Unknown", _redact_serial(d.serial))
                    )
            elif adb_state == AdbState.CONNECTED and not devices:
                self._log_message("ADB server running — no devices detected")
            elif adb_state == AdbState.NO_ADB:
                self._log_message("ADB binary not found")
            elif adb_state == AdbState.ADB_SERVER_ERROR:
                self._log_message("ADB server not responding")
            return

        old_devices = {}
        old_adb_state_str = old_sig[0] if old_sig else ""
        old_devices = dict(old_sig[1]) if old_sig and len(old_sig) > 1 else {}

        new_devices = dict(new_sig[1]) if len(new_sig) > 1 else {}

        if old_adb_state_str != new_sig[0]:
            if new_sig[0] == AdbState.CONNECTED.value:
                self._log_message("ADB server connected")
            elif new_sig[0] in (AdbState.NO_ADB.value, AdbState.ADB_SERVER_ERROR.value):
                self._log_message("ADB server disconnected")

        for serial, state_val in new_devices.items():
            old_state_val = old_devices.get(serial)
            if old_state_val is None:
                self._log_message("Device connected: {} ({})".format(
                    self._get_model_for_serial(serial) or "Unknown",
                    _redact_serial(serial),
                ))
            elif old_state_val != state_val:
                self._log_message(
                    "Device state changed: {} → {} ({})".format(old_state_val, state_val, _redact_serial(serial))
                )

        for serial in old_devices:
            if serial not in new_devices:
                self._log_message("Device disconnected: {}".format(_redact_serial(serial)))

    def _get_model_for_serial(self, serial: str) -> Optional[str]:
        for d in self._devices:
            if d.serial == serial:
                return d.model
        return None

    def _on_refresh(self) -> None:
        self._server_intentionally_stopped = False
        self._start_device_scan(manual=True)

    def _on_device_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._devices):
            self._clear_device_info()
            self._device_banner.setVisible(False)
            self._update_authorised_actions()
            return
        device = self._devices[index]
        self._update_device_info(device)
        self._update_device_banner(device)
        self._update_authorised_actions()

        if device.state == AdbState.CONNECTED:
            self._fetch_device_details_async(device.serial)

    def _update_adb_banner(self, state: AdbState) -> None:
        if state in STATE_BANNER:
            text, btype = STATE_BANNER[state]
            if state == AdbState.CONNECTED:
                count = len(self._devices)
                if count == 0:
                    text = "ADB server running — no devices detected."
                elif count == 1:
                    text = "ADB server running. One authorised device detected."
                else:
                    text = "ADB server running. {} devices detected.".format(count)
            self._adb_banner.set_text(text)
            self._adb_banner.set_banner_type(btype)
        else:
            self._adb_banner.set_text("ADB server is running.")
            self._adb_banner.set_banner_type("verified")

    def _update_device_banner(self, device: AdbDevice) -> None:
        if device.state in DEVICE_BANNER:
            text, btype = DEVICE_BANNER[device.state]
            self._device_banner.set_text(text)
            self._device_banner.set_banner_type(btype)
            self._device_banner.setVisible(True)
        else:
            self._device_banner.setVisible(False)

    def _update_device_selector(self, devices: list[AdbDevice]) -> None:
        current_serial = self._device_selector.currentData()
        self._device_selector.blockSignals(True)
        self._device_selector.clear()
        if not devices:
            self._device_selector.addItem("No devices detected", None)
        else:
            for dev in devices:
                badge = dev.state.value.capitalize()
                label = "{} — {} — {}".format(
                    dev.model or "Unknown",
                    _redact_serial(dev.serial),
                    badge,
                )
                self._device_selector.addItem(label, dev.serial)
                item_idx = self._device_selector.count() - 1
                self._device_selector.setItemData(item_idx, dev.serial, Qt.ToolTipRole)
        if current_serial:
            idx = self._device_selector.findData(current_serial)
            if idx >= 0:
                self._device_selector.setCurrentIndex(idx)
        self._device_selector.blockSignals(False)

    def _update_device_info(self, device: AdbDevice) -> None:
        self._manufacturer_value.setText(device.manufacturer or "—")
        self._model_value.setText(device.model or "—")
        self._android_version_value.setText(device.android_version or "—")
        self._sdk_version_value.setText(device.sdk_version or "—")
        self._serial_value.setText(_redact_serial(device.serial))
        self._serial_value.setToolTip("Full serial: {}".format(device.serial))
        self._transport_id_value.setText(device.transport_id or "—")
        self._connection_type_value.setText(device.connection_type)
        self._authorisation_value.setText(device.state.value.capitalize())

        badge_type = {
            AdbState.CONNECTED: "verified",
            AdbState.UNAUTHORIZED: "unverified",
            AdbState.OFFLINE: "unsupported",
            AdbState.NO_PERMISSIONS: "failed",
            AdbState.UNKNOWN: "unsupported",
            AdbState.BOOTLOADER: "unsupported",
            AdbState.RECOVERY: "partial",
        }.get(device.state, "unsupported")
        self._device_status_badge.setText(device.state.value.upper())
        self._device_status_badge.set_badge_type(badge_type)

    def _apply_device_details(self, device: AdbDevice) -> None:
        self._manufacturer_value.setText(device.manufacturer or "—")
        self._model_value.setText(device.model or "—")
        self._android_version_value.setText(device.android_version or "—")
        self._sdk_version_value.setText(device.sdk_version or "—")
        self._connection_type_value.setText(device.connection_type or "USB")

    def _clear_device_info(self) -> None:
        for field_name in self._field_values:
            self._field_values[field_name].setText("—")
        self._serial_value.setToolTip("")
        self._device_status_badge.setText("No device")
        self._device_status_badge.set_badge_type("unsupported")

    def _on_start_server(self) -> None:
        if self._server_op_in_progress:
            return
        self._server_op_in_progress = True
        self._server_intentionally_stopped = False
        self._set_server_buttons_enabled(False)
        self._log_message("Starting ADB server...")

        token = CancellationToken()
        worker = AdbOperationWorker(
            operation=AdbOperationType.START_SERVER,
            configured_path=self._configured_path,
            timeout=15,
            token=token,
        )
        self._pending_workers.add(worker)

        def on_finished(result: object) -> None:
            self._pending_workers.discard(worker)
            self._server_op_in_progress = False
            self._set_server_buttons_enabled(True)
            self._log_message("ADB server started")
            self._start_device_scan(manual=False)

        def on_error(error_msg: str) -> None:
            self._pending_workers.discard(worker)
            self._server_op_in_progress = False
            self._set_server_buttons_enabled(True)
            self._log_message("Failed to start ADB server: {}".format(error_msg))

        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(on_error)
        thread_pool.start(worker)

    def _on_kill_server(self) -> None:
        if self._server_op_in_progress:
            return
        self._server_op_in_progress = True
        self._server_intentionally_stopped = True
        self._set_server_buttons_enabled(False)
        self._stop_polling()
        self._log_message("Killing ADB server...")

        token = CancellationToken()
        worker = AdbOperationWorker(
            operation=AdbOperationType.KILL_SERVER,
            configured_path=self._configured_path,
            timeout=10,
            token=token,
        )
        self._pending_workers.add(worker)

        def on_finished(result: object) -> None:
            self._pending_workers.discard(worker)
            self._server_op_in_progress = False
            self._set_server_buttons_enabled(True)
            self._log_message("ADB server killed")
            self._clear_device_info()
            self._devices = []
            self._last_scan_signature = None
            self._details_cache.clear()
            self._update_device_selector([])
            self._update_adb_banner(AdbState.ADB_SERVER_ERROR)

        def on_error(error_msg: str) -> None:
            self._pending_workers.discard(worker)
            self._server_op_in_progress = False
            self._set_server_buttons_enabled(True)
            self._log_message("Failed to kill ADB server: {}".format(error_msg))

        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(on_error)
        thread_pool.start(worker)

    def _set_server_buttons_enabled(self, enabled: bool) -> None:
        self._start_server_btn.setEnabled(enabled)
        self._kill_server_btn.setEnabled(enabled)
        self._scan_btn.setEnabled(enabled)

    def _on_troubleshoot(self) -> None:
        lines: list[str] = []
        lines.append("=== ADB Troubleshooting ===\n")
        adb_path = self._container.adb_service.adb_path
        if adb_path:
            lines.append("ADB binary: {}".format(adb_path))
            ver = self._container.adb_service.cached_version
            if ver:
                lines.append("Version: {}".format(ver.split(chr(10))[0]))
        else:
            lines.append("ADB binary: NOT FOUND")
            lines.append("Check: ANDROID_HOME, ANDROID_SDK_ROOT, PATH environment variables")
            lines.append("Or configure path in Settings > ADB")

        lines.append("")
        if self._devices:
            lines.append("Connected devices: {}".format(len(self._devices)))
            for d in self._devices:
                lines.append("  {} [{}] model={}".format(d.serial, d.state.value, d.model))
        else:
            lines.append("No devices connected.")
            lines.append("Checklist:")
            lines.append("  1. USB cable connected?")
            lines.append("  2. USB debugging enabled on device? (Developer Options)")
            lines.append("  3. RSA fingerprint accepted on device?")
            lines.append("  4. Try a different USB port or cable")
            lines.append("  5. Try 'Kill Server' then 'Start Server'")

        self._log.setPlainText("\n".join(lines))
        self._log_message("Troubleshooting information displayed")

    def _on_auto_detect_changed(self, state: int) -> None:
        if state == Qt.Checked:
            self._server_intentionally_stopped = False
            self._start_polling()
            self._start_device_scan(manual=False)
        else:
            self._stop_polling()

    def _log_message(self, msg: str) -> None:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        entry = "[{}] {}".format(ts, msg)
        self._log_entries.append(entry)
        if len(self._log_entries) > MAX_LOG_ENTRIES:
            self._log_entries = self._log_entries[-MAX_LOG_ENTRIES:]
        self._log.appendPlainText(entry)
        if self._log_auto_scroll:
            sb = self._log.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _on_clear_log(self) -> None:
        self._log.clear()
        self._log_entries.clear()

    def _get_selected_serial(self) -> Optional[str]:
        return self._device_selector.currentData()

    def _check_authorised_preconditions(self) -> bool:
        if not self._ctx.is_active:
            self._log_message("Cannot acquire evidence: no case is open.")
            return False
        if not self._get_selected_serial():
            self._log_message("Cannot acquire evidence: no device selected.")
            return False
        if not any(d.state == AdbState.CONNECTED for d in self._devices):
            self._log_message(
                "Cannot acquire evidence: no authorised device connected."
            )
            return False
        return True

    def _is_authorised_action_allowed(self) -> bool:
        return (
            self._ctx.is_active
            and any(d.state == AdbState.CONNECTED for d in self._devices)
        )

    def _finish_authorised_action(self, operation: AdbOperationType) -> None:
        self._authorised_ops_in_progress.discard(operation)
        self._update_authorised_actions()

    def _start_adb_authorised_action(
        self,
        operation: AdbOperationType,
        btn: QPushButton,
        action_name: str,
        timeout: int,
    ) -> None:
        if not self._check_authorised_preconditions():
            return
        if operation in self._authorised_ops_in_progress:
            return

        self._authorised_ops_in_progress.add(operation)
        btn.setEnabled(False)
        self._log_message("{} requested...".format(action_name))

        token = CancellationToken()
        worker = AdbOperationWorker(
            operation=operation,
            configured_path=self._configured_path,
            serial=self._get_selected_serial(),
            timeout=timeout,
            token=token,
            case_dir=Path(self._ctx.case_path) if self._ctx.case_path else None,
            db_path=self._ctx.db_path,
            evidence_service=self._container.evidence_service,
            audit_service=self._container.audit_service,
            hash_service=self._container.hash_service,
            file_store=self._container.file_store,
            case_id=self._ctx.case_id,
        )
        self._pending_workers.add(worker)
        self._adb_operation_workers.add(worker)

        def on_progress(msg: str, current: int, total: int) -> None:
            if current % 10 == 0 or current == total:
                self._log_message("{} ({}/{})".format(msg, current, total))

        def on_finished(result: object) -> None:
            self._pending_workers.discard(worker)
            self._adb_operation_workers.discard(worker)
            self._finish_authorised_action(operation)
            self._on_adb_action_result(operation, action_name, result)

        def on_error(error_msg: str) -> None:
            self._pending_workers.discard(worker)
            self._adb_operation_workers.discard(worker)
            self._finish_authorised_action(operation)
            self._log_message("{} failed: {}".format(action_name, error_msg))

        def on_cancelled() -> None:
            self._pending_workers.discard(worker)
            self._adb_operation_workers.discard(worker)
            self._finish_authorised_action(operation)
            self._log_message("{} cancelled.".format(action_name))

        worker.signals.progress.connect(on_progress)
        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(on_error)
        worker.signals.cancelled.connect(on_cancelled)
        thread_pool.start(worker)

    def _on_adb_action_result(
        self,
        operation: AdbOperationType,
        action_name: str,
        result: object,
    ) -> None:
        from wft.application.services.acquisition_results import (
            DeviceMetadataResult, MediaAcquisitionResult,
            WhatsAppDatabaseExtractionResult,
        )

        if isinstance(result, WhatsAppDatabaseExtractionResult):
            self._log_message(
                "WhatsApp database acquisition {}: {} artefact(s), root={}, "
                "{} failed, {} path(s) not present.".format(
                    result.status,
                    len(result.artifacts),
                    result.root_access,
                    len(result.failures),
                    len(result.unavailable_paths),
                )
            )
            for artifact in result.artifacts:
                state = (
                    "acquired - encrypted / decryption pending"
                    if artifact.encrypted
                    else "acquired"
                )
                self._log_message(
                    "  Artifact: {} ({}) [{}]".format(
                        artifact.remote_path, state, artifact.sha256[:16]
                    )
                )
            for warning in result.warnings:
                self._log_message("  Warning: {}".format(warning))
            for failure in result.failures:
                self._log_message("  Failure: {}".format(failure))
            if result.status in ("ACQUIRED", "PARTIAL"):
                self._log_message(
                    "Databases registered as evidence. Review them on the Evidence "
                    "page; encrypted backups remain decryption pending."
                )
        elif isinstance(result, DeviceMetadataResult):
            self._log_message(
                "Device metadata recorded and verified at: {} ({} fields, hash: {}).".format(
                    result.artifact_path,
                    result.fields_recorded,
                    result.hash_value[:16],
                )
            )
        elif isinstance(result, MediaAcquisitionResult):
            self._log_message(
                "Accessible media acquisition completed: {} copied, {} skipped, {} failed ({} bytes).".format(
                    result.copied_count,
                    result.skipped_count,
                    result.failed_count,
                    result.total_bytes,
                )
            )
            for w in result.warnings:
                self._log_message("  Warning: {}".format(w))
        else:
            self._log_message("{} completed.".format(action_name))

    def _on_import_user_export(self) -> None:
        if not self._check_authorised_preconditions():
            return
        if AdbOperationType.IMPORT_USER_EXPORT in self._authorised_ops_in_progress:
            return

        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select WhatsApp Export",
            "",
            "WhatsApp Export (*.txt *.zip);;Text Files (*.txt);;Zip Files (*.zip);;All Files (*.*)",
        )
        if not file_path:
            self._log_message("Import User Export cancelled.")
            return

        source = Path(file_path)
        if not source.is_file():
            self._log_message(
                "Import User Export failed: the selected file does not exist."
            )
            return

        inspection = self._container.parse_service.inspect_path(source)
        if not inspection:
            self._log_message(
                "Import User Export failed: {} is not a supported format.".format(
                    source.name
                )
            )
            return

        self._authorised_ops_in_progress.add(AdbOperationType.IMPORT_USER_EXPORT)
        self._import_export_btn.setEnabled(False)
        self._log_message("Import User Export: selected {}".format(source.name))

        from wft.ui.workers.import_export_worker import ImportUserExportWorker
        worker = ImportUserExportWorker(
            evidence_service=self._container.evidence_service,
            audit_service=self._container.audit_service,
            parse_service=self._container.parse_service,
            hash_service=self._container.hash_service,
            case_id=self._ctx.case_id,
            case_dir=Path(self._ctx.case_path),
            db_path=self._ctx.db_path,
            source_path=source,
        )
        self._pending_workers.add(worker)

        def on_finished(result: object) -> None:
            self._pending_workers.discard(worker)
            self._finish_authorised_action(AdbOperationType.IMPORT_USER_EXPORT)
            if result is None:
                self._log_message("Import User Export cancelled.")
                return
            from wft.application.services.acquisition_results import ImportUserExportResult
            if isinstance(result, ImportUserExportResult):
                self._log_message(
                    "User export imported successfully. {} messages registered. "
                    "Hash: {}.".format(
                        result.imported_items,
                        result.hash_value[:16],
                    )
                )
                if result.warnings:
                    for w in result.warnings:
                        self._log_message("  Warning: {}".format(w))

        def on_error(error_msg: str) -> None:
            self._pending_workers.discard(worker)
            self._finish_authorised_action(AdbOperationType.IMPORT_USER_EXPORT)
            self._log_message("Import User Export failed: {}".format(error_msg))

        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(on_error)
        thread_pool.start(worker)

    def _on_copy_accessible_media(self) -> None:
        self._start_adb_authorised_action(
            operation=AdbOperationType.COPY_ACCESSIBLE_MEDIA,
            btn=self._copy_media_btn,
            action_name="Copy Accessible Media",
            timeout=300,
        )

    def _on_record_device_metadata(self) -> None:
        self._start_adb_authorised_action(
            operation=AdbOperationType.RECORD_DEVICE_METADATA,
            btn=self._record_metadata_btn,
            action_name="Record Device Metadata",
            timeout=60,
        )

    def _on_extract_whatsapp_databases(self) -> None:
        self._start_adb_authorised_action(
            operation=AdbOperationType.EXTRACT_WHATSAPP_DATABASES,
            btn=self._extract_dbs_btn,
            action_name="Extract WhatsApp Databases",
            timeout=300,
        )
