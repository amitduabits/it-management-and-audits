"""
NIST Cybersecurity Framework (CSF) Compliance Checker.

Implements automated checks mapped to the 5 NIST CSF core functions:
    - Identify (ID): Asset management, risk assessment, governance
    - Protect (PR): Access control, awareness, data security
    - Detect (DE): Anomaly detection, monitoring, detection processes
    - Respond (RS): Response planning, communications, analysis
    - Recover (RC): Recovery planning, improvements, communications

Reference: NIST Cybersecurity Framework v1.1 / v2.0
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CSFSubcategoryResult:
    """Result of a single NIST CSF subcategory check."""

    function: str
    category_id: str
    subcategory_id: str
    subcategory_name: str
    description: str
    status: str  # "pass", "fail", "partial", "not_assessed"
    score: float  # 0.0 to 1.0
    implementation_tier: int  # 1-4 (Partial, Risk Informed, Repeatable, Adaptive)
    evidence: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    remediation: str = ""


@dataclass
class NISTCSFResult:
    """Complete NIST CSF compliance assessment result."""

    assessment_date: str = ""
    overall_score: float = 0.0
    total_subcategories: int = 0
    passed: int = 0
    failed: int = 0
    partial: int = 0
    not_assessed: int = 0
    function_scores: Dict[str, float] = field(default_factory=dict)
    subcategory_results: List[CSFSubcategoryResult] = field(default_factory=list)
    overall_tier: int = 1  # 1-4

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "framework": "NIST CSF v2.0",
            "assessment_date": self.assessment_date,
            "overall_score": self.overall_score,
            "overall_percentage": round(self.overall_score * 100, 1),
            "overall_tier": self.overall_tier,
            "overall_tier_name": {
                1: "Partial", 2: "Risk Informed",
                3: "Repeatable", 4: "Adaptive",
            }.get(self.overall_tier, "Unknown"),
            "total_subcategories": self.total_subcategories,
            "passed": self.passed,
            "failed": self.failed,
            "partial": self.partial,
            "not_assessed": self.not_assessed,
            "function_scores": self.function_scores,
            "subcategories": [
                {
                    "function": s.function,
                    "category_id": s.category_id,
                    "subcategory_id": s.subcategory_id,
                    "subcategory_name": s.subcategory_name,
                    "description": s.description,
                    "status": s.status,
                    "score": s.score,
                    "implementation_tier": s.implementation_tier,
                    "evidence": s.evidence,
                    "findings": s.findings,
                    "remediation": s.remediation,
                }
                for s in self.subcategory_results
            ],
        }


# NIST CSF Subcategories with checks
NIST_CSF_CHECKS = [
    # IDENTIFY Function
    {
        "function": "Identify",
        "function_code": "ID",
        "category_id": "ID.AM",
        "subcategory_id": "ID.AM-1",
        "name": "Physical Devices and Systems Inventory",
        "description": (
            "Physical devices and systems within the organization are "
            "inventoried."
        ),
        "check_type": "policy",
        "check_key": "asset_inventory",
    },
    {
        "function": "Identify",
        "function_code": "ID",
        "category_id": "ID.AM",
        "subcategory_id": "ID.AM-2",
        "name": "Software Platforms and Applications Inventory",
        "description": (
            "Software platforms and applications within the organization "
            "are inventoried."
        ),
        "check_type": "network",
        "check_key": "service_inventory",
    },
    {
        "function": "Identify",
        "function_code": "ID",
        "category_id": "ID.RA",
        "subcategory_id": "ID.RA-1",
        "name": "Asset Vulnerabilities Identified",
        "description": (
            "Asset vulnerabilities are identified and documented."
        ),
        "check_type": "combined",
        "check_key": "vulnerability_identification",
    },
    {
        "function": "Identify",
        "function_code": "ID",
        "category_id": "ID.GV",
        "subcategory_id": "ID.GV-1",
        "name": "Organizational Security Policy Established",
        "description": (
            "Organizational cybersecurity policy is established and "
            "communicated."
        ),
        "check_type": "policy",
        "check_key": "security_policy",
    },
    # PROTECT Function
    {
        "function": "Protect",
        "function_code": "PR",
        "category_id": "PR.AC",
        "subcategory_id": "PR.AC-1",
        "name": "Identities and Credentials Managed",
        "description": (
            "Identities and credentials are issued, managed, verified, "
            "revoked, and audited for authorized devices, users, and processes."
        ),
        "check_type": "web",
        "check_key": "authentication",
    },
    {
        "function": "Protect",
        "function_code": "PR",
        "category_id": "PR.AC",
        "subcategory_id": "PR.AC-3",
        "name": "Remote Access Managed",
        "description": (
            "Remote access is managed through controlled access points."
        ),
        "check_type": "network",
        "check_key": "remote_access",
    },
    {
        "function": "Protect",
        "function_code": "PR",
        "category_id": "PR.AC",
        "subcategory_id": "PR.AC-5",
        "name": "Network Integrity Protected",
        "description": (
            "Network integrity is protected, incorporating network "
            "segregation where appropriate."
        ),
        "check_type": "network",
        "check_key": "network_integrity",
    },
    {
        "function": "Protect",
        "function_code": "PR",
        "category_id": "PR.DS",
        "subcategory_id": "PR.DS-1",
        "name": "Data-at-Rest Protected",
        "description": "Data-at-rest is protected.",
        "check_type": "policy",
        "check_key": "data_encryption_at_rest",
    },
    {
        "function": "Protect",
        "function_code": "PR",
        "category_id": "PR.DS",
        "subcategory_id": "PR.DS-2",
        "name": "Data-in-Transit Protected",
        "description": "Data-in-transit is protected.",
        "check_type": "web",
        "check_key": "transport_encryption",
    },
    {
        "function": "Protect",
        "function_code": "PR",
        "category_id": "PR.DS",
        "subcategory_id": "PR.DS-5",
        "name": "Protections Against Data Leaks Implemented",
        "description": (
            "Protections against data leaks are implemented."
        ),
        "check_type": "web",
        "check_key": "data_leak_prevention",
    },
    {
        "function": "Protect",
        "function_code": "PR",
        "category_id": "PR.IP",
        "subcategory_id": "PR.IP-1",
        "name": "Configuration Management Baseline",
        "description": (
            "A baseline configuration of IT/ICS systems is created and "
            "maintained."
        ),
        "check_type": "network",
        "check_key": "configuration_baseline",
    },
    {
        "function": "Protect",
        "function_code": "PR",
        "category_id": "PR.AT",
        "subcategory_id": "PR.AT-1",
        "name": "Security Awareness Training",
        "description": (
            "All users are informed and trained in cybersecurity awareness."
        ),
        "check_type": "policy",
        "check_key": "security_training",
    },
    # DETECT Function
    {
        "function": "Detect",
        "function_code": "DE",
        "category_id": "DE.AE",
        "subcategory_id": "DE.AE-1",
        "name": "Network Operations Baseline Established",
        "description": (
            "A baseline of network operations and expected data flows "
            "is established and managed."
        ),
        "check_type": "policy",
        "check_key": "network_baseline",
    },
    {
        "function": "Detect",
        "function_code": "DE",
        "category_id": "DE.CM",
        "subcategory_id": "DE.CM-1",
        "name": "Network Monitored for Security Events",
        "description": (
            "The network is monitored to detect potential cybersecurity events."
        ),
        "check_type": "policy",
        "check_key": "network_monitoring",
    },
    {
        "function": "Detect",
        "function_code": "DE",
        "category_id": "DE.CM",
        "subcategory_id": "DE.CM-4",
        "name": "Malicious Code Detected",
        "description": "Malicious code is detected.",
        "check_type": "policy",
        "check_key": "malware_detection",
    },
    {
        "function": "Detect",
        "function_code": "DE",
        "category_id": "DE.CM",
        "subcategory_id": "DE.CM-8",
        "name": "Vulnerability Scans Performed",
        "description": "Vulnerability scans are performed.",
        "check_type": "combined",
        "check_key": "vulnerability_scanning",
    },
    # RESPOND Function
    {
        "function": "Respond",
        "function_code": "RS",
        "category_id": "RS.RP",
        "subcategory_id": "RS.RP-1",
        "name": "Incident Response Plan Executed",
        "description": (
            "Response plan is executed during or after an incident."
        ),
        "check_type": "policy",
        "check_key": "incident_response_plan",
    },
    {
        "function": "Respond",
        "function_code": "RS",
        "category_id": "RS.AN",
        "subcategory_id": "RS.AN-1",
        "name": "Notifications from Detection Systems Investigated",
        "description": (
            "Notifications from detection systems are investigated."
        ),
        "check_type": "policy",
        "check_key": "incident_investigation",
    },
    # RECOVER Function
    {
        "function": "Recover",
        "function_code": "RC",
        "category_id": "RC.RP",
        "subcategory_id": "RC.RP-1",
        "name": "Recovery Plan Executed",
        "description": (
            "Recovery plan is executed during or after a cybersecurity incident."
        ),
        "check_type": "policy",
        "check_key": "recovery_plan",
    },
    {
        "function": "Recover",
        "function_code": "RC",
        "category_id": "RC.IM",
        "subcategory_id": "RC.IM-1",
        "name": "Recovery Plans Incorporate Lessons Learned",
        "description": (
            "Recovery plans incorporate lessons learned."
        ),
        "check_type": "policy",
        "check_key": "lessons_learned",
    },
]


class NISTCSFChecker:
    """
    NIST Cybersecurity Framework compliance checker.

    Evaluates scan findings against NIST CSF subcategories across
    all 5 core functions and provides a maturity assessment.

    Example:
        checker = NISTCSFChecker()
        result = checker.assess(scan_data)
        print(f"Overall Score: {result.overall_score * 100:.1f}%")
        print(f"Implementation Tier: {result.overall_tier}")
        for func, score in result.function_scores.items():
            print(f"  {func}: {score:.1f}%")
    """

    def __init__(self):
        """Initialize the NIST CSF compliance checker."""
        self.checks = NIST_CSF_CHECKS

    def assess(self, scan_data: Dict[str, Any]) -> NISTCSFResult:
        """
        Perform NIST CSF compliance assessment based on scan data.

        Args:
            scan_data: Dictionary containing scan results.

        Returns:
            NISTCSFResult with compliance assessment.
        """
        result = NISTCSFResult()
        result.assessment_date = datetime.now().isoformat()
        result.total_subcategories = len(self.checks)

        network_data = scan_data.get("network_scan", {})
        web_data = scan_data.get("web_scan", {})
        dns_data = scan_data.get("dns_scan", {})
        policies = scan_data.get("policies", {})

        for check_def in self.checks:
            sub_result = self._check_subcategory(
                check_def, network_data, web_data, dns_data, policies
            )
            result.subcategory_results.append(sub_result)

            if sub_result.status == "pass":
                result.passed += 1
            elif sub_result.status == "fail":
                result.failed += 1
            elif sub_result.status == "partial":
                result.partial += 1
            else:
                result.not_assessed += 1

        # Calculate overall score
        total_score = sum(s.score for s in result.subcategory_results)
        result.overall_score = round(
            total_score / result.total_subcategories, 3
        ) if result.total_subcategories > 0 else 0.0

        # Function scores
        functions = {}
        for sr in result.subcategory_results:
            func = sr.function
            if func not in functions:
                functions[func] = {"total": 0, "score": 0.0}
            functions[func]["total"] += 1
            functions[func]["score"] += sr.score

        for func, data in functions.items():
            result.function_scores[func] = round(
                (data["score"] / data["total"]) * 100, 1
            ) if data["total"] > 0 else 0.0

        # Determine overall tier based on score
        if result.overall_score >= 0.85:
            result.overall_tier = 4  # Adaptive
        elif result.overall_score >= 0.65:
            result.overall_tier = 3  # Repeatable
        elif result.overall_score >= 0.40:
            result.overall_tier = 2  # Risk Informed
        else:
            result.overall_tier = 1  # Partial

        return result

    def _check_subcategory(
        self,
        check_def: Dict,
        network_data: Dict,
        web_data: Dict,
        dns_data: Dict,
        policies: Dict,
    ) -> CSFSubcategoryResult:
        """
        Check a single NIST CSF subcategory against scan data.

        Args:
            check_def: Subcategory check definition.
            network_data: Network scan results.
            web_data: Web scan results.
            dns_data: DNS scan results.
            policies: Policy attestation data.

        Returns:
            CSFSubcategoryResult with check outcome.
        """
        sub_result = CSFSubcategoryResult(
            function=check_def["function"],
            category_id=check_def["category_id"],
            subcategory_id=check_def["subcategory_id"],
            subcategory_name=check_def["name"],
            description=check_def["description"],
            status="not_assessed",
            score=0.0,
            implementation_tier=1,
        )

        check_type = check_def["check_type"]
        check_key = check_def["check_key"]

        if check_type == "network":
            self._check_network(sub_result, check_key, network_data)
        elif check_type == "web":
            self._check_web(sub_result, check_key, web_data)
        elif check_type == "combined":
            self._check_combined(
                sub_result, check_key, network_data, web_data, dns_data
            )
        elif check_type == "policy":
            self._check_policy(sub_result, check_key, policies)

        # Determine implementation tier from score
        if sub_result.score >= 0.9:
            sub_result.implementation_tier = 4
        elif sub_result.score >= 0.7:
            sub_result.implementation_tier = 3
        elif sub_result.score >= 0.4:
            sub_result.implementation_tier = 2
        else:
            sub_result.implementation_tier = 1

        return sub_result

    def _check_network(
        self,
        result: CSFSubcategoryResult,
        check_key: str,
        network_data: Dict,
    ):
        """Evaluate a network-based NIST CSF subcategory."""
        if not network_data:
            result.status = "not_assessed"
            result.evidence.append("No network scan data available")
            return

        open_ports = network_data.get("open_ports", [])
        findings = network_data.get("findings", [])

        # ID.AM-2 - Software/Service Inventory
        if check_key == "service_inventory":
            identified = [p for p in open_ports if p.get("service") != "unknown"]
            total = len(open_ports)
            if total > 0:
                ratio = len(identified) / total
                if ratio >= 0.8:
                    result.status = "pass"
                    result.score = 1.0
                    result.evidence.append(
                        f"{len(identified)}/{total} services identified"
                    )
                elif ratio >= 0.5:
                    result.status = "partial"
                    result.score = 0.5
                else:
                    result.status = "partial"
                    result.score = 0.3
            else:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append("No open services detected")
            result.remediation = (
                "Maintain a complete inventory of all software and services. "
                "Use automated discovery tools for continuous monitoring."
            )

        # PR.AC-3 - Remote Access Management
        elif check_key == "remote_access":
            remote_ports = [
                p for p in open_ports
                if p.get("port") in (22, 3389, 5900, 23)
            ]
            insecure_remote = [
                p for p in remote_ports
                if p.get("port") in (23, 5900, 3389)
            ]
            if not remote_ports:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append("No direct remote access services exposed")
            elif not insecure_remote:
                result.status = "partial"
                result.score = 0.7
                result.evidence.append(
                    "SSH only - acceptable with proper hardening"
                )
            else:
                result.status = "fail"
                result.score = 0.1
                result.findings = [
                    f"Insecure remote access: {p['service']} on port {p['port']}"
                    for p in insecure_remote
                ]
            result.remediation = (
                "Require VPN or zero-trust network access for all remote connections. "
                "Disable Telnet and unencrypted remote access."
            )

        # PR.AC-5 - Network Integrity
        elif check_key == "network_integrity":
            high_risk = [
                f for f in findings
                if f.get("severity") in ("critical", "high")
            ]
            if not high_risk:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "No critical network integrity issues"
                )
            elif len(high_risk) <= 3:
                result.status = "partial"
                result.score = 0.4
                result.findings = [f.get("title", "") for f in high_risk]
            else:
                result.status = "fail"
                result.score = 0.0
                result.findings = [f.get("title", "") for f in high_risk]
            result.remediation = (
                "Implement network segmentation. Deploy IDS/IPS. "
                "Restrict lateral movement between network zones."
            )

        # PR.IP-1 - Configuration Baseline
        elif check_key == "configuration_baseline":
            banner_ports = [p for p in open_ports if p.get("banner")]
            unnecessary = [
                p for p in open_ports
                if p.get("port") in (21, 23, 135, 139)
            ]
            if not unnecessary and len(banner_ports) <= 2:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append(
                    "System appears to follow hardening baseline"
                )
            elif not unnecessary:
                result.status = "partial"
                result.score = 0.6
                result.evidence.append(
                    "Some service banners exposed but no legacy services"
                )
            else:
                result.status = "fail"
                result.score = 0.2
                result.findings = [
                    f"Legacy service: {p['service']}" for p in unnecessary
                ]
            result.remediation = (
                "Establish and maintain secure configuration baselines "
                "(CIS Benchmarks). Automate configuration compliance checking."
            )

    def _check_web(
        self,
        result: CSFSubcategoryResult,
        check_key: str,
        web_data: Dict,
    ):
        """Evaluate a web-based NIST CSF subcategory."""
        if not web_data:
            result.status = "not_assessed"
            result.evidence.append("No web scan data available")
            return

        header_findings = web_data.get("header_findings", [])
        ssl_info = web_data.get("ssl_info", {})
        cookie_findings = web_data.get("cookie_findings", [])
        info_disclosure = web_data.get("information_disclosure", [])

        # PR.AC-1 - Identity/Credential Management
        if check_key == "authentication":
            hsts = any(
                h.get("header") == "Strict-Transport-Security"
                and h.get("status") == "present"
                for h in header_findings
            )
            secure_cookies = all(
                c.get("secure") and c.get("httponly")
                for c in cookie_findings
            ) if cookie_findings else True

            if hsts and secure_cookies:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append("Strong authentication controls in place")
            elif hsts or secure_cookies:
                result.status = "partial"
                result.score = 0.5
            else:
                result.status = "fail"
                result.score = 0.0
            result.remediation = (
                "Enable HSTS. Secure all session cookies. "
                "Implement multi-factor authentication."
            )

        # PR.DS-2 - Data in Transit
        elif check_key == "transport_encryption":
            if ssl_info:
                is_valid = not ssl_info.get("is_expired", True)
                has_issues = bool(ssl_info.get("findings", []))
                if is_valid and not has_issues:
                    result.status = "pass"
                    result.score = 1.0
                    result.evidence.append("Strong TLS encryption in place")
                elif is_valid:
                    result.status = "partial"
                    result.score = 0.6
                    result.evidence.append("TLS present but has configuration issues")
                else:
                    result.status = "fail"
                    result.score = 0.0
            else:
                result.status = "fail"
                result.score = 0.0
                result.findings.append("No TLS encryption detected")
            result.remediation = (
                "Enforce TLS 1.2+ for all data in transit. "
                "Disable older protocols. Use strong cipher suites."
            )

        # PR.DS-5 - Data Leak Prevention
        elif check_key == "data_leak_prevention":
            if not info_disclosure:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append("No information leakage detected")
            else:
                result.status = "partial"
                result.score = 0.4
                result.findings = [
                    d.get("header_name", "") for d in info_disclosure
                ]
            result.remediation = (
                "Remove technology disclosure headers. "
                "Implement DLP solutions for sensitive data."
            )

    def _check_combined(
        self,
        result: CSFSubcategoryResult,
        check_key: str,
        network_data: Dict,
        web_data: Dict,
        dns_data: Dict,
    ):
        """Evaluate a subcategory using combined scan data."""

        # ID.RA-1 / DE.CM-8 - Vulnerability Identification/Scanning
        if check_key in ("vulnerability_identification", "vulnerability_scanning"):
            net_findings = network_data.get("findings", []) if network_data else []
            web_findings = web_data.get("all_findings", []) if web_data else []
            dns_findings = dns_data.get("findings", []) if dns_data else []

            total = len(net_findings) + len(web_findings) + len(dns_findings)
            has_scan_data = bool(network_data or web_data or dns_data)

            if has_scan_data:
                result.status = "pass" if total > 0 else "pass"
                result.score = 1.0
                result.evidence.append(
                    f"Vulnerability assessment performed: {total} findings identified "
                    f"(Network: {len(net_findings)}, Web: {len(web_findings)}, "
                    f"DNS: {len(dns_findings)})"
                )
            else:
                result.status = "not_assessed"
                result.evidence.append("No scan data available")

            result.remediation = (
                "Conduct regular vulnerability assessments. "
                "Prioritize remediation by risk severity."
            )

    def _check_policy(
        self,
        result: CSFSubcategoryResult,
        check_key: str,
        policies: Dict,
    ):
        """Evaluate a policy-based NIST CSF subcategory."""
        if policies and check_key in policies:
            attestation = policies[check_key]
            if isinstance(attestation, dict):
                status = attestation.get("status", "not_assessed")
                result.status = status
                result.score = {"pass": 1.0, "partial": 0.5, "fail": 0.0}.get(
                    status, 0.0
                )
                result.evidence.append(
                    attestation.get("evidence", "Attestation provided")
                )
            elif attestation is True:
                result.status = "pass"
                result.score = 1.0
                result.evidence.append("Policy/process attestation: Implemented")
            else:
                result.status = "fail"
                result.score = 0.0
        else:
            result.status = "not_assessed"
            result.evidence.append(
                f"Policy attestation required for '{result.subcategory_name}'"
            )

        # Default remediation by function
        remediation_map = {
            "asset_inventory": (
                "Implement automated asset discovery. Maintain a Configuration "
                "Management Database (CMDB)."
            ),
            "security_policy": (
                "Develop, publish, and regularly review organizational "
                "cybersecurity policies."
            ),
            "data_encryption_at_rest": (
                "Implement encryption for all data at rest using AES-256. "
                "Establish key management procedures."
            ),
            "security_training": (
                "Implement security awareness training program with "
                "regular updates and phishing simulations."
            ),
            "network_baseline": (
                "Establish and document normal network traffic patterns. "
                "Use NetFlow analysis for baselining."
            ),
            "network_monitoring": (
                "Deploy SIEM, IDS/IPS, and NDR solutions. "
                "Implement 24/7 security monitoring."
            ),
            "malware_detection": (
                "Deploy EDR/XDR solutions across all endpoints. "
                "Implement network-level malware detection."
            ),
            "incident_response_plan": (
                "Develop and test an incident response plan. "
                "Conduct tabletop exercises quarterly."
            ),
            "incident_investigation": (
                "Establish SOC procedures for investigating alerts. "
                "Define escalation paths and SLAs."
            ),
            "recovery_plan": (
                "Develop disaster recovery and business continuity plans. "
                "Test annually through simulation exercises."
            ),
            "lessons_learned": (
                "Conduct post-incident reviews. Update recovery plans "
                "based on findings from real incidents and exercises."
            ),
        }
        if not result.remediation:
            result.remediation = remediation_map.get(
                check_key,
                f"Implement controls for {result.subcategory_name}."
            )

    def get_function_summary(self) -> Dict[str, List[str]]:
        """Get a summary of checks organized by NIST CSF function."""
        summary = {}
        for check in self.checks:
            func = check["function"]
            if func not in summary:
                summary[func] = []
            summary[func].append(
                f"{check['subcategory_id']}: {check['name']}"
            )
        return summary
