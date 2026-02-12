"""
Tests for Risk Modules - Risk Engine and Risk Matrix.

Tests cover:
    - Risk engine initialization and weight validation
    - Risk score calculation from findings
    - Category risk computation
    - Risk level classification
    - Risk matrix coordinate mapping
    - Matrix rendering
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRiskEngine(unittest.TestCase):
    """Test cases for the RiskEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.risk.risk_engine import RiskEngine
        self.engine = RiskEngine()

    def test_initialization_defaults(self):
        """Test engine initializes with default weights."""
        self.assertAlmostEqual(sum(self.engine.weights.values()), 1.0, places=2)

    def test_custom_weights(self):
        """Test engine with custom weights."""
        from src.risk.risk_engine import RiskEngine
        custom_weights = {
            "network_security": 0.30,
            "application_security": 0.20,
            "data_protection": 0.20,
            "compliance": 0.10,
            "operational_security": 0.10,
            "third_party_risk": 0.10,
        }
        engine = RiskEngine(weights=custom_weights)
        self.assertAlmostEqual(sum(engine.weights.values()), 1.0, places=2)

    def test_weight_normalization(self):
        """Test that non-normalized weights are corrected."""
        from src.risk.risk_engine import RiskEngine
        bad_weights = {
            "network_security": 0.5,
            "application_security": 0.5,
            "data_protection": 0.5,
            "compliance": 0.5,
            "operational_security": 0.5,
            "third_party_risk": 0.5,
        }
        engine = RiskEngine(weights=bad_weights)
        self.assertAlmostEqual(sum(engine.weights.values()), 1.0, places=2)

    def test_calculate_risk_empty_data(self):
        """Test risk calculation with empty data."""
        result = self.engine.calculate_risk({})
        self.assertEqual(result.total_findings, 0)
        self.assertEqual(result.overall_risk_score, 0.0)
        self.assertEqual(result.overall_risk_level, "minimal")

    def test_calculate_risk_with_findings(self):
        """Test risk calculation with real findings."""
        scan_data = {
            "network_scan": {
                "open_ports": [
                    {"port": 23, "service": "Telnet", "risk_level": "critical"},
                    {"port": 3389, "service": "RDP", "risk_level": "critical"},
                ],
                "findings": [
                    {"title": "Telnet Exposed", "severity": "critical", "cvss_score": 9.1},
                    {"title": "RDP Exposed", "severity": "critical", "cvss_score": 9.0},
                ],
            },
        }
        result = self.engine.calculate_risk(scan_data)
        self.assertGreater(result.overall_risk_score, 0)
        self.assertGreater(result.total_findings, 0)

    def test_severity_distribution(self):
        """Test severity distribution calculation."""
        findings = [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
        ]
        dist = self.engine._severity_distribution(findings)
        self.assertEqual(dist["critical"], 2)
        self.assertEqual(dist["high"], 1)
        self.assertEqual(dist["medium"], 1)
        self.assertEqual(dist["low"], 1)

    def test_findings_to_score(self):
        """Test converting findings to a risk score."""
        # No findings = 0 score
        self.assertEqual(self.engine._findings_to_score([]), 0.0)

        # Critical findings should produce high scores
        critical_findings = [
            {"severity": "critical"} for _ in range(3)
        ]
        score = self.engine._findings_to_score(critical_findings)
        self.assertGreater(score, 5.0)

        # Info findings should produce low scores
        info_findings = [
            {"severity": "info"} for _ in range(3)
        ]
        score = self.engine._findings_to_score(info_findings)
        self.assertLess(score, 1.0)

    def test_score_to_level(self):
        """Test risk level classification."""
        self.assertEqual(self.engine._score_to_level(9.0), "critical")
        self.assertEqual(self.engine._score_to_level(7.0), "high")
        self.assertEqual(self.engine._score_to_level(5.0), "medium")
        self.assertEqual(self.engine._score_to_level(3.0), "low")
        self.assertEqual(self.engine._score_to_level(1.0), "minimal")

    def test_risk_categories_computed(self):
        """Test that all 6 risk categories are computed."""
        result = self.engine.calculate_risk({})
        self.assertEqual(len(result.categories), 6)
        category_names = [c.category for c in result.categories]
        self.assertIn("network_security", category_names)
        self.assertIn("application_security", category_names)
        self.assertIn("data_protection", category_names)
        self.assertIn("compliance", category_names)
        self.assertIn("operational_security", category_names)
        self.assertIn("third_party_risk", category_names)

    def test_recommendations_generated(self):
        """Test that recommendations are generated for risky categories."""
        scan_data = {
            "network_scan": {
                "open_ports": [
                    {"port": 23, "service": "Telnet", "risk_level": "critical"},
                ],
                "findings": [
                    {"title": "Telnet Exposed", "severity": "critical", "cvss_score": 9.1},
                    {"title": "SMB Exposed", "severity": "high", "cvss_score": 8.0},
                    {"title": "FTP Exposed", "severity": "high", "cvss_score": 7.5},
                ],
            },
        }
        result = self.engine.calculate_risk(scan_data)
        self.assertGreater(len(result.recommendations), 0)

    def test_result_serialization(self):
        """Test RiskAssessment serialization."""
        result = self.engine.calculate_risk({})
        d = result.to_dict()
        self.assertIn("overall_risk_score", d)
        self.assertIn("categories", d)
        self.assertIn("recommendations", d)


class TestRiskMatrix(unittest.TestCase):
    """Test cases for the RiskMatrix class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.risk.risk_matrix import RiskMatrix
        self.matrix = RiskMatrix()

    def test_get_risk_level(self):
        """Test getting risk level for specific coordinates."""
        # Critical: high likelihood, high impact
        result = self.matrix.get_risk_level(5, 5)
        self.assertEqual(result["risk_rating"], "Critical")
        self.assertEqual(result["risk_score"], 25)

        # Low: low likelihood, low impact
        result = self.matrix.get_risk_level(1, 1)
        self.assertEqual(result["risk_rating"], "Very Low")
        self.assertEqual(result["risk_score"], 1)

    def test_get_risk_level_clamping(self):
        """Test that out-of-range values are clamped."""
        result = self.matrix.get_risk_level(0, 6)
        self.assertEqual(result["likelihood"], 1)
        self.assertEqual(result["impact"], 5)

    def test_generate_empty(self):
        """Test matrix generation with empty data."""
        result = self.matrix.generate({})
        self.assertEqual(len(result.risk_items), 0)
        self.assertEqual(result.summary["total_risks"], 0)

    def test_generate_with_findings(self):
        """Test matrix generation with findings."""
        scan_data = {
            "network_scan": {
                "findings": [
                    {"title": "Critical Finding", "severity": "critical", "cvss_score": 9.5, "remediation": "Fix it"},
                    {"title": "Low Finding", "severity": "low", "cvss_score": 2.0, "remediation": "Note it"},
                ],
            },
        }
        result = self.matrix.generate(scan_data)
        self.assertEqual(len(result.risk_items), 2)
        self.assertEqual(result.summary["total_risks"], 2)

    def test_severity_to_coordinates(self):
        """Test severity-to-coordinate mapping."""
        # Critical severity should map to high likelihood/impact
        l, i = self.matrix._severity_to_coordinates("critical", 9.5, "network")
        self.assertGreaterEqual(l, 4)
        self.assertEqual(i, 5)

        # Low severity should map to low coordinates
        l, i = self.matrix._severity_to_coordinates("low", 2.0, "web")
        self.assertLessEqual(l, 3)
        self.assertLessEqual(i, 3)

    def test_render_terminal(self):
        """Test terminal rendering produces output."""
        from src.risk.risk_matrix import RiskMatrixResult
        result = RiskMatrixResult()
        output = self.matrix.render_terminal(result)
        self.assertIn("RISK ASSESSMENT MATRIX", output)
        self.assertIn("Negligible", output)
        self.assertIn("Catastrophic", output)

    def test_render_html(self):
        """Test HTML rendering produces valid HTML."""
        from src.risk.risk_matrix import RiskMatrixResult
        result = RiskMatrixResult()
        html = self.matrix.render_html(result)
        self.assertIn("risk-matrix", html)
        self.assertIn("table", html)
        self.assertIn("legend", html)

    def test_matrix_grid_built(self):
        """Test matrix grid contains all 25 cells."""
        result = self.matrix.generate({})
        self.assertEqual(len(result.matrix_data), 25)
        # Check cell 5,5 is Critical
        cell = result.matrix_data["5,5"]
        self.assertEqual(cell["risk_rating"], "Critical")
        self.assertEqual(cell["risk_score"], 25)

    def test_result_serialization(self):
        """Test RiskMatrixResult serialization."""
        result = self.matrix.generate({})
        d = result.to_dict()
        self.assertIn("risk_items", d)
        self.assertIn("matrix_grid", d)
        self.assertIn("summary", d)


if __name__ == "__main__":
    unittest.main()
