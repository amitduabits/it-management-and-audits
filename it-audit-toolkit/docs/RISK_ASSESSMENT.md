# Risk Assessment Methodology

This document describes the quantitative risk assessment methodology used by the IT Audit Toolkit for scoring audit findings, calculating compliance metrics, and generating risk-based prioritization.

---

## Table of Contents

1. [Risk Assessment Overview](#risk-assessment-overview)
2. [Likelihood Scale](#likelihood-scale)
3. [Impact Scale](#impact-scale)
4. [Risk Matrix](#risk-matrix)
5. [Severity Classification](#severity-classification)
6. [Control Risk Scoring](#control-risk-scoring)
7. [Finding Risk Scoring](#finding-risk-scoring)
8. [Compliance Percentage Calculation](#compliance-percentage-calculation)
9. [Engagement-Level Aggregation](#engagement-level-aggregation)
10. [Remediation Timeline Standards](#remediation-timeline-standards)
11. [Risk Heat Map Interpretation](#risk-heat-map-interpretation)
12. [Calibration Guidance](#calibration-guidance)

---

## Risk Assessment Overview

The IT Audit Toolkit employs a quantitative risk scoring methodology based on a 5x5 likelihood-impact matrix. This approach provides:

- **Consistency**: All risks are evaluated against the same scale and criteria
- **Objectivity**: Numeric scores reduce subjectivity in risk classification
- **Prioritization**: Scores enable clear ordering of remediation priorities
- **Communication**: Visual heat maps and severity labels communicate risk posture to stakeholders

### Formula

```
Risk Score = Likelihood x Impact
```

Where:
- **Likelihood** ranges from 1 (Rare) to 5 (Almost Certain)
- **Impact** ranges from 1 (Negligible) to 5 (Severe)
- **Risk Score** ranges from 1 to 25

---

## Likelihood Scale

The likelihood scale represents the probability that a threat will exploit a vulnerability or that a control deficiency will result in a negative outcome within a 12-month period.

| Level | Rating | Probability | Description | Examples |
|-------|--------|-------------|-------------|----------|
| 1 | Rare | < 5% | Highly unlikely to occur; no historical precedent in the organization | Novel zero-day targeting specific technology not widely known |
| 2 | Unlikely | 5-20% | Could occur but not expected; minimal historical precedent | Targeted attack by nation-state actor against a non-critical-infrastructure entity |
| 3 | Possible | 20-50% | May occur; some historical precedent or industry trends suggest increasing probability | Phishing attack leading to credential compromise; insider misuse of broad access rights |
| 4 | Likely | 50-80% | Expected to occur; similar events have occurred in the organization or commonly in the industry | Exploitation of unpatched critical vulnerability with public exploit code; ransomware attack on organization without robust backup |
| 5 | Almost Certain | > 80% | Will almost certainly occur; events of this nature occur regularly | Attempted unauthorized access to internet-facing systems; brute force attacks against public authentication endpoints |

### Factors Increasing Likelihood
- Control is fully manual with no automation
- Control relies on a single individual (key person dependency)
- Organization operates in a high-threat industry (financial services, healthcare)
- Similar incidents have occurred in the past 12 months
- Industry threat intelligence indicates active exploitation
- Control has been identified as deficient in prior audits without remediation

### Factors Decreasing Likelihood
- Control is fully automated with no manual intervention
- Multiple layers of defense (defense in depth)
- Continuous monitoring with automated alerting
- Regular testing and validation of the control
- Strong security culture with trained personnel

---

## Impact Scale

The impact scale represents the magnitude of harm to the organization if the risk materializes.

| Level | Rating | Description | Financial | Operational | Regulatory | Reputational |
|-------|--------|-------------|-----------|-------------|------------|--------------|
| 1 | Negligible | Minimal effect; absorbed by normal operations | < $10K | No disruption | No regulatory attention | No external visibility |
| 2 | Minor | Limited, short-term effect | $10K - $100K | Brief disruption (< 4 hours) | Regulatory inquiry possible | Limited local media |
| 3 | Moderate | Significant effect requiring management attention | $100K - $1M | Extended disruption (4-24 hours) | Regulatory investigation | Regional media coverage |
| 4 | Major | Serious effect on operations or financial position | $1M - $10M | Major disruption (1-7 days) | Regulatory sanctions/fines | National media coverage |
| 5 | Severe | Existential threat; critical to organizational survival | > $10M | Extended outage (> 7 days) | License revocation; criminal liability | Major loss of customer trust |

### Impact Dimensions

When assessing impact, consider all relevant dimensions:

1. **Financial Impact**: Direct costs (fines, remediation, legal fees) and indirect costs (lost revenue, customer churn)
2. **Operational Impact**: Disruption to business processes, service availability, and productivity
3. **Regulatory Impact**: Compliance violations, regulatory sanctions, and mandatory reporting obligations
4. **Reputational Impact**: Customer trust, brand value, market position, and stakeholder confidence
5. **Data Impact**: Volume and sensitivity of data affected (PII, PHI, financial records, trade secrets)

The highest impact across all dimensions determines the overall impact rating.

---

## Risk Matrix

The 5x5 risk matrix maps every combination of likelihood and impact to a risk score:

```
                              I M P A C T
                    Negligible  Minor  Moderate  Major  Severe
                        (1)     (2)      (3)     (4)     (5)
                    +--------+--------+--------+--------+--------+
    Almost          |        |        |        |  ****  |  ****  |
    Certain (5)     |   5    |   10   |   15   |  *20*  |  *25*  |
                    +--------+--------+--------+--------+--------+
L   Likely (4)      |   4    |   8    |   12   |   16   |  *20*  |
I                   +--------+--------+--------+--------+--------+
K   Possible (3)    |   3    |   6    |   9    |   12   |   15   |
E                   +--------+--------+--------+--------+--------+
L   Unlikely (2)    |   2    |   4    |   6    |   8    |   10   |
I                   +--------+--------+--------+--------+--------+
H   Rare (1)        |   1    |   2    |   3    |   4    |   5    |
O                   +--------+--------+--------+--------+--------+
O
D
```

Color coding:
- **Red (Critical)**: Scores 20-25
- **Orange (High)**: Scores 12-19
- **Yellow (Medium)**: Scores 6-11
- **Green (Low)**: Scores 2-5
- **Blue (Informational)**: Score 1

---

## Severity Classification

Risk scores are mapped to five severity levels that drive response timelines and escalation:

| Severity | Score Range | Color | Response Required |
|----------|------------|-------|-------------------|
| **Critical** | 20-25 | Red (#dc3545) | Immediate executive attention; remediation within 7 days |
| **High** | 12-19 | Orange (#fd7e14) | Priority remediation within 30 days; management notification |
| **Medium** | 6-11 | Yellow (#ffc107) | Standard remediation within 90 days |
| **Low** | 2-5 | Green (#28a745) | Planned remediation within 180 days |
| **Informational** | 1 | Blue (#17a2b8) | Noted for awareness; no mandatory action |

---

## Control Risk Scoring

When evaluating individual controls during checklist execution, the toolkit derives risk from two factors:

### Control Status to Likelihood Mapping

| Control Status | Default Likelihood | Rationale |
|---------------|-------------------|-----------|
| Effective | 1 (Rare) | Well-functioning control significantly reduces likelihood |
| Partially Effective | 3 (Possible) | Control operates but has gaps that may be exploited |
| Ineffective | 4 (Likely) | Control failure creates high probability of exploitation |
| Not Tested | 3 (Possible) | Conservative assumption; untested controls carry uncertainty |
| Not Applicable | 0 | Excluded from risk calculation |

### Risk Weight to Impact Mapping

Each control in the toolkit has a risk_weight (1-5) assigned by the checklist designer based on the control's importance:

| Risk Weight | Impact Level | Typical Controls |
|------------|-------------|-----------------|
| 5 | Severe | MFA, privileged access, encryption, DR testing |
| 4 | Major | Password policy, access reviews, change approval, logging |
| 3 | Moderate | RBAC, service accounts, backup monitoring |
| 2 | Minor | Metrics reporting, documentation standards |
| 1 | Negligible | Informational controls, best practice recommendations |

---

## Finding Risk Scoring

Findings can be scored in two ways:

### 1. Explicit Risk Rating
When adding a finding, the auditor can provide specific likelihood and impact values based on professional judgment and the specifics of the deficiency:

```bash
python -m src.cli add-finding --audit data/audit.json \
  --title "Unencrypted Database Backups" \
  --severity critical \
  --description "Production database backups stored without encryption"
```

### 2. Severity-Derived Risk Rating
If no explicit risk rating is provided, the toolkit derives default scores from the severity classification:

| Finding Severity | Default Likelihood | Default Impact | Default Score |
|-----------------|-------------------|---------------|---------------|
| Critical | 5 | 5 | 25 |
| High | 4 | 4 | 16 |
| Medium | 3 | 3 | 9 |
| Low | 2 | 2 | 4 |
| Informational | 1 | 1 | 1 |

Auditors are encouraged to provide explicit risk ratings whenever possible, as they produce more accurate risk assessment than severity-derived defaults.

---

## Compliance Percentage Calculation

Compliance percentage represents the proportion of tested controls that are operating effectively.

### Formula

```
Compliance % = (Effective + 0.5 x Partially Effective) / Tested Controls x 100
```

Where:
- **Effective**: Controls assessed as fully operational
- **Partially Effective**: Controls that operate but have identified gaps (weighted at 50%)
- **Tested Controls**: Total controls assessed, excluding "Not Tested" and "Not Applicable"

### Examples

| Scenario | Effective | Partial | Ineffective | N/A | Not Tested | Compliance % |
|----------|-----------|---------|-------------|-----|------------|-------------|
| Strong controls | 8 | 1 | 1 | 0 | 0 | (8 + 0.5) / 10 = 85.0% |
| Mixed results | 4 | 3 | 3 | 0 | 0 | (4 + 1.5) / 10 = 55.0% |
| Weak controls | 2 | 1 | 7 | 0 | 0 | (2 + 0.5) / 10 = 25.0% |
| With exclusions | 5 | 0 | 2 | 3 | 0 | 5 / 7 = 71.4% |

### Compliance Thresholds

| Level | Threshold | Interpretation |
|-------|-----------|---------------|
| Strong | >= 80% | Controls are generally effective with minor gaps |
| Adequate | 60-79% | Notable deficiencies requiring attention |
| Weak | 40-59% | Significant control failures present |
| Critical | < 40% | Fundamental control breakdown; immediate action needed |

---

## Engagement-Level Aggregation

At the engagement level, metrics are aggregated across all audit areas:

### Overall Compliance
Calculated using the same formula as area-level compliance but across all controls in the engagement.

### Overall Risk Score
The mean of all non-zero control risk scores across the engagement. This provides a single metric representing the average risk exposure.

### Risk Distribution
The full 5x5 matrix populated with counts of controls at each likelihood-impact intersection. This drives the risk heat map visualization.

---

## Remediation Timeline Standards

| Severity | Timeline | Escalation |
|----------|----------|------------|
| Critical | 7 days | CISO / Executive Committee immediately |
| High | 30 days | IT Director within 5 days |
| Medium | 90 days | IT Manager during regular reporting cycle |
| Low | 180 days | Tracked in remediation plan; reviewed quarterly |
| Informational | None | Documented for awareness |

---

## Risk Heat Map Interpretation

The risk heat map is a visual representation of the 5x5 matrix with cell colors indicating severity and cell values showing the count of controls at that risk intersection.

### Reading the Heat Map

- **Dense clustering in red/orange cells**: Indicates a high overall risk posture with many controls operating ineffectively on important (high-weight) controls
- **Dense clustering in green/blue cells**: Indicates a strong control environment with most controls operating effectively
- **Spread across the matrix**: Indicates a mixed environment requiring targeted remediation in specific areas
- **Empty heat map**: May indicate insufficient testing or a very small audit scope

### Actionable Insights

1. Controls in red cells (score 20-25) require immediate attention
2. The total count of controls in orange and red cells indicates the volume of urgent remediation work
3. Trends between audits (comparing heat maps) show whether the control environment is improving or deteriorating

---

## Calibration Guidance

To maintain consistency across audit engagements and audit teams, the following calibration practices are recommended:

### Before the Engagement
- Review the likelihood and impact scales with all audit team members
- Discuss the organization's risk appetite and tolerance levels
- Review relevant industry benchmarks and regulatory expectations
- Calibrate on 2-3 sample findings to ensure team alignment

### During the Engagement
- When uncertain between two likelihood or impact levels, discuss with a peer
- Document the rationale for each risk rating in the finding record
- Consider all impact dimensions, not just the most obvious one
- Use the severity classification as a sanity check (does the computed severity feel right?)

### After the Engagement
- Review all findings as a team to ensure consistency
- Compare risk ratings across findings for logical consistency (a critical finding should not have a lower risk score than a high finding)
- Adjust ratings if new information emerges during the reporting phase
