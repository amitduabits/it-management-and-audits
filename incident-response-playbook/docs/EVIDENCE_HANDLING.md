# Digital Forensics Evidence Handling Guide

## Overview

Proper evidence handling is critical for maintaining the integrity and admissibility of digital evidence during incident response. This guide outlines procedures for evidence collection, preservation, chain of custody, analysis, and storage following forensic best practices and industry standards.

---

## Foundational Principles

### 1. Preserve the Original
Never modify original evidence. Create forensic copies (bit-for-bit images) and perform all analysis on the copies.

### 2. Document Everything
Record every action taken on or near evidence, including who, what, when, where, and why. Contemporaneous notes are more credible than reconstructed timelines.

### 3. Maintain Chain of Custody
Every transfer of evidence between individuals must be documented. An unbroken chain of custody is required for legal proceedings.

### 4. Use Validated Tools
Forensic tools must be validated and their use documented. Tool versions, configurations, and command-line parameters should be recorded.

### 5. Act Proportionally
Collect evidence proportional to the incident severity. Not every incident requires a full disk image of every system.

---

## Order of Volatility (RFC 3227)

Digital evidence must be collected in order of volatility -- the most transient data first.

| Priority | Evidence Type | Volatility | Collection Window | Tools |
|----------|--------------|------------|-------------------|-------|
| 1 | CPU Registers & Cache | Nanoseconds | Specialized; rarely collected | Hardware debuggers |
| 2 | **System Memory (RAM)** | Seconds-Minutes | Before shutdown or reboot | WinPmem, LiME, Magnet RAM Capture, DumpIt |
| 3 | **Network State** | Seconds-Minutes | Before network changes | netstat, ss, arp, route, nmap |
| 4 | **Running Processes** | Minutes | Before termination | ps, tasklist, Process Explorer, Volatility |
| 5 | **Disk / File System** | Hours-Days | Before overwrite | dd, dc3dd, FTK Imager, EnCase |
| 6 | **Log Files** | Days-Weeks | Before rotation | Log collection scripts, SIEM export |
| 7 | Archived/Backup Data | Months-Years | Stable | Backup retrieval |
| 8 | Physical Evidence | Stable | Stable | Physical seizure |

**Critical:** Memory and network state are the highest priority during live response. Once a system is powered off or disconnected, this evidence is permanently lost.

---

## Evidence Collection Procedures

### Memory Acquisition

**When to collect:** Always collect memory for SEV-1 and SEV-2 incidents where the system is still running.

**Procedure:**
1. Connect a forensic USB drive (pre-loaded with acquisition tools) to the target system
2. Execute the memory acquisition tool:
   - **Windows:** `winpmem_mini_x64.exe output.raw`
   - **Linux:** Load LiME kernel module: `insmod lime.ko path=/mnt/usb/memory.lime format=lime`
   - **macOS:** Use MacQuisition or osxpmem
3. Record the start and end timestamps of acquisition
4. Calculate SHA-256 hash of the output file immediately
5. Document the system state at time of acquisition (uptime, logged-in users)

**Hash verification:**
```
sha256sum memory.raw > memory.raw.sha256
```

### Disk Imaging

**When to collect:** Required for all incidents involving malware, unauthorized access, or data theft where persistent artifacts are relevant.

**Procedure:**
1. If possible, image while system is running (live acquisition) to preserve active files
2. For powered-off systems: use a hardware write-blocker between the source drive and the forensic workstation
3. Create a bit-for-bit forensic image:
   - **Linux:** `dc3dd if=/dev/sda of=/evidence/disk.img hash=sha256 log=/evidence/dc3dd.log`
   - **Windows:** Use FTK Imager or EnCase to create E01 format image
4. Verify the image hash matches the source hash
5. Store the original; analyze only the forensic copy

**Write-blocker requirement:** Hardware write-blockers are mandatory when imaging powered-off media. Software write-blockers are acceptable for live acquisition when hardware blockers are not feasible.

### Network Evidence

**What to collect:**
- Active network connections: `netstat -anb` (Windows), `ss -tunap` (Linux)
- ARP table: `arp -a`
- Routing table: `route print` (Windows), `ip route` (Linux)
- DNS cache: `ipconfig /displaydns` (Windows), review systemd-resolved cache (Linux)
- Packet captures: tcpdump, Wireshark, or network tap
- NetFlow/sFlow data from network devices

**Packet capture procedure:**
```bash
# Capture all traffic on interface eth0 to a file
tcpdump -i eth0 -w /evidence/capture_$(date +%Y%m%d_%H%M%S).pcap

# Capture traffic to/from a specific host
tcpdump -i eth0 host 185.220.101.34 -w /evidence/c2_traffic.pcap
```

### Log Collection

**Priority logs to collect:**
- Operating system event logs (Windows Event Logs, syslog)
- Authentication logs (Active Directory, LDAP, SSO/IdP)
- Web server access and error logs
- Database audit logs and query logs
- Firewall and proxy logs
- DNS query logs
- Email gateway logs
- EDR/AV detection logs
- SIEM alerts and raw events
- Cloud service audit logs (AWS CloudTrail, Azure Monitor, GCP Cloud Audit)

**Log preservation:**
```bash
# Export Windows Security Event Log
wevtutil epl Security /evidence/Security.evtx

# Compress and hash Linux logs
tar czf /evidence/var_log_$(date +%Y%m%d).tar.gz /var/log/
sha256sum /evidence/var_log_*.tar.gz > /evidence/log_hashes.sha256
```

---

## Chain of Custody

### Requirements

Every evidence item must have an unbroken chain of custody from collection through final disposition. A chain of custody record must document:

1. **Who** collected or handled the evidence
2. **What** was collected (description, identification number)
3. **When** each custody event occurred (date, time, timezone)
4. **Where** the evidence was stored or transferred
5. **Why** the transfer occurred (reason for each custody change)

### Chain of Custody Form

```
EVIDENCE CHAIN OF CUSTODY

Evidence ID: _______________
Description: _______________
Source System: _______________

| # | Date/Time | Action | From | To | Reason | Signature |
|---|-----------|--------|------|-----|--------|-----------|
| 1 | _________ | Collected | N/A | _______ | Initial collection | _________ |
| 2 | _________ | Transferred | _______ | _______ | ____________ | _________ |
| 3 | _________ | Accessed | _______ | _______ | Analysis | _________ |
| 4 | _________ | Returned | _______ | _______ | Analysis complete | _________ |
```

### Using the Evidence Tracker

The evidence tracker module automates chain of custody documentation:

```python
from src.evidence_tracker import EvidenceTracker

tracker = EvidenceTracker()

# Register new evidence
evidence = tracker.register_evidence(
    evidence_type="memory_dump",
    description="RAM capture from db-prod-07",
    collected_by="J. Martinez",
    source_system="db-prod-07",
    file_path="/evidence/INC-20250115/db-prod-07_memory.raw",
    file_hash_sha256="a1b2c3d4e5f6...",
    file_size_bytes=17179869184,
    is_volatile=True,
    preservation_method="Live acquisition using WinPmem",
    tool_used="WinPmem 4.0",
)

# Record custody transfer
tracker.transfer_custody(
    evidence_id=evidence.evidence_id,
    from_person="J. Martinez",
    to_person="K. Thompson",
    reason="Transfer to forensic analysis team",
)

# Verify integrity
result = tracker.verify_integrity(
    evidence_id=evidence.evidence_id,
    current_hash="a1b2c3d4e5f6...",
    hash_type="sha256",
)
```

---

## Evidence Storage

### Physical Requirements
- Locked, access-controlled evidence storage room or safe
- Environmental controls (temperature 60-75F, humidity 30-50%)
- Fire suppression (FM-200 or equivalent; NOT water sprinklers)
- Video surveillance of the evidence storage area
- Access logging (badge reader or sign-in log)

### Digital Requirements
- Encrypted storage volumes (AES-256 or equivalent)
- Separate from production systems and networks
- Access limited to authorized forensic personnel
- Automated integrity checking (periodic hash verification)
- Backup of evidence storage (separate location)

### Retention Periods

| Category | Minimum Retention | Authority |
|----------|------------------|-----------|
| Criminal investigation | Duration of proceedings + 5 years | Legal counsel |
| Civil litigation | Duration of proceedings + statute of limitations | Legal counsel |
| Regulatory investigation | Per regulatory requirement (varies) | Compliance team |
| Legal hold | Until released by Legal | Legal counsel |
| Standard incident | 1 year from case closure | IR policy |
| Low-severity incident | 90 days from case closure | IR policy |

---

## Evidence Analysis Guidelines

### Working Copy Principle
1. Never analyze original evidence
2. Create a verified forensic copy (matching hash)
3. Perform all analysis on the working copy
4. Document all tools and procedures used during analysis
5. Record all findings with references to specific evidence items

### Analysis Documentation
For each analysis action, record:
- Date and time of analysis
- Analyst performing the analysis
- Tool used (name, version, configuration)
- Procedure followed
- Findings and their evidence references
- Screenshots of significant findings

### Memory Analysis Workflow
```
1. Load memory dump in Volatility
2. Identify the OS profile
3. Extract process list (pslist, pstree, psscan)
4. Identify network connections (netscan, connections)
5. Extract command history
6. Search for malicious indicators (malfind, dlllist)
7. Extract relevant strings and artifacts
8. Document all findings
```

### Disk Analysis Workflow
```
1. Mount forensic image read-only
2. Generate file system timeline (fls, mactime)
3. Search for known IOCs (file names, hashes)
4. Examine recently modified files
5. Check persistence mechanisms (autorun, cron, services)
6. Recover deleted files if applicable
7. Examine browser artifacts, email clients
8. Document all findings
```

---

## Legal Considerations

### Authorization
- Ensure legal authorization before collecting evidence from systems you do not own
- Corporate systems: Acceptable Use Policy typically authorizes monitoring and forensics
- Employee devices (BYOD): May require additional authorization; consult Legal
- Third-party systems: Requires explicit authorization from the system owner
- Law enforcement: May require warrants or subpoenas; coordinate through Legal

### Admissibility
For evidence to be admissible in legal proceedings:
1. Collection must be legally authorized
2. Chain of custody must be unbroken
3. Evidence integrity must be verifiable (hash values)
4. Collection procedures must be documented and defensible
5. Tools must be validated and accepted in the relevant jurisdiction

### Privacy
- Minimize collection of personal data not relevant to the investigation
- Follow organizational privacy policies and applicable regulations
- Document justification for any collection of personal data
- Consult with Privacy Officer for incidents involving employee personal data

---

## References

- RFC 3227: Guidelines for Evidence Collection and Archiving
- NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response
- ISO/IEC 27037: Guidelines for Identification, Collection, Acquisition, and Preservation of Digital Evidence
- SWGDE Best Practices for Computer Forensics
- ACPO Good Practice Guide for Digital Evidence
