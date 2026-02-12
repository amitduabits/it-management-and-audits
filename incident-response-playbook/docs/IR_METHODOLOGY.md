# Incident Response Methodology

## NIST SP 800-61 Rev. 2 Framework

This project implements the incident response lifecycle defined in NIST Special Publication 800-61 Revision 2, "Computer Security Incident Handling Guide." This framework is the industry-standard methodology for organizing and executing incident response operations.

---

## The Four Phases of Incident Response

### Phase 1: Preparation

Preparation is the foundation of effective incident response. Without proper preparation, the remaining phases cannot be executed efficiently under the pressure of a real incident.

**Key Activities:**
- **Policy and procedure development:** Create and maintain IR policies, playbooks, and standard operating procedures for each incident type
- **Team organization:** Define IR team roles, responsibilities, and escalation matrices. Establish on-call rotations and communication channels
- **Tool deployment:** Ensure detection, analysis, containment, and forensic tools are deployed, configured, and tested
- **Training and exercises:** Conduct regular tabletop exercises, simulation training, and purple team operations
- **Communication planning:** Establish internal and external communication plans, including media, regulatory, and law enforcement contacts
- **Legal readiness:** Pre-negotiate forensic vendor retainers, review regulatory notification requirements, and prepare template communications

**Metrics:**
- Mean Time to Acknowledge (MTTA) from exercises
- Playbook coverage (% of incident types with documented procedures)
- Exercise frequency and participation rates
- Tool availability and operational status

---

### Phase 2: Detection and Analysis

Detection and analysis is often the most challenging phase. Security teams must distinguish genuine incidents from false positives and rapidly assess the scope and severity of confirmed incidents.

**Detection Sources:**
- **Security Information and Event Management (SIEM):** Correlation rules, anomaly detection, threat intelligence matching
- **Intrusion Detection/Prevention Systems (IDS/IPS):** Signature-based and behavioral detection at network boundaries
- **Endpoint Detection and Response (EDR):** Process monitoring, behavioral analysis, fileless attack detection on endpoints
- **Data Loss Prevention (DLP):** Policy-based detection of unauthorized data movement
- **User and Entity Behavior Analytics (UEBA):** Baseline deviation detection for insider threats and compromised accounts
- **External sources:** Threat intelligence feeds, vulnerability disclosures, law enforcement notifications, third-party reports
- **User reports:** Employees reporting suspicious activity, phishing emails, or system anomalies

**Analysis Process:**
1. **Alert triage:** Validate the alert as a true positive or false positive
2. **Event correlation:** Connect related alerts across multiple data sources
3. **Scope determination:** Identify all affected systems, accounts, and data
4. **Impact assessment:** Evaluate business, regulatory, and operational impact
5. **Severity classification:** Assign severity per the organizational severity matrix
6. **Documentation:** Record all findings in the IR case management system

**Key Principle:** *Analysis is iterative.* Initial findings drive further investigation, which reveals additional scope, which requires additional analysis. Responders must continuously reassess as new information emerges.

**Metrics:**
- Mean Time to Detect (MTTD)
- False positive rate
- Alert-to-incident conversion rate
- Time to severity classification

---

### Phase 3: Containment, Eradication, and Recovery

This phase encompasses three distinct but interrelated sub-phases. The order and timing of these activities depends on the incident type and severity.

#### 3a: Containment

Containment aims to limit the damage and prevent further harm. There are two containment strategies:

**Short-term containment:** Immediate actions to stop active attacks while preserving evidence.
- Network isolation of affected systems
- Blocking attacker IP addresses and domains at the perimeter
- Disabling compromised user accounts
- Implementing emergency firewall rules

**Long-term containment:** Sustainable measures that allow controlled operation while the attacker's access is fully mapped and eliminated.
- Moving affected systems to isolated network segments
- Applying temporary patches or workarounds
- Implementing enhanced monitoring on contained systems
- Maintaining forensic access for ongoing investigation

**Decision Factors for Containment Strategy:**
- Is the attack still active? (Urgency)
- What evidence will be lost by containment actions? (Forensic preservation)
- What business impact will containment cause? (Operational continuity)
- Is the attacker aware they have been detected? (Tactical advantage)

#### 3b: Eradication

Eradication removes all artifacts of the attacker's presence from the environment.

**Activities:**
- Remove all malware, backdoors, and persistence mechanisms
- Patch exploited vulnerabilities
- Rotate compromised credentials and certificates
- Rebuild severely compromised systems from known-good baselines
- Verify eradication through integrity checks and threat hunting

**Key Principle:** *Eradication must be complete.* Partial eradication allows the attacker to regain access through remaining footholds. When in doubt, rebuild from clean images.

#### 3c: Recovery

Recovery restores affected systems to normal operation with confidence that the threat has been eliminated.

**Activities:**
- Restore systems from verified clean backups
- Apply all security patches before returning systems to production
- Validate system integrity and functionality
- Implement enhanced monitoring for the recovery observation period
- Gradually return systems to production starting with the most critical

**Key Principle:** *Recovery is not just technical.* It includes restoring business processes, customer confidence, and organizational trust.

**Metrics:**
- Mean Time to Contain (MTTC)
- Mean Time to Recover (MTTR)
- Systems restored within RTO
- Data loss within RPO

---

### Phase 4: Post-Incident Activity

The post-incident phase is critical for organizational learning and is frequently the most underinvested phase.

**Post-Incident Review (Lessons Learned):**
- Conduct within 5 business days of incident closure
- Include all teams involved in the response
- Use a blameless review format (focus on process, not individuals)
- Document: what happened, what was done, what worked, what needs improvement
- Assign specific, measurable improvement actions with owners and deadlines

**Incident Report:**
- Produce a formal incident report for internal stakeholders
- Include: executive summary, timeline, technical details, impact assessment, recommendations
- Classify appropriately and distribute on a need-to-know basis
- Archive per organizational retention policy

**Evidence Retention:**
- Maintain evidence per legal hold requirements
- Apply organizational retention policies
- Ensure chain of custody documentation is complete
- Store in secure, access-controlled evidence repository

**Improvement Implementation:**
- Track all post-incident recommendations to completion
- Update playbooks and procedures based on lessons learned
- Modify detection rules to catch similar attacks earlier
- Conduct follow-up exercises to validate improvements

---

## Incident Response Team Roles

| Role | Responsibility |
|------|---------------|
| **Incident Commander (IC)** | Overall authority and coordination of the response. Makes critical decisions. Manages communication with leadership. |
| **IR Lead Analyst** | Technical lead for investigation and analysis. Directs forensic activities and coordinates containment/eradication. |
| **SOC Analyst** | Front-line detection, triage, and monitoring. First responder for new alerts. |
| **Forensic Analyst** | Evidence collection, preservation, and analysis. Maintains chain of custody. |
| **Threat Hunter** | Proactive search for attacker activity beyond known indicators. Validates eradication completeness. |
| **Communications Lead** | Internal and external communications. Coordinates with PR, legal, and customer support. |
| **Scribe/Documenter** | Real-time documentation of all actions, decisions, and findings. Maintains the incident timeline. |

---

## Integration with Other Frameworks

This methodology is compatible with and complementary to:
- **MITRE ATT&CK:** For mapping attacker tactics, techniques, and procedures (TTPs) during analysis
- **SANS Incident Response Process:** Six-phase model that maps closely to NIST 800-61
- **ISO 27035:** International standard for information security incident management
- **ITIL Incident Management:** For coordination with IT service management processes

---

## References

- NIST SP 800-61 Rev. 2: Computer Security Incident Handling Guide
- NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response
- NIST SP 800-83: Guide to Malware Incident Prevention and Handling
- RFC 3227: Guidelines for Evidence Collection and Archiving
- MITRE ATT&CK Framework: https://attack.mitre.org
