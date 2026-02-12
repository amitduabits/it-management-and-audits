"""
Executive Report Generator - One-page executive summary.

Generates a concise, visually compelling executive summary suitable
for C-level and board-level audiences. Focuses on risk posture,
key metrics, compliance status, and top recommendations.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


class ExecutiveReportGenerator:
    """
    Generates executive-level security assessment summaries.

    Produces a single-page HTML report with:
    - Overall risk posture gauge
    - Key security metrics
    - Compliance status by framework
    - Top 5 critical recommendations
    - Risk trend indicators

    Example:
        generator = ExecutiveReportGenerator()
        html = generator.generate(
            risk_data=risk_assessment.to_dict(),
            compliance_data={...},
            scan_summary={...},
        )
        generator.save(html, "reports/executive_summary.html")
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the executive report generator.

        Args:
            template_dir: Optional custom template directory path.
        """
        self.template_dir = template_dir or TEMPLATE_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html"]),
        )

    def generate(
        self,
        risk_data: Dict[str, Any],
        compliance_data: Optional[Dict[str, Any]] = None,
        scan_summary: Optional[Dict[str, Any]] = None,
        organization: str = "Organization",
        assessor: str = "SecureAudit Pro",
    ) -> str:
        """
        Generate the executive summary HTML report.

        Args:
            risk_data: Risk assessment results (RiskAssessment.to_dict()).
            compliance_data: Compliance results by framework.
            scan_summary: Summary of scan coverage and targets.
            organization: Name of the assessed organization.
            assessor: Name of the assessor or tool.

        Returns:
            Rendered HTML string of the executive report.
        """
        compliance_data = compliance_data or {}
        scan_summary = scan_summary or {}

        # Prepare template context
        context = {
            "report_title": "Executive Security Assessment Summary",
            "organization": organization,
            "assessor": assessor,
            "report_date": datetime.now().strftime("%B %d, %Y"),
            "report_id": f"SA-{datetime.now().strftime('%Y%m%d-%H%M')}",

            # Risk overview
            "overall_risk_score": risk_data.get("overall_risk_score", 0),
            "overall_risk_level": risk_data.get("overall_risk_level", "unknown"),
            "risk_trend": risk_data.get("risk_trend", "stable"),
            "total_findings": risk_data.get("total_findings", 0),
            "severity_distribution": risk_data.get("severity_distribution", {}),

            # Category breakdown
            "categories": risk_data.get("categories", []),

            # Compliance
            "compliance_frameworks": self._prepare_compliance_summary(
                compliance_data
            ),

            # Scan coverage
            "scan_targets": scan_summary.get("targets", []),
            "scan_types": scan_summary.get("scan_types", []),
            "scan_duration": scan_summary.get("duration", "N/A"),

            # Top recommendations
            "recommendations": risk_data.get("recommendations", [])[:5],

            # Risk level helpers for conditional styling
            "risk_color": self._risk_color(
                risk_data.get("overall_risk_level", "minimal")
            ),

            # Timestamp
            "generated_at": datetime.now().isoformat(),
        }

        try:
            template = self.env.get_template("executive.html")
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering executive template: {e}")
            return self._fallback_report(context)

    def _prepare_compliance_summary(
        self, compliance_data: Dict
    ) -> list:
        """Prepare compliance framework summary for the template."""
        frameworks = []

        framework_names = {
            "iso27001": "ISO 27001:2022",
            "pci_dss": "PCI-DSS v4.0",
            "nist_csf": "NIST CSF v2.0",
        }

        for key, display_name in framework_names.items():
            fw_data = compliance_data.get(key, {})
            if fw_data:
                score = fw_data.get("overall_percentage",
                    round(fw_data.get("overall_score", 0) * 100, 1)
                )
                frameworks.append({
                    "name": display_name,
                    "score": score,
                    "passed": fw_data.get("passed", 0),
                    "failed": fw_data.get("failed", 0),
                    "partial": fw_data.get("partial", 0),
                    "total": fw_data.get(
                        "total_controls",
                        fw_data.get("total_requirements",
                            fw_data.get("total_subcategories", 0))
                    ),
                    "color": self._score_color(score),
                })
            else:
                frameworks.append({
                    "name": display_name,
                    "score": 0,
                    "passed": 0,
                    "failed": 0,
                    "partial": 0,
                    "total": 0,
                    "color": "#94a3b8",
                })

        return frameworks

    def _risk_color(self, level: str) -> str:
        """Get color for risk level."""
        colors = {
            "critical": "#dc2626",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#22c55e",
            "minimal": "#06b6d4",
        }
        return colors.get(level.lower(), "#94a3b8")

    def _score_color(self, score: float) -> str:
        """Get color for compliance score percentage."""
        if score >= 80:
            return "#22c55e"
        elif score >= 60:
            return "#84cc16"
        elif score >= 40:
            return "#eab308"
        elif score >= 20:
            return "#f97316"
        else:
            return "#ef4444"

    def _fallback_report(self, context: Dict) -> str:
        """Generate a basic HTML report when template is not available."""
        sev = context.get("severity_distribution", {})
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{context['report_title']}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1e293b, #334155); color: white; padding: 30px; border-radius: 12px; }}
        .metric {{ display: inline-block; width: 22%; text-align: center; padding: 15px; margin: 5px; background: #f8fafc; border-radius: 8px; }}
        .metric .value {{ font-size: 2em; font-weight: bold; }}
        .risk-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; color: white; background: {context['risk_color']}; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{context['report_title']}</h1>
        <p>Organization: {context['organization']} | Date: {context['report_date']} | ID: {context['report_id']}</p>
    </div>
    <h2>Risk Overview</h2>
    <div class="metric"><div class="value">{context['overall_risk_score']}/10</div><div>Risk Score</div></div>
    <div class="metric"><div class="value"><span class="risk-badge">{context['overall_risk_level'].upper()}</span></div><div>Risk Level</div></div>
    <div class="metric"><div class="value">{context['total_findings']}</div><div>Total Findings</div></div>
    <div class="metric"><div class="value">{sev.get('critical', 0)}</div><div>Critical</div></div>
    <h2>Top Recommendations</h2>
    <ol>{"".join(f"<li><strong>{r.get('category', '')}</strong>: {r.get('recommendation', '')}</li>" for r in context.get('recommendations', []))}</ol>
    <hr><p><em>Generated by {context['assessor']} on {context['report_date']}</em></p>
</body>
</html>"""

    def save(self, html_content: str, output_path: str):
        """
        Save the report HTML to a file.

        Args:
            html_content: Rendered HTML string.
            output_path: File path to save the report.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Executive report saved to: {output_path}")
