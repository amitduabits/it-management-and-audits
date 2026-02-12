"""
Technical Report Generator - Detailed findings with CVSS-like scoring.

Generates a comprehensive technical report containing:
- All findings with evidence and severity ratings
- CVSS-aligned scoring for each vulnerability
- Detailed remediation steps
- Compliance mapping per finding
- Risk matrix visualization
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

# CVSS v3.1 severity classification
CVSS_SEVERITY = {
    (0.0, 0.0): ("None", "#94a3b8"),
    (0.1, 3.9): ("Low", "#22c55e"),
    (4.0, 6.9): ("Medium", "#eab308"),
    (7.0, 8.9): ("High", "#f97316"),
    (9.0, 10.0): ("Critical", "#ef4444"),
}


def cvss_to_severity(score: float) -> tuple:
    """Convert CVSS score to severity label and color."""
    for (low, high), (label, color) in CVSS_SEVERITY.items():
        if low <= score <= high:
            return label, color
    return "Unknown", "#94a3b8"


class TechnicalReportGenerator:
    """
    Generates detailed technical security assessment reports.

    Produces an HTML report with:
    - Findings sorted by severity (critical first)
    - CVSS-aligned scoring with severity badges
    - Evidence and reproduction steps
    - Remediation guidance per finding
    - Compliance framework references
    - Finding statistics and charts

    Example:
        generator = TechnicalReportGenerator()
        html = generator.generate(
            findings=all_findings,
            risk_data=risk_assessment.to_dict(),
            scan_metadata={...},
        )
        generator.save(html, "reports/technical_report.html")
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the technical report generator.

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
        findings: List[Dict],
        risk_data: Optional[Dict] = None,
        scan_metadata: Optional[Dict] = None,
        organization: str = "Organization",
    ) -> str:
        """
        Generate the technical findings report.

        Args:
            findings: List of all finding dictionaries.
            risk_data: Optional risk assessment data.
            scan_metadata: Optional scan metadata (targets, duration, etc.).
            organization: Organization name.

        Returns:
            Rendered HTML string.
        """
        risk_data = risk_data or {}
        scan_metadata = scan_metadata or {}

        # Enrich findings with CVSS labels
        enriched_findings = self._enrich_findings(findings)

        # Sort by CVSS score descending
        sorted_findings = sorted(
            enriched_findings,
            key=lambda f: f.get("cvss_score", 0),
            reverse=True,
        )

        # Statistics
        stats = self._compute_statistics(sorted_findings)

        context = {
            "report_title": "Technical Security Assessment Report",
            "organization": organization,
            "report_date": datetime.now().strftime("%B %d, %Y"),
            "report_id": f"SA-TECH-{datetime.now().strftime('%Y%m%d-%H%M')}",
            "findings": sorted_findings,
            "statistics": stats,
            "risk_data": risk_data,
            "scan_metadata": scan_metadata,
            "generated_at": datetime.now().isoformat(),
            "total_findings": len(sorted_findings),
        }

        try:
            template = self.env.get_template("technical.html")
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering technical template: {e}")
            return self._fallback_report(context)

    def _enrich_findings(self, findings: List[Dict]) -> List[Dict]:
        """
        Enrich findings with CVSS severity labels and colors.

        Args:
            findings: Raw findings list.

        Returns:
            Enriched findings with additional display fields.
        """
        enriched = []
        for idx, finding in enumerate(findings):
            f = finding.copy()
            cvss = f.get("cvss_score", 0)
            severity_label, severity_color = cvss_to_severity(cvss)

            f["finding_number"] = idx + 1
            f["cvss_severity_label"] = severity_label
            f["cvss_severity_color"] = severity_color
            f["cvss_bar_width"] = int(cvss * 10)  # percentage for progress bar

            # Ensure all display fields exist
            f.setdefault("id", f"FIND-{idx + 1:04d}")
            f.setdefault("title", "Untitled Finding")
            f.setdefault("description", "")
            f.setdefault("severity", severity_label.lower())
            f.setdefault("category", "General")
            f.setdefault("evidence", "")
            f.setdefault("remediation", "")
            f.setdefault("compliance_refs", [])
            f.setdefault("discovered_at", datetime.now().isoformat())

            enriched.append(f)

        return enriched

    def _compute_statistics(self, findings: List[Dict]) -> Dict:
        """
        Compute finding statistics for the report header.

        Args:
            findings: Enriched findings list.

        Returns:
            Statistics dictionary.
        """
        severity_counts = {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0,
        }
        category_counts = {}
        cvss_scores = []

        for f in findings:
            sev = f.get("severity", "info").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

            cat = f.get("category", "Other")
            category_counts[cat] = category_counts.get(cat, 0) + 1

            cvss_scores.append(f.get("cvss_score", 0))

        return {
            "total": len(findings),
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "avg_cvss": (
                round(sum(cvss_scores) / len(cvss_scores), 1)
                if cvss_scores else 0
            ),
            "max_cvss": max(cvss_scores) if cvss_scores else 0,
            "actionable": severity_counts["critical"] + severity_counts["high"],
        }

    def _fallback_report(self, context: Dict) -> str:
        """Generate basic technical report when template is unavailable."""
        findings_html = ""
        for f in context.get("findings", []):
            findings_html += f"""
            <div style="border:1px solid #e2e8f0; border-left:4px solid {f.get('cvss_severity_color','#94a3b8')}; padding:15px; margin:10px 0; border-radius:6px;">
                <h3>#{f.get('finding_number',0)}: {f.get('title','')}</h3>
                <p><strong>CVSS Score:</strong> {f.get('cvss_score',0)}/10 ({f.get('cvss_severity_label','')})</p>
                <p><strong>Category:</strong> {f.get('category','')}</p>
                <p>{f.get('description','')}</p>
                <p><strong>Evidence:</strong> {f.get('evidence','N/A')}</p>
                <p><strong>Remediation:</strong> {f.get('remediation','')}</p>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{context['report_title']}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; color: #1e293b; }}
        .header {{ background: linear-gradient(135deg, #1e293b, #475569); color: white; padding: 30px; border-radius: 12px; }}
        h3 {{ color: #1e293b; margin-bottom: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{context['report_title']}</h1>
        <p>Organization: {context['organization']} | Date: {context['report_date']} | Findings: {context['total_findings']}</p>
    </div>
    <h2>Findings ({context['total_findings']})</h2>
    {findings_html}
    <hr><p><em>Report ID: {context['report_id']}</em></p>
</body>
</html>"""

    def save(self, html_content: str, output_path: str):
        """Save the technical report to a file."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Technical report saved to: {output_path}")
