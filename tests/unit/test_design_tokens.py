import re
from dataclasses import FrozenInstanceError
from wft.ui.theme.tokens import DesignTokens


HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
VALID_WEIGHTS = {100, 200, 300, 400, 500, 600, 700, 800, 900}


class TestDesignTokensRequired:
    def test_has_required_color_fields(self) -> None:
        t = DesignTokens()
        color_fields = [
            "app_background", "sidebar_background", "header_background",
            "surface", "surface_elevated", "surface_hover",
            "border", "border_focus",
            "primary", "primary_hover", "primary_pressed", "primary_text",
            "text_primary", "text_secondary", "text_muted",
            "success", "warning", "error", "information",
            "disabled_background", "disabled_text", "selection_background",
        ]
        for f in color_fields:
            assert hasattr(t, f), f"Missing color field: {f}"
            assert HEX_RE.match(getattr(t, f)), f"Invalid color: {f}={getattr(t, f)}"

    def test_has_required_spacing_fields(self) -> None:
        t = DesignTokens()
        for name in ["space_2", "space_4", "space_6", "space_8",
                      "space_10", "space_12", "space_16", "space_20",
                      "space_24", "space_32"]:
            val = getattr(t, name)
            assert isinstance(val, int), f"{name} not int"
            assert val >= 0, f"{name} negative"

    def test_font_family_non_empty(self) -> None:
        assert len(DesignTokens().font_family) > 0

    def test_dimensions_positive(self) -> None:
        t = DesignTokens()
        dims = ["input_height", "button_height", "compact_button_height",
                "navigation_item_height", "table_row_height", "header_height",
                "sidebar_expanded_width", "sidebar_collapsed_width",
                "dialog_minimum_width"]
        for d in dims:
            assert getattr(t, d) > 0, f"{d} not positive"

    def test_font_weights_valid(self) -> None:
        t = DesignTokens()
        for attr in ["font_weight_regular", "font_weight_medium",
                     "font_weight_semibold", "font_weight_bold"]:
            assert getattr(t, attr) in VALID_WEIGHTS, f"{attr} invalid"

    def test_reduced_motion_is_bool(self) -> None:
        assert isinstance(DesignTokens().reduced_motion, bool)

    def test_frozen_cannot_modify(self) -> None:
        t = DesignTokens()
        try:
            t.primary = "#000000"
            assert False, "Should be frozen"
        except FrozenInstanceError:
            pass
