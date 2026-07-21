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
