# Severity Rating Framework

## Overview

This document describes the severity rating methodology used by the Incident Response Playbook Engine. The framework combines CVSS-inspired technical scoring with business impact assessment to produce a composite severity rating that accurately reflects the organizational risk of an incident.

---

## Composite Severity Model

The severity calculation uses a weighted composite of two dimensions:

```
Composite Score = (Technical Score x 0.35) + (Business Impact Score x 0.65)
```

The business impact weighting is intentionally higher than technical severity because organizational risk is driven more by business consequences (data loss, regulatory fines, revenue impact) than by technical exploitation complexity.

---

## Technical Severity Scoring (CVSS-Inspired)

The technical score is derived from a simplified adaptation of the CVSS v3.1 Base Score methodology. It evaluates the intrinsic characteristics of the vulnerability or attack.

### Exploitability Metrics

| Metric | Description | Values |
|--------|-------------|--------|
| **Attack Vector** | How the attacker reaches the target | Network (0.85), Adjacent (0.62), Local (0.55), Physical (0.20) |
| **Attack Complexity** | Difficulty of exploitation | Low (0.77), High (0.44) |
| **Privileges Required** | Access level needed before exploit | None (0.85), Low (0.62), High (0.27) |
| **User Interaction** | Whether a user must participate | None (0.85), Required (0.62) |

### Impact Metrics

| Metric | Description | Values |
|--------|-------------|--------|
| **Confidentiality Impact** | Effect on data confidentiality | High (0.56), Low (0.22), None (0.0) |
| **Integrity Impact** | Effect on data integrity | High (0.56), Low (0.22), None (0.0) |
| **Availability Impact** | Effect on system availability | High (0.56), Low (0.22), None (0.0) |

### Scope
- **Unchanged:** Impact is limited to the vulnerable component
- **Changed:** Impact extends beyond the vulnerable component to other systems

### Base Score Calculation

```
Exploitability = 8.22 x AV x AC x PR x UI

ISC_Base = 1 - ((1 - Confidentiality) x (1 - Integrity) x (1 - Availability))

If Scope Unchanged:
    Impact = 6.42 x ISC_Base

If Scope Changed:
    Impact = 7.52 x (ISC_Base - 0.029) - 3.25 x (ISC_Base - 0.02)^15

If Impact <= 0: Score = 0
If Scope Unchanged: Score = min(Impact + Exploitability, 10.0)
If Scope Changed: Score = min(1.08 x (Impact + Exploitability), 10.0)
```

**Note:** This is a simplified implementation for incident severity estimation. For official CVE scoring, use the FIRST CVSS Calculator.

---

## Business Impact Scoring

The business impact score evaluates the organizational consequences of the incident across five dimensions, each contributing to a 0-10 composite.

### Dimension 1: Data Sensitivity (0-3 points)

| Classification | Score | Description |
|---------------|-------|-------------|
| Public | 0.0 | Publicly available information |
| Internal | 0.5 | Internal use only; low impact if exposed |
| Confidential | 1.5 | Business-sensitive; moderate impact |
| Restricted | 2.5 | Highly sensitive; significant impact |
| Top Secret | 3.0 | Critical; catastrophic if exposed |

### Dimension 2: Records Affected (0-2 points)

| Records | Score | Rationale |
|---------|-------|-----------|
| >1,000,000 | 2.0 | Massive scale; guaranteed media attention |
| 100,001-1,000,000 | 1.5 | Large scale; significant regulatory exposure |
| 10,001-100,000 | 1.0 | Medium scale; notification threshold likely |
| 1,001-10,000 | 0.5 | Small scale; limited exposure |
| 0-1,000 | 0.2 | Minimal records; targeted exposure |

### Dimension 3: System Criticality (0-2 points)

| Tier | Score | Description |
|------|-------|-------------|
| Tier 1 - Critical | 2.0 | Revenue-generating, customer-facing systems |
| Tier 2 - Important | 1.5 | Business operations support systems |
| Tier 3 - Standard | 0.8 | Internal productivity and collaboration |
| Tier 4 - Non-Critical | 0.3 | Development, testing, sandbox environments |

### Dimension 4: Regulatory Exposure (0-2 points)

Scored based on the number and strictness of applicable regulatory frameworks:

| Factor | Score Contribution |
|--------|-------------------|
| Each applicable framework | +0.5 (max 2.0) |
| Notification required | At least 1.5 |
| GDPR applicable | +0.5 additional |
| HIPAA applicable | +0.5 additional |

### Dimension 5: Reputational Impact (0-1 point)

| Level | Score | Indicators |
|-------|-------|------------|
| Critical | 1.0 | Stock price impact, sustained media coverage, executive turnover |
| High | 0.7 | Media coverage, customer churn, brand damage |
| Medium | 0.4 | Industry notice, limited customer impact |
| Low | 0.1 | Internal awareness only |
| Media coverage likely | 0.8 minimum | Regardless of other factors |

---

## Severity Classification Levels

| Level | Score Range | Response Time | Description |
|-------|------------|---------------|-------------|
| **Critical** | 9.0 - 10.0 | Immediate (< 15 min) | Active, widespread compromise with confirmed data loss or significant financial impact. Regulatory notification required. Executive and board-level visibility. |
| **High** | 7.0 - 8.9 | Urgent (< 1 hour) | Confirmed security incident with potential for significant impact. Limited containment or sensitive data exposure. CISO and VP-level notification. |
| **Medium** | 4.0 - 6.9 | Priority (< 4 hours) | Security event requiring investigation. Limited scope or successful containment of known threat. Security Manager notification. |
| **Low** | 1.0 - 3.9 | Standard (< 24 hours) | Minor security event with minimal impact. Routine investigation required. SOC Team Lead notification. |
| **Informational** | 0.0 - 0.9 | Scheduled | Security observation for awareness. No immediate action required. |

---

## Severity Override Rules

Certain conditions automatically elevate severity regardless of the calculated score:

1. **Regulatory notification required** -> Minimum severity: HIGH
2. **Active attacker with persistence** -> Minimum severity: HIGH
3. **Data exfiltration confirmed** -> Minimum severity: HIGH
4. **Ransomware with active encryption** -> Automatic severity: CRITICAL
5. **Insider threat with sabotage indicators** -> Automatic severity: CRITICAL
6. **Critical infrastructure compromise** -> Automatic severity: CRITICAL

---

## Financial Impact Estimation

The severity calculator includes financial impact estimation based on:

| Cost Category | Methodology |
|--------------|-------------|
| **Revenue loss** | Revenue/hour x estimated downtime hours |
| **Regulatory fines** | Framework-specific fine calculators (GDPR: up to 20M EUR or 4% revenue; HIPAA: up to $1.8M per violation; PCI-DSS: $5K-$100K/month) |
| **Notification costs** | $165 per record (industry average from Ponemon/IBM Cost of Data Breach) |
| **Customer churn** | Affected customers x estimated lifetime value impact |
| **Investigation & remediation** | Based on incident complexity and duration |

---

## Using the Severity Calculator

### Quick Assessment (CLI)
```bash
python -m src.cli severity --data-class confidential --records 50000 \
    --system-tier tier_1_critical --frameworks GDPR,CCPA --notification
```

### Programmatic Assessment
```python
from src.severity_calculator import SeverityCalculator, CVSSVector, BusinessImpactFactors

calc = SeverityCalculator()

# Full assessment with CVSS vector
cvss = CVSSVector(
    attack_vector=0.85,        # Network
    attack_complexity=0.77,    # Low
    privileges_required=0.85,  # None
    user_interaction=0.85,     # None
    confidentiality_impact=0.56,  # High
    integrity_impact=0.22,        # Low
    availability_impact=0.0,      # None
)

business = BusinessImpactFactors(
    data_classification=DataClassification.RESTRICTED,
    records_affected=2_300_000,
    system_criticality=SystemCriticality.TIER_1_CRITICAL,
    regulatory_frameworks=["GDPR", "CCPA"],
    notification_required=True,
)

assessment = calc.calculate_severity(cvss_vector=cvss, business_impact=business)
```

---

## References

- FIRST CVSS v3.1 Specification: https://www.first.org/cvss/specification-document
- NIST SP 800-61 Rev. 2: Incident Severity Classification
- IBM/Ponemon Cost of a Data Breach Report
- FAIR (Factor Analysis of Information Risk) methodology
