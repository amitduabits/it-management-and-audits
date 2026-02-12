"""
HTTP Security Header Analyzer
================================
Checks web application responses for missing or misconfigured
security headers based on OWASP and industry best practices.

Analyzes the following headers:
- X-Frame-Options: Clickjacking protection
- Content-Security-Policy: XSS and injection mitigation
- Strict-Transport-Security: HTTPS enforcement (HSTS)
- X-Content-Type-Options: MIME type sniffing prevention
- X-XSS-Protection: Legacy browser XSS filter
- Referrer-Policy: Referrer information leakage control
- Permissions-Policy: Browser feature restrictions
- Cache-Control: Sensitive data caching prevention
- X-Permitted-Cross-Domain-Policies: Flash/PDF cross-domain control
- Cross-Origin-Embedder-Policy: Cross-origin embedding restrictions
- Cross-Origin-Opener-Policy: Cross-origin window references
- Cross-Origin-Resource-Policy: Cross-origin resource loading

ETHICAL USE ONLY: Only scan targets you own or have written authorization to test.
"""

import requests
from urllib.parse import urlparse
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class HeaderFinding:
    """Represents a single header check finding."""
    header_name: str
    present: bool
    value: Optional[str]
    severity: str  # Critical, High, Medium, Low, Informational
    description: str
    recommendation: str
    owasp_category: str
    cwe_id: str


@dataclass
class HeaderCheckResult:
    """Complete result of a header security check."""
    target_url: str
    status_code: int
    findings: List[HeaderFinding] = field(default_factory=list)
    score: int = 0  # 0-100 security score
    total_headers_checked: int = 0
    missing_headers: int = 0
    present_headers: int = 0
    server_header: Optional[str] = None
    technology_fingerprints: List[str] = field(default_factory=list)


# Security headers configuration with metadata
SECURITY_HEADERS = {
    'X-Frame-Options': {
        'severity': 'High',
        'description': (
            'X-Frame-Options prevents the page from being loaded in an iframe, '
            'protecting against clickjacking attacks. Without this header, an '
            'attacker can embed the page in a malicious site and trick users '
            'into performing unintended actions.'
        ),
        'recommendation': (
            'Set X-Frame-Options to DENY or SAMEORIGIN. '
            'Example: X-Frame-Options: DENY'
        ),
        'valid_values': ['DENY', 'SAMEORIGIN'],
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-1021',
    },
    'Content-Security-Policy': {
        'severity': 'High',
        'description': (
            'Content-Security-Policy (CSP) controls which resources the browser '
            'is allowed to load, providing a strong defense against XSS, data '
            'injection, and other code injection attacks. Missing CSP leaves '
            'the application vulnerable to script injection.'
        ),
        'recommendation': (
            "Set a restrictive CSP. Minimum: Content-Security-Policy: default-src 'self'. "
            "Avoid 'unsafe-inline' and 'unsafe-eval' directives."
        ),
        'valid_values': None,  # Complex header, needs specific validation
        'owasp': 'A03:2021 - Injection',
        'cwe': 'CWE-693',
    },
    'Strict-Transport-Security': {
        'severity': 'High',
        'description': (
            'HTTP Strict-Transport-Security (HSTS) forces browsers to only '
            'communicate over HTTPS, preventing protocol downgrade attacks '
            'and cookie hijacking. Without HSTS, connections may fall back '
            'to insecure HTTP.'
        ),
        'recommendation': (
            'Set HSTS with a minimum max-age of 31536000 (1 year). '
            'Example: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload'
        ),
        'valid_values': None,
        'owasp': 'A02:2021 - Cryptographic Failures',
        'cwe': 'CWE-319',
    },
    'X-Content-Type-Options': {
        'severity': 'Medium',
        'description': (
            'X-Content-Type-Options prevents browsers from MIME-sniffing the '
            'content type, which can lead to security issues when browsers '
            'interpret files as a different content type than intended. '
            'This can enable XSS attacks through file uploads.'
        ),
        'recommendation': (
            'Set X-Content-Type-Options: nosniff'
        ),
        'valid_values': ['nosniff'],
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-16',
    },
    'X-XSS-Protection': {
        'severity': 'Low',
        'description': (
            'X-XSS-Protection enables the browser built-in XSS filter. '
            'While largely superseded by CSP, it provides an additional '
            'layer of defense in older browsers. Note: Some modern browsers '
            'have deprecated this header in favor of CSP.'
        ),
        'recommendation': (
            'Set X-XSS-Protection: 1; mode=block (or rely on CSP instead). '
            'In some contexts, setting it to 0 may be preferred if CSP is in place.'
        ),
        'valid_values': ['0', '1', '1; mode=block'],
        'owasp': 'A03:2021 - Injection',
        'cwe': 'CWE-79',
    },
    'Referrer-Policy': {
        'severity': 'Medium',
        'description': (
            'Referrer-Policy controls how much referrer information is sent '
            'with requests. Without it, sensitive URL parameters (tokens, '
            'session IDs) may leak to third-party sites through the Referer header.'
        ),
        'recommendation': (
            'Set Referrer-Policy to strict-origin-when-cross-origin or no-referrer. '
            'Example: Referrer-Policy: strict-origin-when-cross-origin'
        ),
        'valid_values': [
            'no-referrer', 'no-referrer-when-downgrade', 'origin',
            'origin-when-cross-origin', 'same-origin',
            'strict-origin', 'strict-origin-when-cross-origin'
        ],
        'owasp': 'A01:2021 - Broken Access Control',
        'cwe': 'CWE-200',
    },
    'Permissions-Policy': {
        'severity': 'Medium',
        'description': (
            'Permissions-Policy (formerly Feature-Policy) controls which '
            'browser features (camera, microphone, geolocation, etc.) can '
            'be used by the page. Without it, embedded content may access '
            'sensitive device features.'
        ),
        'recommendation': (
            'Set a restrictive Permissions-Policy. '
            'Example: Permissions-Policy: camera=(), microphone=(), geolocation=()'
        ),
        'valid_values': None,
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-16',
    },
    'Cache-Control': {
        'severity': 'Medium',
        'description': (
            'Cache-Control directives prevent sensitive data from being '
            'stored in browser or proxy caches. Without proper cache control, '
            'sensitive pages may be cached and accessible to other users on '
            'shared computers.'
        ),
        'recommendation': (
            'For sensitive pages: Cache-Control: no-store, no-cache, must-revalidate, private. '
            'Also set Pragma: no-cache for HTTP/1.0 compatibility.'
        ),
        'valid_values': None,
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-525',
    },
    'X-Permitted-Cross-Domain-Policies': {
        'severity': 'Low',
        'description': (
            'X-Permitted-Cross-Domain-Policies restricts Adobe Flash and '
            'PDF cross-domain requests. While Flash is deprecated, this '
            'header prevents potential abuse through PDF embedding.'
        ),
        'recommendation': (
            'Set X-Permitted-Cross-Domain-Policies: none'
        ),
        'valid_values': ['none', 'master-only'],
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-942',
    },
    'Cross-Origin-Embedder-Policy': {
        'severity': 'Low',
        'description': (
            'Cross-Origin-Embedder-Policy (COEP) prevents the page from '
            'loading cross-origin resources that do not explicitly grant '
            'permission. Required for enabling SharedArrayBuffer and '
            'high-resolution timers safely.'
        ),
        'recommendation': (
            'Set Cross-Origin-Embedder-Policy: require-corp'
        ),
        'valid_values': ['require-corp', 'unsafe-none', 'credentialless'],
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-346',
    },
    'Cross-Origin-Opener-Policy': {
        'severity': 'Low',
        'description': (
            'Cross-Origin-Opener-Policy (COOP) ensures that top-level '
            'documents do not share a browsing context group with '
            'cross-origin documents, preventing cross-origin attacks '
            'such as Spectre.'
        ),
        'recommendation': (
            'Set Cross-Origin-Opener-Policy: same-origin'
        ),
        'valid_values': ['same-origin', 'same-origin-allow-popups', 'unsafe-none'],
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-346',
    },
    'Cross-Origin-Resource-Policy': {
        'severity': 'Low',
        'description': (
            'Cross-Origin-Resource-Policy (CORP) prevents other origins '
            'from reading the response of the resources to which this '
            'header is applied, mitigating side-channel attacks.'
        ),
        'recommendation': (
            'Set Cross-Origin-Resource-Policy: same-origin'
        ),
        'valid_values': ['same-origin', 'same-site', 'cross-origin'],
        'owasp': 'A05:2021 - Security Misconfiguration',
        'cwe': 'CWE-346',
    },
}

# Headers that reveal server information (should be removed)
INFORMATION_DISCLOSURE_HEADERS = [
    'Server',
    'X-Powered-By',
    'X-AspNet-Version',
    'X-AspNetMvc-Version',
    'X-Runtime',
    'X-Version',
    'X-Generator',
]


def check_headers(target_url: str, timeout: int = 10, verbose: bool = False) -> HeaderCheckResult:
    """
    Perform a comprehensive security header check on the target URL.

    Args:
        target_url: The URL to check (e.g., http://127.0.0.1:5000)
        timeout: Request timeout in seconds
        verbose: Enable verbose output

    Returns:
        HeaderCheckResult with all findings
    """
    result = HeaderCheckResult(
        target_url=target_url,
        status_code=0,
        total_headers_checked=len(SECURITY_HEADERS),
    )

    try:
        if verbose:
            print(f"[*] Sending request to {target_url}...")

        response = requests.get(
            target_url,
            timeout=timeout,
            allow_redirects=True,
            verify=False  # Allow self-signed certs for testing
        )

        result.status_code = response.status_code

        if verbose:
            print(f"[*] Response status: {response.status_code}")
            print(f"[*] Checking {len(SECURITY_HEADERS)} security headers...")

        # Check each security header
        for header_name, config in SECURITY_HEADERS.items():
            header_value = response.headers.get(header_name)
            present = header_value is not None

            if present:
                result.present_headers += 1
                # Validate the header value if valid_values are defined
                severity = 'Informational'
                if config['valid_values'] and header_value not in config['valid_values']:
                    severity = 'Low'
                    description = (
                        f"{config['description']} Current value '{header_value}' "
                        f"may not be optimal."
                    )
                else:
                    description = f"Header is present with value: {header_value}"
            else:
                result.missing_headers += 1
                severity = config['severity']
                description = config['description']

            finding = HeaderFinding(
                header_name=header_name,
                present=present,
                value=header_value,
                severity=severity if not present else 'Informational',
                description=description,
                recommendation=config['recommendation'],
                owasp_category=config['owasp'],
                cwe_id=config['cwe'],
            )
            result.findings.append(finding)

            if verbose:
                status = "PRESENT" if present else "MISSING"
                icon = "[+]" if present else "[-]"
                print(f"  {icon} {header_name}: {status}")
                if present:
                    print(f"      Value: {header_value}")

        # Check for information disclosure headers
        for header_name in INFORMATION_DISCLOSURE_HEADERS:
            header_value = response.headers.get(header_name)
            if header_value:
                result.technology_fingerprints.append(
                    f"{header_name}: {header_value}"
                )

                finding = HeaderFinding(
                    header_name=header_name,
                    present=True,
                    value=header_value,
                    severity='Low',
                    description=(
                        f"The {header_name} header reveals server/technology information: "
                        f"'{header_value}'. This information helps attackers fingerprint "
                        f"the technology stack and find known vulnerabilities."
                    ),
                    recommendation=(
                        f"Remove the {header_name} header from responses to prevent "
                        f"information disclosure."
                    ),
                    owasp_category='A05:2021 - Security Misconfiguration',
                    cwe_id='CWE-200',
                )
                result.findings.append(finding)

                if verbose:
                    print(f"  [!] Information Disclosure: {header_name}: {header_value}")

        # Store server header separately
        result.server_header = response.headers.get('Server')

        # Calculate security score
        if result.total_headers_checked > 0:
            result.score = int(
                (result.present_headers / result.total_headers_checked) * 100
            )

        if verbose:
            print(f"\n[*] Security Score: {result.score}/100")
            print(f"[*] Headers Present: {result.present_headers}/{result.total_headers_checked}")
            print(f"[*] Headers Missing: {result.missing_headers}/{result.total_headers_checked}")

    except requests.exceptions.ConnectionError:
        print(f"[!] Connection refused: {target_url}")
        print(f"[!] Ensure the target application is running.")
    except requests.exceptions.Timeout:
        print(f"[!] Connection timed out: {target_url}")
    except requests.exceptions.RequestException as e:
        print(f"[!] Request error: {str(e)}")

    return result


def get_missing_headers(result: HeaderCheckResult) -> List[HeaderFinding]:
    """Get only the missing (vulnerable) headers from results."""
    return [f for f in result.findings if not f.present and f.header_name in SECURITY_HEADERS]


def get_findings_by_severity(
    result: HeaderCheckResult,
    severity: str
) -> List[HeaderFinding]:
    """Filter findings by severity level."""
    return [f for f in result.findings if f.severity == severity]


def format_header_report(result: HeaderCheckResult) -> str:
    """Format the header check result as a text report."""
    lines = [
        "=" * 70,
        "  HTTP SECURITY HEADER ANALYSIS REPORT",
        "=" * 70,
        f"  Target: {result.target_url}",
        f"  Status Code: {result.status_code}",
        f"  Security Score: {result.score}/100",
        f"  Headers Present: {result.present_headers}/{result.total_headers_checked}",
        f"  Headers Missing: {result.missing_headers}/{result.total_headers_checked}",
        "=" * 70,
        "",
    ]

    if result.technology_fingerprints:
        lines.append("  TECHNOLOGY FINGERPRINTS:")
        for fp in result.technology_fingerprints:
            lines.append(f"    - {fp}")
        lines.append("")

    # Group by severity
    for severity in ['Critical', 'High', 'Medium', 'Low', 'Informational']:
        severity_findings = get_findings_by_severity(result, severity)
        if severity_findings:
            lines.append(f"  [{severity.upper()}] Findings:")
            lines.append("-" * 60)
            for finding in severity_findings:
                status = "MISSING" if not finding.present else "PRESENT"
                lines.append(f"    Header: {finding.header_name} ({status})")
                lines.append(f"    Description: {finding.description}")
                lines.append(f"    Recommendation: {finding.recommendation}")
                lines.append(f"    OWASP: {finding.owasp_category}")
                lines.append(f"    CWE: {finding.cwe_id}")
                lines.append("")

    return "\n".join(lines)


if __name__ == '__main__':
    # Example usage
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5000'
    print(f"[*] Checking security headers for: {target}")
    print()

    result = check_headers(target, verbose=True)
    print()
    print(format_header_report(result))
