"""
IT Governance Framework Mapper - Report Generator

Generates compliance reports in terminal table format (Rich)
and standalone HTML format (Jinja2).
"""

import os
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from jinja2 import Environment, FileSystemLoader
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False


TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


def print_scorecard(scorecard):
    """Print a compliance scorecard to the terminal using Rich.

    Args:
        scorecard: Scorecard dict from analyzer.generate_compliance_scorecard()
    """
    if not RICH_AVAILABLE:
        _print_scorecard_plain(scorecard)
        return

    console = Console()

    # Title
    title = f"{scorecard['framework']} Compliance Scorecard"
    console.print(Panel(title, style="bold blue"))

    # Domain table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Domain", min_width=25)
    table.add_column("Covered", justify="center", min_width=8)
    table.add_column("Total", justify="center", min_width=8)
    table.add_column("Coverage", min_width=22)
    table.add_column("Status", justify="center", min_width=10)

    for domain in scorecard["domains"]:
        status_color = _status_color(domain["status"])
        coverage_str = f"{domain['visual']} {domain['percentage']}%"
        table.add_row(
            domain["name"],
            str(domain["covered"]),
            str(domain["total"]),
            coverage_str,
            f"[{status_color}]{domain['status']}[/{status_color}]"
        )

    # Summary row
    overall = scorecard["overall"]
    bar_filled = int(overall["overall_coverage_percentage"] / 10)
    bar_empty = 10 - bar_filled
    overall_bar = "█" * bar_filled + "░" * bar_empty
    overall_color = _status_color(overall["status"])

    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{overall['covered_controls']}[/bold]",
        f"[bold]{overall['total_controls']}[/bold]",
        f"[bold]{overall_bar} {overall['overall_coverage_percentage']}%[/bold]",
        f"[bold {overall_color}]{overall['status']}[/bold {overall_color}]"
    )

    console.print(table)


def print_gaps(gaps, limit=10):
    """Print priority gaps to the terminal.

    Args:
        gaps: List of gaps from analyzer.identify_priority_gaps()
        limit: Maximum number of gaps to display
    """
    if not RICH_AVAILABLE:
        _print_gaps_plain(gaps, limit)
        return

    console = Console()
    console.print(Panel("Priority Gaps — Uncovered Controls", style="bold red"))

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("#", justify="right", min_width=3)
    table.add_column("Control ID", min_width=8)
    table.add_column("Control Name", min_width=30)
    table.add_column("Domain", min_width=20)
    table.add_column("Priority", justify="center", min_width=8)

    for i, gap in enumerate(gaps[:limit], 1):
        priority_color = "red" if gap["priority_score"] > 70 else "yellow" if gap["priority_score"] > 40 else "green"
        table.add_row(
            str(i),
            gap["control_id"],
            gap["control_name"],
            gap["domain"],
            f"[{priority_color}]{gap['priority_score']}[/{priority_color}]"
        )

    console.print(table)

    if len(gaps) > limit:
        console.print(f"\n  ... and {len(gaps) - limit} more gaps. Generate full report for details.\n")


def print_mappings(mappings, limit=20):
    """Print process-to-framework mappings to the terminal.

    Args:
        mappings: List of mapping dicts from mapper
        limit: Maximum number of rows to display
    """
    if not RICH_AVAILABLE:
        _print_mappings_plain(mappings, limit)
        return

    console = Console()
    console.print(Panel("Process → Framework Mappings", style="bold green"))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Process", min_width=25)
    table.add_column("Framework Control", min_width=30)
    table.add_column("ID", min_width=8)
    table.add_column("Score", justify="center", min_width=8)

    for m in mappings[:limit]:
        target_name = m.get("objective_name") or m.get("practice_name", "")
        target_id = m.get("objective_id") or m.get("practice_id", "")
        score = m["confidence_score"]
        score_color = "green" if score > 0.5 else "yellow" if score > 0.3 else "red"

        table.add_row(
            m["process_name"],
            target_name,
            target_id,
            f"[{score_color}]{score:.2f}[/{score_color}]"
        )

    console.print(table)


def generate_html_report(scorecard, gaps, mappings, output_path):
    """Generate an HTML compliance report.

    Args:
        scorecard: Compliance scorecard dict
        gaps: Priority gaps list
        mappings: Process-to-framework mappings
        output_path: File path to write the HTML report
    """
    if JINJA_AVAILABLE:
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        template = env.get_template("report.html")
        html = template.render(
            scorecard=scorecard,
            gaps=gaps,
            mappings=mappings,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            framework=scorecard["framework"]
        )
    else:
        html = _generate_html_fallback(scorecard, gaps, mappings)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {output_path}")


# --- Plain text fallbacks when Rich is not available ---

def _print_scorecard_plain(scorecard):
    print(f"\n{'=' * 60}")
    print(f"  {scorecard['framework']} Compliance Scorecard")
    print(f"{'=' * 60}")
    for d in scorecard["domains"]:
        print(f"  {d['name']:<25} {d['covered']}/{d['total']} ({d['percentage']}%) [{d['status']}]")
    overall = scorecard["overall"]
    print(f"{'─' * 60}")
    print(f"  {'TOTAL':<25} {overall['covered_controls']}/{overall['total_controls']} ({overall['overall_coverage_percentage']}%)")
    print()


def _print_gaps_plain(gaps, limit):
    print(f"\nPriority Gaps (top {limit}):")
    for i, g in enumerate(gaps[:limit], 1):
        print(f"  {i}. [{g['control_id']}] {g['control_name']} (Priority: {g['priority_score']})")


def _print_mappings_plain(mappings, limit):
    print(f"\nMappings (top {limit}):")
    for m in mappings[:limit]:
        target = m.get("objective_name") or m.get("practice_name", "")
        tid = m.get("objective_id") or m.get("practice_id", "")
        print(f"  {m['process_name']} → [{tid}] {target} (Score: {m['confidence_score']:.2f})")


def _generate_html_fallback(scorecard, gaps, mappings):
    """Generate basic HTML without Jinja2."""
    rows = ""
    for d in scorecard["domains"]:
        rows += f"<tr><td>{d['name']}</td><td>{d['covered']}</td><td>{d['total']}</td><td>{d['percentage']}%</td><td>{d['status']}</td></tr>\n"

    return f"""<!DOCTYPE html>
<html><head><title>{scorecard['framework']} Compliance Report</title>
<style>body{{font-family:Arial,sans-serif;margin:40px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background:#2563eb;color:white}}</style>
</head><body>
<h1>{scorecard['framework']} Compliance Report</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<h2>Coverage Scorecard</h2>
<table><tr><th>Domain</th><th>Covered</th><th>Total</th><th>Coverage</th><th>Status</th></tr>
{rows}</table>
</body></html>"""


def _status_color(status):
    """Map status to Rich color."""
    return {
        "Strong": "green",
        "Moderate": "yellow",
        "Partial": "dark_orange",
        "Weak": "red",
        "Critical": "bold red"
    }.get(status, "white")
