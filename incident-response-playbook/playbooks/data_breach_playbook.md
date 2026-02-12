# Data Breach Incident Response Playbook

**Classification:** CONFIDENTIAL
**Version:** 2.1
**Last Updated:** 2025-11-15
**Owner:** Security Operations Center
**Review Cycle:** Quarterly

---

## 1. Purpose

This playbook provides step-by-step procedures for responding to a confirmed or suspected data breach involving unauthorized access, acquisition, or exfiltration of sensitive data. It covers the full NIST SP 800-61 incident response lifecycle from detection through post-incident activity.

## 2. Scope

This playbook applies to incidents involving:
- Unauthorized access to databases containing PII, PHI, PCI, or proprietary data
- Confirmed data exfiltration to external destinations
- Unauthorized bulk data queries or exports
- Compromised credentials used to access sensitive data repositories
- Third-party vendor data exposures affecting our data

## 3. Severity Classification

| Indicator | SEV-1 (Critical) | SEV-2 (High) | SEV-3 (Medium) |
|-----------|-------------------|---------------|-----------------|
| Records exposed | >100,000 | 10,000-100,000 | <10,000 |
| Data type | PII+Financial/Health | PII only | Internal only |
| Exfiltration confirmed | Yes | Suspected | No |
| Regulatory notification | Required | Likely | Unlikely |
| Active attacker | Yes | Unknown | No |

---

## Phase 1: Preparation (Pre-Incident)

### Step 1: Maintain Data Inventory
- Maintain current data flow diagrams showing where sensitive data resides
- Classify all data repositories by sensitivity level
- Document data retention policies and legal hold procedures

### Step 2: Ensure Detection Capability
- Verify DLP policies cover all sensitive data categories and egress points
- Confirm database activity monitoring (DAM) is active on all Tier-1 databases
- Validate SIEM correlation rules for anomalous data access patterns
- Test NetFlow visibility on database-tier network segments

### Step 3: Pre-Stage Response Resources
- Maintain current contact list for IR team, legal, PR, and regulatory counsel
- Pre-negotiate retainer agreements with external forensics firms
- Prepare breach notification letter templates for each jurisdiction
- Maintain encrypted communication channels for IR team coordination

### Step 4: Conduct Regular Exercises
- Execute tabletop exercises quarterly using realistic breach scenarios
- Test notification procedures annually with mock breach notifications
- Validate backup and recovery procedures for data repositories

---

## Phase 2: Detection & Analysis

### Step 5: Alert Validation
**Objective:** Confirm the alert is a true positive indicating unauthorized data access.

**Actions:**
1. Review the triggering alert in the SIEM/DLP console
2. Examine the source alert details: timestamp, source, destination, volume, data patterns
3. Cross-reference with database activity monitoring logs for corroborating queries
4. Check NetFlow or packet capture data for anomalous outbound transfers
5. Verify the accessing account's authorization level and normal access patterns
6. Determine if the activity aligns with any known legitimate business process

**Decision Point:** Is this a confirmed data breach or a false positive?
- If **false positive**: Document reasoning, update detection rules, close alert
- If **confirmed or suspected**: Proceed to Step 6

### Step 6: Initial Notification & IR Activation
**Objective:** Activate the incident response team per escalation procedures.

**Actions:**
1. Create an incident ticket in the IR case management system
2. Assign initial severity based on the classification matrix above
3. Notify the Incident Commander per the on-call rotation
4. Activate the IR communication channel (dedicated Slack/Teams/Signal channel)
5. Notify the CISO for SEV-1/SEV-2 incidents
6. Place legal counsel on standby for potential regulatory obligations
7. DO NOT notify non-essential personnel or use general communication channels

### Step 7: Scope the Breach
**Objective:** Determine the full extent of unauthorized data access and exfiltration.

**Actions:**
1. Identify ALL accounts used for unauthorized access (may be more than the initial alert)
2. Query database audit logs for all activity from compromised accounts (past 90 days)
3. Analyze query content to determine exact tables, columns, and records accessed
4. Quantify the volume of data accessed vs. exfiltrated (these may differ)
5. Identify all external destinations data was sent to (IPs, domains, cloud services)
6. Check for lateral movement to other data repositories
7. Determine the attack timeline: initial access, dwell time, exfiltration window
8. Identify the attack vector: how did the attacker gain access?

### Step 8: Classify Affected Data
**Objective:** Determine data categories for regulatory notification assessment.

**Actions:**
1. Map accessed tables/columns to data classification categories:
   - Personally Identifiable Information (PII): names, addresses, SSN, DOB
   - Protected Health Information (PHI): medical records, insurance, diagnoses
   - Payment Card Industry (PCI): card numbers, CVV, expiration dates
   - Intellectual Property (IP): trade secrets, source code, designs
   - Credentials: passwords, hashes, tokens, API keys
2. Quantify affected records per data category
3. Identify affected individuals by jurisdiction (state, country)
4. Determine if data was encrypted at rest and whether encryption keys were also compromised
5. Assess whether exfiltrated data is usable (encrypted, tokenized, hashed)

### Step 9: Assess Business Impact
**Objective:** Quantify organizational impact for executive communication.

**Actions:**
1. Calculate the severity score using the Severity Calculator tool
2. Estimate financial exposure: regulatory fines, notification costs, remediation
3. Assess reputational risk: customer trust, media exposure, stock impact
4. Identify contractual obligations to customers or partners regarding data breaches
5. Determine operational impact on affected systems and business processes

---

## Phase 3: Containment

### Step 10: Short-Term Containment
**Objective:** Stop active data exfiltration immediately while preserving evidence.

**Actions:**
1. **Network isolation:** Apply ACLs to block outbound traffic from affected database servers to all external destinations (except IR team forensic access)
2. **Credential rotation:** Reset all compromised account passwords and revoke active sessions/tokens
3. **Block C2:** Add all known attacker IPs, domains, and URLs to perimeter block lists (firewall, proxy, DNS sinkhole)
4. **Monitor for evasion:** Watch for the attacker pivoting to alternative egress paths
5. DO NOT shut down systems (this destroys volatile evidence)
6. DO NOT delete attacker artifacts yet (preserve for forensics)

### Step 11: Evidence Preservation
**Objective:** Capture volatile and non-volatile evidence before containment alters the environment.

**Actions (in order of volatility):**
1. Capture memory dumps from all affected systems (use WinPmem, LiME, or equivalent)
2. Record active network connections (netstat -anb, ss -tunap)
3. Capture running process list with full command lines and parent processes
4. Record logged-in users and active sessions
5. Capture disk images of affected systems (use write-blockers for originals)
6. Preserve all relevant log files:
   - Database audit logs and query logs
   - Web application server logs
   - Authentication/directory service logs
   - Network flow data and packet captures
   - DLP alert logs
   - Proxy/firewall logs
7. Hash all evidence files (SHA-256) and document chain of custody
8. Store evidence in the designated secure evidence repository

### Step 12: Long-Term Containment
**Objective:** Maintain containment while allowing controlled system restoration.

**Actions:**
1. If the vulnerability is patchable: apply the patch and verify
2. Rebuild compromised systems from known-good images if needed
3. Implement enhanced monitoring on contained systems
4. Verify attacker has no remaining access through alternate paths
5. Move affected systems to an isolated network segment for controlled observation

---

## Phase 4: Eradication

### Step 13: Remove Attacker Persistence
**Objective:** Eliminate all attacker access mechanisms from the environment.

**Actions:**
1. Remove all identified malware, webshells, backdoors, and implants
2. Remove unauthorized cron jobs, scheduled tasks, and startup entries
3. Remove unauthorized SSH keys, certificates, and tokens
4. Audit and remove unauthorized user accounts
5. Verify removal by scanning with updated IOC signatures

### Step 14: Remediate Root Cause
**Objective:** Fix the vulnerability or weakness that enabled the breach.

**Actions:**
1. Patch the exploited vulnerability (SQL injection, API flaw, misconfig, etc.)
2. Rotate ALL credentials that may have been exposed, not just confirmed compromised ones
3. Revoke and reissue API keys, tokens, and certificates
4. Address any misconfigurations that contributed to the breach
5. If root cause was credential reuse: enforce unique credentials across environments

### Step 15: Verify Eradication
**Objective:** Confirm the attacker no longer has access to any systems.

**Actions:**
1. Conduct a targeted threat hunt for the observed TTPs and IOCs
2. Run integrity checks on all remediated systems
3. Verify no new persistence mechanisms have been created
4. Monitor for any callback attempts to known C2 infrastructure
5. Validate that all previously vulnerable entry points are now secured

---

## Phase 5: Recovery

### Step 16: System Restoration
**Objective:** Restore affected systems to normal operation safely.

**Actions:**
1. Verify system integrity before restoring to production
2. Restore data from verified clean backups if needed
3. Apply all security patches and hardening configurations
4. Re-enable services in a controlled, monitored manner
5. Validate application functionality after restoration
6. Confirm no data corruption occurred during the incident

### Step 17: Enhanced Monitoring
**Objective:** Detect any indication of re-compromise during the observation period.

**Actions:**
1. Deploy additional detection rules based on observed attacker TTPs
2. Increase logging verbosity on previously affected systems
3. Set up real-time alerts for any access to previously compromised data
4. Monitor for connections to known attacker infrastructure
5. Maintain enhanced monitoring for a minimum of 30 days post-recovery

---

## Phase 6: Post-Incident Activity

### Step 18: Regulatory Notification
**Objective:** Meet all legal notification obligations within required timeframes.

**Actions:**
1. Determine applicable regulations per jurisdiction and data type:
   - GDPR: 72 hours to supervisory authority; without undue delay to data subjects
   - HIPAA: 60 days to HHS; 60 days to affected individuals
   - PCI-DSS: Immediately to payment brands and acquiring bank
   - State breach notification laws: Varies (typically 30-60 days)
   - CCPA/CPRA: Without unreasonable delay
2. Prepare notification content with Legal review:
   - What happened and when
   - What data was involved
   - What you are doing about it
   - What the individual can do to protect themselves
   - Contact information for questions
3. Coordinate with PR for public-facing communications
4. Offer credit monitoring/identity protection services where appropriate
5. File regulatory notifications and retain proof of filing

### Step 19: Customer and Partner Notification
**Objective:** Inform affected individuals and business partners transparently.

**Actions:**
1. Prepare customer notification letters (work with Legal and PR)
2. Set up a dedicated incident response hotline and FAQ page
3. Notify affected business partners and contractual counterparties
4. Prepare media talking points and Q&A for executive spokesperson
5. Monitor social media and news for coverage; respond per PR guidance

### Step 20: Post-Incident Review
**Objective:** Conduct a blameless review to identify improvements.

**Actions:**
1. Schedule the PIR within 5 business days of incident closure
2. Include all participating teams: IR, SOC, IT Ops, Legal, HR, affected BUs
3. Review the incident timeline end-to-end
4. Document what worked well and what needs improvement
5. Identify specific, actionable improvement recommendations
6. Assign owners and deadlines for each improvement action
7. Update this playbook based on lessons learned

### Step 21: Formal Incident Report
**Objective:** Produce comprehensive documentation for internal and external stakeholders.

**Actions:**
1. Generate the incident report using the reporting tool
2. Include: executive summary, timeline, technical details, impact assessment, actions taken, recommendations
3. Classify the report as CONFIDENTIAL
4. Distribute to authorized stakeholders per the distribution matrix
5. File in the incident archive per retention policy

### Step 22: Control Improvements
**Objective:** Implement systemic improvements to prevent recurrence.

**Actions:**
1. Implement all approved recommendations from the PIR
2. Update detection rules based on observed attack patterns
3. Enhance access controls on affected data repositories
4. Improve network segmentation around data-tier systems
5. Review and strengthen DLP policies
6. Consider implementing data-level encryption or tokenization
7. Schedule follow-up review to verify implementation

---

## Appendix A: Communication Templates

### Internal Escalation Template
```
SUBJECT: [SEVERITY] Data Breach Incident - [INC-ID]
CLASSIFICATION: CONFIDENTIAL

Incident ID: [INC-ID]
Severity: [SEV-1/SEV-2/SEV-3]
Status: [Active/Contained/Resolved]
Incident Commander: [Name]

Summary: [2-3 sentence description]
Affected Systems: [List]
Affected Data: [Categories and estimated volume]
Current Actions: [What is being done now]
Next Briefing: [Time of next update]
```

### Regulatory Notification Template
```
[Organization Name] is writing to notify [Authority] of a personal data
breach pursuant to [Regulation Article/Section].

Date of Discovery: [Date]
Nature of Breach: [Description]
Categories of Data: [List data types]
Approximate Number of Records: [Number]
Likely Consequences: [Assessment]
Measures Taken: [Response actions]
Contact: [DPO/Privacy Officer contact information]
```

## Appendix B: Evidence Checklist

- [ ] Memory dumps from affected systems
- [ ] Network connection state (netstat/ss output)
- [ ] Running process listings
- [ ] Full disk images (forensic copies)
- [ ] Database audit/query logs
- [ ] Web server access and error logs
- [ ] Authentication logs (Active Directory, LDAP, SSO)
- [ ] Network flow data (NetFlow, sFlow)
- [ ] Packet captures from relevant network segments
- [ ] DLP alert logs and matched content
- [ ] Firewall and proxy logs
- [ ] DNS query logs
- [ ] Email logs (if phishing-related)
- [ ] Cloud service access logs (if applicable)
- [ ] Malware samples (webshells, binaries, scripts)

## Appendix C: Regulatory Reference Quick Guide

| Regulation | Notification Deadline | Authority | Individual Notice |
|------------|----------------------|-----------|-------------------|
| GDPR | 72 hours | Supervisory Authority | Without undue delay |
| HIPAA | 60 days | HHS OCR | 60 days |
| PCI-DSS | Immediately | Payment brands | N/A |
| CCPA/CPRA | Without unreasonable delay | CA Attorney General (>500) | Without unreasonable delay |
| SOX | Promptly | SEC | N/A |
| GLBA | As soon as possible | Relevant regulator | As soon as possible |

---

*This playbook is a living document. Report any gaps or suggested improvements to the Security Operations team.*
