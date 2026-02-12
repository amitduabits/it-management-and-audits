# Compliance Framework Mapping

## Overview

SecureAudit Pro maps technical scan findings to three major compliance frameworks. This document details the control-to-finding mappings and assessment methodology.

## ISO 27001:2022 - 20 Key Controls

| Control ID | Control Name | Check Type | Data Source |
|-----------|-------------|------------|-------------|
| A.5.1 | Policies for Information Security | Policy | Attestation |
| A.5.15 | Access Control | Network | Open ports risk level |
| A.5.23 | Cloud Services Security | Policy | Attestation |
| A.6.1 | Screening | Policy | Attestation |
| A.6.3 | Security Awareness Training | Policy | Attestation |
| A.7.1 | Physical Security Perimeters | Policy | Attestation |
| A.7.4 | Physical Security Monitoring | Policy | Attestation |
| A.8.1 | User Endpoint Devices | Network | Remote access ports |
| A.8.3 | Information Access Restriction | Network | Database exposure |
| A.8.5 | Secure Authentication | Web | HSTS + cookie security |
| A.8.7 | Protection Against Malware | Policy | Attestation |
| A.8.9 | Configuration Management | Network | Port exposure ratio |
| A.8.12 | Data Leakage Prevention | Web | Information disclosure |
| A.8.15 | Logging | Policy | Attestation |
| A.8.20 | Network Security | Network | Critical findings |
| A.8.21 | Security of Network Services | Network | Banner exposure |
| A.8.23 | Web Filtering | Web | CSP header |
| A.8.24 | Use of Cryptography | Web | SSL/TLS validity |
| A.8.26 | Application Security Requirements | Web | Security score |
| A.8.28 | Secure Coding | Web | XSS/CORS/Clickjacking |

## PCI-DSS v4.0 - 15 Key Requirements

| Requirement | Name | Check Type | Data Source |
|-----------|------|------------|-------------|
| Req 1.1 | Network Security Controls | Network | Critical findings |
| Req 1.3 | Restrict CDE Access | Network | Database port exposure |
| Req 2.2 | Secure Configuration | Network | Legacy service exposure |
| Req 3.4 | Protect Stored Data | Policy | Encryption attestation |
| Req 4.2 | Encrypt Transmissions | Web | SSL/TLS + HSTS |
| Req 5.2 | Malware Detection | Policy | Anti-malware attestation |
| Req 5.3 | Active Anti-Malware | Policy | Active monitoring attestation |
| Req 6.2 | Secure Development | Web | Security headers |
| Req 6.4 | Public-Facing App Protection | Web | Security score |
| Req 7.2 | Access Management | Network | RDP/VNC exposure |
| Req 8.3 | Strong Authentication | Web | Transport + session security |
| Req 8.6 | Application Account Auth | Network | Unauthenticated services |
| Req 10.2 | Audit Logging | Policy | Logging attestation |
| Req 11.3 | Vulnerability Management | Combined | Critical finding count |
| Req 12.1 | Security Policy | Policy | Policy attestation |

## NIST CSF v2.0 - 20 Subcategories

### Identify (ID) - 4 subcategories
- ID.AM-1: Physical device inventory (Policy)
- ID.AM-2: Software/service inventory (Network: service identification ratio)
- ID.RA-1: Vulnerability identification (Combined: scan coverage)
- ID.GV-1: Security policy (Policy)

### Protect (PR) - 8 subcategories
- PR.AC-1: Identity management (Web: HSTS + cookies)
- PR.AC-3: Remote access management (Network: remote access ports)
- PR.AC-5: Network integrity (Network: critical findings)
- PR.DS-1: Data-at-rest protection (Policy)
- PR.DS-2: Data-in-transit protection (Web: SSL/TLS)
- PR.DS-5: Data leak prevention (Web: information disclosure)
- PR.IP-1: Configuration baseline (Network: legacy services + banners)
- PR.AT-1: Security awareness (Policy)

### Detect (DE) - 4 subcategories
- DE.AE-1: Network baseline (Policy)
- DE.CM-1: Network monitoring (Policy)
- DE.CM-4: Malicious code detection (Policy)
- DE.CM-8: Vulnerability scanning (Combined: scan execution)

### Respond (RS) - 2 subcategories
- RS.RP-1: Incident response plan (Policy)
- RS.AN-1: Alert investigation (Policy)

### Recover (RC) - 2 subcategories
- RC.RP-1: Recovery plan (Policy)
- RC.IM-1: Lessons learned (Policy)

## Assessment Scoring

### Status Definitions
- **Pass**: Control requirement is fully met based on available evidence
- **Fail**: Control requirement is not met; significant gaps identified
- **Partial**: Some aspects of the control are implemented but gaps remain
- **Not Assessed**: Insufficient data to evaluate (typically requires manual verification)

### Score Calculation
- Pass = 1.0, Partial = 0.5, Fail = 0.0, Not Assessed = 0.0
- Category score = average of control scores within category
- Overall score = average of all control scores

## Limitations

- Automated checks provide indicators, not definitive compliance status
- Policy-based controls require manual attestation
- Formal compliance certification requires qualified assessors
- Results should be used as input to a broader compliance program
