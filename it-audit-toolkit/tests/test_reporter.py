"""
Tests for the report generator module.

Validates report context building, HTML report generation,
and executive summary text output.
"""

import os
import sys
import tempfile
import pytest

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    AuditEngagement,
    AuditArea,
    Control,
    Finding,
    ControlStatus,
    FindingSeverity,
)
from src.reporter import AuditReporter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_control(control_id, status, risk_weight=3):
    """Helper to create a Control with given status and weight."""
    return Control(
        control_id=control_id,
        title=f"Test Control {control_id}",
        description="Test control description for report testing.",
        test_procedure="1. Review documentation. 2. Test configuration.",
        expected_evidence="Policy document, system configuration screenshot",
        framework_mapping={"ISO 27001": "A.5.15", "COBIT": "DSS05.04"},
        status=status,
        risk_weight=risk_weight,
        auditor_notes="Tested and documented.",
        tested_date="2025-11-15",
        tested_by="Test Auditor",
    )


def _make_finding(finding_id, severity, area="Test Area"):
    """Helper to create a Finding with given severity."""
    return Finding(
        finding_id=finding_id,
        title=f"Test Finding {finding_id}",
        audit_area=area,
        severity=severity,
        description=f"Detailed description of finding {finding_id} for report testing.",
        root_cause="Process gap identified during testing.",
        business_impact="Potential unauthorized access to sensitive data.",
        recommendation="Implement corrective control within 90 days.",
        management_response="Accepted. Remediation planned for Q1 2026.",
    )


def _make_sample_engagement():
    """Create a comprehensive sample engagement for testing."""
    controls_ac = [
        _make_control("AC-001", ControlStatus.EFFECTIVE.value, risk_weight=5),
        _make_control("AC-002", ControlStatus.PARTIALLY_EFFECTIVE.value, risk_weight=5),
        _make_control("AC-003", ControlStatus.EFFECTIVE.value, risk_weight=4),
        _make_control("AC-004", ControlStatus.INEFFECTIVE.value, risk_weight=5),
        _make_control("AC-005", ControlStatus.INEFFECTIVE.value, risk_weight=5),
    ]

    controls_cm = [
        _make_control("CM-001", ControlStatus.EFFECTIVE.value, risk_weight=4),
        _make_control("CM-002", ControlStatus.EFFECTIVE.value, risk_weight=4),
        _make_control("CM-003", ControlStatus.PARTIALLY_EFFECTIVE.value, risk_weight=5),
    ]

    findings_ac = [
        _make_finding("FND-001", FindingSeverity.CRITICAL.value, "Access Control"),
        _make_finding("FND-002", FindingSeverity.HIGH.value, "Access Control"),
        _make_finding("FND-003", FindingSeverity.MEDIUM.value, "Access Control"),
    ]

    findings_cm = [
        _make_finding("FND-004", FindingSeverity.MEDIUM.value, "Change Management"),
    ]

    area_ac = AuditArea(
        name="Access Control",
        description="Controls for identity and access management.",
        controls=controls_ac,
        findings=findings_ac,
        status="completed",
        start_date="2025-10-01",
        completion_date="2025-11-01",
    )

    area_cm = AuditArea(
        name="Change Management",
        description="Controls for IT change management.",
        controls=controls_cm,
        findings=findings_cm,
        status="completed",
        start_date="2025-11-01",
        completion_date="2025-11-15",
    )

    engagement = AuditEngagement(
        engagement_id="ENG-TEST001",
        name="Test Annual IT Audit",
        client="Test Corporation",
        lead_auditor="Jane Doe, CISA",
        audit_team=["Jane Doe, CISA", "John Smith, CISSP"],
        status="reporting",
        scope_description="Comprehensive IT audit covering access control and change management.",
        objectives=[
            "Evaluate IT control effectiveness",
            "Assess regulatory compliance",
            "Identify control deficiencies",
        ],
        methodology="Risk-based approach aligned with ISACA standards.",
        start_date="2025-10-01",
        end_date="2025-12-01",
        audit_areas=[area_ac, area_cm],
    )

    return engagement


# ---------------------------------------------------------------------------
# Report Context Tests
# ---------------------------------------------------------------------------

class TestReportContext:
    """Tests for the report context building."""

    def test_context_has_required_keys(self):
        """Report context should contain all required top-level keys."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()

        required_keys = [
            "engagement",
            "exec_summary",
            "findings",
            "area_summaries",
            "heat_map",
            "remediation_roadmap",
            "report_generated_at",
        ]
        for key in required_keys:
            assert key in context, f"Missing required key: {key}"

    def test_engagement_metadata_in_context(self):
        """Context should contain correct engagement metadata."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()

        assert context["engagement"]["id"] == "ENG-TEST001"
        assert context["engagement"]["name"] == "Test Annual IT Audit"
        assert context["engagement"]["client"] == "Test Corporation"
        assert context["engagement"]["lead_auditor"] == "Jane Doe, CISA"

    def test_exec_summary_metrics(self):
        """Executive summary should contain correct metrics."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()
        es = context["exec_summary"]

        assert es["total_controls"] == 8  # 5 AC + 3 CM
        assert es["total_findings"] == 4  # 3 AC + 1 CM
        assert es["critical_findings"] == 1
        assert es["high_findings"] == 1
        assert es["medium_findings"] == 2
        assert es["total_areas"] == 2

    def test_findings_sorted_by_severity(self):
        """Findings in context should be sorted by severity (critical first)."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
        previous_order = -1
        for finding in context["findings"]:
            current_order = severity_order.get(finding["severity"], 5)
            assert current_order >= previous_order, (
                f"Finding {finding['finding_id']} with severity {finding['severity']} "
                f"is out of order"
            )
            previous_order = current_order

    def test_area_summaries_present(self):
        """Area summaries should be present for each audit area."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()

        assert len(context["area_summaries"]) == 2
        area_names = [a["name"] for a in context["area_summaries"]]
        assert "Access Control" in area_names
        assert "Change Management" in area_names

    def test_area_summary_contains_metrics(self):
        """Each area summary should contain required metrics."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()

        for area in context["area_summaries"]:
            assert "name" in area
            assert "total_controls" in area
            assert "tested_controls" in area
            assert "compliance_pct" in area
            assert "finding_count" in area
            assert "average_risk_score" in area

    def test_heat_map_structure(self):
        """Heat map data should have the correct structure."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()

        assert "heat_map" in context["heat_map"]
        assert "likelihood_labels" in context["heat_map"]
        assert "impact_labels" in context["heat_map"]
        assert len(context["heat_map"]["heat_map"]) == 5

    def test_remediation_roadmap_present(self):
        """Remediation roadmap should contain entries for findings."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()

        assert len(context["remediation_roadmap"]) == 4


# ---------------------------------------------------------------------------
# HTML Report Generation Tests
# ---------------------------------------------------------------------------

class TestHTMLReport:
    """Tests for HTML report file generation."""

    def test_generates_html_file(self):
        """generate_html_report should create an HTML file."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.html")
            result_path = reporter.generate_html_report(output_path)

            assert os.path.exists(result_path)
            assert result_path.endswith(".html")

    def test_html_contains_client_name(self):
        """Generated HTML should contain the client name."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.html")
            reporter.generate_html_report(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                html = f.read()

            assert "Test Corporation" in html

    def test_html_contains_engagement_name(self):
        """Generated HTML should contain the engagement name."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.html")
            reporter.generate_html_report(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                html = f.read()

            assert "Test Annual IT Audit" in html

    def test_html_contains_findings(self):
        """Generated HTML should contain finding details."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.html")
            reporter.generate_html_report(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                html = f.read()

            assert "FND-001" in html
            assert "FND-002" in html
            assert "CRITICAL" in html

    def test_html_contains_severity_colors(self):
        """Generated HTML should contain severity color coding."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.html")
            reporter.generate_html_report(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                html = f.read()

            # Should contain severity CSS classes
            assert "badge-critical" in html
            assert "badge-high" in html

    def test_html_is_valid_structure(self):
        """Generated HTML should have proper DOCTYPE and structure."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.html")
            reporter.generate_html_report(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                html = f.read()

            assert html.startswith("<!DOCTYPE html>")
            assert "</html>" in html
            assert "<head>" in html
            assert "<body>" in html

    def test_creates_output_directory_if_needed(self):
        """Should create the output directory if it does not exist."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "nested", "report.html")
            result_path = reporter.generate_html_report(output_path)

            assert os.path.exists(result_path)


# ---------------------------------------------------------------------------
# Text Summary Tests
# ---------------------------------------------------------------------------

class TestTextSummary:
    """Tests for the text executive summary generation."""

    def test_text_summary_contains_key_sections(self):
        """Text summary should contain all major sections."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        text = reporter.generate_executive_summary_text()

        assert "EXECUTIVE SUMMARY" in text
        assert "OVERALL RISK POSTURE" in text
        assert "FINDINGS SUMMARY" in text
        assert "COMPLIANCE BY AUDIT AREA" in text
        assert "REMEDIATION PRIORITIES" in text

    def test_text_summary_contains_engagement_info(self):
        """Text summary should contain engagement metadata."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        text = reporter.generate_executive_summary_text()

        assert "Test Annual IT Audit" in text
        assert "Test Corporation" in text
        assert "Jane Doe, CISA" in text

    def test_text_summary_contains_metrics(self):
        """Text summary should contain key metrics."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        text = reporter.generate_executive_summary_text()

        assert "Overall Compliance" in text
        assert "Overall Risk Score" in text
        assert "Total Findings" in text

    def test_findings_detail_text(self):
        """Findings detail text should contain all findings."""
        eng = _make_sample_engagement()
        reporter = AuditReporter(eng)
        text = reporter.generate_findings_detail_text()

        assert "DETAILED FINDINGS" in text
        assert "FND-001" in text
        assert "FND-002" in text
        assert "FND-003" in text
        assert "FND-004" in text
        assert "CRITICAL" in text
        assert "Recommendation" in text


# ---------------------------------------------------------------------------
# Reporter Utility Tests
# ---------------------------------------------------------------------------

class TestReporterUtilities:
    """Tests for reporter utility/filter functions."""

    def test_severity_color_critical(self):
        assert AuditReporter._severity_color("critical") == "#dc3545"

    def test_severity_color_high(self):
        assert AuditReporter._severity_color("high") == "#fd7e14"

    def test_severity_color_medium(self):
        assert AuditReporter._severity_color("medium") == "#ffc107"

    def test_severity_color_low(self):
        assert AuditReporter._severity_color("low") == "#28a745"

    def test_severity_color_informational(self):
        assert AuditReporter._severity_color("informational") == "#17a2b8"

    def test_severity_color_unknown(self):
        """Unknown severity should return default gray."""
        assert AuditReporter._severity_color("unknown") == "#6c757d"

    def test_compliance_color_high(self):
        """80%+ should be green."""
        assert AuditReporter._compliance_color(85.0) == "#28a745"

    def test_compliance_color_medium(self):
        """60-79% should be yellow."""
        assert AuditReporter._compliance_color(65.0) == "#ffc107"

    def test_compliance_color_low(self):
        """40-59% should be orange."""
        assert AuditReporter._compliance_color(45.0) == "#fd7e14"

    def test_compliance_color_critical(self):
        """Below 40% should be red."""
        assert AuditReporter._compliance_color(30.0) == "#dc3545"

    def test_severity_badge_contains_html(self):
        """Severity badge should return an HTML span element."""
        badge = AuditReporter._severity_badge("critical")
        assert "<span" in badge
        assert "CRITICAL" in badge
        assert "#dc3545" in badge

    def test_status_icon_effective(self):
        """Effective status should return checkmark."""
        icon = AuditReporter._status_icon("effective")
        assert "10004" in icon  # Unicode checkmark


# ---------------------------------------------------------------------------
# Empty Engagement Tests
# ---------------------------------------------------------------------------

class TestEmptyEngagement:
    """Tests for reporting on engagements with minimal data."""

    def test_report_with_no_findings(self):
        """Should generate a valid report with no findings."""
        controls = [_make_control("C-1", ControlStatus.EFFECTIVE.value)]
        area = AuditArea(
            name="Test Area",
            controls=controls,
            findings=[],
        )
        eng = AuditEngagement(
            name="Empty Findings Test",
            client="Test",
            lead_auditor="Tester",
            audit_areas=[area],
        )
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()
        assert context["exec_summary"]["total_findings"] == 0
        assert len(context["findings"]) == 0

    def test_report_with_no_controls(self):
        """Should generate a valid report with no controls."""
        area = AuditArea(name="Empty Controls", controls=[], findings=[])
        eng = AuditEngagement(
            name="Empty Controls Test",
            client="Test",
            lead_auditor="Tester",
            audit_areas=[area],
        )
        reporter = AuditReporter(eng)
        context = reporter.build_report_context()
        assert context["exec_summary"]["total_controls"] == 0

    def test_html_generation_with_no_areas(self):
        """Should generate valid HTML with no audit areas."""
        eng = AuditEngagement(
            name="No Areas Test",
            client="Test",
            lead_auditor="Tester",
        )
        reporter = AuditReporter(eng)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "empty_report.html")
            result_path = reporter.generate_html_report(output_path)
            assert os.path.exists(result_path)

            with open(output_path, "r", encoding="utf-8") as f:
                html = f.read()
            assert "<!DOCTYPE html>" in html
            assert "No Areas Test" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
