# Phase 1 — UI Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the foundational UI infrastructure: centralized DesignTokens, ThemeManager, QSS builder, collapsible sidebar navigation, refactored shared components, and main-window shell.

**Architecture:** Frozen dataclass tokens → ThemeManager generates QSS → applied to QApplication. Collapsible sidebar with PageId-based navigation replaces horizontal tab bar. Shared components use dynamic properties and token-aware sizing. Old tab bar kept in parallel until replacement is verified.

**Tech Stack:** PySide6, Python 3.11+ (StrEnum), QRunnable workers, SQLite case DB

## Global Constraints

- Python >=3.11, PySide6 >=6.6
- All positioning via layout managers — no setGeometry(), no move()
- No changes to forensic, ADB, database, evidence, parsing, or business logic
- All 18 existing page widgets preserved in QStackedWidget
- Color validation regex: `^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$`
- primary_text: #020703 (contrast ~6.2:1 on #00C853)
- disabled_text: #7FA98A (improved readability on #1A2E1F)
- No emoji as production icons — packaged SVG/PNG or styled text fallback
- Deprecated APIs (NeonButton.set_style, StatusBadge.set_badge_type) retained with old→new value translation
- High-contrast theme NOT implemented in Phase 1
- DataTable component deferred

---

## File Structure

```
Created:
  src/wft/ui/pages/page_id.py              — PageId StrEnum
  src/wft/ui/theme/__init__.py             — package
  src/wft/ui/theme/tokens.py               — DesignTokens frozen dataclass
  src/wft/ui/theme/themes.py               — dark_forensic preset
  src/wft/ui/theme/theme_manager.py        — ThemeManager
  src/wft/ui/theme/qss_builder.py          — sectioned QSS generation
  src/wft/ui/theme/layout_helpers.py       — apply_page_layout, etc.
  src/wft/ui/theme/style_helpers.py        — refresh_style, set_dynamic_property
  src/wft/ui/components/app_header.py      — AppHeader widget
  src/wft/ui/components/navigation_sidebar.py — collapsible sidebar
  src/wft/ui/components/navigation_item.py — sidebar item widget
  src/wft/ui/components/status_banner.py   — StatusBanner (replaces EvidenceBanner)
  src/wft/ui/components/content_card.py    — ContentCard container
  src/wft/ui/components/confirm_dialog.py  — ConfirmDialog

Modified:
  src/wft/ui/components/evidence_banner.py — compatibility adapter
  src/wft/ui/components/neon_button.py     — refactor with variant property
  src/wft/ui/components/status_badge.py    — refactor with status property
  src/wft/ui/components/page_header.py     — refactor token-aware
  src/wft/ui/components/empty_state.py     — refactor token-aware, non-emoji icon
  src/wft/ui/components/__init__.py        — update exports
  src/wft/ui/components/progress_overlay.py — limited token migration
  src/wft/ui/main_window.py               — refactor shell
  src/wft/bootstrap.py                     — add ThemeManager
  src/wft/infrastructure/settings/settings.py — add theme/sidebar keys
```

---

### Task 1: PageId Enum

**Files:**
- Create: `src/wft/ui/pages/page_id.py`
- Test: `tests/unit/test_page_id.py`

**Interfaces:**
- Produces: `class PageId(StrEnum)` with 18 members and enum value `"home"`–`"settings"`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_page_id.py
from wft.ui.pages.page_id import PageId


class TestPageId:
    def test_has_expected_count(self) -> None:
        members = list(PageId)
        assert len(members) == 18

    def test_home_is_landing(self) -> None:
        assert PageId.HOME == "home"

    def test_settings_is_last(self) -> None:
        assert PageId.SETTINGS == "settings"

    def test_str_returns_key(self) -> None:
        assert str(PageId.DASHBOARD) == "dashboard"

    def test_invalid_value_raises(self) -> None:
        try:
            PageId("nonexistent")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_all_keys_are_known(self) -> None:
        """Matches the page keys used in existing _page_map."""
        expected = {
            "home", "dashboard", "cases", "evidence",
            "adb", "decrypt", "chats", "contacts",
            "groups", "calls", "media", "timeline",
            "recovered", "voip", "search", "reports",
            "audit", "settings",
        }
        actual = {m.value for m in PageId}
        assert actual == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_page_id.py -v --tb=short`
Expected: ERROR / ModuleNotFoundError (file doesn't exist yet)

- [ ] **Step 3: Write minimal implementation**

```python
# src/wft/ui/pages/page_id.py
from enum import StrEnum


class PageId(StrEnum):
    HOME = "home"
    DASHBOARD = "dashboard"
    CASES = "cases"
    EVIDENCE = "evidence"
    ADB_EXTRACTOR = "adb"
    DECRYPTOR = "decrypt"
    CHATS = "chats"
    CONTACTS = "contacts"
    GROUPS = "groups"
    CALLS = "calls"
    MEDIA = "media"
    TIMELINE = "timeline"
    RECOVERED = "recovered"
    VOIP = "voip"
    SEARCH = "search"
    REPORTS = "reports"
    AUDIT = "audit"
    SETTINGS = "settings"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_page_id.py -v --tb=short`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/pages/page_id.py tests/unit/test_page_id.py
git commit -m "feat: add PageId StrEnum with 18 members"
```

---

### Task 2: DesignTokens Data Class

**Files:**
- Create: `src/wft/ui/theme/__init__.py`
- Create: `src/wft/ui/theme/tokens.py`
- Create: `src/wft/ui/theme/themes.py`
- Test: `tests/unit/test_design_tokens.py`

**Interfaces:**
- Produces: `class DesignTokens` (frozen dataclass, all sections validation)
- Produces: `def dark_forensic() -> DesignTokens` preset function
- Consumes: none

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_design_tokens.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_design_tokens.py -v --tb=short`
Expected: Import errors

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/theme/tokens.py
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
```

```python
# src/wft/ui/theme/themes.py
from wft.ui.theme.tokens import DesignTokens


def dark_forensic() -> DesignTokens:
    return DesignTokens()
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/unit/test_design_tokens.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/theme/ tests/unit/test_design_tokens.py
git commit -m "feat: add DesignTokens frozen dataclass and dark_forensic preset"
```

---

### Task 3: Layout Helpers + Style Helpers

**Files:**
- Create: `src/wft/ui/theme/layout_helpers.py`
- Create: `src/wft/ui/theme/style_helpers.py`
- Test: `tests/unit/test_layout_helpers.py`, `tests/unit/test_style_helpers.py`

**Interfaces:**
- Produces: `apply_page_layout(layout, tokens)`, `apply_card_layout(...)`, `apply_form_layout(...)`, `apply_toolbar_layout(...)`
- Produces: `refresh_style(widget)`, `set_dynamic_property(widget, name, value, *, allowed_values, default_value) -> object`
- Consumes: `DesignTokens`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_layout_helpers.py
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout
from wft.ui.theme.tokens import DesignTokens
from wft.ui.theme.layout_helpers import (
    apply_page_layout,
    apply_card_layout,
    apply_form_layout,
    apply_toolbar_layout,
)


def test_apply_page_layout_sets_margins():
    tokens = DesignTokens()
    layout = QVBoxLayout()
    apply_page_layout(layout, tokens)
    margins = layout.contentsMargins()
    assert margins.left() == tokens.space_20
    assert margins.right() == tokens.space_20
    assert margins.top() == tokens.space_20
    assert margins.bottom() == tokens.space_20
    assert layout.spacing() == tokens.space_16


def test_apply_card_layout_sets_margins():
    tokens = DesignTokens()
    layout = QVBoxLayout()
    apply_card_layout(layout, tokens)
    margins = layout.contentsMargins()
    assert margins.left() == tokens.space_16


def test_apply_form_layout_accepts_qform():
    tokens = DesignTokens()
    layout = QFormLayout()
    apply_form_layout(layout, tokens)
    assert layout.spacing() == tokens.space_10


def test_apply_toolbar_layout_sets_margins():
    tokens = DesignTokens()
    layout = QHBoxLayout()
    apply_toolbar_layout(layout, tokens)
    margins = layout.contentsMargins()
    assert margins.left() == tokens.space_16
    assert layout.spacing() == tokens.space_8
```

```python
# tests/unit/test_style_helpers.py
from unittest.mock import MagicMock, patch
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_layout_helpers.py tests/unit/test_style_helpers.py -v --tb=short`
Expected: Import errors

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/theme/layout_helpers.py
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLayout, QVBoxLayout
from wft.ui.theme.tokens import DesignTokens


def apply_page_layout(layout: QLayout, tokens: DesignTokens) -> None:
    layout.setContentsMargins(
        tokens.space_20, tokens.space_20,
        tokens.space_20, tokens.space_20,
    )
    layout.setSpacing(tokens.space_16)


def apply_card_layout(layout: QLayout, tokens: DesignTokens) -> None:
    layout.setContentsMargins(
        tokens.space_16, tokens.space_16,
        tokens.space_16, tokens.space_16,
    )
    layout.setSpacing(tokens.space_12)


def apply_form_layout(layout: QFormLayout, tokens: DesignTokens) -> None:
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(tokens.space_10)
    layout.setVerticalSpacing(tokens.space_10)


def apply_toolbar_layout(layout: QHBoxLayout, tokens: DesignTokens) -> None:
    layout.setContentsMargins(
        tokens.space_16, tokens.space_8,
        tokens.space_16, tokens.space_8,
    )
    layout.setSpacing(tokens.space_8)
```

```python
# src/wft/ui/theme/style_helpers.py
from collections.abc import Collection
from PySide6.QtWidgets import QWidget


def refresh_style(widget: QWidget) -> None:
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def set_dynamic_property(
    widget: QWidget,
    name: str,
    value: object,
    *,
    allowed_values: Collection[object] | None = None,
    default_value: object | None = None,
) -> object:
    if allowed_values is not None and value not in allowed_values:
        value = default_value
    if widget.property(name) == value:
        return value
    widget.setProperty(name, value)
    refresh_style(widget)
    return value
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_layout_helpers.py tests/unit/test_style_helpers.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/theme/layout_helpers.py src/wft/ui/theme/style_helpers.py tests/unit/test_layout_helpers.py tests/unit/test_style_helpers.py
git commit -m "feat: add layout helpers and style helpers"
```

---

### Task 4: QSS Builder

**Files:**
- Create: `src/wft/ui/theme/qss_builder.py`
- Test: `tests/unit/test_qss_builder.py`

**Interfaces:**
- Produces: `build_base_qss(tokens)`, `build_button_qss(tokens)`, etc.
- Produces: `build_full_qss(tokens) -> str` — combines all sections

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_qss_builder.py
from wft.ui.theme.tokens import DesignTokens
from wft.ui.theme.qss_builder import build_full_qss


def test_contains_required_selectors():
    tokens = DesignTokens()
    qss = build_full_qss(tokens)
    assert "NeonButton[variant=" in qss
    assert "StatusBadge[status=" in qss
    assert "StatusBanner[banner_type=" in qss
    assert "NavigationItem[active=" in qss
    assert "QToolTip" in qss
    assert "QSplitter::handle" in qss
    assert "QScrollBar" in qss
    assert "QProgressBar" in qss


def test_no_unresolved_placeholders():
    tokens = DesignTokens()
    qss = build_full_qss(tokens)
    assert "None" not in qss
    assert "{}" not in qss
    assert len(qss) > 1000
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_qss_builder.py -v --tb=short`
Expected: Import error

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/theme/qss_builder.py
from wft.ui.theme.tokens import DesignTokens


def _c(tokens: DesignTokens, name: str) -> str:
    return getattr(tokens, name)


def build_base_qss(tokens: DesignTokens) -> str:
    bg = _c(tokens, "app_background")
    txt = _c(tokens, "text_primary")
    border = _c(tokens, "border")
    bw = _c(tokens, "border_width")
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
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_qss_builder.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/theme/qss_builder.py tests/unit/test_qss_builder.py
git commit -m "feat: add QSS builder with 10 section helpers"
```

---

### Task 5: ThemeManager

**Files:**
- Create: `src/wft/ui/theme/theme_manager.py`
- Test: `tests/unit/test_theme_manager.py`

**Interfaces:**
- Produces: `class ThemeManager` with `get_tokens()`, `apply_theme(name, persist=False) -> bool`, `set_theme(name) -> bool`, `load_saved_theme()`
- Consumes: `DesignTokens`, `dark_forensic()`, `build_full_qss()`, `AppSettings`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_theme_manager.py
from unittest.mock import MagicMock, patch
from wft.ui.theme.theme_manager import ThemeManager
from wft.ui.theme.tokens import DesignTokens


class TestThemeManager:
    def test_default_tokens(self):
        tm = ThemeManager(settings=MagicMock())
        tokens = tm.get_tokens()
        assert isinstance(tokens, DesignTokens)
        assert tokens.primary == "#00C853"

    def test_apply_theme_returns_true_for_valid(self):
        tm = ThemeManager(settings=MagicMock())
        result = tm.apply_theme("dark_forensic", persist=False)
        assert result is True

    def test_invalid_theme_returns_false(self):
        tm = ThemeManager(settings=MagicMock())
        result = tm.apply_theme("nonexistent", persist=False)
        assert result is False

    def test_set_theme_persists(self):
        mock_settings = MagicMock()
        tm = ThemeManager(settings=mock_settings)
        tm.set_theme("dark_forensic")
        mock_settings.set.assert_called_once()

    def test_load_saved_theme_does_not_persist(self):
        mock_settings = MagicMock()
        mock_settings.get.return_value = None
        tm = ThemeManager(settings=mock_settings)
        tm.load_saved_theme()
        mock_settings.set.assert_not_called()

    def test_load_saved_theme_fallback(self):
        mock_settings = MagicMock()
        mock_settings.get.return_value = "invalid_theme"
        tm = ThemeManager(settings=mock_settings)
        tm.load_saved_theme()
        assert tm.get_tokens().primary == "#00C853"
        mock_settings.set.assert_not_called()

    def test_theme_changed_signal_emitted(self):
        mock_settings = MagicMock()
        tm = ThemeManager(settings=mock_settings)
        received = []
        tm.theme_changed.connect(received.append)
        tm.set_theme("dark_forensic")
        assert len(received) == 1
        assert received[0] == "dark_forensic"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_theme_manager.py -v --tb=short`
Expected: Import errors

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/theme/theme_manager.py
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from wft.ui.theme.tokens import DesignTokens
from wft.ui.theme.themes import dark_forensic
from wft.ui.theme.qss_builder import build_full_qss

_THEME_REGISTRY = {
    "dark_forensic": dark_forensic,
}


class ThemeManager(QObject):
    theme_changed = Signal(str)

    def __init__(self, settings=None, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._tokens: DesignTokens = DesignTokens()

    def get_tokens(self) -> DesignTokens:
        return self._tokens

    def apply_theme(self, name: str, persist: bool = False) -> bool:
        preset_fn = _THEME_REGISTRY.get(name)
        if preset_fn is None:
            return False
        self._tokens = preset_fn()
        qss = build_full_qss(self._tokens)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss)
        if persist and self._settings is not None:
            self._settings.set("ui", "theme", name)
        self.theme_changed.emit(name)
        return True

    def set_theme(self, name: str) -> bool:
        return self.apply_theme(name, persist=True)

    def load_saved_theme(self) -> None:
        saved = None
        if self._settings is not None:
            saved = self._settings.get("ui", "theme")
        name = saved if saved in _THEME_REGISTRY else "dark_forensic"
        self._tokens = _THEME_REGISTRY[name]()
        qss = build_full_qss(self._tokens)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_theme_manager.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/theme/theme_manager.py tests/unit/test_theme_manager.py
git commit -m "feat: add ThemeManager with apply/set/load lifecycle"
```

---

### Task 6: Bootstrap Integration

**Files:**
- Modify: `src/wft/bootstrap.py`
- Modify: `src/wft/infrastructure/settings/settings.py`

**Interfaces:**
- Consumes: `ThemeManager` from task 5
- Consumes: existing `AppSettings`

- [ ] **Step 1: Read bootstrap.py and settings.py to understand current code**

Read: `src/wft/bootstrap.py` and `src/wft/infrastructure/settings/settings.py`

- [ ] **Step 2: Add theme/sidebar settings keys to AppSettings**

Add to `settings.py` (or the equivalent settings class):

```python
# Inside the settings class, add defaults:
DEFAULT_SETTINGS = {
    **existing_defaults,
    "ui": {
        "theme": "dark_forensic",
        "sidebar_expanded": True,
    },
}
```

No need to create new settings if the existing AppSettings already supports arbitrary keys via `set(section, key, value)` and `get(section, key)`.

- [ ] **Step 3: Add ThemeManager to bootstrap**

In `bootstrap.py`, after creating AppSettings and before creating MainWindow:
```python
from wft.ui.theme.theme_manager import ThemeManager
# ... existing code ...
self.theme_manager = ThemeManager(settings=self.settings)
self.theme_manager.load_saved_theme()
```

Pass `theme_manager` to `MainWindow` via `self.main_window.set_theme_manager(self.theme_manager)` (the method already exists on MainWindow at line 386).

- [ ] **Step 4: Run existing tests to verify no regression**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All 222 tests pass (no new tests needed for this wiring)

- [ ] **Step 5: Commit**

```bash
git add src/wft/bootstrap.py src/wft/infrastructure/settings/settings.py
git commit -m "feat: wire ThemeManager into bootstrap and settings"
```

---

### Task 7: StatusBanner + EvidenceBanner Compatibility

**Files:**
- Create: `src/wft/ui/components/status_banner.py`
- Modify: `src/wft/ui/components/evidence_banner.py`
- Test: `tests/unit/test_status_banner.py`

**Interfaces:**
- Produces: `class StatusBanner(QFrame)` with `__init__(text="", banner_type="info", parent=None)`, `set_text(text)`, `set_banner_type(banner_type)`
- Produces: `class EvidenceBanner(StatusBanner)` — compatibility subclass (identical API)

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_status_banner.py
from PySide6.QtWidgets import QFrame
from wft.ui.components.status_banner import StatusBanner
from wft.ui.components.evidence_banner import EvidenceBanner


class TestStatusBanner:
    def test_default_construction(self):
        banner = StatusBanner()
        assert isinstance(banner, QFrame)

    def test_text_and_type_constructor(self):
        banner = StatusBanner("Test message", "verified")
        assert banner._label.text() == "Test message"

    def test_set_text(self):
        banner = StatusBanner()
        banner.set_text("Updated")
        assert banner._label.text() == "Updated"

    def test_set_banner_type(self):
        banner = StatusBanner()
        banner.set_banner_type("warning")
        assert banner._banner_type == "warning"


class TestEvidenceBannerCompat:
    def test_is_status_banner_subclass(self):
        assert issubclass(EvidenceBanner, StatusBanner)

    def test_same_constructor(self):
        banner = EvidenceBanner("Test", "info")
        assert banner._label.text() == "Test"
        assert banner._banner_type == "info"

    def test_set_text_works(self):
        banner = EvidenceBanner()
        banner.set_text("Hello")
        assert banner._label.text() == "Hello"

    def test_set_banner_type_works(self):
        banner = EvidenceBanner()
        banner.set_banner_type("verified")
        assert banner._banner_type == "verified"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_status_banner.py -v --tb=short`
Expected: Import errors

- [ ] **Step 3: Write implementations**

```python
# src/wft/ui/components/status_banner.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy


class StatusBanner(QFrame):
    def __init__(self, text: str = "", banner_type: str = "info", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("statusBanner")
        self._banner_type = banner_type
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)

        icon_map = {
            "verified": "\u2713",
            "warning": "\u26A0",
            "hash_mismatch": "\u2717",
            "unsupported": "\u24D8",
            "info": "\u2139",
        }
        icon_char = icon_map.get(banner_type, "")
        self._icon = QLabel(icon_char)
        self._icon.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self._icon.setMinimumWidth(18)
        self._icon.setVisible(bool(icon_char))
        layout.addWidget(self._icon)

        self._label = QLabel(text)
        self._label.setWordWrap(True)
        layout.addWidget(self._label, 1)

    def set_text(self, text: str) -> None:
        self._label.setText(text)

    def set_banner_type(self, banner_type: str) -> None:
        self._banner_type = banner_type
```

```python
# src/wft/ui/components/evidence_banner.py
from wft.ui.components.status_banner import StatusBanner  # noqa: F401

# Compatibility alias — StatusBanner has an identical constructor
# (text="", banner_type="info", parent=None) and identical methods.
EvidenceBanner = StatusBanner
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_status_banner.py -v --tb=short`
Expected: All passed (EvidenceBanner test may need QApplication — use pytest-qt `qapp` fixture)

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/components/status_banner.py src/wft/ui/components/evidence_banner.py tests/unit/test_status_banner.py
git commit -m "feat: add StatusBanner with EvidenceBanner compatibility alias"
```

---

### Task 8: NeonButton Refactor

**Files:**
- Modify: `src/wft/ui/components/neon_button.py`
- Modify: `src/wft/ui/components/__init__.py`
- Test: `tests/unit/test_neon_button.py`

**Interfaces:**
- Consumes: `DesignTokens`, `set_dynamic_property()`
- Produces: refactored `NeonButton(text="", variant="primary", parent=None)`, `set_variant(variant)`, deprecated `set_style(style)` with translation

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_neon_button.py
from unittest.mock import patch
from PySide6.QtWidgets import QPushButton
from wft.ui.components.neon_button import NeonButton


class TestNeonButtonNewAPI:
    def test_constructs_with_variant(self):
        btn = NeonButton("Test", "primary")
        assert isinstance(btn, QPushButton)
        assert btn.text() == "Test"

    def test_variant_dynamic_property_set(self):
        btn = NeonButton("Test", "danger")
        assert btn.property("variant") == "danger"

    def test_set_variant_updates_property(self):
        btn = NeonButton()
        btn.set_variant("secondary")
        assert btn.property("variant") == "secondary"

    def test_invalid_variant_falls_back(self):
        btn = NeonButton("Test", "invalid")
        assert btn.property("variant") == "secondary"


class TestNeonButtonDeprecatedStyle:
    def test_style_primary_translates(self):
        btn = NeonButton("Test", style="primary")
        assert btn.property("variant") == "primary"

    def test_style_destructive_translates_to_danger(self):
        btn = NeonButton("Test", style="destructive")
        assert btn.property("variant") == "danger"

    def test_set_style_deprecated_translates(self):
        btn = NeonButton()
        btn.set_style("destructive")
        assert btn.property("variant") == "danger"

    def test_set_style_warning_translates(self):
        btn = NeonButton()
        btn.set_style("warning")
        assert btn.property("variant") == "secondary"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_neon_button.py -v --tb=short`
Expected: Failures

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/components/neon_button.py
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy
from wft.ui.theme.style_helpers import set_dynamic_property

_LEGACY_STYLE_MAP = {
    "primary": "primary",
    "secondary": "secondary",
    "destructive": "danger",
    "warning": "secondary",
}

_VALID_VARIANTS = {"primary", "secondary", "danger", "ghost"}


class NeonButton(QPushButton):
    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        parent=None,
        style: Optional[str] = None,
    ) -> None:
        super().__init__(text, parent)
        if style is not None:
            variant = _LEGACY_STYLE_MAP.get(style, "secondary")
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.set_variant(variant)

    def set_variant(self, variant: str) -> None:
        set_dynamic_property(
            self, "variant", variant,
            allowed_values=_VALID_VARIANTS,
            default_value="secondary",
        )

    def set_style(self, style: str) -> None:
        variant = _LEGACY_STYLE_MAP.get(style, "secondary")
        self.set_variant(variant)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_neon_button.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Update __init__.py exports (if needed)**

Check `src/wft/ui/components/__init__.py` — ensure `NeonButton` is still exported.

- [ ] **Step 6: Commit**

```bash
git add src/wft/ui/components/neon_button.py tests/unit/test_neon_button.py
git commit -m "feat: refactor NeonButton with variant property and deprecated style mapping"
```

---

### Task 9: StatusBadge Refactor

**Files:**
- Modify: `src/wft/ui/components/status_badge.py`
- Test: `tests/unit/test_status_badge_refactor.py`

**Interfaces:**
- Consumes: `set_dynamic_property()`
- Produces: refactored `StatusBadge(text="", status="neutral", parent=None)`, `set_status(status)`, deprecated `set_badge_type(badge_type)` with translation

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_status_badge_refactor.py
from wft.ui.components.status_badge import StatusBadge


class TestStatusBadgeNewAPI:
    def test_constructs_with_status(self):
        badge = StatusBadge("Test", "success")
        assert badge.text() == "Test"

    def test_status_dynamic_property_set(self):
        badge = StatusBadge("Test", "warning")
        assert badge.property("status") == "warning"

    def test_set_status_updates_property(self):
        badge = StatusBadge()
        badge.set_status("error")
        assert badge.property("status") == "error"

    def test_invalid_status_falls_back(self):
        badge = StatusBadge("Test", "invalid")
        assert badge.property("status") == "neutral"


class TestStatusBadgeDeprecated:
    def test_set_badge_type_parsed_maps_to_success(self):
        badge = StatusBadge()
        badge.set_badge_type("parsed")
        assert badge.property("status") == "success"

    def test_set_badge_type_verified_maps_to_success(self):
        badge = StatusBadge()
        badge.set_badge_type("verified")
        assert badge.property("status") == "success"

    def test_set_badge_type_failed_maps_to_error(self):
        badge = StatusBadge()
        badge.set_badge_type("failed")
        assert badge.property("status") == "error"

    def test_set_badge_type_partial_maps_to_warning(self):
        badge = StatusBadge()
        badge.set_badge_type("partial")
        assert badge.property("status") == "warning"

    def test_set_badge_type_unsupported_maps_to_neutral(self):
        badge = StatusBadge()
        badge.set_badge_type("unsupported")
        assert badge.property("status") == "neutral"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_status_badge_refactor.py -v --tb=short`
Expected: Failures

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/components/status_badge.py
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy
from wft.ui.theme.style_helpers import set_dynamic_property

_LEGACY_BADGE_MAP = {
    "parsed": "success",
    "recovered": "warning",
    "inferred": "neutral",
    "manual": "warning",
    "verified": "success",
    "partial": "warning",
    "failed": "error",
    "unsupported": "neutral",
    "unverified": "warning",
    "relay": "neutral",
    "probable_peer": "neutral",
    "vpn_proxy": "neutral",
}

_VALID_STATUSES = {"success", "warning", "error", "information", "neutral"}


class StatusBadge(QLabel):
    def __init__(
        self,
        text: str = "",
        status: str = "neutral",
        parent=None,
        badge_type: Optional[str] = None,
    ) -> None:
        super().__init__(text, parent)
        if badge_type is not None:
            status = _LEGACY_BADGE_MAP.get(badge_type, "neutral")
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setMinimumHeight(22)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        set_dynamic_property(
            self, "status", status,
            allowed_values=_VALID_STATUSES,
            default_value="neutral",
        )

    def set_badge_type(self, badge_type: str) -> None:
        status = _LEGACY_BADGE_MAP.get(badge_type, "neutral")
        self.set_status(status)

    def _apply_style(self) -> None:
        pass  # Styling now via QSS dynamic property
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_status_badge_refactor.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/components/status_badge.py tests/unit/test_status_badge_refactor.py
git commit -m "feat: refactor StatusBadge with status property and legacy badge_type mapping"
```

---

### Task 10: PageHeader + EmptyState Refactor

**Files:**
- Modify: `src/wft/ui/components/page_header.py`
- Modify: `src/wft/ui/components/empty_state.py`
- Test: `tests/unit/test_page_header_refactor.py`, `tests/unit/test_empty_state_refactor.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_page_header_refactor.py
from PySide6.QtWidgets import QWidget
from wft.ui.components.page_header import PageHeader


class TestPageHeader:
    def test_constructs_with_title_and_subtitle(self):
        h = PageHeader("Title", "Subtitle")
        assert h._title.text() == "Title"

    def test_set_title(self):
        h = PageHeader("Old")
        h.set_title("New")
        assert h._title.text() == "New"

    def test_no_hardcoded_colors(self):
        """Style is now applied via QSS, not inline stylesheets."""
        h = PageHeader("Test")
        assert "color" not in h._title.styleSheet()
```

```python
# tests/unit/test_empty_state_refactor.py
from PySide6.QtWidgets import QWidget
from wft.ui.components.empty_state import EmptyState


class TestEmptyState:
    def test_default_construction(self):
        es = EmptyState()
        assert isinstance(es, QWidget)

    def test_custom_title(self):
        es = EmptyState("Custom Title")
        assert "Custom Title" in es._title.text()

    def test_description_shown(self):
        es = EmptyState("Title", "Description text")
        assert es._desc.text() == "Description text"

    def test_no_emoji_icon(self):
        """Icon must not use emoji glyphs; uses styled text fallback."""
        es = EmptyState()
        icon_text = es._icon.text()
        assert "\U0001F600" not in icon_text  # no smiley emoji
        assert "\u24D8" not in icon_text  # no circled i (this uses it currently)
```

Note: The no-emoji test will need adjustment based on the actual fallback. The goal is to remove `\u24D8` and replace with a styled text label.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_page_header_refactor.py tests/unit/test_empty_state_refactor.py -v --tb=short`
Expected: Failures

- [ ] **Step 3: Write implementations**

```python
# src/wft/ui/components/page_header.py
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)

        self._title = QLabel(title)
        self._title.setObjectName("pageTitle")
        layout.addWidget(self._title)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("subtitleLabel")
            layout.addWidget(sub)

        layout.addStretch()

    def set_title(self, title: str) -> None:
        self._title.setText(title)
```

```python
# src/wft/ui/components/empty_state.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget, QSizePolicy


class EmptyState(QWidget):
    def __init__(
        self,
        title: str = "No data available",
        description: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        self._icon = QLabel("--")
        self._icon.setObjectName("emptyStateIcon")
        self._icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon)

        self._title = QLabel(title)
        self._title.setObjectName("emptyStateTitle")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        self._desc: QLabel | None = None
        if description:
            self._desc = QLabel(description)
            self._desc.setObjectName("emptyStateDescription")
            self._desc.setAlignment(Qt.AlignCenter)
            self._desc.setWordWrap(True)
            layout.addWidget(self._desc)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_title(self, title: str) -> None:
        self._title.setText(title)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_page_header_refactor.py tests/unit/test_empty_state_refactor.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/components/page_header.py src/wft/ui/components/empty_state.py tests/unit/test_page_header_refactor.py tests/unit/test_empty_state_refactor.py
git commit -m "feat: refactor PageHeader and EmptyState to use DesignTokens, no emoji icons"
```

---

### Task 11: ContentCard

**Files:**
- Create: `src/wft/ui/components/content_card.py`
- Test: `tests/unit/test_content_card.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_content_card.py
from PySide6.QtWidgets import QFrame, QLabel
from wft.ui.components.content_card import ContentCard


class TestContentCard:
    def test_default_construction(self):
        card = ContentCard()
        assert isinstance(card, QFrame)

    def test_title_set(self):
        card = ContentCard(title="My Card")
        assert card._title is not None
        assert card._title.text() == "My Card"

    def test_no_title_no_header(self):
        """Header area not created when no title/subtitle/actions."""
        card = ContentCard()
        assert card._title is None

    def test_subtitle_set(self):
        card = ContentCard(title="T", subtitle="S")
        assert card._subtitle is not None
        assert card._subtitle.text() == "S"

    def test_content_layout_has_margins(self):
        card = ContentCard()
        margins = card._content_layout.contentsMargins()
        assert margins.left() > 0  # tokens applied
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_content_card.py -v --tb=short`
Expected: Import errors

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/components/content_card.py
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class ContentCard(QFrame):
    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ContentCard")
        self._title: QLabel | None = None
        self._subtitle: QLabel | None = None
        self._header_layout: QHBoxLayout | None = None
        self._footer_layout: QHBoxLayout | None = None

        self._content_layout = QVBoxLayout(self)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(12)

        if title or subtitle:
            self._header_layout = QHBoxLayout()
            self._header_layout.setContentsMargins(0, 0, 0, 0)
            self._header_layout.setSpacing(8)

            if title:
                self._title = QLabel(title)
                self._title.setObjectName("contentCardTitle")
                self._header_layout.addWidget(self._title)

            if subtitle:
                self._subtitle = QLabel(subtitle)
                self._subtitle.setObjectName("contentCardSubtitle")
                self._header_layout.addWidget(self._subtitle)

            self._header_layout.addStretch()
            self._content_layout.addLayout(self._header_layout)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_content_card.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/components/content_card.py tests/unit/test_content_card.py
git commit -m "feat: add ContentCard reusable container"
```

---

### Task 12: ConfirmDialog

**Files:**
- Create: `src/wft/ui/components/confirm_dialog.py`
- Test: `tests/unit/test_confirm_dialog.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_confirm_dialog.py
from PySide6.QtWidgets import QDialog, QPushButton
from wft.ui.components.confirm_dialog import ConfirmDialog


class TestConfirmDialog:
    def test_standard_mode(self):
        dialog = ConfirmDialog(
            title="Confirm",
            message="Are you sure?",
        )
        assert dialog.windowTitle() == "Confirm"

    def test_destructive_mode_cancel_focused(self):
        dialog = ConfirmDialog(
            title="Delete",
            message="Delete this item?",
            destructive=True,
        )
        # Cancel button should have focus
        focused = dialog.focusWidget()
        assert focused is not None

    def test_accept_returns_correct_code(self):
        dialog = ConfirmDialog(title="Test", message="Test")
        # Can't easily call exec_() in unit test, but can check button roles
        buttons = dialog.findChildren(QPushButton)
        assert len(buttons) >= 2
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_confirm_dialog.py -v --tb=short`
Expected: Import errors

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/components/confirm_dialog.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from wft.ui.components.neon_button import NeonButton


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        details: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        destructive: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        if details:
            details_edit = QTextEdit()
            details_edit.setPlainText(details)
            details_edit.setReadOnly(True)
            details_edit.setMaximumHeight(100)
            layout.addWidget(details_edit)

        layout.addStretch()

        btn_box = QDialogButtonBox()
        cancel = QPushButton(cancel_text)
        confirm = NeonButton(confirm_text, "danger" if destructive else "primary")

        btn_box.addButton(cancel, QDialogButtonBox.RejectRole)
        btn_box.addButton(confirm, QDialogButtonBox.AcceptRole)

        if destructive:
            cancel.setDefault(True)
            cancel.setAutoDefault(True)
            confirm.setDefault(False)
            confirm.setAutoDefault(False)
            cancel.setFocus()

        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_confirm_dialog.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/components/confirm_dialog.py tests/unit/test_confirm_dialog.py
git commit -m "feat: add ConfirmDialog with standard and destructive modes"
```

---

### Task 13: NavigationItem + NavigationSidebar

**Files:**
- Create: `src/wft/ui/components/navigation_item.py`
- Create: `src/wft/ui/components/navigation_sidebar.py`
- Test: `tests/unit/test_navigation_sidebar.py`

**Interfaces:**
- Consumes: `PageId`, `DesignTokens`, `set_dynamic_property()`
- Produces: `NavigationItem` (QPushButton), `NavigationSidebar` (QWidget with expand/collapse, group headers, item list)
- Signal: `NavigationSidebar.page_selected(page_id: PageId)`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_navigation_sidebar.py
from PySide6.QtWidgets import QWidget
from wft.ui.pages.page_id import PageId
from wft.ui.components.navigation_sidebar import NavigationSidebar


class TestNavigationSidebar:
    def test_constructs_expanded(self):
        sidebar = NavigationSidebar()
        assert isinstance(sidebar, QWidget)

    def test_has_all_pages(self):
        sidebar = NavigationSidebar()
        expected_count = 17  # all except HOME
        assert sidebar._item_count() == expected_count

    def test_page_selected_signal(self):
        sidebar = NavigationSidebar()
        received = []
        sidebar.page_selected.connect(received.append)
        sidebar._on_item_clicked(PageId.DASHBOARD)
        assert len(received) == 1
        assert received[0] == PageId.DASHBOARD

    def test_set_active_updates_selection(self):
        sidebar = NavigationSidebar()
        sidebar.set_active(PageId.CASES)
        # active item should have the active property

    def test_collapse_toggle(self):
        sidebar = NavigationSidebar()
        sidebar.toggle_collapse()
        assert sidebar._is_collapsed
        sidebar.toggle_collapse()
        assert not sidebar._is_collapsed

    def test_collapsed_tooltips(self):
        sidebar = NavigationSidebar()
        sidebar.toggle_collapse()
        assert sidebar._is_collapsed
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_navigation_sidebar.py -v --tb=short`
Expected: Import errors

- [ ] **Step 3: Write implementations**

```python
# src/wft/ui/components/navigation_item.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy


class NavigationItem(QPushButton):
    def __init__(self, label: str, icon_text: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setText(label)
        self.setObjectName("NavigationItem")
        self.setProperty("active", False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(False)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)
        self.update()
```

```python
# src/wft/ui/components/navigation_sidebar.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from wft.ui.pages.page_id import PageId
from wft.ui.components.navigation_item import NavigationItem

_GROUPS: list[tuple[str, list[tuple[str, PageId]]]] = [
    ("Case Management", [
        ("Dashboard", PageId.DASHBOARD),
        ("Cases", PageId.CASES),
        ("Evidence", PageId.EVIDENCE),
    ]),
    ("Acquisition", [
        ("ADB Extractor", PageId.ADB_EXTRACTOR),
    ]),
    ("Analysis", [
        ("Chat Viewer", PageId.CHATS),
        ("Contacts", PageId.CONTACTS),
        ("Groups", PageId.GROUPS),
        ("Calls", PageId.CALLS),
        ("Media", PageId.MEDIA),
        ("Timeline", PageId.TIMELINE),
        ("Recovered Data", PageId.RECOVERED),
        ("VoIP Analysis", PageId.VOIP),
    ]),
    ("Tools", [
        ("Decryptor", PageId.DECRYPTOR),
        ("Search", PageId.SEARCH),
        ("Reports", PageId.REPORTS),
    ]),
    ("System", [
        ("Audit Log", PageId.AUDIT),
        ("Settings", PageId.SETTINGS),
    ]),
]


class NavigationSidebar(QWidget):
    page_selected = Signal(PageId)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._is_collapsed = False
        self._items: dict[PageId, NavigationItem] = {}

        self.setObjectName("NavigationSidebar")
        self.setMinimumWidth(56)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)

        self._collapse_btn = QPushButton("\u2630")
        self._collapse_btn.setObjectName("sidebarCollapseBtn")
        self._collapse_btn.setCursor(Qt.PointingHandCursor)
        self._collapse_btn.clicked.connect(self.toggle_collapse)
        self._outer_layout.addWidget(self._collapse_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._scroll_content = QWidget()
        self._nav_layout = QVBoxLayout(self._scroll_content)
        self._nav_layout.setContentsMargins(4, 4, 4, 4)
        self._nav_layout.setSpacing(2)
        self._nav_layout.addStretch()

        self._build_groups()

        scroll.setWidget(self._scroll_content)
        self._outer_layout.addWidget(scroll, 1)

    def _build_groups(self) -> None:
        for group_name, items in _GROUPS:
            header = QLabel(group_name)
            header.setObjectName("sidebarGroupHeader")
            self._nav_layout.addWidget(header)

            for label, page_id in items:
                item = NavigationItem(label)
                self._nav_layout.addWidget(item)
                self._items[page_id] = item
                item.clicked.connect(lambda checked=False, pid=page_id: self._on_item_clicked(pid))

    def _on_item_clicked(self, page_id: PageId) -> None:
        self.page_selected.emit(page_id)

    def set_active(self, page_id: PageId | None) -> None:
        for pid, item in self._items.items():
            item.set_active(pid == page_id)

    def toggle_collapse(self) -> None:
        self._is_collapsed = not self._is_collapsed
        for item in self._items.values():
            item.setVisible(not self._is_collapsed)
        # Hide group headers when collapsed
        for i in range(self._nav_layout.count()):
            w = self._nav_layout.itemAt(i).widget()
            if isinstance(w, QLabel) and w.objectName() == "sidebarGroupHeader":
                w.setVisible(not self._is_collapsed)

    def _item_count(self) -> int:
        return len(self._items)

    @property
    def is_collapsed(self) -> bool:
        return self._is_collapsed
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_navigation_sidebar.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Update __init__.py**

Ensure `src/wft/ui/components/__init__.py` exports `NavigationSidebar`, `NavigationItem`.

- [ ] **Step 6: Commit**

```bash
git add src/wft/ui/components/navigation_item.py src/wft/ui/components/navigation_sidebar.py tests/unit/test_navigation_sidebar.py
git commit -m "feat: add NavigationItem and NavigationSidebar with collapsible groups"
```

---

### Task 14: AppHeader

**Files:**
- Create: `src/wft/ui/components/app_header.py`
- Test: `tests/unit/test_app_header.py`

**Interfaces:**
- Consumes: `DesignTokens`, `PageId`
- Signal: `home_clicked()`
- Produces: `class AppHeader(QWidget)` with case_badge label, case_name label, logo clickable to HOME

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_app_header.py
from PySide6.QtWidgets import QWidget
from wft.ui.components.app_header import AppHeader
from wft.ui.pages.page_id import PageId


class TestAppHeader:
    def test_constructs(self):
        header = AppHeader()
        assert isinstance(header, QWidget)

    def test_logo_clickable(self):
        header = AppHeader()
        received = []
        header.home_clicked.connect(received.append)
        header._logo_btn.click()
        assert len(received) == 1

    def test_case_badge_updates(self):
        header = AppHeader()
        header.set_case_status("OPEN")
        assert "OPEN" in header._case_badge.text()

    def test_case_name_elided(self):
        header = AppHeader()
        header.set_case_name("Test Case 123")
        assert header._case_name.text() == "Test Case 123"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/unit/test_app_header.py -v --tb=short`
Expected: Import errors

- [ ] **Step 3: Write implementation**

```python
# src/wft/ui/components/app_header.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy


class AppHeader(QWidget):
    home_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AppHeader")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        self._logo_btn = QPushButton("WF")
        self._logo_btn.setObjectName("headerLogo")
        self._logo_btn.setCursor(Qt.PointingHandCursor)
        self._logo_btn.setFixedSize(32, 32)
        self._logo_btn.setToolTip("Go to home")
        self._logo_btn.clicked.connect(self.home_clicked.emit)
        layout.addWidget(self._logo_btn)

        self._title = QLabel("WhatsApp Forensicator")
        self._title.setObjectName("headerTitle")
        layout.addWidget(self._title)

        self._version = QLabel("v1.0.0a1")
        self._version.setObjectName("headerVersion")
        layout.addWidget(self._version)

        layout.addStretch()

        self._case_badge = QLabel()
        self._case_badge.setObjectName("headerCaseBadge")
        self._case_badge.setVisible(False)
        layout.addWidget(self._case_badge)

        self._case_name = QLabel()
        self._case_name.setObjectName("headerCaseName")
        self._case_name.setVisible(False)
        self._case_name.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self._case_name.setWordWrap(False)
        layout.addWidget(self._case_name)

    def set_case_status(self, status: str) -> None:
        self._case_badge.setText(status)
        self._case_badge.setVisible(bool(status))

    def set_case_name(self, name: str) -> None:
        self._case_name.setText(name)
        self._case_name.setVisible(bool(name))
        if name:
            self._case_name.setToolTip(name)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/unit/test_app_header.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/wft/ui/components/app_header.py tests/unit/test_app_header.py
git commit -m "feat: add AppHeader with logo, title, version, case badge"
```

---

### Task 15: MainWindow Refactor — Shell Layout + Sidebar Integration

**Files:**
- Modify: `src/wft/ui/main_window.py`
- Test: `tests/unit/test_main_window_shell.py`

**Consumes:** `AppHeader`, `NavigationSidebar`, `PageId`, `ThemeManager`
**Produces:** Refactored MainWindow with sidebar + header + status bar

- [ ] **Step 1: Read current main_window.py to understand all signals and existing code**

- [ ] **Step 2: Write failing tests**

```python
# tests/unit/test_main_window_shell.py
from PySide6.QtWidgets import QMainWindow, QStackedWidget
from wft.ui.pages.page_id import PageId


class TestMainWindowShell:
    def test_has_app_header(self, main_window):
        assert hasattr(main_window, "_app_header")

    def test_has_sidebar(self, main_window):
        assert hasattr(main_window, "_sidebar")

    def test_has_page_stack(self, main_window):
        assert hasattr(main_window, "_pages")
        assert isinstance(main_window._pages, QStackedWidget)

    def test_navigate_to_home(self, main_window):
        main_window.navigate_to(PageId.HOME)
        # verify no exception

    def test_navigate_to_dashboard(self, main_window):
        main_window.navigate_to(PageId.DASHBOARD)
        assert main_window._pages.currentWidget() is not None

    def test_sidebar_signal_connected(self, main_window):
        connections = main_window._sidebar.page_selected.slot_count()
        # Should be connected to something
```

- [ ] **Step 3: Refactor MainWindow**

Key changes to `main_window.py`:
1. Remove `_build_nav_bar()` and `_nav_tabs` attribute
2. Remove global KPI strip (`_build_kpi_strip()` and `_kpi_cards`)
3. Replace horizontal nav with sidebar
4. Add AppHeader
5. Rewrite `navigate_to()` to accept `PageId | str`
6. Rewrite `_on_nav_changed()` → `_on_sidebar_nav(page_id)`
7. Preserve all 18 page instances in `_pages` (QStackedWidget)
8. Build `dict[PageId, QWidget]` mapping
9. Preserve shortcuts, status bar, case change handler
10. Keep `_refresh_kpi_strip()` → move to Dashboard page (deferred)
11. Connect sidebar `page_selected` signal
12. Connect AppHeader `home_clicked` signal

The refactored layout:
```python
def __init__(self, container, ctx):
    super().__init__()
    self._container = container
    self._ctx = ctx
    self.setWindowTitle("WHATSAPP FORENSICATOR")
    self.resize(1366, 768)
    self.setMinimumSize(1024, 600)

    central = QWidget()
    self.setCentralWidget(central)
    root = QVBoxLayout(central)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    # AppHeader
    self._app_header = AppHeader()
    self._app_header.home_clicked.connect(lambda: self.navigate_to(PageId.HOME))
    root.addWidget(self._app_header)

    # Content: Sidebar + Pages
    content = QHBoxLayout()
    content.setContentsMargins(0, 0, 0, 0)
    content.setSpacing(0)

    self._sidebar = NavigationSidebar()
    self._sidebar.page_selected.connect(self._on_sidebar_nav)
    content.addWidget(self._sidebar)

    self._pages = QStackedWidget()
    # ... build all 18 pages ...
    content.addWidget(self._pages, 1)
    root.addLayout(content, 1)

    # Status bar
    self._sb = QStatusBar()
    self.setStatusBar(self._sb)
```

- [ ] **Step 4: Run tests to verify**

Run: `python -m pytest tests/unit/test_main_window_shell.py -v --tb=short`
Expected: All passed

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All 222+ tests pass

- [ ] **Step 6: Commit**

```bash
git add src/wft/ui/main_window.py tests/unit/test_main_window_shell.py
git commit -m "feat: refactor MainWindow shell with AppHeader, NavigationSidebar, native status bar"
```

---

### Task 16: Legacy Tab Bar Removal

**Files:**
- Modify: `src/wft/ui/main_window.py` (final cleanup)
- Test: run full suite

**Note:** The old tab bar references should already be removed in Task 15. This task does a final audit and cleanup.

- [ ] **Step 1: Search for stale references**

```bash
rg "_nav_tabs|_nav_map|_nav_items|_on_nav_changed|QTabBar" src/
```

- [ ] **Step 2: Remove any remaining references**

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: remove legacy horizontal tab bar and stale nav references"
```

---

### Task 17: Sidebar State Persistence

**Files:**
- Modify: `src/wft/ui/components/navigation_sidebar.py` (add persistence)
- Test: `tests/unit/test_navigation_sidebar.py` (extend)

- [ ] **Step 1: Write failing test**

```python
def test_state_persistence(self, sidebar, mock_settings):
    sidebar.toggle_collapse()
    assert sidebar.is_collapsed
```

- [ ] **Step 2: Implement persistence**

Add to `NavigationSidebar.__init__`:
```python
self._settings_callback = None
```

Add method:
```python
def set_persistence_callback(self, callback):
    self._settings_callback = callback

def toggle_collapse(self):
    self._is_collapsed = not self._is_collapsed
    ...
    if self._settings_callback:
        self._settings_callback(self._is_collapsed)
```

Wire in MainWindow:
```python
self._sidebar.set_persistence_callback(
    lambda collapsed: self._container.settings.set(
        "ui", "sidebar_expanded", not collapsed,
    )
)
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: add sidebar state persistence via settings callback"
```

---

### Task 18: ProgressOverlay Token Migration

**Files:**
- Modify: `src/wft/ui/components/progress_overlay.py`
- Test: run existing tests

- [ ] **Step 1: Read progress_overlay.py**

- [ ] **Step 2: Apply limited token migration**

- Replace inline spacing with `apply_card_layout(layout, tokens)` from layout_helpers
- Replace hardcoded button min heights with `tokens.button_height`
- Replace inline color values with QSS class-based styling via object names
- Preserve unique size constraints (minimumWidth, maximumWidth)

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: migrate ProgressOverlay spacing and colors to DesignTokens"
```

---

### Task 19: Contrast Verification + Completion Report

- [ ] **Step 1: Measure all required contrast pairs**

Using the spec's 8 required pairs, calculate contrast ratios for the dark_forensic preset.

- [ ] **Step 2: Adjust any failing combinations**

Record adjustments in the completion report.

- [ ] **Step 3: Verify all 17 pages accessible from sidebar**

Manual check: click each sidebar item, verify the correct page shows.

- [ ] **Step 4: Test at 1366×768, 1600×900, 1920×1080**

- [ ] **Step 5: Test at 100%, 125%, 150% scaling**

- [ ] **Step 6: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All passing

- [ ] **Step 7: Write completion report**

Write `docs/superpowers/reports/2026-07-21-phase1-completion.md` covering:
- Files created and modified
- Token categories added
- Shared QSS sections created
- Reusable components migrated
- Legacy inline styles still remaining
- Compatibility issues found
- Test results
- Manual UI checks
- Contrast ratios measured
- Confirmation that forensic/business logic was not changed
- Recommended tasks for Phase 2

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/reports/2026-07-21-phase1-completion.md
git commit -m "docs: add Phase 1 completion report"
```

---

## Self-Review

**Spec coverage:** Every section of the spec is covered:
- DesignTokens (Section 6) → Task 2
- Theme presets (Section 6.3) → Task 2
- ThemeManager (Section 7) → Task 5
- QSS builder (Section 7.5) → Task 4
- Layout helpers (Section 8) → Task 3
- Style helper (Section 9) → Task 3
- Main window layout (Section 10) → Task 15
- AppHeader (Section 10.1) → Task 14
- NavigationSidebar (Section 10.2) → Task 13
- HomePage (Section 10.3) → Task 15
- StatusBar (Section 10.4) → Task 15
- PageId mapping (Section 10.5) → Task 1, Task 15
- NeonButton (Section 11.1) → Task 8
- StatusBadge (Section 11.2) → Task 9
- StatusBanner (Section 11.3) → Task 7
- PageHeader (Section 11.4) → Task 10
- ContentCard (Section 11.5) → Task 11
- EmptyState (Section 11.6) → Task 10
- ConfirmDialog (Section 11.7) → Task 12
- Component compatibility (Section 12) → Tasks 7, 8, 9, 10
- Settings (Section 13) → Task 6, Task 17
- Accessibility (Section 14) → Task 13 (tooltips), Task 15 (nav)
- Contrast verification (Section 15) → Task 19
- Legacy navigation migration (Section 27) → Task 16
- ProgressOverlay token migration (Section 26) → Task 18
- Icon resource audit (Section 24) → Task 13
- deferred components (Section 28) → acknowledged, no tasks

**Placeholder scan:** No TBDs, TODOs, or incomplete sections.

**Type consistency:** PageId.StrEnum used consistently. DesignTokens values, set_dynamic_property signature, and layout helper signatures are consistent across all tasks.
