"""
Phishing Campaign Scenario
============================

Simulates a targeted spear-phishing campaign that successfully compromises
multiple employee credentials and is used as a precursor for business
email compromise (BEC) and internal lateral phishing.

Attack narrative:
    A threat actor conducts reconnaissance on the organization via LinkedIn
    and public filings, then launches a targeted phishing campaign impersonating
    the CFO. Emails direct recipients to a convincing credential harvesting page.
    Multiple employees submit credentials, and the attacker uses them to access
    email, initiate wire transfers, and launch internal phishing.
"""

from typing import Dict, List, Any


class PhishingScenario:
    """Phishing campaign incident response scenario with decision tree."""

    def __init__(self):
        self.name = "phishing"
        self.title = "Targeted Spear-Phishing & Business Email Compromise"
        self.description = (
            "The security team has identified a coordinated spear-phishing campaign "
            "targeting senior staff. Five employees in Finance and Procurement reported "
            "receiving emails appearing to be from the CFO requesting urgent review of "
            "a 'compensation adjustment document.' Two employees confirmed they clicked "
            "the link and entered their credentials on a fake SSO portal. One of the "
            "compromised accounts (VP of Procurement) has already been used to send "
            "internal emails requesting a $340,000 wire transfer to a vendor that "
            "does not match existing vendor records."
        )
        self.default_severity = "high"
        self.estimated_duration_minutes = 35
        self.category = "phishing"
        self.affected_systems = [
            "Email gateway (O365 Exchange Online)",
            "SSO portal (Okta)",
            "VPN gateway (compromised credentials)",
            "Finance ERP system (attempted unauthorized access)",
            "Procurement portal",
        ]
        self.initial_iocs = [
            {"type": "domain", "value": "sso-company-auth.com", "context": "Credential harvesting domain"},
            {"type": "ip", "value": "104.21.45.67", "context": "Hosting IP for phishing page"},
            {"type": "email_sender", "value": "cfo-notifications@company-secure.net", "context": "Spoofed sender domain"},
            {"type": "url", "value": "https://sso-company-auth.com/login?ref=comp-review", "context": "Credential harvesting URL"},
            {"type": "email_subject", "value": "URGENT: Q4 Compensation Adjustment - Action Required", "context": "Phishing email subject line"},
            {"type": "ip", "value": "196.45.78.12", "context": "Attacker login source IP (VPN access)"},
            {"type": "account", "value": "m.chen@company.com", "context": "Compromised VP Procurement account"},
            {"type": "account", "value": "j.rodriguez@company.com", "context": "Compromised Senior Accountant account"},
        ]
        self.attack_vector = "Spear-phishing email -> credential harvesting -> account takeover -> BEC wire fraud attempt"

    def get_phases(self) -> List[Dict[str, Any]]:
        """Return all scenario phases."""
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
            "title": "Phishing Detection & Validation",
            "narrative": (
                "At 14:22, a vigilant employee in Finance forwarded a suspicious email to the "
                "security team's phishing reporting mailbox (phishing@company.com). The email "
                "appeared to be from the CFO but the sender domain was 'company-secure.net' "
                "instead of 'company.com'. At 14:35, a second report arrived. By 14:50, the "
                "email gateway retroactive scan identified 47 similar emails delivered to "
                "employees across Finance, Procurement, and Executive departments.\n\n"
                "Two employees have confirmed they entered their credentials on the linked page. "
                "The page was a pixel-perfect clone of the corporate Okta SSO portal."
            ),
            "decisions": [
                {
                    "id": "det_1",
                    "prompt": "What is your first priority upon confirming this is a phishing campaign?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Identify all recipients of the phishing emails via email gateway logs, determine who clicked the link via proxy logs, and identify who submitted credentials by correlating authentication logs for unusual login activity",
                            "score": 10,
                            "feedback": "Correct prioritization. You need to determine the blast radius: how many received, how many clicked, and how many are compromised. This drives all subsequent actions.",
                            "next_action": "Analysis reveals: 47 emails delivered, 12 users clicked the link, 2 confirmed credential submissions, suspicious logins detected for both compromised accounts.",
                        },
                        {
                            "id": "b",
                            "text": "Block the phishing domain and URL at the web proxy and email gateway immediately",
                            "score": 7,
                            "feedback": "Good defensive action but it should happen in parallel with scope assessment, not instead of it. Blocking prevents further clicks but does not address already-compromised accounts.",
                            "next_action": "Phishing URL is blocked. New clicks are prevented. Already-compromised accounts remain in attacker control.",
                        },
                        {
                            "id": "c",
                            "text": "Send an all-company email warning about the phishing campaign",
                            "score": 4,
                            "feedback": "Awareness is important but premature. First assess scope and contain compromised accounts. An all-company email may also tip off the attacker if they are monitoring compromised mailboxes.",
                            "next_action": "Warning email is sent. The attacker, who is monitoring the compromised VP account, sees the warning and accelerates their wire transfer attempt.",
                        },
                        {
                            "id": "d",
                            "text": "Contact the phishing domain registrar to take down the credential harvesting site",
                            "score": 3,
                            "feedback": "Domain takedown is a valid long-term action but takes hours to days. It does not address the immediate threat of compromised credentials being actively misused.",
                            "next_action": "Takedown request is submitted. Domain remains active for 48 hours while the registrar processes the request.",
                        },
                    ],
                },
            ],
        }

    def _phase_triage(self) -> Dict[str, Any]:
        return {
            "phase": "triage",
            "phase_number": 2,
            "title": "Compromise Assessment & Impact Scoping",
            "narrative": (
                "Your analysis has identified:\n"
                "  - 2 confirmed compromised accounts: m.chen (VP Procurement) and j.rodriguez (Senior Accountant)\n"
                "  - m.chen's account was accessed from IP 196.45.78.12 (geolocated to Lagos, Nigeria) at 15:03\n"
                "  - The attacker used m.chen's account to send 3 internal emails:\n"
                "    1. Wire transfer request for $340,000 to 'Global Supply Partners' (unknown vendor)\n"
                "    2. Email to HR requesting employee SSN data for 'benefits audit'\n"
                "    3. Internal phishing email to 8 Procurement team members with a new malicious link\n"
                "  - j.rodriguez's account shows VPN login from the same IP at 15:15\n"
                "  - 10 additional users clicked the link but no credential submission was confirmed"
            ),
            "decisions": [
                {
                    "id": "tri_1",
                    "prompt": "How do you assess the severity of this incident?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Escalate to Critical: Active account takeover with attempted wire fraud ($340K), attempted PII theft (SSN request), and secondary internal phishing campaign expanding the attack surface",
                            "score": 10,
                            "feedback": "Correct assessment. The combination of financial fraud, PII exposure risk, and active expansion of the campaign warrants Critical severity.",
                            "next_action": "Severity is escalated to Critical. Full IR team is engaged. Legal and Finance leadership are notified about the wire fraud attempt.",
                        },
                        {
                            "id": "b",
                            "text": "Maintain at High: Only 2 accounts are confirmed compromised",
                            "score": 4,
                            "feedback": "Underestimates the impact. The number of compromised accounts is less important than what the attacker is doing with them. Attempted $340K wire fraud and PII theft demand Critical classification.",
                            "next_action": "Severity remains High. Resource allocation may be insufficient for the financial fraud response.",
                        },
                        {
                            "id": "c",
                            "text": "Medium: Phishing campaigns are common and this one has been identified quickly",
                            "score": 1,
                            "feedback": "Dangerously low assessment. This is not just a phishing campaign - it has progressed to active account takeover, financial fraud, and data theft attempts. Quick detection does not reduce the severity of ongoing attacker actions.",
                            "next_action": "Inadequate response. The wire transfer request is processed before Finance can be warned.",
                        },
                        {
                            "id": "d",
                            "text": "Critical but only because of the wire transfer attempt; the phishing itself is routine",
                            "score": 6,
                            "feedback": "The wire transfer is the most urgent element but dismissing the broader campaign misses the PII exposure attempt and the secondary internal phishing. All elements contribute to the severity.",
                            "next_action": "Focus is placed on the wire transfer. The HR SSN request is not flagged with urgency.",
                        },
                    ],
                },
            ],
        }

    def _phase_containment(self) -> Dict[str, Any]:
        return {
            "phase": "containment",
            "phase_number": 3,
            "title": "Account Containment & Fraud Prevention",
            "narrative": (
                "Severity is Critical. The wire transfer request was sent to accounts-payable@company.com "
                "at 15:10. Standard wire transfer processing takes 2-4 hours. Current time is 15:45. "
                "The attacker is actively using the compromised accounts."
            ),
            "decisions": [
                {
                    "id": "con_1",
                    "prompt": "What is your immediate containment priority?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Simultaneously: (1) Force password reset and revoke all active sessions for both compromised accounts, (2) Contact Accounts Payable directly (phone, not email) to halt the wire transfer, (3) Contact HR to disregard the SSN request, (4) Block the internal phishing URLs, (5) Enable conditional access policies to block logins from suspicious geolocations",
                            "score": 10,
                            "feedback": "Comprehensive parallel containment. Using phone instead of email for fraud prevention is critical since the attacker controls email accounts. Revoking sessions ensures the attacker is immediately locked out.",
                            "next_action": "Accounts are locked. Wire transfer is halted before processing. HR confirms no data was sent. Internal phishing links are blocked.",
                        },
                        {
                            "id": "b",
                            "text": "Reset passwords for the two compromised accounts and send an email to Accounts Payable to hold the wire transfer",
                            "score": 4,
                            "feedback": "Password reset is correct but emailing AP is risky - the attacker may intercept or the email may not be seen in time. Phone contact is essential for urgent fraud prevention. Also misses session revocation.",
                            "next_action": "Passwords are reset but existing sessions may remain active. Email to AP sits in queue.",
                        },
                        {
                            "id": "c",
                            "text": "Disable both accounts entirely and investigate before taking further action",
                            "score": 6,
                            "feedback": "Account disablement stops the attacker but disabling a VP's account without warning causes disruption. More importantly, you must also address the in-flight wire transfer urgently.",
                            "next_action": "Accounts are disabled. VP cannot work. Wire transfer status is unknown.",
                        },
                        {
                            "id": "d",
                            "text": "Focus on blocking all phishing indicators first, then address the compromised accounts",
                            "score": 3,
                            "feedback": "Wrong priority order. The compromised accounts are being actively used for fraud RIGHT NOW. Blocking phishing indicators prevents future clicks but does not stop the active financial fraud.",
                            "next_action": "Phishing indicators are blocked. The wire transfer continues to process.",
                        },
                    ],
                },
            ],
        }

    def _phase_eradication(self) -> Dict[str, Any]:
        return {
            "phase": "eradication",
            "phase_number": 4,
            "title": "Threat Eradication & Access Remediation",
            "narrative": (
                "Containment is successful. Wire transfer was halted. No SSN data was disclosed. "
                "Internal phishing links are blocked. Both compromised accounts are secured. Now "
                "you need to ensure the attacker has no remaining access and that all phishing "
                "artifacts are removed."
            ),
            "decisions": [
                {
                    "id": "era_1",
                    "prompt": "What eradication steps do you take?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Purge all phishing emails from all mailboxes (original campaign + internal phishing), review and revoke any OAuth app consent or mail forwarding rules created by the attacker, force MFA re-enrollment for compromised users, review all emails sent from compromised accounts during the compromise window, check for any data exfiltration from email or connected systems",
                            "score": 10,
                            "feedback": "Thorough eradication. Checking for mail rules and OAuth consent is critical - attackers often set up persistent access through mail forwarding rules or app permissions that survive password resets.",
                            "next_action": "Email purge removes 47 external phishing emails and 8 internal phishing emails. A mail forwarding rule to an external address is found on m.chen's account and removed.",
                        },
                        {
                            "id": "b",
                            "text": "Delete the phishing emails from mailboxes and consider the threat removed",
                            "score": 4,
                            "feedback": "Email deletion is necessary but insufficient. Attackers commonly create persistence through mail rules, OAuth apps, or delegated access. These must be audited and removed.",
                            "next_action": "Phishing emails are purged. The mail forwarding rule on m.chen's account continues to exfiltrate emails.",
                        },
                        {
                            "id": "c",
                            "text": "Reset passwords for all 47 recipients as a precaution",
                            "score": 6,
                            "feedback": "Conservative approach. Resetting all 47 is disruptive when only 2 are confirmed compromised. However, it provides additional assurance. Combine with session revocation and mail rule auditing.",
                            "next_action": "All 47 users have forced password resets. Some users are confused and flood the helpdesk.",
                        },
                        {
                            "id": "d",
                            "text": "Block the sender domains and IPs at the email gateway and consider eradication complete",
                            "score": 3,
                            "feedback": "Blocking indicators is a prevention measure, not eradication. It does not address the existing compromise footprint (forwarding rules, sent emails, potential data exfiltration).",
                            "next_action": "Sender infrastructure is blocked. Existing compromise artifacts remain in the environment.",
                        },
                    ],
                },
            ],
        }

    def _phase_recovery(self) -> Dict[str, Any]:
        return {
            "phase": "recovery",
            "phase_number": 5,
            "title": "Account Recovery & Operational Restoration",
            "narrative": (
                "Eradication is complete. All phishing emails are purged, malicious mail rules removed, "
                "and compromised account access is fully remediated. The wire transfer was prevented. "
                "Now you need to restore normal operations and ensure no residual risk."
            ),
            "decisions": [
                {
                    "id": "rec_1",
                    "prompt": "How do you restore the compromised users to normal operations?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Re-enable accounts with new strong passwords and MFA hardware tokens (replacing software MFA), conduct a brief security debrief with each compromised user, verify no unauthorized changes to their email/calendars/contacts, and implement enhanced mailbox audit logging for 90 days",
                            "score": 10,
                            "feedback": "Secure recovery process. Hardware MFA tokens are more resistant to phishing than software-based MFA. User debrief helps identify any unreported activity. Enhanced monitoring catches residual issues.",
                            "next_action": "Users are restored with hardware MFA. Enhanced monitoring is configured. Users report no additional suspicious activity.",
                        },
                        {
                            "id": "b",
                            "text": "Re-enable accounts with the same MFA method and inform users to be more careful",
                            "score": 3,
                            "feedback": "Does not address the MFA gap. If the attacker bypassed or did not face MFA during the initial compromise, the same weakness remains. Upgrading MFA strength is essential.",
                            "next_action": "Accounts are restored. Same MFA method that was ineffective against the phishing attack remains in place.",
                        },
                        {
                            "id": "c",
                            "text": "Create entirely new accounts for the compromised users and migrate their data",
                            "score": 4,
                            "feedback": "Excessive for this scenario. Account migration is disruptive and unnecessary when proper eradication (password reset, session revocation, rule cleanup) has been performed.",
                            "next_action": "New accounts are created. Users lose access to historical email and face significant workflow disruption.",
                        },
                        {
                            "id": "d",
                            "text": "Re-enable accounts and immediately send a test phishing email to the compromised users",
                            "score": 2,
                            "feedback": "Testing users immediately after an incident is punitive and counterproductive. Phishing awareness training should be supportive and scheduled appropriately, not used as an immediate test.",
                            "next_action": "Users feel targeted and trust in the security team erodes.",
                        },
                    ],
                },
            ],
        }

    def _phase_post_incident(self) -> Dict[str, Any]:
        return {
            "phase": "post_incident",
            "phase_number": 6,
            "title": "Post-Incident Review & Control Enhancement",
            "narrative": (
                "The incident is resolved. Total timeline: 4 hours from detection to full containment. "
                "Financial loss: $0 (wire transfer prevented). Data loss: None confirmed. "
                "Key observations:\n"
                "  - Phishing emails bypassed DMARC checks (sender used a lookalike domain, not spoofing)\n"
                "  - MFA was SMS-based and not phishing-resistant\n"
                "  - No conditional access policies for geographic restrictions\n"
                "  - Wire transfer approval process relied on email authorization only\n"
                "  - Employee phishing reporting was effective (first report within 12 minutes)"
            ),
            "decisions": [
                {
                    "id": "post_1",
                    "prompt": "What are your top recommendations?",
                    "choices": [
                        {
                            "id": "a",
                            "text": "Deploy phishing-resistant MFA (FIDO2/WebAuthn) for all users, implement lookalike domain monitoring and blocking, require multi-party authorization with out-of-band verification for wire transfers over $10K, deploy a phishing-aware web proxy with real-time URL analysis, recognize and reward the employee who reported the phishing",
                            "score": 10,
                            "feedback": "Excellent recommendations addressing every identified gap. Recognizing the reporting employee reinforces the security culture that detected this incident early.",
                            "next_action": "Improvement roadmap is approved. FIDO2 deployment is prioritized. Wire transfer process is updated. Reporting employee receives a security champion award.",
                        },
                        {
                            "id": "b",
                            "text": "Mandatory phishing awareness training for all employees with quarterly simulated phishing tests",
                            "score": 5,
                            "feedback": "Training helps but does not address the technical control gaps. Even well-trained users can be caught by sophisticated spear-phishing. Technical controls must complement training.",
                            "next_action": "Training is implemented. Technical gaps remain.",
                        },
                        {
                            "id": "c",
                            "text": "Block all external emails that contain links or attachments",
                            "score": 1,
                            "feedback": "Catastrophically restrictive. This would cripple business communications. Security controls must enable business operations, not prevent them entirely.",
                            "next_action": "Policy is proposed. Business leadership immediately rejects it as unworkable.",
                        },
                        {
                            "id": "d",
                            "text": "Implement email banners warning users about external emails and deploy an email link rewriting service",
                            "score": 6,
                            "feedback": "Good measures that add friction and visibility, but they do not address the MFA weakness, the wire transfer process gap, or the need for lookalike domain monitoring.",
                            "next_action": "External email banners are deployed. Link rewriting service is implemented. Core gaps remain.",
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
            "expert": f"{int(max_score * 0.9)}-{max_score}: Expert-level phishing response",
            "proficient": f"{int(max_score * 0.7)}-{int(max_score * 0.9) - 1}: Proficient responder",
            "developing": f"{int(max_score * 0.5)}-{int(max_score * 0.7) - 1}: Developing skills",
            "novice": f"Below {int(max_score * 0.5)}: Significant gaps identified",
        }
