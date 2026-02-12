"""
Report Generator - Professional HTML audit report generation using Jinja2.

Generates comprehensive audit reports including:
- Executive summary with key metrics and risk posture
- Detailed findings with evidence references and recommendations
- Risk heat map with color-coded severity visualization
- Compliance dashboard per audit area
- Prioritized remediation roadmap with effort and timeline estimates
"""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models import AuditEngagement, FindingSeverity
from src.risk_calculator import RiskCalculator


# Default template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class AuditReporter:
    """
    Generates professional HTML audit reports from engagement data.

    Uses Jinja2 templates to render reports with executive summaries,
    detailed findings, risk heat maps, and remediation roadmaps.
    """

    def __init__(
        self,
        engagement: AuditEngagement,
        template_dir: Optional[str] = None,
    ):
        """
        Initialize the reporter.

        Args:
            engagement: The AuditEngagement to report on.
            template_dir: Custom template directory path. Defaults to
                         the project's templates/ directory.
        """
        self.engagement = engagement
        self.risk_calculator = RiskCalculator(engagement)
        self.template_dir = Path(template_dir) if template_dir else TEMPLATES_DIR

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Register custom filters
        self.env.filters["severity_color"] = self._severity_color
        self.env.filters["severity_badge"] = self._severity_badge
        self.env.filters["status_icon"] = self._status_icon
        self.env.filters["pct_color"] = self._compliance_color

    @staticmethod
    def _severity_color(severity: str) -> str:
        """Map severity to CSS color code."""
        colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
            "informational": "#17a2b8",
        }
        return colors.get(severity.lower(), "#6c757d")

    @staticmethod
    def _severity_badge(severity: str) -> str:
        """Generate an HTML badge span for a severity level."""
        colors = {
            "critical": "background-color:#dc3545;color:#fff",
            "high": "background-color:#fd7e14;color:#fff",
            "medium": "background-color:#ffc107;color:#212529",
            "low": "background-color:#28a745;color:#fff",
            "informational": "background-color:#17a2b8;color:#fff",
        }
        style = colors.get(severity.lower(), "background-color:#6c757d;color:#fff")
        return f'<span style="{style};padding:2px 8px;border-radius:4px;font-size:0.85em;font-weight:600">{severity.upper()}</span>'

    @staticmethod
    def _status_icon(status: str) -> str:
        """Map control status to an icon/symbol."""
        icons = {
            "effective": "&#10004;",           # Checkmark
            "partially_effective": "&#9888;",  # Warning
            "ineffective": "&#10008;",         # X mark
            "not_applicable": "&#8212;",       # Em dash
            "not_tested": "&#63;",             # Question mark
        }
        return icons.get(status, "&#63;")

    @staticmethod
    def _compliance_color(pct: float) -> str:
        """Map compliance percentage to a color."""
        if pct >= 80:
            return "#28a745"  # Green
        elif pct >= 60:
            return "#ffc107"  # Yellow
        elif pct >= 40:
            return "#fd7e14"  # Orange
        else:
            return "#dc3545"  # Red

    def build_report_context(self) -> dict:
        """
        Build the complete data context for the report template.

        Returns:
            Dictionary containing all data needed to render the report.
        """
        # Calculate engagement-wide risk metrics
        risk_data = self.risk_calculator.calculate_engagement_risk()
        heat_map_data = self.risk_calculator.generate_risk_heat_map_data()

        # Collect all findings across areas
        all_findings = []
        for area in self.engagement.audit_areas:
            findings = area.findings if hasattr(area, "findings") else area.get("findings", [])
            for f in findings:
                finding_data = f.to_dict() if hasattr(f, "to_dict") else f
                area_name = area.name if hasattr(area, "name") else area.get("name", "")
                finding_data["audit_area"] = area_name
                all_findings.append(finding_data)

        # Sort findings by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
        all_findings.sort(key=lambda x: severity_order.get(x.get("severity", "medium"), 2))

        # Build area summaries for the compliance dashboard
        area_summaries = []
        for area_result in risk_data.get("area_results", []):
            area_summaries.append({
                "name": area_result["area_name"],
                "total_controls": area_result["total_controls"],
                "tested_controls": area_result["tested_controls"],
                "effective_controls": area_result["effective_controls"],
                "compliance_pct": area_result["compliance_pct"],
                "finding_count": area_result["finding_count"],
                "average_risk_score": area_result["average_risk_score"],
                "max_risk_score": area_result["max_risk_score"],
            })

        # Build executive summary metrics
        exec_summary = {
            "overall_compliance_pct": risk_data["overall_compliance_pct"],
            "overall_risk_score": risk_data["overall_risk_score"],
            "overall_severity": risk_data["overall_severity"],
            "total_controls_tested": risk_data["total_tested"],
            "total_controls": risk_data["total_controls"],
            "total_findings": risk_data["total_findings"],
            "critical_findings": risk_data["finding_severity_distribution"]["critical"],
            "high_findings": risk_data["finding_severity_distribution"]["high"],
            "medium_findings": risk_data["finding_severity_distribution"]["medium"],
            "low_findings": risk_data["finding_severity_distribution"]["low"],
            "informational_findings": risk_data["finding_severity_distribution"]["informational"],
            "total_areas": len(self.engagement.audit_areas),
        }

        context = {
            "engagement": {
                "id": self.engagement.engagement_id,
                "name": self.engagement.name,
                "client": self.engagement.client,
                "lead_auditor": self.engagement.lead_auditor,
                "audit_team": self.engagement.audit_team,
                "status": self.engagement.status,
                "methodology": self.engagement.methodology,
                "scope_description": self.engagement.scope_description,
                "objectives": self.engagement.objectives,
                "start_date": self.engagement.start_date,
                "end_date": self.engagement.end_date or date.today().isoformat(),
                "report_date": date.today().isoformat(),
            },
            "exec_summary": exec_summary,
            "findings": all_findings,
            "area_summaries": area_summaries,
            "heat_map": heat_map_data,
            "remediation_roadmap": risk_data.get("remediation_summary", []),
            "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return context

    def generate_html_report(self, output_path: str, template_name: str = "audit_report.html") -> str:
        """
        Generate an HTML audit report and write it to a file.

        Args:
            output_path: File path for the output HTML report.
            template_name: Name of the Jinja2 template to use.

        Returns:
            Absolute path to the generated report file.
        """
        # Build the report context
        context = self.build_report_context()

        # Load and render the template
        template = self.env.get_template(template_name)
        html_content = template.render(**context)

        # Ensure output directory exists
        output_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(output_dir, exist_ok=True)

        # Write the report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return os.path.abspath(output_path)

    def generate_executive_summary_text(self) -> str:
        """
        Generate a plain-text executive summary suitable for
        console output or inclusion in other documents.

        Returns:
            Formatted executive summary text.
        """
        context = self.build_report_context()
        es = context["exec_summary"]
        eng = context["engagement"]

        lines = [
            "=" * 70,
            "EXECUTIVE SUMMARY",
            "=" * 70,
            "",
            f"Engagement:    {eng['name']}",
            f"Client:        {eng['client']}",
            f"Lead Auditor:  {eng['lead_auditor']}",
            f"Report Date:   {context['report_generated_at']}",
            "",
            "-" * 70,
            "OVERALL RISK POSTURE",
            "-" * 70,
            "",
            f"  Overall Compliance:     {es['overall_compliance_pct']:.1f}%",
            f"  Overall Risk Score:     {es['overall_risk_score']:.1f} / 25.0",
            f"  Risk Severity:          {es['overall_severity'].upper()}",
            "",
            f"  Controls Tested:        {es['total_controls_tested']} / {es['total_controls']}",
            f"  Audit Areas Covered:    {es['total_areas']}",
            "",
            "-" * 70,
            "FINDINGS SUMMARY",
            "-" * 70,
            "",
            f"  Total Findings:         {es['total_findings']}",
            f"  Critical:               {es['critical_findings']}",
            f"  High:                   {es['high_findings']}",
            f"  Medium:                 {es['medium_findings']}",
            f"  Low:                    {es['low_findings']}",
            f"  Informational:          {es['informational_findings']}",
            "",
            "-" * 70,
            "COMPLIANCE BY AUDIT AREA",
            "-" * 70,
            "",
        ]

        for area in context["area_summaries"]:
            bar_len = int(area["compliance_pct"] / 5)
            bar = "#" * bar_len + "." * (20 - bar_len)
            lines.append(
                f"  {area['name']:<30s} [{bar}] {area['compliance_pct']:5.1f}%  "
                f"({area['finding_count']} findings)"
            )

        lines.extend([
            "",
            "-" * 70,
            "REMEDIATION PRIORITIES",
            "-" * 70,
            "",
        ])

        for item in context["remediation_roadmap"][:10]:
            lines.append(
                f"  {item['priority_order']:2d}. [{item['severity'].upper():^13s}] "
                f"{item['title']}"
            )
            lines.append(
                f"      Timeline: {item['remediation_timeline']}"
            )

        lines.extend(["", "=" * 70])

        return "\n".join(lines)

    def generate_findings_detail_text(self) -> str:
        """
        Generate detailed findings text for console output.

        Returns:
            Formatted findings detail text.
        """
        context = self.build_report_context()
        lines = [
            "=" * 70,
            "DETAILED FINDINGS",
            "=" * 70,
        ]

        for i, finding in enumerate(context["findings"], 1):
            lines.extend([
                "",
                f"--- Finding #{i}: {finding.get('finding_id', 'N/A')} ---",
                "",
                f"  Title:          {finding.get('title', 'N/A')}",
                f"  Audit Area:     {finding.get('audit_area', 'N/A')}",
                f"  Severity:       {finding.get('severity', 'N/A').upper()}",
                f"  Status:         {finding.get('status', 'open')}",
                f"  Identified:     {finding.get('identified_date', 'N/A')}",
                "",
                f"  Description:",
                f"  {finding.get('description', 'N/A')}",
                "",
                f"  Root Cause:",
                f"  {finding.get('root_cause', 'Not determined')}",
                "",
                f"  Business Impact:",
                f"  {finding.get('business_impact', 'Not assessed')}",
                "",
                f"  Recommendation:",
                f"  {finding.get('recommendation', 'No recommendation provided')}",
                "",
                f"  Management Response:",
                f"  {finding.get('management_response', 'Pending')}",
            ])

        lines.extend(["", "=" * 70])
        return "\n".join(lines)
