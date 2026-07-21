from typing import Optional


class ConfidenceScorer:
    def score(self, field_count: int, expected_fields: int, has_provenance: bool,
              has_valid_structure: bool, has_competing: bool) -> str:
        if field_count >= expected_fields and has_provenance and has_valid_structure:
            return "HIGH"
        if field_count >= expected_fields * 0.7 and has_valid_structure:
            return "MEDIUM"
        if field_count > 0:
            return "LOW"
        return "UNRESOLVED"

    def numeric_score(self, confidence_level: str) -> float:
        mapping = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3, "UNRESOLVED": 0.0}
        return mapping.get(confidence_level, 0.0)
