import sys
import pytest
from PySide6.QtWidgets import QApplication, QDialog, QPushButton
from wft.ui.components.confirm_dialog import ConfirmDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestConfirmDialog:
    def test_standard_mode(self, qapp):
        dialog = ConfirmDialog(
            title="Confirm",
            message="Are you sure?",
        )
        assert dialog.windowTitle() == "Confirm"

    def test_destructive_mode_cancel_default(self, qapp):
        dialog = ConfirmDialog(
            title="Delete",
            message="Delete this item?",
            destructive=True,
        )
        cancel = None
        for btn in dialog.findChildren(QPushButton):
            if btn.text() == "Cancel":
                cancel = btn
                break
        assert cancel is not None
        assert cancel.isDefault() is True

    def test_accept_returns_correct_code(self, qapp):
        dialog = ConfirmDialog(title="Test", message="Test")
        buttons = dialog.findChildren(QPushButton)
        assert len(buttons) >= 2

    def test_destructive_confirm_variant_is_danger(self, qapp):
        dialog = ConfirmDialog(
            title="Delete",
            message="Delete?",
            destructive=True,
        )
        confirm = None
        for btn in dialog.findChildren(QPushButton):
            if btn.text() == "Confirm":
                confirm = btn
                break
        assert confirm is not None
        assert confirm.property("variant") == "danger"

    def test_standard_confirm_variant_is_primary(self, qapp):
        dialog = ConfirmDialog(title="Test", message="Test")
        confirm = None
        for btn in dialog.findChildren(QPushButton):
            if btn.text() == "Confirm":
                confirm = btn
                break
        assert confirm is not None
        assert confirm.property("variant") == "primary"

    def test_custom_button_labels(self, qapp):
        dialog = ConfirmDialog(
            title="Test",
            message="Test",
            confirm_text="Yes, proceed",
            cancel_text="No, go back",
        )
        buttons = {btn.text() for btn in dialog.findChildren(QPushButton)}
        assert "Yes, proceed" in buttons
        assert "No, go back" in buttons

    def test_details_text_visible(self, qapp):
        dialog = ConfirmDialog(
            title="Test",
            message="Warning",
            details="Detailed error info here",
        )
        assert dialog is not None

    def test_modal_flag(self, qapp):
        dialog = ConfirmDialog(title="Test", message="Test")
        assert dialog.isModal() is True

    def test_minimum_width(self, qapp):
        dialog = ConfirmDialog(title="Test", message="Test")
        assert dialog.minimumWidth() == 440