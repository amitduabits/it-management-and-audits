"""
Tests for Scanner Modules - Network, Web, and DNS Scanners.

Tests cover:
    - Scanner initialization and configuration
    - Port scanning result structures
    - Web header analysis logic
    - DNS record processing
    - Finding generation
    - Error handling
"""

import unittest
from unittest.mock import patch, MagicMock
import socket

# Add project root to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNetworkScanner(unittest.TestCase):
    """Test cases for the NetworkScanner class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.scanner.network_scanner import NetworkScanner
        self.scanner = NetworkScanner(timeout=1.0, max_threads=10)

    def test_initialization(self):
        """Test scanner initializes with correct defaults."""
        self.assertEqual(self.scanner.timeout, 1.0)
        self.assertEqual(self.scanner.max_threads, 10)
        self.assertEqual(self.scanner.banner_timeout, 3.0)

    def test_initialization_defaults(self):
        """Test scanner default values."""
        from src.scanner.network_scanner import NetworkScanner
        scanner = NetworkScanner()
        self.assertEqual(scanner.timeout, 2.0)
        self.assertEqual(scanner.max_threads, 50)

    def test_empty_target_raises_error(self):
        """Test that empty target raises ValueError."""
        with self.assertRaises(ValueError):
            self.scanner.scan("")

    def test_invalid_port_range(self):
        """Test that invalid port range raises ValueError."""
        with self.assertRaises(ValueError):
            self.scanner.scan("127.0.0.1", port_range=(0, 100))

        with self.assertRaises(ValueError):
            self.scanner.scan("127.0.0.1", port_range=(1000, 500))

        with self.assertRaises(ValueError):
            self.scanner.scan("127.0.0.1", port_range=(1, 70000))

    def test_scan_returns_result_object(self):
        """Test that scan returns a NetworkScanResult."""
        from src.scanner.network_scanner import NetworkScanResult
        result = self.scanner.scan("127.0.0.1", port_range=(1, 5))
        self.assertIsInstance(result, NetworkScanResult)
        self.assertEqual(result.target, "127.0.0.1")
        self.assertEqual(result.total_ports_scanned, 5)

    def test_scan_with_specific_ports(self):
        """Test scanning specific ports."""
        result = self.scanner.scan("127.0.0.1", specific_ports=[80, 443])
        self.assertEqual(result.total_ports_scanned, 2)

    def test_result_to_dict(self):
        """Test NetworkScanResult serialization."""
        result = self.scanner.scan("127.0.0.1", port_range=(1, 3))
        result_dict = result.to_dict()
        self.assertIn("target", result_dict)
        self.assertIn("open_ports", result_dict)
        self.assertIn("findings", result_dict)
        self.assertEqual(result_dict["target"], "127.0.0.1")

    def test_port_result_structure(self):
        """Test PortResult dataclass."""
        from src.scanner.network_scanner import PortResult
        pr = PortResult(port=80, state="open", service="HTTP")
        self.assertEqual(pr.port, 80)
        self.assertEqual(pr.state, "open")
        self.assertEqual(pr.service, "HTTP")
        self.assertEqual(pr.risk_level, "info")

    def test_validate_target_localhost(self):
        """Test target validation with localhost."""
        self.assertTrue(self.scanner.validate_target("127.0.0.1"))

    def test_validate_target_invalid(self):
        """Test target validation with invalid hostname."""
        self.assertFalse(self.scanner.validate_target("this.host.definitely.does.not.exist.invalid"))

    def test_common_services_mapping(self):
        """Test that COMMON_SERVICES contains expected entries."""
        from src.scanner.network_scanner import COMMON_SERVICES
        self.assertEqual(COMMON_SERVICES[80], "HTTP")
        self.assertEqual(COMMON_SERVICES[443], "HTTPS")
        self.assertEqual(COMMON_SERVICES[22], "SSH")
        self.assertEqual(COMMON_SERVICES[3306], "MySQL")

    def test_high_risk_ports_defined(self):
        """Test that high risk ports are defined."""
        from src.scanner.network_scanner import HIGH_RISK_PORTS
        self.assertIn(23, HIGH_RISK_PORTS)   # Telnet
        self.assertIn(3389, HIGH_RISK_PORTS) # RDP
        self.assertIn(6379, HIGH_RISK_PORTS) # Redis

    def test_finding_generation_for_dangerous_ports(self):
        """Test that findings are generated for dangerous open ports."""
        from src.scanner.network_scanner import PortResult
        open_ports = [
            PortResult(port=23, state="open", service="Telnet", risk_level="high"),
            PortResult(port=3389, state="open", service="RDP", risk_level="critical"),
        ]
        findings = self.scanner._generate_findings(open_ports, "test-target")
        self.assertTrue(len(findings) >= 2)
        titles = [f["title"] for f in findings]
        self.assertIn("Telnet Service Exposed", titles)
        self.assertIn("RDP Service Exposed", titles)

    def test_compliance_refs_for_high_risk(self):
        """Test compliance references are generated for high-risk ports."""
        refs = self.scanner._get_compliance_refs(23)
        self.assertTrue(any("PCI-DSS" in r for r in refs))
        self.assertTrue(any("NIST" in r for r in refs))


class TestWebScanner(unittest.TestCase):
    """Test cases for the WebScanner class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.scanner.web_scanner import WebScanner
        self.scanner = WebScanner(timeout=5)

    def test_initialization(self):
        """Test scanner initialization."""
        self.assertEqual(self.scanner.timeout, 5)
        self.assertTrue(self.scanner.verify_ssl)

    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with self.assertRaises(ValueError):
            self.scanner.scan("")

    def test_invalid_url_raises_error(self):
        """Test that invalid URL raises ValueError."""
        with self.assertRaises(ValueError):
            self.scanner.scan("not-a-url")

    def test_security_headers_check(self):
        """Test security header checking logic."""
        headers = {
            "Strict-Transport-Security": "max-age=31536000",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }
        findings = self.scanner._check_security_headers(headers)
        self.assertIsInstance(findings, list)

        # HSTS should be present
        hsts_finding = next(
            (f for f in findings if f.header_name == "Strict-Transport-Security"),
            None,
        )
        self.assertIsNotNone(hsts_finding)
        self.assertEqual(hsts_finding.status, "present")

        # CSP should be missing
        csp_finding = next(
            (f for f in findings if f.header_name == "Content-Security-Policy"),
            None,
        )
        self.assertIsNotNone(csp_finding)
        self.assertEqual(csp_finding.status, "missing")

    def test_header_validation_hsts_weak(self):
        """Test HSTS with weak max-age is flagged."""
        result = self.scanner._validate_header_value(
            "Strict-Transport-Security", "max-age=3600"
        )
        self.assertIsNotNone(result)
        self.assertIn("3600", result["description"])

    def test_header_validation_xframe_invalid(self):
        """Test invalid X-Frame-Options value."""
        result = self.scanner._validate_header_value(
            "X-Frame-Options", "ALLOWALL"
        )
        self.assertIsNotNone(result)

    def test_header_validation_csp_unsafe_inline(self):
        """Test CSP with unsafe-inline is flagged."""
        result = self.scanner._validate_header_value(
            "Content-Security-Policy", "default-src 'self' 'unsafe-inline'"
        )
        self.assertIsNotNone(result)
        self.assertIn("unsafe-inline", result["description"])

    def test_information_disclosure_check(self):
        """Test information disclosure header detection."""
        headers = {"Server": "Apache/2.4.41", "X-Powered-By": "PHP/7.4"}
        findings = self.scanner._check_information_disclosure(headers)
        self.assertEqual(len(findings), 2)
        self.assertTrue(any("Server" in f["header_name"] for f in findings))

    def test_security_score_calculation(self):
        """Test security score calculation."""
        from src.scanner.web_scanner import WebScanResult, HeaderFinding
        result = WebScanResult(url="https://example.com")
        result.header_findings = [
            HeaderFinding(header_name="HSTS", status="missing", severity="high"),
            HeaderFinding(header_name="CSP", status="missing", severity="high"),
        ]
        result.cookie_findings = []
        result.information_disclosure = []
        score = self.scanner._calculate_security_score(result)
        self.assertLess(score, 100)
        self.assertGreaterEqual(score, 0)


class TestDNSScanner(unittest.TestCase):
    """Test cases for the DNSScanner class."""

    def setUp(self):
        """Set up test fixtures."""
        from src.scanner.dns_scanner import DNSScanner
        self.scanner = DNSScanner(timeout=3)

    def test_initialization(self):
        """Test scanner initialization."""
        self.assertEqual(self.scanner.timeout, 3)

    def test_empty_domain_raises_error(self):
        """Test that empty domain raises ValueError."""
        with self.assertRaises(ValueError):
            self.scanner.scan("")

    def test_url_stripping(self):
        """Test that URL protocols are stripped from domain."""
        from src.scanner.dns_scanner import DNSScanResult
        # This should not raise an error
        result = self.scanner.scan("https://example.com")
        self.assertIsInstance(result, DNSScanResult)

    def test_spf_analysis_missing(self):
        """Test SPF analysis with no SPF record."""
        from src.scanner.dns_scanner import DNSRecord
        txt_records = [DNSRecord(record_type="TXT", name="test.com", value="some-other-record")]
        spf = self.scanner._analyze_spf("test.com", txt_records)
        self.assertFalse(spf.exists)
        self.assertTrue(len(spf.findings) > 0)

    def test_spf_analysis_permissive(self):
        """Test SPF analysis with +all (permissive)."""
        from src.scanner.dns_scanner import DNSRecord
        txt_records = [
            DNSRecord(record_type="TXT", name="test.com", value="v=spf1 +all")
        ]
        spf = self.scanner._analyze_spf("test.com", txt_records)
        self.assertTrue(spf.exists)
        self.assertEqual(spf.policy, "pass")
        self.assertTrue(any("allows" in str(f).lower() for f in spf.findings))

    def test_spf_analysis_strict(self):
        """Test SPF analysis with -all (strict)."""
        from src.scanner.dns_scanner import DNSRecord
        txt_records = [
            DNSRecord(record_type="TXT", name="test.com", value="v=spf1 include:_spf.google.com -all")
        ]
        spf = self.scanner._analyze_spf("test.com", txt_records)
        self.assertTrue(spf.exists)
        self.assertEqual(spf.policy, "fail")
        self.assertIn("_spf.google.com", spf.includes)

    def test_result_to_dict(self):
        """Test DNSScanResult serialization."""
        from src.scanner.dns_scanner import DNSScanResult
        result = DNSScanResult(domain="test.com")
        result_dict = result.to_dict()
        self.assertIn("domain", result_dict)
        self.assertIn("records", result_dict)
        self.assertIn("findings", result_dict)

    def test_dns_record_dataclass(self):
        """Test DNSRecord dataclass."""
        from src.scanner.dns_scanner import DNSRecord
        record = DNSRecord(
            record_type="A", name="test.com", value="1.2.3.4", ttl=300
        )
        self.assertEqual(record.record_type, "A")
        self.assertEqual(record.value, "1.2.3.4")
        self.assertEqual(record.ttl, 300)


if __name__ == "__main__":
    unittest.main()
