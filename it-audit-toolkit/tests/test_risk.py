"""
Tests for the risk calculator module.

Validates risk score computation, severity classification, compliance
percentage calculations, and risk distribution metrics.
"""

import pytest
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    AuditEngagement,
    AuditArea,
    Control,
    Finding,
    RiskRating,
    ControlStatus,
    FindingSeverity,
)
from src.risk_calculator import RiskCalculator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_control(control_id, status, risk_weight=3):
    """Helper to create a Control with given status and weight."""
    return Control(
        control_id=control_id,
        title=f"Test Control {control_id}",
        description="Test control description",
        status=status,
        risk_weight=risk_weight,
    )


def _make_finding(finding_id, severity):
    """Helper to create a Finding with given severity."""
    return Finding(
        finding_id=finding_id,
        title=f"Test Finding {finding_id}",
        audit_area="Test Area",
        severity=severity,
        description="Test finding description",
    )


def _make_engagement_with_controls(controls, findings=None):
    """Helper to create an engagement with one area containing given controls."""
    area = AuditArea(
        name="Test Area",
        description="Test audit area",
        controls=controls,
        findings=findings or [],
    )
    engagement = AuditEngagement(
        name="Test Engagement",
        client="Test Client",
        lead_auditor="Test Auditor",
        audit_areas=[area],
    )
    return engagement


# ---------------------------------------------------------------------------
# RiskRating Tests
# ---------------------------------------------------------------------------

class TestRiskRating:
    """Tests for the RiskRating dataclass."""

    def test_basic_risk_calculation(self):
        """Risk score should be likelihood * impact."""
        rating = RiskRating(likelihood=3, impact=4)
        assert rating.score == 12
        assert rating.severity == "high"

    def test_minimum_risk_score(self):
        """Minimum score of 1 should be informational."""
        rating = RiskRating(likelihood=1, impact=1)
        assert rating.score == 1
        assert rating.severity == "informational"

    def test_maximum_risk_score(self):
        """Maximum score of 25 should be critical."""
        rating = RiskRating(likelihood=5, impact=5)
        assert rating.score == 25
        assert rating.severity == "critical"

    def test_critical_threshold_boundary(self):
        """Score of 20 should be critical (lower boundary)."""
        rating = RiskRating(likelihood=4, impact=5)
        assert rating.score == 20
        assert rating.severity == "critical"

    def test_high_threshold_boundary(self):
        """Score of 12 should be high (lower boundary)."""
        rating = RiskRating(likelihood=3, impact=4)
        assert rating.score == 12
        assert rating.severity == "high"

    def test_high_upper_boundary(self):
        """Score of 19 should still be high."""
        # 19 is not achievable with integers (no L*I=19), test closest: 4*4=16
        rating = RiskRating(likelihood=4, impact=4)
        assert rating.score == 16
        assert rating.severity == "high"

    def test_medium_threshold_boundary(self):
        """Score of 6 should be medium (lower boundary)."""
        rating = RiskRating(likelihood=2, impact=3)
        assert rating.score == 6
        assert rating.severity == "medium"

    def test_medium_upper_boundary(self):
        """Score of 10 should be medium."""
        rating = RiskRating(likelihood=2, impact=5)
        assert rating.score == 10
        assert rating.severity == "medium"

    def test_low_threshold_boundary(self):
        """Score of 2 should be low (lower boundary)."""
        rating = RiskRating(likelihood=1, impact=2)
        assert rating.score == 2
        assert rating.severity == "low"

    def test_low_upper_boundary(self):
        """Score of 5 should be low."""
        rating = RiskRating(likelihood=1, impact=5)
        assert rating.score == 5
        assert rating.severity == "low"

    def test_invalid_likelihood_too_high(self):
        """Likelihood > 5 should raise ValueError."""
        with pytest.raises(ValueError, match="Likelihood must be 1-5"):
            RiskRating(likelihood=6, impact=3)

    def test_invalid_likelihood_too_low(self):
        """Likelihood < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="Likelihood must be 1-5"):
            RiskRating(likelihood=0, impact=3)

    def test_invalid_impact_too_high(self):
        """Impact > 5 should raise ValueError."""
        with pytest.raises(ValueError, match="Impact must be 1-5"):
            RiskRating(likelihood=3, impact=6)

    def test_invalid_impact_too_low(self):
        """Impact < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="Impact must be 1-5"):
            RiskRating(likelihood=3, impact=0)

    def test_to_dict(self):
        """to_dict should include all fields."""
        rating = RiskRating(likelihood=3, impact=4, rationale="Test rationale")
        d = rating.to_dict()
        assert d["likelihood"] == 3
        assert d["impact"] == 4
        assert d["score"] == 12
        assert d["severity"] == "high"
        assert d["rationale"] == "Test rationale"

    def test_from_dict(self):
        """from_dict should reconstruct a valid RiskRating."""
        data = {"likelihood": 4, "impact": 5, "rationale": "Reconstructed"}
        rating = RiskRating.from_dict(data)
        assert rating.likelihood == 4
        assert rating.impact == 5
        assert rating.score == 20
        assert rating.severity == "critical"
        assert rating.rationale == "Reconstructed"


# ---------------------------------------------------------------------------
# RiskCalculator.score_to_severity Tests
# ---------------------------------------------------------------------------

class TestScoreToSeverity:
    """Tests for the static score_to_severity mapping."""

    def test_all_severity_levels(self):
        expected = {
            1: "informational",
            2: "low",
            3: "low",
            4: "low",
            5: "low",
            6: "medium",
            8: "medium",
            10: "medium",
            11: "medium",
            12: "high",
            15: "high",
            16: "high",
            19: "high",
            20: "critical",
            25: "critical",
        }
        for score, severity in expected.items():
            assert RiskCalculator.score_to_severity(score) == severity, (
                f"Score {score} should map to {severity}"
            )


# ---------------------------------------------------------------------------
# Control Risk Calculation Tests
# ---------------------------------------------------------------------------

class TestControlRisk:
    """Tests for per-control risk calculation."""

    def test_effective_control_low_risk(self):
        """Effective control with low weight should have minimal risk."""
        ctrl = _make_control("TST-001", ControlStatus.EFFECTIVE.value, risk_weight=1)
        eng = _make_engagement_with_controls([ctrl])
        calc = RiskCalculator(eng)
        result = calc.calculate_control_risk(ctrl)
        assert result["likelihood"] == 1
        assert result["impact"] == 1
        assert result["risk_score"] == 1
        assert result["severity"] == "informational"

    def test_ineffective_control_high_weight(self):
        """Ineffective control with high weight should have high risk."""
        ctrl = _make_control("TST-002", ControlStatus.INEFFECTIVE.value, risk_weight=5)
        eng = _make_engagement_with_controls([ctrl])
        calc = RiskCalculator(eng)
        result = calc.calculate_control_risk(ctrl)
        assert result["likelihood"] == 4
        assert result["impact"] == 5
        assert result["risk_score"] == 20
        assert result["severity"] == "critical"

    def test_partially_effective_control(self):
        """Partially effective control should have moderate risk."""
        ctrl = _make_control("TST-003", ControlStatus.PARTIALLY_EFFECTIVE.value, risk_weight=3)
        eng = _make_engagement_with_controls([ctrl])
        calc = RiskCalculator(eng)
        result = calc.calculate_control_risk(ctrl)
        assert result["likelihood"] == 3
        assert result["impact"] == 3
        assert result["risk_score"] == 9
        assert result["severity"] == "medium"

    def test_not_applicable_control_zero_risk(self):
        """Not applicable control should have zero risk."""
        ctrl = _make_control("TST-004", ControlStatus.NOT_APPLICABLE.value, risk_weight=5)
        eng = _make_engagement_with_controls([ctrl])
        calc = RiskCalculator(eng)
        result = calc.calculate_control_risk(ctrl)
        assert result["risk_score"] == 0
        assert result["severity"] == "not_applicable"

    def test_not_tested_control_assumes_moderate(self):
        """Not tested control should assume moderate likelihood."""
        ctrl = _make_control("TST-005", ControlStatus.NOT_TESTED.value, risk_weight=4)
        eng = _make_engagement_with_controls([ctrl])
        calc = RiskCalculator(eng)
        result = calc.calculate_control_risk(ctrl)
        assert result["likelihood"] == 3  # Default moderate
        assert result["impact"] == 4


# ---------------------------------------------------------------------------
# Compliance Percentage Tests
# ---------------------------------------------------------------------------

class TestComplianceCalculation:
    """Tests for compliance percentage calculations."""

    def test_all_effective_controls(self):
        """All effective controls should yield 100% compliance."""
        controls = [
            _make_control(f"C-{i}", ControlStatus.EFFECTIVE.value) for i in range(5)
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        assert result["compliance_pct"] == 100.0

    def test_all_ineffective_controls(self):
        """All ineffective controls should yield 0% compliance."""
        controls = [
            _make_control(f"C-{i}", ControlStatus.INEFFECTIVE.value) for i in range(5)
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        assert result["compliance_pct"] == 0.0

    def test_mixed_controls_compliance(self):
        """Mix of effective and ineffective should calculate correctly."""
        controls = [
            _make_control("C-1", ControlStatus.EFFECTIVE.value),
            _make_control("C-2", ControlStatus.EFFECTIVE.value),
            _make_control("C-3", ControlStatus.INEFFECTIVE.value),
            _make_control("C-4", ControlStatus.INEFFECTIVE.value),
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        assert result["compliance_pct"] == 50.0  # 2 effective / 4 tested

    def test_partial_controls_weighted_half(self):
        """Partially effective controls count at 50% weight."""
        controls = [
            _make_control("C-1", ControlStatus.EFFECTIVE.value),
            _make_control("C-2", ControlStatus.PARTIALLY_EFFECTIVE.value),
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        # (1 + 0.5) / 2 = 75%
        assert result["compliance_pct"] == 75.0

    def test_untested_controls_excluded_from_compliance(self):
        """Untested controls should not count toward compliance denominator."""
        controls = [
            _make_control("C-1", ControlStatus.EFFECTIVE.value),
            _make_control("C-2", ControlStatus.NOT_TESTED.value),
            _make_control("C-3", ControlStatus.NOT_TESTED.value),
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        # 1 effective / 1 tested = 100%
        assert result["compliance_pct"] == 100.0
        assert result["tested_controls"] == 1

    def test_not_applicable_excluded_from_compliance(self):
        """N/A controls should not count toward compliance denominator."""
        controls = [
            _make_control("C-1", ControlStatus.EFFECTIVE.value),
            _make_control("C-2", ControlStatus.NOT_APPLICABLE.value),
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        assert result["compliance_pct"] == 100.0
        assert result["tested_controls"] == 1

    def test_empty_area_zero_compliance(self):
        """An area with no controls should have 0% compliance."""
        eng = _make_engagement_with_controls([])
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        assert result["compliance_pct"] == 0.0
        assert result["total_controls"] == 0


# ---------------------------------------------------------------------------
# Finding Risk Calculation Tests
# ---------------------------------------------------------------------------

class TestFindingRisk:
    """Tests for per-finding risk calculation."""

    def test_critical_finding_risk(self):
        """Critical finding should have high risk score."""
        finding = _make_finding("FND-001", FindingSeverity.CRITICAL.value)
        eng = _make_engagement_with_controls([], findings=[finding])
        calc = RiskCalculator(eng)
        result = calc.calculate_finding_risk(finding)
        assert result["likelihood"] == 5
        assert result["impact"] == 5
        assert result["risk_score"] == 25
        assert result["computed_severity"] == "critical"

    def test_low_finding_risk(self):
        """Low finding should have minimal risk score."""
        finding = _make_finding("FND-002", FindingSeverity.LOW.value)
        eng = _make_engagement_with_controls([], findings=[finding])
        calc = RiskCalculator(eng)
        result = calc.calculate_finding_risk(finding)
        assert result["likelihood"] == 2
        assert result["impact"] == 2
        assert result["risk_score"] == 4

    def test_finding_with_explicit_risk_rating(self):
        """Finding with explicit risk_rating should use those values."""
        finding = Finding(
            finding_id="FND-003",
            title="Test Finding",
            audit_area="Test Area",
            severity="medium",
            description="Test",
            risk_rating={"likelihood": 4, "impact": 3},
        )
        eng = _make_engagement_with_controls([], findings=[finding])
        calc = RiskCalculator(eng)
        result = calc.calculate_finding_risk(finding)
        assert result["likelihood"] == 4
        assert result["impact"] == 3
        assert result["risk_score"] == 12

    def test_remediation_timeline_critical(self):
        """Critical finding should have immediate remediation timeline."""
        finding = _make_finding("FND-004", FindingSeverity.CRITICAL.value)
        eng = _make_engagement_with_controls([], findings=[finding])
        calc = RiskCalculator(eng)
        result = calc.calculate_finding_risk(finding)
        assert "7 days" in result["remediation_timeline"]

    def test_remediation_timeline_medium(self):
        """Medium finding should have 90-day timeline."""
        finding = _make_finding("FND-005", FindingSeverity.MEDIUM.value)
        eng = _make_engagement_with_controls([], findings=[finding])
        calc = RiskCalculator(eng)
        result = calc.calculate_finding_risk(finding)
        assert "90 days" in result["remediation_timeline"]


# ---------------------------------------------------------------------------
# Engagement-Level Risk Tests
# ---------------------------------------------------------------------------

class TestEngagementRisk:
    """Tests for engagement-wide risk calculation."""

    def test_engagement_risk_with_multiple_areas(self):
        """Engagement risk should aggregate across all areas."""
        area1 = AuditArea(
            name="Area 1",
            controls=[
                _make_control("A1-1", ControlStatus.EFFECTIVE.value, risk_weight=3),
                _make_control("A1-2", ControlStatus.INEFFECTIVE.value, risk_weight=5),
            ],
            findings=[_make_finding("F-1", "high")],
        )
        area2 = AuditArea(
            name="Area 2",
            controls=[
                _make_control("A2-1", ControlStatus.EFFECTIVE.value, risk_weight=4),
            ],
            findings=[],
        )
        eng = AuditEngagement(
            name="Multi-Area Test",
            client="Test",
            lead_auditor="Tester",
            audit_areas=[area1, area2],
        )
        calc = RiskCalculator(eng)
        result = calc.calculate_engagement_risk()
        assert result["total_controls"] == 3
        assert result["total_findings"] == 1
        assert len(result["area_results"]) == 2

    def test_engagement_risk_updates_engagement_metrics(self):
        """calculate_engagement_risk should update engagement attributes."""
        controls = [
            _make_control("C-1", ControlStatus.EFFECTIVE.value, risk_weight=3),
            _make_control("C-2", ControlStatus.INEFFECTIVE.value, risk_weight=4),
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        calc.calculate_engagement_risk()
        assert eng.overall_risk_score > 0
        assert eng.overall_compliance_pct > 0

    def test_risk_distribution_matrix_shape(self):
        """Risk distribution matrix should be 5x5."""
        controls = [_make_control("C-1", ControlStatus.EFFECTIVE.value)]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_engagement_risk()
        matrix = result["risk_distribution"]["matrix"]
        assert len(matrix) == 5
        for row in matrix:
            assert len(row) == 5

    def test_remediation_summary_sorted_by_priority(self):
        """Remediation summary should be sorted by severity (critical first)."""
        findings = [
            _make_finding("F-1", "low"),
            _make_finding("F-2", "critical"),
            _make_finding("F-3", "medium"),
        ]
        eng = _make_engagement_with_controls([], findings=findings)
        calc = RiskCalculator(eng)
        result = calc.calculate_engagement_risk()
        summary = result["remediation_summary"]
        assert len(summary) == 3
        assert summary[0]["severity"] == "critical"
        assert summary[1]["severity"] == "medium"
        assert summary[2]["severity"] == "low"

    def test_heat_map_data_structure(self):
        """Heat map data should have correct structure."""
        controls = [
            _make_control("C-1", ControlStatus.EFFECTIVE.value, risk_weight=2),
            _make_control("C-2", ControlStatus.INEFFECTIVE.value, risk_weight=4),
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        heat_map = calc.generate_risk_heat_map_data()
        assert "heat_map" in heat_map
        assert "likelihood_labels" in heat_map
        assert "impact_labels" in heat_map
        assert len(heat_map["likelihood_labels"]) == 5
        assert len(heat_map["impact_labels"]) == 5
        assert len(heat_map["heat_map"]) == 5
        for row in heat_map["heat_map"]:
            assert len(row) == 5
            for cell in row:
                assert "score" in cell
                assert "severity" in cell
                assert "color" in cell
                assert "count" in cell


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_engagement_with_no_areas(self):
        """Engagement with no audit areas should compute without errors."""
        eng = AuditEngagement(
            name="Empty Engagement",
            client="Test",
            lead_auditor="Tester",
        )
        calc = RiskCalculator(eng)
        result = calc.calculate_engagement_risk()
        assert result["total_controls"] == 0
        assert result["total_findings"] == 0
        assert result["overall_compliance_pct"] == 0.0

    def test_all_controls_not_applicable(self):
        """All N/A controls should result in 0% compliance (no tested controls)."""
        controls = [
            _make_control("C-1", ControlStatus.NOT_APPLICABLE.value),
            _make_control("C-2", ControlStatus.NOT_APPLICABLE.value),
        ]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        assert result["compliance_pct"] == 0.0
        assert result["tested_controls"] == 0

    def test_single_effective_control(self):
        """Single effective control should yield 100% compliance."""
        controls = [_make_control("C-1", ControlStatus.EFFECTIVE.value)]
        eng = _make_engagement_with_controls(controls)
        calc = RiskCalculator(eng)
        result = calc.calculate_area_compliance(eng.audit_areas[0])
        assert result["compliance_pct"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
