"""
Ransomware Attack Scenario
===========================

Simulates a ransomware incident where an attacker deploys file-encrypting
malware across the corporate network after gaining initial access through
a phishing email with a malicious macro-enabled document.

Attack narrative:
    An employee opens a weaponized Excel document received via email.
    The macro downloads a second-stage payload that establishes persistence,
    performs Active Directory reconnaissance, moves laterally using stolen
    credentials, and deploys ransomware to file servers and workstations.
    A ransom note demands 15 BTC within 72 hours.
"""

from typing import Dict, List, Any


class RansomwareScenario:
    """Ransomware incident response scenario with decision tree."""

    def __init__(self):
        self.name = "ransomware"
        self.title = "Enterprise Ransomware Attack - LockStorm Variant"
        self.description = (
            "Multiple endpoints are reporting file encryption. The SOC has received "
            "23 alerts in the past 15 minutes from EDR agents detecting suspicious "
            "file modification patterns consistent with ransomware encryption. Ransom "
            "notes (README_RESTORE.txt) are appearing on affected systems demanding "
            "15 BTC. The encryption appears to be spreading through the network via "
            "SMB and compromised domain admin credentials. Initial patient zero is "
            "identified as workstation WS-FIN-042 in the Finance department."
        )
        self.default_severity = "critical"
        self.estimated_duration_minutes = 50
        self.category = "ransomware"
        self.affected_systems = [
            "WS-FIN-042 (Patient Zero - Finance Workstation)",
            "FS-CORP-01 (Corporate File Server - 12TB)",
            "FS-CORP-02 (Department Shared Drives - 8TB)",
            "WS-FIN-* (14 additional Finance workstations)",
            "DC-PROD-01 (Domain Controller - compromised credentials)",
            "PRINT-SVR-03 (Print Server - encrypted)",
        ]
        self.initial_iocs = [
            {"type": "hash_sha256", "value": "e7a3b1c9d5f2810a4567890bcd123ef456789012abcd3456ef7890123456abcd", "context": "Ransomware binary (lockstorm.exe)"},
            {"type": "hash_sha256", "value": "f8b4c2dae6031b5678901234cde456f0789012345bcde6789f0123456789bcde", "context": "Macro dropper (Q3_Budget_Review.xlsm)"},
            {"type": "filename", "value": "README_RESTORE.txt", "context": "Ransom note dropped in every encrypted directory"},
            {"type": "filename", "value": "lockstorm.exe", "context": "Ransomware payload"},
            {"type": "email", "value": "accounting-dept@financialreview-docs.com", "context": "Phishing sender address"},
            {"type": "domain", "value": "financialreview-docs.com", "context": "Phishing infrastructure domain"},
            {"type": "ip", "value": "91.234.56.78", "context": "C2 server for second-stage payload"},
            {"type": "file_extension", "value": ".lockstorm", "context": "Extension appended to encrypted files"},
            {"type": "registry_key", "value": "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\SysUpdate", "context": "Persistence mechanism"},
        ]
        self.attack_vector = "Phishing email -> macro execution -> Cobalt Strike beacon -> AD recon -> lateral movement -> ransomware deployment"

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
            "title": "Ransomware Detection & Initial Assessment",
            "narrative": (
                "At 09:42 local time, the EDR platform generated burst alerts for rapid file "
                "modification on WS-FIN-042. Within 8 minutes, similar alerts fired on 14 additional "
                "workstations and 2 file servers. The helpdesk is receiving calls from Finance "
                "employees unable to open their files. Files have been renamed with a .lockstorm "
                "extension and a README_RESTORE.txt file is present on every affected desktop.\n\n"
                "The ransom note reads:\n"
                "'Your files have been encrypted by LockStorm. To recover your data, send 15 BTC "
                "to [wallet address] within 72 hours. After 72 hours, the price doubles. After 7 "
                "days, your data will be permanently deleted from our servers. Contact: "
                "restore@lockstorm-support.onion'"
            ),
            "decisions": [
                {
                    "id": "det_1",
                    "prompt": "Encryption is actively spreading. What is your immediate first action?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Isolate affected network segments immediately to stop lateral spread while preserving running systems for forensics",
                            "score": 10,
                            "feedback": "Correct. With active encryption spreading, network isolation is the top priority. Every second of delay means more encrypted files. This is the one scenario where containment can precede full validation.",
                            "next_action": "Finance VLAN is isolated. Encryption stops spreading to new systems. Already-affected systems continue encrypting local files.",
                        },
                        {
                            "id": "b",
                            "text": "Validate the alerts by examining the EDR telemetry in detail before taking action",
                            "score": 4,
                            "feedback": "Normally correct, but ransomware is the exception. When encryption is actively spreading and confirmed by multiple indicators (EDR + user reports + ransom notes), speed of containment outweighs thorough validation.",
                            "next_action": "During the 20-minute validation period, 6 additional systems are encrypted.",
                        },
                        {
                            "id": "c",
                            "text": "Begin negotiating with the threat actor to buy time",
                            "score": 1,
                            "feedback": "Premature and inadvisable without legal counsel and executive authorization. Communication with threat actors should only happen after containment and with proper guidance.",
                            "next_action": "Threat actor is engaged without authorization. Communication is poorly handled.",
                        },
                        {
                            "id": "d",
                            "text": "Shut down all domain controllers to prevent credential-based lateral movement",
                            "score": 5,
                            "feedback": "Addresses credential abuse but shutting down DCs causes massive operational disruption and prevents authentication for legitimate IR activities. Network segmentation is more surgical.",
                            "next_action": "Domain controllers are offline. All authentication-dependent services fail. IR team cannot use standard tools.",
                        },
                    ],
                },
                {
                    "id": "det_2",
                    "prompt": "Who needs to be notified immediately?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Activate the IR team, notify the CISO and CTO, engage the crisis management team, and place legal counsel and cyber insurance carrier on standby",
                            "score": 10,
                            "feedback": "Comprehensive notification. Ransomware events require executive awareness, legal guidance for potential payment decisions, and insurance carrier engagement for coverage.",
                            "next_action": "Full incident response structure is activated. Legal reviews insurance policy. Executive team prepares for potential public disclosure.",
                        },
                        {
                            "id": "b",
                            "text": "Notify only the IT operations team to help contain the spread",
                            "score": 3,
                            "feedback": "Insufficient. Ransomware is a business crisis, not just an IT problem. Executive leadership, legal, and insurance need immediate notification.",
                            "next_action": "IT operations assists with containment but executive leadership is blindsided when they learn about the incident from employees.",
                        },
                        {
                            "id": "c",
                            "text": "Notify the FBI/law enforcement immediately before doing anything else",
                            "score": 5,
                            "feedback": "Law enforcement notification is important and should happen, but it should not delay containment and IR team activation. Engage LE in parallel, not as a gating action.",
                            "next_action": "FBI is notified. They advise against paying the ransom but cannot assist with immediate containment.",
                        },
                        {
                            "id": "d",
                            "text": "Send an all-hands email warning employees not to open any attachments",
                            "score": 4,
                            "feedback": "Good preventive measure but not the priority during active encryption. This should happen in parallel with containment and notification, not as the primary action.",
                            "next_action": "Employees are warned. Some disconnect from the network on their own, which is helpful but uncoordinated.",
                        },
                    ],
                },
            ],
        }

    def _phase_triage(self) -> Dict[str, Any]:
        return {
            "phase": "triage",
            "phase_number": 2,
            "title": "Scope Assessment & Backup Evaluation",
            "narrative": (
                "Network isolation has stopped the lateral spread. Current status:\n"
                "  - 31 workstations confirmed encrypted (all Finance department)\n"
                "  - 2 file servers encrypted (FS-CORP-01 and FS-CORP-02 - combined 20TB)\n"
                "  - 1 print server encrypted (non-critical)\n"
                "  - Domain controller DC-PROD-01 was used for lateral movement but is not encrypted\n"
                "  - Patient zero: WS-FIN-042 received phishing email at 09:15, macro executed at 09:18\n"
                "  - Ransomware variant identified as LockStorm v3.2 (no known free decryptor)\n"
                "  - Backup status is being assessed"
            ),
            "decisions": [
                {
                    "id": "tri_1",
                    "prompt": "What is your priority assessment task?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Verify backup integrity and recovery capability for all affected systems; determine the Recovery Point Objective (RPO) and Recovery Time Objective (RTO) for critical data",
                            "score": 10,
                            "feedback": "Critical assessment. The decision to pay or not pay ransom depends entirely on backup availability and recovery capability. This must be determined first.",
                            "next_action": "Backup assessment reveals: file server backups are 18 hours old and verified intact. Workstation backups are incomplete.",
                        },
                        {
                            "id": "b",
                            "text": "Focus on identifying all encrypted systems and creating a comprehensive asset inventory",
                            "score": 6,
                            "feedback": "Important but secondary to backup assessment. Knowing what is encrypted matters less if you can determine recovery capability from backups.",
                            "next_action": "Full inventory is created but backup viability remains unknown.",
                        },
                        {
                            "id": "c",
                            "text": "Attempt to reverse-engineer the encryption to find weaknesses",
                            "score": 2,
                            "feedback": "Extremely unlikely to succeed. Modern ransomware uses strong encryption (AES-256 + RSA-2048). This is a task for specialized researchers, not an IR priority.",
                            "next_action": "Reverse engineering confirms AES-256 encryption with no implementation flaws.",
                        },
                        {
                            "id": "d",
                            "text": "Research the LockStorm ransomware group to understand their behavior and reliability",
                            "score": 5,
                            "feedback": "Useful intelligence but not the top priority. Understanding the threat actor matters more if you are considering payment. Backup assessment should come first.",
                            "next_action": "OSINT reveals LockStorm is a known group that generally provides working decryptors after payment, but this is not guaranteed.",
                        },
                    ],
                },
            ],
        }

    def _phase_containment(self) -> Dict[str, Any]:
        return {
            "phase": "containment",
            "phase_number": 3,
            "title": "Full Containment & Evidence Preservation",
            "narrative": (
                "Backup assessment is complete:\n"
                "  - File server data: 18-hour-old backup verified intact (offsite, air-gapped)\n"
                "  - Finance workstation data: Mixed - some had cloud sync, some had no backup\n"
                "  - Approximately 2TB of unique workstation data has no backup\n"
                "  - Domain controller: Not encrypted, but compromised credentials need rotation\n\n"
                "The attacker used compromised domain admin credentials (da_jsmith) to deploy "
                "ransomware via PsExec and Group Policy. The Cobalt Strike beacon was communicating "
                "with 91.234.56.78 before network isolation."
            ),
            "decisions": [
                {
                    "id": "con_1",
                    "prompt": "How do you ensure full containment?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Reset all domain admin and privileged account passwords via an out-of-band process; disable PsExec and remote execution tools via GPO; block all known C2 indicators at perimeter and DNS; capture memory and disk images from patient zero and representative encrypted systems",
                            "score": 10,
                            "feedback": "Comprehensive containment addressing credential compromise, lateral movement mechanisms, C2 infrastructure, and evidence preservation.",
                            "next_action": "All privileged credentials are rotated. Lateral movement tools are disabled. C2 is blocked. Forensic images are captured.",
                        },
                        {
                            "id": "b",
                            "text": "Focus on resetting only the compromised da_jsmith account and collecting the ransomware binary for analysis",
                            "score": 4,
                            "feedback": "Insufficient. The attacker likely compromised additional credentials beyond da_jsmith. A full privileged credential reset is necessary. Collecting the binary alone misses volatile evidence.",
                            "next_action": "da_jsmith is reset. The attacker's other compromised accounts remain active.",
                        },
                        {
                            "id": "c",
                            "text": "Disconnect the entire corporate network from the internet to prevent any communication",
                            "score": 5,
                            "feedback": "Effective but overly broad. The attacker's C2 is already severed by segment isolation. Full internet disconnection hampers IR operations and impacts unaffected business units.",
                            "next_action": "Internet is disconnected. IR team loses access to threat intelligence feeds and cloud-based tools.",
                        },
                        {
                            "id": "d",
                            "text": "Pay the ransom immediately to minimize business disruption",
                            "score": 0,
                            "feedback": "Premature and inadvisable. Payment should only be considered as a last resort after full assessment, with legal counsel, insurance carrier approval, and law enforcement consultation. You have viable backups.",
                            "next_action": "15 BTC is transferred. No guarantee of decryption. Legal and compliance implications are triggered.",
                        },
                    ],
                },
            ],
        }

    def _phase_eradication(self) -> Dict[str, Any]:
        return {
            "phase": "eradication",
            "phase_number": 4,
            "title": "Malware Eradication & System Cleaning",
            "narrative": (
                "Containment is complete. Forensic analysis of patient zero reveals:\n"
                "  - Initial access: Phishing email with macro-enabled Excel (Q3_Budget_Review.xlsm)\n"
                "  - Macro downloaded Cobalt Strike beacon from financialreview-docs.com\n"
                "  - Beacon performed Kerberoasting to obtain domain admin hash\n"
                "  - Ransomware was deployed via Group Policy modification and PsExec\n"
                "  - Persistence: Registry Run key, scheduled task 'WindowsUpdate'\n"
                "  - Anti-forensics: VSS shadow copies deleted on all encrypted systems"
            ),
            "decisions": [
                {
                    "id": "era_1",
                    "prompt": "What is your eradication strategy for 31 affected workstations?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Reimage all affected workstations from known-good gold images; rebuild file servers from clean OS with restored data from verified backups; scan all unaffected systems with updated EDR signatures for the specific IOCs; remove the malicious Group Policy object",
                            "score": 10,
                            "feedback": "Complete eradication. Reimaging is the most reliable way to ensure all malware components are removed. Scanning unaffected systems catches any dormant infections.",
                            "next_action": "Reimage process begins. File servers are rebuilt. EDR scans detect 3 additional workstations with dormant Cobalt Strike beacons.",
                        },
                        {
                            "id": "b",
                            "text": "Run antivirus scans on affected systems and remove detected items",
                            "score": 3,
                            "feedback": "Unreliable. The systems are encrypted and may have additional undetected components. Antivirus may miss custom implants. Reimaging is the only way to be certain.",
                            "next_action": "AV removes some components but may miss rootkits or dormant implants.",
                        },
                        {
                            "id": "c",
                            "text": "Only rebuild the file servers and let users continue on their encrypted workstations with new profiles",
                            "score": 2,
                            "feedback": "Leaving potentially compromised workstations in service is a significant risk. The ransomware may have components that survive user profile changes.",
                            "next_action": "File servers are rebuilt but workstations remain potentially compromised.",
                        },
                        {
                            "id": "d",
                            "text": "Replace all affected hardware with new equipment",
                            "score": 4,
                            "feedback": "Excessive. The malware is software-based and does not persist in firmware (for this variant). Reimaging achieves the same result at far lower cost.",
                            "next_action": "Hardware procurement is initiated. Recovery is delayed by weeks waiting for new equipment.",
                        },
                    ],
                },
            ],
        }

    def _phase_recovery(self) -> Dict[str, Any]:
        return {
            "phase": "recovery",
            "phase_number": 5,
            "title": "Data Recovery & Service Restoration",
            "narrative": (
                "Eradication is complete. All affected systems are reimaged or rebuilt. "
                "File server data restoration from 18-hour-old backups is in progress. "
                "The 2TB of unbackable workstation data remains encrypted. "
                "Business operations have been impaired for 16 hours."
            ),
            "decisions": [
                {
                    "id": "rec_1",
                    "prompt": "How do you prioritize recovery?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Restore file servers first (highest business impact), then workstations by department criticality; implement enhanced monitoring on all restored systems; verify data integrity post-restoration; accept 18 hours of data loss and work with business to reconstruct",
                            "score": 10,
                            "feedback": "Prioritized recovery based on business impact. Accepting manageable data loss from backups is the correct approach rather than considering ransom payment for marginal data recovery.",
                            "next_action": "File servers are restored within 6 hours. Workstations are reimaged and users resume operations. 18 hours of data requires manual reconstruction.",
                        },
                        {
                            "id": "b",
                            "text": "Restore everything simultaneously to get everyone back online at the same time",
                            "score": 4,
                            "feedback": "Parallel restoration sounds efficient but stretches IT resources thin. Prioritization ensures the most critical services recover first.",
                            "next_action": "All systems start recovery. Competition for bandwidth and personnel slows overall restoration.",
                        },
                        {
                            "id": "c",
                            "text": "Consider paying the ransom for the 2TB of data with no backup, since backups cover most systems",
                            "score": 3,
                            "feedback": "Payment for a subset of data is still inadvisable when the majority of data is recoverable from backups. There is no guarantee the decryptor works, and payment funds criminal operations.",
                            "next_action": "Legal counsel and insurance carrier are consulted. They advise against payment given the limited unrecoverable data.",
                        },
                        {
                            "id": "d",
                            "text": "Delay recovery until a thorough threat hunt is completed across the entire enterprise",
                            "score": 5,
                            "feedback": "Threat hunting is important but a full enterprise hunt takes days or weeks. Recovery of cleaned systems can proceed in parallel with hunting on unaffected segments.",
                            "next_action": "Recovery is delayed. Business impact continues to accumulate.",
                        },
                    ],
                },
            ],
        }

    def _phase_post_incident(self) -> Dict[str, Any]:
        return {
            "phase": "post_incident",
            "phase_number": 6,
            "title": "Post-Incident Review & Hardening",
            "narrative": (
                "Recovery is complete. Total incident duration: 28 hours. Total downtime: 22 hours. "
                "Data loss: 18 hours of file server changes. The following systemic issues were identified:\n"
                "  - Phishing email bypassed email gateway (no macro blocking policy)\n"
                "  - No MFA on domain admin accounts\n"
                "  - PsExec allowed by default across the network\n"
                "  - No network segmentation between departments\n"
                "  - Backup verification was not performed regularly\n"
                "  - No EDR deployment on file servers"
            ),
            "decisions": [
                {
                    "id": "post_1",
                    "prompt": "What improvements do you recommend?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Implement MFA on all privileged accounts, deploy macro-blocking email policies, enforce network segmentation, extend EDR to all servers, implement automated backup verification, conduct phishing awareness training, and establish a regular purple team exercise program",
                            "score": 10,
                            "feedback": "Comprehensive improvement plan addressing all identified gaps. Each recommendation directly maps to a failure point observed during the incident.",
                            "next_action": "Improvement roadmap is approved by executive leadership. Implementation begins with MFA as the highest priority.",
                        },
                        {
                            "id": "b",
                            "text": "Focus on deploying better email filtering to prevent future phishing emails",
                            "score": 4,
                            "feedback": "Email filtering is important but only addresses the initial access vector. The attacker succeeded because of multiple control failures. Defense in depth requires addressing all gaps.",
                            "next_action": "Email filtering is improved but other vulnerabilities remain unaddressed.",
                        },
                        {
                            "id": "c",
                            "text": "Purchase a ransomware-specific security product to detect and block encryption",
                            "score": 3,
                            "feedback": "A single product does not address the systemic issues. The existing EDR detected the ransomware - the problem was that it was deployed too late and not on all systems. Address process and coverage gaps.",
                            "next_action": "New product is purchased. It provides an additional layer but fundamental gaps remain.",
                        },
                        {
                            "id": "d",
                            "text": "Discipline the employee who opened the phishing email",
                            "score": 0,
                            "feedback": "Punitive approaches to phishing are counterproductive. They discourage incident reporting and do not address the technical control failures. The email should have been blocked before reaching the user.",
                            "next_action": "The employee is reprimanded. Other employees become reluctant to report suspicious emails.",
                        },
                    ],
                },
            ],
        }

    def get_max_score(self) -> int:
        """Calculate the maximum achievable score."""
        total = 0
        for phase in self.get_phases():
            for decision in phase["decisions"]:
                max_choice_score = max(c["score"] for c in decision["choices"])
                total += max_choice_score
        return total

    def get_scoring_rubric(self) -> Dict[str, str]:
        """Return scoring thresholds."""
        max_score = self.get_max_score()
        return {
            "expert": f"{int(max_score * 0.9)}-{max_score}: Expert-level ransomware response",
            "proficient": f"{int(max_score * 0.7)}-{int(max_score * 0.9) - 1}: Proficient responder",
            "developing": f"{int(max_score * 0.5)}-{int(max_score * 0.7) - 1}: Developing skills",
            "novice": f"Below {int(max_score * 0.5)}: Significant gaps identified",
        }
