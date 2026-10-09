from unittest.mock import MagicMock
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


class TestUIPackageThemeWiring:
    def test_ui_package_exports_new_theme_system(self):
        from wft.ui import ThemeManager as ExportedTM
        from wft.ui import DesignTokens
        from wft.ui.theme.theme_manager import ThemeManager as SourceTM
        from wft.ui.theme.tokens import DesignTokens as SourceDT

        assert ExportedTM is SourceTM
        assert DesignTokens is SourceDT
