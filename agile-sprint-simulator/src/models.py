"""
models.py - Core Data Models for the Agile Sprint Simulator
============================================================

Defines the fundamental data structures used throughout the simulation:
    - Task: A unit of work within a user story
    - UserStory: A feature described from the end-user perspective
    - SprintBacklog: The set of stories committed to for a sprint
    - Sprint: A time-boxed iteration
    - TeamMember: An individual contributor on the team
    - Team: The cross-functional Scrum team
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import List, Optional, Dict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class StoryStatus(Enum):
    """Lifecycle states a user story can be in."""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    BLOCKED = "Blocked"


class Priority(Enum):
    """MoSCoW prioritization scheme."""
    MUST_HAVE = "Must Have"
    SHOULD_HAVE = "Should Have"
    COULD_HAVE = "Could Have"
    WONT_HAVE = "Won't Have"

    @property
    def weight(self) -> int:
        """Numeric weight for sorting (lower = higher priority)."""
        return {
            Priority.MUST_HAVE: 1,
            Priority.SHOULD_HAVE: 2,
            Priority.COULD_HAVE: 3,
            Priority.WONT_HAVE: 4,
        }[self]


class TaskStatus(Enum):
    """Status of an individual task."""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class Role(Enum):
    """Scrum team roles."""
    DEVELOPER = "Developer"
    QA_ENGINEER = "QA Engineer"
    DESIGNER = "Designer"
    DEVOPS = "DevOps"
    TECH_LEAD = "Tech Lead"
    SCRUM_MASTER = "Scrum Master"
    PRODUCT_OWNER = "Product Owner"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """
    A concrete piece of work that contributes to completing a user story.

    Attributes:
        task_id:        Unique identifier.
        title:          Short description of the task.
        hours_estimated: Estimated effort in hours.
        hours_remaining: Hours of work still left.
        status:         Current status (To Do / In Progress / Done).
        assigned_to:    Name of the team member working on it.
    """
    title: str
    hours_estimated: float
    hours_remaining: float = 0.0
    status: TaskStatus = TaskStatus.TODO
    assigned_to: Optional[str] = None
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def __post_init__(self):
        if self.hours_remaining == 0.0:
            self.hours_remaining = self.hours_estimated

    def work(self, hours: float) -> float:
        """
        Record work done on this task.

        Args:
            hours: Number of hours of effort applied.

        Returns:
            Actual hours consumed (may be less than requested if task finishes).
        """
        actual = min(hours, self.hours_remaining)
        self.hours_remaining = round(max(0.0, self.hours_remaining - actual), 2)
        if self.hours_remaining == 0.0:
            self.status = TaskStatus.DONE
        else:
            self.status = TaskStatus.IN_PROGRESS
        return actual

    @property
    def is_done(self) -> bool:
        return self.status == TaskStatus.DONE

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "hours_estimated": self.hours_estimated,
            "hours_remaining": self.hours_remaining,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
        }


# ---------------------------------------------------------------------------
# UserStory
# ---------------------------------------------------------------------------

@dataclass
class UserStory:
    """
    A user story following the standard format:
        "As a <role>, I want <goal> so that <benefit>."

    Attributes:
        story_id:    Unique identifier (e.g., "US-001").
        title:       Brief name for the story.
        description: Full user story statement.
        priority:    MoSCoW priority.
        story_points: Estimated complexity (Fibonacci: 1,2,3,5,8,13,21).
        status:      Current lifecycle status.
        tasks:       Breakdown of work items.
        acceptance_criteria: List of conditions for "Done".
        assigned_to: Team member(s) responsible.
        tags:        Labels for filtering (e.g., "backend", "auth").
        sprint_id:   Which sprint this story belongs to, if any.
    """
    story_id: str
    title: str
    description: str
    priority: Priority
    story_points: int
    status: StoryStatus = StoryStatus.TODO
    tasks: List[Task] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    sprint_id: Optional[str] = None

    # -- Computed helpers ----------------------------------------------------

    @property
    def total_hours_estimated(self) -> float:
        return sum(t.hours_estimated for t in self.tasks)

    @property
    def total_hours_remaining(self) -> float:
        return sum(t.hours_remaining for t in self.tasks)

    @property
    def progress_pct(self) -> float:
        """Percentage of work completed based on task hours."""
        if self.total_hours_estimated == 0:
            return 0.0
        done = self.total_hours_estimated - self.total_hours_remaining
        return round((done / self.total_hours_estimated) * 100, 1)

    @property
    def is_done(self) -> bool:
        if not self.tasks:
            return self.status == StoryStatus.DONE
        return all(t.is_done for t in self.tasks)

    def update_status(self):
        """Derive story status from underlying task statuses."""
        if not self.tasks:
            return
        if all(t.is_done for t in self.tasks):
            self.status = StoryStatus.DONE
        elif any(t.status == TaskStatus.IN_PROGRESS for t in self.tasks):
            self.status = StoryStatus.IN_PROGRESS
        else:
            self.status = StoryStatus.TODO

    def add_task(self, title: str, hours: float) -> Task:
        task = Task(title=title, hours_estimated=hours)
        self.tasks.append(task)
        return task

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "story_points": self.story_points,
            "status": self.status.value,
            "tasks": [t.to_dict() for t in self.tasks],
            "acceptance_criteria": self.acceptance_criteria,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserStory":
        """Reconstruct a UserStory from a plain dictionary (e.g., JSON)."""
        priority_map = {p.value: p for p in Priority}
        status_map = {s.value: s for s in StoryStatus}

        tasks = []
        for td in data.get("tasks", []):
            tasks.append(Task(
                title=td["title"],
                hours_estimated=td["hours_estimated"],
                hours_remaining=td.get("hours_remaining", td["hours_estimated"]),
                status=TaskStatus(td.get("status", "To Do")),
                assigned_to=td.get("assigned_to"),
                task_id=td.get("task_id", uuid.uuid4().hex[:8]),
            ))

        return cls(
            story_id=data["story_id"],
            title=data["title"],
            description=data.get("description", ""),
            priority=priority_map.get(data.get("priority", "Could Have"), Priority.COULD_HAVE),
            story_points=data.get("story_points", 3),
            status=status_map.get(data.get("status", "To Do"), StoryStatus.TODO),
            tasks=tasks,
            acceptance_criteria=data.get("acceptance_criteria", []),
            assigned_to=data.get("assigned_to"),
            tags=data.get("tags", []),
        )


# ---------------------------------------------------------------------------
# SprintBacklog
# ---------------------------------------------------------------------------

@dataclass
class SprintBacklog:
    """
    The subset of user stories selected for the current sprint.

    Attributes:
        stories:  Committed user stories.
        capacity: Total team capacity in story points for this sprint.
    """
    stories: List[UserStory] = field(default_factory=list)
    capacity: int = 0

    @property
    def total_points(self) -> int:
        return sum(s.story_points for s in self.stories)

    @property
    def completed_points(self) -> int:
        return sum(s.story_points for s in self.stories if s.is_done)

    @property
    def remaining_points(self) -> int:
        return self.total_points - self.completed_points

    @property
    def total_hours_remaining(self) -> float:
        return sum(s.total_hours_remaining for s in self.stories)

    @property
    def total_hours_estimated(self) -> float:
        return sum(s.total_hours_estimated for s in self.stories)

    @property
    def completion_pct(self) -> float:
        if self.total_points == 0:
            return 0.0
        return round((self.completed_points / self.total_points) * 100, 1)

    def stories_by_status(self, status: StoryStatus) -> List[UserStory]:
        return [s for s in self.stories if s.status == status]

    def to_dict(self) -> dict:
        return {
            "capacity": self.capacity,
            "total_points": self.total_points,
            "stories": [s.to_dict() for s in self.stories],
        }


# ---------------------------------------------------------------------------
# TeamMember
# ---------------------------------------------------------------------------

@dataclass
class TeamMember:
    """
    An individual member of the Scrum team.

    Attributes:
        name:             Full name.
        role:             Primary role on the team.
        capacity_hours:   Available hours per sprint day.
        skills:           List of skill tags (e.g., "python", "react").
        experience_level: Junior / Mid / Senior — affects simulation randomness.
    """
    name: str
    role: Role
    capacity_hours: float = 6.0
    skills: List[str] = field(default_factory=list)
    experience_level: str = "Mid"

    @property
    def daily_velocity_factor(self) -> float:
        """Multiplier applied during simulation to model skill differences."""
        return {
            "Junior": 0.7,
            "Mid": 1.0,
            "Senior": 1.3,
        }.get(self.experience_level, 1.0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role.value,
            "capacity_hours": self.capacity_hours,
            "skills": self.skills,
            "experience_level": self.experience_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TeamMember":
        role_map = {r.value: r for r in Role}
        return cls(
            name=data["name"],
            role=role_map.get(data.get("role", "Developer"), Role.DEVELOPER),
            capacity_hours=data.get("capacity_hours", 6.0),
            skills=data.get("skills", []),
            experience_level=data.get("experience_level", "Mid"),
        )


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

@dataclass
class Team:
    """
    The cross-functional Scrum team.

    Attributes:
        name:    Team name (e.g., "Phoenix Squad").
        members: List of team members.
    """
    name: str
    members: List[TeamMember] = field(default_factory=list)

    @property
    def total_daily_capacity(self) -> float:
        """Sum of all members' available hours in a single sprint day."""
        return sum(m.capacity_hours for m in self.members)

    @property
    def sprint_capacity_hours(self, sprint_days: int = 10) -> float:
        return self.total_daily_capacity * sprint_days

    def velocity_estimate(self, sprint_days: int = 10) -> int:
        """
        Rough story-point capacity estimate.
        Heuristic: 1 story point ~ 4 ideal hours.
        """
        total_hours = self.total_daily_capacity * sprint_days
        return int(total_hours / 4)

    def get_developers(self) -> List[TeamMember]:
        """Return members who can be assigned development tasks."""
        dev_roles = {Role.DEVELOPER, Role.TECH_LEAD, Role.DEVOPS, Role.QA_ENGINEER, Role.DESIGNER}
        return [m for m in self.members if m.role in dev_roles]

    def find_member(self, name: str) -> Optional[TeamMember]:
        for m in self.members:
            if m.name.lower() == name.lower():
                return m
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "members": [m.to_dict() for m in self.members],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Team":
        members = [TeamMember.from_dict(md) for md in data.get("members", [])]
        return cls(name=data.get("name", "Unnamed Team"), members=members)


# ---------------------------------------------------------------------------
# Sprint
# ---------------------------------------------------------------------------

@dataclass
class Sprint:
    """
    Represents a single Scrum sprint (time-boxed iteration).

    Attributes:
        sprint_id:       Unique identifier (e.g., "Sprint-1").
        goal:            The sprint goal — a short objective statement.
        start_date:      First day of the sprint.
        duration_days:   Working days in the sprint (typically 10).
        backlog:         The sprint backlog.
        team:            The team executing the sprint.
        daily_logs:      Per-day simulation records.
        velocity:        Team velocity used for planning.
        blockers_log:    Record of blockers encountered.
    """
    sprint_id: str
    goal: str
    start_date: date = field(default_factory=date.today)
    duration_days: int = 10
    backlog: SprintBacklog = field(default_factory=SprintBacklog)
    team: Optional[Team] = None
    daily_logs: List[Dict] = field(default_factory=list)
    velocity: int = 0
    blockers_log: List[Dict] = field(default_factory=list)

    @property
    def end_date(self) -> date:
        return self.start_date + timedelta(days=self.duration_days - 1)

    @property
    def current_day(self) -> int:
        """How many days of the sprint have been logged so far."""
        return len(self.daily_logs)

    @property
    def is_complete(self) -> bool:
        return self.current_day >= self.duration_days

    def get_day_dates(self) -> List[date]:
        """Return a list of dates for each sprint day."""
        return [self.start_date + timedelta(days=i) for i in range(self.duration_days)]

    def to_dict(self) -> dict:
        return {
            "sprint_id": self.sprint_id,
            "goal": self.goal,
            "start_date": self.start_date.isoformat(),
            "duration_days": self.duration_days,
            "velocity": self.velocity,
            "backlog": self.backlog.to_dict(),
            "daily_logs": self.daily_logs,
            "blockers_log": self.blockers_log,
        }
