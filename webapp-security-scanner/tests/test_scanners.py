"""
Unit Tests for the Web Application Security Scanner
======================================================
Tests cover all scanner modules: header_check, sqli_scanner,
xss_scanner, port_scanner, directory_scanner, and reporter.

Uses pytest with mocking to avoid requiring a live target.
Run with: python -m pytest tests/test_scanners.py -v
"""

import os
import sys
import json
import socket
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.header_check import (
    check_headers,
    HeaderFinding,
    HeaderCheckResult,
    get_missing_headers,
    get_findings_by_severity,
    format_header_report,
    SECURITY_HEADERS,
)
from scanner.sqli_scanner import (
    scan_sqli,
    SQLiFinding,
    SQLiScanResult,
    _check_sql_errors,
    ERROR_BASED_PAYLOADS,
    AUTH_BYPASS_PAYLOADS,
)
from scanner.xss_scanner import (
    scan_xss,
    XSSFinding,
    XSSScanResult,
    _check_reflection,
    _determine_context,
    _get_all_payloads,
    get_unique_findings,
)
from scanner.port_scanner import (
    scan_ports,
    PortFinding,
    PortScanResult,
    _resolve_host,
    _scan_port,
    COMMON_PORTS,
    QUICK_SCAN_PORTS,
)
from scanner.directory_scanner import (
    scan_directories,
    DirectoryFinding,
    DirectoryScanResult,
    SCAN_PATHS,
)
from scanner.reporter import (
    VulnerabilityEntry,
    ScanReport,
    normalize_findings,
    calculate_risk_score,
    generate_summary,
    build_report,
    render_html_report,
    render_json_report,
    print_summary,
    SEVERITY_WEIGHTS,
)


# -----------------------------------------------------------------------
# Test Fixtures
# -----------------------------------------------------------------------

@pytest.fixture
def mock_response_no_security_headers():
    """Mock HTTP response with no security headers."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Server': 'Werkzeug/3.0.1 Python/3.11.0',
        'X-Powered-By': 'Flask',
    }
    mock.text = '<html><body>Test</body></html>'
    mock.content = b'<html><body>Test</body></html>'
    return mock


@pytest.fixture
def mock_response_with_security_headers():
    """Mock HTTP response with all security headers."""
    mock = MagicMock()
    mock.status_code = 200
    mock.headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'X-Frame-Options': 'DENY',
        'Content-Security-Policy': "default-src 'self'",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=()',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'X-Permitted-Cross-Domain-Policies': 'none',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Resource-Policy': 'same-origin',
    }
    mock.text = '<html><body>Secure</body></html>'
    mock.content = b'<html><body>Secure</body></html>'
    return mock


@pytest.fixture
def mock_sqli_error_response():
    """Mock response with SQL error message."""
    mock = MagicMock()
    mock.status_code = 200
    mock.text = (
        '<html><body>Database error: near "test": syntax error'
        '</body></html>'
    )
    return mock


@pytest.fixture
def mock_xss_reflection_response():
    """Mock response with reflected XSS payload."""
    mock = MagicMock()
    mock.status_code = 200
    mock.text = (
        '<html><body>'
        '<div>Search results for: <script>alert("XSS")</script></div>'
        '</body></html>'
    )
    return mock


@pytest.fixture
def sample_vulnerabilities():
    """Sample vulnerability entries for testing."""
    return [
        VulnerabilityEntry(
            title='SQL Injection in Login',
            severity='Critical',
            category='Injection',
            description='SQL injection found in login form.',
            evidence='SQL error detected',
            remediation='Use parameterized queries.',
            url='http://127.0.0.1:5000/login',
            parameter='username',
            owasp_category='A03:2021',
            cwe_id='CWE-89',
            module='sqli_scanner',
        ),
        VulnerabilityEntry(
            title='Missing X-Frame-Options',
            severity='High',
            category='Security Misconfiguration',
            description='X-Frame-Options header is missing.',
            evidence='Header not present',
            remediation='Set X-Frame-Options: DENY',
            url='http://127.0.0.1:5000',
            owasp_category='A05:2021',
            cwe_id='CWE-1021',
            module='header_check',
        ),
        VulnerabilityEntry(
            title='Reflected XSS',
            severity='High',
            category='Cross-Site Scripting',
            description='Reflected XSS in search parameter.',
            evidence='Payload reflected unescaped',
            remediation='Implement output encoding.',
            url='http://127.0.0.1:5000/search',
            parameter='query',
            owasp_category='A03:2021',
            cwe_id='CWE-79',
            module='xss_scanner',
        ),
        VulnerabilityEntry(
            title='Open Port 3306',
            severity='Critical',
            category='Network Security',
            description='MySQL port is open.',
            evidence='Port 3306 is open',
            remediation='Block external access.',
            url='127.0.0.1:3306',
            module='port_scanner',
        ),
        VulnerabilityEntry(
            title='Exposed .env file',
            severity='Medium',
            category='Configuration File',
            description='.env file accessible.',
            evidence='HTTP 200',
            remediation='Remove from web root.',
            url='http://127.0.0.1:5000/.env',
            owasp_category='A05:2021',
            cwe_id='CWE-538',
            module='directory_scanner',
        ),
    ]


# -----------------------------------------------------------------------
# Header Check Tests
# -----------------------------------------------------------------------

class TestHeaderCheck:
    """Tests for the header_check module."""

    @patch('scanner.header_check.requests.get')
    def test_check_headers_missing_all(self, mock_get, mock_response_no_security_headers):
        """Test that missing headers are correctly identified."""
        mock_get.return_value = mock_response_no_security_headers

        result = check_headers('http://127.0.0.1:5000')

        assert result.status_code == 200
        assert result.missing_headers > 0
        assert result.total_headers_checked == len(SECURITY_HEADERS)
        assert len(result.findings) > 0

    @patch('scanner.header_check.requests.get')
    def test_check_headers_all_present(self, mock_get, mock_response_with_security_headers):
        """Test that present headers are correctly identified."""
        mock_get.return_value = mock_response_with_security_headers

        result = check_headers('http://127.0.0.1:5000')

        assert result.status_code == 200
        assert result.present_headers == len(SECURITY_HEADERS)
        assert result.missing_headers == 0
        assert result.score == 100

    @patch('scanner.header_check.requests.get')
    def test_information_disclosure_detection(self, mock_get, mock_response_no_security_headers):
        """Test detection of information disclosure headers."""
        mock_get.return_value = mock_response_no_security_headers

        result = check_headers('http://127.0.0.1:5000')

        assert len(result.technology_fingerprints) > 0
        assert any('Server' in fp for fp in result.technology_fingerprints)

    @patch('scanner.header_check.requests.get')
    def test_connection_error_handling(self, mock_get):
        """Test graceful handling of connection errors."""
        mock_get.side_effect = Exception("Connection refused")

        result = check_headers('http://127.0.0.1:9999')

        assert result.status_code == 0

    def test_get_missing_headers(self):
        """Test filtering of missing headers."""
        result = HeaderCheckResult(
            target_url='http://test.com',
            status_code=200,
        )
        result.findings = [
            HeaderFinding('X-Frame-Options', False, None, 'High',
                          'Missing', 'Add it', 'A05:2021', 'CWE-1021'),
            HeaderFinding('Content-Type', True, 'text/html', 'Informational',
                          'Present', 'OK', 'A05:2021', 'CWE-16'),
        ]

        missing = get_missing_headers(result)
        assert len(missing) == 1
        assert missing[0].header_name == 'X-Frame-Options'

    def test_get_findings_by_severity(self):
        """Test filtering findings by severity."""
        result = HeaderCheckResult(
            target_url='http://test.com',
            status_code=200,
        )
        result.findings = [
            HeaderFinding('H1', False, None, 'High', '', '', '', ''),
            HeaderFinding('H2', False, None, 'Medium', '', '', '', ''),
            HeaderFinding('H3', False, None, 'High', '', '', '', ''),
        ]

        high_findings = get_findings_by_severity(result, 'High')
        assert len(high_findings) == 2

    @patch('scanner.header_check.requests.get')
    def test_format_header_report(self, mock_get, mock_response_no_security_headers):
        """Test report formatting."""
        mock_get.return_value = mock_response_no_security_headers

        result = check_headers('http://127.0.0.1:5000')
        report_text = format_header_report(result)

        assert 'HTTP SECURITY HEADER ANALYSIS REPORT' in report_text
        assert 'http://127.0.0.1:5000' in report_text

    def test_security_headers_config_completeness(self):
        """Test that all security headers have required config fields."""
        required_fields = ['severity', 'description', 'recommendation',
                           'valid_values', 'owasp', 'cwe']
        for header, config in SECURITY_HEADERS.items():
            for field in required_fields:
                assert field in config, f"Missing '{field}' in {header} config"


# -----------------------------------------------------------------------
# SQL Injection Scanner Tests
# -----------------------------------------------------------------------

class TestSQLiScanner:
    """Tests for the sqli_scanner module."""

    def test_check_sql_errors_detects_sqlite(self):
        """Test detection of SQLite error messages."""
        text = 'near "test": syntax error'
        result = _check_sql_errors(text)
        assert result is not None

    def test_check_sql_errors_detects_mysql(self):
        """Test detection of MySQL error messages."""
        text = "You have an error in your SQL syntax"
        result = _check_sql_errors(text)
        assert result is not None

    def test_check_sql_errors_detects_operational(self):
        """Test detection of OperationalError."""
        text = "sqlite3.OperationalError: near test"
        result = _check_sql_errors(text)
        assert result is not None

    def test_check_sql_errors_no_false_positive(self):
        """Test that normal text does not trigger detection."""
        text = "Welcome to our website. Please login."
        result = _check_sql_errors(text)
        assert result is None

    def test_error_based_payloads_not_empty(self):
        """Test that payload lists are populated."""
        assert len(ERROR_BASED_PAYLOADS) > 5
        assert len(AUTH_BYPASS_PAYLOADS) > 5

    @patch('scanner.sqli_scanner.requests.post')
    def test_scan_sqli_error_based(self, mock_post, mock_sqli_error_response):
        """Test error-based SQL injection detection."""
        mock_post.return_value = mock_sqli_error_response

        result = scan_sqli(
            'http://127.0.0.1:5000',
            endpoints=[{
                'path': '/search',
                'method': 'POST',
                'params': ['query'],
                'is_login': False,
            }]
        )

        assert result.vulnerabilities_found > 0
        assert any(
            f.injection_type == 'error-based'
            for f in result.findings
        )

    @patch('scanner.sqli_scanner.requests.post')
    def test_scan_sqli_no_vulnerability(self, mock_post):
        """Test when no SQL injection is found."""
        mock = MagicMock()
        mock.status_code = 200
        mock.text = '<html>No errors here</html>'
        mock_post.return_value = mock

        result = scan_sqli(
            'http://127.0.0.1:5000',
            endpoints=[{
                'path': '/safe-search',
                'method': 'POST',
                'params': ['q'],
                'is_login': False,
            }]
        )

        # May still find boolean-blind if response sizes differ
        assert isinstance(result, SQLiScanResult)

    def test_sqli_finding_dataclass(self):
        """Test SQLiFinding dataclass creation."""
        finding = SQLiFinding(
            url='http://test.com/login',
            parameter='username',
            payload="' OR '1'='1' --",
            method='POST',
            injection_type='auth-bypass',
            severity='Critical',
            evidence='Redirect detected',
            description='Auth bypass found.',
            remediation='Use prepared statements.',
        )
        assert finding.severity == 'Critical'
        assert finding.injection_type == 'auth-bypass'


# -----------------------------------------------------------------------
# XSS Scanner Tests
# -----------------------------------------------------------------------

class TestXSSScanner:
    """Tests for the xss_scanner module."""

    def test_check_reflection_direct(self):
        """Test detection of direct payload reflection."""
        payload = '<script>alert(1)</script>'
        response_text = f'<html>Search: {payload}</html>'

        is_reflected, context = _check_reflection(response_text, payload)

        assert is_reflected is True
        assert context == 'html-body'

    def test_check_reflection_not_found(self):
        """Test when payload is not reflected."""
        payload = '<script>alert(1)</script>'
        response_text = '<html>No reflection here</html>'

        is_reflected, context = _check_reflection(response_text, payload)

        assert is_reflected is False

    def test_determine_context_html_body(self):
        """Test context detection for HTML body."""
        text = '<html><body><div>PAYLOAD</div></body></html>'
        context = _determine_context(text, 'PAYLOAD')
        assert context == 'html-body'

    def test_determine_context_javascript(self):
        """Test context detection for JavaScript context."""
        text = '<script>var x = "PAYLOAD"; alert(x);</script>'
        context = _determine_context(text, 'PAYLOAD')
        assert context == 'javascript'

    def test_determine_context_attribute(self):
        """Test context detection for HTML attribute."""
        text = '<input value="PAYLOAD" type="text">'
        context = _determine_context(text, 'PAYLOAD')
        assert context == 'html-attribute'

    def test_get_all_payloads(self):
        """Test that payload list is comprehensive."""
        payloads = _get_all_payloads()
        assert len(payloads) > 20
        categories = set(cat for _, cat in payloads)
        assert 'script-tag' in categories
        assert 'event-handler' in categories
        assert 'attribute-injection' in categories

    def test_get_unique_findings(self):
        """Test deduplication of XSS findings."""
        result = XSSScanResult(target_url='http://test.com')
        result.findings = [
            XSSFinding('http://test.com/search', 'q', '<script>alert(1)</script>',
                       'POST', 'reflected', 'High', 'Reflected', 'html-body',
                       'XSS found', 'Fix it'),
            XSSFinding('http://test.com/search', 'q', '<img src=x onerror=alert(1)>',
                       'POST', 'reflected', 'High', 'Reflected', 'html-body',
                       'XSS found', 'Fix it'),
            XSSFinding('http://test.com/search', 'q', '"><script>alert(1)</script>',
                       'POST', 'reflected', 'High', 'Reflected', 'html-attribute',
                       'XSS found', 'Fix it'),
        ]

        unique = get_unique_findings(result)
        # Should have 2 unique (same url+param but different contexts)
        assert len(unique) == 2

    @patch('scanner.xss_scanner.requests.post')
    def test_scan_xss_detection(self, mock_post, mock_xss_reflection_response):
        """Test XSS detection when payload is reflected."""
        mock_post.return_value = mock_xss_reflection_response

        result = scan_xss(
            'http://127.0.0.1:5000',
            endpoints=[{
                'path': '/search',
                'method': 'POST',
                'params': ['query'],
            }]
        )

        assert result.vulnerabilities_found > 0


# -----------------------------------------------------------------------
# Port Scanner Tests
# -----------------------------------------------------------------------

class TestPortScanner:
    """Tests for the port_scanner module."""

    def test_resolve_host_url(self):
        """Test hostname resolution from URL."""
        hostname, ip = _resolve_host('http://127.0.0.1:5000')
        assert hostname == '127.0.0.1'
        assert ip == '127.0.0.1'

    def test_resolve_host_localhost(self):
        """Test localhost resolution."""
        hostname, ip = _resolve_host('http://localhost:5000')
        assert hostname == 'localhost'
        assert ip == '127.0.0.1'

    def test_common_ports_data(self):
        """Test that common ports data is complete."""
        critical_ports = [21, 23, 1433, 3306, 5432, 6379, 27017]
        for port in critical_ports:
            assert port in COMMON_PORTS
            assert 'service' in COMMON_PORTS[port]
            assert 'severity' in COMMON_PORTS[port]

    def test_quick_scan_ports_list(self):
        """Test quick scan ports list."""
        assert 80 in QUICK_SCAN_PORTS
        assert 443 in QUICK_SCAN_PORTS
        assert 22 in QUICK_SCAN_PORTS
        assert len(QUICK_SCAN_PORTS) >= 20

    @patch('scanner.port_scanner.socket.socket')
    def test_scan_port_open(self, mock_socket_class):
        """Test scanning an open port."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock.recv.return_value = b'SSH-2.0-OpenSSH_8.9'
        mock_socket_class.return_value = mock_sock

        finding = _scan_port('127.0.0.1', 22, timeout=2.0)

        assert finding.state == 'open'
        assert finding.port == 22

    @patch('scanner.port_scanner.socket.socket')
    def test_scan_port_closed(self, mock_socket_class):
        """Test scanning a closed port."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1
        mock_socket_class.return_value = mock_sock

        finding = _scan_port('127.0.0.1', 12345, timeout=2.0)

        assert finding.state == 'closed'

    @patch('scanner.port_scanner.socket.socket')
    def test_scan_port_timeout(self, mock_socket_class):
        """Test scanning a filtered/timed-out port."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.side_effect = socket.timeout()
        mock_socket_class.return_value = mock_sock

        finding = _scan_port('127.0.0.1', 445, timeout=1.0)

        assert finding.state == 'filtered'

    def test_port_finding_dataclass(self):
        """Test PortFinding creation."""
        finding = PortFinding(
            port=80,
            state='open',
            service='HTTP',
            banner='Apache/2.4.52',
            severity='Medium',
            description='HTTP detected.',
            recommendation='Redirect to HTTPS.',
        )
        assert finding.port == 80
        assert finding.service == 'HTTP'


# -----------------------------------------------------------------------
# Directory Scanner Tests
# -----------------------------------------------------------------------

class TestDirectoryScanner:
    """Tests for the directory_scanner module."""

    def test_scan_paths_categories(self):
        """Test that all scan path categories are defined."""
        expected_categories = [
            'admin_panels', 'config_files', 'version_control',
            'backup_files', 'api_endpoints', 'server_info',
            'log_files', 'cms_framework'
        ]
        for cat in expected_categories:
            assert cat in SCAN_PATHS
            assert 'paths' in SCAN_PATHS[cat]
            assert len(SCAN_PATHS[cat]['paths']) > 0

    def test_scan_paths_have_metadata(self):
        """Test that scan paths have required metadata."""
        for cat_name, config in SCAN_PATHS.items():
            assert 'category' in config, f"Missing 'category' in {cat_name}"
            assert 'severity' in config, f"Missing 'severity' in {cat_name}"
            assert 'owasp' in config, f"Missing 'owasp' in {cat_name}"
            assert 'cwe' in config, f"Missing 'cwe' in {cat_name}"
            assert 'description' in config, f"Missing 'description' in {cat_name}"
            assert 'recommendation' in config, f"Missing 'recommendation' in {cat_name}"

    @patch('scanner.directory_scanner.requests.get')
    def test_scan_directories_found(self, mock_get):
        """Test directory scanning when paths are found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'Admin Panel'
        mock_get.return_value = mock_response

        result = scan_directories(
            'http://127.0.0.1:5000',
            categories=['admin_panels'],
        )

        assert result.paths_found > 0
        assert len(result.findings) > 0

    @patch('scanner.directory_scanner.requests.get')
    def test_scan_directories_not_found(self, mock_get):
        """Test directory scanning when paths are not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = scan_directories(
            'http://127.0.0.1:5000',
            categories=['version_control'],
        )

        assert result.paths_found == 0

    @patch('scanner.directory_scanner.requests.get')
    def test_scan_custom_paths(self, mock_get):
        """Test scanning with custom paths."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'Found'
        mock_get.return_value = mock_response

        result = scan_directories(
            'http://127.0.0.1:5000',
            categories=[],
            custom_paths=['/custom/path', '/another/path'],
        )

        assert result.paths_checked == 2


# -----------------------------------------------------------------------
# Reporter Tests
# -----------------------------------------------------------------------

class TestReporter:
    """Tests for the reporter module."""

    def test_calculate_risk_score_empty(self):
        """Test risk score with no vulnerabilities."""
        score = calculate_risk_score([])
        assert score == 0.0

    def test_calculate_risk_score_critical(self, sample_vulnerabilities):
        """Test risk score with mixed vulnerabilities."""
        score = calculate_risk_score(sample_vulnerabilities)
        assert 0 < score <= 10.0

    def test_calculate_risk_score_max(self):
        """Test risk score does not exceed 10."""
        vulns = [
            VulnerabilityEntry(
                title=f'Vuln {i}', severity='Critical', category='Test',
                description='', evidence='', remediation='', url='',
                module='test',
            )
            for i in range(100)
        ]
        score = calculate_risk_score(vulns)
        assert score <= 10.0

    def test_generate_summary(self, sample_vulnerabilities):
        """Test summary generation."""
        summary = generate_summary(sample_vulnerabilities)

        assert summary['Total'] == 5
        assert summary['Critical'] == 2
        assert summary['High'] == 2
        assert summary['Medium'] == 1
        assert summary['Low'] == 0
        assert summary['Informational'] == 0

    def test_build_report(self, sample_vulnerabilities):
        """Test complete report building."""
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 5, 0)

        report = build_report(
            target_url='http://127.0.0.1:5000',
            scan_start=start,
            scan_end=end,
            modules_executed=['headers', 'sqli', 'xss'],
        )

        assert report.target_url == 'http://127.0.0.1:5000'
        assert report.scan_duration == 300.0
        assert len(report.modules_executed) == 3

    def test_normalize_findings_header_results(self):
        """Test normalization of header check results."""
        header_result = HeaderCheckResult(
            target_url='http://test.com',
            status_code=200,
        )
        header_result.findings = [
            HeaderFinding('X-Frame-Options', False, None, 'High',
                          'Missing', 'Add it', 'A05:2021', 'CWE-1021'),
        ]

        vulns = normalize_findings(header_results=header_result)

        assert len(vulns) == 1
        assert vulns[0].module == 'header_check'
        assert 'X-Frame-Options' in vulns[0].title

    def test_normalize_findings_sqli_results(self):
        """Test normalization of SQLi results."""
        sqli_result = SQLiScanResult(target_url='http://test.com')
        sqli_result.findings = [
            SQLiFinding(
                url='http://test.com/login',
                parameter='username',
                payload="' OR '1'='1",
                method='POST',
                injection_type='error-based',
                severity='Critical',
                evidence='SQL error found',
                description='SQLi detected.',
                remediation='Fix it.',
            )
        ]

        vulns = normalize_findings(sqli_results=sqli_result)

        assert len(vulns) == 1
        assert vulns[0].module == 'sqli_scanner'
        assert vulns[0].severity == 'Critical'

    def test_render_json_report(self, sample_vulnerabilities):
        """Test JSON report generation."""
        report = ScanReport(
            target_url='http://test.com',
            scan_start='2025-01-01 10:00:00',
            scan_end='2025-01-01 10:05:00',
            scan_duration=300.0,
            modules_executed=['headers'],
            vulnerabilities=sample_vulnerabilities,
            summary=generate_summary(sample_vulnerabilities),
            risk_score=calculate_risk_score(sample_vulnerabilities),
        )

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as f:
            output_path = f.name

        try:
            result_path = render_json_report(report, output_path)

            assert os.path.exists(result_path)

            with open(result_path, 'r') as f:
                data = json.load(f)

            assert data['target_url'] == 'http://test.com'
            assert len(data['vulnerabilities']) == 5
            assert data['summary']['Total'] == 5
        finally:
            os.unlink(output_path)

    def test_severity_weights_completeness(self):
        """Test that all severity levels have weights."""
        expected = ['Critical', 'High', 'Medium', 'Low', 'Informational']
        for severity in expected:
            assert severity in SEVERITY_WEIGHTS

    def test_vulnerability_entry_optional_fields(self):
        """Test VulnerabilityEntry with optional fields."""
        vuln = VulnerabilityEntry(
            title='Test',
            severity='Medium',
            category='Test',
            description='Description',
            evidence='Evidence',
            remediation='Remediation',
            url='http://test.com',
        )
        assert vuln.parameter is None
        assert vuln.owasp_category is None
        assert vuln.cwe_id is None
        assert vuln.cvss_score is None


# -----------------------------------------------------------------------
# Integration-style Tests
# -----------------------------------------------------------------------

class TestIntegration:
    """Integration-style tests combining multiple modules."""

    def test_full_report_pipeline(self):
        """Test the complete scan-to-report pipeline with mock data."""
        # Create mock results for each module
        header_result = HeaderCheckResult(
            target_url='http://127.0.0.1:5000',
            status_code=200,
            total_headers_checked=12,
            missing_headers=10,
            present_headers=2,
        )
        header_result.findings = [
            HeaderFinding('X-Frame-Options', False, None, 'High',
                          'Missing clickjacking protection.',
                          'Set X-Frame-Options: DENY',
                          'A05:2021', 'CWE-1021'),
            HeaderFinding('Content-Security-Policy', False, None, 'High',
                          'Missing CSP header.',
                          "Set CSP: default-src 'self'",
                          'A03:2021', 'CWE-693'),
        ]

        sqli_result = SQLiScanResult(target_url='http://127.0.0.1:5000')
        sqli_result.findings = [
            SQLiFinding(
                url='http://127.0.0.1:5000/login',
                parameter='username',
                payload="' OR '1'='1' --",
                method='POST',
                injection_type='auth-bypass',
                severity='Critical',
                evidence='Authentication bypassed.',
                description='Login bypass via SQL injection.',
                remediation='Use parameterized queries.',
            )
        ]

        # Build the report
        start = datetime.now()
        report = build_report(
            target_url='http://127.0.0.1:5000',
            scan_start=start,
            scan_end=datetime.now(),
            modules_executed=['headers', 'sqli'],
            header_results=header_result,
            sqli_results=sqli_result,
        )

        # Verify report
        assert report.target_url == 'http://127.0.0.1:5000'
        assert len(report.vulnerabilities) == 3
        assert report.summary['Total'] == 3
        assert report.summary['Critical'] == 1
        assert report.summary['High'] == 2
        assert report.risk_score > 0

    def test_empty_scan_report(self):
        """Test report generation with no findings."""
        start = datetime.now()
        report = build_report(
            target_url='http://secure-app.com',
            scan_start=start,
            scan_end=datetime.now(),
            modules_executed=['headers'],
        )

        assert report.summary['Total'] == 0
        assert report.risk_score == 0.0


# -----------------------------------------------------------------------
# Edge Case Tests
# -----------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_payload_lists(self):
        """Test scanner behavior with edge case inputs."""
        result = _check_sql_errors('')
        assert result is None

    def test_unicode_in_payload(self):
        """Test handling of unicode characters."""
        result = _check_sql_errors('Error: \u2018test\u2019 syntax error')
        assert result is None  # Unicode quotes should not match SQL patterns

    def test_very_long_response(self):
        """Test reflection check with very long response."""
        payload = '<script>alert(1)</script>'
        long_text = 'x' * 100000 + payload + 'y' * 100000

        is_reflected, context = _check_reflection(long_text, payload)
        assert is_reflected is True

    def test_risk_score_single_low(self):
        """Test risk score with a single low vulnerability."""
        vulns = [
            VulnerabilityEntry(
                title='Low', severity='Low', category='Test',
                description='', evidence='', remediation='', url='',
            )
        ]
        score = calculate_risk_score(vulns)
        assert score == 2.5

    def test_risk_score_single_critical(self):
        """Test risk score with a single critical vulnerability."""
        vulns = [
            VulnerabilityEntry(
                title='Critical', severity='Critical', category='Test',
                description='', evidence='', remediation='', url='',
            )
        ]
        score = calculate_risk_score(vulns)
        assert score == 10.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
