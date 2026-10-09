from wft.ui.components.status_badge import StatusBadge


class TestStatusBadgeNewAPI:
    def test_constructs_with_status(self, qapp):
        badge = StatusBadge("Test", "success")
        assert badge.text() == "Test"

    def test_status_dynamic_property_set(self, qapp):
        badge = StatusBadge("Test", "warning")
        assert badge.property("status") == "warning"

    def test_set_status_updates_property(self, qapp):
        badge = StatusBadge()
        badge.set_status("error")
        assert badge.property("status") == "error"

    def test_invalid_status_falls_back(self, qapp):
        badge = StatusBadge("Test", "invalid")
        assert badge.property("status") == "neutral"


class TestStatusBadgeDeprecated:
    def test_set_badge_type_parsed_maps_to_success(self, qapp):
        badge = StatusBadge()
        badge.set_badge_type("parsed")
        assert badge.property("status") == "success"

    def test_set_badge_type_verified_maps_to_success(self, qapp):
        badge = StatusBadge()
        badge.set_badge_type("verified")
        assert badge.property("status") == "success"

    def test_set_badge_type_failed_maps_to_error(self, qapp):
        badge = StatusBadge()
        badge.set_badge_type("failed")
        assert badge.property("status") == "error"

    def test_set_badge_type_partial_maps_to_warning(self, qapp):
        badge = StatusBadge()
        badge.set_badge_type("partial")
        assert badge.property("status") == "warning"

    def test_set_badge_type_unsupported_maps_to_neutral(self, qapp):
        badge = StatusBadge()
        badge.set_badge_type("unsupported")
        assert badge.property("status") == "neutral"
