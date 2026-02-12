"""
PCI-DSS Compliance Checker - Payment Card Industry Data Security Standard.

Implements automated checks for 15 key PCI-DSS v4.0 requirements.
Maps technical scan findings to PCI-DSS requirements and provides
compliance status with remediation guidance.

Reference: PCI DSS v4.0 (Payment Card Industry Data Security Standard)

Note: Automated technical checks cannot fully verify PCI-DSS compliance.
A Qualified Security Assessor (QSA) is required for formal validation.
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PCIRequirementResult:
    """Result of a single PCI-DSS requirement check."""

    requirement_id: str
    requirement_name: str
    pci_section: str
    description: str
    status: str  # "pass", "fail", "partial", "not_assessed"
    score: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    remediation: str = ""
    compensating_controls: str = ""


@dataclass
class PCIDSSResult:
    """Complete PCI-DSS compliance assessment result."""

    assessment_date: str = ""
    overall_score: float = 0.0
    total_requirements: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    not_assessed: int = 0
    requirement_results: List[PCIRequirementResult] = field(default_factory=list)
    section_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "framework": "PCI-DSS v4.0",
            "assessment_date": self.assessment_date,
            "overall_score": self.overall_score,
            "overall_percentage": round(self.overall_score * 100, 1),
            "total_requirements": self.total_requirements,
            "passed": self.passed,
            "failed": self.failed,
            "partial": self.partial,
            "not_assessed": self.not_assessed,
            "section_scores": self.section_scores,
            "requirements": [
                {
                    "requirement_id": r.requirement_id,
                    "requirement_name": r.requirement_name,
                    "pci_section": r.pci_section,
                    "description": r.description,
                    "status": r.status,
                    "score": r.score,
                    "evidence": r.evidence,
                    "findings": r.findings,
                    "remediation": r.remediation,
                    "compensating_controls": r.compensating_controls,
                }
                for r in self.requirement_results
            ],
        }


# 15 Key PCI-DSS v4.0 Requirements
PCI_DSS_REQUIREMENTS = [
    {
        "id": "Req 1.1",
        "name": "Install and Maintain Network Security Controls",
        "section": "Build and Maintain a Secure Network",
        "description": (
            "Network security controls (firewalls, ACLs) are installed, "
            "configured, and maintained to protect cardholder data."
        ),
    },
    {
        "id": "Req 1.3",
        "name": "Restrict Network Access to Cardholder Data Environment",
        "section": "Build and Maintain a Secure Network",
        "description": (
            "Network access to and from the cardholder data environment "
            "is restricted using network security controls."
        ),
    },
    {
        "id": "Req 2.2",
        "name": "System Components Securely Configured",
        "section": "Build and Maintain a Secure Network",
        "description": (
            "System components are configured and managed securely. "
            "Default passwords changed, unnecessary services disabled."
        ),
    },
    {
        "id": "Req 3.4",
        "name": "Protect Stored Account Data",
        "section": "Protect Account Data",
        "description": (
            "Access to displays of full PAN and ability to copy cardholder "
            "data are restricted. PAN is secured when stored."
        ),
    },
    {
        "id": "Req 4.2",
        "name": "Protect Cardholder Data with Strong Cryptography During Transmission",
        "section": "Protect Account Data",
        "description": (
            "PAN is protected with strong cryptography during transmission "
            "over open, public networks."
        ),
    },
    {
        "id": "Req 5.2",
        "name": "Malicious Software is Detected and Addressed",
        "section": "Maintain a Vulnerability Management Program",
        "description": (
            "Malicious software (malware) is prevented or detected and "
            "addressed on all systems and networks."
        ),
    },
    {
        "id": "Req 5.3",
        "name": "Anti-Malware Mechanisms Are Active",
        "section": "Maintain a Vulnerability Management Program",
        "description": (
            "Anti-malware mechanisms and processes are active, maintained, "
            "and monitored."
        ),
    },
    {
        "id": "Req 6.2",
        "name": "Bespoke and Custom Software Developed Securely",
        "section": "Develop and Maintain Secure Systems",
        "description": (
            "Bespoke and custom software is developed securely, following "
            "secure development practices."
        ),
    },
    {
        "id": "Req 6.4",
        "name": "Public-Facing Web Applications Protected",
        "section": "Develop and Maintain Secure Systems",
        "description": (
            "Public-facing web applications are protected against attacks "
            "through security headers, WAF, or code review."
        ),
    },
    {
        "id": "Req 7.2",
        "name": "Access Appropriately Defined and Assigned",
        "section": "Implement Strong Access Control",
        "description": (
            "Access to system components and data is appropriately defined "
            "and assigned based on job responsibilities."
        ),
    },
    {
        "id": "Req 8.3",
        "name": "Strong Authentication Established",
        "section": "Implement Strong Access Control",
        "description": (
            "Strong authentication for users and administrators is "
            "established and managed."
        ),
    },
    {
        "id": "Req 8.6",
        "name": "Application and System Account Authentication",
        "section": "Implement Strong Access Control",
        "description": (
            "Use of application and system accounts and associated "
            "authentication factors is strictly managed."
        ),
    },
    {
        "id": "Req 10.2",
        "name": "Audit Logs Implemented",
        "section": "Track and Monitor All Access",
        "description": (
            "Audit logs are implemented to support the detection of "
            "anomalies and suspicious activity."
        ),
    },
    {
        "id": "Req 11.3",
        "name": "External and Internal Vulnerabilities Identified and Addressed",
        "section": "Regularly Test Security Systems",
        "description": (
            "External and internal vulnerabilities are regularly identified, "
            "prioritized, and addressed."
        ),
    },
    {
        "id": "Req 12.1",
        "name": "Information Security Policy Established",
        "section": "Maintain an Information Security Policy",
        "description": (
            "A comprehensive information security policy that governs and "
            "provides direction for protection of the entity's information "
            "assets is established and maintained."
        ),
    },
]


class PCIDSSChecker:
    """
    PCI-DSS v4.0 compliance checker.

    Evaluates scan findings against 15 key PCI-DSS requirements
    and provides a compliance scorecard with remediation guidance.

    Example:
        checker = PCIDSSChecker()
        result = checker.assess(scan_data)
        print(f"PCI-DSS Score: {result.overall_score * 100:.1f}%")
        for req in result.requirement_results:
            print(f"  {req.requirement_id}: {req.status}")
    """

    def __init__(self):
        """Initialize the PCI-DSS compliance checker."""
        self.requirements = PCI_DSS_REQUIREMENTS

    def assess(self, scan_data: Dict[str, Any]) -> PCIDSSResult:
        """
        Perform PCI-DSS compliance assessment based on scan data.

        Args:
            scan_data: Dictionary containing scan results with keys:
                - network_scan: NetworkScanResult.to_dict()
                - web_scan: WebScanResult.to_dict()
                - dns_scan: DNSScanResult.to_dict()
                - policies: Optional dict of policy attestations

        Returns:
            PCIDSSResult with compliance assessment.
        """
        result = PCIDSSResult()
        result.assessment_date = datetime.now().isoformat()
        result.total_requirements = len(self.requirements)

        network_data = scan_data.get("network_scan", {})
        web_data = scan_data.get("web_scan", {})
        dns_data = scan_data.get("dns_scan", {})
        policies = scan_data.get("policies", {})

        for req_def in self.requirements:
            req_result = self._check_requirement(
                req_def, network_data, web_data, dns_data, policies
            )
            result.requirement_results.append(req_result)

            if req_result.status == "pass":
                result.passed += 1
            elif req_result.status == "fail":
                result.failed += 1
            elif req_result.status == "partial":
                result.partial += 1
            else:
                result.not_assessed += 1

        # Calculate scores
        total_score = sum(r.score for r in result.requirement_results)
        result.overall_score = round(
            total_score / result.total_requirements, 3
        ) if result.total_requirements > 0 else 0.0

        # Section scores
        sections = {}
        for rr in result.requirement_results:
            sec = rr.pci_section
            if sec not in sections:
                sections[sec] = {"total": 0, "score": 0.0}
            sections[sec]["total"] += 1
            sections[sec]["score"] += rr.score

        for sec, data in sections.items():
            result.section_scores[sec] = round(
                (data["score"] / data["total"]) * 100, 1
            ) if data["total"] > 0 else 0.0

        return result

    def _check_requirement(
        self,
        req_def: Dict,
        network_data: Dict,
        web_data: Dict,
        dns_data: Dict,
        policies: Dict,
    ) -> PCIRequirementResult:
        """
        Check a single PCI-DSS requirement against scan data.

        Args:
            req_def: Requirement definition.
            network_data: Network scan results.
            web_data: Web scan results.
            dns_data: DNS scan results.
            policies: Policy attestation data.

        Returns:
            PCIRequirementResult with check outcome.
        """
        req_result = PCIRequirementResult(
            requirement_id=req_def["id"],
            requirement_name=req_def["name"],
            pci_section=req_def["section"],
            description=req_def["description"],
            status="not_assessed",
            score=0.0,
        )

        req_id = req_def["id"]
        open_ports = network_data.get("open_ports", [])
        net_findings = network_data.get("findings", [])
        header_findings = web_data.get("header_findings", [])
        ssl_info = web_data.get("ssl_info", {})
        web_score = web_data.get("security_score", 0)

        # Req 1.1 - Network Security Controls
        if req_id == "Req 1.1":
            critical_net = [
                f for f in net_findings
                if f.get("severity") in ("critical", "high")
            ]
            if not network_data:
                req_result.status = "not_assessed"
            elif not critical_net:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "No critical network security controls violations found"
                )
            elif len(critical_net) <= 2:
                req_result.status = "partial"
                req_result.score = 0.4
                req_result.findings = [
                    f.get("title", "") for f in critical_net
                ]
            else:
                req_result.status = "fail"
                req_result.score = 0.0
                req_result.findings = [
                    f.get("title", "") for f in critical_net
                ]
            req_result.remediation = (
                "Implement and maintain firewall rules. Document all allowed "
                "network flows. Review firewall rules quarterly."
            )

        # Req 1.3 - Restrict Access to CDE
        elif req_id == "Req 1.3":
            db_exposed = [
                p for p in open_ports
                if p.get("port") in (1433, 3306, 5432, 27017, 9200, 6379)
            ]
            if not network_data:
                req_result.status = "not_assessed"
            elif not db_exposed:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "No database services directly exposed"
                )
            else:
                req_result.status = "fail"
                req_result.score = 0.0
                req_result.findings = [
                    f"Database {p['service']} exposed on port {p['port']}"
                    for p in db_exposed
                ]
            req_result.remediation = (
                "Segment the cardholder data environment. Restrict all "
                "inbound and outbound traffic to only what is required."
            )

        # Req 2.2 - Secure Configuration
        elif req_id == "Req 2.2":
            unnecessary = [
                p for p in open_ports
                if p.get("port") in (21, 23, 135, 139, 5900)
            ]
            if not network_data:
                req_result.status = "not_assessed"
            elif not unnecessary:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "No unnecessary or insecure services detected"
                )
            else:
                req_result.status = "fail"
                req_result.score = 0.0
                req_result.findings = [
                    f"Unnecessary service: {p['service']} (port {p['port']})"
                    for p in unnecessary
                ]
            req_result.remediation = (
                "Remove or disable all unnecessary services. Apply vendor "
                "hardening guides (CIS Benchmarks). Change all default passwords."
            )

        # Req 3.4 - Protect Stored Data
        elif req_id == "Req 3.4":
            if policies.get("data_encryption"):
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append("Data encryption attestation provided")
            else:
                req_result.status = "not_assessed"
                req_result.evidence.append(
                    "Requires manual verification of stored data protection"
                )
            req_result.remediation = (
                "Render PAN unreadable using strong one-way hash functions, "
                "truncation, index tokens, or strong cryptography with "
                "associated key management."
            )

        # Req 4.2 - Encrypt Transmissions
        elif req_id == "Req 4.2":
            if ssl_info:
                expired = ssl_info.get("is_expired", True)
                ssl_findings = ssl_info.get("findings", [])
                weak_cipher = any(
                    "weak" in str(f.get("title", "")).lower()
                    for f in ssl_findings
                )
                if not expired and not weak_cipher:
                    req_result.status = "pass"
                    req_result.score = 1.0
                    req_result.evidence.append(
                        "Valid SSL/TLS with strong cipher suites"
                    )
                elif not expired:
                    req_result.status = "partial"
                    req_result.score = 0.5
                    req_result.evidence.append(
                        "SSL/TLS present but cipher configuration needs improvement"
                    )
                else:
                    req_result.status = "fail"
                    req_result.score = 0.0
                    req_result.findings.append("Expired or invalid SSL certificate")
            elif web_data:
                hsts = any(
                    h.get("header") == "Strict-Transport-Security"
                    and h.get("status") == "present"
                    for h in header_findings
                )
                if hsts:
                    req_result.status = "partial"
                    req_result.score = 0.5
                    req_result.evidence.append("HSTS enabled (SSL details unavailable)")
                else:
                    req_result.status = "fail"
                    req_result.score = 0.0
                    req_result.findings.append("No HSTS and SSL details unavailable")
            else:
                req_result.status = "not_assessed"
            req_result.remediation = (
                "Use strong cryptography (TLS 1.2+) for all transmission "
                "of cardholder data. Disable SSL, TLS 1.0, and TLS 1.1."
            )

        # Req 5.2 - Malware Detection
        elif req_id == "Req 5.2":
            if policies.get("anti_malware"):
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append("Anti-malware attestation provided")
            else:
                req_result.status = "not_assessed"
                req_result.evidence.append(
                    "Requires endpoint verification of anti-malware software"
                )
            req_result.remediation = (
                "Deploy anti-malware on all systems commonly affected by "
                "malware. Ensure automatic updates and periodic scans."
            )

        # Req 5.3 - Active Anti-Malware
        elif req_id == "Req 5.3":
            if policies.get("anti_malware_active"):
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "Active anti-malware monitoring confirmed"
                )
            else:
                req_result.status = "not_assessed"
                req_result.evidence.append(
                    "Requires endpoint verification of active anti-malware"
                )
            req_result.remediation = (
                "Ensure anti-malware solutions cannot be disabled by users. "
                "Implement tamper protection and centralized management."
            )

        # Req 6.2 - Secure Development
        elif req_id == "Req 6.2":
            secure_headers = sum(
                1 for h in header_findings
                if h.get("status") == "present"
                and h.get("header") in (
                    "Content-Security-Policy",
                    "X-Content-Type-Options",
                    "X-Frame-Options",
                )
            )
            if not web_data:
                req_result.status = "not_assessed"
            elif secure_headers >= 3:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "Key security headers implemented (CSP, X-Content-Type, X-Frame)"
                )
            elif secure_headers >= 1:
                req_result.status = "partial"
                req_result.score = 0.4
                req_result.evidence.append(
                    f"{secure_headers}/3 key security headers present"
                )
            else:
                req_result.status = "fail"
                req_result.score = 0.0
                req_result.findings.append("Critical security headers missing")
            req_result.remediation = (
                "Implement secure coding practices per OWASP guidelines. "
                "Deploy all recommended security headers."
            )

        # Req 6.4 - Public-Facing Web App Protection
        elif req_id == "Req 6.4":
            if not web_data:
                req_result.status = "not_assessed"
            elif web_score >= 70:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    f"Web security score: {web_score}/100"
                )
            elif web_score >= 40:
                req_result.status = "partial"
                req_result.score = 0.5
                req_result.evidence.append(
                    f"Web security score: {web_score}/100"
                )
            else:
                req_result.status = "fail"
                req_result.score = 0.0
                req_result.evidence.append(
                    f"Web security score: {web_score}/100"
                )
            req_result.remediation = (
                "Install a web application firewall (WAF) in front of "
                "public-facing web applications. Conduct regular code reviews."
            )
            req_result.compensating_controls = (
                "If a WAF is not feasible, perform annual code reviews "
                "and penetration testing of all public-facing applications."
            )

        # Req 7.2 - Access Management
        elif req_id == "Req 7.2":
            rdp_vnc = [
                p for p in open_ports
                if p.get("port") in (3389, 5900)
            ]
            if not network_data:
                req_result.status = "not_assessed"
            elif not rdp_vnc:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "No unprotected remote access services exposed"
                )
            else:
                req_result.status = "fail"
                req_result.score = 0.0
                req_result.findings = [
                    f"Direct {p['service']} access on port {p['port']}"
                    for p in rdp_vnc
                ]
            req_result.remediation = (
                "Implement role-based access control (RBAC). Restrict "
                "remote access through VPN or zero-trust architecture."
            )

        # Req 8.3 - Strong Authentication
        elif req_id == "Req 8.3":
            auth_indicators = 0
            if any(
                h.get("header") == "Strict-Transport-Security"
                and h.get("status") == "present"
                for h in header_findings
            ):
                auth_indicators += 1
            cookie_findings = web_data.get("cookie_findings", [])
            if not cookie_findings or all(
                c.get("secure") for c in cookie_findings
            ):
                auth_indicators += 1

            if not web_data:
                req_result.status = "not_assessed"
            elif auth_indicators >= 2:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "Secure transport and session management in place"
                )
            elif auth_indicators >= 1:
                req_result.status = "partial"
                req_result.score = 0.5
            else:
                req_result.status = "fail"
                req_result.score = 0.0
            req_result.remediation = (
                "Require multi-factor authentication for all administrative "
                "access. Enforce strong password policies (min 12 chars)."
            )

        # Req 8.6 - Application Account Auth
        elif req_id == "Req 8.6":
            unauth_services = [
                p for p in open_ports
                if p.get("port") in (6379, 9200, 27017)
            ]
            if not network_data:
                req_result.status = "not_assessed"
            elif not unauth_services:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "No services with default unauthenticated access exposed"
                )
            else:
                req_result.status = "fail"
                req_result.score = 0.0
                req_result.findings = [
                    f"Potentially unauthenticated {p['service']} on port {p['port']}"
                    for p in unauth_services
                ]
            req_result.remediation = (
                "Require authentication for all application and system accounts. "
                "Disable default or anonymous access."
            )

        # Req 10.2 - Audit Logging
        elif req_id == "Req 10.2":
            if policies.get("audit_logging"):
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append("Audit logging attestation provided")
            else:
                req_result.status = "not_assessed"
                req_result.evidence.append(
                    "Requires verification of audit logging implementation"
                )
            req_result.remediation = (
                "Implement audit logging for all access to cardholder data. "
                "Record user identification, event type, date/time, "
                "success/failure, origination, and affected data."
            )

        # Req 11.3 - Vulnerability Management
        elif req_id == "Req 11.3":
            total_findings = len(net_findings) + len(
                web_data.get("all_findings", [])
            )
            critical_count = sum(
                1 for f in net_findings
                if f.get("severity") == "critical"
            ) + sum(
                1 for f in web_data.get("all_findings", [])
                if f.get("severity") == "critical"
            )
            if total_findings == 0 and not (network_data or web_data):
                req_result.status = "not_assessed"
            elif critical_count == 0:
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    f"No critical vulnerabilities. Total findings: {total_findings}"
                )
            elif critical_count <= 2:
                req_result.status = "partial"
                req_result.score = 0.3
                req_result.evidence.append(
                    f"{critical_count} critical findings require attention"
                )
            else:
                req_result.status = "fail"
                req_result.score = 0.0
                req_result.evidence.append(
                    f"{critical_count} critical vulnerabilities detected"
                )
            req_result.remediation = (
                "Conduct quarterly external vulnerability scans by an "
                "Approved Scanning Vendor (ASV). Perform internal scans "
                "quarterly and after significant changes."
            )

        # Req 12.1 - Security Policy
        elif req_id == "Req 12.1":
            if policies.get("security_policy"):
                req_result.status = "pass"
                req_result.score = 1.0
                req_result.evidence.append(
                    "Information security policy attestation provided"
                )
            else:
                req_result.status = "not_assessed"
                req_result.evidence.append(
                    "Requires verification of documented security policy"
                )
            req_result.remediation = (
                "Establish and publish an information security policy. "
                "Review and update at least annually. Ensure all personnel "
                "acknowledge the policy."
            )

        return req_result

    def get_requirement_list(self) -> List[Dict]:
        """Get the list of all 15 PCI-DSS requirements being checked."""
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "section": r["section"],
                "description": r["description"],
            }
            for r in self.requirements
        ]
