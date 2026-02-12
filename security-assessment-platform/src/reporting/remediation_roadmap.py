"""
Remediation Roadmap Generator - Prioritized action plan.

Generates a structured remediation plan organized into three phases:
    - Quick Wins (0-30 days): Low-effort, high-impact fixes
    - Short-term (30-90 days): Moderate effort improvements
    - Long-term (90-365 days): Strategic security enhancements

Each remediation item includes effort estimation, responsible party
suggestions, and dependency mapping.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


# Effort estimation rules based on finding characteristics
EFFORT_RULES = {
    # Finding patterns that are quick wins (configuration changes)
    "quick_win_patterns": [
        "header",
        "cookie",
        "x-frame",
        "x-content-type",
        "hsts",
        "referrer-policy",
        "permissions-policy",
        "information disclosure",
        "banner",
    ],
    # Finding patterns requiring short-term effort
    "short_term_patterns": [
        "ssl",
        "tls",
        "certificate",
        "cors",
        "csp",
        "spf",
        "dmarc",
        "dnssec",
        "firewall",
        "access control",
    ],
    # Finding patterns requiring long-term strategic changes
    "long_term_patterns": [
        "architecture",
        "segmentation",
        "authentication",
        "encryption",
        "database",
        "compliance",
        "policy",
        "training",
        "monitoring",
    ],
}


class RemediationItem:
    """A single remediation action item."""

    def __init__(
        self,
        finding_id: str = "",
        title: str = "",
        description: str = "",
        phase: str = "short_term",
        priority: int = 0,
        severity: str = "medium",
        cvss_score: float = 0.0,
        effort: str = "medium",
        estimated_hours: int = 0,
        responsible_team: str = "",
        remediation_steps: str = "",
        dependencies: List[str] = None,
        status: str = "pending",
        compliance_refs: List[str] = None,
    ):
        self.finding_id = finding_id
        self.title = title
        self.description = description
        self.phase = phase
        self.priority = priority
        self.severity = severity
        self.cvss_score = cvss_score
        self.effort = effort
        self.estimated_hours = estimated_hours
        self.responsible_team = responsible_team
        self.remediation_steps = remediation_steps
        self.dependencies = dependencies or []
        self.status = status
        self.compliance_refs = compliance_refs or []

    def to_dict(self) -> Dict:
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "phase": self.phase,
            "priority": self.priority,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "effort": self.effort,
            "estimated_hours": self.estimated_hours,
            "responsible_team": self.responsible_team,
            "remediation_steps": self.remediation_steps,
            "dependencies": self.dependencies,
            "status": self.status,
            "compliance_refs": self.compliance_refs,
        }


class RemediationRoadmapGenerator:
    """
    Generates a prioritized remediation roadmap from assessment findings.

    Categorizes findings into three phases based on effort, impact,
    and dependency analysis:
    - Quick Wins: Configuration changes, header additions, simple fixes
    - Short-term: Certificate renewals, policy implementations, tool deployments
    - Long-term: Architecture changes, process implementations, training programs

    Example:
        generator = RemediationRoadmapGenerator()
        html = generator.generate(
            findings=all_findings,
            risk_data=risk_assessment.to_dict(),
            compliance_data={...},
        )
        generator.save(html, "reports/remediation_roadmap.html")
    """

    def __init__(self, template_dir: Optional[str] = None):
        """Initialize the remediation roadmap generator."""
        self.template_dir = template_dir or TEMPLATE_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html"]),
        )

    def generate(
        self,
        findings: List[Dict],
        risk_data: Optional[Dict] = None,
        compliance_data: Optional[Dict] = None,
        organization: str = "Organization",
    ) -> str:
        """
        Generate the remediation roadmap HTML report.

        Args:
            findings: List of all finding dictionaries.
            risk_data: Optional risk assessment data.
            compliance_data: Optional compliance data.
            organization: Organization name.

        Returns:
            Rendered HTML string.
        """
        risk_data = risk_data or {}
        compliance_data = compliance_data or {}

        # Classify findings into phases
        roadmap = self._classify_findings(findings)

        # Add compliance-driven items
        compliance_items = self._compliance_remediation(compliance_data)
        for item in compliance_items:
            roadmap[item.phase].append(item)

        # Sort each phase by priority
        for phase in roadmap:
            roadmap[phase].sort(key=lambda x: x.priority)

        # Compute summary
        summary = self._compute_summary(roadmap)

        context = {
            "report_title": "Security Remediation Roadmap",
            "organization": organization,
            "report_date": datetime.now().strftime("%B %d, %Y"),
            "report_id": f"SA-REM-{datetime.now().strftime('%Y%m%d-%H%M')}",
            "quick_wins": [i.to_dict() for i in roadmap["quick_wins"]],
            "short_term": [i.to_dict() for i in roadmap["short_term"]],
            "long_term": [i.to_dict() for i in roadmap["long_term"]],
            "summary": summary,
            "risk_data": risk_data,
            "generated_at": datetime.now().isoformat(),
        }

        try:
            template = self.env.get_template("roadmap.html")
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering roadmap template: {e}")
            return self._fallback_report(context)

    def _classify_findings(
        self, findings: List[Dict]
    ) -> Dict[str, List[RemediationItem]]:
        """
        Classify findings into remediation phases.

        Uses severity, finding type, and pattern matching to determine
        the appropriate phase and effort level for each finding.
        """
        roadmap = {"quick_wins": [], "short_term": [], "long_term": []}
        priority_counter = {"quick_wins": 0, "short_term": 0, "long_term": 0}

        for finding in findings:
            title_lower = finding.get("title", "").lower()
            desc_lower = finding.get("description", "").lower()
            combined = f"{title_lower} {desc_lower}"
            severity = finding.get("severity", "info").lower()
            cvss = finding.get("cvss_score", 0)

            # Determine phase
            phase = "short_term"  # default

            for pattern in EFFORT_RULES["quick_win_patterns"]:
                if pattern in combined:
                    phase = "quick_wins"
                    break

            if phase != "quick_wins":
                for pattern in EFFORT_RULES["long_term_patterns"]:
                    if pattern in combined:
                        phase = "long_term"
                        break

            # Override: critical findings with simple fixes = quick wins
            if severity == "critical" and phase == "quick_wins":
                phase = "quick_wins"
            # Override: info findings = long term (nice to have)
            elif severity == "info":
                phase = "long_term"

            priority_counter[phase] += 1

            # Effort estimation
            if phase == "quick_wins":
                effort = "low"
                estimated_hours = 2
            elif phase == "short_term":
                effort = "medium"
                estimated_hours = 8
            else:
                effort = "high"
                estimated_hours = 40

            # Team assignment heuristic
            if "network" in combined or "port" in combined or "firewall" in combined:
                team = "Network Engineering"
            elif "web" in combined or "header" in combined or "cookie" in combined:
                team = "Web Development / DevOps"
            elif "ssl" in combined or "certificate" in combined or "tls" in combined:
                team = "Infrastructure / DevOps"
            elif "dns" in combined or "spf" in combined or "dmarc" in combined:
                team = "DNS / Email Administration"
            elif "compliance" in combined or "policy" in combined:
                team = "Security Governance / GRC"
            else:
                team = "Information Security"

            item = RemediationItem(
                finding_id=finding.get("id", f"REM-{priority_counter[phase]:03d}"),
                title=finding.get("title", ""),
                description=finding.get("description", ""),
                phase=phase,
                priority=priority_counter[phase],
                severity=severity,
                cvss_score=cvss,
                effort=effort,
                estimated_hours=estimated_hours,
                responsible_team=team,
                remediation_steps=finding.get("remediation", ""),
                compliance_refs=finding.get("compliance_refs", []),
                status="pending",
            )

            roadmap[phase].append(item)

        return roadmap

    def _compliance_remediation(
        self, compliance_data: Dict
    ) -> List[RemediationItem]:
        """Generate remediation items from compliance gaps."""
        items = []

        for framework_key in ("iso27001", "pci_dss", "nist_csf"):
            fw = compliance_data.get(framework_key, {})
            if not fw:
                continue

            controls = fw.get("controls", fw.get(
                "requirements", fw.get("subcategories", [])
            ))

            for control in controls:
                status = control.get("status", "not_assessed")
                if status in ("fail", "partial") and control.get("remediation"):
                    control_id = control.get(
                        "control_id",
                        control.get("requirement_id",
                            control.get("subcategory_id", ""))
                    )
                    control_name = control.get(
                        "control_name",
                        control.get("requirement_name",
                            control.get("subcategory_name", ""))
                    )

                    phase = "short_term" if status == "fail" else "long_term"

                    items.append(RemediationItem(
                        finding_id=f"COMP-{control_id}",
                        title=f"Compliance Gap: {control_id} - {control_name}",
                        description=control.get("description", ""),
                        phase=phase,
                        severity="high" if status == "fail" else "medium",
                        cvss_score=7.0 if status == "fail" else 4.0,
                        effort="medium" if status == "fail" else "high",
                        estimated_hours=16 if status == "fail" else 40,
                        responsible_team="Security Governance / GRC",
                        remediation_steps=control.get("remediation", ""),
                        compliance_refs=[control_id],
                        status="pending",
                    ))

        return items

    def _compute_summary(
        self, roadmap: Dict[str, List[RemediationItem]]
    ) -> Dict:
        """Compute roadmap summary statistics."""
        total_items = sum(len(v) for v in roadmap.values())
        total_hours = sum(
            item.estimated_hours
            for phase_items in roadmap.values()
            for item in phase_items
        )

        return {
            "total_items": total_items,
            "quick_wins_count": len(roadmap["quick_wins"]),
            "short_term_count": len(roadmap["short_term"]),
            "long_term_count": len(roadmap["long_term"]),
            "total_estimated_hours": total_hours,
            "estimated_days": round(total_hours / 8, 1),
            "phase_breakdown": {
                "quick_wins": {
                    "count": len(roadmap["quick_wins"]),
                    "hours": sum(i.estimated_hours for i in roadmap["quick_wins"]),
                    "timeframe": "0-30 days",
                    "label": "Quick Wins",
                },
                "short_term": {
                    "count": len(roadmap["short_term"]),
                    "hours": sum(i.estimated_hours for i in roadmap["short_term"]),
                    "timeframe": "30-90 days",
                    "label": "Short-Term",
                },
                "long_term": {
                    "count": len(roadmap["long_term"]),
                    "hours": sum(i.estimated_hours for i in roadmap["long_term"]),
                    "timeframe": "90-365 days",
                    "label": "Long-Term",
                },
            },
        }

    def _fallback_report(self, context: Dict) -> str:
        """Generate basic roadmap when template is unavailable."""
        phase_sections = ""
        for phase_key, phase_label, timeframe in [
            ("quick_wins", "Quick Wins", "0-30 days"),
            ("short_term", "Short-Term Actions", "30-90 days"),
            ("long_term", "Long-Term Strategy", "90-365 days"),
        ]:
            items = context.get(phase_key, [])
            items_html = ""
            for item in items:
                items_html += f"""
                <div style="border:1px solid #e2e8f0; padding:12px; margin:8px 0; border-radius:6px;">
                    <strong>{item.get('title','')}</strong>
                    <span style="float:right; padding:2px 8px; border-radius:12px; background:#f1f5f9; font-size:0.85em;">{item.get('effort','')} effort | ~{item.get('estimated_hours',0)}h</span>
                    <p style="margin:5px 0; color:#475569;">{item.get('remediation_steps','')}</p>
                    <small>Team: {item.get('responsible_team','')} | Severity: {item.get('severity','')}</small>
                </div>"""

            phase_sections += f"""
            <h2>{phase_label} ({timeframe}) - {len(items)} items</h2>
            {items_html if items_html else '<p style="color:#94a3b8;">No items in this phase.</p>'}"""

        summary = context.get("summary", {})
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{context['report_title']}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; color: #1e293b; }}
        .header {{ background: linear-gradient(135deg, #0f766e, #14b8a6); color: white; padding: 30px; border-radius: 12px; }}
        .summary {{ display: flex; gap: 15px; margin: 20px 0; }}
        .summary-card {{ flex:1; background:#f8fafc; padding:20px; border-radius:8px; text-align:center; }}
        .summary-card .num {{ font-size: 2em; font-weight: bold; color: #0f766e; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{context['report_title']}</h1>
        <p>Organization: {context['organization']} | Date: {context['report_date']}</p>
    </div>
    <div class="summary">
        <div class="summary-card"><div class="num">{summary.get('total_items', 0)}</div>Total Items</div>
        <div class="summary-card"><div class="num">{summary.get('quick_wins_count', 0)}</div>Quick Wins</div>
        <div class="summary-card"><div class="num">{summary.get('short_term_count', 0)}</div>Short-Term</div>
        <div class="summary-card"><div class="num">{summary.get('long_term_count', 0)}</div>Long-Term</div>
    </div>
    {phase_sections}
    <hr><p><em>Report ID: {context['report_id']}</em></p>
</body>
</html>"""

    def save(self, html_content: str, output_path: str):
        """Save the roadmap report to a file."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Remediation roadmap saved to: {output_path}")
