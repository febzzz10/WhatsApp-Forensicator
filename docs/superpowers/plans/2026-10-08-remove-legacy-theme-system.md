# Remove Legacy Theme System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the dead legacy theme system (`wft.ui.themes` — old `ColorTokens`/`ThemeManager`/static QSS files) so `wft.ui.theme` (token-built `DesignTokens`/`ThemeManager`/`qss_builder.py`) is the single theme implementation.

**Architecture:** Two complete theme systems coexist. At runtime, `main.py:49` applies the old system's `dark_neon.qss`, then `bootstrap.py:52` (`Container.__init__`) calls the new `ThemeManager.load_saved_theme()`, whose generated QSS immediately overwrites it. The old system is dead code: unreachable (no theme picker in Settings), unread (only an unused `MainWindow._theme_manager` field), and drifting (`ColorTokens` vs `DesignTokens`). Removal preserves current runtime behavior exactly — the new system is already what styles the app.

**Tech Stack:** Python 3.14, PySide6 6.x, pytest + pytest-qt, ruff/black (line length 100)

**Spec:** Derived from architecture-scan of `src/wft/` (2026-10-08). Related design docs: `docs/superpowers/specs/2026-07-21-phase1-ui-redesign.md` (Phase 1 UI redesign — its "PRESERVE legacy .qss for rollback" note is superseded; see Deviations below)

## Global Constraints

- Test command: `python -m pytest tests/ -v --tb=short` (run from repo root)
- Line length: 100 chars; ruff + black configured in `pyproject.toml`
- Baseline before starting: **418 tests, 0 failures** — any step that drops this count unexpectedly is a regression
- Snapshot datetime format stays untouched: `datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")` (that is bottleneck #2, OUT OF SCOPE for this plan)
- Do NOT touch: evidence/parse/audit code paths, `wft.ui.theme.*` (the surviving system), any page other than where imports force it
- Per repo `AGENTS.md`: NO commits unless the user explicitly asks. Commit commands are documented per-task but are executed only with user approval.
- Nothing depends on reduced motion or high-contrast from the old system: `DesignTokens.reduced_motion` (in `wft/ui/theme/tokens.py:73`) already serves `navigation_sidebar.py:185`, and `high_contrast` is spec-deferred (`specs/2026-07-21-phase1-ui-redesign.md:419`, "Settings page theme selector never shows high_contrast in Phase 1")

## File Structure

| File | Responsibility after this plan |
|------|-------------------------------|
| `src/wft/ui/theme/tokens.py` | (survives) `DesignTokens` — single token source |
| `src/wft/ui/theme/qss_builder.py` | (survives) generates all QSS from tokens |
| `src/wft/ui/theme/theme_manager.py` | (survives) only `ThemeManager` in the codebase |
| `src/wft/ui/__init__.py` | re-exports the NEW `ThemeManager`/`DesignTokens` |
| `src/wft/main.py` | no legacy theme code; `Container` owns theme application |
| `src/wft/ui/main_window.py` | no `ThemeManager` import, no unused `set_theme_manager` |
| `tests/unit/test_ui_components.py` | component/nav tests only (9 legacy-theme tests removed) |
| `tests/unit/test_theme_manager.py` | new-system tests **plus** new wiring test from Task 2 |
| `src/wft/ui/themes/` | **DELETED** (2 .py + 3 .qss) |
| `AGENTS.md` | architecture docs updated to match reality |

## Deviations from Prior Specs (deliberate, for reviewer attention)

1. `specs/2026-07-21-phase1-ui-redesign.md:100` marked `themes/` "PRESERVE (legacy QSS files, rollback/reference only)". This plan deletes them: git history (`b7d2128`) serves rollback, and keeping derived QSS in-tree invites drift from `qss_builder.py`.
2. The plan removes the `high_contrast` capability that `AGENTS.md:22` advertises as a feature. It is unreachable at runtime today, so this is a docs correction, not a feature removal. Follow-up: implement `high_contrast` as a real `DesignTokens` preset + registry entry when desired.

---

### Task 1: Purge legacy-theme tests from the component test file

**Files:**
- Modify: `tests/unit/test_ui_components.py` — delete imports at lines 9-10, and classes `TestColorTokens` (23-41), `TestThemeManager` (44-65), `TestThemeQSS` (219-231)
- Test: `tests/unit/test_ui_components.py` (remaining 22 tests)

**Interfaces:**
- Consumes: nothing (pure deletion)
- Produces: nothing — unlocks Tasks 2-4 by removing test locks on dead code

- [ ] **Step 1: Verify which tests currently exist and pass before touching anything**

Run: `python -m pytest tests/unit/test_ui_components.py -v --tb=short | Select-Object -Last 3`
Expected: 31 passed (the file's current count)

- [ ] **Step 2: Delete the legacy imports**

Remove lines 9-10:
```python
from wft.ui.themes.tokens import ColorTokens
from wft.ui.themes.theme_manager import ThemeManager
```

- [ ] **Step 3: Delete the three legacy-theme test classes**

Delete `class TestColorTokens:` (through its last method, line 41), `class TestThemeManager:` (through line 65), and `class TestThemeQSS:` (through end of file, line 231). Keep every other class untouched. The classes to remove are exactly those whose tests reference `ColorTokens`, `ThemeManager(`, or paths under `src/wft/ui/themes/`.

- [ ] **Step 4: Run the file — must pass with 22 tests**

Run: `python -m pytest tests/unit/test_ui_components.py -v --tb=short | Select-Object -Last 3`
Expected: 22 passed

- [ ] **Step 5: Document commit for user approval**

```bash
git add tests/unit/test_ui_components.py
git commit -m "test: remove legacy theme system tests from component suite"
```
(Do not execute without explicit user approval — repo AGENTS.md rule.)

---

### Task 2: Rewire the `wft.ui` package exports to the surviving theme system

**Files:**
- Modify: `src/wft/ui/__init__.py` — swap both imports/exports from `wft.ui.themes` to `wft.ui.theme`
- Test: `tests/unit/test_theme_manager.py` — append one wiring test class

**Interfaces:**
- Consumes: `wft.ui.theme.theme_manager.ThemeManager`, `wft.ui.theme.tokens.DesignTokens` (both exist and are unchanged)
- Produces: `from wft.ui import ThemeManager` resolves to the NEW class; `from wft.ui import DesignTokens` becomes the public token export (replaces `ColorTokens`)

- [ ] **Step 1: Write the failing wiring test**

Append to `tests/unit/test_theme_manager.py`:

```python
class TestUIPackageThemeWiring:
    def test_ui_package_exports_new_theme_system(self):
        from wft.ui import ThemeManager as ExportedTM
        from wft.ui import DesignTokens
        from wft.ui.theme.theme_manager import ThemeManager as SourceTM
        from wft.ui.theme.tokens import DesignTokens as SourceDT

        assert ExportedTM is SourceTM
        assert DesignTokens is SourceDT
```

- [ ] **Step 2: Run it and watch it FAIL**

Run: `python -m pytest tests/unit/test_theme_manager.py::TestUIPackageThemeWiring -v --tb=short`
Expected: FAIL — `ImportError`/`ImportError: cannot import name 'DesignTokens' from 'wft.ui'` (package still exports the legacy `ColorTokens`)

- [ ] **Step 3: Rewire the exports**

`src/wft/ui/__init__.py` becomes:

```python
from wft.ui.theme.theme_manager import ThemeManager
from wft.ui.theme.tokens import DesignTokens

from wft.ui.components import (
    NeonButton,
    StatusBadge,
    StatisticCard,
    PageHeader,
    EvidenceBanner,
    ProgressOverlay,
    EmptyState,
    ErrorPanel,
)

from wft.ui.workers import BackgroundWorker, CancellationToken

__all__ = [
    "ThemeManager",
    "DesignTokens",
    "NeonButton",
    "StatusBadge",
    "StatisticCard",
    "PageHeader",
    "EvidenceBanner",
    "ProgressOverlay",
    "EmptyState",
    "ErrorPanel",
    "BackgroundWorker",
    "CancellationToken",
]
```

- [ ] **Step 4: Run the new test file — all must pass**

Run: `python -m pytest tests/unit/test_theme_manager.py -v --tb=short | Select-Object -Last 3`
Expected: 8 passed (7 existing + 1 new)

- [ ] **Step 5: Document commit for user approval**

```bash
git add src/wft/ui/__init__.py tests/unit/test_theme_manager.py
git commit -m "refactor(ui): export new ThemeManager/DesignTokens from wft.ui package"
```
(Do not execute without explicit user approval.)

---

### Task 3: Remove legacy theme wiring from `main.py` and `main_window.py`

**Files:**
- Modify: `src/wft/main.py` — delete import (line 8), instantiation (lines 48-49), `set_theme_manager` call (line 59)
- Modify: `src/wft/ui/main_window.py` — delete import (line 14), field (line 46), `set_theme_manager` method (lines 270-271)
- Test: full suite (no new test; behavior verified by app construction tests in `test_ui_components.py::TestDashboardNavigation`, which build `MainWindow(container)` and exercise the double-styling path end-to-end)

**Interfaces:**
- Consumes: `Container.theme_manager` (new-system instance, applied via `load_saved_theme()` in `bootstrap.py:51-52`) — already runs before `MainWindow(container)` is constructed at `main.py:58`, so styling is preserved with zero ordering change
- Produces: nothing new; removes the only remaining runtime references to `wft.ui.themes`

- [ ] **Step 1: Edit `src/wft/main.py`**

Delete line 8 (`from wft.ui.themes.theme_manager import ThemeManager`), delete lines 48-49:
```python
    theme_manager = ThemeManager(app)
    theme_manager.set_theme("dark_neon")
```
and delete line 59 (`window.set_theme_manager(theme_manager)`).

- [ ] **Step 2: Edit `src/wft/ui/main_window.py`**

Delete line 14 (`from wft.ui.themes.theme_manager import ThemeManager`). Delete line 46 (`self._theme_manager: Optional[ThemeManager] = None`). Delete the method at lines 270-271:
```python
    def set_theme_manager(self, tm: ThemeManager) -> None:
        self._theme_manager = tm
```
(`Optional` stays imported — it is used by `current_case_id`/`current_case_path` properties at lines 278-282.)

- [ ] **Step 3: Verify no import of the legacy package remains in src/**

Run: `rg "wft\.ui\.themes" src/`
Expected: no matches

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest tests/ -v --tb=short | Select-Object -Last 3`
Expected: 425 passed (418 baseline − 9 legacy tests + 1 wiring test + 9 removed... recount: 418 − 9 + 1 = 410), 0 failures. If the count differs, investigate before proceeding.

- [ ] **Step 5: Document commit for user approval**

```bash
git add src/wft/main.py src/wft/ui/main_window.py
git commit -m "refactor(ui): drop legacy theme wiring from startup and MainWindow"
```
(Do not execute without explicit user approval.)

---

### Task 4: Delete the legacy theme package

**Files:**
- Delete: `src/wft/ui/themes/theme_manager.py`, `src/wft/ui/themes/tokens.py`, `src/wft/ui/themes/dark_neon.qss`, `src/wft/ui/themes/high_contrast.qss`, `src/wft/ui/themes/reduced_glow.qss` (the whole directory)

**Interfaces:**
- Consumes: nothing (Task 3 removed all references)
- Produces: `wft.ui.theme` is the only theme implementation in the codebase

- [ ] **Step 1: Confirm zero references remain anywhere (src, tests, packaging)**

Run:
```
rg "wft\.ui\.themes" . --stats
rg "ColorTokens" . --stats
rg "dark_neon|high_contrast\.qss" src/ tests/ scripts/
```
Expected: no matches in any command output

- [ ] **Step 2: Delete the directory**

```powershell
Remove-Item -Recurse -Force src\wft\ui\themes
```

- [ ] **Step 3: Sanity-import the app entry**

Run: `python -c "import wft.main; import wft.bootstrap; from wft.ui import ThemeManager, DesignTokens; print('imports ok')"`
Expected: `imports ok`

- [ ] **Step 4: Full suite**

Run: `python -m pytest tests/ -v --tb=short | Select-Object -Last 3`
Expected: 410 passed, 0 failures (same count as Task 3 Step 4)

- [ ] **Step 5: E2E demo still passes**

Run: `python scripts/run_e2e_demo.py`
Expected: 27/27 steps pass (per repo AGENTS.md session log)

- [ ] **Step 6: Document commit for user approval**

```bash
git add -A src/wft/ui/themes
git commit -m "refactor(ui): delete legacy theme package superseded by token system"
```
(Do not execute without explicit user approval.)

---

### Task 5: Update AGENTS.md and final verification

**Files:**
- Modify: `AGENTS.md` — lines 22, 108, 133, 261, 262, 290 (documented below)
- Modify: `AGENTS.md` — session memory log append

**Interfaces:**
- Consumes: nothing
- Produces: docs match code (repo AGENTS.md rule 8 requires this whenever architecture changes)

- [ ] **Step 1: Update the directory tree (line 108)**

Replace:
```
│       │   ├── themes/               # dark_neon.qss, high_contrast.qss, tokens.py, theme_manager.py
```
with:
```
│       │   ├── theme/                # DesignTokens, qss_builder, ThemeManager, layout/style helpers
```

- [ ] **Step 2: Update the Design System section (lines 261-262)**

Replace:
```
- **Color tokens** defined in `wft/ui/themes/tokens.py` (frozen dataclass `ColorTokens`).
- **QSS files:** `dark_neon.qss`, `high_contrast.qss`, `reduced_glow.qss` in `wft/ui/themes/`.
```
with:
```
- **Color tokens** defined in `wft/ui/theme/tokens.py` (frozen dataclass `DesignTokens`).
- **QSS** is generated from tokens by `wft/ui/theme/qss_builder.py` (`build_full_qss`); there are NO static .qss files.
```

- [ ] **Step 3: Update the theme bullets in section 6 header (line ~254 theme list)**

Change "**Theme:** Dark neon (default), High Contrast (alternative), Reduced Glow." to "**Theme:** Dark forensic (default, token-built). High Contrast is spec-deferred, not implemented."

- [ ] **Step 4: Fix line 290 (reduced motion bullet)**

Replace "- Reduced motion setting available via `ThemeManager.set_reduced_motion(True)`." with "- Reduced motion available as `DesignTokens.reduced_motion` (consumed by `NavigationSidebar`); no runtime API to toggle it yet."

- [ ] **Step 5: Fix line 22 (feature list)**

Replace "dark-neon and high-contrast themes" with "token-built dark theme".

- [ ] **Step 6: Fix line 133 (test file description)**

Replace "# UI components, nav, themes (32 tests)" with "# UI components, nav (22 tests)".

- [ ] **Step 7: Append session memory log entry**

Add under "## 14. Session Memory Log":

```markdown
### 2026-10-08 (Legacy Theme System Removal)
- Change: Deleted the entire legacy theme system (`src/wft/ui/themes/`: ColorTokens, old ThemeManager, 3 static .qss files). The surviving token system (`src/wft/ui/theme/`: DesignTokens + qss_builder.py + ThemeManager) is now the only implementation. `main.py` no longer pre-applies a stylesheet; `Container.__init__` applies the built QSS via `load_saved_theme()`. Removed the unused `MainWindow.set_theme_manager()` hook and repointed `wft.ui` package exports to the new classes.
- Reason: architecture-scan found two full theme systems; the old one applied `dark_neon.qss` at `main.py:49` which was immediately overwritten by `bootstrap.py:52` — dead at runtime, with drifting token definitions and 9 tests locking it in place.
- Verification: full suite 410 passed (418 − 9 legacy tests + 1 new wiring test); E2E demo 27/27; `python -c "import wft.main"` clean.
- Deviations from spec: `docs/superpowers/specs/2026-07-21-phase1-ui-redesign.md` had marked the legacy .qss files "PRESERVE for rollback" — deleted instead (git history serves rollback; in-tree derived QSS invites drift). `high_contrast`, previously advertised in AGENTS.md, was spec-deferred and unreachable; removing it is a docs correction, not a feature removal. Follow-up: add `high_contrast` as a `DesignTokens` preset + registry entry when wanted.
```

- [ ] **Step 8: Final verification battery**

Run:
```
python -m pytest tests/ -v --tb=short | Select-Object -Last 3
python scripts/run_e2e_demo.py
python -m compileall -q src/wft
```
Expected: 410 passed; 27/27 steps; compileall silent (exit 0)

- [ ] **Step 9: Document commit for user approval**

```bash
git add AGENTS.md
git commit -m "docs: remove legacy theme system from architecture docs"
```
(Do not execute without explicit user approval.)

---

## Self-Review Notes

1. **Scan coverage:** every `wft.ui.themes` reference found in the repo (src: `main.py`, `main_window.py`, `ui/__init__.py`; tests: `test_ui_components.py` × 9 tests) has a removal step in Tasks 1-3. Deletion of the package itself is Task 4, gated by the `rg` verification in Task 4 Step 1.
2. **Behavior preservation:** the new `ThemeManager.load_saved_theme()` already runs in `Container.__init__` before `MainWindow` construction — the exact moment the legacy QSS was being overwritten — so removing the legacy call cannot change final styles.
3. **No placeholders:** every step contains exact file/line targets and commands; test counts are precomputed (418 → 410).
4. **Known follow-ups (out of scope):** (a) `SettingsPage._on_save` writes to `~/.wft/settings.toml` while `main.py` reads the platform path — settings silently lost on Windows; (b) timestamp helper duplication (bottleneck #2, 12 copies); (c) high_contrast as a real preset.
