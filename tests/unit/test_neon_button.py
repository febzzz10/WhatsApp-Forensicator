import sys
import pytest
from PySide6.QtWidgets import QApplication, QPushButton
from wft.ui.components.neon_button import NeonButton


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestNeonButtonNewAPI:
    def test_constructs_with_variant(self, qapp):
        btn = NeonButton("Test", "primary")
        assert isinstance(btn, QPushButton)
        assert btn.text() == "Test"

    def test_variant_dynamic_property_set(self, qapp):
        btn = NeonButton("Test", "danger")
        assert btn.property("variant") == "danger"

    def test_set_variant_updates_property(self, qapp):
        btn = NeonButton()
        btn.set_variant("secondary")
        assert btn.property("variant") == "secondary"

    def test_invalid_variant_falls_back(self, qapp):
        btn = NeonButton("Test", "invalid")
        assert btn.property("variant") == "secondary"


class TestNeonButtonDeprecatedStyle:
    def test_style_primary_translates(self, qapp):
        btn = NeonButton("Test", style="primary")
        assert btn.property("variant") == "primary"

    def test_style_destructive_translates_to_danger(self, qapp):
        btn = NeonButton("Test", style="destructive")
        assert btn.property("variant") == "danger"

    def test_set_style_deprecated_translates(self, qapp):
        btn = NeonButton()
        btn.set_style("destructive")
        assert btn.property("variant") == "danger"

    def test_set_style_warning_translates(self, qapp):
        btn = NeonButton()
        btn.set_style("warning")
        assert btn.property("variant") == "secondary"
