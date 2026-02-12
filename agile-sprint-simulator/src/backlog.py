"""
backlog.py - Product Backlog Management
========================================

Provides utilities for creating, loading, prioritizing, and estimating
user stories in a product backlog. Supports JSON persistence and
multiple prioritization strategies.

Usage:
    from src.backlog import ProductBacklog

    backlog = ProductBacklog.load_from_json("data/sample_backlog.json")
    backlog.prioritize(strategy="moscow")
    top_stories = backlog.top_n(10)
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import List, Optional, Callable

from .models import UserStory, Priority, StoryStatus, Task


# ---------------------------------------------------------------------------
# Fibonacci points used in Planning Poker
# ---------------------------------------------------------------------------
FIBONACCI_POINTS = [1, 2, 3, 5, 8, 13, 21]


def nearest_fibonacci(value: float) -> int:
    """Round a numeric estimate to the nearest Fibonacci story-point value."""
    return min(FIBONACCI_POINTS, key=lambda f: abs(f - value))


# ---------------------------------------------------------------------------
# Estimation helpers
# ---------------------------------------------------------------------------

def estimate_story_points(story: UserStory, team_avg_hours: float = 4.0) -> int:
    """
    Estimate story points from task-hour breakdown.

    Heuristic: total task hours / team_avg_hours per point, rounded to
    the nearest Fibonacci number.
    """
    if story.total_hours_estimated == 0:
        return story.story_points  # keep existing if no tasks
    raw = story.total_hours_estimated / team_avg_hours
    return nearest_fibonacci(raw)


def generate_tasks_for_story(story: UserStory) -> List[Task]:
    """
    Auto-generate a realistic task breakdown for a story based on its
    story points. Useful for bootstrapping simulations.
    """
    if story.tasks:
        return story.tasks

    base_hours = story.story_points * 2.5
    task_templates = [
        ("Design & analysis", 0.15),
        ("Implementation", 0.40),
        ("Unit testing", 0.15),
        ("Code review", 0.10),
        ("QA testing", 0.15),
        ("Documentation", 0.05),
    ]

    tasks = []
    for title, ratio in task_templates:
        hours = round(base_hours * ratio + random.uniform(-0.5, 0.5), 1)
        hours = max(0.5, hours)
        tasks.append(Task(title=f"{title} — {story.story_id}", hours_estimated=hours))

    story.tasks = tasks
    return tasks


# ---------------------------------------------------------------------------
# ProductBacklog class
# ---------------------------------------------------------------------------

class ProductBacklog:
    """
    Manages the full product backlog: loading, saving, sorting, filtering,
    and selecting stories for sprint planning.
    """

    def __init__(self, stories: Optional[List[UserStory]] = None):
        self.stories: List[UserStory] = stories or []

    # -- Persistence --------------------------------------------------------

    @classmethod
    def load_from_json(cls, filepath: str) -> "ProductBacklog":
        """Load stories from a JSON file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Backlog file not found: {filepath}")

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        stories_data = data if isinstance(data, list) else data.get("stories", [])
        stories = [UserStory.from_dict(sd) for sd in stories_data]
        return cls(stories=stories)

    def save_to_json(self, filepath: str) -> None:
        """Persist current backlog to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"stories": [s.to_dict() for s in self.stories]}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    # -- Adding stories -----------------------------------------------------

    def add_story(self, story: UserStory) -> None:
        self.stories.append(story)

    def add_stories(self, stories: List[UserStory]) -> None:
        self.stories.extend(stories)

    def remove_story(self, story_id: str) -> Optional[UserStory]:
        for i, s in enumerate(self.stories):
            if s.story_id == story_id:
                return self.stories.pop(i)
        return None

    # -- Querying -----------------------------------------------------------

    def find(self, story_id: str) -> Optional[UserStory]:
        for s in self.stories:
            if s.story_id == story_id:
                return s
        return None

    def filter_by_status(self, status: StoryStatus) -> List[UserStory]:
        return [s for s in self.stories if s.status == status]

    def filter_by_priority(self, priority: Priority) -> List[UserStory]:
        return [s for s in self.stories if s.priority == priority]

    def filter_by_tag(self, tag: str) -> List[UserStory]:
        return [s for s in self.stories if tag in s.tags]

    @property
    def todo_stories(self) -> List[UserStory]:
        return self.filter_by_status(StoryStatus.TODO)

    @property
    def total_points(self) -> int:
        return sum(s.story_points for s in self.stories)

    # -- Prioritization -----------------------------------------------------

    def prioritize(self, strategy: str = "moscow") -> None:
        """
        Sort the backlog in-place.

        Strategies:
            moscow  - MoSCoW priority, then story points descending.
            value   - Highest story points first (proxy for value).
            wsjf    - Weighted Shortest Job First (value / size).
            random  - Randomize order (useful for experiments).
        """
        strategies: dict[str, Callable] = {
            "moscow": self._sort_moscow,
            "value": self._sort_value,
            "wsjf": self._sort_wsjf,
            "random": self._sort_random,
        }
        sorter = strategies.get(strategy.lower(), self._sort_moscow)
        sorter()

    def _sort_moscow(self) -> None:
        self.stories.sort(key=lambda s: (s.priority.weight, -s.story_points))

    def _sort_value(self) -> None:
        self.stories.sort(key=lambda s: -s.story_points)

    def _sort_wsjf(self) -> None:
        """Weighted Shortest Job First: higher ratio = do first."""
        def wsjf_score(s: UserStory) -> float:
            # Use inverse priority weight as a proxy for business value
            value = (5 - s.priority.weight) * 10
            size = max(s.story_points, 1)
            return -(value / size)  # negative for ascending sort
        self.stories.sort(key=wsjf_score)

    def _sort_random(self) -> None:
        random.shuffle(self.stories)

    # -- Selection ----------------------------------------------------------

    def top_n(self, n: int) -> List[UserStory]:
        """Return the top N stories (assumes backlog is already sorted)."""
        return self.stories[:n]

    def select_by_velocity(self, velocity: int) -> List[UserStory]:
        """
        Greedily select stories from the top of the backlog until
        the team velocity (story-point budget) is exhausted.
        Only considers stories with status TODO.
        """
        selected: List[UserStory] = []
        remaining = velocity
        for story in self.stories:
            if story.status != StoryStatus.TODO:
                continue
            if story.story_points <= remaining:
                selected.append(story)
                remaining -= story.story_points
            if remaining <= 0:
                break
        return selected

    # -- Estimation ---------------------------------------------------------

    def auto_estimate(self) -> None:
        """Re-estimate all stories based on their task breakdowns."""
        for story in self.stories:
            story.story_points = estimate_story_points(story)

    def auto_generate_tasks(self) -> None:
        """Generate task breakdowns for stories that lack them."""
        for story in self.stories:
            if not story.tasks:
                generate_tasks_for_story(story)

    # -- Summary ------------------------------------------------------------

    def summary(self) -> dict:
        """Return a summary dictionary of backlog statistics."""
        status_counts = {}
        for s in self.stories:
            key = s.status.value
            status_counts[key] = status_counts.get(key, 0) + 1

        priority_counts = {}
        for s in self.stories:
            key = s.priority.value
            priority_counts[key] = priority_counts.get(key, 0) + 1

        return {
            "total_stories": len(self.stories),
            "total_points": self.total_points,
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "average_points": round(self.total_points / max(len(self.stories), 1), 1),
        }

    def __len__(self) -> int:
        return len(self.stories)

    def __repr__(self) -> str:
        return f"ProductBacklog(stories={len(self.stories)}, points={self.total_points})"
