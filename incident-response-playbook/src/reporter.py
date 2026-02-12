"""
Incident Report Generator
===========================

Generates formatted incident reports using Jinja2 templates.
Supports HTML and Markdown output formats for distribution
to stakeholders, management, and regulatory bodies.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models import Incident
from src.severity_calculator import SeverityAssessment


class IncidentReporter:
    """Generates incident reports from templates and incident data."""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the reporter with template directory.

        Args:
            templates_dir: Path to Jinja2 templates directory.
                          Defaults to ../templates/ relative to this file.
        """
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "templates",
            )

        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        # Register custom filters
        self.env.filters["datetime_format"] = self._format_datetime
        self.env.filters["severity_color"] = self._severity_color
        self.env.filters["truncate_hash"] = self._truncate_hash

    def generate_html_report(
        self,
        incident: Incident,
        severity_assessment: Optional[SeverityAssessment] = None,
        simulation_results: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate an HTML incident report.

        Args:
            incident: The incident data to report on.
            severity_assessment: Optional severity calculation results.
            simulation_results: Optional simulation scoring results.
            output_path: If provided, write the report to this file.

        Returns:
            The rendered HTML report string.
        """
        template = self.env.get_template("incident_report.html")

        context = self._build_report_context(
            incident, severity_assessment, simulation_results
        )

        html = template.render(**context)

        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

        return html

    def generate_executive_summary(self, incident: Incident) -> str:
        """
        Generate a concise executive summary for leadership briefing.

        Args:
            incident: The incident data.

        Returns:
            Formatted executive summary string.
        """
        duration = incident.get_duration_hours()
        duration_str = f"{duration:.1f} hours" if duration else "Ongoing"

        summary_lines = [
            "EXECUTIVE SUMMARY - INCIDENT REPORT",
            "=" * 50,
            "",
            f"Incident ID:      {incident.incident_id}",
            f"Title:            {incident.title}",
            f"Severity:         {incident.severity.value.upper()}",
            f"Status:           {incident.status.value.upper()}",
            f"Category:         {incident.category.value.replace('_', ' ').title()}",
            f"Duration:         {duration_str}",
            f"Affected Systems: {len(incident.affected_systems)}",
            f"Affected Users:   {incident.affected_users:,}",
            "",
            "DESCRIPTION:",
            incident.description[:500],
            "",
        ]

        if incident.attack_vector:
            summary_lines.extend([
                "ATTACK VECTOR:",
                incident.attack_vector,
                "",
            ])

        if incident.containment_strategy:
            summary_lines.extend([
                "CONTAINMENT:",
                incident.containment_strategy,
                "",
            ])

        if incident.root_cause:
            summary_lines.extend([
                "ROOT CAUSE:",
                incident.root_cause,
                "",
            ])

        if incident.business_impact_score > 0:
            summary_lines.extend([
                f"BUSINESS IMPACT SCORE: {incident.business_impact_score}/10.0",
                "",
            ])

        if incident.regulatory_notifications:
            summary_lines.extend([
                "REGULATORY NOTIFICATIONS REQUIRED:",
                *[f"  - {n}" for n in incident.regulatory_notifications],
                "",
            ])

        if incident.lessons_learned:
            summary_lines.extend([
                "KEY FINDINGS & RECOMMENDATIONS:",
                *[f"  {i+1}. {lesson}" for i, lesson in enumerate(incident.lessons_learned)],
                "",
            ])

        summary_lines.extend([
            "=" * 50,
            f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Classification: CONFIDENTIAL - Need to Know",
        ])

        return "\n".join(summary_lines)

    def generate_evidence_log(
        self,
        evidence_items: List[Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate an evidence log document.

        Args:
            evidence_items: List of evidence dictionaries.
            output_path: Optional file path to write output.

        Returns:
            Formatted evidence log string.
        """
        try:
            template = self.env.get_template("evidence_log.md")
            content = template.render(
                evidence_items=evidence_items,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                total_items=len(evidence_items),
            )
        except Exception:
            # Fallback to manual formatting if template not available
            content = self._format_evidence_log_manual(evidence_items)

        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def generate_json_report(
        self,
        incident: Incident,
        severity_assessment: Optional[SeverityAssessment] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a machine-readable JSON incident report.

        Args:
            incident: The incident data.
            severity_assessment: Optional severity assessment.
            output_path: Optional file path to write output.

        Returns:
            JSON string of the report.
        """
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "format_version": "1.0",
                "classification": "CONFIDENTIAL",
            },
            "incident": incident.to_dict(),
        }

        if severity_assessment:
            report_data["severity_assessment"] = severity_assessment.to_dict()

        json_str = json.dumps(report_data, indent=2, default=str)

        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    def _build_report_context(
        self,
        incident: Incident,
        severity_assessment: Optional[SeverityAssessment],
        simulation_results: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build the template context dictionary."""
        return {
            "incident": incident,
            "incident_dict": incident.to_dict(),
            "severity": severity_assessment,
            "simulation": simulation_results,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "report_classification": "CONFIDENTIAL - RESTRICTED DISTRIBUTION",
            "timeline_events": [e.to_dict() for e in incident.timeline],
            "evidence_items": [e.to_dict() for e in incident.evidence],
            "actions_taken": [a.to_dict() for a in incident.actions],
            "iocs": incident.iocs,
            "duration_hours": incident.get_duration_hours(),
        }

    def _format_evidence_log_manual(self, evidence_items: List[Dict[str, Any]]) -> str:
        """Manual evidence log formatting as fallback."""
        lines = [
            "# Evidence Collection Log",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total Items: {len(evidence_items)}",
            "",
            "---",
            "",
        ]

        for i, item in enumerate(evidence_items, 1):
            lines.extend([
                f"## Evidence Item {i}: {item.get('evidence_id', 'N/A')}",
                "",
                f"- **Type:** {item.get('evidence_type', 'N/A')}",
                f"- **Description:** {item.get('description', 'N/A')}",
                f"- **Collected By:** {item.get('collected_by', 'N/A')}",
                f"- **Collected At:** {item.get('collected_at', 'N/A')}",
                f"- **Source System:** {item.get('source_system', 'N/A')}",
                f"- **File Path:** {item.get('file_path', 'N/A')}",
                f"- **SHA-256:** {item.get('file_hash_sha256', 'N/A')}",
                f"- **MD5:** {item.get('file_hash_md5', 'N/A')}",
                f"- **Size:** {item.get('file_size_bytes', 'N/A')} bytes",
                f"- **Volatile:** {'Yes' if item.get('is_volatile') else 'No'}",
                f"- **Integrity Verified:** {'Yes' if item.get('integrity_verified') else 'No'}",
                "",
                "---",
                "",
            ])

        return "\n".join(lines)

    @staticmethod
    def _format_datetime(value, fmt: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
        """Jinja2 filter: Format a datetime string or object."""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return value
        if isinstance(value, datetime):
            return value.strftime(fmt)
        return str(value)

    @staticmethod
    def _severity_color(severity: str) -> str:
        """Jinja2 filter: Return CSS color for severity level."""
        colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
            "informational": "#17a2b8",
        }
        return colors.get(severity.lower(), "#6c757d")

    @staticmethod
    def _truncate_hash(hash_value: str, length: int = 12) -> str:
        """Jinja2 filter: Truncate a hash for display."""
        if not hash_value or hash_value == "N/A":
            return "N/A"
        if len(hash_value) > length:
            return hash_value[:length] + "..."
        return hash_value
