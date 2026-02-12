# Scanning Methodology

## Overview

SecureAudit Pro employs three scanning engines that perform non-destructive, read-only reconnaissance against authorized targets. All scanning activities follow responsible security testing practices.

## Network Scanning

### Approach: TCP Connect Scan
- Uses full TCP three-way handshake (`connect()`)
- Non-stealth: detectable by IDS/IPS systems (by design -- we are authorized)
- Concurrent scanning via ThreadPoolExecutor for performance
- Configurable timeout and thread limits

### Service Detection
- Known port-to-service mapping (27 common services)
- Banner grabbing via protocol-specific probes (HTTP HEAD, SMTP EHLO)
- Version extraction from banner strings

### Risk Classification
- **High Risk Ports**: FTP (21), Telnet (23), RPC (135), NetBIOS (139), SMB (445), databases, RDP (3389), VNC (5900), Redis (6379), Elasticsearch (9200), MongoDB (27017)
- **Medium Risk Ports**: SMTP (25), DNS (53), HTTP (80), POP3 (110), RPCBind (111), IMAP (143), HTTP-Proxy (8080)
- **Low Risk**: All other identified services

### Finding Generation
- Findings generated for known-dangerous service exposures
- Each finding includes CVSS-aligned severity, evidence, and remediation
- Excessive open port count triggers additional findings

## Web Application Scanning

### Security Headers Analysis
Eight critical security headers are checked:
1. **Strict-Transport-Security** (HSTS)
2. **Content-Security-Policy** (CSP)
3. **X-Frame-Options** (clickjacking protection)
4. **X-Content-Type-Options** (MIME sniffing prevention)
5. **X-XSS-Protection** (legacy XSS filter)
6. **Referrer-Policy** (referrer leakage control)
7. **Permissions-Policy** (browser API restrictions)
8. **Cache-Control** (caching directives)

### SSL/TLS Analysis
- Certificate validity and expiry checking
- Cipher suite strength evaluation
- Certificate chain verification
- Protocol version detection

### Cookie Security
- Secure flag presence (HTTPS only)
- HttpOnly flag (JavaScript access prevention)
- SameSite attribute (CSRF protection)

### CORS Evaluation
- Wildcard origin detection
- Origin reflection testing
- Credential allowance with wildcard check

### Information Disclosure
- Server technology headers (Server, X-Powered-By, etc.)

## DNS Scanning

### Record Enumeration
- Standard records: A, AAAA, MX, NS, TXT, CNAME, SOA
- Uses dnspython library (falls back to socket resolution)

### Email Security
- **SPF**: Record existence, policy strength, DNS lookup count
- **DMARC**: Policy level, reporting configuration, alignment settings

### Infrastructure
- DNSSEC verification
- Nameserver redundancy check
- Wildcard DNS detection

## Limitations

- Network scanning is TCP-only (no UDP scanning)
- Web scanning is passive (no active exploitation or fuzzing)
- DNS scanning is query-based (no zone transfer attempts)
- All findings are point-in-time assessments
- CVSS scores are estimated, not formally calculated

## Ethical Considerations

- All scanning is non-destructive
- No exploitation or payload delivery
- No credential guessing or brute-force
- No data exfiltration or modification
- Results should be handled as confidential
