"""
Risk Calculator - Quantitative risk assessment for IT audit engagements.

Implements a 5x5 likelihood x impact risk matrix methodology to calculate
risk scores at the control, finding, audit area, and engagement levels.
Also computes compliance percentages and generates risk distribution metrics.

Risk Score = Likelihood x Impact

Likelihood Scale:
    1 = Rare (< 5% probability in 12 months)
    2 = Unlikely (5-20% probability)
    3 = Possible (20-50% probability)
    4 = Likely (50-80% probability)
    5 = Almost Certain (> 80% probability)

Impact Scale:
    1 = Negligible (minimal operational impact, no data loss)
    2 = Minor (limited operational disruption, minor data exposure)
    3 = Moderate (significant disruption, regulated data exposure)
    4 = Major (extended outage, large-scale data breach, regulatory fines)
    5 = Severe (existential threat, critical infrastructure failure, criminal liability)

Severity Mapping:
    20-25 = Critical (immediate executive attention required)
    12-19 = High (requires priority remediation within 30 days)
    6-11  = Medium (remediation within 90 days)
    2-5   = Low (remediation within 180 days)
    1     = Informational (noted for awareness, no action required)
"""

from typing import Optional
from src.models import (
    AuditEngagement,
    AuditArea,
    Control,
    Finding,
    RiskRating,
    ControlStatus,
    FindingSeverity,
)


# Severity classification thresholds
SEVERITY_THRESHOLDS = {
    "critical": (20, 25),
    "high": (12, 19),
    "medium": (6, 11),
    "low": (2, 5),
    "informational": (1, 1),
}

# Default likelihood mapping based on control status
CONTROL_STATUS_LIKELIHOOD = {
    ControlStatus.INEFFECTIVE.value: 4,
    ControlStatus.PARTIALLY_EFFECTIVE.value: 3,
    ControlStatus.EFFECTIVE.value: 1,
    ControlStatus.NOT_APPLICABLE.value: 0,
    ControlStatus.NOT_TESTED.value: 3,  # Assume moderate risk if untested
}

# Default impact mapping based on risk weight
RISK_WEIGHT_IMPACT = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
}

# Severity to numeric score for averaging and aggregation
SEVERITY_NUMERIC = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "informational": 1,
}

# Remediation timeline by severity
REMEDIATION_TIMELINES = {
    "critical": "Immediate - within 7 days",
    "high": "Priority - within 30 days",
    "medium": "Standard - within 90 days",
    "low": "Planned - within 180 days",
    "informational": "No action required - noted for awareness",
}


class RiskCalculator:
    """
    Calculates risk scores, compliance percentages, and risk distributions
    for IT audit engagements.
    """

    def __init__(self, engagement: AuditEngagement):
        """
        Initialize the risk calculator with an engagement.

        Args:
            engagement: The AuditEngagement to calculate risk for.
        """
        self.engagement = engagement

    @staticmethod
    def calculate_risk_score(likelihood: int, impact: int) -> RiskRating:
        """
        Calculate a risk score from likelihood and impact values.

        Args:
            likelihood: Probability score (1-5).
            impact: Impact score (1-5).

        Returns:
            RiskRating with computed score and severity.
        """
        return RiskRating(likelihood=likelihood, impact=impact)

    @staticmethod
    def score_to_severity(score: int) -> str:
        """
        Map a numeric risk score (1-25) to a severity classification.

        Args:
            score: Numeric risk score.

        Returns:
            Severity classification string.
        """
        if score >= 20:
            return FindingSeverity.CRITICAL.value
        elif score >= 12:
            return FindingSeverity.HIGH.value
        elif score >= 6:
            return FindingSeverity.MEDIUM.value
        elif score >= 2:
            return FindingSeverity.LOW.value
        else:
            return FindingSeverity.INFORMATIONAL.value

    @staticmethod
    def severity_to_likelihood(severity: str) -> int:
        """
        Estimate a default likelihood based on finding severity.

        Args:
            severity: Severity classification string.

        Returns:
            Estimated likelihood score (1-5).
        """
        mapping = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "informational": 1,
        }
        return mapping.get(severity.lower(), 3)

    @staticmethod
    def severity_to_impact(severity: str) -> int:
        """
        Estimate a default impact based on finding severity.

        Args:
            severity: Severity classification string.

        Returns:
            Estimated impact score (1-5).
        """
        mapping = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "informational": 1,
        }
        return mapping.get(severity.lower(), 3)

    def calculate_control_risk(self, control) -> dict:
        """
        Calculate risk for a single control based on its status and weight.

        Args:
            control: Control object or dictionary.

        Returns:
            Dictionary with risk assessment details.
        """
        status = control.status if hasattr(control, "status") else control.get("status", "not_tested")
        risk_weight = control.risk_weight if hasattr(control, "risk_weight") else control.get("risk_weight", 3)
        ctrl_id = control.control_id if hasattr(control, "control_id") else control.get("control_id", "")
        title = control.title if hasattr(control, "title") else control.get("title", "")

        likelihood = CONTROL_STATUS_LIKELIHOOD.get(status, 3)
        impact = RISK_WEIGHT_IMPACT.get(risk_weight, 3)

        # Not applicable controls have zero risk
        if status == ControlStatus.NOT_APPLICABLE.value:
            return {
                "control_id": ctrl_id,
                "title": title,
                "status": status,
                "likelihood": 0,
                "impact": 0,
                "risk_score": 0,
                "severity": "not_applicable",
                "risk_weight": risk_weight,
            }

        score = likelihood * impact
        severity = self.score_to_severity(score)

        return {
            "control_id": ctrl_id,
            "title": title,
            "status": status,
            "likelihood": likelihood,
            "impact": impact,
            "risk_score": score,
            "severity": severity,
            "risk_weight": risk_weight,
        }

    def calculate_finding_risk(self, finding) -> dict:
        """
        Calculate or retrieve the risk rating for a finding.

        If the finding already has a risk_rating, use it. Otherwise,
        derive risk from the finding's severity classification.

        Args:
            finding: Finding object or dictionary.

        Returns:
            Dictionary with risk assessment details.
        """
        finding_id = finding.finding_id if hasattr(finding, "finding_id") else finding.get("finding_id", "")
        title = finding.title if hasattr(finding, "title") else finding.get("title", "")
        severity = finding.severity if hasattr(finding, "severity") else finding.get("severity", "medium")
        risk_rating = finding.risk_rating if hasattr(finding, "risk_rating") else finding.get("risk_rating")

        if risk_rating and isinstance(risk_rating, dict):
            likelihood = risk_rating.get("likelihood", self.severity_to_likelihood(severity))
            impact = risk_rating.get("impact", self.severity_to_impact(severity))
        else:
            likelihood = self.severity_to_likelihood(severity)
            impact = self.severity_to_impact(severity)

        score = likelihood * impact
        computed_severity = self.score_to_severity(score)

        return {
            "finding_id": finding_id,
            "title": title,
            "severity": severity,
            "likelihood": likelihood,
            "impact": impact,
            "risk_score": score,
            "computed_severity": computed_severity,
            "remediation_timeline": REMEDIATION_TIMELINES.get(severity, "Standard - within 90 days"),
        }

    def calculate_area_compliance(self, area) -> dict:
        """
        Calculate compliance percentage and risk metrics for an audit area.

        Compliance percentage is based on the ratio of effective controls
        to total tested controls (excluding N/A and untested).

        Args:
            area: AuditArea object or dictionary.

        Returns:
            Dictionary with compliance and risk metrics for the area.
        """
        area_name = area.name if hasattr(area, "name") else area.get("name", "Unknown")
        controls = area.controls if hasattr(area, "controls") else area.get("controls", [])
        findings = area.findings if hasattr(area, "findings") else area.get("findings", [])

        total_controls = len(controls)
        if total_controls == 0:
            return {
                "area_name": area_name,
                "total_controls": 0,
                "tested_controls": 0,
                "effective_controls": 0,
                "compliance_pct": 0.0,
                "average_risk_score": 0.0,
                "max_risk_score": 0,
                "finding_count": len(findings),
                "control_risks": [],
                "finding_risks": [],
            }

        # Calculate per-control risk
        control_risks = []
        effective_count = 0
        partially_count = 0
        tested_count = 0
        risk_scores = []

        for ctrl in controls:
            status = ctrl.status if hasattr(ctrl, "status") else ctrl.get("status", "not_tested")
            ctrl_risk = self.calculate_control_risk(ctrl)
            control_risks.append(ctrl_risk)

            if status != ControlStatus.NOT_TESTED.value and status != ControlStatus.NOT_APPLICABLE.value:
                tested_count += 1
                if ctrl_risk["risk_score"] > 0:
                    risk_scores.append(ctrl_risk["risk_score"])

            if status == ControlStatus.EFFECTIVE.value:
                effective_count += 1
            elif status == ControlStatus.PARTIALLY_EFFECTIVE.value:
                partially_count += 1

        # Compliance: effective + partial (at 50% weight) / tested
        compliance_numerator = effective_count + (partially_count * 0.5)
        compliance_pct = (compliance_numerator / tested_count * 100) if tested_count > 0 else 0.0

        # Calculate per-finding risk
        finding_risks = [self.calculate_finding_risk(f) for f in findings]

        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        max_risk = max(risk_scores) if risk_scores else 0

        return {
            "area_name": area_name,
            "total_controls": total_controls,
            "tested_controls": tested_count,
            "effective_controls": effective_count,
            "partially_effective_controls": partially_count,
            "compliance_pct": round(compliance_pct, 1),
            "average_risk_score": round(avg_risk, 1),
            "max_risk_score": max_risk,
            "finding_count": len(findings),
            "control_risks": control_risks,
            "finding_risks": finding_risks,
        }

    def calculate_engagement_risk(self) -> dict:
        """
        Calculate comprehensive risk metrics for the entire engagement.

        Returns:
            Dictionary with engagement-level risk and compliance metrics.
        """
        area_results = []
        all_control_risks = []
        all_finding_risks = []
        total_effective = 0
        total_partial = 0
        total_tested = 0
        total_controls = 0

        for area in self.engagement.audit_areas:
            area_result = self.calculate_area_compliance(area)
            area_results.append(area_result)
            all_control_risks.extend(area_result["control_risks"])
            all_finding_risks.extend(area_result["finding_risks"])
            total_effective += area_result["effective_controls"]
            total_partial += area_result.get("partially_effective_controls", 0)
            total_tested += area_result["tested_controls"]
            total_controls += area_result["total_controls"]

        # Overall compliance
        compliance_numerator = total_effective + (total_partial * 0.5)
        overall_compliance = (compliance_numerator / total_tested * 100) if total_tested > 0 else 0.0

        # Risk score aggregation
        all_risk_scores = [cr["risk_score"] for cr in all_control_risks if cr["risk_score"] > 0]
        avg_risk = sum(all_risk_scores) / len(all_risk_scores) if all_risk_scores else 0.0
        max_risk = max(all_risk_scores) if all_risk_scores else 0

        # Risk distribution (for heat map)
        risk_distribution = self._build_risk_distribution(all_control_risks)

        # Finding severity distribution
        finding_severity_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for fr in all_finding_risks:
            sev = fr.get("severity", "medium")
            if sev in finding_severity_dist:
                finding_severity_dist[sev] += 1

        # Overall risk rating
        overall_severity = self.score_to_severity(int(round(avg_risk))) if avg_risk > 0 else "informational"

        # Update engagement metrics
        self.engagement.overall_risk_score = round(avg_risk, 1)
        self.engagement.overall_compliance_pct = round(overall_compliance, 1)

        return {
            "engagement_id": self.engagement.engagement_id,
            "overall_compliance_pct": round(overall_compliance, 1),
            "overall_risk_score": round(avg_risk, 1),
            "max_risk_score": max_risk,
            "overall_severity": overall_severity,
            "total_controls": total_controls,
            "total_tested": total_tested,
            "total_effective": total_effective,
            "total_findings": len(all_finding_risks),
            "area_results": area_results,
            "risk_distribution": risk_distribution,
            "finding_severity_distribution": finding_severity_dist,
            "all_finding_risks": all_finding_risks,
            "remediation_summary": self._build_remediation_summary(all_finding_risks),
        }

    def _build_risk_distribution(self, control_risks: list) -> dict:
        """
        Build a 5x5 risk distribution matrix for heat map visualization.

        Returns:
            Dictionary with the risk matrix and severity counts.
        """
        # Initialize 5x5 matrix (likelihood x impact)
        matrix = [[0 for _ in range(5)] for _ in range(5)]

        for cr in control_risks:
            l = cr.get("likelihood", 0)
            i = cr.get("impact", 0)
            if 1 <= l <= 5 and 1 <= i <= 5:
                matrix[l - 1][i - 1] += 1

        # Severity counts from control risks
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for cr in control_risks:
            sev = cr.get("severity", "informational")
            if sev in severity_counts:
                severity_counts[sev] += 1

        return {
            "matrix": matrix,
            "likelihood_labels": ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
            "impact_labels": ["Negligible", "Minor", "Moderate", "Major", "Severe"],
            "severity_counts": severity_counts,
        }

    def _build_remediation_summary(self, finding_risks: list) -> list:
        """
        Build a prioritized remediation roadmap from finding risks.

        Returns:
            Sorted list of findings with remediation priorities.
        """
        roadmap = []
        for fr in finding_risks:
            roadmap.append({
                "finding_id": fr["finding_id"],
                "title": fr["title"],
                "severity": fr["severity"],
                "risk_score": fr["risk_score"],
                "remediation_timeline": fr["remediation_timeline"],
                "priority_rank": SEVERITY_NUMERIC.get(fr["severity"], 3),
            })

        # Sort by priority rank (highest first), then by risk score
        roadmap.sort(key=lambda x: (-x["priority_rank"], -x["risk_score"]))

        # Assign priority numbers
        for i, item in enumerate(roadmap, 1):
            item["priority_order"] = i

        return roadmap

    def generate_risk_heat_map_data(self) -> dict:
        """
        Generate data suitable for rendering a risk heat map.

        Returns:
            Dictionary with heat map cell data including colors and counts.
        """
        engagement_risk = self.calculate_engagement_risk()
        matrix = engagement_risk["risk_distribution"]["matrix"]

        # Define color mapping for each cell based on risk score
        heat_map = []
        for l_idx in range(5):
            row = []
            for i_idx in range(5):
                score = (l_idx + 1) * (i_idx + 1)
                severity = self.score_to_severity(score)
                color_map = {
                    "critical": "#dc3545",
                    "high": "#fd7e14",
                    "medium": "#ffc107",
                    "low": "#28a745",
                    "informational": "#17a2b8",
                }
                row.append({
                    "likelihood": l_idx + 1,
                    "impact": i_idx + 1,
                    "score": score,
                    "severity": severity,
                    "color": color_map.get(severity, "#6c757d"),
                    "count": matrix[l_idx][i_idx],
                })
            heat_map.append(row)

        return {
            "heat_map": heat_map,
            "likelihood_labels": ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
            "impact_labels": ["Negligible", "Minor", "Moderate", "Major", "Severe"],
        }
