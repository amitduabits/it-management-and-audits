"""
cli.py - Command-Line Interface for the Agile Sprint Simulator
===============================================================

Built with Click, providing these commands:
    sprint init    — Initialize a new sprint project with sample data
    sprint plan    — Run Sprint Planning and display the plan
    sprint run     — Execute the full sprint simulation
    sprint retro   — Run the retrospective on a completed sprint
    sprint report  — Generate Markdown and HTML reports
    sprint kanban  — Display the current Kanban board
    sprint burndown — Generate and display the burndown chart

Usage:
    python -m src.cli run --backlog data/sample_backlog.json --team data/team.json
    python -m src.cli plan --velocity 40
    python -m src.cli retro --output output/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .simulator import SprintSimulator
from .backlog import ProductBacklog
from .models import Team
from .sprint_planner import SprintPlanner
from .kanban import KanbanBoard
from .burndown import BurndownCalculator
from .retrospective import Retrospective
from .reporter import SprintReporter
from .daily_standup import StandupSimulator


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="1.4.0", prog_name="Agile Sprint Simulator")
def cli():
    """
    Agile Sprint Simulator — A hands-on tool for practicing Scrum.

    Simulate sprint planning, daily standups, burndown tracking,
    and sprint retrospectives with realistic data.
    """
    pass


# ---------------------------------------------------------------------------
# INIT command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--output-dir", "-o", default=".", help="Project root directory.")
def init(output_dir: str):
    """Initialize a new sprint simulation project with sample data."""
    root = Path(output_dir)

    # Create directory structure
    dirs = ["data", "output", "src"]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
        click.echo(f"  Created directory: {d}/")

    # Check for sample data
    backlog_path = root / "data" / "sample_backlog.json"
    team_path = root / "data" / "team.json"

    if backlog_path.exists():
        click.echo(f"  [exists] {backlog_path}")
    else:
        click.echo(f"  Sample backlog not found at {backlog_path}")
        click.echo(f"  Copy data/sample_backlog.json to this location.")

    if team_path.exists():
        click.echo(f"  [exists] {team_path}")
    else:
        click.echo(f"  Team file not found at {team_path}")
        click.echo(f"  Copy data/team.json to this location.")

    click.echo("\n  Project initialized. Run 'sprint plan' to begin.\n")


# ---------------------------------------------------------------------------
# PLAN command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--backlog", "-b", default="data/sample_backlog.json", help="Path to backlog JSON.")
@click.option("--team", "-t", default="data/team.json", help="Path to team JSON.")
@click.option("--velocity", "-v", default=None, type=int, help="Override velocity (story points).")
@click.option("--sprint-days", "-d", default=10, type=int, help="Sprint duration in days.")
@click.option("--sprint-id", default="Sprint-1", help="Sprint identifier.")
@click.option("--goal", "-g", default="Deliver core features for beta", help="Sprint goal.")
@click.option("--strategy", "-s", default="moscow",
              type=click.Choice(["moscow", "value", "wsjf", "random"]),
              help="Prioritization strategy.")
def plan(backlog, team, velocity, sprint_days, sprint_id, goal, strategy):
    """Run Sprint Planning and display the plan."""
    click.echo("\n  === SPRINT PLANNING ===\n")

    # Load data
    try:
        product_backlog = ProductBacklog.load_from_json(backlog)
    except FileNotFoundError:
        click.echo(f"  Error: Backlog file not found: {backlog}", err=True)
        sys.exit(1)

    try:
        with open(team, "r", encoding="utf-8") as f:
            team_data = json.load(f)
        scrum_team = Team.from_dict(team_data)
    except FileNotFoundError:
        click.echo(f"  Error: Team file not found: {team}", err=True)
        sys.exit(1)

    # Prioritize
    product_backlog.prioritize(strategy=strategy)
    click.echo(f"  Backlog: {len(product_backlog)} stories, {product_backlog.total_points} points")
    click.echo(f"  Strategy: {strategy}")
    click.echo(f"  Team: {scrum_team.name} ({len(scrum_team.members)} members)")

    # Plan
    planner = SprintPlanner(scrum_team, product_backlog, sprint_days=sprint_days)
    sprint = planner.plan_sprint(
        sprint_id=sprint_id,
        goal=goal,
        velocity_override=velocity,
    )

    summary = planner.planning_summary(sprint)

    click.echo(f"\n  --- Plan Summary ---")
    click.echo(f"  Sprint: {summary['sprint_id']}")
    click.echo(f"  Goal: {summary['sprint_goal']}")
    click.echo(f"  Dates: {summary['start_date']} to {summary['end_date']}")
    click.echo(f"  Velocity: {summary['velocity']} pts")
    click.echo(f"  Stories: {summary['stories_committed']}")
    click.echo(f"  Points: {summary['total_story_points']}")
    click.echo(f"  Task hours: {summary['total_task_hours']}")

    click.echo(f"\n  --- Committed Stories ---")
    for s in summary["stories"]:
        click.echo(f"    [{s['id']}] {s['title']} ({s['points']} pts, {s['priority']})")

    click.echo(f"\n  --- Team Utilization ---")
    for name, util in summary["member_utilization"].items():
        click.echo(
            f"    {name}: {util['assigned_hours']}/{util['capacity_hours']} hrs "
            f"({util['utilization_pct']}%)"
        )

    click.echo()


# ---------------------------------------------------------------------------
# RUN command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--backlog", "-b", default="data/sample_backlog.json", help="Path to backlog JSON.")
@click.option("--team", "-t", default="data/team.json", help="Path to team JSON.")
@click.option("--output", "-o", default="output", help="Output directory.")
@click.option("--sprint-days", "-d", default=10, type=int, help="Sprint duration.")
@click.option("--sprint-id", default="Sprint-1", help="Sprint identifier.")
@click.option("--goal", "-g", default="Deliver core mobile banking features", help="Sprint goal.")
@click.option("--seed", default=None, type=int, help="Random seed for reproducibility.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress detailed output.")
def run(backlog, team, output, sprint_days, sprint_id, goal, seed, quiet):
    """Execute a full sprint simulation end-to-end."""
    sim = SprintSimulator(
        backlog_path=backlog,
        team_path=team,
        output_dir=output,
        sprint_days=sprint_days,
        sprint_id=sprint_id,
        sprint_goal=goal,
        verbose=not quiet,
        seed=seed,
    )

    try:
        results = sim.run()
        click.echo("\n  Simulation complete. Output files:")
        for key, path in results.items():
            click.echo(f"    {key}: {path}")
        click.echo()
    except Exception as e:
        click.echo(f"\n  Error during simulation: {e}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# RETRO command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--sprint-data", "-s", default="output/sprint_data.json",
              help="Path to saved sprint data JSON.")
@click.option("--output", "-o", default="output", help="Output directory.")
def retro(sprint_data, output):
    """Run a sprint retrospective on saved sprint data."""
    click.echo("\n  === SPRINT RETROSPECTIVE ===\n")

    try:
        with open(sprint_data, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        click.echo(f"  Error: Sprint data not found: {sprint_data}", err=True)
        click.echo("  Run a simulation first: sprint run", err=True)
        sys.exit(1)

    from .models import Sprint, SprintBacklog, UserStory
    from datetime import date as date_cls

    # Reconstruct sprint from saved data
    stories = [UserStory.from_dict(sd) for sd in data.get("backlog", {}).get("stories", [])]
    sprint_backlog = SprintBacklog(
        stories=stories,
        capacity=data.get("backlog", {}).get("capacity", 0),
    )

    sprint = Sprint(
        sprint_id=data.get("sprint_id", "Sprint-?"),
        goal=data.get("goal", "Unknown"),
        start_date=date_cls.fromisoformat(data.get("start_date", date_cls.today().isoformat())),
        duration_days=data.get("duration_days", 10),
        backlog=sprint_backlog,
        velocity=data.get("velocity", 0),
        daily_logs=data.get("daily_logs", []),
        blockers_log=data.get("blockers_log", []),
    )

    retro_engine = Retrospective(sprint)
    result = retro_engine.run()
    retro_engine.display()

    # Save retro results
    retro_path = Path(output) / "retro_results.json"
    retro_path.parent.mkdir(parents=True, exist_ok=True)
    with open(retro_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)
    click.echo(f"\n  Retro results saved to: {retro_path.resolve()}\n")


# ---------------------------------------------------------------------------
# REPORT command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--sprint-data", "-s", default="output/sprint_data.json",
              help="Path to saved sprint data JSON.")
@click.option("--output", "-o", default="output", help="Output directory.")
@click.option("--format", "-f", "fmt", default="both",
              type=click.Choice(["markdown", "html", "both"]),
              help="Report format.")
def report(sprint_data, output, fmt):
    """Generate sprint summary reports."""
    click.echo("\n  === GENERATING REPORTS ===\n")

    try:
        with open(sprint_data, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        click.echo(f"  Error: Sprint data not found: {sprint_data}", err=True)
        sys.exit(1)

    from .models import Sprint, SprintBacklog, UserStory
    from datetime import date as date_cls

    stories = [UserStory.from_dict(sd) for sd in data.get("backlog", {}).get("stories", [])]
    sprint_backlog = SprintBacklog(
        stories=stories,
        capacity=data.get("backlog", {}).get("capacity", 0),
    )

    sprint = Sprint(
        sprint_id=data.get("sprint_id", "Sprint-?"),
        goal=data.get("goal", "Unknown"),
        start_date=date_cls.fromisoformat(data.get("start_date", date_cls.today().isoformat())),
        duration_days=data.get("duration_days", 10),
        backlog=sprint_backlog,
        velocity=data.get("velocity", 0),
        daily_logs=data.get("daily_logs", []),
        blockers_log=data.get("blockers_log", []),
    )

    reporter = SprintReporter(sprint=sprint)

    if fmt in ("markdown", "both"):
        md_path = reporter.generate_markdown(str(Path(output) / "sprint_report.md"))
        click.echo(f"  Markdown report: {md_path}")

    if fmt in ("html", "both"):
        html_path = reporter.generate_html(str(Path(output) / "sprint_report.html"))
        click.echo(f"  HTML report: {html_path}")

    click.echo()


# ---------------------------------------------------------------------------
# KANBAN command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--sprint-data", "-s", default="output/sprint_data.json",
              help="Path to saved sprint data JSON.")
def kanban(sprint_data):
    """Display the Kanban board for a sprint."""
    try:
        with open(sprint_data, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        click.echo(f"  Error: Sprint data not found: {sprint_data}", err=True)
        sys.exit(1)

    from .models import Sprint, SprintBacklog, UserStory
    from datetime import date as date_cls

    stories = [UserStory.from_dict(sd) for sd in data.get("backlog", {}).get("stories", [])]
    sprint_backlog = SprintBacklog(
        stories=stories,
        capacity=data.get("backlog", {}).get("capacity", 0),
    )

    sprint = Sprint(
        sprint_id=data.get("sprint_id", "Sprint-?"),
        goal=data.get("goal", "Unknown"),
        start_date=date_cls.fromisoformat(data.get("start_date", date_cls.today().isoformat())),
        duration_days=data.get("duration_days", 10),
        backlog=sprint_backlog,
        velocity=data.get("velocity", 0),
        daily_logs=data.get("daily_logs", []),
    )

    board = KanbanBoard(sprint)
    board.display()


# ---------------------------------------------------------------------------
# BURNDOWN command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--sprint-data", "-s", default="output/sprint_data.json",
              help="Path to saved sprint data JSON.")
@click.option("--output", "-o", default="output/burndown.png", help="Output image path.")
@click.option("--metric", "-m", default="hours",
              type=click.Choice(["hours", "points"]),
              help="Burndown metric.")
@click.option("--ascii", "use_ascii", is_flag=True, help="Use ASCII chart instead of image.")
def burndown(sprint_data, output, metric, use_ascii):
    """Generate and display the burndown chart."""
    try:
        with open(sprint_data, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        click.echo(f"  Error: Sprint data not found: {sprint_data}", err=True)
        sys.exit(1)

    from .models import Sprint, SprintBacklog, UserStory
    from datetime import date as date_cls

    stories = [UserStory.from_dict(sd) for sd in data.get("backlog", {}).get("stories", [])]
    sprint_backlog = SprintBacklog(
        stories=stories,
        capacity=data.get("backlog", {}).get("capacity", 0),
    )

    sprint = Sprint(
        sprint_id=data.get("sprint_id", "Sprint-?"),
        goal=data.get("goal", "Unknown"),
        start_date=date_cls.fromisoformat(data.get("start_date", date_cls.today().isoformat())),
        duration_days=data.get("duration_days", 10),
        backlog=sprint_backlog,
        velocity=data.get("velocity", 0),
        daily_logs=data.get("daily_logs", []),
    )

    calc = BurndownCalculator(sprint, metric=metric)

    if use_ascii:
        click.echo(calc.ascii_chart())
    else:
        try:
            path = calc.plot(output_path=output)
            click.echo(f"\n  Burndown chart saved to: {path}\n")
        except ImportError:
            click.echo("  matplotlib not available. Using ASCII chart:\n")
            click.echo(calc.ascii_chart())

    # Show trend
    trend = calc.trend_analysis()
    click.echo(f"\n  Trend: {trend['overall']}")
    projected = calc.projected_completion_day()
    if projected:
        click.echo(f"  Projected completion: Day {projected}")
    click.echo()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
