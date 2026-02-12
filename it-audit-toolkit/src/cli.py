"""
Command-Line Interface for the IT Audit Toolkit.

Provides the following commands:
    new-audit        Create a new audit engagement
    run-checklist    Execute a control checklist interactively
    add-finding      Record an audit finding
    calculate-risk   Compute risk scores and compliance metrics
    generate-report  Generate a professional HTML audit report

Built on Click with Rich for formatted terminal output.
"""

import json
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.audit_engine import AuditEngine, AVAILABLE_CHECKLISTS, CHECKLIST_DISPLAY_NAMES
from src.models import AuditEngagement, FindingSeverity
from src.risk_calculator import RiskCalculator
from src.reporter import AuditReporter


console = Console()


def _severity_style(severity: str) -> str:
    """Map severity to Rich style string."""
    styles = {
        "critical": "bold white on red",
        "high": "bold white on dark_orange",
        "medium": "bold black on yellow",
        "low": "bold white on green",
        "informational": "bold white on blue",
    }
    return styles.get(severity.lower(), "bold")


@click.group()
@click.version_option(version="1.0.0", prog_name="IT Audit Toolkit")
def cli():
    """IT Audit Toolkit - Professional IT Audit Management Suite.

    A structured toolkit for planning, executing, and reporting on
    Information Technology audits. Run any command with --help for
    detailed usage information.
    """
    pass


@cli.command("new-audit")
@click.option("--name", required=True, help="Descriptive name for the audit engagement")
@click.option("--client", required=True, help="Name of the client organization")
@click.option("--lead-auditor", required=True, help="Name and credentials of the lead auditor")
@click.option("--scope", default="", help="Description of the audit scope")
@click.option("--output", required=True, help="Output file path for the engagement JSON")
def new_audit(name, client, lead_auditor, scope, output):
    """Create a new audit engagement.

    Initializes a new engagement with metadata and saves it to a JSON file.
    The engagement can then be used with run-checklist, add-finding, and
    other commands.

    Example:
        python -m src.cli new-audit --name "Q1 Audit" --client "Acme Corp"
        --lead-auditor "J. Smith, CISA" --output data/audit.json
    """
    engine = AuditEngine()
    engagement = engine.create_engagement(
        name=name,
        client=client,
        lead_auditor=lead_auditor,
        scope_description=scope,
    )

    engine.save_engagement(output)

    console.print()
    console.print(Panel(
        f"[bold green]Audit Engagement Created Successfully[/bold green]\n\n"
        f"  Engagement ID:  {engagement.engagement_id}\n"
        f"  Name:           {name}\n"
        f"  Client:         {client}\n"
        f"  Lead Auditor:   {lead_auditor}\n"
        f"  Status:         {engagement.status}\n"
        f"  Created:        {engagement.created_at}\n\n"
        f"  Saved to:       {os.path.abspath(output)}",
        title="New Engagement",
        border_style="green",
    ))
    console.print()

    # Show available checklists
    table = Table(title="Available Checklists", show_header=True, header_style="bold cyan")
    table.add_column("Key", style="bold")
    table.add_column("Domain")
    table.add_column("Controls", justify="right")

    available = AuditEngine.list_available_checklists()
    for key, info in available.items():
        table.add_row(key, info["display_name"], str(info["control_count"]))

    console.print(table)
    console.print()
    console.print("[dim]Run a checklist with: python -m src.cli run-checklist --audit", output, "--checklist <key>[/dim]")


@cli.command("run-checklist")
@click.option("--audit", required=True, type=click.Path(exists=True), help="Path to the audit engagement JSON file")
@click.option(
    "--checklist",
    required=True,
    type=click.Choice(list(AVAILABLE_CHECKLISTS.keys())),
    help="Checklist to execute",
)
@click.option("--auditor", default="", help="Name of the auditor performing the testing")
def run_checklist(audit, checklist, auditor):
    """Execute a control checklist interactively.

    Loads the specified checklist and iterates through each control,
    prompting for assessment status and auditor notes. Progress is
    saved to the engagement file after completion.

    Example:
        python -m src.cli run-checklist --audit data/audit.json
        --checklist access_control
    """
    engine = AuditEngine()
    engine.load_engagement(audit)

    checklist_info = AuditEngine.list_available_checklists().get(checklist, {})
    display_name = checklist_info.get("display_name", checklist)
    control_count = checklist_info.get("control_count", "?")

    console.print()
    console.print(Panel(
        f"[bold]Checklist:[/bold] {display_name}\n"
        f"[bold]Controls:[/bold] {control_count}\n"
        f"[bold]Engagement:[/bold] {engine.engagement.name}\n"
        f"[bold]Client:[/bold] {engine.engagement.client}",
        title="Running Audit Checklist",
        border_style="cyan",
    ))
    console.print()

    # Run the interactive checklist
    area = engine.run_checklist_interactive(checklist, auditor_name=auditor)

    # Save progress
    engine.save_engagement(audit)

    # Show completion summary
    progress = engine.get_area_progress(
        area.name if hasattr(area, "name") else area.get("name", "")
    )

    console.print()
    console.print(Panel(
        f"[bold green]Checklist Completed[/bold green]\n\n"
        f"  Total Controls:           {progress['total_controls']}\n"
        f"  Tested:                   {progress['tested']}\n"
        f"  Effective:                {progress['effective']}\n"
        f"  Partially Effective:      {progress['partially_effective']}\n"
        f"  Ineffective:              {progress['ineffective']}\n"
        f"  Not Applicable:           {progress['not_applicable']}\n"
        f"  Completion:               {progress['completion_pct']}%",
        title="Checklist Summary",
        border_style="green",
    ))


@cli.command("add-finding")
@click.option("--audit", required=True, type=click.Path(exists=True), help="Path to the audit engagement JSON file")
@click.option("--title", required=True, help="Brief descriptive title of the finding")
@click.option("--area", required=True, help="Audit area this finding relates to")
@click.option(
    "--severity",
    required=True,
    type=click.Choice(["critical", "high", "medium", "low", "informational"]),
    help="Severity classification",
)
@click.option("--description", required=True, help="Detailed description of the finding")
@click.option("--root-cause", default="", help="Identified root cause")
@click.option("--impact", default="", help="Business impact description")
@click.option("--recommendation", default="", help="Recommended remediation action")
@click.option("--auditor", default="", help="Name of the identifying auditor")
def add_finding(audit, title, area, severity, description, root_cause, impact, recommendation, auditor):
    """Record an audit finding with severity rating.

    Findings document control deficiencies discovered during fieldwork.
    Each finding is associated with an audit area and assigned a severity
    level that drives remediation priority.

    Example:
        python -m src.cli add-finding --audit data/audit.json
        --title "Weak Password Policy" --area "Access Control"
        --severity high --description "Password minimum length is 6 characters"
    """
    engine = AuditEngine()
    engine.load_engagement(audit)

    finding = engine.add_finding(
        title=title,
        audit_area=area,
        severity=severity,
        description=description,
        root_cause=root_cause,
        business_impact=impact,
        recommendation=recommendation,
        identified_by=auditor,
    )

    engine.save_engagement(audit)

    style = _severity_style(severity)
    console.print()
    console.print(Panel(
        f"[bold]Finding Recorded Successfully[/bold]\n\n"
        f"  Finding ID:     {finding.finding_id}\n"
        f"  Title:          {title}\n"
        f"  Audit Area:     {area}\n"
        f"  Severity:       [{style}] {severity.upper()} [/{style}]\n"
        f"  Status:         Open\n"
        f"  Date:           {finding.identified_date}",
        title="New Finding",
        border_style="yellow",
    ))


@cli.command("calculate-risk")
@click.option("--audit", required=True, type=click.Path(exists=True), help="Path to the audit engagement JSON file")
@click.option("--verbose", is_flag=True, help="Show detailed per-control risk breakdown")
def calculate_risk(audit, verbose):
    """Compute risk scores and compliance percentages.

    Calculates risk using a 5x5 likelihood x impact matrix for all
    controls and findings. Generates compliance percentages per audit
    area and overall.

    Example:
        python -m src.cli calculate-risk --audit data/audit.json
    """
    engine = AuditEngine()
    engine.load_engagement(audit)

    calculator = RiskCalculator(engine.engagement)
    risk_data = calculator.calculate_engagement_risk()

    # Save updated risk scores
    engine.save_engagement(audit)

    # Display overall risk posture
    overall_sev = risk_data["overall_severity"]
    style = _severity_style(overall_sev)

    console.print()
    console.print(Panel(
        f"[bold]Overall Compliance:[/bold]  {risk_data['overall_compliance_pct']:.1f}%\n"
        f"[bold]Overall Risk Score:[/bold]  {risk_data['overall_risk_score']:.1f} / 25.0\n"
        f"[bold]Risk Severity:[/bold]       [{style}] {overall_sev.upper()} [/{style}]\n"
        f"[bold]Controls Tested:[/bold]     {risk_data['total_tested']} / {risk_data['total_controls']}\n"
        f"[bold]Total Findings:[/bold]      {risk_data['total_findings']}",
        title="Engagement Risk Assessment",
        border_style="cyan",
    ))

    # Area compliance table
    console.print()
    table = Table(title="Compliance by Audit Area", show_header=True, header_style="bold cyan")
    table.add_column("Audit Area", style="bold", min_width=25)
    table.add_column("Controls", justify="right")
    table.add_column("Tested", justify="right")
    table.add_column("Effective", justify="right")
    table.add_column("Compliance", justify="right")
    table.add_column("Avg Risk", justify="right")
    table.add_column("Findings", justify="right")

    for area in risk_data["area_results"]:
        pct = area["compliance_pct"]
        if pct >= 80:
            pct_style = "green"
        elif pct >= 60:
            pct_style = "yellow"
        elif pct >= 40:
            pct_style = "dark_orange"
        else:
            pct_style = "red"

        table.add_row(
            area["area_name"],
            str(area["total_controls"]),
            str(area["tested_controls"]),
            str(area["effective_controls"]),
            f"[{pct_style}]{pct:.1f}%[/{pct_style}]",
            f"{area['average_risk_score']:.1f}",
            str(area["finding_count"]),
        )

    console.print(table)

    # Finding severity distribution
    console.print()
    dist = risk_data["finding_severity_distribution"]
    findings_table = Table(title="Finding Severity Distribution", show_header=True, header_style="bold cyan")
    findings_table.add_column("Severity", style="bold")
    findings_table.add_column("Count", justify="right")
    findings_table.add_column("Bar")

    max_count = max(dist.values()) if any(dist.values()) else 1
    for sev in ["critical", "high", "medium", "low", "informational"]:
        count = dist[sev]
        bar_len = int((count / max_count) * 20) if max_count > 0 else 0
        style = _severity_style(sev)
        findings_table.add_row(
            f"[{style}]{sev.upper()}[/{style}]",
            str(count),
            f"[{style}]{'█' * bar_len}[/{style}]",
        )

    console.print(findings_table)

    # Remediation roadmap (top 10)
    if risk_data.get("remediation_summary"):
        console.print()
        road_table = Table(title="Remediation Roadmap (Top 10)", show_header=True, header_style="bold cyan")
        road_table.add_column("#", justify="right", style="bold")
        road_table.add_column("Finding")
        road_table.add_column("Severity")
        road_table.add_column("Risk Score", justify="right")
        road_table.add_column("Timeline")

        for item in risk_data["remediation_summary"][:10]:
            style = _severity_style(item["severity"])
            road_table.add_row(
                str(item["priority_order"]),
                item["title"],
                f"[{style}]{item['severity'].upper()}[/{style}]",
                str(item["risk_score"]),
                item["remediation_timeline"],
            )

        console.print(road_table)

    # Verbose: per-control breakdown
    if verbose:
        for area in risk_data["area_results"]:
            console.print()
            ctrl_table = Table(
                title=f"Control Risk Detail: {area['area_name']}",
                show_header=True,
                header_style="bold cyan",
            )
            ctrl_table.add_column("Control ID", style="bold")
            ctrl_table.add_column("Title")
            ctrl_table.add_column("Status")
            ctrl_table.add_column("L", justify="right")
            ctrl_table.add_column("I", justify="right")
            ctrl_table.add_column("Score", justify="right")
            ctrl_table.add_column("Severity")

            for cr in area["control_risks"]:
                sev = cr.get("severity", "informational")
                style = _severity_style(sev) if sev != "not_applicable" else "dim"
                ctrl_table.add_row(
                    cr["control_id"],
                    cr["title"][:40] + "..." if len(cr.get("title", "")) > 40 else cr.get("title", ""),
                    cr["status"],
                    str(cr["likelihood"]),
                    str(cr["impact"]),
                    str(cr["risk_score"]),
                    f"[{style}]{sev.upper()}[/{style}]",
                )

            console.print(ctrl_table)


@cli.command("generate-report")
@click.option("--audit", required=True, type=click.Path(exists=True), help="Path to the audit engagement JSON file")
@click.option("--output", required=True, help="Output file path for the HTML report")
@click.option("--template", default="audit_report.html", help="Template filename to use")
@click.option("--text-summary", is_flag=True, help="Also print text executive summary to console")
def generate_report(audit, output, template, text_summary):
    """Generate a professional HTML audit report.

    Creates a comprehensive audit report including executive summary,
    detailed findings, risk heat map, compliance dashboard, and
    remediation roadmap.

    Example:
        python -m src.cli generate-report --audit data/audit.json
        --output reports/audit_report.html
    """
    engine = AuditEngine()
    engine.load_engagement(audit)

    reporter = AuditReporter(engine.engagement)

    # Generate HTML report
    report_path = reporter.generate_html_report(output, template_name=template)

    console.print()
    console.print(Panel(
        f"[bold green]Audit Report Generated Successfully[/bold green]\n\n"
        f"  Report File:    {report_path}\n"
        f"  Engagement:     {engine.engagement.name}\n"
        f"  Client:         {engine.engagement.client}\n"
        f"  Template:       {template}",
        title="Report Generated",
        border_style="green",
    ))

    if text_summary:
        console.print()
        summary_text = reporter.generate_executive_summary_text()
        console.print(summary_text)


@cli.command("list-checklists")
def list_checklists():
    """List all available audit checklists with details."""
    available = AuditEngine.list_available_checklists()

    console.print()
    table = Table(
        title="Available Audit Checklists",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Key", style="bold")
    table.add_column("Domain")
    table.add_column("Controls", justify="right")
    table.add_column("Version")
    table.add_column("Frameworks")

    for key, info in available.items():
        frameworks = ", ".join(info["framework_references"][:3])
        if len(info["framework_references"]) > 3:
            frameworks += f" (+{len(info['framework_references']) - 3} more)"
        table.add_row(
            key,
            info["display_name"],
            str(info["control_count"]),
            info["version"],
            frameworks,
        )

    console.print(table)
    console.print()

    # Total controls
    total = sum(info["control_count"] for info in available.values())
    console.print(f"  Total controls across all checklists: [bold]{total}[/bold]")
    console.print()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
