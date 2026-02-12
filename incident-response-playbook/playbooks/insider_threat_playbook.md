# Insider Threat Incident Response Playbook

**Classification:** CONFIDENTIAL - RESTRICTED
**Version:** 2.0
**Last Updated:** 2025-11-15
**Owner:** Security Operations Center / Insider Threat Program Office
**Review Cycle:** Quarterly

---

## 1. Purpose

This playbook provides structured response procedures for incidents involving malicious, negligent, or compromised insiders. Insider threats require special handling due to employment law considerations, privacy regulations, the need for coordination with HR and Legal, and the sensitivity of investigating current or former employees.

## 2. Scope

This playbook covers:
- Malicious insiders: Deliberate data theft, sabotage, or fraud
- Negligent insiders: Accidental data exposure or policy violations
- Compromised insiders: Employees whose credentials are stolen by external actors
- Departing employees: Resignation or termination with elevated risk indicators
- Third-party insiders: Contractors, vendors, or partners with access to systems

## 3. Critical Principles

1. **Need-to-know:** Limit awareness of the investigation to essential personnel only
2. **Legal coordination:** All actions must be coordinated with Legal and HR
3. **Due process:** Follow organizational policies and applicable labor laws
4. **Evidence preservation:** Maintain forensic integrity for potential litigation
5. **Proportionality:** Response actions must be proportional to the confirmed threat
6. **Blameless for negligence:** Negligent incidents are handled differently from malicious ones

## 4. Severity Classification

| Indicator | SEV-1 (Critical) | SEV-2 (High) | SEV-3 (Medium) | SEV-4 (Low) |
|-----------|-------------------|---------------|-----------------|-------------|
| Intent | Confirmed malicious | Suspected malicious | Negligent | Policy violation |
| Data involved | Trade secrets, large PII | Confidential business data | Internal data | Public data |
| Sabotage risk | Active/imminent | Potential | None | None |
| Access level | Admin/privileged | Standard + sensitive data | Standard | Limited |
| External recipient | Competitor or adversary | Unknown third party | Personal account | None |

---

## Phase 1: Preparation

### Step 1: Insider Threat Program
- Establish a formal Insider Threat Program with executive sponsorship
- Define the Insider Threat Working Group: Security, HR, Legal, IT, Business Units
- Develop clear acceptable use and data handling policies signed by all employees
- Implement annual insider threat awareness training for all employees

### Step 2: Technical Detection Controls
- Deploy User and Entity Behavior Analytics (UEBA) for anomaly detection
- Configure DLP policies for bulk data downloads and transfers to personal accounts
- Implement Privileged Access Management (PAM) with session recording for admin users
- Enable database activity monitoring for sensitive data repositories
- Configure USB device control policies
- Monitor for printing anomalies (large print jobs, after-hours printing)
- Enable cloud application monitoring (Shadow IT detection)

### Step 3: HR Integration
- Establish automated notification from HR to Security for:
  - Employee resignations (especially to competitors)
  - Terminations (voluntary and involuntary)
  - Performance improvement plans (PIP)
  - Significant disciplinary actions
  - Contractor end-of-engagement notices
- Define enhanced monitoring criteria and procedures for departing employees
- Pre-define the termination-day access revocation checklist

### Step 4: Legal Framework
- Maintain current legal guidance on monitoring rights and limitations by jurisdiction
- Ensure acceptable use policies authorize monitoring (employee acknowledgment required)
- Pre-approve investigation procedures with Legal
- Establish relationships with employment law counsel for rapid consultation
- Document data privacy requirements for investigation evidence handling

---

## Phase 2: Detection & Analysis

### Step 5: Identify Insider Threat Indicators
**Behavioral indicators (require HR/Legal coordination to act on):**
- Expressed dissatisfaction or grievances
- Sudden behavioral changes
- Working unusual hours without business justification
- Resistance to access or role changes
- Interest in projects outside their scope

**Technical indicators (detectable by security tools):**
- Bulk data downloads exceeding job function requirements
- Uploads to personal cloud storage (Dropbox, Google Drive, personal OneDrive)
- Email of sensitive files to personal email accounts
- USB mass storage device usage
- Access to systems outside normal job scope
- After-hours access to sensitive systems
- Database queries exceeding normal patterns
- Source code repository cloning outside standard development workflow
- Attempts to access restricted network segments
- Disabling or circumventing security controls (antivirus, DLP)

### Step 6: Validate and Correlate Indicators
**Actions:**
1. Correlate technical indicators with HR context (resignation, PIP, termination)
2. Verify the data access is indeed outside the employee's job function
3. Review the employee's normal access patterns as a baseline
4. Check if there is a legitimate business explanation (project, role change)
5. Consult with the employee's manager ONLY after Legal/HR approval
6. Assess the risk: is this negligence, policy violation, or malicious intent?

**Decision Point:**
- **Legitimate activity:** Document and close
- **Negligent/accidental:** Proceed to Step 7 with HR notification
- **Suspected malicious:** Proceed to Step 7 with full insider threat protocol

### Step 7: Initiate Formal Investigation
**Actions (MUST coordinate with HR and Legal):**
1. Convene the Insider Threat Working Group (Security, HR, Legal)
2. Assign an investigation lead from Security
3. Obtain Legal authorization for enhanced monitoring
4. Document the scope and objectives of the investigation
5. Establish strict need-to-know for investigation details
6. Open a confidential investigation case (separate from standard IR ticketing)
7. Determine if law enforcement notification is appropriate (consult Legal)

### Step 8: Enhanced Monitoring
**With Legal authorization:**
1. Enable full DLP monitoring on the subject's accounts and devices
2. Enable email content inspection for outbound emails
3. Enable web proxy full content logging for the subject's traffic
4. Enable keylogging or screen recording if legally authorized and warranted
5. Monitor badge access and physical access patterns
6. Review all cloud storage sync activity
7. Monitor printing activity

### Step 9: Evidence Collection
**Actions:**
1. Preserve all DLP alerts and violation reports
2. Export email logs showing data transmission to external destinations
3. Capture web proxy logs showing cloud storage uploads
4. Preserve database audit logs showing unauthorized queries
5. Collect badge access records for physical access patterns
6. Preserve UEBA anomaly reports and risk scores
7. Maintain forensic chain of custody for all evidence
8. Store evidence in a restricted-access location with audit logging

### Step 10: Assess Sabotage Risk
**If the insider has privileged/administrative access:**
1. Audit all systems the subject has admin access to for:
   - New cron jobs, scheduled tasks, or startup scripts
   - Modified system configurations or firewall rules
   - Unauthorized user accounts or SSH keys
   - Database triggers or stored procedures
   - Modified application code or build scripts
   - Logic bombs or time-delayed destructive actions
2. Review recent code commits by the subject for backdoors
3. Check for data destruction preparation (DELETE queries, rm scripts)
4. Assess backup integrity for systems the subject can access

---

## Phase 3: Containment

### Step 11: Containment Strategy Selection
**Options (select based on risk and Legal guidance):**

**Option A: Immediate termination and access revocation (High Risk)**
- Used when: active sabotage risk, confirmed malicious intent, significant data theft
- Execute simultaneous access revocation and HR termination meeting
- Must be coordinated to prevent the subject from acting between learning of termination and losing access

**Option B: Controlled access reduction (Medium Risk)**
- Used when: evidence is building but risk does not warrant immediate termination
- Gradually reduce access privileges to limit further damage
- Reduce privileged access while maintaining basic job function access
- Continue monitoring to build the case

**Option C: Monitored continuation (Low Risk / Negligent)**
- Used when: negligent behavior, policy violation without malicious intent
- Maintain monitoring and engage HR for corrective action
- Provide security awareness refresher training

### Step 12: Execute Containment (Option A - Immediate)
**Precise coordination required:**
1. **T-minus preparation:**
   - Schedule HR meeting room
   - Prepare termination documentation (HR)
   - Pre-stage access revocation scripts (IT Security)
   - Notify physical security for building escort
   - Prepare device collection checklist
   - Remove any identified sabotage mechanisms (logic bombs, scheduled tasks)

2. **T-zero execution (simultaneous):**
   - HR escorts subject to private meeting room
   - IT Security executes access revocation:
     - Disable Active Directory account
     - Revoke VPN and remote access tokens
     - Revoke cloud service access (O365, GCP, AWS IAM)
     - Disable badge access
     - Disable MFA tokens
     - Remove from all distribution lists and shared mailboxes
   - Physical security stands by for escort after meeting

3. **Immediately following:**
   - Collect all company devices (laptop, phone, tablet, USB drives)
   - Collect badge and any physical keys
   - Collect any printed materials
   - Change all shared credentials and service accounts the subject knew
   - Rotate secrets for any shared infrastructure (Wi-Fi passwords, shared accounts)

### Step 13: Evidence Preservation Post-Containment
**Actions:**
1. Forensic image the subject's workstation and mobile devices
2. Preserve email mailbox (legal hold)
3. Preserve all cloud storage content
4. Preserve all source code commits and access history
5. Preserve all DLP, UEBA, and monitoring data
6. Document the termination meeting (HR responsibility)
7. Ensure all evidence maintains chain of custody

---

## Phase 4: Eradication

### Step 14: Remove Insider Access and Artifacts
**Actions:**
1. Conduct comprehensive access revocation audit:
   - All Active Directory groups and permissions
   - All cloud service roles and permissions (AWS IAM, Azure RBAC, GCP IAM)
   - VPN and remote access configurations
   - SSH keys on all systems
   - API keys and tokens
   - Database user accounts
   - Application-specific user accounts
   - Shared accounts with known passwords
   - Physical access (badge, keys, combinations)
2. Change all shared credentials the subject had access to
3. Rotate service account passwords the subject could access
4. Remove the subject from code signing certificates and trusted lists

### Step 15: Audit System Integrity
**Actions:**
1. Audit all systems the subject had privileged access to for backdoors:
   - Cron jobs and scheduled tasks
   - Modified system binaries or configuration files
   - Unauthorized network shares or listeners
   - Database triggers and stored procedures
   - Modified application code
   - Infrastructure-as-code changes (Terraform, Ansible, etc.)
2. Run integrity checks against known-good baselines
3. Review recent changes to firewall rules and network ACLs
4. Verify backup integrity for all systems the subject managed

### Step 16: Validate Eradication
**Actions:**
1. Monitor for any access attempts from the former employee
2. Check for previously unknown accounts or access methods
3. Verify no residual automated processes are running under the subject's context
4. Conduct a targeted threat hunt for the subject's known TTPs
5. Verify all identified sabotage mechanisms have been removed

---

## Phase 5: Recovery

### Step 17: System Recovery
**Actions:**
1. Restore any data or systems damaged by the insider
2. Verify integrity of all data repositories the subject had access to
3. Re-assign the subject's responsibilities to other team members
4. Transfer ownership of shared resources and projects
5. Update documentation, runbooks, and procedures the subject maintained

### Step 18: Legal and Regulatory Actions
**Actions:**
1. Work with Legal to assess civil and criminal remedies:
   - Trade secret misappropriation (DTSA, state laws)
   - Computer fraud (CFAA if applicable)
   - Breach of fiduciary duty
   - Breach of employment agreement (NDA, non-compete)
2. If data was exfiltrated to a competitor: pursue injunctive relief (TRO/preliminary injunction)
3. Send cease-and-desist to the receiving party (competitor, personal storage provider)
4. Assess regulatory notification requirements for exposed data
5. File law enforcement reports if criminal prosecution is warranted
6. Document everything for litigation support

---

## Phase 6: Post-Incident Activity

### Step 19: Post-Incident Review
**Conduct within 5 business days (restricted attendance - need-to-know only):**
1. Review the full investigation timeline
2. Assess detection effectiveness: how long before the activity was noticed?
3. Identify gaps in monitoring that allowed the activity to continue
4. Evaluate HR-Security integration: was the resignation flagged timely?
5. Assess the effectiveness of access controls and least-privilege enforcement
6. Review the containment coordination: was access revocation executed cleanly?

### Step 20: Program Improvements
**Actions:**
1. Enhance UEBA rules based on observed insider behavior patterns
2. Implement automated HR event correlation with security monitoring
3. Strengthen departing employee procedures:
   - Immediate enhanced monitoring upon resignation notice
   - Access reduction for departing employees during notice period
   - Mandatory exit interview with security component
4. Enforce least-privilege access reviews quarterly
5. Implement Privileged Access Management (PAM) with session recording
6. Require dual authorization for destructive operations on critical systems
7. Establish data loss prevention policies for departing employees
8. Review and update NDAs and non-compete agreements

### Step 21: Documentation
**Actions:**
1. Generate confidential incident report (Legal review required before distribution)
2. Update the insider threat risk register
3. Document investigation procedures and evidence for potential litigation
4. Archive case file per legal hold requirements
5. Update insider threat playbook with lessons learned

---

## Appendix A: Insider Threat Risk Indicators Matrix

| Category | Indicator | Risk Level | Action |
|----------|-----------|------------|--------|
| HR Event | Resignation to competitor | High | Immediate enhanced monitoring |
| HR Event | Involuntary termination | High | Pre-termination access audit |
| HR Event | Performance improvement plan | Medium | Enhanced monitoring |
| HR Event | Passed over for promotion | Low-Medium | Awareness monitoring |
| Technical | Bulk data download | Medium-High | Investigate and verify |
| Technical | Cloud storage uploads | Medium | Verify business justification |
| Technical | After-hours privileged access | Medium | Verify with manager |
| Technical | New cron job on production server | High | Immediate investigation |
| Technical | Disabling security tools | High | Immediate investigation |
| Technical | Access outside job scope | Medium | Investigate |

## Appendix B: Termination-Day Access Revocation Checklist

- [ ] Active Directory account disabled
- [ ] Email account disabled (mailbox preserved for legal hold)
- [ ] VPN access revoked
- [ ] MFA tokens revoked
- [ ] Cloud service access revoked (O365, AWS, GCP, Azure)
- [ ] Badge access disabled
- [ ] Remote desktop access removed
- [ ] SSH keys removed from all servers
- [ ] Shared account passwords rotated
- [ ] Wi-Fi credentials rotated (if shared)
- [ ] Application-specific accounts disabled
- [ ] Code repository access revoked
- [ ] Database user accounts disabled
- [ ] Removed from shared mailboxes and distribution lists
- [ ] Laptop, phone, and other devices collected
- [ ] Physical keys and badges collected
- [ ] Personal items from desk allowed (supervised)

## Appendix C: Evidence Categories for Insider Investigations

| Evidence Type | Source | Retention |
|---------------|--------|-----------|
| Email content and logs | Mail server, eDiscovery | Legal hold |
| Web proxy logs | Proxy server, SWG | 90 days minimum |
| DLP violation reports | DLP platform | Duration of investigation + litigation hold |
| UEBA anomaly reports | UEBA platform | Duration of investigation |
| Badge access records | Physical security system | 1 year |
| Database audit logs | DAM platform | 1 year |
| Endpoint telemetry | EDR platform | 90 days |
| Cloud access logs | CASB, cloud provider | 1 year |
| File access logs | File server audit, CASB | 90 days |
| Device forensic image | Forensic workstation | Duration of litigation |

---

*This playbook is RESTRICTED. Distribution limited to Insider Threat Program members and authorized investigators. Report any gaps to the Insider Threat Program Office.*
