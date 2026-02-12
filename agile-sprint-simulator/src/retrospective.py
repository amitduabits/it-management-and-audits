"""
retrospective.py - Sprint Retrospective Analysis
==================================================

Simulates the Sprint Retrospective ceremony by analyzing sprint data
and generating actionable insights. Covers:

    - Velocity and throughput metrics
    - Individual contributor statistics
    - Blocker analysis
    - What went well / what to improve / action items
    - Happiness index simulation
    - Sprint health score

Usage:
    from src.retrospective import Retrospective
    retro = Retrospective(sprint)
    results = retro.run()
    retro.display()
"""

from __future__ import annotations

import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from .models import Sprint, StoryStatus, TaskStatus, TeamMember


# ---------------------------------------------------------------------------
# Insight templates
# ---------------------------------------------------------------------------

WENT_WELL_TEMPLATES = [
    "Team collaboration was strong, especially on cross-functional stories",
    "Velocity of {velocity} points was {comparison} the team average",
    "The team completed {done_pct}% of committed story points",
    "Daily standups were focused and under 15 minutes",
    "Code review turnaround time improved significantly",
    "Automated tests caught two regressions before they hit staging",
    "Knowledge sharing sessions helped unblock junior developers",
    "Sprint goal was {goal_status} achieved",
    "{top_contributor} showed excellent leadership in tackling complex tasks",
    "Technical debt reduction tasks were prioritized effectively",
    "Zero critical bugs reported in production during this sprint",
    "CI/CD pipeline stability improved after infrastructure work",
]

IMPROVE_TEMPLATES = [
    "Scope creep: {scope_change} story points were added mid-sprint",
    "{blocked_count} blockers impacted productivity — root cause analysis needed",
    "Story splitting needed: {large_stories} stories exceeded 8 points",
    "Testing started late in the sprint — shift-left testing approach recommended",
    "Estimation accuracy was off: planned {planned} points but actual capacity was {actual}",
    "Too many context switches reduced individual focus time",
    "Acceptance criteria were vague on {unclear_count} stories",
    "Dependency on external teams caused {ext_delay} days of delay",
    "Not all team members participated equally in code reviews",
    "Sprint planning took longer than the 2-hour timebox",
    "Retrospective action items from last sprint were not followed up on",
]

ACTION_TEMPLATES = [
    "Implement 'definition of ready' checklist for all stories entering the sprint",
    "Schedule mid-sprint backlog refinement to catch estimation gaps early",
    "Set up pair programming rotations to distribute knowledge",
    "Create a shared dependency tracker with external teams",
    "Allocate 10% sprint capacity for addressing technical debt",
    "Introduce story-point ceiling of 8 — larger stories must be split",
    "Add automated integration tests for the {focus_area} module",
    "Establish 'no-meeting' blocks to protect deep work time",
    "Rotate Scrum Master facilitation to build team capability",
    "Review and update the team's Definition of Done",
    "Start tracking cycle time per story to identify bottlenecks",
    "Create a blocker escalation playbook for common impediment types",
]


# ---------------------------------------------------------------------------
# Retro result container
# ---------------------------------------------------------------------------

@dataclass
class RetroResult:
    """Holds the complete results of a sprint retrospective."""
    sprint_id: str
    velocity_actual: int
    velocity_planned: int
    completion_rate: float
    stories_completed: int
    stories_total: int
    total_blockers: int
    avg_blocker_duration: float
    member_stats: List[Dict]
    went_well: List[str]
    to_improve: List[str]
    action_items: List[str]
    health_score: float
    happiness_index: Dict[str, int]
    scope_change_points: int
    cycle_time_avg: float

    def to_dict(self) -> dict:
        return {
            "sprint_id": self.sprint_id,
            "metrics": {
                "velocity_planned": self.velocity_planned,
                "velocity_actual": self.velocity_actual,
                "completion_rate": self.completion_rate,
                "stories_completed": self.stories_completed,
                "stories_total": self.stories_total,
                "total_blockers": self.total_blockers,
                "avg_blocker_duration": self.avg_blocker_duration,
                "health_score": self.health_score,
                "scope_change_points": self.scope_change_points,
                "cycle_time_avg": self.cycle_time_avg,
            },
            "member_stats": self.member_stats,
            "went_well": self.went_well,
            "to_improve": self.to_improve,
            "action_items": self.action_items,
            "happiness_index": self.happiness_index,
        }


# ---------------------------------------------------------------------------
# Retrospective engine
# ---------------------------------------------------------------------------

class Retrospective:
    """
    Analyzes sprint results and generates retrospective insights.
    """

    def __init__(self, sprint: Sprint):
        self.sprint = sprint
        self.result: Optional[RetroResult] = None

    # -- Core analysis ------------------------------------------------------

    def run(self) -> RetroResult:
        """
        Execute the full retrospective analysis.

        Returns:
            RetroResult with all computed metrics and insights.
        """
        sprint = self.sprint
        backlog = sprint.backlog

        # -- Basic metrics --------------------------------------------------
        velocity_planned = sprint.velocity
        stories_completed = len(backlog.stories_by_status(StoryStatus.DONE))
        stories_total = len(backlog.stories)
        velocity_actual = backlog.completed_points
        completion_rate = round(
            (velocity_actual / max(velocity_planned, 1)) * 100, 1
        )

        # -- Blocker analysis -----------------------------------------------
        total_blockers = len(sprint.blockers_log)
        blocker_durations = []
        for b in sprint.blockers_log:
            start = b.get("day_started", 1)
            end = b.get("expected_resolution_day", start + 1)
            blocker_durations.append(end - start)
        avg_blocker_duration = round(
            sum(blocker_durations) / max(len(blocker_durations), 1), 1
        )

        # -- Member stats ---------------------------------------------------
        member_stats = self._compute_member_stats()

        # -- Scope change ---------------------------------------------------
        scope_change_points = self._estimate_scope_change()

        # -- Cycle time -----------------------------------------------------
        cycle_time_avg = self._estimate_cycle_time()

        # -- Health score ---------------------------------------------------
        health_score = self._calculate_health_score(
            completion_rate, total_blockers, scope_change_points
        )

        # -- Happiness index ------------------------------------------------
        happiness = self._simulate_happiness()

        # -- Insights -------------------------------------------------------
        went_well = self._generate_went_well(
            velocity_actual, velocity_planned, completion_rate,
            stories_completed, member_stats
        )
        to_improve = self._generate_improvements(
            total_blockers, scope_change_points, velocity_planned, velocity_actual
        )
        action_items = self._generate_action_items()

        self.result = RetroResult(
            sprint_id=sprint.sprint_id,
            velocity_actual=velocity_actual,
            velocity_planned=velocity_planned,
            completion_rate=completion_rate,
            stories_completed=stories_completed,
            stories_total=stories_total,
            total_blockers=total_blockers,
            avg_blocker_duration=avg_blocker_duration,
            member_stats=member_stats,
            went_well=went_well,
            to_improve=to_improve,
            action_items=action_items,
            health_score=health_score,
            happiness_index=happiness,
            scope_change_points=scope_change_points,
            cycle_time_avg=cycle_time_avg,
        )

        return self.result

    # -- Member statistics --------------------------------------------------

    def _compute_member_stats(self) -> List[Dict]:
        """Aggregate per-member statistics from daily logs."""
        if not self.sprint.team:
            return []

        stats: Dict[str, Dict] = {}
        for member in self.sprint.team.get_developers():
            stats[member.name] = {
                "name": member.name,
                "role": member.role.value,
                "total_hours": 0.0,
                "tasks_completed": 0,
                "tasks_progressed": 0,
                "days_blocked": 0,
            }

        for log in self.sprint.daily_logs:
            for entry in log.get("entries", []):
                name = entry.get("member", "")
                if name in stats:
                    stats[name]["total_hours"] += entry.get("hours_worked", 0)
                    stats[name]["tasks_completed"] += len(entry.get("tasks_completed", []))
                    stats[name]["tasks_progressed"] += len(entry.get("tasks_progressed", []))
                    if entry.get("blocker"):
                        stats[name]["days_blocked"] += 1

        result = []
        for name, s in stats.items():
            s["total_hours"] = round(s["total_hours"], 1)
            s["productivity_score"] = round(
                (s["tasks_completed"] + s["tasks_progressed"] * 0.3) /
                max(self.sprint.duration_days, 1), 2
            )
            result.append(s)

        result.sort(key=lambda x: -x["productivity_score"])
        return result

    # -- Scope change estimation --------------------------------------------

    def _estimate_scope_change(self) -> int:
        """
        Estimate scope change during the sprint.
        In a real tool, this would compare planned vs actual stories.
        Here we simulate it based on sprint data.
        """
        planned = self.sprint.velocity
        committed = self.sprint.backlog.total_points
        return max(0, committed - planned)

    # -- Cycle time ---------------------------------------------------------

    def _estimate_cycle_time(self) -> float:
        """
        Estimate average cycle time (days from In Progress to Done).
        Simulated based on story completion patterns.
        """
        stories = self.sprint.backlog.stories
        if not stories:
            return 0.0

        # Approximate: stories that are done took proportional time
        done_stories = [s for s in stories if s.is_done]
        if not done_stories:
            return 0.0

        # Heuristic: larger stories take longer
        total_cycle_days = sum(
            min(s.story_points * 1.2, self.sprint.duration_days) for s in done_stories
        )
        return round(total_cycle_days / len(done_stories), 1)

    # -- Health score -------------------------------------------------------

    def _calculate_health_score(
        self, completion_rate: float, blockers: int, scope_change: int
    ) -> float:
        """
        Calculate an overall sprint health score (0-100).

        Factors:
            - Completion rate (40% weight)
            - Blocker impact (25% weight)
            - Scope stability (20% weight)
            - Team engagement (15% weight, simulated)
        """
        # Completion factor (0-40)
        completion_factor = min(completion_rate, 100) * 0.4

        # Blocker factor (0-25): fewer blockers = higher score
        max_expected_blockers = self.sprint.duration_days * 0.5
        blocker_ratio = min(blockers / max(max_expected_blockers, 1), 1.0)
        blocker_factor = (1 - blocker_ratio) * 25

        # Scope stability (0-20): less change = higher score
        scope_ratio = min(scope_change / max(self.sprint.velocity, 1), 1.0)
        scope_factor = (1 - scope_ratio) * 20

        # Engagement factor (0-15): simulated
        engagement_factor = random.uniform(10, 15)

        score = completion_factor + blocker_factor + scope_factor + engagement_factor
        return round(min(score, 100), 1)

    # -- Happiness simulation -----------------------------------------------

    def _simulate_happiness(self) -> Dict[str, int]:
        """
        Simulate a team happiness index (1-5) per member.
        In practice, this would be collected via a survey.
        """
        if not self.sprint.team:
            return {}

        happiness = {}
        base = 3  # Neutral

        # Adjust base on sprint performance
        completion = self.sprint.backlog.completion_pct
        if completion >= 80:
            base = 4
        elif completion >= 50:
            base = 3
        else:
            base = 2

        for member in self.sprint.team.members:
            noise = random.choice([-1, 0, 0, 0, 1])
            score = max(1, min(5, base + noise))
            happiness[member.name] = score

        return happiness

    # -- Insight generation -------------------------------------------------

    def _generate_went_well(
        self, velocity_actual, velocity_planned, completion_rate,
        stories_completed, member_stats
    ) -> List[str]:
        """Generate 3-5 'what went well' observations."""
        items = []

        comparison = "above" if velocity_actual >= velocity_planned else "below"
        items.append(
            f"Team delivered {velocity_actual} story points "
            f"({comparison} the planned {velocity_planned})"
        )

        goal_status = "fully" if completion_rate >= 90 else "partially"
        items.append(f"Sprint goal was {goal_status} achieved with {completion_rate}% completion")

        if member_stats:
            top = member_stats[0]
            items.append(
                f"{top['name']} demonstrated strong productivity with "
                f"{top['tasks_completed']} tasks completed"
            )

        # Add 1-2 random positive observations
        pool = [
            "Team collaboration during sprint was effective and well-coordinated",
            "Code review turnaround stayed under 24 hours for most pull requests",
            "No critical production incidents during the sprint",
            "Sprint ceremonies stayed within their timeboxes",
            "Knowledge sharing improved team-wide understanding of the codebase",
        ]
        items.extend(random.sample(pool, min(2, len(pool))))

        return items[:5]

    def _generate_improvements(
        self, blockers, scope_change, planned, actual
    ) -> List[str]:
        """Generate 3-4 improvement observations."""
        items = []

        if blockers > 0:
            items.append(
                f"{blockers} blockers were encountered — "
                f"consider proactive dependency management"
            )

        if scope_change > 0:
            items.append(
                f"Scope changed by {scope_change} story points mid-sprint — "
                f"protect sprint commitment more firmly"
            )

        if actual < planned:
            gap = planned - actual
            items.append(
                f"Velocity fell short by {gap} points — "
                f"review estimation accuracy in next refinement"
            )

        pool = [
            "Stories entering the sprint lacked adequate acceptance criteria",
            "Late-sprint testing created a bottleneck at the Done column",
            "Too many work-in-progress items reduced overall throughput",
            "Sprint planning could be more focused with better backlog refinement",
        ]
        items.extend(random.sample(pool, min(2, len(pool))))

        return items[:4]

    def _generate_action_items(self) -> List[str]:
        """Generate 3-4 concrete action items for the next sprint."""
        focus_areas = ["authentication", "payments", "notifications", "data-sync", "UI"]
        focus = random.choice(focus_areas)

        pool = [t.format(focus_area=focus) for t in ACTION_TEMPLATES]
        return random.sample(pool, min(4, len(pool)))

    # -- Display ------------------------------------------------------------

    def display(self) -> None:
        """Print the retrospective results to the terminal."""
        if not self.result:
            self.run()

        result = self.result

        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            from rich import box

            console = Console()
            console.print()
            console.print(Panel(
                f"[bold]{result.sprint_id} — Sprint Retrospective[/bold]",
                style="bright_cyan",
            ))

            # Metrics table
            metrics_table = Table(title="Sprint Metrics", box=box.ROUNDED)
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="white")
            metrics_table.add_row("Planned Velocity", f"{result.velocity_planned} pts")
            metrics_table.add_row("Actual Velocity", f"{result.velocity_actual} pts")
            metrics_table.add_row("Completion Rate", f"{result.completion_rate}%")
            metrics_table.add_row("Stories Done", f"{result.stories_completed}/{result.stories_total}")
            metrics_table.add_row("Total Blockers", str(result.total_blockers))
            metrics_table.add_row("Avg Blocker Duration", f"{result.avg_blocker_duration} days")
            metrics_table.add_row("Sprint Health Score", f"{result.health_score}/100")
            metrics_table.add_row("Avg Cycle Time", f"{result.cycle_time_avg} days")
            console.print(metrics_table)

            # Member stats
            if result.member_stats:
                member_table = Table(title="Team Member Performance", box=box.ROUNDED)
                member_table.add_column("Name", style="cyan")
                member_table.add_column("Role")
                member_table.add_column("Hours Worked", justify="right")
                member_table.add_column("Tasks Done", justify="right")
                member_table.add_column("Days Blocked", justify="right")
                member_table.add_column("Score", justify="right")

                for ms in result.member_stats:
                    member_table.add_row(
                        ms["name"], ms["role"],
                        str(ms["total_hours"]), str(ms["tasks_completed"]),
                        str(ms["days_blocked"]), str(ms["productivity_score"]),
                    )
                console.print(member_table)

            # Went well
            console.print(Panel(
                "\n".join(f"  [green]+[/green] {item}" for item in result.went_well),
                title="[green]What Went Well[/green]",
                border_style="green",
            ))

            # Improvements
            console.print(Panel(
                "\n".join(f"  [yellow]-[/yellow] {item}" for item in result.to_improve),
                title="[yellow]What To Improve[/yellow]",
                border_style="yellow",
            ))

            # Action items
            console.print(Panel(
                "\n".join(f"  [cyan]{i+1}.[/cyan] {item}" for i, item in enumerate(result.action_items)),
                title="[cyan]Action Items for Next Sprint[/cyan]",
                border_style="cyan",
            ))

            # Happiness
            if result.happiness_index:
                emojis = {1: "Very Unhappy", 2: "Unhappy", 3: "Neutral", 4: "Happy", 5: "Very Happy"}
                happiness_lines = [
                    f"  {name}: {'*' * score} ({emojis.get(score, '?')})"
                    for name, score in result.happiness_index.items()
                ]
                avg = sum(result.happiness_index.values()) / max(len(result.happiness_index), 1)
                happiness_lines.append(f"\n  Team Average: {avg:.1f}/5.0")
                console.print(Panel(
                    "\n".join(happiness_lines),
                    title="Happiness Index",
                    border_style="magenta",
                ))

            console.print()

        except ImportError:
            self._display_plain()

    def _display_plain(self) -> None:
        """Fallback plain-text display."""
        r = self.result
        print(f"\n{'='*60}")
        print(f"  {r.sprint_id} — SPRINT RETROSPECTIVE")
        print(f"{'='*60}")
        print(f"  Planned Velocity:   {r.velocity_planned} pts")
        print(f"  Actual Velocity:    {r.velocity_actual} pts")
        print(f"  Completion Rate:    {r.completion_rate}%")
        print(f"  Stories Completed:  {r.stories_completed}/{r.stories_total}")
        print(f"  Blockers:           {r.total_blockers}")
        print(f"  Health Score:       {r.health_score}/100")

        print(f"\n  WHAT WENT WELL:")
        for item in r.went_well:
            print(f"    + {item}")

        print(f"\n  WHAT TO IMPROVE:")
        for item in r.to_improve:
            print(f"    - {item}")

        print(f"\n  ACTION ITEMS:")
        for i, item in enumerate(r.action_items, 1):
            print(f"    {i}. {item}")
        print()
