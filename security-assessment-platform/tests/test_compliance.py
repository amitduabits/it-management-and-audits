"""
Tests for Compliance Modules - ISO 27001, PCI-DSS, NIST CSF.

Tests cover:
    - Framework initialization
    - Control/requirement enumeration
    - Assessment logic with mock data
    - Score calculation
    - Result serialization
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestISO27001Checker(unittest.TestCase):
    """Test cases for the ISO27001Checker class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.compliance.iso27001 import ISO27001Checker
        self.checker = ISO27001Checker()

    def test_initialization(self):
        """Test checker initializes with 20 controls."""
        self.assertEqual(len(self.checker.controls), 20)

    def test_control_list(self):
        """Test get_control_list returns all controls."""
        controls = self.checker.get_control_list()
        self.assertEqual(len(controls), 20)
        self.assertIn("id", controls[0])
        self.assertIn("name", controls[0])
        self.assertIn("category", controls[0])

    def test_assess_empty_data(self):
        """Test assessment with empty scan data."""
        result = self.checker.assess({})
        self.assertEqual(result.total_controls, 20)
        self.assertIsNotNone(result.assessment_date)

    def test_assess_with_network_data(self):
        """Test assessment with network scan data."""
        scan_data = {
            "network_scan": {
                "open_ports": [
                    {"port": 80, "service": "HTTP", "risk_level": "medium", "banner": ""},
                    {"port": 443, "service": "HTTPS", "risk_level": "low", "banner": ""},
                ],
                "findings": [],
                "total_ports_scanned": 1024,
            },
        }
        result = self.checker.assess(scan_data)
        self.assertGreater(result.total_controls, 0)
        # With only HTTP/HTTPS open, access control should pass
        access_control = next(
            (c for c in result.control_results if c.control_id == "A.5.15"),
            None,
        )
        self.assertIsNotNone(access_control)
        self.assertEqual(access_control.status, "pass")

    def test_assess_with_dangerous_services(self):
        """Test that dangerous services cause control failures."""
        scan_data = {
            "network_scan": {
                "open_ports": [
                    {"port": 23, "service": "Telnet", "risk_level": "critical", "banner": ""},
                    {"port": 3389, "service": "RDP", "risk_level": "critical", "banner": ""},
                    {"port": 6379, "service": "Redis", "risk_level": "critical", "banner": ""},
                    {"port": 3306, "service": "MySQL", "risk_level": "high", "banner": ""},
                ],
                "findings": [
                    {"title": "Telnet Exposed", "severity": "critical"},
                    {"title": "RDP Exposed", "severity": "critical"},
                ],
                "total_ports_scanned": 1024,
            },
        }
        result = self.checker.assess(scan_data)

        # Access control should fail with critical services exposed
        access_control = next(
            (c for c in result.control_results if c.control_id == "A.5.15"),
            None,
        )
        self.assertEqual(access_control.status, "fail")

        # Database access restriction should fail
        db_control = next(
            (c for c in result.control_results if c.control_id == "A.8.3"),
            None,
        )
        self.assertEqual(db_control.status, "fail")

    def test_result_serialization(self):
        """Test result to_dict serialization."""
        result = self.checker.assess({})
        result_dict = result.to_dict()
        self.assertEqual(result_dict["framework"], "ISO 27001:2022")
        self.assertIn("controls", result_dict)
        self.assertIn("category_scores", result_dict)

    def test_category_scores_calculated(self):
        """Test that category scores are calculated."""
        result = self.checker.assess({})
        self.assertIn("Organizational Controls", result.category_scores)
        self.assertIn("Technological Controls", result.category_scores)

    def test_policy_controls_with_attestation(self):
        """Test policy controls respond to attestation data."""
        scan_data = {
            "policies": {
                "security_policy": True,
                "security_training": True,
            }
        }
        result = self.checker.assess(scan_data)
        policy_control = next(
            (c for c in result.control_results if c.control_id == "A.5.1"),
            None,
        )
        self.assertIsNotNone(policy_control)
        self.assertEqual(policy_control.status, "pass")


class TestPCIDSSChecker(unittest.TestCase):
    """Test cases for the PCIDSSChecker class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.compliance.pci_dss import PCIDSSChecker
        self.checker = PCIDSSChecker()

    def test_initialization(self):
        """Test checker initializes with 15 requirements."""
        self.assertEqual(len(self.checker.requirements), 15)

    def test_requirement_list(self):
        """Test get_requirement_list returns all requirements."""
        reqs = self.checker.get_requirement_list()
        self.assertEqual(len(reqs), 15)
        self.assertTrue(all("id" in r for r in reqs))

    def test_assess_empty_data(self):
        """Test assessment with empty data."""
        result = self.checker.assess({})
        self.assertEqual(result.total_requirements, 15)

    def test_assess_secure_network(self):
        """Test that clean network passes relevant requirements."""
        scan_data = {
            "network_scan": {
                "open_ports": [
                    {"port": 443, "service": "HTTPS", "risk_level": "low"},
                ],
                "findings": [],
            },
        }
        result = self.checker.assess(scan_data)
        # Req 2.2 (no unnecessary services) should pass
        req_22 = next(
            (r for r in result.requirement_results if r.requirement_id == "Req 2.2"),
            None,
        )
        self.assertEqual(req_22.status, "pass")

    def test_assess_insecure_network(self):
        """Test that insecure services fail requirements."""
        scan_data = {
            "network_scan": {
                "open_ports": [
                    {"port": 21, "service": "FTP", "risk_level": "high"},
                    {"port": 23, "service": "Telnet", "risk_level": "critical"},
                ],
                "findings": [
                    {"title": "FTP Exposed", "severity": "high"},
                    {"title": "Telnet Exposed", "severity": "critical"},
                ],
            },
        }
        result = self.checker.assess(scan_data)
        req_22 = next(
            (r for r in result.requirement_results if r.requirement_id == "Req 2.2"),
            None,
        )
        self.assertEqual(req_22.status, "fail")

    def test_section_scores_calculated(self):
        """Test that section scores are calculated."""
        result = self.checker.assess({})
        self.assertIsInstance(result.section_scores, dict)

    def test_result_serialization(self):
        """Test result serialization."""
        result = self.checker.assess({})
        d = result.to_dict()
        self.assertEqual(d["framework"], "PCI-DSS v4.0")
        self.assertIn("requirements", d)


class TestNISTCSFChecker(unittest.TestCase):
    """Test cases for the NISTCSFChecker class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.compliance.nist_csf import NISTCSFChecker
        self.checker = NISTCSFChecker()

    def test_initialization(self):
        """Test checker initializes with 20 subcategories."""
        self.assertEqual(len(self.checker.checks), 20)

    def test_function_summary(self):
        """Test function summary returns all 5 functions."""
        summary = self.checker.get_function_summary()
        self.assertIn("Identify", summary)
        self.assertIn("Protect", summary)
        self.assertIn("Detect", summary)
        self.assertIn("Respond", summary)
        self.assertIn("Recover", summary)

    def test_assess_empty_data(self):
        """Test assessment with empty data."""
        result = self.checker.assess({})
        self.assertEqual(result.total_subcategories, 20)
        self.assertIn("Identify", result.function_scores)

    def test_tier_calculation(self):
        """Test implementation tier calculation."""
        # With no data, tier should be low
        result = self.checker.assess({})
        self.assertIn(result.overall_tier, [1, 2, 3, 4])

    def test_assess_with_all_policies(self):
        """Test assessment with all policy attestations."""
        scan_data = {
            "policies": {
                "asset_inventory": True,
                "security_policy": True,
                "data_encryption_at_rest": True,
                "security_training": True,
                "network_baseline": True,
                "network_monitoring": True,
                "malware_detection": True,
                "incident_response_plan": True,
                "incident_investigation": True,
                "recovery_plan": True,
                "lessons_learned": True,
            }
        }
        result = self.checker.assess(scan_data)
        # Should have some passes
        self.assertGreater(result.passed, 0)

    def test_result_serialization(self):
        """Test result serialization."""
        result = self.checker.assess({})
        d = result.to_dict()
        self.assertEqual(d["framework"], "NIST CSF v2.0")
        self.assertIn("function_scores", d)
        self.assertIn("overall_tier_name", d)


if __name__ == "__main__":
    unittest.main()
