# IT Audit Methodology

This document describes the structured methodology used by the IT Audit Toolkit for planning, executing, and reporting on Information Technology audits.

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: Planning](#phase-1-planning)
3. [Phase 2: Fieldwork](#phase-2-fieldwork)
4. [Phase 3: Analysis and Reporting](#phase-3-analysis-and-reporting)
5. [Phase 4: Follow-Up](#phase-4-follow-up)
6. [Risk-Based Audit Approach](#risk-based-audit-approach)
7. [Evidence Standards](#evidence-standards)
8. [Quality Assurance](#quality-assurance)

---

## Overview

The IT Audit Toolkit employs a risk-based audit methodology aligned with the ISACA IT Audit and Assurance Standards (ITAF). The methodology consists of four primary phases that together form a complete audit lifecycle:

```
+-------------+     +-------------+     +-------------------+     +-----------+
|  PLANNING   | --> |  FIELDWORK  | --> | ANALYSIS/REPORTING| --> | FOLLOW-UP |
+-------------+     +-------------+     +-------------------+     +-----------+
| - Scoping   |     | - Testing   |     | - Risk scoring    |     | - Track   |
| - Risk ID   |     | - Evidence  |     | - Finding write-up|     |   remediation
| - Resources |     | - Interviews|     | - Draft report    |     | - Retest  |
| - Timeline  |     | - Sampling  |     | - Mgmt response   |     | - Close   |
+-------------+     +-------------+     +-------------------+     +-----------+
```

### Guiding Principles

- **Risk-Based Focus**: Audit effort is concentrated on areas of highest risk to the organization
- **Evidence-Driven**: All conclusions are supported by documented, verifiable evidence
- **Professional Skepticism**: Auditors maintain an objective, questioning mindset throughout
- **Proportionality**: Testing depth is proportional to the risk level and materiality of the control
- **Communication**: Findings are communicated clearly with actionable recommendations

---

## Phase 1: Planning

The planning phase establishes the foundation for an effective audit. Thorough planning ensures audit resources are directed at the most significant risks and that the engagement is executed efficiently.

### 1.1 Engagement Initiation

**Objective**: Establish the audit mandate and define the engagement parameters.

Activities:
- Review audit charter and authority
- Identify the audit sponsor and key stakeholders
- Define the engagement type (compliance, operational, integrated, investigative)
- Establish the reporting line and independence requirements
- Confirm engagement timeline and resource availability

### 1.2 Preliminary Risk Assessment

**Objective**: Identify and prioritize IT risks to focus audit scope on highest-risk areas.

Activities:
- Review prior audit reports and outstanding findings
- Analyze industry threat intelligence and emerging risks
- Review recent security incidents and near-misses
- Assess organizational changes (mergers, new systems, personnel changes)
- Interview management to understand current risk concerns
- Review regulatory landscape and compliance obligations

### 1.3 Scope Definition

**Objective**: Define the boundaries of the audit engagement clearly and completely.

The scope document should address:
- **Systems in scope**: Specific applications, databases, servers, and network segments
- **Audit domains**: Which control areas will be examined (access control, change management, etc.)
- **Time period**: The audit period under examination
- **Locations**: Physical and logical locations included
- **Exclusions**: Explicitly state what is out of scope and why
- **Limitations**: Any constraints that may affect audit coverage

### 1.4 Audit Program Development

**Objective**: Create detailed test procedures for each in-scope control.

Activities:
- Select relevant checklists from the toolkit's library
- Customize control test procedures based on the client's environment
- Define sample sizes based on population size and control frequency
- Identify required evidence for each test procedure
- Assign audit team members to specific audit areas
- Establish the fieldwork schedule

### 1.5 Resource Planning

**Objective**: Ensure adequate and qualified resources are allocated.

Considerations:
- Technical expertise required (network, database, cloud, application)
- Certifications and qualifications (CISA, CISSP, CISM, CRISC)
- Tools and access requirements
- Budget and timeline constraints
- Client availability for interviews and evidence provision

---

## Phase 2: Fieldwork

Fieldwork is the execution phase where controls are tested and evidence is collected. This is typically the most resource-intensive phase of the audit.

### 2.1 Opening Conference

**Objective**: Establish expectations and communication protocols with the client.

Agenda items:
- Introduce the audit team and their responsibilities
- Confirm the audit scope and timeline
- Establish the evidence request process
- Define communication channels (status meetings, email protocols)
- Discuss escalation procedures for identified issues
- Set expectations for management responses

### 2.2 Control Testing

**Objective**: Evaluate the design and operating effectiveness of IT controls.

#### Design Effectiveness Testing
Determine whether the control, as designed, would achieve its objective. This involves:
- Reviewing policy and procedure documentation
- Evaluating the logical design of the control
- Assessing whether the control addresses the relevant risk
- Identifying design gaps where the control does not fully address the risk

#### Operating Effectiveness Testing
Determine whether the control operates as designed over the audit period. Testing methods include:

| Method | Description | When to Use |
|--------|-------------|-------------|
| **Inquiry** | Interview control owners about processes and procedures | Initial understanding; supplement with corroborating evidence |
| **Observation** | Watch the control being performed | Real-time controls (physical access, monitoring) |
| **Inspection** | Examine documents, records, and system configurations | Configuration controls, documentation reviews |
| **Re-performance** | Independently execute the control procedure | Critical controls, automated controls, calculations |

### 2.3 Evidence Collection

**Objective**: Gather sufficient, relevant, and reliable evidence to support audit conclusions.

Evidence classification:
- **Documents**: Policies, procedures, contracts, forms
- **System outputs**: Configuration exports, log files, reports
- **Screenshots**: System configuration screens, access control settings
- **Observations**: Notes from walkthroughs and inspections
- **Interview notes**: Documented conversations with control owners
- **Re-performance results**: Auditor-generated test outputs

Evidence quality attributes:
- **Sufficient**: Enough evidence to support the conclusion
- **Relevant**: Evidence relates directly to the control objective
- **Reliable**: Evidence is from a trustworthy source
- **Timely**: Evidence covers the audit period under review

### 2.4 Sampling Methodology

**Objective**: Select representative samples for testing when 100% testing is not practical.

Sample size guidelines:

| Control Frequency | Population Size | Recommended Sample |
|-------------------|-----------------|--------------------|
| Annually | 1 | 1 (test all) |
| Quarterly | 4 | 2-4 |
| Monthly | 12 | 5-8 |
| Weekly | 52 | 15-25 |
| Daily | 250+ | 25-40 |
| Per occurrence | Varies | 25 (minimum) |

When exceptions are found, consider expanding the sample to determine whether the exception is isolated or systemic.

### 2.5 Working with the Toolkit Checklists

Each toolkit checklist provides structured control testing guidance:

1. **Run the checklist**: `python -m src.cli run-checklist --audit <file> --checklist <name>`
2. **For each control**, the toolkit displays:
   - Control objective and description
   - Detailed test procedure
   - Expected evidence to collect
   - Framework mapping references
3. **Record the assessment**: Effective, Partially Effective, Ineffective, or Not Applicable
4. **Document auditor notes**: Observations, exceptions, and evidence references
5. **Progress is saved automatically** after checklist completion

---

## Phase 3: Analysis and Reporting

The analysis and reporting phase transforms fieldwork results into actionable findings and a professional audit report.

### 3.1 Risk Assessment

**Objective**: Quantify the risk associated with identified control deficiencies.

The toolkit uses a 5x5 likelihood x impact risk matrix:

| | Negligible (1) | Minor (2) | Moderate (3) | Major (4) | Severe (5) |
|---|---|---|---|---|---|
| **Almost Certain (5)** | 5 | 10 | 15 | 20 | **25** |
| **Likely (4)** | 4 | 8 | 12 | 16 | **20** |
| **Possible (3)** | 3 | 6 | 9 | 12 | 15 |
| **Unlikely (2)** | 2 | 4 | 6 | 8 | 10 |
| **Rare (1)** | 1 | 2 | 3 | 4 | 5 |

Risk scores map to severity classifications:
- **Critical (20-25)**: Requires immediate executive attention and remediation within 7 days
- **High (12-19)**: Priority remediation within 30 days
- **Medium (6-11)**: Standard remediation within 90 days
- **Low (2-5)**: Planned remediation within 180 days
- **Informational (1)**: Noted for awareness, no action required

### 3.2 Finding Documentation

Each finding is documented with the following structure:

1. **Title**: Concise description of the deficiency
2. **Severity**: Risk-based severity classification
3. **Description**: Detailed explanation of what was found
4. **Root Cause**: Why the deficiency exists
5. **Business Impact**: Potential consequence if not remediated
6. **Recommendation**: Specific, actionable remediation steps
7. **Evidence References**: Links to supporting evidence
8. **Related Controls**: Control IDs associated with the finding

### 3.3 Report Generation

The toolkit generates professional HTML reports containing:

1. **Executive Summary**: High-level metrics and risk posture overview
2. **Scope and Methodology**: What was audited and how
3. **Compliance Dashboard**: Per-area compliance percentages
4. **Risk Heat Map**: Visual representation of risk distribution
5. **Detailed Findings**: Individual findings with full context
6. **Remediation Roadmap**: Prioritized list of remediation actions

### 3.4 Management Response

Before finalizing the report, findings are shared with management for:
- Factual accuracy validation
- Management response and action plan
- Remediation timeline commitment
- Risk acceptance documentation (if applicable)

---

## Phase 4: Follow-Up

The follow-up phase ensures that audit findings are actually remediated and controls are improved.

### 4.1 Remediation Tracking

- Assign finding owners responsible for remediation
- Establish milestone dates for complex remediation efforts
- Track status updates at agreed-upon intervals
- Escalate overdue findings to appropriate management level

### 4.2 Validation Testing

When management reports that a finding has been remediated:
- Review evidence of the corrective action
- Re-perform the original test procedure
- Validate that the remediation addresses the root cause
- Update the finding status (remediated, partially remediated, or still open)

### 4.3 Closure

A finding is closed when:
- Remediation has been validated through re-testing
- Management has formally accepted the residual risk (for risk-accepted findings)
- The control environment has changed, making the finding no longer applicable

---

## Risk-Based Audit Approach

The toolkit prioritizes audit effort based on risk significance:

### Inherent Risk Assessment
Evaluate the raw risk without considering controls:
- Data sensitivity (PII, financial, health records)
- System criticality (revenue-generating, customer-facing)
- Regulatory exposure (PCI, SOX, GDPR, HIPAA)
- Threat landscape (internet-facing, complex integrations)
- History (prior incidents, past audit findings)

### Control Risk Assessment
Evaluate the likelihood that controls will fail to prevent or detect issues:
- Control design maturity
- Operating consistency
- Automation level (manual vs. automated)
- Monitoring and oversight

### Detection Risk
The risk that audit procedures will fail to detect a material control deficiency. Managed through:
- Adequate sample sizes
- Multiple testing methods
- Professional skepticism
- Peer review of work papers

---

## Evidence Standards

### Documentation Requirements

All audit evidence must be:
- Labeled with a unique identifier (evidence ID)
- Linked to the specific control or finding it supports
- Dated with the collection date
- Attributed to the collecting auditor
- Stored securely with restricted access

### Retention

Audit work papers and evidence should be retained for a minimum of:
- 7 years for SOX-related audits
- 6 years for HIPAA-related audits
- 5 years for general IT audits
- Per applicable regulatory requirements

---

## Quality Assurance

### Peer Review
All findings and work papers should be reviewed by a second auditor before inclusion in the report. The reviewer should verify:
- Test procedures were properly executed
- Evidence supports the conclusion
- Findings are accurately described
- Risk ratings are appropriately calibrated

### Report Review
The draft report should be reviewed for:
- Factual accuracy
- Consistency in severity ratings
- Clarity and professionalism of language
- Completeness of recommendations
- Proper formatting and structure
