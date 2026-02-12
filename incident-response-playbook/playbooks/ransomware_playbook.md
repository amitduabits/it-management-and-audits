# Ransomware Incident Response Playbook

**Classification:** CONFIDENTIAL
**Version:** 3.0
**Last Updated:** 2025-11-15
**Owner:** Security Operations Center
**Review Cycle:** Quarterly

---

## 1. Purpose

This playbook provides structured procedures for responding to ransomware attacks, including file-encrypting ransomware, wiper malware disguised as ransomware, and ransomware-as-a-service (RaaS) operations. Speed is critical in ransomware incidents as encryption spreads rapidly once deployed.

## 2. Scope

This playbook covers:
- File-encrypting ransomware on endpoints and servers
- Network-propagating ransomware (worm-like behavior)
- Double extortion (encryption + data theft)
- Ransomware delivered via phishing, RDP, or supply chain
- Ransom negotiation considerations (with legal guidance)

## 3. Critical First Response

**RANSOMWARE IS THE ONE SCENARIO WHERE IMMEDIATE CONTAINMENT MAY PRECEDE FULL VALIDATION.**

If encryption is actively spreading, network isolation takes priority over all other actions.

---

## Phase 1: Preparation

### Step 1: Backup Resilience
- Implement the 3-2-1 backup strategy: 3 copies, 2 different media, 1 offsite/air-gapped
- Test backup restoration quarterly with documented RTO/RPO validation
- Ensure backups are immutable or air-gapped to prevent ransomware encryption of backups
- Maintain offline backup of Active Directory and critical configurations

### Step 2: Network Segmentation
- Segment networks to limit lateral movement potential
- Implement micro-segmentation for critical server tiers
- Restrict SMB traffic (TCP 445) between workstation VLANs
- Deploy jump servers for administrative access to sensitive segments

### Step 3: Endpoint Protection
- Deploy EDR on all endpoints and servers (no exceptions for servers)
- Enable anti-ransomware behavioral detection (canary files, entropy monitoring)
- Restrict macro execution in Office documents via Group Policy
- Implement application whitelisting on critical servers

### Step 4: Access Controls
- Enforce MFA on all remote access (VPN, RDP, cloud admin portals)
- Implement Privileged Access Management (PAM) for admin accounts
- Apply least-privilege principles to service accounts
- Disable or restrict PsExec, PowerShell remoting, and WMI where not required

---

## Phase 2: Detection & Analysis

### Step 5: Identify Ransomware Activity
**Time-critical: Proceed to Step 7 (containment) if active encryption is confirmed.**

**Indicators of ransomware:**
- EDR alerts for rapid file modification or encryption patterns
- Files renamed with unusual extensions (.lockstorm, .encrypted, .crypto, etc.)
- Ransom notes appearing on desktops or in directories (README.txt, DECRYPT.html)
- Volume Shadow Copy Service (VSS) deletions (vssadmin delete shadows)
- Sudden high CPU utilization across multiple systems
- Helpdesk reports of users unable to open files
- Anomalous SMB traffic volume between internal hosts

### Step 6: Classify the Ransomware
**Actions:**
1. Identify the ransomware variant from ransom note content, file extensions, or binary analysis
2. Check ID Ransomware (id-ransomware.malwarehunterteam.com) for variant identification
3. Check No More Ransom (nomoreransom.org) for available free decryptors
4. Determine if this is single extortion (encrypt only) or double extortion (encrypt + steal)
5. Identify the ransomware's propagation mechanism (SMB, GPO, PsExec, scheduled tasks)
6. Assess whether this is automated deployment or human-operated ransomware

---

## Phase 3: Containment (IMMEDIATE PRIORITY)

### Step 7: Network Isolation
**Objective:** Stop ransomware propagation immediately.

**Actions (execute within minutes, not hours):**
1. Isolate affected network segments at the switch/router level
2. Disable SMB (TCP 445, 139) between all workstation VLANs via ACL
3. Block all known C2 IPs and domains at the perimeter firewall
4. Disable any Group Policy Objects that may be deploying the ransomware
5. If domain admin credentials are compromised: isolate domain controllers
6. Consider temporarily disabling network shares on unaffected file servers
7. DO NOT power off affected systems (preserve memory evidence)

### Step 8: Identify Patient Zero
**Objective:** Find the initial infection point to understand the attack timeline.

**Actions:**
1. Review EDR telemetry for the earliest ransomware execution timestamp
2. Trace the execution chain: parent process -> child process -> ransomware binary
3. Identify the initial delivery mechanism (email attachment, drive-by download, RDP)
4. Check email gateway logs for suspicious attachments around the initial timestamp
5. Review RDP/VPN authentication logs for unauthorized access
6. Identify the user account and system that first executed the malware

### Step 9: Assess Encryption Scope
**Objective:** Determine what has been encrypted and what remains unaffected.

**Actions:**
1. Inventory all affected systems (workstations, servers, network shares)
2. Determine which file types are encrypted (some variants skip system files)
3. Identify any data that was exfiltrated before encryption (check for double extortion)
4. Map the ransomware's network propagation path
5. Identify systems that are at risk but not yet encrypted

### Step 10: Backup Assessment (CRITICAL)
**Objective:** Determine recovery capability from backups.

**Actions:**
1. Verify backup system integrity - confirm backups are NOT encrypted
2. Identify the most recent clean backup for each affected system
3. Calculate the Recovery Point Objective (RPO): how much data loss?
4. Calculate the Recovery Time Objective (RTO): how long to restore?
5. Test backup restoration on an isolated system before committing
6. Assess the gap between backup and encryption time for data loss impact

### Step 11: Preserve Evidence
**Actions:**
1. Capture memory dumps from patient zero and representative infected systems
2. Collect the ransomware binary, ransom note, and associated artifacts
3. Capture network traffic logs showing C2 communication and lateral movement
4. Preserve email artifacts if phishing was the delivery vector
5. Image affected systems using forensic imaging tools
6. Document chain of custody for all evidence

---

## Phase 4: Eradication

### Step 12: Remove Ransomware Artifacts
**Actions:**
1. For workstations: REIMAGE from known-good gold images (do not attempt to clean)
2. For servers: Rebuild from clean OS installation or verified clean backups
3. Remove all identified persistence mechanisms:
   - Registry Run/RunOnce keys
   - Scheduled tasks
   - Services
   - Startup folder shortcuts
   - WMI event subscriptions
   - GPO modifications
4. Remove the ransomware delivery mechanism (malicious GPO, PsExec, etc.)

### Step 13: Credential Remediation
**Actions:**
1. Reset ALL domain admin account passwords (use out-of-band methods)
2. Reset ALL service account passwords
3. Reset the KRBTGT account password TWICE (to invalidate Golden Tickets)
4. Reset all local administrator passwords across the environment
5. Revoke all Kerberos tickets and force re-authentication
6. If NTDS.dit was exfiltrated: plan for enterprise-wide password reset

### Step 14: Patch & Harden
**Actions:**
1. Patch the initial access vulnerability (e.g., VPN exploit, web app flaw)
2. Enable MFA on all remote access methods
3. Restrict administrative tool usage (PsExec, PowerShell, WMI)
4. Implement SMB signing and restrict SMB traffic
5. Disable unnecessary services on servers
6. Apply updated EDR detection rules for the ransomware variant

### Step 15: Verify Eradication
**Actions:**
1. Conduct a full environment threat hunt for related IOCs and TTPs
2. Scan all systems with updated EDR/AV signatures
3. Monitor for C2 callback attempts from any system
4. Verify no dormant malware exists on non-encrypted systems
5. Confirm all persistence mechanisms are removed

---

## Phase 5: Recovery

### Step 16: Prioritized Restoration
**Priority order for restoration:**
1. **Critical infrastructure:** Domain controllers, DNS, DHCP, authentication
2. **Tier-1 systems:** Revenue-generating, customer-facing applications
3. **Tier-2 systems:** Business operations support systems
4. **Tier-3 systems:** File servers and shared drives
5. **Tier-4 systems:** Individual workstations and non-critical systems

**Actions per system:**
1. Restore from verified clean backup
2. Apply all security patches before reconnecting to network
3. Install/update EDR agent
4. Verify system integrity
5. Reconnect to network under enhanced monitoring

### Step 17: Data Recovery
**Actions:**
1. Restore data from the most recent clean backup for each system
2. Quantify data loss between last backup and encryption time
3. Work with business units to reconstruct lost data where possible
4. If no backup exists and decryption is critical: consult Legal about payment (see Step 19)
5. Document all data that could not be recovered

### Step 18: Monitoring & Validation
**Actions:**
1. Deploy enhanced monitoring rules for 30-60 days post-recovery
2. Monitor for any ransomware re-execution or new infections
3. Watch for data exfiltration if double extortion was suspected
4. Conduct daily validation checks for the first week
5. Perform weekly threat hunts for the first month

---

## Phase 6: Ransom Payment Decision Framework

### Step 19: Payment Considerations (Last Resort Only)
**This section applies ONLY when:**
- All recovery options have been exhausted
- Backups are unavailable or destroyed
- The data loss would cause catastrophic business impact
- Legal counsel has been consulted

**Decision framework:**
1. Consult legal counsel on payment legality (OFAC sanctions screening)
2. Notify law enforcement (FBI IC3, CISA) - they may have decryptors
3. Engage cyber insurance carrier for coverage and guidance
4. Research the ransomware operator's reliability (do they provide working decryptors?)
5. If proceeding: use a professional ransomware negotiator, never communicate directly
6. Verify the decryptor works on a sample file before full payment
7. Document everything for insurance and legal purposes

**Important:** Payment does NOT guarantee data recovery and funds criminal operations.

---

## Phase 7: Post-Incident Activity

### Step 20: Lessons Learned Review
**Conduct within 5 business days of recovery:**
1. Full incident timeline reconstruction
2. Root cause analysis: how did the attacker get in?
3. Detection gap analysis: why was it not caught sooner?
4. Containment effectiveness review
5. Backup and recovery process evaluation
6. Communication effectiveness assessment
7. Document all improvement recommendations with owners and deadlines

### Step 21: Report & Notification
**Actions:**
1. Generate formal incident report
2. Assess regulatory notification requirements (data theft component)
3. File law enforcement reports (FBI, CISA)
4. Notify cyber insurance carrier with full incident documentation
5. Prepare customer communication if customer data was impacted
6. Brief executive leadership and board (if applicable)

### Step 22: Strategic Improvements
**Address systemic weaknesses identified during the incident:**
1. Implement immutable/air-gapped backup architecture
2. Deploy network segmentation and micro-segmentation
3. Enable MFA on all privileged access
4. Implement EDR on all endpoints and servers
5. Restrict lateral movement tools (PsExec, PSRemoting, WMI)
6. Establish a regular phishing simulation and training program
7. Conduct purple team exercises simulating ransomware TTPs

---

## Appendix A: Ransomware-Specific IOC Collection Checklist

- [ ] Ransomware binary/executable
- [ ] Ransom note (all variants found)
- [ ] File extension used for encrypted files
- [ ] Attacker communication addresses (email, Tor site, chat)
- [ ] Bitcoin/cryptocurrency wallet addresses from ransom note
- [ ] C2 server IP addresses and domains
- [ ] Delivery mechanism artifacts (phishing email, exploit kit)
- [ ] Persistence mechanisms (registry keys, scheduled tasks)
- [ ] Lateral movement tools used (PsExec, Cobalt Strike, etc.)
- [ ] Exfiltrated data indicators (if double extortion)

## Appendix B: Offline Recovery Checklist

- [ ] Confirm backups are available and not encrypted
- [ ] Test backup restoration on isolated system
- [ ] Prepare clean OS installation media
- [ ] Prepare network re-imaging infrastructure (PXE boot)
- [ ] Prepare credential rotation plan (step-by-step order)
- [ ] Prepare enhanced monitoring rules for post-recovery
- [ ] Coordinate with business units on restoration priority

---

*This playbook is a living document. Report any gaps or suggested improvements to the Security Operations team.*
