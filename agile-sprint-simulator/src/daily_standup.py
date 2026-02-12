"""
daily_standup.py - Daily Standup (Daily Scrum) Simulation
=========================================================

Simulates the daily 15-minute standup meeting where each team member
answers three questions:
    1. What did I do yesterday?
    2. What will I do today?
    3. Are there any blockers?

The simulation models:
    - Random progress on assigned tasks
    - Occasional blockers with varying severity
    - Blocker resolution over time
    - Varying productivity based on experience level

Usage:
    from src.daily_standup import StandupSimulator
    sim = StandupSimulator(sprint)
    day_log = sim.run_standup(day_number=1)
"""

from __future__ import annotations

import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from .models import (
    Sprint, Task, TaskStatus, UserStory, StoryStatus,
    TeamMember, Team,
)


# ---------------------------------------------------------------------------
# Blocker templates
# ---------------------------------------------------------------------------

BLOCKER_TEMPLATES = [
    "Waiting on API specification from external team",
    "Environment configuration issue — staging server down",
    "Dependency conflict in third-party library upgrade",
    "Unclear acceptance criteria — need PO clarification",
    "Database migration script failing on test data",
    "Merge conflict in shared module — coordinating with {member}",
    "SSL certificate renewal blocking deployment pipeline",
    "Performance regression detected in load tests",
    "UI design mockups not finalized for this component",
    "Access permissions pending for cloud infrastructure",
    "Flaky test suite blocking CI pipeline",
    "Cross-team dependency: payment gateway integration delayed",
    "Code review feedback requires significant refactoring",
    "Security vulnerability found during static analysis",
    "Missing test data for edge-case scenarios",
]

YESTERDAY_TEMPLATES = [
    "Worked on {task} — made good progress",
    "Continued implementation of {task}",
    "Completed code review for {task}",
    "Investigated a tricky bug in {task}",
    "Pair-programmed with {peer} on {task}",
    "Refactored {task} based on review feedback",
    "Set up test fixtures for {task}",
    "Ran integration tests for {task}",
    "Updated documentation for {task}",
    "Resolved merge conflicts and pushed {task}",
]

TODAY_TEMPLATES = [
    "Will continue working on {task}",
    "Plan to finish {task} and move to review",
    "Starting implementation of {task}",
    "Will write unit tests for {task}",
    "Going to pair with {peer} on {task}",
    "Will address code review comments on {task}",
    "Focusing on completing {task} today",
    "Planning to run QA tests on {task}",
    "Will deploy {task} to staging environment",
    "Picking up {task} from the board",
]


# ---------------------------------------------------------------------------
# Standup entry for a single team member
# ---------------------------------------------------------------------------

@dataclass
class StandupEntry:
    """One team member's standup update."""
    member_name: str
    yesterday: str
    today: str
    blocker: Optional[str] = None
    hours_worked: float = 0.0
    tasks_progressed: List[str] = field(default_factory=list)
    tasks_completed: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = {
            "member": self.member_name,
            "yesterday": self.yesterday,
            "today": self.today,
            "hours_worked": self.hours_worked,
            "tasks_progressed": self.tasks_progressed,
            "tasks_completed": self.tasks_completed,
        }
        if self.blocker:
            result["blocker"] = self.blocker
        return result


# ---------------------------------------------------------------------------
# StandupSimulator
# ---------------------------------------------------------------------------

class StandupSimulator:
    """
    Simulates daily standup meetings and applies progress to the sprint.

    Attributes:
        sprint:             The active sprint.
        blocker_probability: Chance a member encounters a blocker (0.0-1.0).
        blocker_duration:    How many days a blocker typically lasts.
        active_blockers:     Currently active blockers per member.
    """

    def __init__(
        self,
        sprint: Sprint,
        blocker_probability: float = 0.12,
        blocker_duration_range: Tuple[int, int] = (1, 3),
    ):
        self.sprint = sprint
        self.blocker_probability = blocker_probability
        self.blocker_duration_range = blocker_duration_range
        self.active_blockers: Dict[str, Dict] = {}  # member_name -> blocker info

    # -- Main standup -------------------------------------------------------

    def run_standup(self, day_number: int) -> Dict:
        """
        Simulate a single day's standup and progress.

        Args:
            day_number: Which day of the sprint (1-based).

        Returns:
            A dictionary containing the full day log.
        """
        if not self.sprint.team:
            return {"day": day_number, "entries": [], "error": "No team assigned"}

        entries: List[StandupEntry] = []
        developers = self.sprint.team.get_developers()

        # Resolve any expired blockers
        self._resolve_blockers(day_number)

        for member in developers:
            entry = self._simulate_member_day(member, day_number)
            entries.append(entry)

        # Update story statuses based on task progress
        for story in self.sprint.backlog.stories:
            story.update_status()

        # Build the day log
        day_log = {
            "day": day_number,
            "date": (self.sprint.start_date.__class__(
                self.sprint.start_date.year,
                self.sprint.start_date.month,
                self.sprint.start_date.day,
            ).__add__(
                __import__("datetime").timedelta(days=day_number - 1)
            )).isoformat(),
            "entries": [e.to_dict() for e in entries],
            "hours_remaining": round(self.sprint.backlog.total_hours_remaining, 1),
            "points_remaining": self.sprint.backlog.remaining_points,
            "points_completed": self.sprint.backlog.completed_points,
            "active_blockers": len(self.active_blockers),
            "stories_done": len(self.sprint.backlog.stories_by_status(StoryStatus.DONE)),
            "stories_in_progress": len(self.sprint.backlog.stories_by_status(StoryStatus.IN_PROGRESS)),
        }

        self.sprint.daily_logs.append(day_log)
        return day_log

    # -- Member simulation --------------------------------------------------

    def _simulate_member_day(self, member: TeamMember, day_number: int) -> StandupEntry:
        """Simulate one team member's daily work."""
        # Find tasks assigned to this member
        assigned_tasks = self._get_member_tasks(member.name)

        # Check for blockers
        is_blocked = member.name in self.active_blockers
        new_blocker = None

        if not is_blocked and random.random() < self.blocker_probability:
            new_blocker = self._create_blocker(member, day_number)
            is_blocked = True

        # Calculate effective working hours
        base_hours = member.capacity_hours
        velocity_factor = member.daily_velocity_factor

        if is_blocked:
            # Blocked members work at reduced capacity
            effective_hours = base_hours * velocity_factor * 0.3
        else:
            # Normal productivity with some daily variance
            variance = random.uniform(0.75, 1.15)
            effective_hours = base_hours * velocity_factor * variance

        effective_hours = round(effective_hours, 1)

        # Apply work to tasks
        tasks_progressed = []
        tasks_completed = []
        hours_left = effective_hours

        # Sort: prioritize in-progress tasks, then to-do
        active_tasks = [t for t in assigned_tasks if t.status == TaskStatus.IN_PROGRESS]
        todo_tasks = [t for t in assigned_tasks if t.status == TaskStatus.TODO]
        work_queue = active_tasks + todo_tasks

        for task in work_queue:
            if hours_left <= 0:
                break
            hours_applied = task.work(hours_left)
            hours_left -= hours_applied

            if hours_applied > 0:
                tasks_progressed.append(task.title)
                if task.is_done:
                    tasks_completed.append(task.title)

        # Generate standup messages
        peers = [m.name for m in self.sprint.team.get_developers() if m.name != member.name]
        peer = random.choice(peers) if peers else "the team"

        yesterday_msg = self._generate_yesterday(tasks_progressed, tasks_completed, peer)
        today_msg = self._generate_today(work_queue, peer)

        entry = StandupEntry(
            member_name=member.name,
            yesterday=yesterday_msg,
            today=today_msg,
            blocker=new_blocker,
            hours_worked=round(effective_hours - hours_left, 1),
            tasks_progressed=tasks_progressed,
            tasks_completed=tasks_completed,
        )

        return entry

    # -- Task lookup --------------------------------------------------------

    def _get_member_tasks(self, member_name: str) -> List[Task]:
        """Get all tasks assigned to a specific member across all stories."""
        tasks = []
        for story in self.sprint.backlog.stories:
            for task in story.tasks:
                if task.assigned_to == member_name and not task.is_done:
                    tasks.append(task)
        return tasks

    # -- Blocker management -------------------------------------------------

    def _create_blocker(self, member: TeamMember, day_number: int) -> str:
        """Generate a random blocker for a team member."""
        peers = [m.name for m in self.sprint.team.get_developers() if m.name != member.name]
        peer = random.choice(peers) if peers else "another team"

        template = random.choice(BLOCKER_TEMPLATES)
        description = template.format(member=peer)

        duration = random.randint(*self.blocker_duration_range)

        blocker_info = {
            "description": description,
            "started_day": day_number,
            "resolve_day": day_number + duration,
            "severity": random.choice(["Low", "Medium", "High"]),
        }

        self.active_blockers[member.name] = blocker_info
        self.sprint.blockers_log.append({
            "member": member.name,
            "blocker": description,
            "day_started": day_number,
            "expected_resolution_day": day_number + duration,
            "severity": blocker_info["severity"],
        })

        return description

    def _resolve_blockers(self, current_day: int) -> None:
        """Remove blockers that have reached their resolution day."""
        resolved = []
        for member_name, info in self.active_blockers.items():
            if current_day >= info["resolve_day"]:
                resolved.append(member_name)

        for name in resolved:
            del self.active_blockers[name]

    # -- Message generation -------------------------------------------------

    def _generate_yesterday(
        self, progressed: List[str], completed: List[str], peer: str
    ) -> str:
        if completed:
            task_name = completed[0].split(" — ")[0] if " — " in completed[0] else completed[0]
            return f"Completed {task_name} and moved it to Done"
        elif progressed:
            task_name = progressed[0].split(" — ")[0] if " — " in progressed[0] else progressed[0]
            template = random.choice(YESTERDAY_TEMPLATES)
            return template.format(task=task_name, peer=peer)
        else:
            return "Was working on backlog refinement and team coordination"

    def _generate_today(self, work_queue: List[Task], peer: str) -> str:
        pending = [t for t in work_queue if not t.is_done]
        if pending:
            task_name = pending[0].title.split(" — ")[0] if " — " in pending[0].title else pending[0].title
            template = random.choice(TODAY_TEMPLATES)
            return template.format(task=task_name, peer=peer)
        else:
            return "All my assigned tasks are complete — will pick up new work or help teammates"

    # -- Run full sprint standups -------------------------------------------

    def run_all_standups(self) -> List[Dict]:
        """
        Run standups for every day of the sprint.

        Returns:
            List of daily logs.
        """
        all_logs = []
        for day in range(1, self.sprint.duration_days + 1):
            log = self.run_standup(day)
            all_logs.append(log)
        return all_logs
