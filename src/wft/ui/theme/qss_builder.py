from wft.ui.theme.tokens import DesignTokens


def _c(tokens: DesignTokens, name: str) -> str:
    return str(getattr(tokens, name))


def build_base_qss(tokens: DesignTokens) -> str:
    bg = _c(tokens, "app_background")
    txt = _c(tokens, "text_primary")
    return f"""
QApplication, QWidget, QMainWindow {{
    background-color: {bg};
    color: {txt};
    font-family: {_c(tokens, "font_family")};
}}
"""


def build_button_qss(tokens: DesignTokens) -> str:
    return f"""
NeonButton[variant="primary"] {{
    background-color: {_c(tokens, "primary")};
    color: {_c(tokens, "primary_text")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "primary")};
    border-radius: {_c(tokens, "radius_medium")}px;
    padding: 0 {_c(tokens, "space_16")}px;
    min-height: {_c(tokens, "button_height")}px;
    font-weight: {_c(tokens, "font_weight_semibold")};
}}
NeonButton[variant="primary"]:hover {{
    background-color: {_c(tokens, "primary_hover")};
}}
NeonButton[variant="primary"]:pressed {{
    background-color: {_c(tokens, "primary_pressed")};
}}
NeonButton[variant="secondary"] {{
    background-color: transparent;
    color: {_c(tokens, "text_primary")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_medium")}px;
    padding: 0 {_c(tokens, "space_16")}px;
    min-height: {_c(tokens, "button_height")}px;
}}
NeonButton[variant="secondary"]:hover {{
    border-color: {_c(tokens, "primary")};
    color: {_c(tokens, "primary")};
}}
NeonButton[variant="danger"] {{
    background-color: transparent;
    color: {_c(tokens, "error")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "error")};
    border-radius: {_c(tokens, "radius_medium")}px;
    padding: 0 {_c(tokens, "space_16")}px;
    min-height: {_c(tokens, "button_height")}px;
}}
NeonButton[variant="danger"]:hover {{
    background-color: {_c(tokens, "error")};
    color: #FFFFFF;
}}
NeonButton[variant="ghost"] {{
    background: transparent;
    color: {_c(tokens, "text_secondary")};
    border: none;
    border-radius: {_c(tokens, "radius_medium")}px;
    padding: 0 {_c(tokens, "space_12")}px;
    min-height: {_c(tokens, "button_height")}px;
}}
NeonButton[variant="ghost"]:hover {{
    color: {_c(tokens, "text_primary")};
}}
NeonButton:disabled {{
    background-color: {_c(tokens, "disabled_background")};
    color: {_c(tokens, "disabled_text")};
    border-color: {_c(tokens, "disabled_background")};
}}
"""


def build_form_qss(tokens: DesignTokens) -> str:
    return f"""
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {{
    background-color: {_c(tokens, "surface")};
    color: {_c(tokens, "text_primary")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_small")}px;
    padding: {_c(tokens, "space_4")}px {_c(tokens, "space_8")}px;
    min-height: {_c(tokens, "input_height")}px;
    font-size: {_c(tokens, "font_size_body")}px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {{
    border-color: {_c(tokens, "border_focus")};
}}
QComboBox {{
    background-color: {_c(tokens, "surface")};
    color: {_c(tokens, "text_primary")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_small")}px;
    padding: {_c(tokens, "space_4")}px {_c(tokens, "space_8")}px;
    min-height: {_c(tokens, "input_height")}px;
}}
QComboBox:focus {{
    border-color: {_c(tokens, "border_focus")};
}}
QCheckBox, QRadioButton {{
    color: {_c(tokens, "text_primary")};
    spacing: {_c(tokens, "space_6")}px;
}}
QCheckBox:disabled, QRadioButton:disabled {{
    color: {_c(tokens, "disabled_text")};
}}
"""


def build_table_qss(tokens: DesignTokens) -> str:
    return f"""
QTableView, QTableWidget {{
    background-color: {_c(tokens, "surface")};
    color: {_c(tokens, "text_primary")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    gridline-color: {_c(tokens, "border")};
    selection-background-color: {_c(tokens, "selection_background")};
}}
QHeaderView::section {{
    background-color: {_c(tokens, "surface_elevated")};
    color: {_c(tokens, "text_secondary")};
    border: none;
    border-bottom: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    padding: {_c(tokens, "space_4")}px {_c(tokens, "space_8")}px;
    font-weight: {_c(tokens, "font_weight_semibold")};
    min-height: {_c(tokens, "table_row_height")}px;
}}
QTableView::item, QTableWidget::item {{
    min-height: {_c(tokens, "table_row_height")}px;
    padding: {_c(tokens, "space_2")}px {_c(tokens, "space_8")}px;
}}
QTableView::item:selected, QTableWidget::item:selected {{
    background-color: {_c(tokens, "selection_background")};
    color: {_c(tokens, "text_primary")};
}}
"""


def build_navigation_qss(tokens: DesignTokens) -> str:
    return f"""
NavigationSidebar {{
    background-color: {_c(tokens, "sidebar_background")};
    border-right: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
}}
NavigationItem {{
    background: transparent;
    color: {_c(tokens, "text_secondary")};
    border: none;
    border-radius: {_c(tokens, "radius_small")}px;
    min-height: {_c(tokens, "navigation_item_height")}px;
    padding: 0 {_c(tokens, "space_12")}px;
    font-size: {_c(tokens, "font_size_label")}px;
}}
NavigationItem:hover {{
    background-color: {_c(tokens, "surface_hover")};
    color: {_c(tokens, "text_primary")};
}}
NavigationItem[active="true"] {{
    background-color: {_c(tokens, "selection_background")};
    color: {_c(tokens, "primary")};
    border-left: 3px solid {_c(tokens, "primary")};
}}
AppHeader {{
    background-color: {_c(tokens, "header_background")};
    border-bottom: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    min-height: {_c(tokens, "header_height")}px;
}}
"""


def build_dialog_qss(tokens: DesignTokens) -> str:
    return f"""
QDialog {{
    background-color: {_c(tokens, "surface")};
    color: {_c(tokens, "text_primary")};
    min-width: {_c(tokens, "dialog_minimum_width")}px;
}}
QMessageBox {{
    background-color: {_c(tokens, "surface")};
    color: {_c(tokens, "text_primary")};
}}
QDialogButtonBox QPushButton {{
    min-height: {_c(tokens, "button_height")}px;
    padding: 0 {_c(tokens, "space_12")}px;
}}
"""


def build_scrollbar_qss(tokens: DesignTokens) -> str:
    return f"""
QScrollBar:vertical {{
    background: {_c(tokens, "surface")};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_small")}px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {_c(tokens, "text_muted")};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {_c(tokens, "surface")};
    height: 10px;
}}
QScrollBar::handle:horizontal {{
    background: {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_small")}px;
    min-width: 30px;
}}
"""


def build_feedback_qss(tokens: DesignTokens) -> str:
    return f"""
QToolTip {{
    background-color: {_c(tokens, "surface_elevated")};
    color: {_c(tokens, "text_primary")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_small")}px;
    padding: {_c(tokens, "space_4")}px {_c(tokens, "space_8")}px;
    font-size: {_c(tokens, "font_size_caption")}px;
}}
QMenu {{
    background-color: {_c(tokens, "surface_elevated")};
    color: {_c(tokens, "text_primary")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_small")}px;
    padding: {_c(tokens, "space_4")}px;
}}
QMenu::item {{
    padding: {_c(tokens, "space_6")}px {_c(tokens, "space_16")}px;
    border-radius: {_c(tokens, "radius_small")}px;
}}
QMenu::item:selected {{
    background-color: {_c(tokens, "selection_background")};
    color: {_c(tokens, "primary")};
}}
QProgressBar {{
    background-color: {_c(tokens, "surface")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_small")}px;
    text-align: center;
    color: {_c(tokens, "text_primary")};
    min-height: 20px;
}}
QProgressBar::chunk {{
    background-color: {_c(tokens, "primary")};
    border-radius: {_c(tokens, "radius_small")}px;
}}
"""


def build_container_qss(tokens: DesignTokens) -> str:
    return f"""
QSplitter::handle {{
    background-color: {_c(tokens, "border")};
    width: 1px;
    height: 1px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QGroupBox {{
    background-color: {_c(tokens, "surface")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_medium")}px;
    margin-top: {_c(tokens, "space_12")}px;
    padding: {_c(tokens, "space_16")}px {_c(tokens, "space_12")}px {_c(tokens, "space_12")}px;
    font-weight: {_c(tokens, "font_weight_semibold")};
    color: {_c(tokens, "text_secondary")};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 {_c(tokens, "space_8")}px;
    color: {_c(tokens, "text_secondary")};
}}
"""


def build_misc_qss(tokens: DesignTokens) -> str:
    return f"""
QStatusBar {{
    background-color: {_c(tokens, "header_background")};
    color: {_c(tokens, "text_muted")};
    border-top: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    font-size: {_c(tokens, "font_size_caption")}px;
    min-height: 26px;
}}
QStatusBar::item {{
    border: none;
}}
QLabel {{
    color: {_c(tokens, "text_primary")};
}}
StatusBadge[status="success"] {{
    color: {_c(tokens, "success")};
}}
StatusBadge[status="warning"] {{
    color: {_c(tokens, "warning")};
}}
StatusBadge[status="error"] {{
    color: {_c(tokens, "error")};
}}
StatusBadge[status="information"] {{
    color: {_c(tokens, "information")};
}}
StatusBadge[status="neutral"] {{
    color: {_c(tokens, "text_muted")};
}}
StatusBanner {{
    border-radius: {_c(tokens, "radius_medium")}px;
    padding: {_c(tokens, "space_10")}px {_c(tokens, "space_16")}px;
}}
StatusBanner[banner_type="verified"] {{
    border-left: 4px solid {_c(tokens, "success")};
    background-color: {_c(tokens, "surface")};
}}
StatusBanner[banner_type="warning"] {{
    border-left: 4px solid {_c(tokens, "warning")};
    background-color: {_c(tokens, "surface")};
}}
StatusBanner[banner_type="hash_mismatch"] {{
    border-left: 4px solid {_c(tokens, "error")};
    background-color: {_c(tokens, "surface")};
}}
StatusBanner[banner_type="unsupported"] {{
    border-left: 4px solid {_c(tokens, "text_muted")};
    background-color: {_c(tokens, "surface")};
}}
StatusBanner[banner_type="info"] {{
    border-left: 4px solid {_c(tokens, "information")};
    background-color: {_c(tokens, "surface")};
}}
ContentCard {{
    background-color: {_c(tokens, "surface")};
    border: {_c(tokens, "border_width")}px solid {_c(tokens, "border")};
    border-radius: {_c(tokens, "radius_medium")}px;
}}
"""


def build_full_qss(tokens: DesignTokens) -> str:
    sections = [
        build_base_qss,
        build_button_qss,
        build_form_qss,
        build_table_qss,
        build_navigation_qss,
        build_dialog_qss,
        build_scrollbar_qss,
        build_feedback_qss,
        build_container_qss,
        build_misc_qss,
    ]
    return "\n".join(fn(tokens) for fn in sections)
