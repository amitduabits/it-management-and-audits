"""
sprint_planner.py - Sprint Planning Ceremony Simulation
========================================================

Simulates Sprint Planning (Scrum Event):
    1. Review the prioritized product backlog.
    2. Determine team velocity / capacity.
    3. Select stories that fit within the velocity budget.
    4. Break stories into tasks.
    5. Assign tasks to team members based on skills and capacity.

Usage:
    from src.sprint_planner import SprintPlanner
    planner = SprintPlanner(team, backlog)
    sprint = planner.plan_sprint(sprint_id="Sprint-1", goal="Launch MVP login flow")
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import List, Optional, Dict

from .models import (
    UserStory, Sprint, SprintBacklog, Team, TeamMember,
    Task, TaskStatus, StoryStatus, Priority, Role,
)
from .backlog import ProductBacklog, generate_tasks_for_story


class SprintPlanner:
    """
    Encapsulates the Sprint Planning ceremony logic.

    Attributes:
        team:            The Scrum team.
        backlog:         The product backlog to pull stories from.
        sprint_days:     Number of working days in the sprint.
        focus_factor:    Percentage of capacity actually available (0.0-1.0).
                         Accounts for meetings, interruptions, etc.
    """

    def __init__(
        self,
        team: Team,
        backlog: ProductBacklog,
        sprint_days: int = 10,
        focus_factor: float = 0.80,
    ):
        self.team = team
        self.backlog = backlog
        self.sprint_days = sprint_days
        self.focus_factor = focus_factor

    # -- Capacity calculation -----------------------------------------------

    def calculate_capacity(self) -> Dict[str, float]:
        """
        Calculate each member's available hours for the sprint,
        adjusted by the focus factor.

        Returns:
            Dictionary mapping member name -> available sprint hours.
        """
        capacity: Dict[str, float] = {}
        for member in self.team.get_developers():
            raw = member.capacity_hours * self.sprint_days
            adjusted = round(raw * self.focus_factor, 1)
            capacity[member.name] = adjusted
        return capacity

    def total_capacity_hours(self) -> float:
        return sum(self.calculate_capacity().values())

    def estimated_velocity(self) -> int:
        """
        Estimate team velocity in story points.
        Heuristic: 1 story point ~ 4 ideal hours.
        """
        return int(self.total_capacity_hours() / 4)

    # -- Story selection ----------------------------------------------------

    def select_stories(self, velocity_override: Optional[int] = None) -> List[UserStory]:
        """
        Select stories from the prioritized backlog that fit within the
        velocity budget. Ensures backlog is sorted before selection.

        Args:
            velocity_override: If provided, use this instead of the
                               calculated velocity.
        Returns:
            List of selected UserStory objects.
        """
        velocity = velocity_override or self.estimated_velocity()
        self.backlog.prioritize(strategy="moscow")
        return self.backlog.select_by_velocity(velocity)

    # -- Task generation & assignment ---------------------------------------

    def ensure_tasks(self, stories: List[UserStory]) -> None:
        """Make sure every selected story has a task breakdown."""
        for story in stories:
            if not story.tasks:
                generate_tasks_for_story(story)

    def assign_tasks(self, stories: List[UserStory]) -> Dict[str, List[str]]:
        """
        Assign tasks to team members using a round-robin strategy
        weighted by member capacity and skill match.

        Returns:
            Mapping of member name -> list of task IDs assigned.
        """
        developers = self.team.get_developers()
        if not developers:
            return {}

        # Track remaining capacity per developer
        capacity = self.calculate_capacity()
        assignments: Dict[str, List[str]] = {m.name: [] for m in developers}

        # Collect all unassigned tasks
        all_tasks: List[Task] = []
        task_story_map: Dict[str, UserStory] = {}
        for story in stories:
            for task in story.tasks:
                if task.assigned_to is None and task.status != TaskStatus.DONE:
                    all_tasks.append(task)
                    task_story_map[task.task_id] = story

        # Sort tasks by estimated hours descending (assign big tasks first)
        all_tasks.sort(key=lambda t: -t.hours_estimated)

        for task in all_tasks:
            best_member = self._find_best_member(
                task, task_story_map.get(task.task_id), developers, capacity
            )
            if best_member:
                task.assigned_to = best_member.name
                capacity[best_member.name] -= task.hours_estimated
                assignments[best_member.name].append(task.task_id)

        return assignments

    def _find_best_member(
        self,
        task: Task,
        story: Optional[UserStory],
        developers: List[TeamMember],
        capacity: Dict[str, float],
    ) -> Optional[TeamMember]:
        """
        Choose the best team member for a given task based on:
            1. Remaining capacity (must have enough hours).
            2. Skill match with story tags.
            3. Experience level (seniors get harder tasks).
        """
        candidates = [
            m for m in developers
            if capacity.get(m.name, 0) >= task.hours_estimated
        ]

        if not candidates:
            # If nobody has enough capacity, pick the person with most remaining
            candidates = sorted(developers, key=lambda m: -capacity.get(m.name, 0))
            if candidates:
                return candidates[0]
            return None

        # Score candidates
        def score(member: TeamMember) -> float:
            s = 0.0
            # Skill match bonus
            if story and story.tags:
                overlap = len(set(member.skills) & set(story.tags))
                s += overlap * 10
            # Capacity bonus — prefer members with more free time
            s += capacity.get(member.name, 0) * 0.5
            # Experience bonus for larger tasks
            if task.hours_estimated > 4 and member.experience_level == "Senior":
                s += 5
            # Small random factor to avoid deterministic patterns
            s += random.uniform(0, 2)
            return s

        candidates.sort(key=score, reverse=True)
        return candidates[0]

    # -- Full planning ceremony ---------------------------------------------

    def plan_sprint(
        self,
        sprint_id: str = "Sprint-1",
        goal: str = "Deliver planned backlog items",
        start_date: Optional[date] = None,
        velocity_override: Optional[int] = None,
    ) -> Sprint:
        """
        Run the full Sprint Planning ceremony:
            1. Calculate team capacity & velocity.
            2. Select stories from the backlog.
            3. Generate task breakdowns.
            4. Assign tasks to team members.
            5. Build and return the Sprint object.

        Args:
            sprint_id:          Identifier for the sprint.
            goal:               Sprint goal statement.
            start_date:         First day of the sprint.
            velocity_override:  Manual velocity setting.

        Returns:
            A fully-configured Sprint ready for simulation.
        """
        start = start_date or date.today()
        velocity = velocity_override or self.estimated_velocity()

        # Step 1 & 2: Select stories
        selected = self.select_stories(velocity_override=velocity)

        # Step 3: Generate tasks
        self.ensure_tasks(selected)

        # Step 4: Assign tasks to team members
        self.assign_tasks(selected)

        # Mark selected stories as belonging to this sprint
        for story in selected:
            story.sprint_id = sprint_id

        # Step 5: Build the sprint
        sprint_backlog = SprintBacklog(stories=selected, capacity=velocity)

        sprint = Sprint(
            sprint_id=sprint_id,
            goal=goal,
            start_date=start,
            duration_days=self.sprint_days,
            backlog=sprint_backlog,
            team=self.team,
            velocity=velocity,
        )

        return sprint

    # -- Planning summary ---------------------------------------------------

    def planning_summary(self, sprint: Sprint) -> Dict:
        """
        Generate a human-readable summary of the sprint plan.
        """
        capacity = self.calculate_capacity()
        stories = sprint.backlog.stories

        member_load: Dict[str, float] = {m.name: 0.0 for m in self.team.get_developers()}
        for story in stories:
            for task in story.tasks:
                if task.assigned_to and task.assigned_to in member_load:
                    member_load[task.assigned_to] += task.hours_estimated

        utilization = {}
        for name, load in member_load.items():
            cap = capacity.get(name, 1)
            utilization[name] = {
                "assigned_hours": round(load, 1),
                "capacity_hours": cap,
                "utilization_pct": round((load / cap) * 100, 1) if cap > 0 else 0.0,
            }

        return {
            "sprint_id": sprint.sprint_id,
            "sprint_goal": sprint.goal,
            "start_date": sprint.start_date.isoformat(),
            "end_date": sprint.end_date.isoformat(),
            "duration_days": sprint.duration_days,
            "velocity": sprint.velocity,
            "stories_committed": len(stories),
            "total_story_points": sprint.backlog.total_points,
            "total_task_hours": round(sprint.backlog.total_hours_estimated, 1),
            "team_capacity_hours": round(self.total_capacity_hours(), 1),
            "member_utilization": utilization,
            "stories": [
                {
                    "id": s.story_id,
                    "title": s.title,
                    "points": s.story_points,
                    "priority": s.priority.value,
                    "tasks": len(s.tasks),
                }
                for s in stories
            ],
        }
