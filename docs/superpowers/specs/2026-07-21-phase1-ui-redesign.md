# Phase 1 — UI Redesign Foundation

**Date:** 2026-07-21
**Project:** WhatsApp Forensic Toolkit
**Status:** Approved design specification (v3)
**Version:** 1.2

---

## 1. Overview

Phase 1 establishes the foundational UI infrastructure for a complete
application redesign. It introduces a centralized theme system, reusable
presentation components, a collapsible grouped sidebar, and a refactored
main-window shell — without modifying any forensic, acquisition, parsing,
or business logic.

Existing pages remain usable inside the new shell. Individual page contents
will be redesigned in Phases 2–6.

---

## 2. Scope

### In Scope

- DesignTokens (frozen dataclass with color, spacing, typography,
  dimension, radius, animation, and icon tokens)
- Theme presets (dark_forensic default; high_contrast deferred)
- ThemeManager (holds active tokens, generates+applies QSS)
- QSS builder (section-based helpers: base, button, form, table,
  navigation, dialog, scrollbar, feedback, container, misc)
- Layout helpers (apply_page_layout, apply_card_layout, etc.)
- Style helper (refresh_style via unpolish/polish)
- App header (logo, title, version, active case badge)
- Collapsible grouped sidebar (expanded 240px, collapsed 56px)
- Navigation groups: Case Management, Acquisition, Analysis, Tools, System
- Main window shell (header + sidebar + page area + status bar)
- Refactored shared components (NeonButton, StatusBadge, StatusBanner,
  PageHeader, EmptyState, ContentCard, ConfirmDialog)
- EvidenceBanner → StatusBanner compatibility adapter
- Global QSS generated from tokens (sole app-level stylesheet)
- Theme integration with existing settings system
- Sidebar state persistence
- Removal of horizontal tab-bar navigation
- KPI strip removal from global chrome
- All 18 existing widgets preserved in QStackedWidget (17 nav-accessible
  pages + HomePage as landing page outside navigation)
- Keyboard navigation, focus states, accessible names
- Responsive layout at 1366×768–1920×1080, 100%–150% scaling

### Out of Scope (Phase 1)

- Redesign of individual page contents (Dashboard, Evidence, Chats, etc.)
- Changes to forensic, ADB, database, evidence, decryption, recovery,
  report, audit, search, or case-management logic
- New features or functionality
- Migration of ParseEvidenceWorker / BatchImportWorker to QRunnable
- PDF report generation, ADB extraction, backup decryption
- Network capture, media thumbnail generation
- Case encryption, locking, export manifests
- high_contrast theme preset (deferred until stable)
- DataTable reusable component (deferred until first table-heavy page
  redesign in Phase 2 or later)

---

## 3. Directory Structure

```
src/wft/ui/
├── __init__.py
├── main_window.py              # REFACTOR — new shell layout
├── theme/
│   ├── __init__.py
│   ├── tokens.py               # DesignTokens frozen dataclass
│   ├── themes.py               # Theme presets (dark_forensic only)
│   ├── theme_manager.py        # ThemeManager
│   ├── qss_builder.py          # QSS generation from tokens
│   ├── layout_helpers.py       # apply_page_layout, etc.
│   └── style_helpers.py        # refresh_style helper
├── components/
│   ├── __init__.py
│   ├── app_header.py           # NEW — top header bar
│   ├── navigation_sidebar.py   # NEW — collapsible grouped sidebar
│   ├── page_header.py          # REFACTOR — token-aware
│   ├── content_card.py         # NEW — reusable card container
│   ├── neon_button.py          # REFACTOR — dynamic property "variant"
│   ├── status_badge.py         # REFACTOR — dynamic property "status"
│   ├── status_banner.py        # RENAME from evidence_banner.py
│   ├── evidence_banner.py      # COMPAT — adapter wrapping StatusBanner
│   ├── empty_state.py          # REFACTOR — token-aware
│   ├── confirm_dialog.py       # NEW — standardized dialog
│   └── progress_overlay.py     # PRESERVE (unchanged in Phase 1)
├── pages/
│   ├── __init__.py
│   ├── page_id.py              # NEW — PageId StrEnum
│   └── ... (existing pages preserved)
├── workers/                    # PRESERVE
├── themes/                     # PRESERVE (legacy QSS files, rollback/reference only)
└── utils/
    └── font_utils.py           # PRESERVE
```

---

## 4. Page Inventory

The following table documents every page widget in the existing
QStackedWidget. Page IDs with a dash in the sidebar group column are not
nav-accessible.

| # | Page Key | Widget Class | PageId | Sidebar Group | Sidebar Label | Lazy-loaded |
|---|----------|-------------|--------|---------------|---------------|-------------|
| 0 | _(none)_ | HomePage | HOME | — (landing) | — | No |
| 1 | dashboard | DashboardPage | DASHBOARD | Case Management | Dashboard | No |
| 2 | cases | CreateCasePage | CASES | Case Management | Cases | No |
| 3 | evidence | EvidencePage | EVIDENCE | Case Management | Evidence | No |
| 4 | adb | ADBExtractorPage | ADB_EXTRACTOR | Acquisition | ADB Extractor | No |
| 5 | decrypt | DecryptorPage | DECRYPTOR | Tools | Decryptor | No |
| 6 | chats | ChatsPage | CHATS | Analysis | Chat Viewer | No |
| 7 | contacts | ContactsPage | CONTACTS | Analysis | Contacts | No |
| 8 | groups | GroupsPage | GROUPS | Analysis | Groups | No |
| 9 | calls | CallsPage | CALLS | Analysis | Calls | No |
| 10 | media | MediaPage | MEDIA | Analysis | Media | No |
| 11 | timeline | TimelinePage | TIMELINE | Analysis | Timeline | No |
| 12 | recovered | RecoveredPage | RECOVERED | Analysis | Recovered Data | No |
| 13 | voip | VoIPPage | VOIP | Analysis | VoIP Analysis | No |
| 14 | search | SearchPage | SEARCH | Tools | Search | No |
| 15 | reports | ReportsPage | REPORTS | Tools | Reports | No |
| 16 | audit | AuditPage | AUDIT | System | Audit Log | No |
| 17 | settings | SettingsPage | SETTINGS | System | Settings | No |

**Totals:** 18 QStackedWidget children, 17 _page_map entries, 17 sidebar
items. Page 0 (HomePage) is the startup landing page and is not
nav-accessible.

---

## 5. PageId Enum

```python
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

One enum member per verified existing page. The project requires
Python >=3.11 (per `pyproject.toml`), so `StrEnum` is valid.

MainWindow or NavigationController maintains a `dict[PageId, QWidget]`
whose values are registered as children of QStackedWidget. A reverse
mapping `dict[QWidget, PageId]` is defined only if required by signal
handlers. No scattered numeric indexes in new code. Existing
numeric-index dependencies in the old tab bar must be audited and
migrated before the old tab bar is removed (see Section 27).

---

## 6. DesignTokens

### 6.1 Definition

Frozen dataclass `DesignTokens` with the following groups:

**Colors:**
- `app_background` — main window background
- `sidebar_background` — sidebar surface
- `header_background` — header surface
- `surface` — card/section surface
- `surface_elevated` — hovered/elevated surface
- `surface_hover` — hover state for interactive surfaces
- `border` — default border
- `border_focus` — focus ring border
- `primary` — primary action fill
- `primary_hover` — primary hover fill
- `primary_pressed` — primary pressed fill
- `primary_text` — text on primary fill
- `text_primary` — primary body text
- `text_secondary` — secondary/supporting text
- `text_muted` — muted/disabled text
- `success` — success indicator
- `warning` — warning indicator
- `error` — error indicator
- `information` — information indicator
- `disabled_background` — disabled control fill
- `disabled_text` — disabled control text
- `selection_background` — selection highlight

**Spacing:** `space_2`, `space_4`, `space_6`, `space_8`, `space_10`,
`space_12`, `space_16`, `space_20`, `space_24`, `space_32`

Each is an `int` representing pixels.

**Typography:**
- `font_family: str` — primary font family (e.g. `"Segoe UI, sans-serif"`)
- `font_size_caption: int` — 11px
- `font_size_body: int` — 13px
- `font_size_label: int` — 12px
- `font_size_section: int` — 15px
- `font_size_page_title: int` — 20px
- `font_size_app_title: int` — 22px
- `font_weight_regular: int` — 400
- `font_weight_medium: int` — 500
- `font_weight_semibold: int` — 600
- `font_weight_bold: int` — 700

**Dimensions:**
- `input_height: int` — 40px
- `button_height: int` — 42px
- `compact_button_height: int` — 34px
- `navigation_item_height: int` — 44px
- `table_row_height: int` — 44px
- `header_height: int` — 48px
- `sidebar_expanded_width: int` — 240px
- `sidebar_collapsed_width: int` — 56px
- `dialog_minimum_width: int` — 440px

**Radii:**
- `radius_small: int` — 4px
- `radius_medium: int` — 6px
- `radius_large: int` — 8px
- `radius_pill: int` — 9999px

**Animation:**
- `reduced_motion: bool` — disable decorative animations
- `animation_duration_fast_ms: int` — 100ms
- `animation_duration_normal_ms: int` — 200ms

When `reduced_motion` is true:
- Sidebar does not animate its width
- No decorative transitions anywhere
- State changes remain immediate and functional

**Other:**
- `border_width: int` — 1px
- `focus_border_width: int` — 2px
- `icon_small: int` — 14px
- `icon_medium: int` — 18px
- `icon_large: int` — 22px

### 6.2 Validation

DesignTokens constructor validates all fields on instantiation:

- Color values match `^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$` — only
  `#RRGGBB` or `#RRGGBBAA`. No `#RGB`, no incomplete values, no invalid
  hex characters.
- `font_family` is non-empty
- Spacing, dimension, radius, and animation-duration values are `int`
- Spacing and radius values are non-negative (zero is valid)
- Dimension and font-size values are greater than zero
- Font weights are one of: 100, 200, 300, 400, 500, 600, 700, 800, 900
- `reduced_motion` is `bool`
- Animation durations are non-negative integers

### 6.3 Theme Presets

**dark_forensic** (default — required for Phase 1):
- app_background: #020703
- sidebar_background: #051208
- header_background: #040D06
- surface: #0A1A0E
- surface_elevated: #0F2415
- surface_hover: #142E1B
- border: #1A3D22
- border_focus: #00F56A
- primary: #00C853
- primary_hover: #00E676
- primary_pressed: #00A845
- primary_text: #020703        (dark foreground for ~6.2:1 contrast on #00C853)
- text_primary: #EAF7EE
- text_secondary: #9BBAA3
- text_muted: #6E9278
- success: #00E676
- warning: #FFD600
- error: #FF1744
- information: #00B8D4
- disabled_background: #1A2E1F
- disabled_text: #7FA98A        (improved readability on #1A2E1F)
- selection_background: #1A3D22
- font_family: "Segoe UI, Noto Sans, sans-serif"
- reduced_motion: false
- animation_duration_fast_ms: 100
- animation_duration_normal_ms: 200

**high_contrast** (deferred — do NOT implement in Phase 1):
- Pure black background, white text, high-saturation green accent
- 2px borders for clear outlines
- Same DesignTokens schema; can be implemented later
- Do not show in Settings, do not persist, do not require tests until
  implemented and stable

---

## 7. ThemeManager

### 7.1 Lifecycle

1. Create QApplication.
2. Create AppSettings and application services.
3. Create ThemeManager with QApplication and AppSettings dependencies.
4. Call `load_saved_theme()` — reads settings, does NOT apply QSS until
   QApplication exists.
5. Construct MainWindow using the active tokens.
6. Show MainWindow.

If ThemeManager is created before QApplication, `load_saved_theme()`
reads settings and caches the theme name but does NOT call
`setStyleSheet()` until QApplication.instance() is available.

### 7.2 Responsibilities

- Holds the active DesignTokens instance
- Provides `get_tokens()` — returns current DesignTokens
- Provides `apply_theme(name, persist=False) -> bool` — loads preset,
  regenerates QSS, reapplies, optionally persists. Returns True on
  success, False on failure. On failure, keeps the previously active
  theme and does NOT persist the invalid value.
- Provides `set_theme(name) -> bool` — convenience wrapper with
  `persist=True` for explicit user changes. Returns True on success,
  False on failure. Does NOT silently fall back to dark_forensic for
  invalid explicit user selections — caller must handle the False case.
- Provides `load_saved_theme()` — reads `ui.theme` from AppSettings at
  startup. If missing or invalid → uses dark_forensic without persisting.
  If valid → loads and applies the preset. Never writes to settings.
- Generates application-wide QSS via QSS builder sections
- Emits `theme_changed(str)` signal after successful application
- Unrelated settings remain untouched
- Failure to generate or apply QSS falls back to minimal built-in QSS
  (flat fallback with readable default colors)

### 7.3 Safety

- `QApplication.instance()` is verified before `setStyleSheet()` is
  called. If QApplication does not exist yet, QSS application is queued
  or skipped with a logged warning.

### 7.4 QSS Application Order

- Generated token-based QSS becomes the sole application-level stylesheet
  in Phase 1
- Do NOT apply legacy global QSS files afterward
- Existing widget-level inline styles may temporarily remain and override
  global QSS — record those conflicts for later page migration
- Legacy QSS files remain in the repository only as rollback/reference
  assets until removed in a later phase
- Startup code must NOT apply both the old global theme and the generated
  theme in undefined order

### 7.5 QSS Builder Coverage

QssBuilder provides section functions, each returning a QSS string.
ThemeManager combines them into one final stylesheet.

- `build_base_qss(tokens)` — QApplication, QWidget, QMainWindow
- `build_button_qss(tokens)` — QPushButton variants via dynamic properties
- `build_form_qss(tokens)` — QLineEdit, QTextEdit, QPlainTextEdit,
  QComboBox, QSpinBox, QCheckBox, QRadioButton
- `build_table_qss(tokens)` — QTableView, QTableWidget, QHeaderView,
  QAbstractItemView selection states
- `build_navigation_qss(tokens)` — sidebar, header, navigation items
- `build_dialog_qss(tokens)` — QDialog, QMessageBox, QDialogButtonBox
- `build_scrollbar_qss(tokens)` — QScrollBar (vertical and horizontal)
- `build_feedback_qss(tokens)` — QToolTip, QMenu, QProgressBar
- `build_container_qss(tokens)` — QSplitter, QSplitter::handle,
  QScrollArea and viewport, QGroupBox
- `build_misc_qss(tokens)` — QStatusBar, remaining minor widgets

QSS uses dynamic property selectors scoped to custom component classes:

```css
NeonButton[variant="primary"] { ... }
StatusBadge[status="success"] { ... }
StatusBanner[banner_type="verified"] { ... }
NavigationItem[active="true"] { ... }
```

For standard Qt widgets, use class-name selectors or object-name selectors
to avoid accidentally styling unrelated widgets of the same class.

Invalid dynamic-property values are normalized before assignment by
`set_dynamic_property()`:
- Invalid button variant → `"secondary"`
- Invalid badge status → `"neutral"`
- Invalid banner type → `"info"`

### 7.6 Theme Application Sequence

1. Bootstrap creates Container → ThemeManager
2. Container calls `theme_manager.load_saved_theme()` at startup
   - Reads `ui.theme` from AppSettings
   - If missing or invalid → use dark_forensic (do NOT persist)
   - If valid → load and apply the preset
   - Does NOT write to settings
3. User changes theme in Settings → calls `theme_manager.set_theme(name)`
   - Applies and persists to settings
   - Returns False on invalid name; caller shows error to user
   - Does NOT silently reset to default for explicit user selections
4. Settings page theme selector never shows high_contrast in Phase 1

---

## 8. Layout Helpers

Standardized layout configuration using DesignTokens. Every helper
accepts an explicit `tokens: DesignTokens` parameter — no global mutable
state is imported.

```python
def apply_page_layout(
    layout: QLayout,
    tokens: DesignTokens,
) -> None:
    layout.setContentsMargins(
        tokens.space_20, tokens.space_20,
        tokens.space_20, tokens.space_20,
    )
    layout.setSpacing(tokens.space_16)


def apply_card_layout(
    layout: QLayout,
    tokens: DesignTokens,
) -> None:
    layout.setContentsMargins(
        tokens.space_16, tokens.space_16,
        tokens.space_16, tokens.space_16,
    )
    layout.setSpacing(tokens.space_12)


def apply_form_layout(
    layout: QFormLayout,
    tokens: DesignTokens,
) -> None:
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(tokens.space_10)
    layout.setVerticalSpacing(tokens.space_10)


def apply_toolbar_layout(
    layout: QHBoxLayout,
    tokens: DesignTokens,
) -> None:
    layout.setContentsMargins(
        tokens.space_16, tokens.space_8,
        tokens.space_16, tokens.space_8,
    )
    layout.setSpacing(tokens.space_8)
```

Components receive tokens from their context or from the injected
ThemeManager.

---

## 9. Style Helper

```python
def refresh_style(widget: QWidget) -> None:
    """Unpolish and repolish a widget after dynamic property changes."""
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
    """Set a dynamic property and refresh widget style.

    If *value* is not in *allowed_values*, *default_value* is substituted.
    Returns the actual value assigned.

    If the property is already set to *value*, the widget is NOT
    repolished (avoids unnecessary style passes).
    """
    if allowed_values is not None and value not in allowed_values:
        value = default_value

    if widget.property(name) == value:
        return value

    widget.setProperty(name, value)
    refresh_style(widget)
    return value
```

Usage:

```python
set_dynamic_property(
    button, "variant", variant,
    allowed_values={"primary", "secondary", "danger", "ghost"},
    default_value="secondary",
)

set_dynamic_property(
    badge, "status", status,
    allowed_values={"success", "warning", "error", "information", "neutral"},
    default_value="neutral",
)

set_dynamic_property(
    banner, "banner_type", banner_type,
    allowed_values={"verified", "warning", "hash_mismatch", "unsupported", "info"},
    default_value="info",
)
```

---

## 10. Main Window Layout

The status bar uses QMainWindow.setStatusBar() (native QStatusBar), NOT
a custom widget in the root QVBoxLayout.

```
QMainWindow
├── centralWidget
│   └── rootLayout (QVBoxLayout, margins=0, spacing=0)
│       ├── AppHeader (min 48px, via sizeHint/QSizePolicy)
│       │   ├── [logo icon, clickable → HOME]
│       │   ├── "WhatsApp Forensicator" — 22px semibold
│       │   ├── version label — 12px muted
│       │   ├── (stretch)
│       │   ├── [case status badge]
│       │   └── [case name, elided with tooltip]
│       └── contentLayout (QHBoxLayout, margins=0, spacing=0)
│           ├── NavigationSidebar (expanded=240, collapsed=56)
│           └── QStackedWidget (stretch=1) — all 18 page widgets
└── StatusBar (QStatusBar, min 26px, via setStatusBar)
```

### 10.1 AppHeader

Components left-to-right:
- Logo icon (packaged SVG/PNG resource — NOT an emoji character).
  Clicking the logo navigates to PageId.HOME. Tooltip: "Go to home".
- "WhatsApp Forensicator" — 22px semibold, primary text
- Version label — 12px muted
- (stretch)
- Active case badge (StatusBadge with case status)
- Case name label (elided with tooltip on overflow)

Icon source: existing project assets. If no icon resource exists, use a
styled text fallback (e.g. "WF" in a coloured square). Do NOT add an
external icon dependency unless existing assets are verified as
insufficient.

### 10.2 NavigationSidebar

**CASE MANAGEMENT**
| PageId | Sidebar Label | Icon |
|--------|---------------|------|
| DASHBOARD | Dashboard | _(audit existing assets)_ |
| CASES | Cases | _(audit existing assets)_ |
| EVIDENCE | Evidence | _(audit existing assets)_ |

**ACQUISITION**
| PageId | Sidebar Label | Icon |
|--------|---------------|------|
| ADB_EXTRACTOR | ADB Extractor | _(audit existing assets)_ |

**ANALYSIS**
| PageId | Sidebar Label | Icon |
|--------|---------------|------|
| CHATS | Chat Viewer | _(audit existing assets)_ |
| CONTACTS | Contacts | _(audit existing assets)_ |
| GROUPS | Groups | _(audit existing assets)_ |
| CALLS | Calls | _(audit existing assets)_ |
| MEDIA | Media | _(audit existing assets)_ |
| TIMELINE | Timeline | _(audit existing assets)_ |
| RECOVERED | Recovered Data | _(audit existing assets)_ |
| VOIP | VoIP Analysis | _(audit existing assets)_ |

**TOOLS**
| PageId | Sidebar Label | Icon |
|--------|---------------|------|
| DECRYPTOR | Decryptor | _(audit existing assets)_ |
| SEARCH | Search | _(audit existing assets)_ |
| REPORTS | Reports | _(audit existing assets)_ |

**SYSTEM**
| PageId | Sidebar Label | Icon |
|--------|---------------|------|
| AUDIT | Audit Log | _(audit existing assets)_ |
| SETTINGS | Settings | _(audit existing assets)_ |

Item height: 44px (tokens.navigation_item_height). Selected item: primary
background + left border accent. Collapsed: 56px wide, icons only,
tooltips on hover/selection. Group headings in sentence case, visually
secondary to items. Scrollable when height is limited.

Icons must have a safe fallback (styled text label) when a resource fails
to load. Every icon must be readable in normal, hover, selected, focused,
and disabled states. Consistent icon size (tokens.icon_medium = 18px).
Do NOT use emoji glyphs as production icons.

### 10.3 HomePage Navigation Behavior

- HomePage is the startup landing page (first widget in QStackedWidget)
- HomePage is NOT represented in the sidebar
- When HomePage is visible, no sidebar item is shown as selected
- The application logo/title in AppHeader navigates to PageId.HOME
  (tooltip: "Go to home")
- `navigate_to(PageId.HOME)` remains supported
- Leaving and returning to HomePage preserves normal case and page state
- No duplicate Home sidebar item

### 10.4 StatusBar

- Preserved as native QStatusBar (via `QMainWindow.setStatusBar()`)
- Left: general application status text
- Right: "Local mode" (instead of "OFFLINE"), version label, UTC indicator
- Lower-priority items are hidden (not removed) when available width is
  narrow
- Preserves existing status-update API: `QStatusBar.showMessage()` and
  any custom `addPermanentWidget()` calls
- Minimum height 26px

### 10.5 Page ID Mapping

MainWindow or NavigationController maintains a `dict[PageId, QWidget]`
whose values are registered as children of QStackedWidget. Navigation
signals carry `PageId` values. A reverse `dict[QWidget, PageId]` is
defined only if required by signal handlers.

---

## 11. Shared Components

### 11.1 NeonButton

- Extends QPushButton
- Dynamic property `variant`: primary, secondary, danger, ghost
- Invalid variant → secondary
- Token-based height (tokens.button_height)
- Supports icons without clipping text
- Consistent focus, hover, pressed, disabled states via QSS
- Danger variant does NOT auto-execute actions
- Ghost buttons remain visible against dark surfaces
- Constructor: `__init__(self, text: str = "", variant: str = "primary", parent=None)`
  - `variant` replaces old `style` parameter
  - `set_style(style)` kept as deprecated alias → translates old values:
    - "destructive" → "danger"
    - "warning" → "secondary"
    - "primary" → "primary" (unchanged)
    - "secondary" → "secondary" (unchanged)
  - New method: `set_variant(variant)` for the new API

### 11.2 StatusBadge

- Extends QLabel
- Dynamic property `status`: success, warning, error, information, neutral
- Invalid status → neutral
- Pill-style radius (tokens.radius_pill)
- Auto-sizing according to text
- Uses text + icon, not colour alone
- Icon uses packaged resources or styled text — NOT emoji glyphs
- Constructor: `__init__(self, text: str = "", status: str = "neutral", parent=None)`
  - `status` replaces old `badge_type` parameter
  - `set_badge_type(badge_type)` kept as deprecated alias → maps old
    values to new status equivalents:
    - "verified", "parsed" → "success"
    - "partial", "manual", "unverified" → "warning"
    - "failed" → "error"
    - "inferred", "unsupported", "relay", "probable_peer", "vpn_proxy" → "neutral"
  - New method: `set_status(status)` for the new API

### 11.3 StatusBanner (was EvidenceBanner)

- Extends QFrame
- Dynamic property `banner_type`: verified, warning, hash_mismatch,
  unsupported, info
- Invalid banner_type → info
- Supports: text string, banner type, optional action button
- Dismissible or persistent modes
- Multiline text via word-wrap
- Accessible status description
- Constructor: `__init__(self, text: str = "", banner_type: str = "info", parent=None)`
  - Identical signature to EvidenceBanner
  - `set_text(text)` and `set_banner_type(banner_type)` preserved
  - No signals; a simple rename with no translation needed

### 11.4 PageHeader

- QWidget with QHBoxLayout
- Title label (tokens.font_size_page_title, semibold)
- Optional subtitle label (tokens.font_size_body, text_secondary)
- Stretch after header content
- Constructor: `__init__(self, title: str, subtitle: str = "", parent=None)`
  - Identical to existing API
- Token-based typography, no hardcoded colors

### 11.5 ContentCard

- Extends QFrame
- Creates an internal QVBoxLayout (`_content_layout`) and applies
  token-based padding via `_content_layout.setContentsMargins()` (QSS
  padding on a QFrame does NOT reliably configure child layout margins)
- Supports optional sections:
  - Header area (layout only created when used)
  - Title label (tokens.font_size_section, semibold)
  - Subtitle label (optional, tokens.font_size_body, text_secondary)
  - Header actions (QHBoxLayout, right-aligned)
  - Content area (stretch)
  - Footer area (layout only created when used)
- Empty header/footer containers are NOT created when unused
- Token-based border and radius
- Expanding size policy where appropriate
- Does NOT contain page-specific data loading, filtering, or permission
  logic

### 11.6 EmptyState

- QWidget with centered QVBoxLayout
- Icon preference: packaged SVG/PNG. Fallback: styled text label.
  Do NOT use emoji glyphs as production icons. Fallback must have an
  accessible name.
- Title label (tokens.font_size_section, semibold)
- Optional description label (tokens.font_size_body, text_secondary)
- Token-based spacing
- Optional action button (NeonButton with page-specific action)
- Constructor: `__init__(self, title: str = "No data available", description: str = "", parent=None)`
  - Identical to existing API

### 11.7 ConfirmDialog

- Extends QDialog
- Standard and destructive confirmation modes
- Custom title, message, optional details text
- Custom confirm and cancel button labels
- Returns `QDialog.DialogCode.Accepted` or `QDialog.DialogCode.Rejected`
- `exec()` returns the corresponding dialog result code
- The dialog NEVER performs the destructive operation itself — it only
  returns the user's decision
- For destructive mode:
  - Cancel receives initial focus
  - Cancel is the default button
  - Destructive confirm uses `setDefault(False)` and
    `setAutoDefault(False)` where required
- Escape and window close both reject the dialog

---

## 12. Component Compatibility Strategy

### 12.1 EvidenceBanner → StatusBanner

EvidenceBanner and StatusBanner share an identical constructor:
`(text="", banner_type="info", parent=None)` and identical methods
`set_text(text)`, `set_banner_type(banner_type)`. A simple alias
(`EvidenceBanner = StatusBanner`) is sufficient. EvidenceBanner can be
a subclass that delegates entirely to StatusBanner for clarity.

### 12.2 NeonButton (refactored)

Constructor parameter `style` is renamed to `variant`. Old callers pass
`style` as a keyword arg; the constructor accepts both and maps:
- `style="destructive"` → `variant="danger"`
- `style="warning"` → `variant="secondary"`
- `style="primary"` → `variant="primary"`
- `style="secondary"` → `variant="secondary"`

`set_style(style)` is kept as deprecated, applying the same translation.
New method `set_variant(variant)` uses dynamic property directly.

### 12.3 StatusBadge (refactored)

Constructor parameter `badge_type` is renamed to `status`. Old callers
pass `badge_type`; the constructor accepts both and maps old values:
- `badge_type="verified"`, `badge_type="parsed"` → `status="success"`
- `badge_type="partial"`, `badge_type="manual"`,
  `badge_type="unverified"` → `status="warning"`
- `badge_type="failed"` → `status="error"`
- Other old values → `status="neutral"`

`set_badge_type(badge_type)` is kept as deprecated with the same mapping.
New method `set_status(status)` uses dynamic property directly.

### 12.4 PageHeader (refactored)

Constructor and API unchanged. Internal styling updated to use
DesignTokens.

### 12.5 EmptyState (refactored)

Constructor and API unchanged. Internal styling updated to use
DesignTokens. Icon uses non-emoji fallback.

### Summary Table

| Old Name | New Name | Compatibility |
|----------|----------|---------------|
| EvidenceBanner | StatusBanner | Alias; identical constructor and methods |
| NeonButton | NeonButton | Same class; `style`→`variant` rename with translation |
| StatusBadge | StatusBadge | Same class; `badge_type`→`status` rename with translation |
| PageHeader | PageHeader | Unchanged API; token-aware internals |
| EmptyState | EmptyState | Unchanged API; token-aware internals; non-emoji icon |

All existing imports continue to work without changes.

---

## 13. Settings Integration

Theme selection stored in AppSettings under key `ui.theme`.
Default: `"dark_forensic"`. Invalid saved value → fall back to
`"dark_forensic"` without overwriting the setting.
Sidebar state stored under key `ui.sidebar_expanded` (boolean).
Default: `True`. Saved only on explicit collapse/expand toggle.
Unrelated settings are never touched.

---

## 14. Accessibility

- Keyboard navigation through sidebar items (Up/Down arrows, Enter to
  select, logical tab order)
- Visible focus rings (2px tokens.focus_border_width)
- Tooltips on all collapsed sidebar items
- Accessible names on navigation buttons and header logo
- StatusBadge uses icon + text, not colour alone
- All icon components (AppHeader, sidebar, EmptyState, StatusBadge,
  StatusBanner) apply the same icon policy: packaged asset or styled
  text fallback, no emoji, accessible name required
- Target WCAG AA contrast — verify the final rendered theme during
  implementation (see Section 15)
- Minimum clickable height 40px
- Tab order follows visual layout left-to-right, top-to-bottom

---

## 15. Contrast Verification (Implementation Deliverable)

Phase 1 completion report must include these measured pairs:

- `text_primary` on `surface`
- `text_secondary` on `surface`
- `text_muted` on `surface`
- `primary_text` on `primary`
- `text_primary` on `sidebar_background`
- `text_primary` on `header_background`
- `success` / `warning` / `error` / `information` on `surface`
- `disabled_text` on `disabled_background`

Each pair reports:
- Foreground hex, background hex
- Calculated contrast ratio
- WCAG AA pass/fail at normal text, large text, and UI components
- Any adjustment made

Plus a qualitative check: confirm that every StatusBadge and
StatusBanner is readable without colour information.

---

## 16. QSS Selector Reference

```css
/* Buttons — scoped to NeonButton class */
NeonButton[variant="primary"] { background: ... }
NeonButton[variant="secondary"] { border: 1px solid ... }
NeonButton[variant="danger"] { background: ... }
NeonButton[variant="ghost"] { background: transparent; ... }

/* Badges — scoped to StatusBadge class */
StatusBadge[status="success"] { color: ... }
StatusBadge[status="warning"] { color: ... }
StatusBadge[status="error"] { color: ... }
StatusBadge[status="information"] { color: ... }
StatusBadge[status="neutral"] { color: ... }

/* Banners — scoped to StatusBanner class */
StatusBanner[banner_type="verified"] { border-left: 4px solid ... }
StatusBanner[banner_type="warning"] { border-left: 4px solid ... }
StatusBanner[banner_type="hash_mismatch"] { border-left: 4px solid ... }
StatusBanner[banner_type="unsupported"] { border-left: 4px solid ... }
StatusBanner[banner_type="info"] { border-left: 4px solid ... }

/* Navigation — scoped to NavigationItem class */
NavigationItem[active="true"] { background: ... }
```

---

## 17. Implementation Order

1. Audit current theme, stylesheets, imports, shared components, icon
   resources, and all legacy tab-bar dependencies (see Section 27)
2. Create PageId enum (`src/wft/ui/pages/page_id.py`)
3. Create DesignTokens + theme presets (dark_forensic only)
4. Create QSS builder + ThemeManager
5. Create layout helpers + style helpers
6. Apply theme at startup (bootstrap integration)
7. Build the PageId-to-page-widget mapping in MainWindow
8. Build the sidebar (NavigationSidebar + NavigationItem)
9. Connect sidebar navigation while retaining the old tab bar
   temporarily (parallel navigation path)
10. Migrate `navigate_to()`, shortcuts, KPI links, HomePage links, and
    internal page links to use PageId
11. Verify navigation parity for all 17 sidebar pages and HomePage
12. Remove the horizontal tab bar
13. Search again for stale tab/index references
14. Remove global KPI strip (preserve KPI data providers)
15. Refactor shared components (NeonButton, StatusBadge, StatusBanner,
    PageHeader, EmptyState, ContentCard, ConfirmDialog)
16. Create compatibility adapters (evidence_banner.py, NeonButton
    deprecated methods, StatusBadge deprecated methods)
17. Build AppHeader component
18. Refactor MainWindow shell (app header, page area, status bar)
19. Add sidebar state persistence
20. Run full test suite
21. Manual responsive/scaling/contrast tests
22. Deliver Phase 1 completion report

---

## 18. Testing

### Unit Tests

- DesignTokens immutability, required fields, value validation
  (including bool, exact hex regex, non-empty font_family, positive
  dimensions, non-negative spacing/radii, valid font weights)
- Theme presets: dark_forensic loads correctly
- Invalid theme name: falls back to dark_forensic
- Startup theme load: does NOT persist fallback
- QSS generation: contains expected selectors, no unresolved
  placeholder tokens
- ThemeManager: apply_theme() applies QSS, emits theme_changed, returns
  bool; invalid explicit name returns False without changing theme
- QApplication safety: graceful skip if no QApplication.instance()
- Layout helpers: margins and spacing match tokens
- Style helper: refresh_style() and set_dynamic_property()
- set_dynamic_property: normalization, returned-value matches assigned,
  unchanged property does NOT repolish (verify via mock or spy)
- NeonButton: all valid variants, invalid fallback, set_style()→set_variant()
  translation, deprecated set_style("destructive") maps to "danger"
- StatusBadge: all valid statuses, invalid fallback,
  set_badge_type()→set_status() mapping, deprecated set_badge_type("verified")
  maps to "success"
- StatusBanner: all valid banner types, invalid fallback
- ConfirmDialog: accept, reject, destructive mode focus behavior
- ContentCard: optional sections not created when unused
- Sidebar: expanded state, collapsed state, tooltip availability
- Sidebar: active item updates
- Sidebar: state persistence round-trip
- PageId: valid members match _page_map keys, invalid raises ValueError
- PageId: str(PageId.DASHBOARD) == "dashboard"
- EvidenceBanner compatibility alias: same constructor, set_text,
  set_banner_type all work identically
- AppHeader: logo click emits/triggers HOME navigation
- All 17 nav-accessible pages are reachable via PageId mapping
- HomePage shown at startup, sidebar active state cleared on HOME

### Manual Tests

- All 17 pages accessible from sidebar navigation
- HomePage accessible via logo click
- Sidebar collapse/expand with state persistence
- Header case badge updates when case is opened/closed
- Status bar shows correct information at all widths
- No widget overlap at 1366×768, 1600×900, 1920×1080
- No clipping at 100%, 125%, 150% scaling
- Keyboard navigation through sidebar (arrows + enter)
- Window maximize/restore
- Existing page signals, workers, data loading unchanged
- Old tab bar completely removed with no stale references
- All shortcuts still work (Ctrl+N, Ctrl+I, Ctrl+F, Ctrl+R, Ctrl+L)

---

## 19. Remaining Legacy After Phase 1

- Individual page contents: all 18 pages retain their current internal
  layouts and inline stylesheets (to be redesigned in Phases 2–6)
- Global KPI strip: removed; KPI data providers (statistics_service) and
  the `_on_kpi_click()` mapping preserved for Dashboard redesign
- Old `themes/dark_neon.qss` and `themes/high_contrast.qss`: preserved
  as rollback/reference assets, NOT applied at startup
- Inline stylesheets in page files: remain until that page is redesigned
  in a later phase; any conflicts with global QSS are recorded
- ParseEvidenceWorker/BatchImportWorker: remain synchronous
- Reduced_glow QSS file: still missing (not part of this phase)
- high_contrast theme: not implemented, not shown in Settings
- DataTable component: deferred

---

## 20. Design Decisions

1. **Sidebar over tabs**: 17 items in a horizontal bar is too many.
   A collapsible sidebar follows forensic-tool conventions (FTK, EnCase).

2. **DesignTokens over scattered constants**: Single source of truth for
   all visual values. Testable, changeable, consistent.

3. **Generated QSS over static files**: Tokens are the source; QSS is
   derived. No need to keep .qss files in sync with code.

4. **Dynamic properties over subclasses**: QSS property selectors are
   cleaner than creating QPushButtonPrimary, QPushButtonDanger, etc.

5. **Phase approach over big-bang**: Each phase delivers a working,
   testable increment. Pages remain functional throughout.

6. **Compatibility adapters over silent breakage**: Deprecated APIs
   translate old values to new equivalents; no existing caller breaks
   until the page is explicitly redesigned.

7. **Native QStatusBar over custom widget**: Qt's built-in status bar
   handles resize, hiding, and styling; custom widget duplicates this
   work.

8. **PageId StrEnum over string constants**: Type-safe, self-documenting,
   no scattered string literals in new code.

9. **Parallel navigation during migration**: New sidebar connected
   before old tab bar is removed; no navigation downtime.

---

## 21. Files to Create

- `src/wft/ui/theme/__init__.py`
- `src/wft/ui/theme/tokens.py`
- `src/wft/ui/theme/themes.py`
- `src/wft/ui/theme/theme_manager.py`
- `src/wft/ui/theme/qss_builder.py`
- `src/wft/ui/theme/layout_helpers.py`
- `src/wft/ui/theme/style_helpers.py`
- `src/wft/ui/pages/page_id.py`
- `src/wft/ui/components/app_header.py`
- `src/wft/ui/components/navigation_sidebar.py`
- `src/wft/ui/components/navigation_item.py`
- `src/wft/ui/components/content_card.py`
- `src/wft/ui/components/status_banner.py`
- `src/wft/ui/components/confirm_dialog.py`

## 22. Files to Modify

- `src/wft/ui/components/neon_button.py` — refactor to use DesignTokens,
  dynamic variant property, deprecated `set_style()` translation
- `src/wft/ui/components/status_badge.py` — refactor to use DesignTokens,
  dynamic status property, deprecated `set_badge_type()` translation
- `src/wft/ui/components/page_header.py` — refactor to use DesignTokens
- `src/wft/ui/components/empty_state.py` — refactor to use DesignTokens,
  replace emoji icon with packaged asset or styled text fallback
- `src/wft/ui/components/evidence_banner.py` — convert to compatibility
  adapter wrapping StatusBanner (identical constructor + method delegation)
- `src/wft/ui/components/__init__.py` — update exports
- `src/wft/ui/main_window.py` — refactor shell layout: add sidebar,
  app header, page area, status bar; remove tab bar and KPI strip
- `src/wft/bootstrap.py` — add ThemeManager creation and startup theme
  loading
- `src/wft/infrastructure/settings/settings.py` — add theme and sidebar
  state settings keys

---

## 23. PageId File

`src/wft/ui/pages/page_id.py`:

```python
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

---

## 24. Icon Resource Audit (Implementation Task)

Before implementing the sidebar, audit the existing project assets:

- Search `src/wft/ui/resources/` for SVG, PNG, ICO files
- Search the codebase for any existing icon provider or icon lookup
- If no icons exist, provide a clear recommendation:
  - Use simple styled text labels as a fallback (e.g. first letter of
    page name in a styled QLabel)
  - Or add a lightweight set of monochromatic SVG icons (recommended
    10–15 icons for sidebar groups + items)
- Do NOT add external icon libraries without explicit justification

Each sidebar entry must have:
- A valid icon resource or styled text fallback (NOT emoji)
- Consistent icon size (tokens.icon_medium = 18px)
- A tooltip in collapsed mode
- A readable selected, hover, focused, and disabled state
- An accessible name when the label is not visible

---

## 25. Contrast Verification Checklist

Phase 1 completion report must include these measured pairs:

- `text_primary` on `surface`
- `text_secondary` on `surface`
- `text_muted` on `surface`
- `primary_text` on `primary`
- `text_primary` on `sidebar_background`
- `text_primary` on `header_background`
- `success` / `warning` / `error` / `information` on `surface`
- `disabled_text` on `disabled_background`

Each pair reports:
- Foreground hex, background hex
- Calculated contrast ratio
- WCAG AA pass/fail at normal text, large text, and UI components
- Any adjustment made

Plus a qualitative check: confirm that every StatusBadge and
StatusBanner is readable without colour information.

---

## 26. ProgressOverlay Token Migration

`progress_overlay.py` receives a limited token update in Phase 1.
Unique existing size constraints (minimumWidth, maximumWidth,
minimumHeight) are preserved as-is. Only these values are migrated:

- Colours → generated QSS selectors where possible
- Spacing → `apply_card_layout(tokens)`
- Button heights → `tokens.button_height`
- Typography → token-based font sizes
- Border and radius → token-based values

---

## 27. Legacy Navigation Migration Audit

Before removing the horizontal tab widget (`_nav_tabs`), search the
entire repository for and document all uses of:

- `_nav_tabs` (attribute references)
- `_nav_tabs.currentChanged` (signal connection)
- `_nav_tabs.setCurrentIndex()` (programmatic tab switching)
- `_nav_map` (index-to-key mapping)
- `_on_nav_changed(index)` (handler depends on numeric index)
- `_nav_items` (list index assumed by `navigate_to()`)
- Raw page-index numbers (0–16) in the tab context
- Any import or reference to QTabBar from the navigation

Migration (performed in this order, same as Section 17):

1. Create PageId.
2. Build the PageId-to-page-widget mapping.
3. Build the sidebar.
4. Connect sidebar navigation while retaining the old tab bar
   temporarily (parallel path — both navigation methods active).
5. Migrate `navigate_to()`, shortcuts, KPI links, HomePage links, and
   internal page links to use PageId.
6. Verify navigation parity for all 17 sidebar pages and HomePage.
7. Remove the horizontal tab bar.
8. Search again for stale tab/index references.
9. Run navigation and full regression tests.

All callers of `navigate_to()` use string keys (not indices), so the
migration is primarily within `main_window.py`.

---

## 28. Deferred Components

The following components were discussed during design but are explicitly
deferred from Phase 1:

| Component | Reason | Planned Phase |
|-----------|--------|---------------|
| DataTable | No table-heavy pages are redesigned in Phase 1 | Phase 2+ |
| High-contrast theme | Requires separate testing and contrast verification | Phase 5+ |
| ToastNotification | Not required until page redesigns introduce async operations | Phase 2+ |
| DetailPanel | Not required for shell | Phase 2+ |
| FilePicker | Not required for shell | Phase 2+ |

---

## 29. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Global QSS conflicts with page-specific inline styles | Record conflicting pages in completion report; remove legacy QSS per-page in later phases |
| Sidebar navigation breaks existing page signal chain | Preserve all 18 page instances in QStackedWidget; route through existing page keys via PageId mapping |
| ThemeManager at startup crashes on bad settings | Try/except with fallback to dark_forensic; fallback does NOT persist |
| QSS generation fails | ThemeManager provides a minimal built-in flat QSS fallback |
| KPI removal breaks something unexpected | Audit all references to KPI widget objects and `_kpi_cards` before removal |
| EvidenceBanner rename breaks imports | Compatibility adapter in evidence_banner.py; grep for all references before deleting old file |
| High-contrast theme causes instability | Not implemented in Phase 1; deferred |
| Missing icon resources | Styled text fallback (initials in a coloured square) for every sidebar item |
| Tab-bar removal breaks existing tests | Migrate all test references from tab indexing to PageId navigation; keep parallel path during migration |
| Deprecated `style`/`badge_type` usage not caught | All 59 instantiation sites audited in design phase; adapter handles translation |
