"""
Tests for Reporting Modules - Executive, Technical, and Remediation.

Tests cover:
    - Report generator initialization
    - Report generation with mock data
    - HTML output validation
    - Fallback report generation
    - Finding enrichment
    - Remediation classification
"""

import unittest
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestExecutiveReport(unittest.TestCase):
    """Test cases for the ExecutiveReportGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.reporting.executive_report import ExecutiveReportGenerator
        self.generator = ExecutiveReportGenerator()
        self.sample_risk_data = {
            "overall_risk_score": 6.4,
            "overall_risk_level": "high",
            "risk_trend": "stable",
            "total_findings": 15,
            "severity_distribution": {
                "critical": 2, "high": 5, "medium": 5, "low": 2, "info": 1,
            },
            "categories": [
                {"display_name": "Network Security", "raw_score": 7.5, "weight": 0.25, "finding_count": 5},
            ],
            "recommendations": [
                {"priority": 1, "urgency": "immediate", "category": "Network", "recommendation": "Fix critical issues", "timeframe": "0-30 days"},
            ],
        }

    def test_initialization(self):
        """Test generator initialization."""
        self.assertIsNotNone(self.generator.template_dir)
        self.assertIsNotNone(self.generator.env)

    def test_generate_html_output(self):
        """Test that generate produces HTML string."""
        html = self.generator.generate(risk_data=self.sample_risk_data)
        self.assertIsInstance(html, str)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Executive", html)

    def test_generate_with_compliance(self):
        """Test generation with compliance data."""
        compliance_data = {
            "iso27001": {"overall_score": 0.55, "overall_percentage": 55.0, "passed": 7, "failed": 6, "partial": 4},
        }
        html = self.generator.generate(
            risk_data=self.sample_risk_data,
            compliance_data=compliance_data,
        )
        self.assertIn("html", html)

    def test_save_to_file(self):
        """Test saving report to file."""
        html = self.generator.generate(risk_data=self.sample_risk_data)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_executive.html")
            self.generator.save(html, path)
            self.assertTrue(os.path.exists(path))
            with open(path, "r") as f:
                content = f.read()
            self.assertIn("html", content)

    def test_risk_color_mapping(self):
        """Test risk color mapping."""
        self.assertEqual(self.generator._risk_color("critical"), "#dc2626")
        self.assertEqual(self.generator._risk_color("high"), "#f97316")
        self.assertEqual(self.generator._risk_color("low"), "#22c55e")

    def test_score_color_mapping(self):
        """Test compliance score color mapping."""
        self.assertEqual(self.generator._score_color(90), "#22c55e")
        self.assertEqual(self.generator._score_color(50), "#eab308")
        self.assertEqual(self.generator._score_color(10), "#ef4444")

    def test_fallback_report(self):
        """Test fallback report generation."""
        context = {
            "report_title": "Test Report",
            "organization": "Test Org",
            "report_date": "2025-01-01",
            "report_id": "TEST-001",
            "assessor": "Tester",
            "overall_risk_score": 5.0,
            "overall_risk_level": "medium",
            "risk_color": "#eab308",
            "risk_trend": "stable",
            "total_findings": 10,
            "severity_distribution": {"critical": 1, "high": 2, "medium": 3, "low": 3, "info": 1},
            "recommendations": [],
        }
        html = self.generator._fallback_report(context)
        self.assertIn("Test Report", html)
        self.assertIn("Test Org", html)


class TestTechnicalReport(unittest.TestCase):
    """Test cases for the TechnicalReportGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.reporting.technical_report import TechnicalReportGenerator
        self.generator = TechnicalReportGenerator()
        self.sample_findings = [
            {
                "id": "NET-001",
                "title": "RDP Service Exposed",
                "description": "Remote Desktop Protocol is accessible.",
                "category": "Network Security",
                "severity": "critical",
                "cvss_score": 9.0,
                "evidence": "Port 3389 open",
                "remediation": "Require VPN for RDP.",
                "compliance_refs": ["PCI-DSS Req 7.2"],
            },
            {
                "id": "WEB-001",
                "title": "Missing HSTS",
                "description": "HSTS header not present.",
                "category": "Web Security",
                "severity": "high",
                "cvss_score": 7.4,
                "evidence": "Header not set",
                "remediation": "Add HSTS header.",
            },
        ]

    def test_generate_html_output(self):
        """Test generation produces HTML."""
        html = self.generator.generate(findings=self.sample_findings)
        self.assertIsInstance(html, str)
        self.assertIn("html", html)

    def test_finding_enrichment(self):
        """Test finding enrichment adds display fields."""
        enriched = self.generator._enrich_findings(self.sample_findings)
        self.assertEqual(len(enriched), 2)
        self.assertIn("cvss_severity_label", enriched[0])
        self.assertIn("cvss_severity_color", enriched[0])
        self.assertIn("finding_number", enriched[0])

    def test_cvss_severity_mapping(self):
        """Test CVSS to severity label conversion."""
        from src.reporting.technical_report import cvss_to_severity
        label, color = cvss_to_severity(9.5)
        self.assertEqual(label, "Critical")

        label, color = cvss_to_severity(7.0)
        self.assertEqual(label, "High")

        label, color = cvss_to_severity(5.0)
        self.assertEqual(label, "Medium")

        label, color = cvss_to_severity(2.0)
        self.assertEqual(label, "Low")

    def test_statistics_computation(self):
        """Test statistics are correctly computed."""
        enriched = self.generator._enrich_findings(self.sample_findings)
        stats = self.generator._compute_statistics(enriched)
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["severity_counts"]["critical"], 1)
        self.assertEqual(stats["severity_counts"]["high"], 1)
        self.assertGreater(stats["avg_cvss"], 0)

    def test_empty_findings(self):
        """Test generation with no findings."""
        html = self.generator.generate(findings=[])
        self.assertIn("html", html)


class TestRemediationRoadmap(unittest.TestCase):
    """Test cases for the RemediationRoadmapGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.reporting.remediation_roadmap import RemediationRoadmapGenerator
        self.generator = RemediationRoadmapGenerator()
        self.sample_findings = [
            {
                "id": "WEB-001",
                "title": "Missing HSTS Header",
                "description": "Add HSTS security header",
                "severity": "high",
                "cvss_score": 7.4,
                "remediation": "Add Strict-Transport-Security header.",
            },
            {
                "id": "NET-001",
                "title": "Implement Network Segmentation",
                "description": "Architecture change needed for segmentation",
                "severity": "high",
                "cvss_score": 8.0,
                "remediation": "Design and implement VLAN segmentation.",
            },
            {
                "id": "WEB-002",
                "title": "Remove Server Banner Information",
                "description": "Server header reveals version info",
                "severity": "low",
                "cvss_score": 2.6,
                "remediation": "Remove Server header.",
            },
        ]

    def test_generate_html_output(self):
        """Test generation produces HTML."""
        html = self.generator.generate(findings=self.sample_findings)
        self.assertIsInstance(html, str)
        self.assertIn("html", html)

    def test_finding_classification(self):
        """Test findings are classified into correct phases."""
        roadmap = self.generator._classify_findings(self.sample_findings)
        self.assertIn("quick_wins", roadmap)
        self.assertIn("short_term", roadmap)
        self.assertIn("long_term", roadmap)

        # Header finding should be a quick win
        quick_win_titles = [i.title for i in roadmap["quick_wins"]]
        self.assertTrue(
            any("HSTS" in t or "Banner" in t for t in quick_win_titles),
            f"Expected header or banner finding in quick wins, got: {quick_win_titles}"
        )

    def test_summary_computation(self):
        """Test summary statistics are computed."""
        roadmap = self.generator._classify_findings(self.sample_findings)
        summary = self.generator._compute_summary(roadmap)
        self.assertIn("total_items", summary)
        self.assertIn("total_estimated_hours", summary)
        self.assertIn("phase_breakdown", summary)
        self.assertEqual(summary["total_items"], 3)

    def test_remediation_item_structure(self):
        """Test RemediationItem dataclass."""
        from src.reporting.remediation_roadmap import RemediationItem
        item = RemediationItem(
            finding_id="TEST-001",
            title="Test Finding",
            phase="quick_wins",
            effort="low",
            estimated_hours=2,
        )
        d = item.to_dict()
        self.assertEqual(d["finding_id"], "TEST-001")
        self.assertEqual(d["phase"], "quick_wins")

    def test_compliance_remediation_items(self):
        """Test compliance gap remediation items are generated."""
        compliance_data = {
            "iso27001": {
                "controls": [
                    {
                        "control_id": "A.8.20",
                        "control_name": "Network Security",
                        "description": "Network controls",
                        "status": "fail",
                        "remediation": "Implement network controls",
                    },
                ],
            },
        }
        items = self.generator._compliance_remediation(compliance_data)
        self.assertGreater(len(items), 0)
        self.assertTrue(any("A.8.20" in i.finding_id for i in items))

    def test_save_to_file(self):
        """Test saving roadmap to file."""
        html = self.generator.generate(findings=self.sample_findings)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_roadmap.html")
            self.generator.save(html, path)
            self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
