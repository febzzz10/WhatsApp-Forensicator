from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from wft.ui.themes.tokens import ColorTokens


class ThemeManager(QObject):
    theme_changed = Signal(str)

    THEMES = {
        "dark_neon": "Dark Neon",
        "high_contrast": "High Contrast",
        "reduced_glow": "Reduced Glow",
    }

    def __init__(self, app: QApplication, themes_dir: Optional[Path] = None) -> None:
        super().__init__()
        self._app = app
        self._themes_dir = themes_dir or Path(__file__).parent
        self._current_theme = "dark_neon"
        self._reduced_motion = False
        self._tokens = ColorTokens()
        self._on_theme_change: Optional[Callable[[str], None]] = None

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def reduced_motion(self) -> bool:
        return self._reduced_motion

    @property
    def tokens(self) -> ColorTokens:
        return self._tokens

    def set_theme(self, theme_name: str) -> None:
        if theme_name not in self.THEMES:
            return
        self._current_theme = theme_name
        qss_path = self._themes_dir / f"{theme_name}.qss"
        if not qss_path.exists():
            qss_path = self._themes_dir / "dark_neon.qss"
        try:
            qss = qss_path.read_text(encoding="utf-8")
            self._app.setStyleSheet(qss)
        except Exception:
            pass
        self._tokens = (
            ColorTokens.high_contrast() if theme_name == "high_contrast" else ColorTokens()
        )
        self.theme_changed.emit(theme_name)
        if self._on_theme_change:
            self._on_theme_change(theme_name)

    def set_reduced_motion(self, enabled: bool) -> None:
        self._reduced_motion = enabled

    def set_on_theme_change(self, callback: Optional[Callable[[str], None]]) -> None:
        self._on_theme_change = callback
