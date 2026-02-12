"""
Tests for the Severity Calculator.

Validates CVSS-inspired scoring, business impact assessment,
composite severity calculation, and severity override rules.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.severity_calculator import (
    SeverityCalculator,
    CVSSVector,
    BusinessImpactFactors,
    SeverityAssessment,
    DataClassification,
    SystemCriticality,
)


class TestCVSSVector:
    """Tests for CVSS base score calculation."""

    def test_default_vector_score(self):
        """Default vector (all medium values) should produce a moderate score."""
        vector = CVSSVector()
        score = vector.calculate_base_score()
        assert 3.0 <= score <= 7.0, f"Default vector score {score} outside expected range"

    def test_maximum_severity_vector(self):
        """Maximum exploitability and impact should produce a high score."""
        vector = CVSSVector(
            attack_vector=0.85,
            attack_complexity=0.77,
            privileges_required=0.85,
            user_interaction=0.85,
            confidentiality_impact=0.56,
            integrity_impact=0.56,
            availability_impact=0.56,
            scope_changed=True,
        )
        score = vector.calculate_base_score()
        assert score >= 8.0, f"Maximum vector score {score} should be >= 8.0"

    def test_minimum_severity_vector(self):
        """Minimum impact values should produce a low score."""
        vector = CVSSVector(
            attack_vector=0.20,
            attack_complexity=0.44,
            privileges_required=0.27,
            user_interaction=0.62,
            confidentiality_impact=0.0,
            integrity_impact=0.0,
            availability_impact=0.0,
        )
        score = vector.calculate_base_score()
        assert score == 0.0, f"Zero impact vector should produce score 0.0, got {score}"

    def test_scope_changed_increases_score(self):
        """Changed scope should produce a higher score than unchanged."""
        base_params = dict(
            attack_vector=0.85,
            attack_complexity=0.77,
            privileges_required=0.62,
            user_interaction=0.85,
            confidentiality_impact=0.56,
            integrity_impact=0.22,
            availability_impact=0.22,
        )
        unchanged = CVSSVector(**base_params, scope_changed=False)
        changed = CVSSVector(**base_params, scope_changed=True)
        assert changed.calculate_base_score() >= unchanged.calculate_base_score()

    def test_score_range(self):
        """All CVSS scores should be between 0.0 and 10.0."""
        test_vectors = [
            CVSSVector(attack_vector=0.85, confidentiality_impact=0.56),
            CVSSVector(attack_vector=0.20, confidentiality_impact=0.0),
            CVSSVector(attack_vector=0.55, confidentiality_impact=0.22),
        ]
        for vector in test_vectors:
            score = vector.calculate_base_score()
            assert 0.0 <= score <= 10.0, f"Score {score} outside valid range"

    def test_confidentiality_only_impact(self):
        """An attack affecting only confidentiality should still produce a positive score."""
        vector = CVSSVector(
            attack_vector=0.85,
            attack_complexity=0.77,
            privileges_required=0.85,
            user_interaction=0.85,
            confidentiality_impact=0.56,
            integrity_impact=0.0,
            availability_impact=0.0,
        )
        score = vector.calculate_base_score()
        assert score > 0.0


class TestBusinessImpactFactors:
    """Tests for business impact factor creation."""

    def test_default_factors(self):
        """Default factors should have reasonable initial values."""
        bif = BusinessImpactFactors()
        assert bif.data_classification == DataClassification.INTERNAL
        assert bif.records_affected == 0
        assert bif.system_criticality == SystemCriticality.TIER_3_STANDARD
        assert bif.notification_required is False

    def test_custom_factors(self):
        """Custom factors should be properly stored."""
        bif = BusinessImpactFactors(
            data_classification=DataClassification.RESTRICTED,
            records_affected=2_300_000,
            system_criticality=SystemCriticality.TIER_1_CRITICAL,
            regulatory_frameworks=["GDPR", "CCPA"],
            notification_required=True,
            revenue_impact_per_hour=15000,
            estimated_downtime_hours=8,
            affected_customers=500000,
        )
        assert bif.records_affected == 2_300_000
        assert len(bif.regulatory_frameworks) == 2
        assert bif.notification_required is True


class TestSeverityCalculator:
    """Tests for the composite severity calculator."""

    @pytest.fixture
    def calc(self):
        """Provide a SeverityCalculator instance."""
        return SeverityCalculator()

    def test_default_assessment(self, calc):
        """Assessment without inputs should produce medium defaults."""
        assessment = calc.calculate_severity()
        assert assessment.technical_score == 5.0
        assert assessment.business_impact_score == 5.0
        assert assessment.confidence == "low"

    def test_critical_data_breach_assessment(self, calc):
        """A large PII breach should produce high or critical severity."""
        cvss = CVSSVector(
            attack_vector=0.85,
            attack_complexity=0.77,
            privileges_required=0.85,
            user_interaction=0.85,
            confidentiality_impact=0.56,
            integrity_impact=0.22,
            availability_impact=0.0,
        )
        business = BusinessImpactFactors(
            data_classification=DataClassification.RESTRICTED,
            records_affected=2_300_000,
            system_criticality=SystemCriticality.TIER_1_CRITICAL,
            regulatory_frameworks=["GDPR", "CCPA", "HIPAA"],
            notification_required=True,
            customer_trust_impact="critical",
            media_coverage_likely=True,
        )
        assessment = calc.calculate_severity(cvss, business)
        assert assessment.severity_level in ("critical", "high")
        assert assessment.composite_score >= 7.0
        assert assessment.regulatory_risk in ("critical", "high")

    def test_low_severity_event(self, calc):
        """A minor internal event should produce low severity."""
        cvss = CVSSVector(
            attack_vector=0.55,
            attack_complexity=0.44,
            privileges_required=0.27,
            user_interaction=0.62,
            confidentiality_impact=0.22,
            integrity_impact=0.0,
            availability_impact=0.0,
        )
        business = BusinessImpactFactors(
            data_classification=DataClassification.PUBLIC,
            records_affected=0,
            system_criticality=SystemCriticality.TIER_4_NON_CRITICAL,
        )
        assessment = calc.calculate_severity(cvss, business)
        assert assessment.severity_level in ("low", "informational", "medium")
        assert assessment.composite_score < 5.0

    def test_notification_elevates_severity(self, calc):
        """Regulatory notification requirement should elevate to at least HIGH."""
        business = BusinessImpactFactors(
            data_classification=DataClassification.INTERNAL,
            records_affected=100,
            system_criticality=SystemCriticality.TIER_4_NON_CRITICAL,
            notification_required=True,
            regulatory_frameworks=["GDPR"],
        )
        assessment = calc.calculate_severity(business_impact=business)
        assert assessment.severity_level in ("high", "critical")

    def test_quick_severity_convenience(self, calc):
        """quick_severity should produce valid assessments."""
        assessment = calc.quick_severity(
            data_classification="confidential",
            records_affected=50000,
            system_criticality="tier_2_important",
            regulatory_frameworks=["GDPR"],
            notification_required=True,
        )
        assert isinstance(assessment, SeverityAssessment)
        assert assessment.composite_score > 0
        assert assessment.severity_level in ("critical", "high", "medium", "low", "informational")
        assert assessment.recommended_response_time != ""

    def test_financial_impact_estimation(self, calc):
        """Financial impact should increase with records and regulatory frameworks."""
        business_small = BusinessImpactFactors(
            records_affected=100,
            regulatory_frameworks=[],
        )
        business_large = BusinessImpactFactors(
            records_affected=1_000_000,
            regulatory_frameworks=["GDPR", "HIPAA"],
            notification_required=True,
            revenue_impact_per_hour=10000,
            estimated_downtime_hours=24,
        )
        assessment_small = calc.calculate_severity(business_impact=business_small)
        assessment_large = calc.calculate_severity(business_impact=business_large)
        assert assessment_large.financial_impact_estimate > assessment_small.financial_impact_estimate

    def test_composite_score_range(self, calc):
        """Composite score should always be between 0 and 10."""
        test_cases = [
            (CVSSVector(), BusinessImpactFactors()),
            (CVSSVector(confidentiality_impact=0.56), BusinessImpactFactors(records_affected=1_000_000)),
            (CVSSVector(confidentiality_impact=0.0), BusinessImpactFactors(records_affected=0)),
        ]
        for cvss, bif in test_cases:
            assessment = calc.calculate_severity(cvss, bif)
            assert 0.0 <= assessment.composite_score <= 10.0

    def test_confidence_levels(self, calc):
        """Confidence should reflect the completeness of input data."""
        # Both inputs -> high
        assessment_both = calc.calculate_severity(CVSSVector(), BusinessImpactFactors())
        assert assessment_both.confidence == "high"

        # One input -> medium
        assessment_one = calc.calculate_severity(cvss_vector=CVSSVector())
        assert assessment_one.confidence == "medium"

        # No inputs -> low
        assessment_none = calc.calculate_severity()
        assert assessment_none.confidence == "low"

    def test_assessment_serialization(self, calc):
        """SeverityAssessment.to_dict should produce valid dictionary."""
        assessment = calc.quick_severity(
            data_classification="confidential",
            records_affected=10000,
        )
        d = assessment.to_dict()
        assert "technical_score" in d
        assert "business_impact_score" in d
        assert "composite_score" in d
        assert "severity_level" in d
        assert "justification" in d
        assert isinstance(d["justification"], list)

    def test_severity_matrix_completeness(self):
        """Severity matrix should define all 5 severity levels."""
        matrix = SeverityCalculator.get_severity_matrix()
        expected_levels = {"critical", "high", "medium", "low", "informational"}
        assert set(matrix.keys()) == expected_levels
        for level, details in matrix.items():
            assert "score_range" in details
            assert "description" in details
            assert "response_time" in details
            assert "examples" in details
            assert "escalation" in details

    def test_response_time_targets(self, calc):
        """Each severity level should have a defined response time."""
        for level in ["critical", "high", "medium", "low", "informational"]:
            assert level in calc.RESPONSE_TIMES

    def test_regulatory_risk_assessment(self, calc):
        """Regulatory risk should scale with frameworks and notification requirement."""
        bif_low = BusinessImpactFactors()
        bif_high = BusinessImpactFactors(
            regulatory_frameworks=["GDPR", "HIPAA", "PCI-DSS"],
            notification_required=True,
            records_affected=500_000,
        )
        assess_low = calc.calculate_severity(business_impact=bif_low)
        assess_high = calc.calculate_severity(business_impact=bif_high)
        risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        assert risk_order[assess_high.regulatory_risk] >= risk_order[assess_low.regulatory_risk]


class TestDataClassificationEnum:
    """Tests for data classification enum values."""

    def test_all_classifications(self):
        """All classification levels should be defined."""
        levels = [e.value for e in DataClassification]
        assert "public" in levels
        assert "internal" in levels
        assert "confidential" in levels
        assert "restricted" in levels
        assert "top_secret" in levels

    def test_classification_from_string(self):
        """Classifications should be constructible from string values."""
        assert DataClassification("public") == DataClassification.PUBLIC
        assert DataClassification("restricted") == DataClassification.RESTRICTED


class TestSystemCriticalityEnum:
    """Tests for system criticality enum values."""

    def test_all_tiers(self):
        """All four tiers should be defined."""
        tiers = [e.value for e in SystemCriticality]
        assert len(tiers) == 4
        assert "tier_1_critical" in tiers
        assert "tier_4_non_critical" in tiers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
