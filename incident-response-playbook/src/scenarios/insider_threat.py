"""
Insider Threat Scenario
========================

Simulates a malicious insider incident where a disgruntled employee
with privileged access exfiltrates proprietary data and attempts to
sabotage systems before departing the organization.

Attack narrative:
    A senior database administrator who recently received a negative
    performance review and was passed over for promotion is observed
    accessing systems outside normal business hours. DLP alerts show
    large data transfers to personal cloud storage. HR has confirmed
    the employee submitted a resignation effective in two weeks. Forensic
    indicators suggest data theft and potential logic bomb placement.
"""

from typing import Dict, List, Any


class InsiderThreatScenario:
    """Insider threat incident response scenario with decision tree."""

    def __init__(self):
        self.name = "insider_threat"
        self.title = "Privileged Insider Data Theft & Sabotage Attempt"
        self.description = (
            "The DLP system has flagged multiple policy violations from the account of "
            "Robert Keller, a senior database administrator. Over the past 5 days, his "
            "account has downloaded 14 GB of data from internal repositories including "
            "product design documents, customer lists, pricing databases, and source code "
            "repositories. The data was uploaded to a personal Dropbox account. HR confirms "
            "Keller submitted his resignation 3 days ago after receiving a negative performance "
            "review. He is joining a direct competitor. IT monitoring also detected unusual "
            "cron job creation on production database servers during off-hours access sessions."
        )
        self.default_severity = "high"
        self.estimated_duration_minutes = 40
        self.category = "insider_threat"
        self.affected_systems = [
            "db-prod-01 through db-prod-04 (Production databases)",
            "gitlab.internal (Source code repository)",
            "sharepoint.internal (Document management)",
            "crm.internal (Customer relationship management)",
            "pricing-db.internal (Pricing and contracts database)",
        ]
        self.initial_iocs = [
            {"type": "account", "value": "r.keller", "context": "Subject of insider threat investigation"},
            {"type": "dlp_violation", "value": "14 GB uploaded to Dropbox personal account", "context": "Data exfiltration channel"},
            {"type": "access_anomaly", "value": "Off-hours access 02:00-04:00 for 5 consecutive nights", "context": "Unusual access pattern"},
            {"type": "data_access", "value": "Bulk download of customer list (847,000 records)", "context": "Accessed data outside job scope"},
            {"type": "data_access", "value": "Clone of product-roadmap repository on GitLab", "context": "IP theft indicator"},
            {"type": "suspicious_activity", "value": "New cron jobs created on db-prod-02 and db-prod-03", "context": "Potential logic bomb"},
            {"type": "data_access", "value": "Export of pricing database with competitor analysis", "context": "Trade secret access"},
        ]
        self.attack_vector = "Legitimate privileged access abused for unauthorized data exfiltration and potential sabotage"

    def get_phases(self) -> List[Dict[str, Any]]:
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
            "title": "Insider Threat Detection & Initial Assessment",
            "narrative": (
                "The DLP alert was triggered at 08:30 when the daily policy violation report "
                "was reviewed by the SOC. The alert shows Keller's account uploading files to "
                "Dropbox (cloud-storage-personal policy violation) over the past 5 days:\n\n"
                "  - Day 1: 2.1 GB - Product design documents (PDF, CAD files)\n"
                "  - Day 2: 3.4 GB - Source code repositories (git bundle files)\n"
                "  - Day 3: 4.8 GB - Customer lists and CRM exports (CSV, Excel)\n"
                "  - Day 4: 2.2 GB - Pricing database exports and contract terms\n"
                "  - Day 5: 1.5 GB - Additional source code and architecture documents\n\n"
                "Keller's manager confirms the employee has no legitimate business need to "
                "access pricing databases or customer lists in bulk. His role is database "
                "administration, not business analytics."
            ),
            "decisions": [
                {
                    "id": "det_1",
                    "prompt": "How do you handle this detection given that the subject is a current employee with privileged access?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Engage HR, Legal, and the insider threat program lead before taking any action; document all findings; do NOT alert the subject; coordinate a response plan that addresses both the data theft and the potential sabotage risk",
                            "score": 10,
                            "feedback": "Correct. Insider threat investigations require careful coordination with HR and Legal due to employment law, privacy regulations, and the need to preserve evidence without tipping off the subject. The potential for sabotage adds urgency.",
                            "next_action": "Confidential coordination call with HR, Legal, and IR. Investigation plan is established with strict need-to-know.",
                        },
                        {
                            "id": "b",
                            "text": "Immediately disable Keller's account and confront him about the data transfers",
                            "score": 2,
                            "feedback": "Dangerous. Confronting the subject before evidence is preserved may prompt destruction of evidence or activation of the potential logic bomb. Disabling access without coordination with HR/Legal may violate employment policies.",
                            "next_action": "Keller is confronted. He becomes hostile and refuses to cooperate. Legal implications arise from improper handling.",
                        },
                        {
                            "id": "c",
                            "text": "Monitor Keller's activity silently for several more weeks to build a stronger case",
                            "score": 3,
                            "feedback": "Extended monitoring allows continued data theft. While building a case is important, the combination of confirmed exfiltration and potential sabotage (cron jobs) requires prompt action. Balance evidence gathering with risk mitigation.",
                            "next_action": "Monitoring continues. Keller exfiltrates an additional 6 GB of data over the next week.",
                        },
                        {
                            "id": "d",
                            "text": "Send a company-wide reminder about data handling policies as a deterrent",
                            "score": 1,
                            "feedback": "Ineffective and counterproductive. A general reminder will not stop a deliberate insider threat and may alert Keller that his activities are being noticed, prompting him to accelerate.",
                            "next_action": "Policy reminder is sent. Keller accelerates his data exfiltration, suspecting detection.",
                        },
                    ],
                },
            ],
        }

    def _phase_triage(self) -> Dict[str, Any]:
        return {
            "phase": "triage",
            "phase_number": 2,
            "title": "Investigation Scoping & Risk Assessment",
            "narrative": (
                "The insider threat response team (IR lead, HR, Legal, Keller's VP) has convened. "
                "Legal has confirmed the investigation can proceed under the acceptable use policy "
                "that Keller signed. Key findings so far:\n\n"
                "  - Keller has database admin (DBA) privileges on all production databases\n"
                "  - He has root/sudo access on 4 production database servers\n"
                "  - The cron jobs created on db-prod-02 and db-prod-03 are set to execute on a future date\n"
                "  - The cron job scripts have not been analyzed yet but were created at 03:15 AM\n"
                "  - Keller's new employer is a direct competitor (confirmed via LinkedIn)\n"
                "  - His resignation is effective in 11 days\n"
                "  - He is scheduled to work normally until his last day"
            ),
            "decisions": [
                {
                    "id": "tri_1",
                    "prompt": "What is your top priority risk to assess?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Analyze the cron job scripts immediately - they could be logic bombs designed to destroy or corrupt production data on a trigger date; this is a potential sabotage threat that takes priority over the exfiltration investigation",
                            "score": 10,
                            "feedback": "Correct priority. A logic bomb on production databases represents catastrophic risk. Data exfiltration has already occurred and cannot be undone; sabotage can potentially be prevented.",
                            "next_action": "Analysis reveals the cron jobs are scripts that would DROP all tables in the production databases on the date of Keller's last day.",
                        },
                        {
                            "id": "b",
                            "text": "Focus on quantifying exactly what data was exfiltrated to assess regulatory notification requirements",
                            "score": 5,
                            "feedback": "Important for the overall investigation but not the top priority when potential destructive logic bombs exist. Exfiltrated data cannot be un-exfiltrated; sabotage can be prevented.",
                            "next_action": "Exfiltration scope is documented. Cron job analysis is deferred.",
                        },
                        {
                            "id": "c",
                            "text": "Check if Keller has shared the exfiltrated data with anyone else",
                            "score": 4,
                            "feedback": "Relevant for damage assessment but premature. Addressing the immediate sabotage risk and securing evidence should come first.",
                            "next_action": "Investigation into data sharing begins. Cron job risk remains unassessed.",
                        },
                        {
                            "id": "d",
                            "text": "Interview Keller's colleagues to understand his recent behavior and motivations",
                            "score": 3,
                            "feedback": "Background context is useful but interviews risk breaking need-to-know and alerting Keller. Technical evidence analysis should precede interviews.",
                            "next_action": "Two colleagues are interviewed. Word reaches Keller through informal channels.",
                        },
                    ],
                },
                {
                    "id": "tri_2",
                    "prompt": "The cron jobs are confirmed logic bombs that would drop all production tables. What severity do you assign?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Critical (SEV-1): Confirmed data theft of trade secrets and customer data heading to a competitor, plus an active sabotage device on production systems that could destroy business-critical data",
                            "score": 10,
                            "feedback": "Accurate. The combination of confirmed IP theft, customer data exfiltration, and an active logic bomb on production systems is a Critical severity event requiring maximum priority.",
                            "next_action": "Critical severity declared. Response is accelerated. Executive team is briefed under NDA.",
                        },
                        {
                            "id": "b",
                            "text": "High (SEV-2): Serious but the logic bomb has not executed yet so the damage is preventable",
                            "score": 5,
                            "feedback": "The logic bomb's non-execution is fortunate but does not reduce the overall severity. The confirmed data theft alone warrants Critical, and the sabotage intent elevates the threat.",
                            "next_action": "High severity is assigned. Resources may be insufficient for the combined data theft and sabotage response.",
                        },
                        {
                            "id": "c",
                            "text": "Medium: This is an HR issue, not a security incident",
                            "score": 0,
                            "feedback": "Fundamentally incorrect classification. Data theft of trade secrets and active sabotage devices are severe security incidents. This requires full IR response, not just HR action.",
                            "next_action": "The incident is underresourced and mishandled.",
                        },
                        {
                            "id": "d",
                            "text": "Critical but only classify it internally to avoid reputational damage",
                            "score": 6,
                            "feedback": "Critical classification is correct. Internal handling is appropriate initially, but regulatory notification obligations may require external disclosure depending on the data types exfiltrated.",
                            "next_action": "Critical severity is assigned internally. Legal assesses external notification requirements.",
                        },
                    ],
                },
            ],
        }

    def _phase_containment(self) -> Dict[str, Any]:
        return {
            "phase": "containment",
            "phase_number": 3,
            "title": "Insider Containment & Access Revocation",
            "narrative": (
                "Severity is Critical. The logic bombs are confirmed. Legal and HR have approved "
                "immediate termination with cause. The plan must be executed carefully to prevent "
                "Keller from taking any destructive action if he realizes he is being investigated. "
                "He is currently at his desk working normally. It is 10:30 AM."
            ),
            "decisions": [
                {
                    "id": "con_1",
                    "prompt": "How do you execute the containment?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Coordinate simultaneous actions: (1) Remove the logic bomb cron jobs from production servers, (2) Revoke all of Keller's access credentials and VPN tokens at the exact moment HR escorts him to a private meeting room for termination, (3) Have security present for the HR meeting, (4) Collect all company devices (laptop, phone, badge), (5) Block his personal Dropbox endpoints at the proxy",
                            "score": 10,
                            "feedback": "Precisely coordinated containment. Simultaneous execution prevents Keller from taking action between learning he is terminated and losing access. Logic bomb removal is prioritized.",
                            "next_action": "At 10:45, Keller is escorted to HR. Simultaneously, his access is revoked, logic bombs are removed, and devices are collected. Keller is terminated with cause.",
                        },
                        {
                            "id": "b",
                            "text": "Disable Keller's accounts first, then have HR inform him about the termination",
                            "score": 5,
                            "feedback": "Access revocation should be simultaneous with the HR action, not before. If Keller notices his access is disabled (locked out of his workstation) before HR reaches him, he may flee with devices or attempt alternative destructive actions.",
                            "next_action": "Keller's access is disabled. He notices his login failing and becomes agitated before HR arrives.",
                        },
                        {
                            "id": "c",
                            "text": "Let Keller continue working for the remaining 11 days under enhanced monitoring while building a legal case",
                            "score": 1,
                            "feedback": "Unacceptable risk. A confirmed malicious insider with root access to production databases and active logic bombs cannot be allowed to continue operating. The legal case is already strong with the DLP evidence and logic bomb discovery.",
                            "next_action": "Keller discovers the investigation and modifies the logic bombs to execute immediately.",
                        },
                        {
                            "id": "d",
                            "text": "Remove the cron jobs first, then wait for Keller's last day to address the termination",
                            "score": 3,
                            "feedback": "Removing the immediate sabotage threat is good, but allowing a confirmed malicious insider to retain privileged access for 11 more days invites creation of new sabotage mechanisms or continued exfiltration.",
                            "next_action": "Logic bombs are removed. Keller creates new, better-hidden persistence mechanisms over the next few days.",
                        },
                    ],
                },
            ],
        }

    def _phase_eradication(self) -> Dict[str, Any]:
        return {
            "phase": "eradication",
            "phase_number": 4,
            "title": "Threat Eradication & System Integrity Verification",
            "narrative": (
                "Keller has been terminated and escorted from the building. All company devices "
                "are recovered. Access is fully revoked. The logic bomb cron jobs have been removed. "
                "Now you must ensure no other backdoors or sabotage mechanisms remain."
            ),
            "decisions": [
                {
                    "id": "era_1",
                    "prompt": "How do you verify system integrity after removing the insider's access?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Conduct a comprehensive audit: review all cron jobs, scheduled tasks, and startup scripts on systems Keller had access to; check for unauthorized user accounts or SSH keys; verify database triggers and stored procedures for malicious modifications; review recent code commits in repositories he accessed; rotate all shared credentials and service account passwords he may have known",
                            "score": 10,
                            "feedback": "Thorough eradication approach. A privileged insider could have planted backdoors in many places. Checking all persistence mechanisms and shared credentials is essential.",
                            "next_action": "Audit discovers a modified database trigger on db-prod-01 that would corrupt data if a specific table was updated. It is removed. All shared credentials are rotated.",
                        },
                        {
                            "id": "b",
                            "text": "The cron jobs were the main threat. With those removed and Keller's access revoked, the eradication is complete",
                            "score": 2,
                            "feedback": "Dangerously narrow view. A senior DBA with root access had unlimited ability to plant backdoors. The cron jobs may be only the visible sabotage. Deep inspection of all accessible systems is required.",
                            "next_action": "The hidden database trigger remains in place. Months later, a routine table update triggers data corruption.",
                        },
                        {
                            "id": "c",
                            "text": "Rebuild all production database servers from scratch to be certain",
                            "score": 6,
                            "feedback": "Complete rebuilds provide the highest assurance but cause extended downtime for production databases. A thorough audit may be sufficient if conducted competently. Rebuilds should be reserved for cases where audit cannot provide confidence.",
                            "next_action": "Database servers are rebuilt. Extended downtime impacts business operations for 72 hours.",
                        },
                        {
                            "id": "d",
                            "text": "Run antivirus and rootkit detection scans on the affected servers",
                            "score": 3,
                            "feedback": "Insider threat artifacts are not malware in the traditional sense. Antivirus will not detect malicious cron jobs, database triggers, or modified application code. Manual and targeted auditing is required.",
                            "next_action": "Scans complete with no findings. The insider's non-malware artifacts remain undetected.",
                        },
                    ],
                },
            ],
        }

    def _phase_recovery(self) -> Dict[str, Any]:
        return {
            "phase": "recovery",
            "phase_number": 5,
            "title": "Recovery & Damage Assessment",
            "narrative": (
                "Eradication is complete. All identified sabotage mechanisms have been removed. "
                "System integrity is verified. The focus now shifts to assessing the damage from "
                "data exfiltration and determining appropriate actions."
            ),
            "decisions": [
                {
                    "id": "rec_1",
                    "prompt": "How do you address the exfiltrated data heading to a competitor?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Work with Legal to pursue immediate injunctive relief (temporary restraining order) against Keller to prevent use or disclosure of trade secrets, send a cease-and-desist to the competitor with legal notice that they may be receiving stolen trade secrets, preserve all evidence for potential litigation, assess whether customer notification is required for the PII exposure",
                            "score": 10,
                            "feedback": "Comprehensive legal and business response. Injunctive relief can prevent immediate use of stolen data. Notifying the competitor puts them on legal notice. Customer notification assessment addresses regulatory obligations.",
                            "next_action": "Legal obtains a TRO within 48 hours. Competitor is served with notice. Customer notification assessment identifies 847,000 affected individuals.",
                        },
                        {
                            "id": "b",
                            "text": "Focus on notifying affected customers about the data exposure",
                            "score": 5,
                            "feedback": "Customer notification is important but is only one part of the response. Legal action against Keller and the competitor is equally critical to prevent misuse of trade secrets.",
                            "next_action": "Customer notification is prepared. No legal action is taken against Keller or the competitor.",
                        },
                        {
                            "id": "c",
                            "text": "Contact Keller and offer a settlement in exchange for deleting the data",
                            "score": 3,
                            "feedback": "Negotiating with the subject without legal counsel is inadvisable. There is no guarantee of compliance, and it may complicate future litigation. Let Legal handle all communication.",
                            "next_action": "Direct contact with Keller creates legal complications for future proceedings.",
                        },
                        {
                            "id": "d",
                            "text": "Consider the data lost and focus on improving controls to prevent future incidents",
                            "score": 4,
                            "feedback": "Forward-looking but fails to pursue available legal remedies. Trade secret law provides robust protections if pursued promptly. Accepting the loss without legal action invites future incidents.",
                            "next_action": "No legal action is taken. Keller provides the stolen data to the competitor without consequence.",
                        },
                    ],
                },
            ],
        }

    def _phase_post_incident(self) -> Dict[str, Any]:
        return {
            "phase": "post_incident",
            "phase_number": 6,
            "title": "Post-Incident Review & Insider Threat Program Enhancement",
            "narrative": (
                "The incident is resolved. Legal proceedings are underway. Key findings:\n"
                "  - DLP alerts were generated but daily review introduced a 5-day detection delay\n"
                "  - No insider threat indicators were correlated (resignation + off-hours access + bulk downloads)\n"
                "  - DBA had excessive access beyond job requirements (pricing database, CRM)\n"
                "  - No separation of duties on production database operations\n"
                "  - Off-hours access was not flagged or restricted for departing employees\n"
                "  - Logic bombs were only discovered by chance during the data theft investigation"
            ),
            "decisions": [
                {
                    "id": "post_1",
                    "prompt": "What program improvements do you recommend?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Establish a formal insider threat program with behavioral analytics (UEBA), implement real-time DLP alerting for high-severity violations, enforce least privilege access reviews quarterly, create an automated correlation between HR events (resignation, PIP, termination) and enhanced security monitoring, implement privileged access management (PAM) with session recording for DBA activities, require dual authorization for destructive database operations",
                            "score": 10,
                            "feedback": "Comprehensive insider threat program addressing all identified gaps. UEBA correlation with HR events would have detected this threat days earlier. PAM and dual authorization prevent unilateral sabotage.",
                            "next_action": "Insider threat program charter is approved. UEBA deployment is initiated. PAM solution is budgeted. HR-Security integration process is established.",
                        },
                        {
                            "id": "b",
                            "text": "Implement stricter background checks and increase monitoring of all employees",
                            "score": 3,
                            "feedback": "Background checks help with hiring but do not address current employees who become threats. Blanket monitoring of all employees is resource-intensive and may violate privacy. Targeted, risk-based monitoring is more effective.",
                            "next_action": "Background check process is enhanced. Mass monitoring generates too many alerts to be useful.",
                        },
                        {
                            "id": "c",
                            "text": "Block all personal cloud storage services and restrict USB access",
                            "score": 5,
                            "feedback": "These are reasonable data loss prevention controls but only address specific exfiltration channels. A determined insider will find alternative methods. A holistic insider threat program is needed.",
                            "next_action": "Cloud storage and USB are blocked. DLP coverage improves but insider threat detection capability remains limited.",
                        },
                        {
                            "id": "d",
                            "text": "Require all departing employees to sign enhanced non-compete and non-disclosure agreements",
                            "score": 4,
                            "feedback": "Legal protections are one layer but do not prevent the theft itself. Keller already violated existing policies. Technical controls and monitoring are needed alongside legal measures.",
                            "next_action": "Enhanced NDAs are implemented. They provide stronger legal standing but do not prevent data theft.",
                        },
                    ],
                },
            ],
        }

    def get_max_score(self) -> int:
        total = 0
        for phase in self.get_phases():
            for decision in phase["decisions"]:
                max_choice_score = max(c["score"] for c in decision["choices"])
                total += max_choice_score
        return total

    def get_scoring_rubric(self) -> Dict[str, str]:
        max_score = self.get_max_score()
        return {
            "expert": f"{int(max_score * 0.9)}-{max_score}: Expert-level insider threat response",
            "proficient": f"{int(max_score * 0.7)}-{int(max_score * 0.9) - 1}: Proficient responder",
            "developing": f"{int(max_score * 0.5)}-{int(max_score * 0.7) - 1}: Developing skills",
            "novice": f"Below {int(max_score * 0.5)}: Significant gaps identified",
        }
