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
        expected = {
            "home", "dashboard", "cases", "evidence",
            "adb", "decrypt", "chats", "contacts",
            "groups", "calls", "media", "timeline",
            "recovered", "voip", "search", "reports",
            "audit", "settings",
        }
        actual = {m.value for m in PageId}
        assert actual == expected
