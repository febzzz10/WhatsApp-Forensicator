from PySide6.QtWidgets import QFrame
from wft.ui.components.status_banner import StatusBanner
from wft.ui.components.evidence_banner import EvidenceBanner


class TestStatusBanner:
    def test_default_construction(self, qapp):
        banner = StatusBanner()
        assert isinstance(banner, QFrame)

    def test_text_and_type_constructor(self, qapp):
        banner = StatusBanner("Test message", "verified")
        assert banner._label.text() == "Test message"

    def test_set_text(self, qapp):
        banner = StatusBanner()
        banner.set_text("Updated")
        assert banner._label.text() == "Updated"

    def test_set_banner_type(self, qapp):
        banner = StatusBanner()
        banner.set_banner_type("warning")
        assert banner._banner_type == "warning"


class TestEvidenceBannerCompat:
    def test_is_status_banner_subclass(self):
        assert issubclass(EvidenceBanner, StatusBanner)

    def test_same_constructor(self, qapp):
        banner = EvidenceBanner("Test", "info")
        assert banner._label.text() == "Test"
        assert banner._banner_type == "info"

    def test_set_text_works(self, qapp):
        banner = EvidenceBanner()
        banner.set_text("Hello")
        assert banner._label.text() == "Hello"

    def test_set_banner_type_works(self, qapp):
        banner = EvidenceBanner()
        banner.set_banner_type("verified")
        assert banner._banner_type == "verified"
