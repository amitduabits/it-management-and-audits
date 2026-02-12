# Security Scanning Methodology

> This document describes the scanning methodology used by the Web Application
> Security Scanner, including the phases of assessment, detection techniques,
> and severity classification framework.

---

## Ethical Use Disclaimer

This methodology documentation is provided for authorized security testing only.
All techniques described here must only be applied to systems you own or have
explicit written permission to test. Unauthorized security testing is illegal.

---

## Overview

The scanner follows a structured methodology based on industry-standard practices
from the OWASP Testing Guide, PTES (Penetration Testing Execution Standard),
and NIST SP 800-115 (Technical Guide to Information Security Testing).

The assessment is divided into five sequential phases:

```
Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
Reconnaissance   Configuration    Injection        Network          Reporting
& Discovery      Analysis         Testing          Analysis         & Output
     |                |               |               |                |
     v                v               v               v                v
Directory        Security         SQL Injection    Port             HTML/JSON
Enumeration      Headers          Detection        Scanning         Report
                 Analysis                                           Generation
                                  XSS Detection
```

---

## Phase 1: Reconnaissance and Discovery

### Objective
Identify the attack surface by discovering exposed directories, files,
endpoints, and resources that may be unintentionally accessible.

### Module: `directory_scanner.py`

### Technique: Forced Browsing / Content Discovery

The scanner performs HTTP GET requests against a comprehensive wordlist
of common paths organized by category:

| Category | Example Paths | Risk |
|---|---|---|
| Admin Panels | `/admin`, `/wp-admin`, `/phpmyadmin` | Unauthorized administrative access |
| Config Files | `/.env`, `/config.php`, `/web.config` | Credential and secret exposure |
| Version Control | `/.git/HEAD`, `/.svn/entries` | Source code disclosure |
| Backup Files | `/backup.sql`, `/backup.zip` | Data exposure |
| API Endpoints | `/api/`, `/swagger.json`, `/graphql` | API abuse |
| Server Info | `/phpinfo.php`, `/server-status` | Information disclosure |
| Log Files | `/error.log`, `/debug.log` | Sensitive data in logs |

### Detection Logic

```
For each path in the wordlist:
    1. Send HTTP GET request to target + path
    2. Analyze response status code:
       - 200 OK        -> Resource found (confirmed)
       - 301/302       -> Resource exists (redirected)
       - 401/403       -> Resource exists but protected
       - 404           -> Not found (skip)
    3. Record finding with severity based on category
    4. Extract content length for evidence
```

### Concurrency
- Uses ThreadPoolExecutor with configurable thread count (default: 20)
- Each path check is independent and can run in parallel
- Connection timeouts prevent hanging on unresponsive endpoints

---

## Phase 2: Configuration Analysis

### Objective
Evaluate the security configuration of the web application by analyzing
HTTP response headers and identifying misconfigurations.

### Module: `header_check.py`

### Technique: HTTP Header Analysis

The scanner sends an HTTP GET request to the target and analyzes the
response headers against a database of 12+ security headers:

### Headers Analyzed

| Header | Purpose | Missing = Severity |
|---|---|---|
| X-Frame-Options | Clickjacking protection | High |
| Content-Security-Policy | XSS/injection mitigation | High |
| Strict-Transport-Security | HTTPS enforcement | High |
| X-Content-Type-Options | MIME sniffing prevention | Medium |
| Referrer-Policy | Referrer leakage control | Medium |
| Permissions-Policy | Feature restriction | Medium |
| Cache-Control | Caching of sensitive data | Medium |
| X-XSS-Protection | Legacy XSS filter | Low |
| X-Permitted-Cross-Domain-Policies | Flash/PDF cross-domain | Low |
| Cross-Origin-Embedder-Policy | COEP | Low |
| Cross-Origin-Opener-Policy | COOP | Low |
| Cross-Origin-Resource-Policy | CORP | Low |

### Information Disclosure Detection

Additionally, the scanner checks for headers that reveal technology
stack information:

- `Server` header (e.g., "Apache/2.4.52", "nginx/1.21")
- `X-Powered-By` header (e.g., "PHP/8.1", "Express")
- `X-AspNet-Version`, `X-AspNetMvc-Version`
- `X-Runtime`, `X-Generator`

### Scoring

A security score (0-100) is calculated based on the ratio of present
security headers to the total headers checked.

---

## Phase 3: Injection Testing

### Objective
Detect injection vulnerabilities by sending crafted payloads through
input fields and URL parameters, then analyzing the application's response.

### 3A: SQL Injection Detection

#### Module: `sqli_scanner.py`

#### Technique Categories

**1. Error-Based Detection**
```
Methodology:
    1. Send payloads designed to cause SQL syntax errors
    2. Analyze response for database error patterns
    3. Match against 30+ regex patterns for different DBMS

Payloads include:
    - Single quotes: '
    - Boolean conditions: ' OR '1'='1
    - Comment injection: ' --
    - UNION attempts: ' UNION SELECT NULL--

Detection: Response contains SQL error strings like:
    - "syntax error"
    - "sqlite3.OperationalError"
    - "You have an error in your SQL syntax"
    - "ORA-xxxxx"
```

**2. Boolean-Based Blind Detection**
```
Methodology:
    1. Send TRUE condition payload (e.g., ' AND '1'='1' --)
    2. Send FALSE condition payload (e.g., ' AND '1'='2' --)
    3. Compare response lengths and status codes
    4. Significant difference indicates injection

Detection criteria:
    - Response length difference > 100 bytes
    - Different HTTP status codes
```

**3. Time-Based Blind Detection**
```
Methodology:
    1. Establish baseline response time
    2. Send time-delay payloads:
       - MySQL: ' OR SLEEP(3)--
       - MSSQL: '; WAITFOR DELAY '0:0:5'--
       - PostgreSQL: '; SELECT pg_sleep(3)--
    3. Compare response time to baseline
    4. Delay > 2.5 seconds indicates injection

Detection criteria:
    - Response time exceeds baseline + threshold
    - Request timeout (possible extreme delay)
```

**4. Authentication Bypass Detection**
```
Methodology:
    1. Record normal failed login response
    2. Send bypass payloads as username/password
    3. Compare response to normal failed login
    4. Check for redirect (302) indicating success

Detection criteria:
    - HTTP 302 redirect after injection
    - Response differs significantly from failed login
```

### 3B: Cross-Site Scripting (XSS) Detection

#### Module: `xss_scanner.py`

#### Technique Categories

**1. Script Tag Injection**
```
Payloads: <script>alert(1)</script> and variants
Detection: Payload appears unescaped in response body
```

**2. Event Handler Injection**
```
Payloads: <img src=x onerror=alert(1)>, <svg onload=alert(1)>
Detection: Event handler tag reflected in response
```

**3. Attribute Injection**
```
Payloads: " onmouseover="alert(1)" x="
Detection: Injected attribute appears in HTML element
```

**4. JavaScript Context Injection**
```
Payloads: ';alert(1);//
Detection: Payload breaks out of JavaScript string context
```

**5. Encoded Payloads**
```
Payloads: URL-encoded and HTML-entity-encoded versions
Detection: Decoded payload reflected in response
```

#### Context Detection

The scanner determines the reflection context to assess exploitability:

```
Response text analysis:
    1. Check for <script>...</script> wrapping -> JavaScript context
    2. Check for ="..." preceding payload     -> Attribute context
    3. Check for <style>...</style> wrapping   -> CSS context
    4. Check for <!--...--> wrapping           -> Comment context
    5. Default                                 -> HTML body context
```

---

## Phase 4: Network Analysis

### Objective
Discover open network ports and identify running services that may
represent security risks.

### Module: `port_scanner.py`

### Technique: TCP Connect Scan

```
For each port in the scan range:
    1. Create a TCP socket
    2. Set connection timeout (default: 2 seconds)
    3. Attempt to connect (connect_ex)
    4. Analyze result:
       - Return 0    -> Port OPEN
       - Return != 0 -> Port CLOSED
       - Timeout     -> Port FILTERED
    5. If open, attempt banner grab:
       - Send minimal data
       - Read up to 1024 bytes
       - Record banner for service identification
```

### Service Identification

Open ports are mapped to known services:

| Port | Service | Default Severity |
|---|---|---|
| 21 | FTP | High |
| 22 | SSH | Informational |
| 23 | Telnet | Critical |
| 80 | HTTP | Medium |
| 443 | HTTPS | Informational |
| 3306 | MySQL | Critical |
| 3389 | RDP | High |
| 5432 | PostgreSQL | Critical |

### Scan Types

- **Quick Scan**: 25 most common and dangerous ports
- **Full Scan**: Ports 1-1024 plus additional high-risk ports

### Concurrency
- ThreadPoolExecutor with configurable thread count (default: 50)
- Each port scan is independent and highly parallelizable

---

## Phase 5: Reporting and Output

### Objective
Compile all findings into a professional, actionable vulnerability report
with severity classification and remediation guidance.

### Module: `reporter.py`

### Finding Normalization

All findings from different scanner modules are normalized into a
unified `VulnerabilityEntry` format:

```
VulnerabilityEntry:
    - title: Human-readable finding title
    - severity: Critical | High | Medium | Low | Informational
    - category: Vulnerability category
    - description: Detailed description
    - evidence: Proof of vulnerability
    - remediation: How to fix the issue
    - url: Affected URL/endpoint
    - parameter: Affected parameter (if applicable)
    - owasp_category: OWASP Top 10 mapping
    - cwe_id: CWE reference number
    - module: Scanner module that detected it
```

### Severity Classification

| Severity | Weight | Criteria |
|---|---|---|
| Critical | 10.0 | Direct compromise, data breach, RCE possible |
| High | 7.5 | Significant impact, exploitation likely |
| Medium | 5.0 | Moderate impact, exploitation requires effort |
| Low | 2.5 | Minor impact, limited exploitation potential |
| Informational | 0.5 | Best practice recommendation, no direct risk |

### Risk Score Calculation

```
risk_score = (sum of severity weights) / (count * max_weight) * 10.0
Capped at 10.0
```

### Output Formats

1. **HTML Report** - Professional styled report with severity color coding
2. **JSON Report** - Machine-readable format for integration with other tools
3. **Console Summary** - Quick overview printed to terminal

---

## Limitations

This scanner has the following known limitations:

1. **Authenticated scanning** - The scanner does not maintain authenticated sessions
   for testing pages behind login
2. **Stored XSS** - Only reflected XSS is tested; stored XSS requires multi-step
   testing that is not currently automated
3. **Business logic flaws** - Cannot detect vulnerabilities in application business logic
4. **WAF bypass** - Payloads are not designed to bypass Web Application Firewalls
5. **Rate limiting** - No built-in rate limiting; rapid scanning may trigger defenses
6. **JavaScript rendering** - Does not execute JavaScript; DOM-based XSS detection
   is limited
7. **False positives** - Automated scanning may produce false positives that require
   manual verification

---

## References

- OWASP Testing Guide v4.2: https://owasp.org/www-project-web-security-testing-guide/
- PTES (Penetration Testing Execution Standard): http://www.pentest-standard.org/
- NIST SP 800-115: https://csrc.nist.gov/publications/detail/sp/800-115/final
- CWE (Common Weakness Enumeration): https://cwe.mitre.org/
