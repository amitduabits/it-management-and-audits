"""
cli.py -- Click-based command-line interface for Financial Data Manager.

Commands
--------
- init-db        Create the database schema.
- seed           Populate with synthetic data.
- query SQL      Execute an ad-hoc SQL statement.
- check-quality  Run all 10 data quality checks.
- report         Generate Markdown + HTML DQ reports.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src import DB_PATH, ensure_dirs
from src.schema import create_schema, get_row_counts, get_table_names, table_exists
from src.seed_data import seed_all
from src.query_runner import run_and_display, run_sql_file
from src.data_quality import run_all_checks
from src.reporter import generate_reports

console = Console()


@click.group()
@click.version_option(version="1.4.0", prog_name="financial-data-manager")
def cli():
    """Financial Data Manager -- schema, seed, query, quality, report."""
    pass


# ---------------------------------------------------------------------------
# init-db
# ---------------------------------------------------------------------------


@cli.command("init-db")
def init_db():
    """Create the database schema (tables, indexes, constraints)."""
    ensure_dirs()
    console.print("[bold]Initialising database ...[/bold]")
    create_schema()

    tables = get_table_names()
    tbl = Table(title="Created Tables", show_lines=False)
    tbl.add_column("Table", style="cyan")
    for t in tables:
        tbl.add_row(t)
    console.print(tbl)
    console.print(f"\n[green]Schema created at:[/green] {DB_PATH}")


# ---------------------------------------------------------------------------
# seed
# ---------------------------------------------------------------------------


@cli.command("seed")
@click.option("--force", is_flag=True, help="Drop and recreate before seeding.")
def seed(force):
    """Generate synthetic financial data (500 customers, 1000 accounts, 5000 txns)."""
    ensure_dirs()

    if force:
        from src.schema import drop_all
        console.print("[yellow]Dropping existing tables ...[/yellow]")
        drop_all()
        create_schema()

    console.print("[bold]Seeding database ...[/bold]")
    counts = seed_all(verbose=False)

    tbl = Table(title="Seed Results", show_lines=False)
    tbl.add_column("Entity", style="cyan")
    tbl.add_column("Rows", justify="right", style="green")
    for entity, count in counts.items():
        tbl.add_row(entity, f"{count:,}")
    console.print(tbl)
    console.print(f"\n[green]Database populated at:[/green] {DB_PATH}")


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


@cli.command("query")
@click.argument("sql")
def query(sql):
    """Execute a SQL statement and display results in a formatted table."""
    if not DB_PATH.exists():
        console.print("[red]Database not found. Run init-db and seed first.[/red]")
        raise SystemExit(1)

    run_and_display(sql)


# ---------------------------------------------------------------------------
# run-file  (bonus -- run a .sql file)
# ---------------------------------------------------------------------------


@cli.command("run-file")
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option("--limit", type=int, default=None, help="Run only first N statements.")
def run_file(filepath, limit):
    """Execute every statement in a .sql file with formatted output."""
    if not DB_PATH.exists():
        console.print("[red]Database not found. Run init-db and seed first.[/red]")
        raise SystemExit(1)

    run_sql_file(filepath, limit=limit)


# ---------------------------------------------------------------------------
# check-quality
# ---------------------------------------------------------------------------


@cli.command("check-quality")
def check_quality():
    """Run all 10 data quality checks and display results."""
    if not DB_PATH.exists():
        console.print("[red]Database not found. Run init-db and seed first.[/red]")
        raise SystemExit(1)

    console.print("[bold]Running data quality checks ...[/bold]\n")
    results = run_all_checks()

    tbl = Table(title="Data Quality Results", show_lines=True)
    tbl.add_column("#", justify="right", width=3)
    tbl.add_column("Check ID", style="cyan", width=8)
    tbl.add_column("Dimension", width=14)
    tbl.add_column("Name", width=32)
    tbl.add_column("Result", width=6, justify="center")
    tbl.add_column("Affected", justify="right", width=10)
    tbl.add_column("Total", justify="right", width=10)
    tbl.add_column("Pass Rate", justify="right", width=10)

    for idx, r in enumerate(results, 1):
        result_str = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        tbl.add_row(
            str(idx),
            r.check_id,
            r.dimension,
            r.name,
            result_str,
            f"{r.affected_rows:,}",
            f"{r.total_rows:,}",
            f"{r.pass_rate * 100:.2f}%",
        )

    console.print(tbl)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    console.print(
        f"\n[bold]Summary:[/bold] {passed} passed, {failed} failed, "
        f"{passed / len(results) * 100:.1f}% overall pass rate."
    )

    # Print details for failures
    failures = [r for r in results if not r.passed]
    if failures:
        console.print("\n[bold red]Failed Check Details:[/bold red]")
        for r in failures:
            console.print(Panel(
                f"[bold]{r.check_id}:[/bold] {r.name}\n"
                f"[dim]{r.details}[/dim]\n"
                f"Affected: {r.affected_rows:,} / {r.total_rows:,}",
                title=f"{r.dimension} -- {r.check_id}",
                border_style="red",
            ))


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


@cli.command("report")
def report():
    """Generate Markdown and HTML data quality reports."""
    if not DB_PATH.exists():
        console.print("[red]Database not found. Run init-db and seed first.[/red]")
        raise SystemExit(1)

    console.print("[bold]Running checks and generating reports ...[/bold]\n")
    results = run_all_checks()
    md_path, html_path = generate_reports(results)

    console.print(f"[green]Markdown report:[/green] {md_path}")
    console.print(f"[green]HTML report:[/green]     {html_path}")

    passed = sum(1 for r in results if r.passed)
    console.print(
        f"\n[bold]Overall:[/bold] {passed}/{len(results)} checks passed "
        f"({passed / len(results) * 100:.1f}%)."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
