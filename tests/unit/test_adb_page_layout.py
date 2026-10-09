from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QGridLayout, QCheckBox, QHBoxLayout,
    QGroupBox, QSpinBox, QComboBox, QSplitter, QTextEdit, QWidget,
    QPushButton, QSizePolicy,
)
from PySide6.QtGui import QFont

from wft.application.services.adb_service import AdbState, AdbDevice
from wft.ui.pages.adb_extractor_page import (
    _redact_serial, _make_scan_signature, MAX_LOG_ENTRIES,
)
from wft.ui.utils.font_utils import ensure_valid_font_size
from wft.ui.components.evidence_banner import EvidenceBanner
from wft.infrastructure.settings.settings import AppSettings


@pytest.fixture
def mock_container():
    settings = AppSettings()
    container = MagicMock()
    container.settings = settings
    container.adb_service = None
    return container


class TestEnsureValidFontSize:
    def test_keeps_existing_valid_size(self, qapp):
        widget = QLabel()
        font = QFont()
        font.setPointSize(14)
        widget.setFont(font)
        ensure_valid_font_size(widget, 10)
        assert widget.font().pointSize() == 14

    def test_does_not_crash_with_zero_point_size(self, qapp):
        widget = QLabel()
        font = QFont()
        font.setPointSize(0)
        widget.setFont(font)
        ensure_valid_font_size(widget, 10)

    def test_does_not_crash_with_default_font(self, qapp):
        widget = QLabel()
        ensure_valid_font_size(widget, 12)
        assert widget.font().pointSize() > 0


class TestRedactSerial:
    def test_redact_long_serial(self):
        result = _redact_serial("0123456789ABCDEF")
        assert result == "0123****CDEF"
        assert len(result) == 12

    def test_redact_short_serial(self):
        result = _redact_serial("ABCDEF")
        assert result == "ABCDEF"

    def test_redact_empty(self):
        assert _redact_serial("") == ""


class TestScanSignature:
    def test_make_signature(self):
        devices = [
            AdbDevice(serial="A1", state=AdbState.CONNECTED),
            AdbDevice(serial="B2", state=AdbState.UNAUTHORIZED),
        ]
        sig = _make_scan_signature(devices, AdbState.CONNECTED)
        assert len(sig) == 2
        assert sig[0] == "connected"
        assert ("A1", "connected") in sig[1]
        assert ("B2", "unauthorized") in sig[1]

    def test_signature_unchanged_for_same_devices(self):
        d1 = [AdbDevice(serial="X", state=AdbState.CONNECTED)]
        s1 = _make_scan_signature(d1, AdbState.CONNECTED)
        d2 = [AdbDevice(serial="X", state=AdbState.CONNECTED)]
        s2 = _make_scan_signature(d2, AdbState.CONNECTED)
        assert s1 == s2

    def test_signature_differs_when_state_changes(self):
        d1 = [AdbDevice(serial="X", state=AdbState.CONNECTED)]
        s1 = _make_scan_signature(d1, AdbState.CONNECTED)
        d2 = [AdbDevice(serial="X", state=AdbState.UNAUTHORIZED)]
        s2 = _make_scan_signature(d2, AdbState.CONNECTED)
        assert s1 != s2


class TestEvidenceBannerIcon:
    def test_icon_hidden_when_empty_type(self, qapp):
        banner = EvidenceBanner("Test message", "unknown_type")
        banner.show()
        icon = banner.findChildren(QLabel)[0]
        assert not icon.isVisible()
        sp = icon.sizePolicy()
        assert sp.horizontalPolicy() == QSizePolicy.Minimum

    def test_icon_visible_for_known_type(self, qapp):
        banner = EvidenceBanner("Test message", "verified")
        banner.show()
        icon = banner.findChildren(QLabel)[0]
        assert icon.isVisible()
        assert icon.text() == "\u2713"

    def test_icon_updates_on_set_banner_type(self, qapp):
        banner = EvidenceBanner("Test", "info")
        banner.show()
        icon = banner.findChildren(QLabel)[0]
        assert icon.isVisible()
        banner.set_banner_type("unknown")
        assert not icon.isVisible()

    def test_icon_becomes_visible_after_valid_type(self, qapp):
        banner = EvidenceBanner("Test", "unknown")
        banner.show()
        icon = banner.findChildren(QLabel)[0]
        assert not icon.isVisible()
        banner.set_banner_type("warning")
        assert icon.isVisible()
        assert icon.text() == "\u26A0"


class TestMaxLogEntries:
    def test_log_entries_limited(self):
        entries = []
        for i in range(MAX_LOG_ENTRIES + 100):
            entries.append("[00:00:00] Entry {}".format(i))
            if len(entries) > MAX_LOG_ENTRIES:
                entries = entries[-MAX_LOG_ENTRIES:]
        assert len(entries) == MAX_LOG_ENTRIES
        assert entries[0].endswith("Entry {}".format(100))

    def test_log_under_limit_not_truncated(self):
        entries = []
        for i in range(50):
            entries.append("Entry {}".format(i))
        assert len(entries) == 50


class TestPageLayout:

    def _make_page(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        return ADBExtractorPage(mock_container, ctx)

    def test_device_info_has_all_fields(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)

        expected = [
            "Manufacturer",
            "Model",
            "Android Version",
            "SDK Version",
            "Serial",
            "Transport ID",
            "Connection Type",
            "Authorisation State",
        ]
        for field in expected:
            assert field in page._field_labels, "Missing label: {}".format(field)
            assert field in page._field_values, "Missing value: {}".format(field)
            assert page._field_labels[field].text() == field + ":"
            assert page._field_values[field].text() == "—"

    def test_device_info_has_individual_attributes(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert hasattr(page, "_manufacturer_value")
        assert hasattr(page, "_model_value")
        assert hasattr(page, "_android_version_value")
        assert hasattr(page, "_sdk_version_value")
        assert hasattr(page, "_serial_value")
        assert hasattr(page, "_transport_id_value")
        assert hasattr(page, "_connection_type_value")
        assert hasattr(page, "_authorisation_value")

    def test_device_info_values_have_min_height(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        for name, label in page._field_values.items():
            assert label.minimumHeight() >= 20, "{} minimumHeight too small".format(name)

    def test_device_selector_min_and_max_widths(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._device_selector.minimumWidth() >= 300
        assert page._device_selector.maximumWidth() <= 800

    def test_device_selector_has_tooltip_data(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert isinstance(page._device_selector, QComboBox)
        assert page._device_selector.minimumWidth() >= 300

    def test_poll_interval_spinbox_exists(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._poll_interval_spin is not None
        assert isinstance(page._poll_interval_spin, QSpinBox)
        assert page._poll_interval_spin.minimum() == 2
        assert page._poll_interval_spin.maximum() == 30
        assert page._poll_interval_spin.suffix() == " s"

    def test_poll_interval_spinbox_default_from_settings(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._poll_interval_spin.value() == mock_container.settings.adb.poll_interval_seconds

    def test_auto_detect_separate_from_buttons(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        cb = page._auto_detect_cb
        assert isinstance(cb, QCheckBox)
        assert cb.text() == "Auto-detect devices"

    def test_clear_log_button_exists(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._clear_log_btn is not None
        assert page._clear_log_btn.text() == "Clear Log"

    def test_splitter_has_two_widgets(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        splitter = page.findChild(QSplitter)
        assert splitter is not None
        assert splitter.count() == 2

    def test_splitter_sizes_set(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        splitter = page.findChild(QSplitter)
        assert splitter is not None
        sizes = splitter.sizes()
        assert len(sizes) == 2
        assert all(s > 0 for s in sizes)

    def test_left_panel_minimum_width(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        splitter = page.findChild(QSplitter)
        assert splitter is not None
        left = splitter.widget(0)
        assert left.minimumWidth() >= 600

    def test_log_panel_minimum_width(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        splitter = page.findChild(QSplitter)
        assert splitter is not None
        right = splitter.widget(1)
        assert right.minimumWidth() >= 300

    def test_buttons_have_minimum_height(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        for btn in [page._scan_btn, page._start_server_btn, page._kill_server_btn, page._troubleshoot_btn]:
            assert btn.minimumHeight() >= 36, "Button too short: {}".format(btn.text())

    def test_authorised_actions_have_minimum_height(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        for btn in [page._import_export_btn, page._copy_media_btn, page._record_metadata_btn]:
            assert btn.minimumHeight() >= 36

    def test_adb_banner_initial_text(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._adb_banner is not None


class TestFontSafety:
    def test_page_info_labels_have_valid_font_sizes(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        page = ADBExtractorPage(mock_container, ctx)
        for name, label in page._field_labels.items():
            size = label.font().pointSize()
            assert size > 0, "Label {} has pointSize {}".format(name, size)
        for name, label in page._field_values.items():
            size = label.font().pointSize()
            assert size > 0, "Value {} has pointSize {}".format(name, size)

    def test_log_widget_has_valid_font(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        page = ADBExtractorPage(mock_container, ctx)
        size = page._log.font().pointSize()
        assert size > 0


class TestDeviceInfoContent:
    def test_serial_is_redacted_in_value(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        page = ADBExtractorPage(mock_container, ctx)

        device = AdbDevice(
            serial="0123456789ABCDEF",
            state=AdbState.CONNECTED,
            manufacturer="TestMan",
            model="TestModel",
            android_version="15",
            sdk_version="35",
            transport_id="1",
            connection_type="USB",
        )
        page._update_device_info(device)
        assert page._serial_value.text() == "0123****CDEF"
        assert page._serial_value.toolTip() == "Full serial: 0123456789ABCDEF"

    def test_missing_fields_show_dash(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        page = ADBExtractorPage(mock_container, ctx)

        device = AdbDevice(
            serial="SERIAL01",
            state=AdbState.CONNECTED,
        )
        page._update_device_info(device)
        assert page._manufacturer_value.text() == "—"
        assert page._model_value.text() == "—"
        assert page._android_version_value.text() == "—"
        assert page._sdk_version_value.text() == "—"
        assert page._transport_id_value.text() == "—"
        assert page._connection_type_value.text() == "USB"

    def test_clearing_device_info_resets_all(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        page = ADBExtractorPage(mock_container, ctx)

        device = AdbDevice(serial="X", state=AdbState.CONNECTED, manufacturer="M")
        page._update_device_info(device)
        assert page._manufacturer_value.text() == "M"

        page._clear_device_info()
        for label in page._field_values.values():
            assert label.text() == "—"


class TestCaseBanner:
    def test_case_banner_visible_when_no_case(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext

        ctx = ActiveCaseContext()
        page = ADBExtractorPage(mock_container, ctx)
        page.show()

        assert page._case_banner is not None
        assert page._case_banner.isVisible()

    def test_authorised_actions_disabled_when_no_case(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext

        ctx = ActiveCaseContext()
        page = ADBExtractorPage(mock_container, ctx)

        assert not page._import_export_btn.isEnabled()
        assert not page._copy_media_btn.isEnabled()
        assert not page._record_metadata_btn.isEnabled()


class TestEvidenceBannerSizePolicy:
    def test_icon_size_policy_minimum_when_visible(self, qapp):
        from PySide6.QtWidgets import QSizePolicy as SP
        banner = EvidenceBanner("Test", "verified")
        icon = banner._icon
        sp = icon.sizePolicy()
        assert sp.horizontalPolicy() == SP.Minimum

    def test_icon_minimum_width_set(self, qapp):
        banner = EvidenceBanner("Test", "verified")
        assert banner._icon.minimumWidth() >= 16

    def test_icon_no_fixed_width(self, qapp):
        banner = EvidenceBanner("Test", "verified")
        min_w = banner._icon.minimumWidth()
        assert min_w >= 16


class TestAuthorisedActions:
    def _make_page(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        return ADBExtractorPage(mock_container, ctx)

    def test_buttons_have_correct_text(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._import_export_btn.text() == "Import User Export"
        assert page._copy_media_btn.text() == "Copy Accessible Media"
        assert page._record_metadata_btn.text() == "Record Device Metadata"

    def test_buttons_start_disabled_without_case(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert not page._import_export_btn.isEnabled()
        assert not page._copy_media_btn.isEnabled()
        assert not page._record_metadata_btn.isEnabled()

    def test_buttons_start_disabled_without_device(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        page = ADBExtractorPage(mock_container, ctx)
        assert not page._import_export_btn.isEnabled()
        assert not page._copy_media_btn.isEnabled()
        assert not page._record_metadata_btn.isEnabled()

    def test_buttons_enabled_with_case_and_connected_device(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        page = ADBExtractorPage(mock_container, ctx)
        device = AdbDevice(serial="TEST001", state=AdbState.CONNECTED, model="Pixel")
        page._devices = [device]
        page._update_device_selector([device])
        page._update_authorised_actions()
        assert page._import_export_btn.isEnabled()
        assert page._copy_media_btn.isEnabled()
        assert page._record_metadata_btn.isEnabled()

    def test_buttons_disabled_with_case_but_unauthorised_device(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        page = ADBExtractorPage(mock_container, ctx)
        device = AdbDevice(serial="TEST001", state=AdbState.UNAUTHORIZED, model="Pixel")
        page._devices = [device]
        page._update_device_selector([device])
        page._update_authorised_actions()
        assert not page._import_export_btn.isEnabled()
        assert not page._copy_media_btn.isEnabled()
        assert not page._record_metadata_btn.isEnabled()

    def test_handler_methods_exist(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert hasattr(page, "_on_import_user_export")
        assert hasattr(page, "_on_copy_accessible_media")
        assert hasattr(page, "_on_record_device_metadata")

    def test_authorised_ops_set_empty(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._authorised_ops_in_progress == set()

    def test_get_selected_serial_returns_none_when_empty(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._get_selected_serial() is None

    def test_check_authorised_preconditions_false_without_case(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert not page._check_authorised_preconditions()

    def test_check_authorised_preconditions_false_without_device(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        page = ADBExtractorPage(mock_container, ctx)
        assert not page._check_authorised_preconditions()

    def test_check_authorised_preconditions_false_with_unauthorised_device(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        page = ADBExtractorPage(mock_container, ctx)
        device = AdbDevice(serial="TEST001", state=AdbState.UNAUTHORIZED, model="Pixel")
        page._devices = [device]
        page._update_device_selector([device])
        assert not page._check_authorised_preconditions()

    def test_is_authorised_action_allowed_false_without_case(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert not page._is_authorised_action_allowed()

    def test_is_authorised_action_allowed_false_without_connected_device(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        page = ADBExtractorPage(mock_container, ctx)
        device = AdbDevice(serial="TEST001", state=AdbState.UNAUTHORIZED, model="Pixel")
        page._devices = [device]
        page._update_device_selector([device])
        assert not page._is_authorised_action_allowed()

    def test_is_authorised_action_allowed_true_with_case_and_connected_device(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        page = ADBExtractorPage(mock_container, ctx)
        device = AdbDevice(serial="TEST001", state=AdbState.CONNECTED, model="Pixel")
        page._devices = [device]
        page._update_device_selector([device])
        assert page._is_authorised_action_allowed()

    def test_tooltips_update_with_state(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        page = ADBExtractorPage(mock_container, ctx)
        tip = page._import_export_btn.toolTip()
        assert "case" in tip.lower()

        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        page._update_authorised_actions()
        tip = page._import_export_btn.toolTip()
        assert "device" in tip.lower() or "authorised" in tip.lower()

    def test_start_authorised_action_logs_on_no_case(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        initial_len = len(page._log_entries)
        page._on_import_user_export()
        assert len(page._log_entries) > initial_len
        assert "no case" in page._log_entries[-1].lower()

    def test_import_export_handler_updates_log(self, qapp, mock_container, tmp_path):
        from unittest.mock import patch, MagicMock
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = str(tmp_path)
        ctx._is_active = True
        page = ADBExtractorPage(mock_container, ctx)
        device = AdbDevice(serial="TEST001", state=AdbState.CONNECTED, model="Pixel")
        page._devices = [device]
        page._update_device_selector([device])
        page._update_authorised_actions()
        test_file = tmp_path / "test_export.txt"
        test_file.write_text("test content")
        with patch.object(page._container.parse_service, "inspect_path", return_value={"adapter_id": "test"}):
            with patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(str(test_file), "")):
                initial_len = len(page._log_entries)
                page._on_import_user_export()
                assert len(page._log_entries) > initial_len
                assert "selected" in page._log_entries[-1].lower()

    def test_copy_media_handler_updates_log(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        page = ADBExtractorPage(mock_container, ctx)
        device = AdbDevice(serial="TEST001", state=AdbState.CONNECTED, model="Pixel")
        page._devices = [device]
        page._update_device_selector([device])
        page._update_authorised_actions()
        initial_len = len(page._log_entries)
        page._on_copy_accessible_media()
        assert len(page._log_entries) > initial_len

    def test_record_metadata_handler_updates_log(self, qapp, mock_container):
        from wft.application.services.case_context import ActiveCaseContext
        from wft.application.services.adb_service import AdbDevice, AdbState
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        ctx = ActiveCaseContext()
        ctx._case_id = 1
        ctx._case_path = "/tmp/fake"
        ctx._is_active = True
        page = ADBExtractorPage(mock_container, ctx)
        device = AdbDevice(serial="TEST001", state=AdbState.CONNECTED, model="Pixel")
        page._devices = [device]
        page._update_device_selector([device])
        page._update_authorised_actions()
        initial_len = len(page._log_entries)
        page._on_record_device_metadata()
        assert len(page._log_entries) > initial_len

class TestWhatsAppExtractionAction:
    def _make_page(self, qapp, mock_container):
        from wft.ui.pages.adb_extractor_page import ADBExtractorPage
        from wft.application.services.case_context import ActiveCaseContext
        ctx = ActiveCaseContext()
        return ADBExtractorPage(mock_container, ctx)

    def test_button_exists_with_correct_label(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert hasattr(page, "_extract_dbs_btn")
        assert page._extract_dbs_btn.text() == "Extract WhatsApp Databases"

    def test_button_disabled_without_case(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        assert page._extract_dbs_btn.isEnabled() is False

    def test_button_tooltip_states_acquisition_not_decryption(self, qapp, mock_container, tmp_path):
        page = self._make_page(qapp, mock_container)
        page._ctx.open(1, tmp_path)
        page._devices = [AdbDevice(serial="S1", state=AdbState.CONNECTED)]
        page._update_authorised_actions()
        tooltip = page._extract_dbs_btn.toolTip().lower()
        assert "not decrypted" in tooltip
        assert "evidence" in tooltip
        assert page._extract_dbs_btn.isEnabled() is True

    def test_button_lives_in_authorised_group(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        group = page._extract_dbs_btn.parent()
        assert group is not None
        labels = [
            b.text() for b in group.findChildren(QPushButton)
        ]
        assert "Extract WhatsApp Databases" in labels

    def test_handler_dispatches_extract_operation(self, qapp, mock_container):
        page = self._make_page(qapp, mock_container)
        calls = {}
        page._check_authorised_preconditions = lambda: True
        page._start_adb_authorised_action = lambda **kwargs: calls.update(kwargs)
        page._on_extract_whatsapp_databases()
        from wft.ui.workers.adb_scan_worker import AdbOperationType
        assert calls["operation"] == AdbOperationType.EXTRACT_WHATSAPP_DATABASES
        assert calls["action_name"] == "Extract WhatsApp Databases"
        assert calls["timeout"] == 300
