"""
Severity Calculator
====================

Calculates incident severity using CVSS-inspired scoring methodology
combined with business impact assessment. Produces a composite severity
rating that considers technical severity, data sensitivity, operational
impact, and regulatory exposure.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class DataClassification(Enum):
    """Data sensitivity classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class SystemCriticality(Enum):
    """System criticality tiers for business impact assessment."""
    TIER_1_CRITICAL = "tier_1_critical"      # Revenue-generating, customer-facing
    TIER_2_IMPORTANT = "tier_2_important"    # Business operations support
    TIER_3_STANDARD = "tier_3_standard"      # Internal productivity
    TIER_4_NON_CRITICAL = "tier_4_non_critical"  # Development, testing


@dataclass
class CVSSVector:
    """
    Simplified CVSS v3.1-inspired scoring vector for incident severity.

    Each metric is scored on a 0.0 - 1.0 scale representing the impact
    or exploitability of the relevant dimension.
    """
    # Exploitability metrics
    attack_vector: float = 0.5       # Network=0.85, Adjacent=0.62, Local=0.55, Physical=0.20
    attack_complexity: float = 0.5   # Low=0.77, High=0.44
    privileges_required: float = 0.5 # None=0.85, Low=0.62, High=0.27
    user_interaction: float = 0.5    # None=0.85, Required=0.62

    # Impact metrics
    confidentiality_impact: float = 0.5  # High=0.56, Low=0.22, None=0.0
    integrity_impact: float = 0.5        # High=0.56, Low=0.22, None=0.0
    availability_impact: float = 0.5     # High=0.56, Low=0.22, None=0.0

    # Scope
    scope_changed: bool = False  # Whether the vulnerability impacts resources beyond its scope

    def calculate_base_score(self) -> float:
        """
        Calculate CVSS-inspired base score (0.0 - 10.0).

        This is a simplified calculation inspired by CVSS v3.1 methodology.
        For official CVSS scoring, use the FIRST calculator.
        """
        # Exploitability sub-score
        exploitability = (
            8.22
            * self.attack_vector
            * self.attack_complexity
            * self.privileges_required
            * self.user_interaction
        )

        # Impact sub-score (ISC)
        isc_base = 1 - (
            (1 - self.confidentiality_impact)
            * (1 - self.integrity_impact)
            * (1 - self.availability_impact)
        )

        if self.scope_changed:
            impact = 7.52 * (isc_base - 0.029) - 3.25 * (isc_base - 0.02) ** 15
        else:
            impact = 6.42 * isc_base

        if impact <= 0:
            return 0.0

        if self.scope_changed:
            score = min(1.08 * (impact + exploitability), 10.0)
        else:
            score = min(impact + exploitability, 10.0)

        return round(score, 1)


@dataclass
class BusinessImpactFactors:
    """
    Business impact assessment factors for severity calculation.

    These factors capture the organizational impact dimensions that
    go beyond technical severity.
    """
    # Data impact
    data_classification: DataClassification = DataClassification.INTERNAL
    records_affected: int = 0
    data_categories: List[str] = field(default_factory=list)  # PII, PHI, PCI, IP, etc.

    # System impact
    system_criticality: SystemCriticality = SystemCriticality.TIER_3_STANDARD
    systems_affected_count: int = 1
    service_degradation_percent: float = 0.0  # 0-100

    # Operational impact
    revenue_impact_per_hour: float = 0.0
    estimated_downtime_hours: float = 0.0
    affected_users: int = 0
    affected_customers: int = 0

    # Regulatory exposure
    regulatory_frameworks: List[str] = field(default_factory=list)  # GDPR, HIPAA, PCI-DSS, etc.
    notification_required: bool = False
    notification_deadline_hours: Optional[int] = None

    # Reputational impact
    public_visibility: bool = False
    media_coverage_likely: bool = False
    customer_trust_impact: str = "low"  # low, medium, high, critical


@dataclass
class SeverityAssessment:
    """Complete severity assessment result."""
    technical_score: float = 0.0         # CVSS-inspired score (0-10)
    business_impact_score: float = 0.0   # Business impact score (0-10)
    composite_score: float = 0.0         # Weighted composite (0-10)
    severity_level: str = "medium"       # critical, high, medium, low, informational
    confidence: str = "medium"           # Confidence in the assessment
    financial_impact_estimate: float = 0.0
    regulatory_risk: str = "low"
    recommended_response_time: str = ""
    justification: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "technical_score": self.technical_score,
            "business_impact_score": self.business_impact_score,
            "composite_score": self.composite_score,
            "severity_level": self.severity_level,
            "confidence": self.confidence,
            "financial_impact_estimate": self.financial_impact_estimate,
            "regulatory_risk": self.regulatory_risk,
            "recommended_response_time": self.recommended_response_time,
            "justification": self.justification,
        }


class SeverityCalculator:
    """
    Calculates incident severity combining CVSS-based technical scoring
    with business impact assessment.
    """

    # Severity level thresholds (composite score)
    SEVERITY_THRESHOLDS = {
        "critical": 9.0,
        "high": 7.0,
        "medium": 4.0,
        "low": 1.0,
        "informational": 0.0,
    }

    # Response time targets per severity
    RESPONSE_TIMES = {
        "critical": "Immediate (< 15 minutes)",
        "high": "Urgent (< 1 hour)",
        "medium": "Priority (< 4 hours)",
        "low": "Standard (< 24 hours)",
        "informational": "Scheduled (next business day)",
    }

    # Business impact score weights
    WEIGHTS = {
        "technical": 0.35,
        "business": 0.65,
    }

    def calculate_severity(
        self,
        cvss_vector: Optional[CVSSVector] = None,
        business_impact: Optional[BusinessImpactFactors] = None,
    ) -> SeverityAssessment:
        """
        Calculate composite incident severity.

        Args:
            cvss_vector: CVSS-inspired technical severity vector.
            business_impact: Business impact assessment factors.

        Returns:
            Complete SeverityAssessment with scores and recommendations.
        """
        assessment = SeverityAssessment()
        justifications = []

        # Calculate technical score
        if cvss_vector:
            assessment.technical_score = cvss_vector.calculate_base_score()
            justifications.append(
                f"Technical severity (CVSS-based): {assessment.technical_score}/10.0"
            )
        else:
            assessment.technical_score = 5.0  # Default medium
            justifications.append("Technical severity: Default medium (no CVSS vector provided)")

        # Calculate business impact score
        if business_impact:
            assessment.business_impact_score = self._calculate_business_score(
                business_impact, justifications
            )
            assessment.financial_impact_estimate = self._estimate_financial_impact(
                business_impact
            )
            assessment.regulatory_risk = self._assess_regulatory_risk(business_impact)
        else:
            assessment.business_impact_score = 5.0
            justifications.append("Business impact: Default medium (no factors provided)")

        # Calculate composite score
        assessment.composite_score = round(
            (assessment.technical_score * self.WEIGHTS["technical"])
            + (assessment.business_impact_score * self.WEIGHTS["business"]),
            1,
        )

        # Determine severity level
        assessment.severity_level = self._score_to_severity(assessment.composite_score)

        # Override: regulatory notification always elevates to at least High
        if business_impact and business_impact.notification_required:
            if assessment.severity_level in ("medium", "low", "informational"):
                assessment.severity_level = "high"
                justifications.append(
                    "Severity elevated to HIGH: Regulatory notification obligation detected"
                )

        # Set response time
        assessment.recommended_response_time = self.RESPONSE_TIMES.get(
            assessment.severity_level, "Standard"
        )

        # Set confidence
        if cvss_vector and business_impact:
            assessment.confidence = "high"
        elif cvss_vector or business_impact:
            assessment.confidence = "medium"
        else:
            assessment.confidence = "low"

        assessment.justification = justifications
        return assessment

    def _calculate_business_score(
        self,
        bif: BusinessImpactFactors,
        justifications: List[str],
    ) -> float:
        """Calculate business impact score from impact factors."""
        score = 0.0

        # Data sensitivity scoring (0-3 points)
        data_scores = {
            DataClassification.PUBLIC: 0.0,
            DataClassification.INTERNAL: 0.5,
            DataClassification.CONFIDENTIAL: 1.5,
            DataClassification.RESTRICTED: 2.5,
            DataClassification.TOP_SECRET: 3.0,
        }
        data_score = data_scores.get(bif.data_classification, 1.0)
        score += data_score
        if data_score >= 2.0:
            justifications.append(
                f"Data sensitivity: {bif.data_classification.value} ({data_score}/3.0)"
            )

        # Records affected scoring (0-2 points)
        if bif.records_affected > 1_000_000:
            records_score = 2.0
        elif bif.records_affected > 100_000:
            records_score = 1.5
        elif bif.records_affected > 10_000:
            records_score = 1.0
        elif bif.records_affected > 1_000:
            records_score = 0.5
        else:
            records_score = 0.2
        score += records_score
        if bif.records_affected > 0:
            justifications.append(
                f"Records affected: {bif.records_affected:,} ({records_score}/2.0)"
            )

        # System criticality scoring (0-2 points)
        criticality_scores = {
            SystemCriticality.TIER_1_CRITICAL: 2.0,
            SystemCriticality.TIER_2_IMPORTANT: 1.5,
            SystemCriticality.TIER_3_STANDARD: 0.8,
            SystemCriticality.TIER_4_NON_CRITICAL: 0.3,
        }
        crit_score = criticality_scores.get(bif.system_criticality, 1.0)
        score += crit_score
        justifications.append(
            f"System criticality: {bif.system_criticality.value} ({crit_score}/2.0)"
        )

        # Regulatory exposure (0-2 points)
        reg_score = min(len(bif.regulatory_frameworks) * 0.5, 2.0)
        if bif.notification_required:
            reg_score = max(reg_score, 1.5)
        score += reg_score
        if bif.regulatory_frameworks:
            justifications.append(
                f"Regulatory exposure: {', '.join(bif.regulatory_frameworks)} ({reg_score}/2.0)"
            )

        # Reputational impact (0-1 point)
        rep_scores = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 1.0}
        rep_score = rep_scores.get(bif.customer_trust_impact, 0.2)
        if bif.media_coverage_likely:
            rep_score = max(rep_score, 0.8)
        score += rep_score

        # Normalize to 0-10 scale
        return round(min(score, 10.0), 1)

    def _estimate_financial_impact(self, bif: BusinessImpactFactors) -> float:
        """Estimate total financial impact in dollars."""
        impact = 0.0

        # Direct revenue loss
        impact += bif.revenue_impact_per_hour * bif.estimated_downtime_hours

        # Regulatory fines estimate
        fine_estimates = {
            "GDPR": min(bif.records_affected * 150, 20_000_000),      # Up to 4% revenue or 20M EUR
            "HIPAA": min(bif.records_affected * 100, 1_800_000),       # Up to $1.8M per violation
            "PCI-DSS": min(bif.records_affected * 50, 500_000),        # $5K-$100K/month + assessments
            "CCPA": min(bif.records_affected * 7500, 7_500_000),       # $2,500-$7,500 per violation
            "SOX": 5_000_000,                                          # Criminal penalties
        }
        for framework in bif.regulatory_frameworks:
            impact += fine_estimates.get(framework, 100_000)

        # Notification costs ($150-$200 per record industry average)
        if bif.notification_required and bif.records_affected > 0:
            impact += bif.records_affected * 165

        # Reputational/customer churn estimate
        if bif.customer_trust_impact == "critical":
            impact += bif.affected_customers * 500
        elif bif.customer_trust_impact == "high":
            impact += bif.affected_customers * 200

        return round(impact, 2)

    def _assess_regulatory_risk(self, bif: BusinessImpactFactors) -> str:
        """Assess overall regulatory risk level."""
        if not bif.regulatory_frameworks:
            return "low"

        risk_factors = 0
        if bif.notification_required:
            risk_factors += 2
        if bif.records_affected > 100_000:
            risk_factors += 2
        elif bif.records_affected > 10_000:
            risk_factors += 1
        if "GDPR" in bif.regulatory_frameworks:
            risk_factors += 2
        if "HIPAA" in bif.regulatory_frameworks:
            risk_factors += 2
        risk_factors += len(bif.regulatory_frameworks)

        if risk_factors >= 6:
            return "critical"
        elif risk_factors >= 4:
            return "high"
        elif risk_factors >= 2:
            return "medium"
        return "low"

    def _score_to_severity(self, score: float) -> str:
        """Convert numeric score to severity level string."""
        for level, threshold in self.SEVERITY_THRESHOLDS.items():
            if score >= threshold:
                return level
        return "informational"

    def quick_severity(
        self,
        data_classification: str = "internal",
        records_affected: int = 0,
        system_criticality: str = "tier_3_standard",
        regulatory_frameworks: Optional[List[str]] = None,
        notification_required: bool = False,
    ) -> SeverityAssessment:
        """
        Quick severity assessment from simple parameters.

        Convenience method for rapid triage without constructing
        full CVSS vectors and business impact objects.
        """
        bif = BusinessImpactFactors(
            data_classification=DataClassification(data_classification),
            records_affected=records_affected,
            system_criticality=SystemCriticality(system_criticality),
            regulatory_frameworks=regulatory_frameworks or [],
            notification_required=notification_required,
        )
        return self.calculate_severity(business_impact=bif)

    @staticmethod
    def get_severity_matrix() -> Dict[str, Dict[str, str]]:
        """Return the severity classification matrix for reference."""
        return {
            "critical": {
                "score_range": "9.0 - 10.0",
                "description": "Active, widespread compromise with confirmed data loss, "
                               "significant financial impact, or regulatory notification required",
                "response_time": "Immediate (< 15 minutes)",
                "examples": "Active ransomware, large-scale data breach, critical infrastructure compromise",
                "escalation": "CISO, CEO, Legal, Board (if public company)",
            },
            "high": {
                "score_range": "7.0 - 8.9",
                "description": "Confirmed security incident with potential for significant impact, "
                               "limited containment, or sensitive data exposure",
                "response_time": "Urgent (< 1 hour)",
                "examples": "Confirmed intrusion, targeted phishing with credential compromise, "
                            "insider threat with data access",
                "escalation": "CISO, VP Engineering, Legal",
            },
            "medium": {
                "score_range": "4.0 - 6.9",
                "description": "Security event requiring investigation, limited scope, "
                               "or successful containment of known threat",
                "response_time": "Priority (< 4 hours)",
                "examples": "Malware detection on single endpoint, policy violation, "
                            "unsuccessful attack attempt",
                "escalation": "Security Manager, IT Operations",
            },
            "low": {
                "score_range": "1.0 - 3.9",
                "description": "Minor security event with minimal impact, "
                               "routine investigation required",
                "response_time": "Standard (< 24 hours)",
                "examples": "Spam campaign, low-severity vulnerability exploitation attempt, "
                            "single failed login burst",
                "escalation": "SOC Team Lead",
            },
            "informational": {
                "score_range": "0.0 - 0.9",
                "description": "Security observation for awareness, no action required",
                "response_time": "Scheduled (next business day)",
                "examples": "Informational IDS alert, routine policy exception, "
                            "security tool notification",
                "escalation": "SOC Analyst",
            },
        }
