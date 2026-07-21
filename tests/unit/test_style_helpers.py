from unittest.mock import patch
from PySide6.QtWidgets import QPushButton
from wft.ui.theme.style_helpers import (
    refresh_style,
    set_dynamic_property,
)


class TestRefreshStyle:
    def test_calls_unpolish_and_polish(self):
        btn = QPushButton()
        with patch.object(btn.style(), "unpolish") as mock_unpolish:
            with patch.object(btn.style(), "polish") as mock_polish:
                refresh_style(btn)
                mock_unpolish.assert_called_once_with(btn)
                mock_polish.assert_called_once_with(btn)


class TestSetDynamicProperty:
    def test_sets_property_and_returns_value(self):
        btn = QPushButton()
        result = set_dynamic_property(
            btn, "variant", "primary",
            allowed_values={"primary", "secondary"},
            default_value="secondary",
        )
        assert result == "primary"
        assert btn.property("variant") == "primary"

    def test_normalizes_invalid_value(self):
        btn = QPushButton()
        result = set_dynamic_property(
            btn, "variant", "invalid_value",
            allowed_values={"primary", "secondary"},
            default_value="secondary",
        )
        assert result == "secondary"
        assert btn.property("variant") == "secondary"

    def test_does_not_repolish_unchanged_property(self):
        btn = QPushButton()
        btn.setProperty("variant", "primary")
        with patch.object(btn.style(), "unpolish") as mock_unpolish:
            result = set_dynamic_property(
                btn, "variant", "primary",
                allowed_values={"primary", "secondary"},
                default_value="secondary",
            )
            assert result == "primary"
            mock_unpolish.assert_not_called()
