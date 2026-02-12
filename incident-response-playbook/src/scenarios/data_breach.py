"""
Data Breach Scenario
====================

Simulates a data exfiltration incident where an external threat actor
gains unauthorized access to sensitive data repositories and exfiltrates
PII, financial records, or intellectual property.

Attack narrative:
    An attacker exploits a vulnerable public-facing web application to gain
    initial access, escalates privileges via a misconfigured service account,
    moves laterally to the database tier, and exfiltrates customer records
    through an encrypted channel to an external staging server.
"""

from typing import Dict, List, Any


class DataBreachScenario:
    """Data breach incident response scenario with decision tree."""

    def __init__(self):
        self.name = "data_breach"
        self.title = "Customer Database Exfiltration"
        self.description = (
            "The SIEM has flagged anomalous outbound data transfers from a production "
            "database server (db-prod-07). Network sensors detected 4.2 GB of encrypted "
            "traffic to an unrecognized external IP (185.220.101.34) over the past 6 hours. "
            "The DLP system also triggered on structured data patterns matching PII fields. "
            "Initial triage suggests a compromised service account (svc_webapp_prod) was used "
            "to query the customer database outside of normal application behavior."
        )
        self.default_severity = "critical"
        self.estimated_duration_minutes = 45
        self.category = "data_breach"
        self.affected_systems = [
            "db-prod-07 (PostgreSQL 14 - Customer DB)",
            "app-web-03 (Tomcat 9 - Web Application)",
            "proxy-dmz-01 (Squid - Outbound Proxy)",
        ]
        self.initial_iocs = [
            {"type": "ip", "value": "185.220.101.34", "context": "External C2/exfil destination"},
            {"type": "ip", "value": "185.220.101.35", "context": "Secondary exfil destination"},
            {"type": "account", "value": "svc_webapp_prod", "context": "Compromised service account"},
            {"type": "hash_sha256", "value": "a1b2c3d4e5f6789012345678abcdef01234567890abcdef1234567890abcdef1", "context": "Webshell uploaded to app-web-03"},
            {"type": "domain", "value": "update-cdn-services.net", "context": "Attacker infrastructure"},
            {"type": "user_agent", "value": "Mozilla/5.0 (compatible; DataSync/2.1)", "context": "Custom exfil tool UA string"},
        ]
        self.attack_vector = "SQL injection in customer search API -> webshell upload -> lateral movement -> data exfiltration"

    def get_phases(self) -> List[Dict[str, Any]]:
        """Return all scenario phases with decision points."""
        return [
            self._phase_detection(),
            self._phase_triage(),
            self._phase_containment(),
            self._phase_eradication(),
            self._phase_recovery(),
            self._phase_post_incident(),
        ]

    def _phase_detection(self) -> Dict[str, Any]:
        return {
            "phase": "detection",
            "phase_number": 1,
            "title": "Initial Detection & Alert Validation",
            "narrative": (
                "At 02:17 UTC, the SIEM correlation engine generated a high-severity alert "
                "(SIEM-47821) for anomalous outbound data volume from db-prod-07. The alert "
                "was triggered by Rule CR-2041 (Large Outbound Transfer from DB Tier). "
                "Simultaneously, the DLP gateway flagged structured data patterns in encrypted "
                "traffic. The SOC Tier-1 analyst has escalated the alert to your team.\n\n"
                "Current indicators:\n"
                "  - 4.2 GB transferred to 185.220.101.34 over 6 hours\n"
                "  - svc_webapp_prod executed 847 SELECT queries in the past 3 hours\n"
                "  - Normal baseline for this account: ~120 queries/hour during business hours\n"
                "  - Traffic is TLS-encrypted to a non-standard port (TCP/8443)\n"
                "  - The destination IP is hosted in a data center known for bulletproof hosting"
            ),
            "decisions": [
                {
                    "id": "det_1",
                    "prompt": "What is your first action upon receiving this alert?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Validate the alert by reviewing SIEM logs, DLP alerts, and NetFlow data for the flagged traffic",
                            "score": 10,
                            "feedback": "Correct. Alert validation is the critical first step. You confirm the alert is not a false positive by correlating multiple data sources.",
                            "next_action": "Cross-reference the SIEM alert with DLP logs and NetFlow records confirms consistent anomalous outbound transfers.",
                        },
                        {
                            "id": "b",
                            "text": "Immediately block the external IP at the perimeter firewall",
                            "score": 4,
                            "feedback": "Premature. While blocking the IP may stop active exfiltration, acting without validation risks disrupting legitimate traffic and tips off the attacker before you understand the full scope. Always validate first.",
                            "next_action": "The IP is blocked but you have not confirmed the alert validity or identified the full scope of compromise.",
                        },
                        {
                            "id": "c",
                            "text": "Disable the svc_webapp_prod service account immediately",
                            "score": 3,
                            "feedback": "Risky without validation. Disabling the service account could cause a production outage if this is a false positive, and alerts the attacker. Validate first, then contain.",
                            "next_action": "The service account is disabled. The web application is now experiencing errors.",
                        },
                        {
                            "id": "d",
                            "text": "Send the alert to the next shift and monitor",
                            "score": 0,
                            "feedback": "Unacceptable. High-severity alerts indicating active data exfiltration require immediate response. Delaying action allows continued data loss.",
                            "next_action": "Another 1.8 GB of data is exfiltrated during the shift handover delay.",
                        },
                    ],
                },
                {
                    "id": "det_2",
                    "prompt": "After validating the alert is genuine, who do you notify first?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Activate the IR team and notify the Incident Commander per the escalation matrix",
                            "score": 10,
                            "feedback": "Correct. The escalation matrix defines notification procedures. Activating the full IR team ensures proper coordination from the start.",
                            "next_action": "IR team is assembled. Incident Commander designates roles and opens a dedicated communication channel.",
                        },
                        {
                            "id": "b",
                            "text": "Notify the CISO and legal team before assembling the IR team",
                            "score": 5,
                            "feedback": "Partially correct. Executive notification is important but should happen in parallel with IR team activation, not before. The IR team needs to begin immediately.",
                            "next_action": "CISO is aware but the IR team mobilization is delayed by 25 minutes.",
                        },
                        {
                            "id": "c",
                            "text": "Notify the database administrator to check for issues",
                            "score": 2,
                            "feedback": "Insufficient. The DBA may be helpful later, but this is an active security incident requiring the IR team. Also, involving non-IR personnel risks evidence contamination.",
                            "next_action": "DBA logs into db-prod-07 and inadvertently overwrites volatile evidence in the process table.",
                        },
                        {
                            "id": "d",
                            "text": "Post in the general IT Slack channel to ask if anyone knows about the traffic",
                            "score": 0,
                            "feedback": "Dangerous. Broadcasting incident details in a general channel violates need-to-know principles and could alert an insider threat. Use established IR communication channels only.",
                            "next_action": "Multiple non-essential personnel are now aware of the incident, complicating response.",
                        },
                    ],
                },
            ],
        }

    def _phase_triage(self) -> Dict[str, Any]:
        return {
            "phase": "triage",
            "phase_number": 2,
            "title": "Scoping & Impact Assessment",
            "narrative": (
                "The IR team is now assembled. Initial analysis confirms:\n"
                "  - The svc_webapp_prod account was compromised via a webshell on app-web-03\n"
                "  - The webshell was uploaded through a SQL injection vulnerability in the customer search API\n"
                "  - Queries targeted the 'customers' table containing: full names, emails, phone numbers, "
                "hashed passwords, and billing addresses\n"
                "  - Approximately 2.3 million customer records were queried\n"
                "  - Traffic analysis shows data was exfiltrated in chunked, compressed transfers\n"
                "  - Attacker has been active for an estimated 48 hours based on webshell creation timestamp"
            ),
            "decisions": [
                {
                    "id": "tri_1",
                    "prompt": "How do you assess the scope of this breach?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Review database audit logs to identify all queries from the compromised account, analyze NetFlow for all external destinations, and check for lateral movement to other systems",
                            "score": 10,
                            "feedback": "Comprehensive approach. Correlating database audit logs, network flows, and endpoint telemetry gives the full picture of attacker activity.",
                            "next_action": "Analysis reveals the attacker also accessed a secondary reporting database but did not exfiltrate from it.",
                        },
                        {
                            "id": "b",
                            "text": "Focus solely on the customer database since that is what the alert identified",
                            "score": 3,
                            "feedback": "Too narrow. Attackers often access multiple systems. Limiting scope to the initial alert misses lateral movement and additional compromised assets.",
                            "next_action": "You miss the attacker's presence on the reporting database, which they continue to access.",
                        },
                        {
                            "id": "c",
                            "text": "Run a full vulnerability scan on all production systems to find other weaknesses",
                            "score": 2,
                            "feedback": "Wrong timing. Active vulnerability scanning during an incident adds noise, may trigger the attacker to accelerate, and does not help scope the current breach.",
                            "next_action": "The vulnerability scan causes performance degradation on production systems and generates thousands of unrelated alerts.",
                        },
                        {
                            "id": "d",
                            "text": "Check only whether payment card data was accessed, since that has the highest regulatory impact",
                            "score": 4,
                            "feedback": "Regulatory focus is important but incomplete. You need full scope assessment first, then determine which data categories trigger notification requirements.",
                            "next_action": "You confirm no payment card data was accessed but miss the full extent of PII exposure.",
                        },
                    ],
                },
                {
                    "id": "tri_2",
                    "prompt": "The CISO asks for an initial severity classification. What do you recommend?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Critical (SEV-1): Confirmed exfiltration of 2.3M PII records, active attacker presence, regulatory notification obligations under GDPR/CCPA, significant business impact",
                            "score": 10,
                            "feedback": "Accurate assessment. The volume of PII, confirmed exfiltration, and regulatory implications clearly warrant Critical severity.",
                            "next_action": "CISO concurs. Executive leadership is briefed. Legal team initiates regulatory notification timeline assessment.",
                        },
                        {
                            "id": "b",
                            "text": "High (SEV-2): Significant but no payment card data was compromised",
                            "score": 4,
                            "feedback": "Understated. The absence of payment card data does not reduce severity when 2.3M PII records are confirmed exfiltrated. PII triggers its own regulatory obligations.",
                            "next_action": "Response resources are allocated at High level, which may be insufficient for the actual scope.",
                        },
                        {
                            "id": "c",
                            "text": "Medium (SEV-3): The data was encrypted in transit so it may not be usable",
                            "score": 1,
                            "feedback": "Incorrect reasoning. The attacker encrypted the exfiltration channel (which they control), meaning they have the decryption keys. This does not reduce the severity.",
                            "next_action": "Inadequate resources are allocated. Response is delayed.",
                        },
                        {
                            "id": "d",
                            "text": "Defer classification until forensic analysis is complete",
                            "score": 3,
                            "feedback": "Delaying classification delays resource allocation and executive communication. Initial classification should be based on available information and updated as analysis progresses.",
                            "next_action": "No severity is assigned. Executive team is not briefed on urgency.",
                        },
                    ],
                },
            ],
        }

    def _phase_containment(self) -> Dict[str, Any]:
        return {
            "phase": "containment",
            "phase_number": 3,
            "title": "Containment Strategy Execution",
            "narrative": (
                "Severity is confirmed Critical. The IR Commander has authorized containment actions. "
                "The attacker is still active - NetFlow shows ongoing small data transfers (likely "
                "command-and-control heartbeats) to 185.220.101.34. You need to stop the bleeding "
                "without destroying evidence or tipping off the attacker prematurely.\n\n"
                "Current attacker footprint:\n"
                "  - Webshell on app-web-03 (/opt/tomcat/webapps/ROOT/css/style.jsp)\n"
                "  - Compromised service account svc_webapp_prod\n"
                "  - Possible persistence mechanism on db-prod-07 (scheduled task TBD)\n"
                "  - C2 channel to 185.220.101.34:8443 and 185.220.101.35:443"
            ),
            "decisions": [
                {
                    "id": "con_1",
                    "prompt": "What is your containment strategy?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Implement network segmentation to isolate db-prod-07 and app-web-03 from external traffic while maintaining internal access for forensics; block C2 IPs at the perimeter; rotate the compromised service account credentials",
                            "score": 10,
                            "feedback": "Excellent. This balanced approach stops exfiltration, preserves evidence, maintains forensic access, and addresses the compromised credentials.",
                            "next_action": "Network ACLs are applied. C2 communication is severed. Attacker loses external connectivity but evidence is preserved.",
                        },
                        {
                            "id": "b",
                            "text": "Shut down db-prod-07 and app-web-03 completely to stop all attacker activity",
                            "score": 3,
                            "feedback": "Overly aggressive. Hard shutdown destroys volatile evidence (memory, running processes, network connections). It also causes a production outage. Network isolation achieves containment while preserving evidence.",
                            "next_action": "Systems are powered off. Volatile memory evidence is lost. Customer-facing application is down.",
                        },
                        {
                            "id": "c",
                            "text": "Block only the primary C2 IP (185.220.101.34) and monitor for the attacker to pivot to backup channels",
                            "score": 5,
                            "feedback": "Partial containment. Blocking only one C2 IP while the attacker has a secondary channel is insufficient. Block all known C2 infrastructure simultaneously.",
                            "next_action": "Attacker switches to the secondary C2 (185.220.101.35) within minutes and continues operations.",
                        },
                        {
                            "id": "d",
                            "text": "Set up a honeypot with fake data to divert the attacker while you prepare full containment",
                            "score": 2,
                            "feedback": "Creative but impractical during active exfiltration. Every minute of delay means more real data is exfiltrated. Honeypot deployment requires time you do not have.",
                            "next_action": "An additional 800 MB of customer data is exfiltrated while the honeypot is being prepared.",
                        },
                    ],
                },
                {
                    "id": "con_2",
                    "prompt": "What evidence do you prioritize collecting before containment actions potentially alter the environment?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Capture volatile data first: memory dumps from both servers, active network connections, running processes, then preserve disk images and log files",
                            "score": 10,
                            "feedback": "Correct priority. Volatile evidence (memory, connections, processes) is lost on reboot or containment. Order of volatility dictates collection sequence.",
                            "next_action": "Memory dumps, process listings, and network state are captured. Disk images are queued for acquisition.",
                        },
                        {
                            "id": "b",
                            "text": "Start with full disk images of both servers to get complete copies of everything",
                            "score": 4,
                            "feedback": "Disk images are important but take hours to complete. During that time, volatile evidence may be lost. Always prioritize volatile data per the order of volatility.",
                            "next_action": "Disk imaging begins but active network connections and process memory are lost when containment actions are executed.",
                        },
                        {
                            "id": "c",
                            "text": "Focus on collecting the webshell file and database query logs only",
                            "score": 3,
                            "feedback": "Too narrow. The webshell and logs are important but non-volatile. Missing memory analysis could mean missing additional malware, credentials in memory, or C2 configuration.",
                            "next_action": "Webshell and logs are collected but memory-resident artifacts are not captured.",
                        },
                        {
                            "id": "d",
                            "text": "Evidence collection can wait until after containment is complete",
                            "score": 1,
                            "feedback": "Incorrect. Containment actions alter the environment (severing network connections, killing processes). Volatile evidence must be captured before or during containment.",
                            "next_action": "Containment is executed. Volatile evidence is permanently lost.",
                        },
                    ],
                },
            ],
        }

    def _phase_eradication(self) -> Dict[str, Any]:
        return {
            "phase": "eradication",
            "phase_number": 4,
            "title": "Threat Eradication",
            "narrative": (
                "Containment is in place. The attacker's external communication is severed. "
                "Forensic analysis has identified:\n"
                "  - Webshell: /opt/tomcat/webapps/ROOT/css/style.jsp (SHA256: a1b2c3...)\n"
                "  - Scheduled cron job on db-prod-07 as persistence (runs every 15 min)\n"
                "  - Modified SSH authorized_keys on db-prod-07 with attacker's public key\n"
                "  - SQL injection vulnerability in /api/v2/customers/search endpoint\n"
                "  - The svc_webapp_prod account password was the same across three environments"
            ),
            "decisions": [
                {
                    "id": "era_1",
                    "prompt": "How do you approach eradication?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Remove all identified persistence mechanisms (webshell, cron job, SSH keys), patch the SQL injection vulnerability, rotate all service account credentials across all environments, and verify removal through integrity checks",
                            "score": 10,
                            "feedback": "Comprehensive eradication. Addressing all persistence, the root cause vulnerability, and credential reuse prevents re-compromise.",
                            "next_action": "All attacker artifacts are removed. Vulnerability is patched. Credentials are rotated across all environments.",
                        },
                        {
                            "id": "b",
                            "text": "Reimage both affected servers from known-good backups",
                            "score": 6,
                            "feedback": "Reimaging ensures clean systems but does not address the root cause (SQL injection vulnerability) or credential reuse. The attacker could re-exploit the same vulnerability.",
                            "next_action": "Servers are reimaged. The SQL injection vulnerability is reintroduced from the backup. Credentials are unchanged.",
                        },
                        {
                            "id": "c",
                            "text": "Remove the webshell and block the C2 IPs permanently in the firewall",
                            "score": 3,
                            "feedback": "Incomplete. This misses the cron job persistence, SSH key backdoor, root cause vulnerability, and credential issue. The attacker retains multiple re-entry points.",
                            "next_action": "Webshell is removed but the cron job reinstalls a new backdoor within 15 minutes.",
                        },
                        {
                            "id": "d",
                            "text": "Only patch the SQL injection and consider the incident contained",
                            "score": 2,
                            "feedback": "Dangerous. Active persistence mechanisms remain. The attacker can continue operating through the cron job and SSH backdoor even without the original entry point.",
                            "next_action": "Vulnerability is patched but the attacker regains access through the SSH backdoor.",
                        },
                    ],
                },
            ],
        }

    def _phase_recovery(self) -> Dict[str, Any]:
        return {
            "phase": "recovery",
            "phase_number": 5,
            "title": "Recovery & Validation",
            "narrative": (
                "Eradication is complete. All identified persistence mechanisms have been removed, "
                "the vulnerability is patched, and credentials are rotated. Now you must restore "
                "normal operations while ensuring the attacker cannot regain access. The customer-facing "
                "application has been offline for 4 hours."
            ),
            "decisions": [
                {
                    "id": "rec_1",
                    "prompt": "What is your recovery approach?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Perform integrity verification on all remediated systems, restore services with enhanced monitoring, implement additional detection rules for the observed TTPs, and conduct a validation scan before going live",
                            "score": 10,
                            "feedback": "Thorough recovery process. Validation, enhanced monitoring, and TTP-based detection rules reduce the risk of undetected re-compromise.",
                            "next_action": "Systems pass integrity checks. Enhanced monitoring is deployed. Services are restored with additional safeguards.",
                        },
                        {
                            "id": "b",
                            "text": "Bring systems back online immediately to minimize business impact",
                            "score": 2,
                            "feedback": "Risky. Restoring without validation could mean residual attacker access. The short-term business pressure does not justify the risk of re-compromise.",
                            "next_action": "Systems are restored without validation. Two days later, anomalous activity is detected again.",
                        },
                        {
                            "id": "c",
                            "text": "Keep systems offline for a full week for extended forensic analysis",
                            "score": 4,
                            "feedback": "Excessive downtime. If eradication was thorough, a week-long shutdown is unnecessary and causes severe business impact. Validate and restore with monitoring.",
                            "next_action": "Extended outage causes significant revenue loss and customer complaints.",
                        },
                        {
                            "id": "d",
                            "text": "Restore from the most recent backup taken before the incident",
                            "score": 5,
                            "feedback": "Reasonable but the backup may pre-date the vulnerability patch. Ensure the patched version is applied after restoration and validate system integrity.",
                            "next_action": "Systems are restored from backup. The vulnerability patch must be reapplied.",
                        },
                    ],
                },
            ],
        }

    def _phase_post_incident(self) -> Dict[str, Any]:
        return {
            "phase": "post_incident",
            "phase_number": 6,
            "title": "Post-Incident Activity",
            "narrative": (
                "The incident is contained and services are restored. The following tasks remain:\n"
                "  - Regulatory notification (2.3M records, PII, potential GDPR/CCPA obligations)\n"
                "  - Customer notification\n"
                "  - Post-incident review (lessons learned)\n"
                "  - Report generation\n"
                "  - Control improvements"
            ),
            "decisions": [
                {
                    "id": "post_1",
                    "prompt": "What is your post-incident priority?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Initiate regulatory notification within required timeframes (72 hours for GDPR), prepare customer notifications with credit monitoring offer, schedule a blameless post-incident review within 5 business days, and document all findings in a formal incident report",
                            "score": 10,
                            "feedback": "Complete post-incident response. Regulatory compliance, transparent customer communication, and structured lessons learned are all addressed.",
                            "next_action": "Legal files regulatory notifications. Customer communication is prepared. Post-incident review is scheduled.",
                        },
                        {
                            "id": "b",
                            "text": "Focus on the incident report first, then handle notifications when the report is complete",
                            "score": 4,
                            "feedback": "Report is important but regulatory notification deadlines are strict (72 hours under GDPR). Delaying notifications to complete the report risks regulatory penalties.",
                            "next_action": "Report writing takes priority. GDPR 72-hour notification deadline approaches.",
                        },
                        {
                            "id": "c",
                            "text": "Immediately issue a public press release about the breach",
                            "score": 3,
                            "feedback": "Premature public disclosure without legal review and proper preparation can cause additional harm. Work with legal and PR to craft appropriate communications.",
                            "next_action": "Press release goes out with incomplete information, causing public confusion and stock price impact.",
                        },
                        {
                            "id": "d",
                            "text": "Delay notifications to assess whether the exfiltrated data is actually usable",
                            "score": 1,
                            "feedback": "Non-compliant approach. Regulatory frameworks require notification based on the breach occurring, not on confirmed misuse. Delaying risks severe penalties.",
                            "next_action": "Notification deadline passes. Regulatory authority opens an investigation.",
                        },
                    ],
                },
            ],
        }

    def get_max_score(self) -> int:
        """Calculate the maximum achievable score for this scenario."""
        total = 0
        for phase in self.get_phases():
            for decision in phase["decisions"]:
                max_choice_score = max(c["score"] for c in decision["choices"])
                total += max_choice_score
        return total

    def get_scoring_rubric(self) -> Dict[str, str]:
        """Return scoring thresholds and their interpretations."""
        max_score = self.get_max_score()
        return {
            "expert": f"{int(max_score * 0.9)}-{max_score} points: Expert-level incident response",
            "proficient": f"{int(max_score * 0.7)}-{int(max_score * 0.9) - 1} points: Proficient responder",
            "developing": f"{int(max_score * 0.5)}-{int(max_score * 0.7) - 1} points: Developing skills, review playbook",
            "novice": f"Below {int(max_score * 0.5)} points: Significant gaps, training recommended",
        }
