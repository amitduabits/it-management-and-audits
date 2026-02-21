# Phishing Campaign Incident Response Playbook

**Classification:** CONFIDENTIAL
**Version:** 2.4
**Last Updated:** 2025-11-15
**Owner:** Security Operations Center
**Review Cycle:** Quarterly

---

## 1. Purpose

This playbook covers the response to phishing attacks including bulk phishing campaigns, spear-phishing targeting specific individuals, business email compromise (BEC), and credential harvesting operations. It addresses the full lifecycle from initial report through remediation and control improvements.

## 2. Scope

This playbook applies to:
- Mass phishing campaigns targeting organizational email accounts
- Spear-phishing directed at specific employees or groups
- Business email compromise and wire fraud attempts
- Credential harvesting via fake login portals
- Internal (lateral) phishing from compromised accounts
- Smishing (SMS phishing) and vishing (voice phishing) attacks

## 3. Severity Classification

| Indicator | SEV-1 (Critical) | SEV-2 (High) | SEV-3 (Medium) | SEV-4 (Low) |
|-----------|-------------------|---------------|-----------------|-------------|
| Credential compromise | Multiple privileged accounts | Single privileged or multiple standard | Single standard account | None confirmed |
| Financial fraud attempted | Yes (>$50K) | Yes (<$50K) | No | No |
| Data exfiltration | Confirmed | Suspected | No | No |
| Internal phishing launched | Yes (widespread) | Yes (limited) | No | No |
| Account takeover actions | BEC, data theft, lateral movement | Mailbox access | Login only | No access |

---

## Phase 1: Preparation

### Step 1: Email Security Controls
- Deploy email gateway with anti-phishing, anti-spoofing, and sandbox detonation
- Implement SPF, DKIM, and DMARC (p=reject) on all organizational domains
- Configure external email banners warning users about external senders
- Enable URL rewriting/click-time analysis for embedded links
- Block macro-enabled attachments by default at the email gateway
- Implement lookalike domain monitoring for typosquatting detection

### Step 2: Authentication Hardening
- Deploy phishing-resistant MFA (FIDO2/WebAuthn) for all users (preferred)
- At minimum: TOTP-based MFA for all users; avoid SMS-based MFA
- Implement conditional access policies: block logins from impossible geographies
- Enable session token revocation capabilities for rapid response
- Configure OAuth/SAML application consent policies to prevent consent phishing

### Step 3: User Reporting Program
- Establish and promote a phishing reporting mechanism (report button, dedicated mailbox)
- Implement automated triage of reported phishing emails (SOAR integration)
- Train users to report suspicious emails without interacting with them
- Recognize and reward employees who report phishing promptly

### Step 4: Financial Controls
- Require multi-party authorization for wire transfers above threshold
- Mandate out-of-band verification (phone call) for payment changes and new vendors
- Implement transaction monitoring for anomalous financial activity
- Pre-register approved vendor payment details; flag deviations

---

## Phase 2: Detection & Analysis

### Step 5: Receive & Validate Phishing Report
**Sources of phishing detection:**
- Employee reports via phishing button or dedicated mailbox
- Email gateway automated detection
- SIEM correlation of authentication anomalies post-click
- External notification (partner, vendor, security researcher)
- Impossible travel alerts from identity provider

**Validation actions:**
1. Examine the reported email headers (Return-Path, Received, X-Originating-IP)
2. Analyze the sender domain: is it spoofed, lookalike, or legitimate compromise?
3. Examine embedded URLs without clicking (use URL analysis tools)
4. Detonate attachments in sandbox if present
5. Check threat intelligence feeds for known phishing infrastructure
6. Determine: Is this a targeted (spear-phishing) or bulk campaign?

### Step 6: Determine Blast Radius
**Objective:** Identify all recipients and those who interacted with the phishing content.

**Actions:**
1. Search email gateway logs for all instances of the phishing email (by subject, sender, URL, attachment hash)
2. Determine: how many recipients total?
3. Query web proxy logs: who clicked the phishing URL?
4. Query DNS logs: who resolved the phishing domain?
5. Review authentication logs: are there successful logins from the phishing infrastructure?
6. Check for login attempts from known attacker IPs
7. Identify any credential submissions to the harvesting page (web proxy POST requests)

### Step 7: Assess Account Compromise
**For each user who may have submitted credentials:**
1. Review sign-in logs for anomalous activity (unusual IP, location, device, time)
2. Check for new mail forwarding rules or inbox rules
3. Check for OAuth application consent grants
4. Review sent items for attacker-generated emails (BEC, lateral phishing)
5. Check for mailbox delegation changes
6. Review file access patterns in cloud storage (SharePoint, OneDrive, Google Drive)
7. Check for password changes initiated by the user's account from unknown sources

### Step 8: Identify Attacker Actions
**If account takeover is confirmed:**
1. Document all emails sent from the compromised account during the compromise window
2. Identify any wire transfer requests or payment change requests
3. Check for data accessed or downloaded from email and connected systems
4. Identify internal phishing emails launched from the compromised account
5. Check for new MFA device registrations
6. Review API access logs for programmatic data access
7. Check for Power Automate / Logic Apps / mail flow rules created

---

## Phase 3: Containment

### Step 9: Immediate Account Containment
**Actions (execute in parallel):**
1. Force password reset on all confirmed compromised accounts
2. Revoke ALL active sessions and refresh tokens (Azure AD: Revoke-AzureADUserAllRefreshToken)
3. Disable accounts if active abuse is ongoing and immediate lockout is required
4. Remove any attacker-created mail forwarding rules or inbox rules
5. Remove any unauthorized OAuth application consent grants
6. Remove any new MFA devices registered by the attacker
7. Block the attacker's known login source IPs in conditional access policies

### Step 10: Stop the Phishing Campaign
**Actions:**
1. Block the phishing sender domain/address at the email gateway
2. Block the phishing URL at the web proxy and DNS (sinkhole)
3. Purge the phishing email from ALL mailboxes (not just those who reported it):
   - O365: Search-Mailbox or Content Search + Compliance Search with purge action
   - Google Workspace: Admin email audit with delete
4. Block the phishing domain at the firewall
5. If internal phishing was launched: repeat purge for internally-sent phishing emails
6. Submit the phishing URL and domain to browser safe browsing blocklists

### Step 11: Financial Fraud Prevention
**If BEC wire transfer was attempted:**
1. Contact Accounts Payable/Treasury BY PHONE (not email) to halt the transfer
2. If transfer was initiated: contact the receiving bank to request recall
3. File a complaint with the FBI IC3 and local law enforcement
4. If wire was sent internationally: request the bank to issue a SWIFT recall
5. Document the fraudulent transaction details for insurance and legal proceedings
6. Notify the CFO and legal counsel immediately

### Step 12: Notify Affected Parties
**Actions:**
1. Notify all employees who received the phishing email (after purge)
2. If HR/PII data was requested via BEC: notify HR to disregard and secure data
3. If internal phishing was sent: notify all recipients of the internal campaign
4. Brief executive leadership on scope and impact

---

## Phase 4: Eradication

### Step 13: Remove All Phishing Artifacts
**Actions:**
1. Confirm all phishing emails are purged from all mailboxes
2. Verify all mail forwarding rules and inbox rules created by the attacker are removed
3. Verify all OAuth consent grants by the attacker are revoked
4. Remove any data staging or exfiltration mechanisms the attacker may have set up
5. Block all identified IOCs (domains, IPs, URLs, email addresses) permanently

### Step 14: Credential Remediation
**Actions:**
1. Force password reset for confirmed compromised accounts (already done in containment)
2. Force MFA re-enrollment with phishing-resistant method (FIDO2 if available)
3. For accounts with significant access (VPN, admin, financial): conduct detailed access review
4. If credentials were reused across systems: identify and reset on all systems
5. Review and rotate any API keys, tokens, or secrets accessible from compromised accounts

### Step 15: Validate Clean State
**Actions:**
1. Verify no attacker access remains by monitoring login activity for 48-72 hours
2. Confirm no residual phishing emails exist in any mailbox
3. Verify no unauthorized changes persist in email configurations
4. Confirm financial fraud was fully prevented or remediated
5. Verify no data was exfiltrated during the compromise window

---

## Phase 5: Recovery

### Step 16: Account Restoration
**Actions:**
1. Re-enable any disabled accounts with new credentials and MFA
2. Provide affected users with security debrief (what happened, what to watch for)
3. Help users verify their mailbox settings are correct (signatures, rules, delegates)
4. Implement enhanced mailbox audit logging for 90 days
5. Set up alerts for any suspicious login activity on previously compromised accounts

### Step 17: Business Process Recovery
**Actions:**
1. Resume normal email operations
2. If financial transactions were disrupted: verify all legitimate transactions are processing
3. If internal communications were impacted: restore normal communication flow
4. Notify helpdesk to close any related tickets after user confirmation

---

## Phase 6: Post-Incident Activity

### Step 18: Post-Incident Review
**Conduct within 5 business days:**
1. Document the full attack timeline
2. Analyze why the phishing emails bypassed email security controls
3. Assess the effectiveness of user reporting (time to first report)
4. Review the speed and completeness of containment actions
5. Identify any detection gaps (e.g., no MFA bypass alerting)
6. Assess whether financial controls prevented fraud effectively

### Step 19: Control Improvements
**Address identified gaps:**
1. Deploy phishing-resistant MFA (FIDO2/WebAuthn) if not already in place
2. Implement lookalike domain detection and blocking
3. Enhance email gateway rules based on observed bypass techniques
4. Implement conditional access policies for geographic restrictions
5. Strengthen financial authorization procedures for wire transfers
6. Deploy automated mailbox rule auditing
7. Update phishing awareness training to include observed attack techniques
8. Recognize employees who reported the phishing promptly

### Step 20: Documentation & Reporting
**Actions:**
1. Generate formal incident report with timeline and impact assessment
2. Document all IOCs for threat intelligence sharing (within ISAC if applicable)
3. Update phishing playbook based on lessons learned
4. Share anonymized case study with security awareness program
5. File regulatory notifications if PII was exposed

---

## Appendix A: Email Header Analysis Quick Reference

**Key headers to examine:**
```
Return-Path: <actual-sender@domain.com>     - Envelope sender
From: "Display Name" <shown@domain.com>      - Display sender (can be spoofed)
Received: from mail-server (IP)              - Trace delivery path
X-Originating-IP: [IP]                       - Original sender IP
Authentication-Results: spf=pass/fail;       - SPF/DKIM/DMARC results
                       dkim=pass/fail;
                       dmarc=pass/fail
Reply-To: <different@domain.com>             - May differ from From:
```

## Appendix B: Phishing IOC Collection Checklist

- [ ] Complete email headers (raw/original message)
- [ ] Sender email address and display name
- [ ] Reply-to address (if different from sender)
- [ ] Subject line
- [ ] All embedded URLs (defanged)
- [ ] Attachment file names and hashes (MD5, SHA-256)
- [ ] Phishing page screenshots
- [ ] Source code of phishing page (if possible)
- [ ] Hosting infrastructure IPs and domains
- [ ] SSL certificate details for phishing domains
- [ ] Registration details for phishing domains (WHOIS)
- [ ] Attacker login source IPs
- [ ] Timestamps of all attacker actions

## Appendix C: O365/M365 Containment Commands

```powershell
# Revoke all sessions for a user
Revoke-AzureADUserAllRefreshToken -ObjectId <user-object-id>

# Search and purge phishing emails
New-ComplianceSearch -Name "PhishPurge" -ExchangeLocation All `
  -ContentMatchQuery 'subject:"URGENT: Q4 Compensation" AND from:attacker@domain.com'
Start-ComplianceSearch -Identity "PhishPurge"
New-ComplianceSearchAction -SearchName "PhishPurge" -Purge -PurgeType SoftDelete

# Check mailbox rules for suspicious forwarding
Get-InboxRule -Mailbox user@company.com | Where-Object {$_.ForwardTo -or $_.RedirectTo}

# Check OAuth consent grants
Get-AzureADServicePrincipal | Get-AzureADServicePrincipalOAuth2PermissionGrant
```

---

*This playbook is a living document. Report any gaps or suggested improvements to the Security Operations team.*
