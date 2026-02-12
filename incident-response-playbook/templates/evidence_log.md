# Digital Evidence Collection Log

**Classification:** CONFIDENTIAL
**Generated:** {{ generated_at }}
**Total Evidence Items:** {{ total_items }}
**Case Reference:** _________________
**Forensic Examiner:** _________________

---

## Chain of Custody Acknowledgment

By handling evidence documented in this log, all personnel agree to:
1. Maintain evidence integrity at all times
2. Document all access and transfers in the chain of custody
3. Use write-blocking hardware when accessing original media
4. Store evidence in a secure, access-controlled environment
5. Never modify original evidence; work only on forensic copies

---

## Evidence Collection Priority (Order of Volatility)

Evidence should be collected in the following order per RFC 3227:

| Priority | Evidence Type | Volatility | Status |
|----------|--------------|------------|--------|
| 1 | CPU Registers & Cache | Nanoseconds | [ ] Collected |
| 2 | System Memory (RAM) | Seconds-Minutes | [ ] Collected |
| 3 | Network State & Connections | Seconds-Minutes | [ ] Collected |
| 4 | Running Processes | Minutes | [ ] Collected |
| 5 | Disk / File System | Hours-Days | [ ] Collected |
| 6 | Log Files | Days-Weeks | [ ] Collected |
| 7 | Archived Data / Backups | Months-Years | [ ] Collected |
| 8 | Physical Evidence | Stable | [ ] Collected |

---

## Evidence Items

{% if evidence_items %}
{% for item in evidence_items %}
### Item {{ loop.index }}: {{ item.evidence_id }}

| Field | Value |
|-------|-------|
| **Evidence ID** | {{ item.evidence_id }} |
| **Type** | {{ item.evidence_type }} |
| **Description** | {{ item.description }} |
| **Collected By** | {{ item.collected_by }} |
| **Collection Date/Time** | {{ item.collected_at }} |
| **Source System** | {{ item.source_system }} |
| **Storage Path** | {{ item.file_path or 'N/A' }} |
| **File Size** | {{ item.file_size_bytes or 'N/A' }} bytes |
| **MD5 Hash** | `{{ item.file_hash_md5 or 'N/A' }}` |
| **SHA-256 Hash** | `{{ item.file_hash_sha256 or 'N/A' }}` |
| **Volatile Evidence** | {{ 'Yes' if item.is_volatile else 'No' }} |
| **Preservation Method** | {{ item.preservation_method or 'N/A' }} |
| **Tool Used** | {{ item.tool_used or 'N/A' }} |
| **Integrity Verified** | {{ 'Yes' if item.integrity_verified else 'No' }} |
| **Tags** | {{ ', '.join(item.tags) if item.tags else 'None' }} |

**Analyst Notes:**
{{ item.notes or '_No notes recorded._' }}

**Chain of Custody:**

| Timestamp | Action | Person(s) | Details |
|-----------|--------|-----------|---------|
{% for entry in item.chain_of_custody %}
| {{ entry.timestamp if entry.timestamp is defined else 'N/A' }} | {{ entry.action if entry.action is defined else 'N/A' }} | {{ entry.person if entry.person is defined else (entry.get('from', 'N/A') + ' -> ' + entry.get('to', 'N/A')) }} | {{ entry.details if entry.details is defined else entry.get('reason', 'N/A') }} |
{% endfor %}

---

{% endfor %}
{% else %}

_No evidence items have been registered for this case._

---

{% endif %}

## Evidence Handling Reminders

### Before Collection
- [ ] Photograph the physical setup before touching anything
- [ ] Document date, time, location, and personnel present
- [ ] Use write-blocking hardware for all disk access
- [ ] Use validated forensic tools for memory acquisition
- [ ] Prepare evidence bags/containers with tamper-evident seals

### During Collection
- [ ] Collect volatile evidence FIRST (memory, network connections, processes)
- [ ] Calculate and record hash values immediately after acquisition
- [ ] Use forensic imaging tools (dd, FTK Imager, EnCase) for disk images
- [ ] Verify image integrity by comparing source and image hashes
- [ ] Document every action taken on or near the evidence

### After Collection
- [ ] Store evidence in a locked, access-controlled evidence room
- [ ] Maintain environmental controls (temperature, humidity)
- [ ] Log all access to evidence in the chain of custody
- [ ] Create working copies for analysis; never analyze originals
- [ ] Retain evidence per legal hold and retention policies

---

## Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Lead Examiner | ______________ | ______________ | ____/____/____ |
| Evidence Custodian | ______________ | ______________ | ____/____/____ |
| Incident Commander | ______________ | ______________ | ____/____/____ |
| Legal Representative | ______________ | ______________ | ____/____/____ |

---

*This document is part of the incident case file. Maintain per organizational retention policy and any applicable legal hold requirements.*
