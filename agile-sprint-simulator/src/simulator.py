"""
simulator.py - Main Sprint Simulation Orchestrator
====================================================

Ties together all components to run a full end-to-end sprint simulation:

    1. Load product backlog and team data.
    2. Run Sprint Planning — select stories, generate tasks, assign work.
    3. Simulate daily standups — progress, blockers, status changes.
    4. Track burndown data throughout the sprint.
    5. Run Sprint Retrospective — analyze metrics and generate insights.
    6. Display Kanban board at key points.
    7. Generate reports (Markdown + HTML).

Usage:
    from src.simulator import SprintSimulator
    sim = SprintSimulator(backlog_path="data/sample_backlog.json",
                          team_path="data/team.json")
    sim.run()
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional, Dict
from datetime import date

from .models import Sprint, Team, StoryStatus
from .backlog import ProductBacklog
from .sprint_planner import SprintPlanner
from .daily_standup import StandupSimulator
from .burndown import BurndownCalculator
from .kanban import KanbanBoard
from .retrospective import Retrospective
from .reporter import SprintReporter


class SprintSimulator:
    """
    End-to-end sprint simulation orchestrator.

    Attributes:
        backlog_path:    Path to the product backlog JSON.
        team_path:       Path to the team definition JSON.
        output_dir:      Directory for output files.
        sprint_days:     Number of working days in the sprint.
        sprint_id:       Identifier for this sprint.
        sprint_goal:     Sprint goal statement.
        verbose:         Print detailed output during simulation.
    """

    def __init__(
        self,
        backlog_path: str = "data/sample_backlog.json",
        team_path: str = "data/team.json",
        output_dir: str = "output",
        sprint_days: int = 10,
        sprint_id: str = "Sprint-1",
        sprint_goal: str = "Deliver core mobile banking features for beta launch",
        verbose: bool = True,
        seed: Optional[int] = None,
    ):
        self.backlog_path = backlog_path
        self.team_path = team_path
        self.output_dir = output_dir
        self.sprint_days = sprint_days
        self.sprint_id = sprint_id
        self.sprint_goal = sprint_goal
        self.verbose = verbose

        if seed is not None:
            random.seed(seed)

        # Internal state
        self.backlog: Optional[ProductBacklog] = None
        self.team: Optional[Team] = None
        self.sprint: Optional[Sprint] = None
        self.retro_result = None

    # -- Step 1: Load data --------------------------------------------------

    def load_data(self) -> None:
        """Load backlog and team from JSON files."""
        self._print_header("LOADING DATA")

        self.backlog = ProductBacklog.load_from_json(self.backlog_path)
        self._log(f"  Loaded {len(self.backlog)} user stories from {self.backlog_path}")
        self._log(f"  Total backlog: {self.backlog.total_points} story points")

        team_path = Path(self.team_path)
        with open(team_path, "r", encoding="utf-8") as f:
            team_data = json.load(f)

        self.team = Team.from_dict(team_data)
        self._log(f"  Team: {self.team.name} ({len(self.team.members)} members)")
        for m in self.team.members:
            self._log(f"    - {m.name} ({m.role.value}, {m.experience_level})")

    # -- Step 2: Sprint Planning -------------------------------------------

    def plan_sprint(self) -> Sprint:
        """Execute the Sprint Planning ceremony."""
        self._print_header("SPRINT PLANNING")

        if not self.backlog or not self.team:
            self.load_data()

        planner = SprintPlanner(
            team=self.team,
            backlog=self.backlog,
            sprint_days=self.sprint_days,
        )

        # Calculate capacity
        capacity = planner.calculate_capacity()
        velocity = planner.estimated_velocity()
        self._log(f"  Team capacity: {planner.total_capacity_hours()} hours")
        self._log(f"  Estimated velocity: {velocity} story points")
        self._log(f"  Capacity by member:")
        for name, hours in capacity.items():
            self._log(f"    - {name}: {hours} hours available")

        # Plan the sprint
        self.sprint = planner.plan_sprint(
            sprint_id=self.sprint_id,
            goal=self.sprint_goal,
        )

        # Summary
        summary = planner.planning_summary(self.sprint)
        self._log(f"\n  Sprint planned successfully:")
        self._log(f"    Stories committed: {summary['stories_committed']}")
        self._log(f"    Total points: {summary['total_story_points']}")
        self._log(f"    Total task hours: {summary['total_task_hours']}")
        self._log(f"    Sprint dates: {summary['start_date']} to {summary['end_date']}")

        self._log(f"\n  Committed stories:")
        for s in summary["stories"]:
            self._log(f"    [{s['id']}] {s['title']} ({s['points']} pts, {s['tasks']} tasks)")

        return self.sprint

    # -- Step 3: Daily Standups --------------------------------------------

    def run_standups(self) -> None:
        """Simulate daily standups for the entire sprint."""
        self._print_header("DAILY STANDUPS")

        if not self.sprint:
            self.plan_sprint()

        standup_sim = StandupSimulator(self.sprint)

        for day in range(1, self.sprint.duration_days + 1):
            day_log = standup_sim.run_standup(day)
            self._log(f"\n  --- Day {day} ---")
            self._log(f"  Hours remaining: {day_log['hours_remaining']}")
            self._log(f"  Points remaining: {day_log['points_remaining']}")
            self._log(f"  Stories done: {day_log['stories_done']}")
            self._log(f"  Active blockers: {day_log['active_blockers']}")

            for entry in day_log["entries"]:
                self._log(f"    [{entry['member']}]")
                self._log(f"      Yesterday: {entry['yesterday']}")
                self._log(f"      Today: {entry['today']}")
                if entry.get("blocker"):
                    self._log(f"      BLOCKER: {entry['blocker']}")

            # Show Kanban board at midpoint and end
            if day in (self.sprint.duration_days // 2, self.sprint.duration_days):
                if self.verbose:
                    self._log(f"\n  [Kanban Board — Day {day}]")
                    board = KanbanBoard(self.sprint)
                    board.display()

    # -- Step 4: Burndown Chart --------------------------------------------

    def generate_burndown(self) -> str:
        """Calculate and plot the burndown chart."""
        self._print_header("BURNDOWN CHART")

        if not self.sprint:
            raise RuntimeError("Sprint has not been run yet.")

        output_path = str(Path(self.output_dir) / "burndown.png")
        calc = BurndownCalculator(self.sprint, metric="hours")

        # Trend analysis
        trend = calc.trend_analysis()
        self._log(f"  Overall trend: {trend['overall']}")
        self._log(f"  Total work: {trend['total_work']} hours")
        self._log(f"  Remaining: {trend['remaining']} hours")

        projected = calc.projected_completion_day()
        if projected:
            self._log(f"  Projected completion: Day {projected}")

        # Try to plot
        try:
            saved_path = calc.plot(output_path=output_path)
            self._log(f"  Burndown chart saved to: {saved_path}")
        except ImportError:
            self._log("  [matplotlib not available — showing ASCII chart]")
            ascii = calc.ascii_chart()
            self._log(ascii)
            saved_path = None

        return saved_path or ""

    # -- Step 5: Retrospective ---------------------------------------------

    def run_retrospective(self) -> Dict:
        """Run the Sprint Retrospective."""
        self._print_header("SPRINT RETROSPECTIVE")

        if not self.sprint:
            raise RuntimeError("Sprint has not been run yet.")

        retro = Retrospective(self.sprint)
        self.retro_result = retro.run()

        if self.verbose:
            retro.display()

        return self.retro_result.to_dict()

    # -- Step 6: Generate Reports ------------------------------------------

    def generate_reports(self, burndown_path: str = "") -> Dict[str, str]:
        """Generate Markdown and HTML reports."""
        self._print_header("GENERATING REPORTS")

        if not self.sprint:
            raise RuntimeError("Sprint has not been run yet.")

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        reporter = SprintReporter(
            sprint=self.sprint,
            retro_result=self.retro_result,
            burndown_image=burndown_path if burndown_path else None,
        )

        md_path = reporter.generate_markdown(
            str(Path(self.output_dir) / "sprint_report.md")
        )
        self._log(f"  Markdown report: {md_path}")

        html_path = reporter.generate_html(
            str(Path(self.output_dir) / "sprint_report.html")
        )
        self._log(f"  HTML report: {html_path}")

        # Also save raw sprint data
        data_path = Path(self.output_dir) / "sprint_data.json"
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(self.sprint.to_dict(), f, indent=2, default=str)
        self._log(f"  Sprint data: {data_path.resolve()}")

        return {
            "markdown": md_path,
            "html": html_path,
            "data": str(data_path.resolve()),
        }

    # -- Full simulation ----------------------------------------------------

    def run(self) -> Dict:
        """
        Execute the complete sprint simulation end-to-end.

        Returns:
            Dictionary with paths to all generated artifacts.
        """
        self._print_header("AGILE SPRINT SIMULATOR", char="=")
        self._log(f"  Simulating: {self.sprint_id}")
        self._log(f"  Goal: {self.sprint_goal}")
        self._log(f"  Duration: {self.sprint_days} days")
        self._log("")

        # Run all phases
        self.load_data()
        self.plan_sprint()
        self.run_standups()
        burndown_path = self.generate_burndown()
        self.run_retrospective()
        report_paths = self.generate_reports(burndown_path)

        # Final summary
        self._print_header("SIMULATION COMPLETE", char="=")
        self._log(f"  Sprint: {self.sprint_id}")
        self._log(f"  Stories completed: "
                   f"{self.sprint.backlog.completed_points}/{self.sprint.backlog.total_points} points")
        self._log(f"  Completion rate: {self.sprint.backlog.completion_pct}%")
        self._log(f"\n  Output files:")
        for key, path in report_paths.items():
            self._log(f"    - {key}: {path}")

        return report_paths

    # -- Helpers ------------------------------------------------------------

    def _print_header(self, title: str, char: str = "-") -> None:
        if self.verbose:
            width = 60
            print(f"\n{char * width}")
            print(f"  {title}")
            print(f"{char * width}")

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)
