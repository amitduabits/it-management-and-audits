# Sample Audit Walkthrough

This document provides a complete, step-by-step walkthrough of an IT audit engagement using the IT Audit Toolkit. The walkthrough uses the included sample audit data for a fictional digital lending company called "QuickLend Pro."

---

## Table of Contents

1. [Scenario Background](#scenario-background)
2. [Phase 1: Creating the Engagement](#phase-1-creating-the-engagement)
3. [Phase 2: Running Checklists](#phase-2-running-checklists)
4. [Phase 3: Documenting Findings](#phase-3-documenting-findings)
5. [Phase 4: Calculating Risk](#phase-4-calculating-risk)
6. [Phase 5: Generating the Report](#phase-5-generating-the-report)
7. [Understanding the Output](#understanding-the-output)
8. [Working with the Sample Data](#working-with-the-sample-data)

---

## Scenario Background

### About QuickLend Pro

QuickLend Pro is a mid-sized fintech company operating a digital lending platform. Key facts:

- **Business**: Online personal and small business loans
- **Volume**: Approximately 50,000 loan applications per month
- **Data Sensitivity**: Handles SSNs, bank account numbers, credit reports, and income verification documents
- **Infrastructure**: Hybrid cloud (AWS for application tier, on-premises Oracle database servers)
- **Employees**: 200 IT staff (grown from 50 in 18 months)
- **Regulatory Environment**: Subject to GLBA, state lending regulations, and PCI-DSS (for payment processing)

### Audit Objectives

The annual IT audit for QuickLend Pro aims to:
1. Evaluate IT general controls protecting borrower data
2. Assess compliance with PCI-DSS v4.0 requirements
3. Review access control mechanisms for sensitive financial data
4. Evaluate change management practices for platform stability
5. Assess backup and disaster recovery readiness
6. Identify control deficiencies and recommend improvements

### Audit Team

- **Maria Chen, CISA, CRISC** - Lead Auditor (access controls, overall management)
- **David Park, CISSP** - Senior Auditor (change management, network security)
- **Sarah Thompson, CISM** - Staff Auditor (data backup, incident response)

---

## Phase 1: Creating the Engagement

### Step 1.1: Initialize the Engagement

Create a new audit engagement with the relevant metadata:

```bash
python -m src.cli new-audit \
  --name "QuickLend Pro Annual IT Audit FY2025" \
  --client "QuickLend Pro Inc." \
  --lead-auditor "Maria Chen, CISA, CRISC" \
  --scope "Comprehensive IT audit covering application infrastructure, data security, and regulatory compliance for the digital lending platform." \
  --output data/quicklend_audit.json
```

**Expected Output:**

The toolkit creates a new engagement JSON file and displays:
- Unique engagement ID
- Engagement metadata confirmation
- List of available checklists

### Step 1.2: Review Available Checklists

Before starting fieldwork, review the available checklists:

```bash
python -m src.cli list-checklists
```

This displays all six checklist domains with their control counts:

| Domain | Controls |
|--------|----------|
| Access Control | 15 |
| Change Management | 12 |
| Incident Response | 10 |
| Data Backup and Recovery | 10 |
| Network Security | 12 |
| Regulatory Compliance | 10 |

For the QuickLend audit, we will focus on Access Control, Change Management, and Data Backup as the three highest-risk domains based on the preliminary risk assessment.

---

## Phase 2: Running Checklists

### Step 2.1: Access Control Checklist

Run the access control checklist, the highest-priority domain given the sensitive financial data:

```bash
python -m src.cli run-checklist \
  --audit data/quicklend_audit.json \
  --checklist access_control \
  --auditor "Maria Chen, CISA, CRISC"
```

The toolkit presents each of the 15 controls sequentially. For each control, you will see:

```
======================================================================
  Control 1/15: [AC-001] User Account Provisioning Process
======================================================================

  Description:
  Verify that a formal, documented process exists for provisioning
  user accounts...

  Test Procedure:
  1. Obtain the user provisioning policy/procedure document.
  2. Select a sample of 25 user accounts created in the past 6 months...

  Expected Evidence:
  User provisioning policy document, sample access request forms...

  Assessment Status:
    1 = Effective
    2 = Partially Effective
    3 = Ineffective
    4 = Not Applicable
    5 = Not Tested (skip)

  Enter status [1-5]:
```

### Sample Responses for Key Controls

Here is how the QuickLend audit team assessed several key controls:

**AC-001 (User Provisioning)** - Status: **1 (Effective)**
```
Notes: Formal provisioning process in place using ServiceNow. All 25
sampled accounts had approved access requests.
Evidence: policies/IAM/User_Provisioning_Policy_v3.2.pdf
```

**AC-004 (Multi-Factor Authentication)** - Status: **3 (Ineffective)**
```
Notes: MFA enforced for VPN and SSO but NOT for 12 domain admin accounts
and 8 DBA accounts. Oracle console uses legacy RADIUS with password-only.
Evidence: evidence/AC-004/mfa_enrollment_report.csv
```

**AC-005 (Privileged Access Management)** - Status: **3 (Ineffective)**
```
Notes: No PAM solution. Shared credentials in encrypted spreadsheet.
Three service accounts share the same password, not rotated in 14 months.
Evidence: evidence/AC-005/privileged_account_inventory.xlsx
```

After completing all 15 controls, the toolkit displays a summary:

```
+------------------------------------------+
|          Checklist Summary               |
+------------------------------------------+
  Total Controls:           15
  Tested:                   14
  Effective:                 6
  Partially Effective:       3
  Ineffective:               4
  Not Applicable:            1
  Completion:              93.3%
+------------------------------------------+
```

### Step 2.2: Change Management Checklist

```bash
python -m src.cli run-checklist \
  --audit data/quicklend_audit.json \
  --checklist change_management \
  --auditor "David Park, CISSP"
```

### Step 2.3: Data Backup Checklist

```bash
python -m src.cli run-checklist \
  --audit data/quicklend_audit.json \
  --checklist data_backup \
  --auditor "Sarah Thompson, CISM"
```

---

## Phase 3: Documenting Findings

Based on fieldwork observations, the audit team documents seven findings:

### Finding 1: Privileged Accounts Lack MFA (Critical)

```bash
python -m src.cli add-finding \
  --audit data/quicklend_audit.json \
  --title "Privileged Accounts Lack Multi-Factor Authentication" \
  --area "Access Control" \
  --severity critical \
  --description "12 domain admin and 8 DBA accounts do not enforce MFA. Oracle console uses legacy RADIUS supporting password-only access. These accounts have direct access to 2.3M borrower records containing SSNs and financial data." \
  --root-cause "Legacy Oracle authentication does not support modern MFA protocols." \
  --impact "Compromised privileged credentials could expose all borrower records. Estimated financial exposure: \$5-15M." \
  --recommendation "1. Enable MFA for domain admins within 30 days. 2. Deploy SAML proxy for Oracle console within 60 days. 3. Implement PAM solution."
```

### Finding 2: Shared Service Account Credentials (Critical)

```bash
python -m src.cli add-finding \
  --audit data/quicklend_audit.json \
  --title "Service Accounts Using Shared Credentials Without Rotation" \
  --area "Access Control" \
  --severity critical \
  --description "Three production service accounts share the same password, not rotated in 14 months. Credentials stored in spreadsheet accessible to 15 IT staff." \
  --root-cause "No PAM solution. Manual rotation process neglected after responsible admin departed." \
  --impact "Shared credentials create single point of compromise with no attribution." \
  --recommendation "1. Immediately rotate passwords to unique credentials. 2. Implement PAM with automated rotation. 3. Restrict access to need-to-know."
```

### Finding 3: Developers Retain Production Access (High)

```bash
python -m src.cli add-finding \
  --audit data/quicklend_audit.json \
  --title "Developers Retain Production Write Access" \
  --area "Change Management" \
  --severity high \
  --description "Four senior developers have AWS IAM roles with production write access provisioned 9 months ago for emergency fix. Access not time-limited or monitored." \
  --root-cause "Emergency access not revoked after incident resolution. No process for temporary access review." \
  --impact "Developers can introduce unauthorized code changes to production, bypassing CI/CD and change management." \
  --recommendation "1. Revoke standing production access immediately. 2. Implement JIT access mechanism. 3. Enable CloudTrail alerting."
```

### Finding 4: DR Plan Not Tested (High)

```bash
python -m src.cli add-finding \
  --audit data/quicklend_audit.json \
  --title "Disaster Recovery Plan Not Tested Within 12 Months" \
  --area "Data Backup and Recovery" \
  --severity high \
  --description "Last full DR test was March 2024 (20 months ago). RTO achievement was 6.5 hours against 4-hour target. Remediation items from that test are still outstanding." \
  --root-cause "DR testing postponed twice for competing priorities. No enforcement mechanism for testing deadlines." \
  --impact "Cannot confirm ability to recover within RTO. Extended downtime could impact in-flight loan applications." \
  --recommendation "1. Schedule full DR test within 60 days. 2. Address outstanding remediation items. 3. Add DR testing as management KPI."
```

Continue adding the remaining findings for de-provisioning delays (Medium), no formal CAB (Medium), and RTO not achievable (Medium).

---

## Phase 4: Calculating Risk

After documenting all findings, calculate risk scores:

```bash
python -m src.cli calculate-risk --audit data/quicklend_audit.json --verbose
```

**Expected Output:**

```
+-----------------------------------------------+
|       Engagement Risk Assessment              |
+-----------------------------------------------+
  Overall Compliance:   68.5%
  Overall Risk Score:   9.4 / 25.0
  Risk Severity:        MEDIUM
  Controls Tested:      23 / 25
  Total Findings:       7
+-----------------------------------------------+

Compliance by Audit Area:
+-----------------------+----------+--------+-----------+------------+----------+----------+
| Audit Area            | Controls | Tested | Effective | Compliance | Avg Risk | Findings |
+-----------------------+----------+--------+-----------+------------+----------+----------+
| Access Control        | 15       | 14     | 6         | 62.5%      | 11.2     | 3        |
| Change Management     | 4        | 4      | 2         | 75.0%      | 8.5      | 2        |
| Data Backup           | 3        | 3      | 2         | 66.7%      | 10.0     | 2        |
+-----------------------+----------+--------+-----------+------------+----------+----------+

Finding Severity Distribution:
+-----------------+-------+-----------------------+
| Severity        | Count | Bar                   |
+-----------------+-------+-----------------------+
| CRITICAL        |   2   | ████████████████████  |
| HIGH            |   2   | ████████████████████  |
| MEDIUM          |   3   | ██████████████████████|
| LOW             |   0   |                       |
| INFORMATIONAL   |   0   |                       |
+-----------------+-------+-----------------------+

Remediation Roadmap (Top 7):
+---+-----------------------------------------+-----------+-------+---------------------------+
| # | Finding                                 | Severity  | Score | Timeline                  |
+---+-----------------------------------------+-----------+-------+---------------------------+
| 1 | Privileged Accounts Lack MFA            | CRITICAL  |  20   | Immediate - within 7 days |
| 2 | Service Accounts Shared Credentials     | CRITICAL  |  20   | Immediate - within 7 days |
| 3 | Developers Retain Production Access     | HIGH      |  16   | Priority - within 30 days |
| 4 | DR Plan Not Tested Within 12 Months     | HIGH      |  15   | Priority - within 30 days |
| 5 | No Formal Change Advisory Board         | MEDIUM    |   9   | Standard - within 90 days |
| 6 | Delayed User De-Provisioning            | MEDIUM    |   9   | Standard - within 90 days |
| 7 | RTO Not Achievable Based on Last Test   | MEDIUM    |  12   | Standard - within 90 days |
+---+-----------------------------------------+-----------+-------+---------------------------+
```

---

## Phase 5: Generating the Report

Generate the final HTML audit report:

```bash
python -m src.cli generate-report \
  --audit data/quicklend_audit.json \
  --output reports/quicklend_audit_report.html \
  --text-summary
```

This generates:
1. A professional HTML report at `reports/quicklend_audit_report.html`
2. A text executive summary printed to the console

The HTML report contains:
- **Cover page** with engagement metadata
- **Executive summary** with key metrics and finding severity distribution
- **Scope and methodology** section
- **Compliance dashboard** with per-area compliance bars
- **Risk heat map** showing control risk distribution
- **Detailed findings** with color-coded severity headers
- **Remediation roadmap** with prioritized actions
- **Confidentiality footer**

---

## Understanding the Output

### Compliance Dashboard

The compliance dashboard shows each audit area with a progress bar:

- **Green (80%+)**: Controls are generally effective
- **Yellow (60-79%)**: Notable gaps requiring attention
- **Orange (40-59%)**: Significant control failures
- **Red (<40%)**: Fundamental control breakdown

For QuickLend Pro:
- Access Control at 62.5% (yellow) indicates several key controls need improvement
- Change Management at 75.0% (yellow) shows the process exists but has gaps
- Data Backup at 66.7% (yellow) shows reliable operations but untested DR capability

### Risk Heat Map

The heat map shows how controls are distributed across the risk matrix. For QuickLend Pro, you would see concentration in the upper-right quadrant (high likelihood, high impact) for the ineffective controls on high-weight items like MFA and PAM, while effective controls cluster in the lower-left (low likelihood, low impact).

### Remediation Roadmap

The roadmap prioritizes findings from most to least urgent. QuickLend Pro's roadmap places the two critical findings (MFA and shared credentials) at the top, requiring immediate action within 7 days.

---

## Working with the Sample Data

The toolkit includes a pre-built sample audit file at `data/sample_audit.json` that contains the complete QuickLend Pro audit data described in this walkthrough.

### Load and Explore the Sample

```bash
# Calculate risk scores from the sample data
python -m src.cli calculate-risk --audit data/sample_audit.json --verbose

# Generate a report from the sample data
python -m src.cli generate-report \
  --audit data/sample_audit.json \
  --output reports/sample_report.html \
  --text-summary
```

### Examine the JSON Structure

The sample audit file demonstrates the complete data model:
- Engagement metadata (ID, name, client, team, dates)
- Three audit areas (Access Control, Change Management, Data Backup)
- Controls with various assessment statuses and auditor notes
- Seven findings with full descriptions, risk ratings, and management responses
- Evidence inventory with references to supporting documentation

This sample data can be used as a template for creating custom audit engagements or for testing customizations to the toolkit.

---

## Tips for Real Engagements

1. **Start with the highest-risk areas**: Focus limited audit time on the most critical domains
2. **Document as you go**: Record auditor notes and evidence references during testing rather than retroactively
3. **Be specific in findings**: Include specific counts, dates, and system names rather than vague statements
4. **Link findings to controls**: Always reference which control(s) the finding relates to
5. **Propose actionable recommendations**: Each recommendation should be specific and achievable
6. **Request management responses promptly**: Do not wait until the report is finalized
7. **Use the sample data as a template**: Model your engagement structure after the sample data
