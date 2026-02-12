"""
ISO 27001 Compliance Checker - Annex A Controls Assessment.

Implements automated checks for 20 key ISO 27001:2022 Annex A controls
based on scan findings. Maps technical security findings to specific
control requirements and provides pass/fail/partial status with
remediation guidance.

Reference: ISO/IEC 27001:2022 Information Security Management Systems
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ControlResult:
    """Result of a single ISO 27001 control check."""

    control_id: str
    control_name: str
    category: str
    description: str
    status: str  # "pass", "fail", "partial", "not_assessed"
    score: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    remediation: str = ""
    priority: str = "medium"  # "critical", "high", "medium", "low"


@dataclass
class ISO27001Result:
    """Complete ISO 27001 compliance assessment result."""

    assessment_date: str = ""
    overall_score: float = 0.0
    total_controls: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    not_assessed: int = 0
    control_results: List[ControlResult] = field(default_factory=list)
    category_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "framework": "ISO 27001:2022",
            "assessment_date": self.assessment_date,
            "overall_score": self.overall_score,
            "overall_percentage": round(self.overall_score * 100, 1),
            "total_controls": self.total_controls,
            "passed": self.passed,
            "failed": self.failed,
            "partial": self.partial,
            "not_assessed": self.not_assessed,
            "category_scores": self.category_scores,
            "controls": [
                {
                    "control_id": c.control_id,
                    "control_name": c.control_name,
                    "category": c.category,
                    "description": c.description,
                    "status": c.status,
                    "score": c.score,
                    "evidence": c.evidence,
                    "findings": c.findings,
                    "remediation": c.remediation,
                    "priority": c.priority,
                }
                for c in self.control_results
            ],
        }


# 20 Key ISO 27001:2022 Annex A Controls
ISO27001_CONTROLS = [
    {
        "id": "A.5.1",
        "name": "Policies for Information Security",
        "category": "Organizational Controls",
        "description": (
            "A set of policies for information security shall be defined, "
            "approved by management, published and communicated."
        ),
        "check_type": "policy",
        "check_keys": ["security_policy"],
        "priority": "high",
    },
    {
        "id": "A.5.15",
        "name": "Access Control",
        "category": "Organizational Controls",
        "description": (
            "Rules to control physical and logical access to information "
            "and information processing facilities shall be established."
        ),
        "check_type": "network",
        "check_keys": ["access_control", "authentication"],
        "priority": "critical",
    },
    {
        "id": "A.5.23",
        "name": "Information Security for Cloud Services",
        "category": "Organizational Controls",
        "description": (
            "Processes for acquisition, use, management and exit from cloud "
            "services shall be established."
        ),
        "check_type": "policy",
        "check_keys": ["cloud_security"],
        "priority": "high",
    },
    {
        "id": "A.6.1",
        "name": "Screening",
        "category": "People Controls",
        "description": (
            "Background verification checks on candidates shall be carried out "
            "prior to joining the organization."
        ),
        "check_type": "policy",
        "check_keys": ["personnel_screening"],
        "priority": "medium",
    },
    {
        "id": "A.6.3",
        "name": "Information Security Awareness and Training",
        "category": "People Controls",
        "description": (
            "Personnel shall receive appropriate security awareness education, "
            "training and regular updates."
        ),
        "check_type": "policy",
        "check_keys": ["security_training"],
        "priority": "high",
    },
    {
        "id": "A.7.1",
        "name": "Physical Security Perimeters",
        "category": "Physical Controls",
        "description": (
            "Security perimeters shall be defined and used to protect areas "
            "containing information and information processing facilities."
        ),
        "check_type": "policy",
        "check_keys": ["physical_security"],
        "priority": "medium",
    },
    {
        "id": "A.7.4",
        "name": "Physical Security Monitoring",
        "category": "Physical Controls",
        "description": (
            "Premises shall be continuously monitored for unauthorized "
            "physical access."
        ),
        "check_type": "policy",
        "check_keys": ["physical_monitoring"],
        "priority": "medium",
    },
    {
        "id": "A.8.1",
        "name": "User Endpoint Devices",
        "category": "Technological Controls",
        "description": (
            "Information stored on, processed by or accessible via user "
            "endpoint devices shall be protected."
        ),
        "check_type": "network",
        "check_keys": ["endpoint_protection"],
        "priority": "high",
    },
    {
        "id": "A.8.3",
        "name": "Information Access Restriction",
        "category": "Technological Controls",
        "description": (
            "Access to information and application system functions shall "
            "be restricted per access control policy."
        ),
        "check_type": "network",
        "check_keys": ["access_restriction", "exposed_services"],
        "priority": "critical",
    },
    {
        "id": "A.8.5",
        "name": "Secure Authentication",
        "category": "Technological Controls",
        "description": (
            "Secure authentication technologies and procedures shall be "
            "established based on access control policy."
        ),
        "check_type": "web",
        "check_keys": ["authentication_headers", "session_security"],
        "priority": "critical",
    },
    {
        "id": "A.8.7",
        "name": "Protection Against Malware",
        "category": "Technological Controls",
        "description": (
            "Protection against malware shall be implemented and supported "
            "by appropriate user awareness."
        ),
        "check_type": "policy",
        "check_keys": ["malware_protection"],
        "priority": "high",
    },
    {
        "id": "A.8.9",
        "name": "Configuration Management",
        "category": "Technological Controls",
        "description": (
            "Configurations, including security configurations, of hardware, "
            "software, services and networks shall be managed."
        ),
        "check_type": "network",
        "check_keys": ["configuration_management", "hardening"],
        "priority": "high",
    },
    {
        "id": "A.8.12",
        "name": "Data Leakage Prevention",
        "category": "Technological Controls",
        "description": (
            "Data leakage prevention measures shall be applied to systems, "
            "networks and devices containing sensitive information."
        ),
        "check_type": "web",
        "check_keys": ["data_leakage", "information_disclosure"],
        "priority": "high",
    },
    {
        "id": "A.8.15",
        "name": "Logging",
        "category": "Technological Controls",
        "description": (
            "Logs that record activities, exceptions, faults and security "
            "events shall be produced, stored, protected and analyzed."
        ),
        "check_type": "policy",
        "check_keys": ["logging", "monitoring"],
        "priority": "high",
    },
    {
        "id": "A.8.20",
        "name": "Network Security",
        "category": "Technological Controls",
        "description": (
            "Networks and network devices shall be secured, managed and "
            "controlled to protect information in systems and applications."
        ),
        "check_type": "network",
        "check_keys": ["network_security", "port_exposure"],
        "priority": "critical",
    },
    {
        "id": "A.8.21",
        "name": "Security of Network Services",
        "category": "Technological Controls",
        "description": (
            "Security mechanisms, service levels and service requirements "
            "of network services shall be identified and implemented."
        ),
        "check_type": "network",
        "check_keys": ["service_security", "banner_exposure"],
        "priority": "high",
    },
    {
        "id": "A.8.23",
        "name": "Web Filtering",
        "category": "Technological Controls",
        "description": (
            "Access to external websites shall be managed to reduce "
            "exposure to malicious content."
        ),
        "check_type": "web",
        "check_keys": ["web_filtering", "content_security_policy"],
        "priority": "medium",
    },
    {
        "id": "A.8.24",
        "name": "Use of Cryptography",
        "category": "Technological Controls",
        "description": (
            "Rules for the effective use of cryptography, including key "
            "management, shall be defined and implemented."
        ),
        "check_type": "web",
        "check_keys": ["ssl_tls", "encryption"],
        "priority": "critical",
    },
    {
        "id": "A.8.26",
        "name": "Application Security Requirements",
        "category": "Technological Controls",
        "description": (
            "Information security requirements shall be identified, "
            "specified and approved when developing or acquiring applications."
        ),
        "check_type": "web",
        "check_keys": ["security_headers", "application_security"],
        "priority": "high",
    },
    {
        "id": "A.8.28",
        "name": "Secure Coding",
        "category": "Technological Controls",
        "description": (
            "Secure coding principles shall be applied to software development."
        ),
        "check_type": "web",
        "check_keys": ["secure_coding", "xss_protection", "cors"],
        "priority": "high",
    },
]


class ISO27001Checker:
    """
    ISO 27001:2022 Annex A compliance checker.

    Evaluates scan findings against 20 key ISO 27001 controls and
    provides a compliance scorecard with remediation guidance.

    Attributes:
        controls: List of ISO 27001 control definitions.

    Example:
        checker = ISO27001Checker()
        result = checker.assess(scan_data)
        print(f"Overall Score: {result.overall_score * 100:.1f}%")
        for control in result.control_results:
            print(f"  {control.control_id}: {control.status}")
    """

    def __init__(self):
        """Initialize the ISO 27001 compliance checker."""
        self.controls = ISO27001_CONTROLS

    def assess(self, scan_data: Dict[str, Any]) -> ISO27001Result:
        """
        Perform ISO 27001 compliance assessment based on scan data.

        Evaluates each of the 20 key controls against findings from
        network, web, and DNS scans.

        Args:
            scan_data: Dictionary containing scan results with keys:
                - network_scan: NetworkScanResult.to_dict()
                - web_scan: WebScanResult.to_dict()
                - dns_scan: DNSScanResult.to_dict()
                - policies: Optional dict of policy attestations

        Returns:
            ISO27001Result with compliance assessment.
        """
        result = ISO27001Result()
        result.assessment_date = datetime.now().isoformat()
        result.total_controls = len(self.controls)

        network_data = scan_data.get("network_scan", {})
        web_data = scan_data.get("web_scan", {})
        dns_data = scan_data.get("dns_scan", {})
        policies = scan_data.get("policies", {})

        for control_def in self.controls:
            control_result = self._check_control(
                control_def, network_data, web_data, dns_data, policies
            )
            result.control_results.append(control_result)

            if control_result.status == "pass":
                result.passed += 1
            elif control_result.status == "fail":
                result.failed += 1
            elif control_result.status == "partial":
                result.partial += 1
            else:
                result.not_assessed += 1

        # Calculate overall score
        total_score = sum(c.score for c in result.control_results)
        result.overall_score = round(
            total_score / result.total_controls, 3
        ) if result.total_controls > 0 else 0.0

        # Calculate category scores
        categories = {}
        for cr in result.control_results:
            if cr.category not in categories:
                categories[cr.category] = {"total": 0, "score": 0.0}
            categories[cr.category]["total"] += 1
            categories[cr.category]["score"] += cr.score

        for cat, data in categories.items():
            result.category_scores[cat] = round(
                (data["score"] / data["total"]) * 100, 1
            ) if data["total"] > 0 else 0.0

        return result

    def _check_control(
        self,
        control_def: Dict,
        network_data: Dict,
        web_data: Dict,
        dns_data: Dict,
        policies: Dict,
    ) -> ControlResult:
        """
        Check a single ISO 27001 control against scan data.

        Args:
            control_def: Control definition from ISO27001_CONTROLS.
            network_data: Network scan results.
            web_data: Web scan results.
            dns_data: DNS scan results.
            policies: Policy attestation data.

        Returns:
            ControlResult with check outcome.
        """
        control_result = ControlResult(
            control_id=control_def["id"],
            control_name=control_def["name"],
            category=control_def["category"],
            description=control_def["description"],
            status="not_assessed",
            score=0.0,
            priority=control_def["priority"],
        )

        check_type = control_def["check_type"]
        check_keys = control_def["check_keys"]

        if check_type == "network":
            self._check_network_control(
                control_result, control_def, network_data
            )
        elif check_type == "web":
            self._check_web_control(
                control_result, control_def, web_data
            )
        elif check_type == "dns":
            self._check_dns_control(
                control_result, control_def, dns_data
            )
        elif check_type == "policy":
            self._check_policy_control(
                control_result, control_def, policies
            )

        return control_result

    def _check_network_control(
        self,
        result: ControlResult,
        control_def: Dict,
        network_data: Dict,
    ):
        """Evaluate a network-related control."""
        check_keys = control_def["check_keys"]
        open_ports = network_data.get("open_ports", [])
        findings = network_data.get("findings", [])

        if not network_data:
            result.status = "not_assessed"
            result.evidence.append("No network scan data available")
            return

        # A.5.15 - Access Control
        if control_def["id"] == "A.5.15":
            high_risk_open = [
                p for p in open_ports
                if p.get("risk_level") in ("high", "critical")
            ]
            if not high_risk_open:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "No high-risk services exposed to the network"
                )
            elif len(high_risk_open) <= 2:
                result.status = "partial"
                result.score = 0.5
                result.evidence.append(
                    f"{len(high_risk_open)} high-risk service(s) exposed"
                )
                result.findings = [
                    f"Port {p['port']}/{p['service']}" for p in high_risk_open
                ]
            else:
                result.status = "fail"
                result.score = 0.0
                result.evidence.append(
                    f"{len(high_risk_open)} high-risk services exposed"
                )
                result.findings = [
                    f"Port {p['port']}/{p['service']}" for p in high_risk_open
                ]
            result.remediation = (
                "Implement network segmentation and restrict access to "
                "high-risk services. Use firewalls and ACLs to limit exposure."
            )

        # A.8.3 - Information Access Restriction
        elif control_def["id"] == "A.8.3":
            db_ports = [
                p for p in open_ports
                if p.get("port") in (1433, 3306, 5432, 27017, 9200, 6379)
            ]
            if not db_ports:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "No database services directly exposed"
                )
            else:
                result.status = "fail"
                result.score = 0.0
                result.findings = [
                    f"Database {p['service']} on port {p['port']}"
                    for p in db_ports
                ]
                result.evidence.append(
                    f"{len(db_ports)} database(s) directly accessible"
                )
            result.remediation = (
                "Database services must not be directly accessible. "
                "Implement network segmentation and restrict access "
                "to application servers only."
            )

        # A.8.1 - User Endpoint Devices
        elif control_def["id"] == "A.8.1":
            remote_access = [
                p for p in open_ports
                if p.get("port") in (3389, 5900, 22)
            ]
            if not remote_access:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "No direct remote access services exposed"
                )
            elif len(remote_access) == 1 and remote_access[0].get("port") == 22:
                result.status = "partial"
                result.score = 0.7
                result.evidence.append(
                    "SSH is exposed (acceptable with proper hardening)"
                )
            else:
                result.status = "fail"
                result.score = 0.2
                result.findings = [
                    f"{p['service']} on port {p['port']}" for p in remote_access
                ]
            result.remediation = (
                "Require VPN for all remote access. Disable RDP and VNC "
                "direct exposure. Use SSH with key-based authentication."
            )

        # A.8.9 - Configuration Management
        elif control_def["id"] == "A.8.9":
            total_ports = network_data.get("total_ports_scanned", 0)
            open_count = len(open_ports)
            if total_ports > 0:
                open_ratio = open_count / total_ports
                if open_ratio < 0.02:
                    result.status = "pass"
                    result.score = 1.0
                    result.evidence.append(
                        f"Low port exposure ratio: {open_count}/{total_ports}"
                    )
                elif open_ratio < 0.05:
                    result.status = "partial"
                    result.score = 0.6
                    result.evidence.append(
                        f"Moderate port exposure: {open_count}/{total_ports}"
                    )
                else:
                    result.status = "fail"
                    result.score = 0.2
                    result.evidence.append(
                        f"High port exposure: {open_count}/{total_ports}"
                    )
            result.remediation = (
                "Implement system hardening standards. Disable unnecessary "
                "services. Apply CIS benchmarks for operating systems."
            )

        # A.8.20 - Network Security
        elif control_def["id"] == "A.8.20":
            critical_findings = [
                f for f in findings
                if f.get("severity") in ("critical", "high")
            ]
            if not critical_findings:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "No critical network security findings"
                )
            elif len(critical_findings) <= 2:
                result.status = "partial"
                result.score = 0.4
                result.findings = [f.get("title", "") for f in critical_findings]
            else:
                result.status = "fail"
                result.score = 0.0
                result.findings = [f.get("title", "") for f in critical_findings]
            result.remediation = (
                "Address all critical and high-severity network findings. "
                "Implement network segmentation, firewall rules, and IDS/IPS."
            )

        # A.8.21 - Security of Network Services
        elif control_def["id"] == "A.8.21":
            banner_exposed = [
                p for p in open_ports if p.get("banner")
            ]
            if not banner_exposed:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "No service banners exposing version information"
                )
            else:
                result.status = "partial"
                result.score = 0.5
                result.findings = [
                    f"Port {p['port']}: {p['banner'][:60]}"
                    for p in banner_exposed
                ]
            result.remediation = (
                "Configure services to suppress version information in banners. "
                "Implement banner hardening across all exposed services."
            )

        else:
            result.status = "not_assessed"
            result.evidence.append(
                "Network control check not implemented for this control"
            )

    def _check_web_control(
        self,
        result: ControlResult,
        control_def: Dict,
        web_data: Dict,
    ):
        """Evaluate a web-security-related control."""
        if not web_data:
            result.status = "not_assessed"
            result.evidence.append("No web scan data available")
            return

        header_findings = web_data.get("header_findings", [])
        ssl_info = web_data.get("ssl_info", {})
        cors_result = web_data.get("cors_result", {})
        cookie_findings = web_data.get("cookie_findings", [])
        security_score = web_data.get("security_score", 0)

        # A.8.5 - Secure Authentication
        if control_def["id"] == "A.8.5":
            hsts_present = any(
                h.get("header") == "Strict-Transport-Security"
                and h.get("status") == "present"
                for h in header_findings
            )
            cookies_secure = all(
                c.get("secure", False) and c.get("httponly", False)
                for c in cookie_findings
            ) if cookie_findings else True

            if hsts_present and cookies_secure:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "HSTS enabled and cookies properly secured"
                )
            elif hsts_present or cookies_secure:
                result.status = "partial"
                result.score = 0.5
                if not hsts_present:
                    result.findings.append("HSTS not configured")
                if not cookies_secure:
                    result.findings.append("Cookies missing security flags")
            else:
                result.status = "fail"
                result.score = 0.0
                result.findings.extend([
                    "HSTS not configured",
                    "Cookies missing security flags",
                ])
            result.remediation = (
                "Enable HSTS with min 1-year max-age. Set Secure, HttpOnly, "
                "and SameSite flags on all session cookies."
            )

        # A.8.12 - Data Leakage Prevention
        elif control_def["id"] == "A.8.12":
            info_disclosure = web_data.get("information_disclosure", [])
            if not info_disclosure:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "No information disclosure headers detected"
                )
            else:
                result.status = "partial"
                result.score = 0.4
                result.findings = [
                    d.get("header_name", "Unknown") for d in info_disclosure
                ]
            result.remediation = (
                "Remove or obfuscate Server, X-Powered-By, and other "
                "technology disclosure headers."
            )

        # A.8.23 - Web Filtering / CSP
        elif control_def["id"] == "A.8.23":
            csp_present = any(
                h.get("header") == "Content-Security-Policy"
                and h.get("status") == "present"
                for h in header_findings
            )
            if csp_present:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "Content Security Policy is configured"
                )
            else:
                result.status = "fail"
                result.score = 0.0
                result.findings.append("Content-Security-Policy header missing")
            result.remediation = (
                "Implement Content-Security-Policy header to control "
                "resource loading and prevent XSS attacks."
            )

        # A.8.24 - Use of Cryptography
        elif control_def["id"] == "A.8.24":
            if ssl_info:
                is_expired = ssl_info.get("is_expired", True)
                days_left = ssl_info.get("days_until_expiry", 0)
                ssl_findings = ssl_info.get("findings", [])

                if not is_expired and days_left > 30 and not ssl_findings:
                    result.status = "pass"
                    result.score = 1.0
                    result.evidence.append(
                        f"Valid SSL certificate ({days_left} days remaining)"
                    )
                elif not is_expired and days_left > 0:
                    result.status = "partial"
                    result.score = 0.6
                    result.evidence.append(
                        f"SSL certificate expiring in {days_left} days"
                    )
                else:
                    result.status = "fail"
                    result.score = 0.0
                    result.findings.append("SSL certificate expired or invalid")
            else:
                result.status = "fail"
                result.score = 0.0
                result.findings.append("No SSL/TLS configuration detected")
            result.remediation = (
                "Ensure valid SSL/TLS certificates with strong cipher suites. "
                "Implement automated certificate management."
            )

        # A.8.26 - Application Security Requirements
        elif control_def["id"] == "A.8.26":
            if security_score >= 80:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    f"Web security score: {security_score}/100"
                )
            elif security_score >= 50:
                result.status = "partial"
                result.score = 0.5
                result.evidence.append(
                    f"Web security score: {security_score}/100"
                )
            else:
                result.status = "fail"
                result.score = 0.0
                result.evidence.append(
                    f"Web security score: {security_score}/100"
                )
            result.remediation = (
                "Address all missing security headers and web misconfigurations. "
                "Implement secure development lifecycle practices."
            )

        # A.8.28 - Secure Coding
        elif control_def["id"] == "A.8.28":
            xss_header = any(
                h.get("header") in (
                    "X-XSS-Protection", "Content-Security-Policy"
                ) and h.get("status") == "present"
                for h in header_findings
            )
            cors_ok = not (cors_result and cors_result.get("is_misconfigured"))
            xframe = any(
                h.get("header") == "X-Frame-Options"
                and h.get("status") == "present"
                for h in header_findings
            )

            checks_passed = sum([xss_header, cors_ok, xframe])
            if checks_passed == 3:
                result.status = "pass"
                result.score = 1.0
            elif checks_passed >= 2:
                result.status = "partial"
                result.score = 0.6
            else:
                result.status = "fail"
                result.score = 0.2
            result.evidence.append(
                f"Secure coding checks passed: {checks_passed}/3 "
                "(XSS protection, CORS, Clickjacking)"
            )
            result.remediation = (
                "Implement all OWASP recommended security headers. "
                "Fix CORS misconfigurations. Add clickjacking protection."
            )

        else:
            result.status = "not_assessed"

    def _check_dns_control(
        self,
        result: ControlResult,
        control_def: Dict,
        dns_data: Dict,
    ):
        """Evaluate a DNS-related control."""
        if not dns_data:
            result.status = "not_assessed"
            result.evidence.append("No DNS scan data available")
            return

    def _check_policy_control(
        self,
        result: ControlResult,
        control_def: Dict,
        policies: Dict,
    ):
        """
        Evaluate a policy-based control.

        Policy controls require attestation data since they cannot be
        verified through technical scanning alone.
        """
        policy_key = control_def["check_keys"][0] if control_def["check_keys"] else ""

        if policies and policy_key in policies:
            attestation = policies[policy_key]
            if isinstance(attestation, dict):
                status = attestation.get("status", "not_assessed")
                result.status = status
                result.score = {
                    "pass": 1.0, "partial": 0.5, "fail": 0.0
                }.get(status, 0.0)
                result.evidence.append(
                    attestation.get("evidence", "Policy attestation provided")
                )
            elif attestation is True:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append("Policy attestation: Implemented")
            else:
                result.status = "fail"
                result.score = 0.0
                result.evidence.append("Policy attestation: Not implemented")
        else:
            result.status = "not_assessed"
            result.score = 0.0
            result.evidence.append(
                f"Policy attestation required for '{control_def['name']}'. "
                "Provide policy data in scan configuration."
            )

        # Set default remediation for policy controls
        remediation_map = {
            "A.5.1": (
                "Develop and publish an Information Security Policy. "
                "Ensure management approval and regular review."
            ),
            "A.5.23": (
                "Establish cloud security policies covering acquisition, "
                "configuration, monitoring, and exit strategies."
            ),
            "A.6.1": (
                "Implement background screening procedures for all "
                "personnel with access to sensitive information."
            ),
            "A.6.3": (
                "Establish a security awareness training program with "
                "annual refresher courses and phishing simulations."
            ),
            "A.7.1": (
                "Define and implement physical security perimeters with "
                "access controls for server rooms and data centers."
            ),
            "A.7.4": (
                "Deploy CCTV, alarm systems, and access logging for "
                "physical security monitoring."
            ),
            "A.8.7": (
                "Deploy endpoint protection (EDR/XDR) on all systems. "
                "Ensure definitions are updated automatically."
            ),
            "A.8.15": (
                "Implement centralized logging (SIEM). Ensure all systems "
                "forward security events. Establish log retention policy."
            ),
        }
        if not result.remediation:
            result.remediation = remediation_map.get(
                control_def["id"],
                f"Implement {control_def['name']} per ISO 27001 requirements."
            )

    def get_control_list(self) -> List[Dict]:
        """
        Get the list of all 20 ISO 27001 controls being checked.

        Returns:
            List of control definition dictionaries.
        """
        return [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c["category"],
                "description": c["description"],
                "priority": c["priority"],
            }
            for c in self.controls
        ]
