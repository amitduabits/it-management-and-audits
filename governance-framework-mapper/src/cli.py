"""
IT Governance Framework Mapper - CLI Interface

Provides command-line access to mapping, analysis, and reporting functions.
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import click
from src.mapper import load_org_processes, map_processes, map_to_cobit, map_to_itil
from src.analyzer import analyze_coverage, identify_priority_gaps, generate_compliance_scorecard
from src.reporter import print_scorecard, print_gaps, print_mappings, generate_html_report


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """IT Governance Framework Mapper

    Map organizational IT processes to COBIT 2019 and ITIL v4 frameworks.
    Perform gap analysis and generate compliance reports.
    """
    pass


@cli.command()
@click.option("--input", "-i", "input_file", required=True, help="Path to organization processes JSON file")
@click.option("--framework", "-f", type=click.Choice(["cobit", "itil", "all"]), default="all", help="Target framework")
@click.option("--threshold", "-t", default=0.15, type=float, help="Minimum match score (0.0-1.0)")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON instead of table")
def map(input_file, framework, threshold, json_output):
    """Map organization processes to framework controls."""
    processes = load_org_processes(input_file)
    click.echo(f"Loaded {len(processes)} organizational processes.\n")

    results = map_processes(processes, framework, threshold)

    for fw_name, mappings in results.items():
        if json_output:
            click.echo(json.dumps(mappings, indent=2))
        else:
            click.echo(f"\n--- {fw_name.upper()} Mappings ({len(mappings)} matches) ---\n")
            print_mappings(mappings)


@cli.command()
@click.option("--input", "-i", "input_file", required=True, help="Path to organization processes JSON file")
@click.option("--framework", "-f", type=click.Choice(["cobit", "itil"]), required=True, help="Framework to analyze")
@click.option("--threshold", "-t", default=0.15, type=float, help="Minimum match score")
@click.option("--show-gaps", "-g", is_flag=True, help="Show priority gaps")
def analyze(input_file, framework, threshold, show_gaps):
    """Run gap analysis against a framework."""
    processes = load_org_processes(input_file)
    click.echo(f"Loaded {len(processes)} processes. Analyzing against {framework.upper()}...\n")

    if framework == "cobit":
        mappings = map_to_cobit(processes, threshold)
    else:
        mappings = map_to_itil(processes, threshold)

    analysis = analyze_coverage(mappings, framework)
    scorecard = generate_compliance_scorecard(analysis)
    print_scorecard(scorecard)

    if show_gaps:
        gaps = identify_priority_gaps(analysis)
        click.echo()
        print_gaps(gaps)


@cli.command()
@click.option("--input", "-i", "input_file", required=True, help="Path to organization processes JSON file")
@click.option("--framework", "-f", type=click.Choice(["cobit", "itil"]), default="cobit", help="Framework to report on")
@click.option("--format", "output_format", type=click.Choice(["terminal", "html"]), default="terminal", help="Report format")
@click.option("--output", "-o", "output_file", default="reports/compliance_report.html", help="Output file for HTML reports")
@click.option("--threshold", "-t", default=0.15, type=float, help="Minimum match score")
def report(input_file, framework, output_format, output_file, threshold):
    """Generate a compliance report."""
    processes = load_org_processes(input_file)

    if framework == "cobit":
        mappings = map_to_cobit(processes, threshold)
    else:
        mappings = map_to_itil(processes, threshold)

    analysis = analyze_coverage(mappings, framework)
    scorecard = generate_compliance_scorecard(analysis)
    gaps = identify_priority_gaps(analysis)

    if output_format == "terminal":
        print_scorecard(scorecard)
        click.echo()
        print_gaps(gaps, limit=15)
        click.echo()
        print_mappings(mappings, limit=25)
    else:
        generate_html_report(scorecard, gaps, mappings, output_file)
        click.echo(f"HTML report saved to: {output_file}")


if __name__ == "__main__":
    cli()
