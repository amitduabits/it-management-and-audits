"""
query_runner.py -- Execute SQL statements and render results as formatted tables.

Uses the *rich* library for terminal output, falling back to plain-text
tabulation when rich is unavailable.
"""

from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.schema import get_connection, DB_PATH

console = Console()

# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------


def execute_query(
    sql: str,
    params: tuple = (),
    db_path: Optional[Path] = None,
) -> tuple[list[str], list[tuple]]:
    """
    Execute *sql* and return ``(column_names, rows)``.

    Parameters
    ----------
    sql : str
        A single SQL statement (SELECT, PRAGMA, etc.).
    params : tuple
        Bind parameters.
    db_path : Path, optional
        Override for the default database path.

    Returns
    -------
    columns : list[str]
        Column names from the result set.
    rows : list[tuple]
        Result rows.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.execute(sql, params)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = [tuple(row) for row in cur.fetchall()]
        return columns, rows
    finally:
        conn.close()


def execute_query_raw(
    sql: str,
    params: tuple = (),
    db_path: Optional[Path] = None,
) -> list[dict]:
    """Execute *sql* and return rows as a list of dicts."""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(sql, params)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Rich display helpers
# ---------------------------------------------------------------------------


def _format_cell(value) -> str:
    """Convert a cell value to a display string."""
    if value is None:
        return "[dim]NULL[/dim]"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def display_results(
    columns: list[str],
    rows: list[tuple],
    title: str = "Query Results",
    max_rows: int = 200,
) -> None:
    """
    Print a rich table to the console.

    Parameters
    ----------
    columns : list[str]
        Column header names.
    rows : list[tuple]
        Data rows.
    title : str
        Table title shown above the header.
    max_rows : int
        Truncate output after this many rows.
    """
    if not columns:
        console.print("[yellow]Query returned no columns.[/yellow]")
        return

    table = Table(title=title, show_lines=False, header_style="bold cyan")
    for col in columns:
        table.add_column(col, overflow="fold")

    displayed = rows[:max_rows]
    for row in displayed:
        table.add_row(*[_format_cell(v) for v in row])

    console.print(table)

    if len(rows) > max_rows:
        console.print(
            f"[dim]... showing {max_rows} of {len(rows)} rows[/dim]"
        )
    else:
        console.print(f"[dim]{len(rows)} row(s) returned.[/dim]")


def run_and_display(
    sql: str,
    params: tuple = (),
    db_path: Optional[Path] = None,
    title: str = "Query Results",
) -> None:
    """Execute *sql*, measure wall time, and print a formatted table."""
    start = time.perf_counter()
    try:
        columns, rows = execute_query(sql, params, db_path)
    except sqlite3.Error as exc:
        console.print(Panel(f"[red bold]SQL Error:[/red bold] {exc}", title="Error"))
        return

    elapsed_ms = (time.perf_counter() - start) * 1000
    display_results(columns, rows, title=title)
    console.print(f"[dim]Elapsed: {elapsed_ms:.1f} ms[/dim]\n")


# ---------------------------------------------------------------------------
# Batch runner -- read a .sql file and execute each statement block
# ---------------------------------------------------------------------------


def _split_sql_file(content: str) -> list[tuple[str, str]]:
    """
    Split a multi-statement SQL file into (comment, sql) pairs.

    Blocks are separated by semicolons.  The comment is the leading
    ``-- ...`` line(s) immediately above each statement.
    """
    blocks: list[tuple[str, str]] = []
    current_comment_lines: list[str] = []
    current_sql_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            if current_sql_lines:
                # blank line inside a statement -- keep it
                current_sql_lines.append(line)
            continue

        if stripped.startswith("--") and not current_sql_lines:
            current_comment_lines.append(stripped.lstrip("-").strip())
        else:
            current_sql_lines.append(line)

        if stripped.endswith(";"):
            sql_text = "\n".join(current_sql_lines).strip()
            comment_text = " | ".join(current_comment_lines) if current_comment_lines else ""
            if sql_text:
                blocks.append((comment_text, sql_text))
            current_comment_lines = []
            current_sql_lines = []

    # Handle trailing block without semicolon
    if current_sql_lines:
        sql_text = "\n".join(current_sql_lines).strip()
        comment_text = " | ".join(current_comment_lines) if current_comment_lines else ""
        if sql_text:
            blocks.append((comment_text, sql_text))

    return blocks


def run_sql_file(
    filepath: Path,
    db_path: Optional[Path] = None,
    limit: Optional[int] = None,
) -> None:
    """
    Read *filepath*, split into individual statements, and execute each
    with formatted output.

    Parameters
    ----------
    filepath : Path
        Path to a ``.sql`` file.
    db_path : Path, optional
        Database override.
    limit : int, optional
        Only execute the first *limit* statements.
    """
    content = filepath.read_text(encoding="utf-8")
    blocks = _split_sql_file(content)

    if limit:
        blocks = blocks[:limit]

    for idx, (comment, sql) in enumerate(blocks, 1):
        title = f"[{idx}/{len(blocks)}] {comment}" if comment else f"Statement {idx}"
        console.rule(title)
        console.print(f"[dim]{sql[:300]}{'...' if len(sql) > 300 else ''}[/dim]\n")
        run_and_display(sql, db_path=db_path, title=title)
