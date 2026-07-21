from dataclasses import dataclass


@dataclass(frozen=True)
class DesignTokens:
    # Colors
    app_background: str = "#020703"
    sidebar_background: str = "#051208"
    header_background: str = "#040D06"
    surface: str = "#0A1A0E"
    surface_elevated: str = "#0F2415"
    surface_hover: str = "#142E1B"
    border: str = "#1A3D22"
    border_focus: str = "#00F56A"
    primary: str = "#00C853"
    primary_hover: str = "#00E676"
    primary_pressed: str = "#00A845"
    primary_text: str = "#020703"
    text_primary: str = "#EAF7EE"
    text_secondary: str = "#9BBAA3"
    text_muted: str = "#6E9278"
    success: str = "#00E676"
    warning: str = "#FFD600"
    error: str = "#FF1744"
    information: str = "#00B8D4"
    disabled_background: str = "#1A2E1F"
    disabled_text: str = "#7FA98A"
    selection_background: str = "#1A3D22"

    # Spacing
    space_2: int = 2
    space_4: int = 4
    space_6: int = 6
    space_8: int = 8
    space_10: int = 10
    space_12: int = 12
    space_16: int = 16
    space_20: int = 20
    space_24: int = 24
    space_32: int = 32

    # Typography
    font_family: str = "Segoe UI, Noto Sans, sans-serif"
    font_size_caption: int = 11
    font_size_body: int = 13
    font_size_label: int = 12
    font_size_section: int = 15
    font_size_page_title: int = 20
    font_size_app_title: int = 22
    font_weight_regular: int = 400
    font_weight_medium: int = 500
    font_weight_semibold: int = 600
    font_weight_bold: int = 700

    # Dimensions
    input_height: int = 40
    button_height: int = 42
    compact_button_height: int = 34
    navigation_item_height: int = 44
    table_row_height: int = 44
    header_height: int = 48
    sidebar_expanded_width: int = 240
    sidebar_collapsed_width: int = 56
    dialog_minimum_width: int = 440

    # Radii
    radius_small: int = 4
    radius_medium: int = 6
    radius_large: int = 8
    radius_pill: int = 9999

    # Animation
    reduced_motion: bool = False
    animation_duration_fast_ms: int = 100
    animation_duration_normal_ms: int = 200

    # Other
    border_width: int = 1
    focus_border_width: int = 2
    icon_small: int = 14
    icon_medium: int = 18
    icon_large: int = 22
