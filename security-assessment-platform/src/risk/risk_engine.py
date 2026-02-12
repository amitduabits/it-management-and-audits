"""
Risk Engine Module - Weighted risk calculation across security categories.

Implements a quantitative risk assessment model that calculates composite
risk scores across 6 categories:
    1. Network Security
    2. Application Security
    3. Data Protection
    4. Compliance
    5. Operational Security
    6. Third-Party Risk

Each category is weighted according to organizational priorities and
findings are scored using a CVSS-aligned 0-10 scale.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# Default category weights (must sum to 1.0)
DEFAULT_WEIGHTS = {
    "network_security": 0.25,
    "application_security": 0.20,
    "data_protection": 0.20,
    "compliance": 0.15,
    "operational_security": 0.10,
    "third_party_risk": 0.10,
}

# Severity score mappings (CVSS-aligned)
SEVERITY_SCORES = {
    "critical": 9.5,
    "high": 7.5,
    "medium": 5.0,
    "low": 2.5,
    "info": 0.5,
}

# Risk level thresholds
RISK_LEVELS = {
    "critical": (8.0, 10.0),
    "high": (6.0, 7.99),
    "medium": (4.0, 5.99),
    "low": (2.0, 3.99),
    "minimal": (0.0, 1.99),
}


@dataclass
class CategoryRisk:
    """Risk assessment for a single category."""

    category: str
    display_name: str
    weight: float
    raw_score: float  # 0-10
    weighted_score: float  # raw_score * weight
    risk_level: str
    finding_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    top_findings: List[Dict] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """Complete risk assessment result."""

    assessment_date: str = ""
    overall_risk_score: float = 0.0  # 0-10
    overall_risk_level: str = "minimal"
    categories: List[CategoryRisk] = field(default_factory=list)
    total_findings: int = 0
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    risk_trend: str = "stable"  # "improving", "stable", "worsening"
    recommendations: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "assessment_date": self.assessment_date,
            "overall_risk_score": self.overall_risk_score,
            "overall_risk_level": self.overall_risk_level,
            "total_findings": self.total_findings,
            "severity_distribution": self.severity_distribution,
            "risk_trend": self.risk_trend,
            "categories": [
                {
                    "category": c.category,
                    "display_name": c.display_name,
                    "weight": c.weight,
                    "raw_score": c.raw_score,
                    "weighted_score": c.weighted_score,
                    "risk_level": c.risk_level,
                    "finding_count": c.finding_count,
                    "critical_count": c.critical_count,
                    "high_count": c.high_count,
                    "medium_count": c.medium_count,
                    "low_count": c.low_count,
                    "top_findings": c.top_findings[:5],
                }
                for c in self.categories
            ],
            "recommendations": self.recommendations,
        }


class RiskEngine:
    """
    Weighted risk scoring engine.

    Calculates composite risk scores from scan findings across 6 security
    categories. Each category contributes to the overall risk score based
    on its assigned weight.

    The scoring algorithm:
    1. Findings are categorized by type (network, web, dns, compliance)
    2. Each category's raw score is computed from finding severities
    3. Raw scores are weighted by category importance
    4. Overall score = sum of weighted category scores

    Attributes:
        weights: Dictionary of category weights (sum to 1.0).

    Example:
        engine = RiskEngine()
        assessment = engine.calculate_risk(scan_data, compliance_data)
        print(f"Overall Risk: {assessment.overall_risk_score:.1f}/10")
        print(f"Risk Level: {assessment.overall_risk_level}")
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize the RiskEngine.

        Args:
            weights: Optional custom category weights. Must sum to 1.0.
                Keys: network_security, application_security, data_protection,
                compliance, operational_security, third_party_risk
        """
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self._validate_weights()

    def _validate_weights(self):
        """Ensure weights sum to approximately 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Category weights sum to {total:.3f}, not 1.0. "
                "Normalizing weights."
            )
            for key in self.weights:
                self.weights[key] /= total

    def calculate_risk(
        self,
        scan_data: Dict[str, Any],
        compliance_data: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """
        Calculate comprehensive risk assessment from scan and compliance data.

        Args:
            scan_data: Dictionary containing:
                - network_scan: Network scan results
                - web_scan: Web scan results
                - dns_scan: DNS scan results
            compliance_data: Optional compliance assessment results:
                - iso27001: ISO27001Result.to_dict()
                - pci_dss: PCIDSSResult.to_dict()
                - nist_csf: NISTCSFResult.to_dict()

        Returns:
            RiskAssessment with overall and per-category scores.
        """
        assessment = RiskAssessment()
        assessment.assessment_date = datetime.now().isoformat()

        # Collect all findings
        all_findings = self._collect_findings(scan_data)
        assessment.total_findings = len(all_findings)

        # Calculate severity distribution
        assessment.severity_distribution = self._severity_distribution(
            all_findings
        )

        # Calculate per-category risk
        assessment.categories = [
            self._calculate_network_risk(scan_data),
            self._calculate_application_risk(scan_data),
            self._calculate_data_protection_risk(scan_data),
            self._calculate_compliance_risk(compliance_data or {}),
            self._calculate_operational_risk(scan_data, compliance_data or {}),
            self._calculate_third_party_risk(scan_data),
        ]

        # Calculate overall risk score
        assessment.overall_risk_score = round(
            sum(c.weighted_score for c in assessment.categories), 2
        )

        # Determine overall risk level
        assessment.overall_risk_level = self._score_to_level(
            assessment.overall_risk_score
        )

        # Generate recommendations
        assessment.recommendations = self._generate_recommendations(
            assessment
        )

        return assessment

    def _collect_findings(self, scan_data: Dict) -> List[Dict]:
        """Collect all findings from scan data."""
        findings = []

        network = scan_data.get("network_scan", {})
        if network:
            findings.extend(network.get("findings", []))

        web = scan_data.get("web_scan", {})
        if web:
            findings.extend(web.get("all_findings", []))

        dns = scan_data.get("dns_scan", {})
        if dns:
            findings.extend(dns.get("findings", []))

        return findings

    def _severity_distribution(self, findings: List[Dict]) -> Dict[str, int]:
        """Calculate the distribution of finding severities."""
        dist = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            severity = f.get("severity", "info").lower()
            if severity in dist:
                dist[severity] += 1
        return dist

    def _findings_to_score(self, findings: List[Dict]) -> float:
        """
        Convert a list of findings into a risk score (0-10).

        Algorithm: weighted average of finding severities, capped at 10.
        More critical findings exponentially increase the score.
        """
        if not findings:
            return 0.0

        # Count by severity
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            sev = f.get("severity", "info").lower()
            if sev in counts:
                counts[sev] += 1

        # Weighted severity score with diminishing returns per additional finding
        score = 0.0
        score += min(counts["critical"] * 3.0, 10.0)
        score += min(counts["high"] * 1.5, 5.0)
        score += min(counts["medium"] * 0.8, 3.0)
        score += min(counts["low"] * 0.3, 1.5)
        score += min(counts["info"] * 0.1, 0.5)

        return min(round(score, 2), 10.0)

    def _calculate_network_risk(self, scan_data: Dict) -> CategoryRisk:
        """Calculate network security category risk."""
        network = scan_data.get("network_scan", {})
        findings = network.get("findings", [])
        open_ports = network.get("open_ports", [])

        raw_score = self._findings_to_score(findings)

        # Additional risk from open port count
        if len(open_ports) > 20:
            raw_score = min(raw_score + 2.0, 10.0)
        elif len(open_ports) > 10:
            raw_score = min(raw_score + 1.0, 10.0)

        weight = self.weights["network_security"]
        counts = self._count_severities(findings)

        return CategoryRisk(
            category="network_security",
            display_name="Network Security",
            weight=weight,
            raw_score=raw_score,
            weighted_score=round(raw_score * weight, 3),
            risk_level=self._score_to_level(raw_score),
            finding_count=len(findings),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            top_findings=sorted(
                findings, key=lambda x: x.get("cvss_score", 0), reverse=True
            )[:5],
        )

    def _calculate_application_risk(self, scan_data: Dict) -> CategoryRisk:
        """Calculate application security category risk."""
        web = scan_data.get("web_scan", {})
        all_findings = web.get("all_findings", [])

        # Filter to application-specific findings
        app_findings = [
            f for f in all_findings
            if "header" in f.get("title", "").lower()
            or "cookie" in f.get("title", "").lower()
            or "cors" in f.get("title", "").lower()
            or "xss" in f.get("title", "").lower()
        ]

        raw_score = self._findings_to_score(app_findings)

        # Factor in web security score
        web_score = web.get("security_score", 100)
        if web_score < 50:
            raw_score = min(raw_score + 2.0, 10.0)
        elif web_score < 70:
            raw_score = min(raw_score + 1.0, 10.0)

        weight = self.weights["application_security"]
        counts = self._count_severities(app_findings)

        return CategoryRisk(
            category="application_security",
            display_name="Application Security",
            weight=weight,
            raw_score=raw_score,
            weighted_score=round(raw_score * weight, 3),
            risk_level=self._score_to_level(raw_score),
            finding_count=len(app_findings),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            top_findings=sorted(
                app_findings,
                key=lambda x: x.get("cvss_score", 0),
                reverse=True,
            )[:5],
        )

    def _calculate_data_protection_risk(self, scan_data: Dict) -> CategoryRisk:
        """Calculate data protection category risk."""
        web = scan_data.get("web_scan", {})
        dns = scan_data.get("dns_scan", {})

        data_findings = []

        # SSL/TLS findings
        ssl_info = web.get("ssl_info", {})
        if ssl_info:
            data_findings.extend(ssl_info.get("findings", []))

        # Information disclosure findings
        data_findings.extend(web.get("information_disclosure", []))

        # Email security findings (SPF/DMARC)
        if dns:
            spf = dns.get("spf", {})
            if spf:
                data_findings.extend(spf.get("findings", []))
            dmarc = dns.get("dmarc", {})
            if dmarc:
                data_findings.extend(dmarc.get("findings", []))

        raw_score = self._findings_to_score(data_findings)
        weight = self.weights["data_protection"]
        counts = self._count_severities(data_findings)

        return CategoryRisk(
            category="data_protection",
            display_name="Data Protection",
            weight=weight,
            raw_score=raw_score,
            weighted_score=round(raw_score * weight, 3),
            risk_level=self._score_to_level(raw_score),
            finding_count=len(data_findings),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            top_findings=sorted(
                data_findings,
                key=lambda x: x.get("cvss_score", 0),
                reverse=True,
            )[:5],
        )

    def _calculate_compliance_risk(
        self, compliance_data: Dict
    ) -> CategoryRisk:
        """Calculate compliance category risk."""
        compliance_findings = []
        scores = []

        for framework in ("iso27001", "pci_dss", "nist_csf"):
            fw_data = compliance_data.get(framework, {})
            if fw_data:
                fw_score = fw_data.get("overall_score", 0)
                scores.append(fw_score)

                # Generate findings for failed controls
                controls = fw_data.get("controls", fw_data.get(
                    "requirements", fw_data.get("subcategories", [])
                ))
                for control in controls:
                    if control.get("status") == "fail":
                        compliance_findings.append({
                            "title": (
                                f"Failed: {control.get('control_id', control.get('requirement_id', control.get('subcategory_id', '')))} "
                                f"- {control.get('control_name', control.get('requirement_name', control.get('subcategory_name', '')))}"
                            ),
                            "severity": "high",
                            "cvss_score": 7.0,
                        })
                    elif control.get("status") == "partial":
                        compliance_findings.append({
                            "title": (
                                f"Partial: {control.get('control_id', control.get('requirement_id', control.get('subcategory_id', '')))} "
                                f"- {control.get('control_name', control.get('requirement_name', control.get('subcategory_name', '')))}"
                            ),
                            "severity": "medium",
                            "cvss_score": 4.0,
                        })

        # Compute raw score from compliance gaps
        if scores:
            avg_compliance = sum(scores) / len(scores)
            raw_score = round((1.0 - avg_compliance) * 10.0, 2)
        else:
            raw_score = self._findings_to_score(compliance_findings)

        weight = self.weights["compliance"]
        counts = self._count_severities(compliance_findings)

        return CategoryRisk(
            category="compliance",
            display_name="Compliance",
            weight=weight,
            raw_score=min(raw_score, 10.0),
            weighted_score=round(min(raw_score, 10.0) * weight, 3),
            risk_level=self._score_to_level(raw_score),
            finding_count=len(compliance_findings),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            top_findings=compliance_findings[:5],
        )

    def _calculate_operational_risk(
        self, scan_data: Dict, compliance_data: Dict
    ) -> CategoryRisk:
        """Calculate operational security category risk."""
        op_findings = []

        # Operational findings from DNS
        dns = scan_data.get("dns_scan", {})
        if dns:
            dns_findings = dns.get("findings", [])
            for f in dns_findings:
                if any(
                    kw in f.get("title", "").lower()
                    for kw in ("dnssec", "nameserver", "wildcard")
                ):
                    op_findings.append(f)

        # Excessive open ports indicates operational issues
        network = scan_data.get("network_scan", {})
        if network:
            open_count = network.get("open_ports_count", len(
                network.get("open_ports", [])
            ))
            if open_count > 15:
                op_findings.append({
                    "title": "Excessive services indicate weak change management",
                    "severity": "medium",
                    "cvss_score": 5.0,
                })

        raw_score = self._findings_to_score(op_findings)
        weight = self.weights["operational_security"]
        counts = self._count_severities(op_findings)

        return CategoryRisk(
            category="operational_security",
            display_name="Operational Security",
            weight=weight,
            raw_score=raw_score,
            weighted_score=round(raw_score * weight, 3),
            risk_level=self._score_to_level(raw_score),
            finding_count=len(op_findings),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            top_findings=op_findings[:5],
        )

    def _calculate_third_party_risk(self, scan_data: Dict) -> CategoryRisk:
        """Calculate third-party risk category."""
        tp_findings = []

        # DNS-based third-party indicators
        dns = scan_data.get("dns_scan", {})
        if dns:
            spf = dns.get("spf", {})
            if spf and spf.get("includes"):
                includes = spf.get("includes", [])
                if len(includes) > 5:
                    tp_findings.append({
                        "title": (
                            f"Excessive SPF includes ({len(includes)}) "
                            "indicate many third-party email senders"
                        ),
                        "severity": "low",
                        "cvss_score": 3.0,
                    })

        # Web-based third-party indicators
        web = scan_data.get("web_scan", {})
        if web:
            cors = web.get("cors_result", {})
            if cors and cors.get("allows_all_origins"):
                tp_findings.append({
                    "title": "CORS allows all origins - third-party integration risk",
                    "severity": "medium",
                    "cvss_score": 5.0,
                })

        raw_score = self._findings_to_score(tp_findings)
        weight = self.weights["third_party_risk"]
        counts = self._count_severities(tp_findings)

        return CategoryRisk(
            category="third_party_risk",
            display_name="Third-Party Risk",
            weight=weight,
            raw_score=raw_score,
            weighted_score=round(raw_score * weight, 3),
            risk_level=self._score_to_level(raw_score),
            finding_count=len(tp_findings),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            top_findings=tp_findings[:5],
        )

    def _count_severities(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            sev = f.get("severity", "info").lower()
            if sev in counts:
                counts[sev] += 1
        return counts

    def _score_to_level(self, score: float) -> str:
        """Convert a numeric score to a risk level string."""
        for level, (low, high) in RISK_LEVELS.items():
            if low <= score <= high:
                return level
        return "minimal"

    def _generate_recommendations(
        self, assessment: RiskAssessment
    ) -> List[Dict]:
        """
        Generate prioritized recommendations based on the risk assessment.

        Args:
            assessment: The completed RiskAssessment.

        Returns:
            List of recommendation dictionaries sorted by priority.
        """
        recommendations = []
        priority_counter = 0

        # Sort categories by raw_score descending (highest risk first)
        sorted_categories = sorted(
            assessment.categories,
            key=lambda c: c.raw_score,
            reverse=True,
        )

        for category in sorted_categories:
            if category.raw_score >= 6.0:
                priority_counter += 1
                recommendations.append({
                    "priority": priority_counter,
                    "urgency": "immediate",
                    "category": category.display_name,
                    "risk_score": category.raw_score,
                    "recommendation": (
                        f"Address critical and high-severity findings in "
                        f"{category.display_name}. Current risk score: "
                        f"{category.raw_score}/10 ({category.risk_level})."
                    ),
                    "finding_count": category.finding_count,
                    "timeframe": "0-30 days",
                })
            elif category.raw_score >= 4.0:
                priority_counter += 1
                recommendations.append({
                    "priority": priority_counter,
                    "urgency": "short_term",
                    "category": category.display_name,
                    "risk_score": category.raw_score,
                    "recommendation": (
                        f"Reduce risk in {category.display_name} by addressing "
                        f"medium-severity findings. Current risk score: "
                        f"{category.raw_score}/10 ({category.risk_level})."
                    ),
                    "finding_count": category.finding_count,
                    "timeframe": "30-90 days",
                })
            elif category.raw_score >= 2.0:
                priority_counter += 1
                recommendations.append({
                    "priority": priority_counter,
                    "urgency": "long_term",
                    "category": category.display_name,
                    "risk_score": category.raw_score,
                    "recommendation": (
                        f"Improve {category.display_name} posture through "
                        f"ongoing hardening and monitoring."
                    ),
                    "finding_count": category.finding_count,
                    "timeframe": "90-365 days",
                })

        return recommendations
