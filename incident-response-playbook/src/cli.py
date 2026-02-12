"""
Command-Line Interface
=======================

Provides a Click-based CLI for running incident response simulations,
listing scenarios, and generating reports.

Usage:
    ir-playbook list-scenarios
    ir-playbook simulate --scenario data_breach
    ir-playbook generate-report --scenario data_breach --output report.html
    ir-playbook severity --data-class confidential --records 50000 --frameworks GDPR,HIPAA
"""

import os
import sys
import json
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich import box

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulator import IncidentSimulator
from src.scenarios import list_scenarios, get_scenario, SCENARIO_REGISTRY
from src.severity_calculator import (
    SeverityCalculator, CVSSVector, BusinessImpactFactors,
    DataClassification, SystemCriticality,
)
from src.timeline import TimelineGenerator
from src.evidence_tracker import EvidenceTracker
from src.reporter import IncidentReporter
from src.models import Incident, IncidentCategory, SeverityLevel

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="IR Playbook Engine")
def cli():
    """Incident Response Playbook Engine - Interactive IR Training & Simulation

    A comprehensive incident response simulation framework built on
    NIST SP 800-61 Rev. 2 methodology. Run tabletop exercises, practice
    decision-making under pressure, and generate professional IR reports.
    """
    pass


@cli.command("list-scenarios")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]),
              default="table", help="Output format")
def list_scenarios_cmd(output_format):
    """List all available incident response scenarios."""
    scenarios = list_scenarios()

    if output_format == "json":
        click.echo(json.dumps(scenarios, indent=2))
        return

    table = Table(
        title="Available Incident Response Scenarios",
        box=box.DOUBLE_EDGE,
        show_lines=True,
    )
    table.add_column("Name", style="cyan", width=18)
    table.add_column("Title", style="white", width=45)
    table.add_column("Severity", style="bold", width=10)
    table.add_column("Duration", justify="right", width=10)
    table.add_column("Description", style="dim", width=50)

    for s in scenarios:
        severity = s["severity"].upper()
        sev_colors = {
            "CRITICAL": "red",
            "HIGH": "bright_red",
            "MEDIUM": "yellow",
            "LOW": "green",
        }
        color = sev_colors.get(severity, "white")
        desc = s["description"][:100] + "..." if len(s["description"]) > 100 else s["description"]

        table.add_row(
            s["name"],
            s["title"],
            f"[{color}]{severity}[/{color}]",
            f"{s['estimated_duration']} min",
            desc,
        )

    console.print(table)
    console.print(f"\n[dim]Use 'ir-playbook simulate --scenario <name>' to start a simulation[/dim]")


@cli.command("simulate")
@click.option("--scenario", "-s", required=True,
              type=click.Choice(list(SCENARIO_REGISTRY.keys())),
              help="Scenario to simulate")
@click.option("--output", "-o", default=None,
              help="Output file for simulation results (JSON)")
def simulate_cmd(scenario, output):
    """Run an interactive incident response simulation.

    Presents a realistic incident scenario with decision points at each
    phase of the NIST IR lifecycle. Your choices are scored and feedback
    is provided in real-time.
    """
    simulator = IncidentSimulator()

    console.print(f"\n[bold blue]Starting {scenario.replace('_', ' ').title()} simulation...[/bold blue]\n")
    console.print("[dim]You will be presented with decision points. Select the best response at each step.[/dim]\n")

    result = simulator.run_simulation(scenario)

    if output:
        output_data = result.to_dict()
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
        console.print(f"\n[green]Results saved to: {output}[/green]")


@cli.command("generate-report")
@click.option("--scenario", "-s", required=True,
              type=click.Choice(list(SCENARIO_REGISTRY.keys())),
              help="Scenario to generate report for")
@click.option("--output", "-o", default=None,
              help="Output file path (defaults to ./reports/<scenario>_report.html)")
@click.option("--format", "report_format",
              type=click.Choice(["html", "json", "text"]),
              default="html", help="Report format")
def generate_report_cmd(scenario, output, report_format):
    """Generate an incident report for a scenario.

    Creates a professional incident report using the scenario data,
    including timeline, severity assessment, and evidence summary.
    """
    scenario_obj = get_scenario(scenario)

    # Build a sample incident from the scenario
    incident = Incident(
        title=scenario_obj.title,
        description=scenario_obj.description,
        category=IncidentCategory(scenario_obj.category),
        severity=SeverityLevel(scenario_obj.default_severity),
        detected_at=datetime.now(),
        affected_systems=scenario_obj.affected_systems,
        attack_vector=scenario_obj.attack_vector,
        incident_commander="IR Team Lead",
        reported_by="SOC Tier-2 Analyst",
    )

    for ioc in scenario_obj.initial_iocs:
        incident.add_ioc(ioc["type"], ioc["value"], ioc.get("confidence", "high"))

    # Generate timeline
    timeline_gen = TimelineGenerator()
    timeline_events = timeline_gen.generate_scenario_timeline(
        incident_start=incident.detected_at,
        severity=scenario_obj.default_severity.upper(),
    )
    incident.timeline.extend(timeline_events)

    # Calculate severity
    severity_calc = SeverityCalculator()
    assessment = severity_calc.quick_severity(
        data_classification="confidential",
        records_affected=100000,
        system_criticality="tier_1_critical",
        regulatory_frameworks=["GDPR", "CCPA"],
        notification_required=True,
    )
    incident.business_impact_score = assessment.composite_score

    # Set default output path
    if not output:
        reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "reports",
        )
        os.makedirs(reports_dir, exist_ok=True)
        ext = {"html": "html", "json": "json", "text": "txt"}.get(report_format, "html")
        output = os.path.join(reports_dir, f"{scenario}_report.{ext}")

    reporter = IncidentReporter()

    if report_format == "html":
        reporter.generate_html_report(
            incident=incident,
            severity_assessment=assessment,
            output_path=output,
        )
    elif report_format == "json":
        reporter.generate_json_report(
            incident=incident,
            severity_assessment=assessment,
            output_path=output,
        )
    elif report_format == "text":
        summary = reporter.generate_executive_summary(incident)
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(summary)

    console.print(f"\n[green]Report generated: {output}[/green]")


@cli.command("severity")
@click.option("--data-class", type=click.Choice(["public", "internal", "confidential", "restricted"]),
              default="internal", help="Data classification level")
@click.option("--records", type=int, default=0, help="Number of records affected")
@click.option("--system-tier", type=click.Choice(["tier_1_critical", "tier_2_important",
              "tier_3_standard", "tier_4_non_critical"]),
              default="tier_3_standard", help="System criticality tier")
@click.option("--frameworks", default="", help="Comma-separated regulatory frameworks (GDPR,HIPAA,PCI-DSS,CCPA)")
@click.option("--notification/--no-notification", default=False,
              help="Whether regulatory notification is required")
def severity_cmd(data_class, records, system_tier, frameworks, notification):
    """Calculate incident severity from assessment parameters.

    Uses CVSS-inspired technical scoring combined with business impact
    factors to produce a composite severity rating.
    """
    framework_list = [f.strip() for f in frameworks.split(",") if f.strip()]

    calc = SeverityCalculator()
    assessment = calc.quick_severity(
        data_classification=data_class,
        records_affected=records,
        system_criticality=system_tier,
        regulatory_frameworks=framework_list,
        notification_required=notification,
    )

    # Display results
    sev_colors = {
        "critical": "red",
        "high": "bright_red",
        "medium": "yellow",
        "low": "green",
        "informational": "blue",
    }
    color = sev_colors.get(assessment.severity_level, "white")

    table = Table(title="Severity Assessment", box=box.DOUBLE_EDGE)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Severity Level", f"[{color}]{assessment.severity_level.upper()}[/{color}]")
    table.add_row("Composite Score", f"{assessment.composite_score}/10.0")
    table.add_row("Technical Score", f"{assessment.technical_score}/10.0")
    table.add_row("Business Impact Score", f"{assessment.business_impact_score}/10.0")
    table.add_row("Confidence", assessment.confidence.capitalize())
    table.add_row("Regulatory Risk", assessment.regulatory_risk.capitalize())
    table.add_row("Response Time Target", assessment.recommended_response_time)

    if assessment.financial_impact_estimate > 0:
        table.add_row("Est. Financial Impact", f"${assessment.financial_impact_estimate:,.2f}")

    console.print(table)

    if assessment.justification:
        console.print("\n[bold]Assessment Justification:[/bold]")
        for j in assessment.justification:
            console.print(f"  - {j}")


@cli.command("timeline")
@click.option("--scenario", "-s", default=None,
              type=click.Choice(list(SCENARIO_REGISTRY.keys())),
              help="Generate timeline for a specific scenario")
@click.option("--output", "-o", default=None, help="Output file path")
def timeline_cmd(scenario, output):
    """Generate an incident response timeline.

    Creates a realistic timeline with timestamps for each phase
    of the NIST IR lifecycle.
    """
    gen = TimelineGenerator()
    events = gen.generate_scenario_timeline(
        scenario_type=scenario or "generic",
        severity="HIGH",
        commander="IR Team Lead",
    )

    formatted = gen.format_timeline()

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(formatted)
        console.print(f"[green]Timeline saved to: {output}[/green]")
    else:
        console.print(formatted)


@cli.command("evidence-guide")
def evidence_guide_cmd():
    """Display evidence collection priority order guidance.

    Shows the RFC 3227 order of volatility for digital evidence
    collection during incident response.
    """
    guidance = EvidenceTracker.get_collection_order_guidance()

    table = Table(title="Evidence Collection Priority (Order of Volatility)", box=box.DOUBLE_EDGE)
    table.add_column("Priority", style="bold cyan", width=10)
    table.add_column("Evidence Type", style="white", width=30)
    table.add_column("Volatility", style="yellow", width=20)
    table.add_column("Collection Method", style="dim", width=50)

    for item in guidance:
        table.add_row(
            item["priority"],
            item["type"],
            item["volatility"],
            item["method"],
        )

    console.print(table)


@cli.command("severity-matrix")
def severity_matrix_cmd():
    """Display the incident severity classification matrix."""
    matrix = SeverityCalculator.get_severity_matrix()

    for level, details in matrix.items():
        sev_colors = {
            "critical": "red",
            "high": "bright_red",
            "medium": "yellow",
            "low": "green",
            "informational": "blue",
        }
        color = sev_colors.get(level, "white")

        console.print(f"\n[{color} bold]{level.upper()}[/{color} bold] ({details['score_range']})")
        console.print(f"  Description:   {details['description']}")
        console.print(f"  Response Time: {details['response_time']}")
        console.print(f"  Examples:      {details['examples']}")
        console.print(f"  Escalation:    {details['escalation']}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
