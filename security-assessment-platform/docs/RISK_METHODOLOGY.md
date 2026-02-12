# Risk Assessment Methodology

## Overview

SecureAudit Pro uses a quantitative risk assessment model that calculates composite risk scores across six security categories. The methodology combines CVSS-aligned severity scoring with organizational risk weighting.

## Risk Categories

| Category | Default Weight | Description |
|----------|---------------|-------------|
| Network Security | 25% | Network infrastructure, ports, services, segmentation |
| Application Security | 20% | Web application headers, CORS, cookies, session management |
| Data Protection | 20% | Encryption (SSL/TLS), email security (SPF/DMARC), data leakage |
| Compliance | 15% | Gaps across ISO 27001, PCI-DSS, and NIST CSF frameworks |
| Operational Security | 10% | Configuration management, change control, DNS infrastructure |
| Third-Party Risk | 10% | Third-party integrations, supply chain indicators |

## Scoring Algorithm

### Step 1: Finding Severity Classification
Each finding receives a CVSS-aligned severity:
- Critical: 9.0-10.0
- High: 7.0-8.9
- Medium: 4.0-6.9
- Low: 0.1-3.9
- Informational: 0.0

### Step 2: Category Raw Score (0-10)
```
For each category:
  score = 0
  score += min(critical_count * 3.0, 10.0)
  score += min(high_count * 1.5, 5.0)
  score += min(medium_count * 0.8, 3.0)
  score += min(low_count * 0.3, 1.5)
  score += min(info_count * 0.1, 0.5)
  raw_score = min(score, 10.0)
```

### Step 3: Weighted Score
```
weighted_score = raw_score * category_weight
```

### Step 4: Overall Risk Score
```
overall_score = sum(weighted_scores for all categories)
```

## Risk Levels

| Level | Score Range | Response Time | Description |
|-------|-----------|---------------|-------------|
| Critical | 8.0 - 10.0 | 24 hours | Immediate action required |
| High | 6.0 - 7.99 | 7 days | Urgent remediation needed |
| Medium | 4.0 - 5.99 | 30 days | Planned remediation required |
| Low | 2.0 - 3.99 | 90 days | Address during maintenance |
| Minimal | 0.0 - 1.99 | 365 days | Monitor and improve |

## 5x5 Risk Matrix

The risk matrix maps findings onto a Likelihood x Impact grid:

### Likelihood Scale
1. **Rare**: May occur only in exceptional circumstances
2. **Unlikely**: Could occur at some time
3. **Possible**: Might occur at some time
4. **Likely**: Will probably occur in most circumstances
5. **Almost Certain**: Expected to occur in most circumstances

### Impact Scale
1. **Negligible**: Minimal impact on operations
2. **Minor**: Minor disruption, easily managed
3. **Moderate**: Significant disruption, some data exposure
4. **Major**: Major disruption, substantial data breach
5. **Catastrophic**: Complete system compromise, regulatory penalties

### Severity-to-Coordinate Mapping
- Critical findings: Likelihood 4-5, Impact 5
- High findings: Likelihood 3-4, Impact 4
- Medium findings: Likelihood 3, Impact 3
- Low findings: Likelihood 2, Impact 2
- Network findings receive +1 likelihood (higher exploitability)

## Customization

Risk category weights can be customized in `config/thresholds.yaml` to match organizational priorities. Weights must sum to 1.0 and are automatically normalized if they do not.
