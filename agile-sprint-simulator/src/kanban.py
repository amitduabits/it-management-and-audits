"""
kanban.py - Terminal Kanban Board Display
==========================================

Renders a Kanban board in the terminal using the Rich library.
Columns represent the workflow stages:
    To Do | In Progress | In Review | Done | Blocked

Each card shows the story ID, title, assignee, and progress bar.

Usage:
    from src.kanban import KanbanBoard
    board = KanbanBoard(sprint)
    board.display()
"""

from __future__ import annotations

from typing import List, Dict, Optional

from .models import Sprint, UserStory, StoryStatus, Task, TaskStatus


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

COLUMNS = [
    {"status": StoryStatus.TODO, "title": "TO DO", "style": "bright_white on grey30"},
    {"status": StoryStatus.IN_PROGRESS, "title": "IN PROGRESS", "style": "bright_white on blue"},
    {"status": StoryStatus.IN_REVIEW, "title": "IN REVIEW", "style": "bright_white on dark_orange"},
    {"status": StoryStatus.DONE, "title": "DONE", "style": "bright_white on green"},
    {"status": StoryStatus.BLOCKED, "title": "BLOCKED", "style": "bright_white on red"},
]


class KanbanBoard:
    """
    Builds and displays a Kanban board for a sprint.

    Attributes:
        sprint:  The sprint whose backlog to visualize.
    """

    def __init__(self, sprint: Sprint):
        self.sprint = sprint

    def get_stories_by_column(self) -> Dict[StoryStatus, List[UserStory]]:
        """Group stories by their current status."""
        grouped: Dict[StoryStatus, List[UserStory]] = {
            col["status"]: [] for col in COLUMNS
        }
        for story in self.sprint.backlog.stories:
            if story.status in grouped:
                grouped[story.status].append(story)
            else:
                grouped[StoryStatus.TODO].append(story)
        return grouped

    def _build_card_text(self, story: UserStory) -> str:
        """Build a plain-text representation of a story card."""
        lines = []
        lines.append(f"[bold]{story.story_id}[/bold]")
        lines.append(f"{story.title}")
        lines.append(f"Points: {story.story_points}  |  Priority: {story.priority.value}")

        if story.assigned_to:
            lines.append(f"Assigned: {story.assigned_to}")

        # Task progress
        total_tasks = len(story.tasks)
        done_tasks = sum(1 for t in story.tasks if t.is_done)
        if total_tasks > 0:
            pct = story.progress_pct
            bar_width = 15
            filled = int((pct / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            lines.append(f"Tasks: {done_tasks}/{total_tasks}  [{bar}] {pct}%")

        return "\n".join(lines)

    def display(self) -> None:
        """Render the Kanban board to the terminal using Rich."""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            from rich.columns import Columns as RichColumns
            from rich.text import Text
            from rich import box
        except ImportError:
            # Fallback to plain-text
            self._display_plain()
            return

        console = Console()
        grouped = self.get_stories_by_column()

        # Header
        console.print()
        console.print(
            f"  [bold bright_cyan]KANBAN BOARD[/bold bright_cyan]  —  "
            f"{self.sprint.sprint_id}  |  "
            f"Day {self.sprint.current_day}/{self.sprint.duration_days}  |  "
            f"Goal: {self.sprint.goal}",
        )
        console.print()

        # Build a table with one column per status
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold",
            expand=True,
            padding=(0, 1),
        )

        for col_def in COLUMNS:
            status = col_def["status"]
            count = len(grouped.get(status, []))
            header = f"{col_def['title']} ({count})"
            table.add_column(header, style=None, justify="left", min_width=25)

        # Determine max number of rows
        max_cards = max(len(stories) for stories in grouped.values()) if grouped else 0

        for row_idx in range(max_cards):
            row_cells = []
            for col_def in COLUMNS:
                status = col_def["status"]
                stories = grouped.get(status, [])
                if row_idx < len(stories):
                    story = stories[row_idx]
                    card = self._build_rich_card(story, col_def["style"])
                    row_cells.append(card)
                else:
                    row_cells.append("")
            table.add_row(*row_cells)

        console.print(table)

        # Summary footer
        total = len(self.sprint.backlog.stories)
        done = len(grouped.get(StoryStatus.DONE, []))
        blocked = len(grouped.get(StoryStatus.BLOCKED, []))
        points_done = self.sprint.backlog.completed_points
        points_total = self.sprint.backlog.total_points

        console.print(
            f"  [dim]Stories: {done}/{total} done  |  "
            f"Points: {points_done}/{points_total}  |  "
            f"Blocked: {blocked}  |  "
            f"Completion: {self.sprint.backlog.completion_pct}%[/dim]"
        )
        console.print()

    def _build_rich_card(self, story: UserStory, style: str) -> str:
        """Build a Rich-formatted card string."""
        lines = []
        lines.append(f"[bold cyan]{story.story_id}[/bold cyan]")
        lines.append(f"[white]{story.title}[/white]")

        prio_colors = {
            "Must Have": "red",
            "Should Have": "yellow",
            "Could Have": "green",
            "Won't Have": "dim",
        }
        pcolor = prio_colors.get(story.priority.value, "white")
        lines.append(f"[{pcolor}]{story.priority.value}[/{pcolor}] | {story.story_points} pts")

        if story.assigned_to:
            lines.append(f"[dim]-> {story.assigned_to}[/dim]")

        total_tasks = len(story.tasks)
        done_tasks = sum(1 for t in story.tasks if t.is_done)
        if total_tasks > 0:
            pct = story.progress_pct
            filled = int((pct / 100) * 10)
            bar = "[green]" + "█" * filled + "[/green][dim]" + "░" * (10 - filled) + "[/dim]"
            lines.append(f"{bar} {pct}%  ({done_tasks}/{total_tasks})")

        return "\n".join(lines)

    # -- Plain-text fallback ------------------------------------------------

    def _display_plain(self) -> None:
        """Render a simple text-based Kanban board without Rich."""
        grouped = self.get_stories_by_column()
        col_width = 30
        separator = "+" + (("-" * col_width + "+") * len(COLUMNS))

        print(f"\n  KANBAN BOARD — {self.sprint.sprint_id}")
        print(f"  Sprint Day: {self.sprint.current_day}/{self.sprint.duration_days}")
        print(f"  Goal: {self.sprint.goal}\n")

        # Headers
        print(separator)
        header = "|"
        for col_def in COLUMNS:
            status = col_def["status"]
            count = len(grouped.get(status, []))
            h = f" {col_def['title']} ({count})"
            header += h.ljust(col_width) + "|"
        print(header)
        print(separator)

        max_cards = max(len(s) for s in grouped.values()) if grouped else 0

        for row_idx in range(max_cards):
            # Story ID line
            line = "|"
            for col_def in COLUMNS:
                stories = grouped.get(col_def["status"], [])
                if row_idx < len(stories):
                    s = stories[row_idx]
                    cell = f" {s.story_id}: {s.title[:18]}"
                else:
                    cell = ""
                line += cell.ljust(col_width) + "|"
            print(line)

            # Details line
            line = "|"
            for col_def in COLUMNS:
                stories = grouped.get(col_def["status"], [])
                if row_idx < len(stories):
                    s = stories[row_idx]
                    cell = f" {s.story_points}pts | {s.progress_pct}%"
                else:
                    cell = ""
                line += cell.ljust(col_width) + "|"
            print(line)
            print(separator)

        total = len(self.sprint.backlog.stories)
        done = len(grouped.get(StoryStatus.DONE, []))
        print(f"\n  Done: {done}/{total} stories | "
              f"{self.sprint.backlog.completed_points}/{self.sprint.backlog.total_points} points\n")

    # -- Data export --------------------------------------------------------

    def to_dict(self) -> Dict:
        """Export board state as a dictionary."""
        grouped = self.get_stories_by_column()
        return {
            "sprint_id": self.sprint.sprint_id,
            "day": self.sprint.current_day,
            "columns": {
                col_def["title"]: [
                    {
                        "story_id": s.story_id,
                        "title": s.title,
                        "points": s.story_points,
                        "progress": s.progress_pct,
                        "assigned_to": s.assigned_to,
                    }
                    for s in grouped.get(col_def["status"], [])
                ]
                for col_def in COLUMNS
            },
        }
