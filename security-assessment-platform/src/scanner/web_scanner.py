"""
Web Application Scanner Module - HTTP security header analysis.

Analyzes web applications for security misconfigurations including:
- HTTP security headers (HSTS, CSP, X-Frame-Options, etc.)
- SSL/TLS certificate information and validity
- Cookie security flags (Secure, HttpOnly, SameSite)
- CORS (Cross-Origin Resource Sharing) policy evaluation

ETHICAL USE NOTICE:
    Only scan web applications you own or have explicit authorization to test.
    Unauthorized scanning may violate computer misuse laws.
"""

import ssl
import socket
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


# Security headers that should be present on production web applications
REQUIRED_SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "description": "HTTP Strict Transport Security (HSTS)",
        "severity": "high",
        "cvss_score": 7.4,
        "remediation": (
            "Add header: Strict-Transport-Security: max-age=31536000; "
            "includeSubDomains; preload"
        ),
    },
    "Content-Security-Policy": {
        "description": "Content Security Policy (CSP)",
        "severity": "high",
        "cvss_score": 7.1,
        "remediation": (
            "Implement a Content-Security-Policy header that restricts "
            "resource loading to trusted origins. Start with report-only mode."
        ),
    },
    "X-Frame-Options": {
        "description": "Clickjacking protection",
        "severity": "medium",
        "cvss_score": 5.4,
        "remediation": (
            "Add header: X-Frame-Options: DENY or SAMEORIGIN. "
            "Also consider using CSP frame-ancestors directive."
        ),
    },
    "X-Content-Type-Options": {
        "description": "MIME type sniffing prevention",
        "severity": "medium",
        "cvss_score": 5.3,
        "remediation": "Add header: X-Content-Type-Options: nosniff",
    },
    "X-XSS-Protection": {
        "description": "XSS filter (legacy browsers)",
        "severity": "low",
        "cvss_score": 3.0,
        "remediation": (
            "Add header: X-XSS-Protection: 1; mode=block. "
            "Note: Modern browsers rely on CSP instead."
        ),
    },
    "Referrer-Policy": {
        "description": "Controls referrer information leakage",
        "severity": "medium",
        "cvss_score": 4.3,
        "remediation": (
            "Add header: Referrer-Policy: strict-origin-when-cross-origin "
            "or no-referrer"
        ),
    },
    "Permissions-Policy": {
        "description": "Controls browser feature access",
        "severity": "medium",
        "cvss_score": 4.0,
        "remediation": (
            "Add Permissions-Policy header to restrict access to browser APIs "
            "like camera, microphone, geolocation, etc."
        ),
    },
    "Cache-Control": {
        "description": "Caching directives for sensitive content",
        "severity": "medium",
        "cvss_score": 4.0,
        "remediation": (
            "For sensitive pages, set: Cache-Control: no-store, no-cache, "
            "must-revalidate, private"
        ),
    },
}

# Headers that reveal server information and should be removed
INFORMATION_DISCLOSURE_HEADERS = [
    "Server",
    "X-Powered-By",
    "X-AspNet-Version",
    "X-AspNetMvc-Version",
    "X-Generator",
]


@dataclass
class HeaderFinding:
    """A single HTTP header security finding."""

    header_name: str
    status: str  # "present", "missing", "misconfigured"
    current_value: str = ""
    expected: str = ""
    severity: str = "info"
    cvss_score: float = 0.0
    description: str = ""
    remediation: str = ""


@dataclass
class CookieFinding:
    """A single cookie security finding."""

    cookie_name: str
    issues: List[str] = field(default_factory=list)
    severity: str = "info"
    secure_flag: bool = False
    httponly_flag: bool = False
    samesite_value: str = ""
    domain: str = ""
    path: str = ""


@dataclass
class SSLInfo:
    """SSL/TLS certificate information."""

    issuer: str = ""
    subject: str = ""
    serial_number: str = ""
    version: int = 0
    not_before: str = ""
    not_after: str = ""
    days_until_expiry: int = 0
    is_expired: bool = False
    signature_algorithm: str = ""
    san_entries: List[str] = field(default_factory=list)
    protocol_version: str = ""
    cipher_suite: str = ""
    key_size: int = 0
    findings: List[Dict] = field(default_factory=list)


@dataclass
class CORSResult:
    """CORS policy evaluation result."""

    allows_all_origins: bool = False
    allows_credentials: bool = False
    allowed_origins: str = ""
    allowed_methods: str = ""
    allowed_headers: str = ""
    exposed_headers: str = ""
    max_age: str = ""
    is_misconfigured: bool = False
    findings: List[Dict] = field(default_factory=list)


@dataclass
class WebScanResult:
    """Complete web application scan result."""

    url: str
    scan_timestamp: str = ""
    status_code: int = 0
    response_time_ms: float = 0.0
    header_findings: List[HeaderFinding] = field(default_factory=list)
    cookie_findings: List[CookieFinding] = field(default_factory=list)
    ssl_info: Optional[SSLInfo] = None
    cors_result: Optional[CORSResult] = None
    information_disclosure: List[Dict] = field(default_factory=list)
    all_findings: List[Dict] = field(default_factory=list)
    security_score: float = 0.0  # 0-100, higher is better

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "scan_timestamp": self.scan_timestamp,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "security_score": self.security_score,
            "header_findings": [
                {
                    "header": f.header_name,
                    "status": f.status,
                    "current_value": f.current_value,
                    "severity": f.severity,
                    "cvss_score": f.cvss_score,
                    "description": f.description,
                    "remediation": f.remediation,
                }
                for f in self.header_findings
            ],
            "cookie_findings": [
                {
                    "name": c.cookie_name,
                    "issues": c.issues,
                    "severity": c.severity,
                    "secure": c.secure_flag,
                    "httponly": c.httponly_flag,
                    "samesite": c.samesite_value,
                }
                for c in self.cookie_findings
            ],
            "ssl_info": (
                {
                    "issuer": self.ssl_info.issuer,
                    "subject": self.ssl_info.subject,
                    "not_before": self.ssl_info.not_before,
                    "not_after": self.ssl_info.not_after,
                    "days_until_expiry": self.ssl_info.days_until_expiry,
                    "is_expired": self.ssl_info.is_expired,
                    "protocol_version": self.ssl_info.protocol_version,
                    "findings": self.ssl_info.findings,
                }
                if self.ssl_info
                else None
            ),
            "cors_result": (
                {
                    "allows_all_origins": self.cors_result.allows_all_origins,
                    "allows_credentials": self.cors_result.allows_credentials,
                    "is_misconfigured": self.cors_result.is_misconfigured,
                    "findings": self.cors_result.findings,
                }
                if self.cors_result
                else None
            ),
            "information_disclosure": self.information_disclosure,
            "all_findings": self.all_findings,
        }


class WebScanner:
    """
    Web application security scanner.

    Performs comprehensive analysis of web application security posture
    including HTTP headers, SSL/TLS configuration, cookie security,
    and CORS policy evaluation.

    Attributes:
        timeout: HTTP request timeout in seconds.
        verify_ssl: Whether to verify SSL certificates.
        user_agent: User-Agent header for HTTP requests.

    Example:
        scanner = WebScanner(timeout=10)
        result = scanner.scan("https://example.com")
        print(f"Security Score: {result.security_score}/100")
        for finding in result.header_findings:
            print(f"  {finding.header_name}: {finding.status}")
    """

    def __init__(
        self,
        timeout: int = 10,
        verify_ssl: bool = True,
        user_agent: str = "SecureAudit-Pro/1.0 Security-Scanner",
    ):
        """
        Initialize the WebScanner.

        Args:
            timeout: HTTP request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates.
            user_agent: User-Agent string for requests.
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.user_agent = user_agent

    def scan(self, url: str) -> WebScanResult:
        """
        Perform a comprehensive web security scan.

        Analyzes HTTP security headers, SSL/TLS configuration,
        cookie security, and CORS policy for the given URL.

        Args:
            url: The URL to scan (must include protocol, e.g., https://...).

        Returns:
            WebScanResult with all findings.

        Raises:
            ValueError: If URL is malformed.
        """
        if not url:
            raise ValueError("URL must be specified")

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: {url}")

        result = WebScanResult(url=url)
        result.scan_timestamp = datetime.now().isoformat()

        if not REQUESTS_AVAILABLE:
            logger.warning(
                "requests library not available. "
                "Install with: pip install requests"
            )
            return result

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"User-Agent": self.user_agent},
                allow_redirects=True,
            )

            result.status_code = response.status_code
            result.response_time_ms = round(
                response.elapsed.total_seconds() * 1000, 2
            )

            # Run all checks
            result.header_findings = self._check_security_headers(
                response.headers
            )
            result.information_disclosure = self._check_information_disclosure(
                response.headers
            )
            result.cookie_findings = self._check_cookies(response.cookies, url)
            result.cors_result = self._check_cors(url, response.headers)

            # SSL check for HTTPS URLs
            if parsed.scheme == "https":
                result.ssl_info = self._check_ssl(
                    parsed.hostname, parsed.port or 443
                )

            # Aggregate all findings
            result.all_findings = self._aggregate_findings(result)

            # Calculate security score
            result.security_score = self._calculate_security_score(result)

        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error scanning {url}: {e}")
            result.all_findings.append({
                "id": "WEB-SSL-ERR",
                "category": "Web Security",
                "title": "SSL/TLS Connection Failure",
                "description": f"Could not establish secure connection: {str(e)[:200]}",
                "severity": "critical",
                "cvss_score": 9.0,
                "remediation": (
                    "Ensure the server has a valid SSL/TLS certificate. "
                    "Check certificate chain completeness and validity."
                ),
            })
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error scanning {url}: {e}")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout scanning {url}")
        except Exception as e:
            logger.error(f"Unexpected error scanning {url}: {e}")

        return result

    def _check_security_headers(
        self, headers: Any
    ) -> List[HeaderFinding]:
        """
        Check for the presence and correctness of security headers.

        Args:
            headers: HTTP response headers dictionary.

        Returns:
            List of HeaderFinding objects.
        """
        findings = []

        for header_name, config in REQUIRED_SECURITY_HEADERS.items():
            header_value = headers.get(header_name, "")

            if not header_value:
                findings.append(HeaderFinding(
                    header_name=header_name,
                    status="missing",
                    current_value="",
                    expected=config.get("remediation", ""),
                    severity=config["severity"],
                    cvss_score=config["cvss_score"],
                    description=f"Missing: {config['description']}",
                    remediation=config["remediation"],
                ))
            else:
                # Validate header values
                issues = self._validate_header_value(
                    header_name, header_value
                )
                if issues:
                    findings.append(HeaderFinding(
                        header_name=header_name,
                        status="misconfigured",
                        current_value=str(header_value),
                        expected=issues["expected"],
                        severity="medium",
                        cvss_score=issues.get("cvss_score", 4.0),
                        description=issues["description"],
                        remediation=issues["remediation"],
                    ))
                else:
                    findings.append(HeaderFinding(
                        header_name=header_name,
                        status="present",
                        current_value=str(header_value),
                        severity="info",
                        cvss_score=0.0,
                        description=f"{config['description']} is properly configured",
                        remediation="",
                    ))

        return findings

    def _validate_header_value(
        self, header_name: str, value: str
    ) -> Optional[Dict]:
        """
        Validate specific header values for known misconfigurations.

        Args:
            header_name: Name of the HTTP header.
            value: Current value of the header.

        Returns:
            Dictionary with issue details if misconfigured, None if correct.
        """
        value_lower = value.lower()

        if header_name == "Strict-Transport-Security":
            if "max-age" in value_lower:
                try:
                    max_age_str = value_lower.split("max-age=")[1].split(";")[0]
                    max_age = int(max_age_str.strip())
                    if max_age < 31536000:
                        return {
                            "description": (
                                f"HSTS max-age is {max_age} seconds "
                                f"({max_age // 86400} days). "
                                "Recommended minimum is 1 year (31536000)."
                            ),
                            "expected": "max-age=31536000; includeSubDomains",
                            "cvss_score": 4.0,
                            "remediation": (
                                "Increase max-age to at least 31536000 (1 year). "
                                "Add includeSubDomains directive."
                            ),
                        }
                except (IndexError, ValueError):
                    pass

        elif header_name == "X-Frame-Options":
            if value_lower not in ("deny", "sameorigin"):
                return {
                    "description": f"X-Frame-Options has unusual value: {value}",
                    "expected": "DENY or SAMEORIGIN",
                    "cvss_score": 4.0,
                    "remediation": "Set X-Frame-Options to DENY or SAMEORIGIN",
                }

        elif header_name == "X-Content-Type-Options":
            if value_lower != "nosniff":
                return {
                    "description": (
                        f"X-Content-Type-Options has incorrect value: {value}"
                    ),
                    "expected": "nosniff",
                    "cvss_score": 4.0,
                    "remediation": "Set X-Content-Type-Options to 'nosniff'",
                }

        elif header_name == "Content-Security-Policy":
            if "unsafe-inline" in value_lower:
                return {
                    "description": (
                        "CSP contains 'unsafe-inline', which weakens "
                        "protection against XSS attacks."
                    ),
                    "expected": "CSP without unsafe-inline; use nonce or hash instead",
                    "cvss_score": 5.0,
                    "remediation": (
                        "Replace 'unsafe-inline' with nonce-based or hash-based "
                        "CSP directives for inline scripts and styles."
                    ),
                }
            if "unsafe-eval" in value_lower:
                return {
                    "description": (
                        "CSP contains 'unsafe-eval', allowing dynamic "
                        "code execution via eval()."
                    ),
                    "expected": "CSP without unsafe-eval",
                    "cvss_score": 6.0,
                    "remediation": (
                        "Remove 'unsafe-eval' from CSP and refactor code "
                        "to avoid eval(), Function(), and setTimeout with strings."
                    ),
                }

        return None

    def _check_information_disclosure(
        self, headers: Any
    ) -> List[Dict]:
        """
        Check for headers that disclose server technology information.

        Args:
            headers: HTTP response headers.

        Returns:
            List of information disclosure findings.
        """
        findings = []

        for header_name in INFORMATION_DISCLOSURE_HEADERS:
            value = headers.get(header_name, "")
            if value:
                findings.append({
                    "id": f"WEB-INFO-{header_name.upper().replace('-', '')}",
                    "category": "Web Security",
                    "title": f"Information Disclosure via {header_name} Header",
                    "description": (
                        f"The {header_name} header reveals server technology: "
                        f"'{value}'. This information assists attackers in "
                        "targeting known vulnerabilities."
                    ),
                    "severity": "low",
                    "cvss_score": 2.6,
                    "header_name": header_name,
                    "header_value": value,
                    "remediation": (
                        f"Remove or obfuscate the {header_name} header "
                        "in your web server configuration."
                    ),
                })

        return findings

    def _check_cookies(
        self, cookies: Any, url: str
    ) -> List[CookieFinding]:
        """
        Analyze cookies for security flag compliance.

        Checks each cookie for Secure, HttpOnly, and SameSite attributes.

        Args:
            cookies: Response cookies from the request.
            url: The target URL for context.

        Returns:
            List of CookieFinding objects.
        """
        findings = []
        is_https = url.startswith("https://")

        for cookie in cookies:
            issues = []
            severity = "info"

            secure = getattr(cookie, "secure", False)
            httponly = cookie.has_nonstandard_attr("HttpOnly") if hasattr(
                cookie, "has_nonstandard_attr"
            ) else False

            # Get SameSite from cookie dictionary
            samesite = ""
            cookie_dict = cookie.__dict__ if hasattr(cookie, "__dict__") else {}
            for attr_key in cookie_dict:
                if "samesite" in str(attr_key).lower():
                    samesite = str(cookie_dict[attr_key])

            # Check Secure flag
            if not secure:
                if is_https:
                    issues.append("Missing Secure flag on HTTPS site")
                    severity = "high"
                else:
                    issues.append("Missing Secure flag (site is HTTP)")
                    severity = "medium"

            # Check HttpOnly flag
            if not httponly:
                issues.append(
                    "Missing HttpOnly flag - cookie accessible via JavaScript"
                )
                if severity != "high":
                    severity = "medium"

            # Check SameSite attribute
            if not samesite or samesite.lower() == "none":
                issues.append(
                    "Missing or weak SameSite attribute - "
                    "vulnerable to CSRF attacks"
                )
                if severity != "high":
                    severity = "medium"

            if issues:
                findings.append(CookieFinding(
                    cookie_name=cookie.name,
                    issues=issues,
                    severity=severity,
                    secure_flag=secure,
                    httponly_flag=httponly,
                    samesite_value=samesite,
                    domain=cookie.domain or "",
                    path=cookie.path or "/",
                ))

        return findings

    def _check_cors(self, url: str, headers: Any) -> CORSResult:
        """
        Evaluate CORS (Cross-Origin Resource Sharing) policy.

        Sends a preflight request with a test origin to check for
        overly permissive CORS configurations.

        Args:
            url: The target URL.
            headers: Response headers from the initial request.

        Returns:
            CORSResult with policy evaluation.
        """
        cors_result = CORSResult()

        # Check response headers for CORS configuration
        acao = headers.get("Access-Control-Allow-Origin", "")
        acac = headers.get("Access-Control-Allow-Credentials", "")
        acam = headers.get("Access-Control-Allow-Methods", "")
        acah = headers.get("Access-Control-Allow-Headers", "")
        aceh = headers.get("Access-Control-Expose-Headers", "")
        acma = headers.get("Access-Control-Max-Age", "")

        cors_result.allowed_origins = acao
        cors_result.allows_credentials = acac.lower() == "true"
        cors_result.allowed_methods = acam
        cors_result.allowed_headers = acah
        cors_result.exposed_headers = aceh
        cors_result.max_age = acma

        if acao == "*":
            cors_result.allows_all_origins = True
            cors_result.is_misconfigured = True
            cors_result.findings.append({
                "id": "WEB-CORS-WILDCARD",
                "category": "Web Security",
                "title": "CORS Allows All Origins",
                "description": (
                    "Access-Control-Allow-Origin is set to '*', allowing "
                    "any website to make cross-origin requests."
                ),
                "severity": "medium",
                "cvss_score": 5.3,
                "remediation": (
                    "Restrict CORS to specific trusted origins. "
                    "Implement a whitelist of allowed domains."
                ),
            })

        if cors_result.allows_all_origins and cors_result.allows_credentials:
            cors_result.is_misconfigured = True
            cors_result.findings.append({
                "id": "WEB-CORS-CRED",
                "category": "Web Security",
                "title": "CORS Wildcard with Credentials",
                "description": (
                    "CORS allows all origins AND credentials. This is a "
                    "critical misconfiguration that can enable data theft."
                ),
                "severity": "critical",
                "cvss_score": 8.7,
                "remediation": (
                    "Never combine Access-Control-Allow-Origin: * with "
                    "Access-Control-Allow-Credentials: true. "
                    "Use specific origins instead."
                ),
            })

        # Test with a malicious origin (preflight check)
        if REQUESTS_AVAILABLE:
            try:
                test_origin = "https://evil-attacker-domain.example.com"
                preflight_response = requests.options(
                    url,
                    headers={
                        "Origin": test_origin,
                        "Access-Control-Request-Method": "GET",
                        "User-Agent": self.user_agent,
                    },
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )

                reflected_origin = preflight_response.headers.get(
                    "Access-Control-Allow-Origin", ""
                )
                if reflected_origin == test_origin:
                    cors_result.is_misconfigured = True
                    cors_result.findings.append({
                        "id": "WEB-CORS-REFLECT",
                        "category": "Web Security",
                        "title": "CORS Origin Reflection Vulnerability",
                        "description": (
                            "The server reflects the Origin header in "
                            "Access-Control-Allow-Origin, allowing any "
                            "origin to make authenticated cross-origin requests."
                        ),
                        "severity": "high",
                        "cvss_score": 7.5,
                        "remediation": (
                            "Implement a strict origin whitelist instead of "
                            "reflecting the Origin header. Validate origins "
                            "against a predefined list."
                        ),
                    })
            except Exception:
                pass

        return cors_result

    def _check_ssl(self, hostname: str, port: int = 443) -> SSLInfo:
        """
        Check SSL/TLS certificate and connection information.

        Args:
            hostname: The server hostname.
            port: The HTTPS port (default 443).

        Returns:
            SSLInfo with certificate details and findings.
        """
        ssl_info = SSLInfo()

        try:
            context = ssl.create_default_context()
            conn = context.wrap_socket(
                socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                server_hostname=hostname,
            )
            conn.settimeout(self.timeout)
            conn.connect((hostname, port))

            cert = conn.getpeercert()
            cipher = conn.cipher()

            # Extract certificate information
            if cert:
                # Subject
                subject_parts = []
                for item in cert.get("subject", ()):
                    for key, value in item:
                        subject_parts.append(f"{key}={value}")
                ssl_info.subject = ", ".join(subject_parts)

                # Issuer
                issuer_parts = []
                for item in cert.get("issuer", ()):
                    for key, value in item:
                        issuer_parts.append(f"{key}={value}")
                ssl_info.issuer = ", ".join(issuer_parts)

                # Validity dates
                ssl_info.not_before = cert.get("notBefore", "")
                ssl_info.not_after = cert.get("notAfter", "")

                # Calculate days until expiry
                if ssl_info.not_after:
                    try:
                        expiry_date = datetime.strptime(
                            ssl_info.not_after, "%b %d %H:%M:%S %Y %Z"
                        )
                        now = datetime.now()
                        delta = expiry_date - now
                        ssl_info.days_until_expiry = delta.days
                        ssl_info.is_expired = delta.days < 0
                    except ValueError:
                        pass

                # Serial number
                ssl_info.serial_number = str(cert.get("serialNumber", ""))

                # Version
                ssl_info.version = cert.get("version", 0)

                # Subject Alternative Names
                san_list = cert.get("subjectAltName", ())
                ssl_info.san_entries = [
                    f"{san_type}: {san_value}"
                    for san_type, san_value in san_list
                ]

            # Cipher information
            if cipher:
                ssl_info.cipher_suite = cipher[0]
                ssl_info.protocol_version = cipher[1]
                ssl_info.key_size = cipher[2] if len(cipher) > 2 else 0

            # Generate SSL findings
            ssl_info.findings = self._generate_ssl_findings(ssl_info)

            conn.close()

        except ssl.SSLCertVerificationError as e:
            ssl_info.findings.append({
                "id": "WEB-SSL-VERIFY",
                "category": "Web Security",
                "title": "SSL Certificate Verification Failed",
                "description": f"Certificate verification error: {str(e)[:200]}",
                "severity": "critical",
                "cvss_score": 9.0,
                "remediation": (
                    "Obtain a valid SSL certificate from a trusted Certificate "
                    "Authority. Ensure the certificate chain is complete."
                ),
            })
        except Exception as e:
            logger.error(f"SSL check error for {hostname}:{port}: {e}")

        return ssl_info

    def _generate_ssl_findings(self, ssl_info: SSLInfo) -> List[Dict]:
        """
        Generate findings from SSL/TLS analysis.

        Args:
            ssl_info: Populated SSLInfo object.

        Returns:
            List of finding dictionaries.
        """
        findings = []

        # Certificate expiry checks
        if ssl_info.is_expired:
            findings.append({
                "id": "WEB-SSL-EXPIRED",
                "category": "Web Security",
                "title": "SSL Certificate Has Expired",
                "description": (
                    f"The SSL certificate expired "
                    f"{abs(ssl_info.days_until_expiry)} days ago."
                ),
                "severity": "critical",
                "cvss_score": 9.0,
                "remediation": "Immediately renew the SSL certificate.",
            })
        elif ssl_info.days_until_expiry < 30:
            findings.append({
                "id": "WEB-SSL-EXPIRING",
                "category": "Web Security",
                "title": "SSL Certificate Expiring Soon",
                "description": (
                    f"Certificate expires in {ssl_info.days_until_expiry} days."
                ),
                "severity": "high",
                "cvss_score": 7.0,
                "remediation": (
                    "Renew the SSL certificate before expiry. "
                    "Consider automated certificate management (ACME/Let's Encrypt)."
                ),
            })
        elif ssl_info.days_until_expiry < 90:
            findings.append({
                "id": "WEB-SSL-EXPWARN",
                "category": "Web Security",
                "title": "SSL Certificate Expiry Warning",
                "description": (
                    f"Certificate expires in {ssl_info.days_until_expiry} days."
                ),
                "severity": "medium",
                "cvss_score": 4.0,
                "remediation": "Plan certificate renewal within the next 60 days.",
            })

        # Weak cipher check
        weak_ciphers = ["RC4", "DES", "3DES", "NULL", "EXPORT", "anon"]
        if ssl_info.cipher_suite:
            for weak in weak_ciphers:
                if weak.lower() in ssl_info.cipher_suite.lower():
                    findings.append({
                        "id": "WEB-SSL-WEAKCIPHER",
                        "category": "Web Security",
                        "title": "Weak SSL/TLS Cipher Suite",
                        "description": (
                            f"Server negotiated a weak cipher: "
                            f"{ssl_info.cipher_suite}"
                        ),
                        "severity": "high",
                        "cvss_score": 7.5,
                        "remediation": (
                            "Disable weak cipher suites. Configure the server "
                            "to use only strong ciphers (AES-256-GCM, ChaCha20)."
                        ),
                    })
                    break

        # Small key size check
        if ssl_info.key_size and ssl_info.key_size < 128:
            findings.append({
                "id": "WEB-SSL-WEAKKEY",
                "category": "Web Security",
                "title": "Weak SSL/TLS Key Size",
                "description": (
                    f"Key size is {ssl_info.key_size} bits. "
                    "Minimum recommended is 128 bits."
                ),
                "severity": "high",
                "cvss_score": 7.0,
                "remediation": "Use a minimum key size of 2048 bits for RSA keys.",
            })

        return findings

    def _aggregate_findings(self, result: WebScanResult) -> List[Dict]:
        """
        Aggregate all findings from different check types into a unified list.

        Args:
            result: The WebScanResult being built.

        Returns:
            Unified list of all findings.
        """
        all_findings = []
        finding_counter = 0

        # Header findings
        for hf in result.header_findings:
            if hf.status != "present":
                finding_counter += 1
                all_findings.append({
                    "id": f"WEB-HDR-{finding_counter:03d}",
                    "category": "Web Security",
                    "title": f"Security Header: {hf.header_name} - {hf.status.title()}",
                    "description": hf.description,
                    "severity": hf.severity,
                    "cvss_score": hf.cvss_score,
                    "remediation": hf.remediation,
                    "evidence": f"Current value: {hf.current_value or 'Not set'}",
                    "compliance_refs": [
                        "ISO 27001 A.14.1.2",
                        "PCI-DSS Req 6.5.10",
                        "NIST CSF PR.DS-2",
                    ],
                })

        # Information disclosure findings
        all_findings.extend(result.information_disclosure)

        # Cookie findings
        for cf in result.cookie_findings:
            finding_counter += 1
            all_findings.append({
                "id": f"WEB-COOKIE-{finding_counter:03d}",
                "category": "Web Security",
                "title": f"Insecure Cookie: {cf.cookie_name}",
                "description": "; ".join(cf.issues),
                "severity": cf.severity,
                "cvss_score": 5.3 if cf.severity == "high" else 3.5,
                "remediation": (
                    f"Set the following flags on cookie '{cf.cookie_name}': "
                    "Secure; HttpOnly; SameSite=Strict (or Lax)"
                ),
                "evidence": (
                    f"Cookie '{cf.cookie_name}': "
                    f"Secure={cf.secure_flag}, "
                    f"HttpOnly={cf.httponly_flag}, "
                    f"SameSite={cf.samesite_value or 'Not set'}"
                ),
                "compliance_refs": [
                    "ISO 27001 A.14.1.2",
                    "PCI-DSS Req 6.5.10",
                ],
            })

        # SSL findings
        if result.ssl_info:
            all_findings.extend(result.ssl_info.findings)

        # CORS findings
        if result.cors_result:
            all_findings.extend(result.cors_result.findings)

        return all_findings

    def _calculate_security_score(self, result: WebScanResult) -> float:
        """
        Calculate an overall web security score from 0-100.

        Higher scores indicate better security posture. Scoring is based
        on the presence and correctness of security controls.

        Args:
            result: The complete WebScanResult.

        Returns:
            Security score as a float between 0 and 100.
        """
        max_score = 100.0
        deductions = 0.0

        # Header deductions (up to 50 points)
        for hf in result.header_findings:
            if hf.status == "missing":
                if hf.severity == "high":
                    deductions += 8.0
                elif hf.severity == "medium":
                    deductions += 5.0
                else:
                    deductions += 2.0
            elif hf.status == "misconfigured":
                deductions += 3.0

        # Cookie deductions (up to 15 points)
        for cf in result.cookie_findings:
            if cf.severity == "high":
                deductions += 5.0
            elif cf.severity == "medium":
                deductions += 3.0
            else:
                deductions += 1.0

        # SSL deductions (up to 25 points)
        if result.ssl_info:
            for finding in result.ssl_info.findings:
                if finding.get("severity") == "critical":
                    deductions += 25.0
                elif finding.get("severity") == "high":
                    deductions += 15.0
                elif finding.get("severity") == "medium":
                    deductions += 8.0

        # CORS deductions (up to 15 points)
        if result.cors_result and result.cors_result.is_misconfigured:
            for finding in result.cors_result.findings:
                if finding.get("severity") == "critical":
                    deductions += 15.0
                elif finding.get("severity") == "high":
                    deductions += 10.0
                else:
                    deductions += 5.0

        # Information disclosure deductions (up to 5 points)
        deductions += len(result.information_disclosure) * 1.5

        final_score = max(0.0, min(100.0, max_score - deductions))
        return round(final_score, 1)
