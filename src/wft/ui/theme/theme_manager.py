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
