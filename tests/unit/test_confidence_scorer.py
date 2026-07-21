from wft.recovery.scoring.confidence_scorer import ConfidenceScorer


class TestConfidenceScorer:
    def setup_method(self) -> None:
        self.scorer = ConfidenceScorer()

    def test_high_confidence(self) -> None:
        result = self.scorer.score(
            field_count=10, expected_fields=10,
            has_provenance=True, has_valid_structure=True, has_competing=False,
        )
        assert result == "HIGH"

    def test_medium_confidence(self) -> None:
        result = self.scorer.score(
            field_count=7, expected_fields=10,
            has_provenance=False, has_valid_structure=True, has_competing=False,
        )
        assert result == "MEDIUM"

    def test_low_confidence(self) -> None:
        result = self.scorer.score(
            field_count=3, expected_fields=10,
            has_provenance=False, has_valid_structure=False, has_competing=True,
        )
        assert result == "LOW"

    def test_unresolved(self) -> None:
        result = self.scorer.score(
            field_count=0, expected_fields=10,
            has_provenance=False, has_valid_structure=False, has_competing=True,
        )
        assert result == "UNRESOLVED"

    def test_numeric_score(self) -> None:
        assert self.scorer.numeric_score("HIGH") == 1.0
        assert self.scorer.numeric_score("MEDIUM") == 0.6
        assert self.scorer.numeric_score("LOW") == 0.3
        assert self.scorer.numeric_score("UNRESOLVED") == 0.0
