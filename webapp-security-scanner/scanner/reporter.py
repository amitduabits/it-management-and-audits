"""
Vulnerability Report Generator
==================================
Generates professional HTML vulnerability reports with severity
classification, OWASP mapping, and remediation guidance.

Report Features:
- Executive summary with vulnerability statistics
- Severity distribution chart (Critical, High, Medium, Low, Informational)
- Detailed findings with evidence and remediation
- OWASP Top 10 cross-reference mapping
- Scan metadata (target, duration, modules, timestamps)
- Risk scoring and prioritized recommendations
- Export to HTML format

ETHICAL USE ONLY: Reports should be shared only with authorized stakeholders.
"""

import os
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclass
class VulnerabilityEntry:
    """Normalized vulnerability entry for reporting."""
    title: str
    severity: str
    category: str
    description: str
    evidence: str
    remediation: str
    url: str
    parameter: Optional[str] = None
    owasp_category: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    module: str = ''
    raw_data: Optional[Dict] = None


@dataclass
class ScanReport:
    """Complete scan report data structure."""
    target_url: str
    scan_start: str
    scan_end: str
    scan_duration: float
    scanner_version: str = '1.0.0'
    modules_executed: List[str] = field(default_factory=list)
    vulnerabilities: List[VulnerabilityEntry] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    risk_score: float = 0.0
    total_requests: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# Severity weights for risk scoring
SEVERITY_WEIGHTS = {
    'Critical': 10.0,
    'High': 7.5,
    'Medium': 5.0,
    'Low': 2.5,
    'Informational': 0.5,
}

SEVERITY_COLORS = {
    'Critical': '#dc3545',
    'High': '#e94560',
    'Medium': '#ffa502',
    'Low': '#2ed573',
    'Informational': '#3498db',
}


def normalize_findings(
    header_results=None,
    sqli_results=None,
    xss_results=None,
    port_results=None,
    directory_results=None
) -> List[VulnerabilityEntry]:
    """
    Normalize findings from all scanner modules into a unified format.

    Args:
        header_results: HeaderCheckResult from header_check module
        sqli_results: SQLiScanResult from sqli_scanner module
        xss_results: XSSScanResult from xss_scanner module
        port_results: PortScanResult from port_scanner module
        directory_results: DirectoryScanResult from directory_scanner module

    Returns:
        List of normalized VulnerabilityEntry objects
    """
    vulnerabilities = []

    # Normalize header findings
    if header_results:
        for finding in header_results.findings:
            if finding.severity != 'Informational' or not finding.present:
                if not finding.present:
                    vulnerabilities.append(VulnerabilityEntry(
                        title=f'Missing Security Header: {finding.header_name}',
                        severity=finding.severity,
                        category='Security Misconfiguration',
                        description=finding.description,
                        evidence=f'Header not present in HTTP response',
                        remediation=finding.recommendation,
                        url=header_results.target_url,
                        owasp_category=finding.owasp_category,
                        cwe_id=finding.cwe_id,
                        module='header_check',
                    ))
                elif finding.severity != 'Informational':
                    # Information disclosure headers
                    vulnerabilities.append(VulnerabilityEntry(
                        title=f'Information Disclosure: {finding.header_name}',
                        severity=finding.severity,
                        category='Information Disclosure',
                        description=finding.description,
                        evidence=f'Header value: {finding.value}',
                        remediation=finding.recommendation,
                        url=header_results.target_url,
                        owasp_category=finding.owasp_category,
                        cwe_id=finding.cwe_id,
                        module='header_check',
                    ))

    # Normalize SQL injection findings
    if sqli_results:
        for finding in sqli_results.findings:
            vulnerabilities.append(VulnerabilityEntry(
                title=f'SQL Injection ({finding.injection_type}): {finding.parameter}',
                severity=finding.severity,
                category='Injection',
                description=finding.description,
                evidence=finding.evidence,
                remediation=finding.remediation,
                url=finding.url,
                parameter=finding.parameter,
                owasp_category=finding.owasp_category,
                cwe_id=finding.cwe_id,
                module='sqli_scanner',
                raw_data={'payload': finding.payload, 'method': finding.method},
            ))

    # Normalize XSS findings
    if xss_results:
        for finding in xss_results.findings:
            vulnerabilities.append(VulnerabilityEntry(
                title=f'Cross-Site Scripting ({finding.xss_type}): {finding.parameter}',
                severity=finding.severity,
                category='Cross-Site Scripting',
                description=finding.description,
                evidence=finding.evidence,
                remediation=finding.remediation,
                url=finding.url,
                parameter=finding.parameter,
                owasp_category=finding.owasp_category,
                cwe_id=finding.cwe_id,
                module='xss_scanner',
                raw_data={'payload': finding.payload, 'context': finding.context},
            ))

    # Normalize port scan findings
    if port_results:
        for finding in port_results.findings:
            if finding.state == 'open' and finding.severity not in ('Informational',):
                vulnerabilities.append(VulnerabilityEntry(
                    title=f'Open Port: {finding.port}/tcp ({finding.service})',
                    severity=finding.severity,
                    category='Network Security',
                    description=finding.description,
                    evidence=(
                        f'Port {finding.port}/tcp is open. '
                        f'Banner: {finding.banner or "N/A"}'
                    ),
                    remediation=finding.recommendation,
                    url=f'{port_results.target_host}:{finding.port}',
                    module='port_scanner',
                ))

    # Normalize directory scan findings
    if directory_results:
        for finding in directory_results.findings:
            vulnerabilities.append(VulnerabilityEntry(
                title=f'Exposed {finding.category}: {finding.path}',
                severity=finding.severity,
                category=finding.category,
                description=finding.description,
                evidence=(
                    f'HTTP {finding.status_code} response for {finding.url} '
                    f'(Content-Length: {finding.content_length} bytes)'
                ),
                remediation=finding.recommendation,
                url=finding.url,
                owasp_category=finding.owasp_category,
                cwe_id=finding.cwe_id,
                module='directory_scanner',
            ))

    # Sort by severity
    severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Informational': 4}
    vulnerabilities.sort(key=lambda v: severity_order.get(v.severity, 5))

    return vulnerabilities


def calculate_risk_score(vulnerabilities: List[VulnerabilityEntry]) -> float:
    """
    Calculate an overall risk score based on vulnerability findings.

    Score range: 0.0 (no risk) to 10.0 (critical risk)
    """
    if not vulnerabilities:
        return 0.0

    total_weight = sum(
        SEVERITY_WEIGHTS.get(v.severity, 0) for v in vulnerabilities
    )

    # Normalize to 0-10 scale with diminishing returns
    # More vulnerabilities increase the score but with diminishing impact
    max_theoretical = len(vulnerabilities) * 10.0
    normalized = (total_weight / max_theoretical) * 10.0 if max_theoretical > 0 else 0.0

    # Cap at 10.0
    return min(round(normalized, 1), 10.0)


def generate_summary(vulnerabilities: List[VulnerabilityEntry]) -> Dict[str, int]:
    """Generate a severity count summary."""
    summary = {
        'Critical': 0,
        'High': 0,
        'Medium': 0,
        'Low': 0,
        'Informational': 0,
        'Total': len(vulnerabilities),
    }

    for vuln in vulnerabilities:
        if vuln.severity in summary:
            summary[vuln.severity] += 1

    return summary


def build_report(
    target_url: str,
    scan_start: datetime,
    scan_end: datetime,
    modules_executed: List[str],
    header_results=None,
    sqli_results=None,
    xss_results=None,
    port_results=None,
    directory_results=None,
    total_requests: int = 0
) -> ScanReport:
    """
    Build a complete scan report from all module results.

    Args:
        target_url: The scanned target URL
        scan_start: Scan start timestamp
        scan_end: Scan end timestamp
        modules_executed: List of module names that were executed
        header_results: Results from header check module
        sqli_results: Results from SQL injection scanner
        xss_results: Results from XSS scanner
        port_results: Results from port scanner
        directory_results: Results from directory scanner
        total_requests: Total HTTP requests made during the scan

    Returns:
        ScanReport object
    """
    vulnerabilities = normalize_findings(
        header_results=header_results,
        sqli_results=sqli_results,
        xss_results=xss_results,
        port_results=port_results,
        directory_results=directory_results,
    )

    summary = generate_summary(vulnerabilities)
    risk_score = calculate_risk_score(vulnerabilities)
    duration = (scan_end - scan_start).total_seconds()

    report = ScanReport(
        target_url=target_url,
        scan_start=scan_start.strftime('%Y-%m-%d %H:%M:%S'),
        scan_end=scan_end.strftime('%Y-%m-%d %H:%M:%S'),
        scan_duration=round(duration, 2),
        modules_executed=modules_executed,
        vulnerabilities=vulnerabilities,
        summary=summary,
        risk_score=risk_score,
        total_requests=total_requests,
        metadata={
            'scanner_name': 'Web Application Security Scanner',
            'scanner_version': '1.0.0',
            'target_url': target_url,
            'report_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        },
    )

    return report


def render_html_report(
    report: ScanReport,
    output_path: str,
    template_dir: Optional[str] = None
) -> str:
    """
    Render the scan report as an HTML file using the Jinja2 template.

    Args:
        report: ScanReport object
        output_path: Path to save the HTML report
        template_dir: Directory containing the report template

    Returns:
        Path to the generated report file
    """
    if template_dir is None:
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'reports'
        )

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html']),
    )

    template = env.get_template('template.html')

    # Prepare template data
    template_data = {
        'report': report,
        'vulnerabilities': report.vulnerabilities,
        'summary': report.summary,
        'risk_score': report.risk_score,
        'severity_colors': SEVERITY_COLORS,
        'scan_start': report.scan_start,
        'scan_end': report.scan_end,
        'scan_duration': report.scan_duration,
        'target_url': report.target_url,
        'modules_executed': report.modules_executed,
        'total_requests': report.total_requests,
        'metadata': report.metadata,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    html_content = template.render(**template_data)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[+] HTML report saved to: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)


def render_json_report(report: ScanReport, output_path: str) -> str:
    """
    Export the scan report as JSON.

    Args:
        report: ScanReport object
        output_path: Path to save the JSON report

    Returns:
        Path to the generated report file
    """
    # Convert to serializable dict
    report_dict = {
        'metadata': report.metadata,
        'target_url': report.target_url,
        'scan_start': report.scan_start,
        'scan_end': report.scan_end,
        'scan_duration': report.scan_duration,
        'modules_executed': report.modules_executed,
        'risk_score': report.risk_score,
        'summary': report.summary,
        'total_requests': report.total_requests,
        'vulnerabilities': [],
    }

    for vuln in report.vulnerabilities:
        vuln_dict = {
            'title': vuln.title,
            'severity': vuln.severity,
            'category': vuln.category,
            'description': vuln.description,
            'evidence': vuln.evidence,
            'remediation': vuln.remediation,
            'url': vuln.url,
            'parameter': vuln.parameter,
            'owasp_category': vuln.owasp_category,
            'cwe_id': vuln.cwe_id,
            'module': vuln.module,
        }
        report_dict['vulnerabilities'].append(vuln_dict)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    print(f"[+] JSON report saved to: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)


def print_summary(report: ScanReport):
    """Print a formatted summary to the console."""
    print()
    print("=" * 70)
    print("  SCAN SUMMARY")
    print("=" * 70)
    print(f"  Target:     {report.target_url}")
    print(f"  Duration:   {report.scan_duration}s")
    print(f"  Modules:    {', '.join(report.modules_executed)}")
    print(f"  Risk Score: {report.risk_score}/10.0")
    print()
    print("  VULNERABILITY SUMMARY:")
    print(f"    Critical:      {report.summary.get('Critical', 0)}")
    print(f"    High:          {report.summary.get('High', 0)}")
    print(f"    Medium:        {report.summary.get('Medium', 0)}")
    print(f"    Low:           {report.summary.get('Low', 0)}")
    print(f"    Informational: {report.summary.get('Informational', 0)}")
    print(f"    Total:         {report.summary.get('Total', 0)}")
    print("=" * 70)

    # Risk assessment
    if report.risk_score >= 8.0:
        risk_level = "CRITICAL - Immediate action required"
    elif report.risk_score >= 6.0:
        risk_level = "HIGH - Address vulnerabilities promptly"
    elif report.risk_score >= 4.0:
        risk_level = "MEDIUM - Plan remediation efforts"
    elif report.risk_score >= 2.0:
        risk_level = "LOW - Monitor and address in regular cycle"
    else:
        risk_level = "MINIMAL - Continue regular security practices"

    print(f"  RISK LEVEL: {risk_level}")
    print("=" * 70)
