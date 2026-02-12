# OWASP Top 10 (2021) - Vulnerability Reference Guide

> **This document provides a comprehensive reference for each vulnerability category
> in the OWASP Top 10 (2021), explaining how each relates to the scanner's detection
> capabilities and the included vulnerable application.**

---

## Important Notice

This reference is intended for educational purposes and authorized security testing.
Understanding these vulnerabilities is essential for building secure applications.
Never exploit vulnerabilities in systems without explicit written authorization.

---

## A01:2021 - Broken Access Control

### Description
Broken access control occurs when restrictions on authenticated users are not properly
enforced. This allows attackers to access unauthorized functionality or data, such as
accessing other users' accounts, viewing sensitive files, modifying other users' data,
or changing access rights.

### Common Weaknesses
- Bypassing access control checks by modifying the URL, application state, or HTML page
- Allowing the primary key to be changed to another user's record (IDOR)
- Elevation of privilege (acting as a user without being logged in, or as admin while logged in as user)
- Missing access control for POST, PUT, and DELETE methods in APIs
- CORS misconfiguration allowing API access from unauthorized origins

### Example in Vulnerable App
The vulnerable application contains an **Insecure Direct Object Reference (IDOR)**
vulnerability in the `/profile/<user_id>` endpoint. Any user can access any other
user's profile by simply changing the ID in the URL without any authorization check.

```python
# VULNERABLE CODE - No authorization check
@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return render_template('profile.html', user=user)

# SECURE CODE - Authorization check added
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    if session['user_id'] != user_id and session['role'] != 'admin':
        abort(403)
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return render_template('profile.html', user=user)
```

### Scanner Coverage
- `directory_scanner.py`: Detects exposed admin panels and unauthorized endpoints
- Manual testing recommended for IDOR vulnerabilities

### Remediation
1. Implement proper access control in server-side code (never rely on client-side)
2. Deny access by default except for public resources
3. Implement access control mechanisms once and reuse throughout the application
4. Log access control failures and alert administrators
5. Rate-limit API and controller access to minimize mass exploitation
6. Invalidate session tokens and JWTs after logout

### CWE References
- CWE-200: Exposure of Sensitive Information
- CWE-284: Improper Access Control
- CWE-285: Improper Authorization
- CWE-639: Authorization Bypass Through User-Controlled Key (IDOR)

---

## A02:2021 - Cryptographic Failures

### Description
Previously known as "Sensitive Data Exposure," this category focuses on failures
related to cryptography that lead to exposure of sensitive data. This includes
transmitting data in plaintext, using deprecated cryptographic algorithms, using
weak or default cryptographic keys, and improper certificate validation.

### Common Weaknesses
- Data transmitted in cleartext (HTTP instead of HTTPS)
- Old or weak cryptographic algorithms (MD5, SHA1, DES)
- Default or weak crypto keys; key reuse
- Missing or improper certificate validation
- Passwords stored in plaintext or with weak hashing

### Example in Vulnerable App
The vulnerable application stores passwords in **plaintext** in the SQLite database.
No hashing algorithm is applied, meaning anyone with database access can read all
user passwords directly.

```python
# VULNERABLE - Plaintext password storage
cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
               (username, password))

# SECURE - Password hashing with bcrypt
import bcrypt
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
               (username, hashed))
```

### Scanner Coverage
- `header_check.py`: Detects missing HSTS header (Strict-Transport-Security)
- `header_check.py`: Checks for secure transport configuration

### Remediation
1. Classify data by sensitivity and apply appropriate protections
2. Use HTTPS everywhere (enforce with HSTS)
3. Hash passwords with strong adaptive algorithms (bcrypt, scrypt, argon2)
4. Use current, strong cryptographic algorithms and keys
5. Disable caching for responses containing sensitive data

### CWE References
- CWE-259: Use of Hard-coded Password
- CWE-327: Use of a Broken or Risky Cryptographic Algorithm
- CWE-331: Insufficient Entropy
- CWE-319: Cleartext Transmission of Sensitive Information

---

## A03:2021 - Injection

### Description
Injection flaws occur when untrusted data is sent to an interpreter as part of a
command or query. Hostile data can trick the interpreter into executing unintended
commands or accessing data without proper authorization. SQL injection, NoSQL
injection, OS command injection, and LDAP injection are the most common variants.

### Common Weaknesses
- User-supplied data is not validated, filtered, or sanitized
- Dynamic queries or non-parameterized calls without context-aware escaping
- Hostile data used within ORM search parameters
- Direct use of external content in SQL queries or commands

### Example in Vulnerable App
The vulnerable application contains **SQL injection** in both the login form and
search functionality. User input is directly concatenated into SQL queries.

```python
# VULNERABLE - String concatenation in SQL
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
cursor = db.execute(query)

# SECURE - Parameterized query
query = "SELECT * FROM users WHERE username = ? AND password = ?"
cursor = db.execute(query, (username, hashed_password))
```

The application also contains **Reflected XSS** where user input is rendered in
the response without encoding:

```html
<!-- VULNERABLE - Using |safe filter -->
<div>Results for: {{ query|safe }}</div>

<!-- SECURE - Auto-escaping (default in Jinja2) -->
<div>Results for: {{ query }}</div>
```

### Scanner Coverage
- `sqli_scanner.py`: Tests for error-based, boolean-blind, time-based, and UNION SQL injection
- `xss_scanner.py`: Tests for reflected XSS with multiple payload categories

### Remediation
1. Use parameterized queries (prepared statements) for all database operations
2. Use an ORM framework for database access
3. Implement server-side input validation with allowlists
4. Escape special characters in dynamic queries
5. Use LIMIT and other SQL controls to prevent mass disclosure
6. Deploy a Content Security Policy (CSP) to mitigate XSS impact

### CWE References
- CWE-79: Cross-site Scripting (XSS)
- CWE-89: SQL Injection
- CWE-73: External Control of File Name or Path
- CWE-77: Command Injection

---

## A04:2021 - Insecure Design

### Description
Insecure design is a broad category representing different weaknesses that stem
from missing or ineffective security controls in the application's design phase.
It focuses on risks related to design and architectural flaws, calling for the
use of threat modeling, secure design patterns, and reference architectures.

### Common Weaknesses
- Missing security requirements during design phase
- No threat modeling performed
- Missing rate limiting on sensitive operations
- No defense-in-depth strategy

### Example in Vulnerable App
The vulnerable application lacks fundamental security design patterns:
- No rate limiting on login attempts
- No CSRF protection on forms
- No account lockout mechanism
- Session management relies on Flask defaults without hardening

### Scanner Coverage
- Limited automated detection; primarily requires manual review
- `header_check.py` can detect some design issues via missing headers

### Remediation
1. Establish a secure development lifecycle with security experts
2. Use threat modeling for authentication, access control, and business logic
3. Integrate security language and controls into user stories
4. Write unit and integration tests for security controls
5. Separate application tiers based on trust levels

### CWE References
- CWE-256: Unprotected Storage of Credentials
- CWE-501: Trust Boundary Violation
- CWE-522: Insufficiently Protected Credentials

---

## A05:2021 - Security Misconfiguration

### Description
Security misconfiguration is the most commonly seen vulnerability. It occurs when
security hardening is missing, default settings are insecure, cloud storage is
open, HTTP headers are misconfigured, error messages contain sensitive information,
or unnecessary features are enabled.

### Common Weaknesses
- Missing or improperly configured security headers
- Unnecessary features enabled (e.g., debug mode, default accounts)
- Default credentials not changed
- Error handling reveals stack traces or implementation details
- Directory listing enabled on the web server
- Unnecessary services or ports open

### Example in Vulnerable App
Multiple security misconfigurations are present:

```python
# VULNERABLE - Debug mode enabled
app.debug = True

# VULNERABLE - Hardcoded weak secret key
app.secret_key = 'supersecretkey123'

# VULNERABLE - Missing security headers
# No X-Frame-Options, CSP, HSTS, etc.

# VULNERABLE - Verbose error messages
error = f'Database error: {str(e)}'
```

### Scanner Coverage
- `header_check.py`: Comprehensive security header analysis
- `directory_scanner.py`: Detects exposed config files, backups, logs
- `port_scanner.py`: Identifies unnecessary open ports

### Remediation
1. Implement a repeatable security hardening process
2. Remove or do not install unnecessary features, frameworks, and components
3. Review and update security configurations regularly
4. Use a segmented application architecture
5. Send security directives (headers) to clients
6. Automate configuration verification

### CWE References
- CWE-2: Environmental Security Flaws
- CWE-16: Configuration
- CWE-388: Error Handling

---

## A06:2021 - Vulnerable and Outdated Components

### Description
Applications are vulnerable when they use components (libraries, frameworks, other
software modules) with known vulnerabilities, or when the software is unsupported,
out of date, or unpatched.

### Common Weaknesses
- Using components with known CVEs
- Not knowing the versions of all components used
- Software is no longer supported or out of date
- Not regularly scanning for vulnerabilities
- Not fixing or upgrading dependencies in a timely manner

### Scanner Coverage
- `directory_scanner.py`: Identifies CMS/framework specific files for version detection
- Full dependency scanning planned for future versions

### Remediation
1. Remove unused dependencies and unnecessary features
2. Continuously inventory component versions using tools like OWASP Dependency-Check
3. Monitor sources like CVE and NVD for vulnerabilities
4. Obtain components only from official sources over secure links
5. Monitor for libraries and components that are unmaintained

### CWE References
- CWE-1104: Use of Unmaintained Third Party Components

---

## A07:2021 - Identification and Authentication Failures

### Description
Previously "Broken Authentication," this category covers weaknesses in
authentication and session management. This includes permitting brute force
or automated attacks, allowing weak passwords, using plaintext or weakly
hashed passwords, missing MFA, and improper session management.

### Common Weaknesses
- Permits automated credential stuffing and brute force attacks
- Permits default, weak, or well-known passwords
- Uses weak credential recovery processes
- Stores passwords in plain text or with weak hashing
- Missing or ineffective multi-factor authentication
- Exposes session tokens in URLs

### Example in Vulnerable App
The application has multiple authentication failures:
- Passwords stored in plaintext
- No account lockout after failed attempts
- No password complexity requirements
- Session not properly invalidated on logout
- Predictable session token generation

### Scanner Coverage
- `sqli_scanner.py`: Tests for authentication bypass via SQL injection
- `header_check.py`: Checks session-related headers

### Remediation
1. Implement multi-factor authentication
2. Do not use default credentials
3. Implement weak password checks against lists of top 10,000 worst passwords
4. Use server-side session management with random, high-entropy session IDs
5. Implement account lockout with logging

### CWE References
- CWE-255: Credentials Management Errors
- CWE-287: Improper Authentication
- CWE-384: Session Fixation

---

## A08:2021 - Software and Data Integrity Failures

### Description
This category focuses on making assumptions related to software updates, critical
data, and CI/CD pipelines without verifying integrity. It includes insecure
deserialization as a subcategory.

### Common Weaknesses
- Code and infrastructure that does not protect against integrity violations
- Unsigned or unverified software updates
- Insecure CI/CD pipeline allowing unauthorized access
- Auto-update functionality without integrity verification

### Scanner Coverage
- `header_check.py`: Checks for Subresource Integrity related headers
- Limited automated detection; requires architecture review

### Remediation
1. Use digital signatures to verify software and data integrity
2. Ensure libraries and dependencies are from trusted repositories
3. Use dependency verification tools
4. Review code and configuration changes in CI/CD
5. Ensure CI/CD pipeline has proper segregation and access control

### CWE References
- CWE-345: Insufficient Verification of Data Authenticity
- CWE-353: Missing Support for Integrity Check
- CWE-502: Deserialization of Untrusted Data

---

## A09:2021 - Security Logging and Monitoring Failures

### Description
Without logging and monitoring, breaches cannot be detected. Insufficient logging,
detection, monitoring, and active response occurs when login, access control, and
server-side input validation failures are not logged with sufficient context,
logs are only stored locally, and alerting thresholds are not defined.

### Common Weaknesses
- Auditable events (logins, failed logins, high-value transactions) not logged
- Warnings and errors generate no, inadequate, or unclear log messages
- Logs not monitored for suspicious activity
- Logs only stored locally without centralization
- Alerting thresholds and response escalation not defined
- Penetration testing and DAST scans do not trigger alerts

### Example in Vulnerable App
The `audit_log` table exists but is never populated - the application performs
no security logging whatsoever.

### Scanner Coverage
- `header_check.py`: Partial detection of logging-related misconfigurations
- `directory_scanner.py`: Detects exposed log files (different issue)

### Remediation
1. Log all login, access control, and server-side input validation failures
2. Ensure logs are in a format that can be consumed by log management solutions
3. Ensure high-value transactions have an audit trail with integrity controls
4. Establish effective monitoring and alerting
5. Establish an incident response and recovery plan

### CWE References
- CWE-117: Improper Output Neutralization for Logs
- CWE-223: Omission of Security-relevant Information
- CWE-532: Insertion of Sensitive Information into Log File
- CWE-778: Insufficient Logging

---

## A10:2021 - Server-Side Request Forgery (SSRF)

### Description
SSRF flaws occur when a web application fetches a remote resource without
validating the user-supplied URL. It allows an attacker to coerce the application
to send a crafted request to an unexpected destination, even behind firewalls,
VPNs, or access control lists.

### Common Weaknesses
- Fetching remote resources based on user input without URL validation
- Accessing internal services via manipulated URLs
- Cloud metadata service access (169.254.169.254)

### Scanner Coverage
- Planned for future scanner versions
- Requires manual testing with appropriate payloads

### Remediation
1. Sanitize and validate all client-supplied input data
2. Enforce URL schema, port, and destination with a positive allowlist
3. Do not send raw responses to clients
4. Disable HTTP redirections
5. Use network segmentation to restrict SSRF impact

### CWE References
- CWE-918: Server-Side Request Forgery

---

## References

- [OWASP Top 10 (2021) Official Page](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [CWE/SANS Top 25 Most Dangerous Software Weaknesses](https://cwe.mitre.org/top25/)
- [NIST National Vulnerability Database](https://nvd.nist.gov/)
