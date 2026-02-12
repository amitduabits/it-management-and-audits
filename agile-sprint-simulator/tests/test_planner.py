"""
test_planner.py - Unit Tests for Sprint Planning
==================================================

Tests cover:
    - Team capacity calculation
    - Velocity estimation
    - Story selection by velocity budget
    - Task generation for stories without tasks
    - Task assignment to team members
    - Full sprint planning flow
    - Edge cases (empty backlog, single member team, etc.)
"""

import json
import os
import sys
import pytest
from datetime import date
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models import (
    UserStory, Sprint, SprintBacklog, Team, TeamMember,
    Task, TaskStatus, StoryStatus, Priority, Role,
)
from src.backlog import ProductBacklog, generate_tasks_for_story, nearest_fibonacci
from src.sprint_planner import SprintPlanner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_team() -> Team:
    """Create a test team with 3 members."""
    return Team(
        name="Test Squad",
        members=[
            TeamMember(
                name="Alice",
                role=Role.TECH_LEAD,
                capacity_hours=6.0,
                skills=["backend", "api", "security"],
                experience_level="Senior",
            ),
            TeamMember(
                name="Bob",
                role=Role.DEVELOPER,
                capacity_hours=7.0,
                skills=["mobile", "ui", "frontend"],
                experience_level="Mid",
            ),
            TeamMember(
                name="Carol",
                role=Role.QA_ENGINEER,
                capacity_hours=6.0,
                skills=["testing", "automation", "qa"],
                experience_level="Mid",
            ),
        ],
    )


@pytest.fixture
def sample_stories() -> list:
    """Create a set of test user stories."""
    stories = [
        UserStory(
            story_id="TS-001",
            title="User Authentication",
            description="As a user, I want to log in securely.",
            priority=Priority.MUST_HAVE,
            story_points=5,
            tags=["auth", "security"],
        ),
        UserStory(
            story_id="TS-002",
            title="Dashboard View",
            description="As a user, I want to see my dashboard.",
            priority=Priority.MUST_HAVE,
            story_points=3,
            tags=["ui", "frontend"],
        ),
        UserStory(
            story_id="TS-003",
            title="Payment Processing",
            description="As a user, I want to make payments.",
            priority=Priority.SHOULD_HAVE,
            story_points=8,
            tags=["backend", "api"],
        ),
        UserStory(
            story_id="TS-004",
            title="Notification System",
            description="As a user, I want push notifications.",
            priority=Priority.SHOULD_HAVE,
            story_points=5,
            tags=["notifications", "mobile"],
        ),
        UserStory(
            story_id="TS-005",
            title="Dark Mode",
            description="As a user, I want dark mode support.",
            priority=Priority.COULD_HAVE,
            story_points=3,
            tags=["ui", "theme"],
        ),
        UserStory(
            story_id="TS-006",
            title="Multi-language Support",
            description="As a user, I want the app in my language.",
            priority=Priority.COULD_HAVE,
            story_points=13,
            tags=["i18n", "frontend"],
        ),
    ]
    return stories


@pytest.fixture
def sample_backlog(sample_stories) -> ProductBacklog:
    """Create a product backlog from sample stories."""
    return ProductBacklog(stories=sample_stories)


@pytest.fixture
def planner(sample_team, sample_backlog) -> SprintPlanner:
    """Create a SprintPlanner with test data."""
    return SprintPlanner(
        team=sample_team,
        backlog=sample_backlog,
        sprint_days=10,
        focus_factor=0.80,
    )


# ---------------------------------------------------------------------------
# Capacity & Velocity Tests
# ---------------------------------------------------------------------------

class TestCapacityCalculation:
    """Tests for team capacity computation."""

    def test_capacity_includes_all_developers(self, planner, sample_team):
        """All developer-role members should be in the capacity map."""
        capacity = planner.calculate_capacity()
        devs = sample_team.get_developers()
        assert len(capacity) == len(devs)
        for dev in devs:
            assert dev.name in capacity

    def test_capacity_applies_focus_factor(self, planner):
        """Capacity should be reduced by the focus factor."""
        capacity = planner.calculate_capacity()
        # Alice: 6.0 * 10 * 0.80 = 48.0
        assert capacity["Alice"] == 48.0
        # Bob: 7.0 * 10 * 0.80 = 56.0
        assert capacity["Bob"] == 56.0

    def test_total_capacity_hours(self, planner):
        """Total capacity should be sum of all member capacities."""
        total = planner.total_capacity_hours()
        capacity = planner.calculate_capacity()
        assert total == sum(capacity.values())

    def test_velocity_estimate_is_positive(self, planner):
        """Estimated velocity should be a positive integer."""
        velocity = planner.estimated_velocity()
        assert velocity > 0
        assert isinstance(velocity, int)

    def test_velocity_proportional_to_capacity(self):
        """A larger team should have higher estimated velocity."""
        small_team = Team(name="Small", members=[
            TeamMember(name="Solo", role=Role.DEVELOPER, capacity_hours=6.0),
        ])
        large_team = Team(name="Large", members=[
            TeamMember(name=f"Dev-{i}", role=Role.DEVELOPER, capacity_hours=6.0)
            for i in range(5)
        ])

        backlog = ProductBacklog()  # empty, doesn't matter for velocity calc
        small_planner = SprintPlanner(small_team, backlog)
        large_planner = SprintPlanner(large_team, backlog)

        assert large_planner.estimated_velocity() > small_planner.estimated_velocity()


# ---------------------------------------------------------------------------
# Story Selection Tests
# ---------------------------------------------------------------------------

class TestStorySelection:
    """Tests for selecting stories from the backlog."""

    def test_select_stories_within_velocity(self, planner):
        """Selected stories should not exceed velocity budget."""
        stories = planner.select_stories(velocity_override=15)
        total_points = sum(s.story_points for s in stories)
        assert total_points <= 15

    def test_select_stories_prioritized(self, planner):
        """Must Have stories should be selected before Should Have."""
        stories = planner.select_stories(velocity_override=20)
        # All Must Have stories (5+3=8 pts) should be included
        must_have = [s for s in stories if s.priority == Priority.MUST_HAVE]
        assert len(must_have) == 2

    def test_select_stories_with_zero_velocity(self, planner):
        """Zero velocity should return no stories."""
        stories = planner.select_stories(velocity_override=0)
        assert len(stories) == 0

    def test_select_stories_with_large_velocity(self, planner, sample_stories):
        """Large velocity should select all eligible stories."""
        stories = planner.select_stories(velocity_override=1000)
        assert len(stories) == len(sample_stories)

    def test_select_skips_non_todo_stories(self, planner, sample_backlog):
        """Stories not in TODO status should be skipped."""
        sample_backlog.stories[0].status = StoryStatus.DONE
        stories = planner.select_stories(velocity_override=100)
        ids = [s.story_id for s in stories]
        assert "TS-001" not in ids


# ---------------------------------------------------------------------------
# Task Generation Tests
# ---------------------------------------------------------------------------

class TestTaskGeneration:
    """Tests for automatic task generation."""

    def test_ensure_tasks_creates_tasks(self, planner, sample_stories):
        """Stories without tasks should get tasks generated."""
        # sample_stories start with no tasks
        assert len(sample_stories[0].tasks) == 0
        planner.ensure_tasks(sample_stories[:1])
        assert len(sample_stories[0].tasks) > 0

    def test_ensure_tasks_preserves_existing(self):
        """Stories that already have tasks should not be modified."""
        story = UserStory(
            story_id="TS-X",
            title="Test",
            description="Test",
            priority=Priority.MUST_HAVE,
            story_points=3,
            tasks=[Task(title="Existing task", hours_estimated=4.0)],
        )
        original_count = len(story.tasks)
        generate_tasks_for_story(story)
        assert len(story.tasks) == original_count

    def test_generated_tasks_have_positive_hours(self, sample_stories):
        """All generated tasks should have positive hour estimates."""
        story = sample_stories[1]
        generate_tasks_for_story(story)
        for task in story.tasks:
            assert task.hours_estimated > 0
            assert task.hours_remaining > 0

    def test_task_titles_contain_story_id(self, sample_stories):
        """Generated task titles should reference the parent story ID."""
        story = sample_stories[2]
        generate_tasks_for_story(story)
        for task in story.tasks:
            assert story.story_id in task.title


# ---------------------------------------------------------------------------
# Task Assignment Tests
# ---------------------------------------------------------------------------

class TestTaskAssignment:
    """Tests for assigning tasks to team members."""

    def test_all_tasks_get_assigned(self, planner, sample_stories):
        """Every task should be assigned to a team member."""
        planner.ensure_tasks(sample_stories[:2])
        planner.assign_tasks(sample_stories[:2])

        for story in sample_stories[:2]:
            for task in story.tasks:
                assert task.assigned_to is not None
                assert isinstance(task.assigned_to, str)

    def test_assignments_reference_valid_members(self, planner, sample_team, sample_stories):
        """Assigned names should match actual team members."""
        planner.ensure_tasks(sample_stories[:3])
        planner.assign_tasks(sample_stories[:3])

        valid_names = {m.name for m in sample_team.members}
        for story in sample_stories[:3]:
            for task in story.tasks:
                assert task.assigned_to in valid_names

    def test_assignment_returns_mapping(self, planner, sample_stories):
        """assign_tasks should return a dict mapping member -> task IDs."""
        planner.ensure_tasks(sample_stories[:2])
        mapping = planner.assign_tasks(sample_stories[:2])

        assert isinstance(mapping, dict)
        assert len(mapping) > 0
        for name, task_ids in mapping.items():
            assert isinstance(task_ids, list)


# ---------------------------------------------------------------------------
# Full Sprint Planning Tests
# ---------------------------------------------------------------------------

class TestFullPlanning:
    """Tests for the complete plan_sprint method."""

    def test_plan_sprint_returns_sprint_object(self, planner):
        """plan_sprint should return a Sprint instance."""
        sprint = planner.plan_sprint(sprint_id="Test-Sprint-1")
        assert isinstance(sprint, Sprint)
        assert sprint.sprint_id == "Test-Sprint-1"

    def test_planned_sprint_has_stories(self, planner):
        """The planned sprint should contain committed stories."""
        sprint = planner.plan_sprint()
        assert len(sprint.backlog.stories) > 0

    def test_planned_sprint_has_team(self, planner, sample_team):
        """The sprint should reference the team."""
        sprint = planner.plan_sprint()
        assert sprint.team is not None
        assert sprint.team.name == sample_team.name

    def test_planned_stories_have_tasks(self, planner):
        """All committed stories should have task breakdowns."""
        sprint = planner.plan_sprint()
        for story in sprint.backlog.stories:
            assert len(story.tasks) > 0

    def test_planned_stories_have_assignments(self, planner):
        """All tasks in committed stories should be assigned."""
        sprint = planner.plan_sprint()
        for story in sprint.backlog.stories:
            for task in story.tasks:
                assert task.assigned_to is not None

    def test_sprint_goal_is_set(self, planner):
        """Sprint goal should match what was passed."""
        sprint = planner.plan_sprint(goal="Test goal ABC")
        assert sprint.goal == "Test goal ABC"

    def test_sprint_dates_are_correct(self, planner):
        """Sprint end date should be start_date + duration - 1."""
        start = date(2026, 3, 1)
        sprint = planner.plan_sprint(start_date=start)
        assert sprint.start_date == start
        expected_end = date(2026, 3, 10)  # 10-day sprint
        assert sprint.end_date == expected_end

    def test_planning_summary_structure(self, planner):
        """planning_summary should return expected keys."""
        sprint = planner.plan_sprint()
        summary = planner.planning_summary(sprint)

        expected_keys = [
            "sprint_id", "sprint_goal", "start_date", "end_date",
            "duration_days", "velocity", "stories_committed",
            "total_story_points", "total_task_hours",
            "team_capacity_hours", "member_utilization", "stories",
        ]
        for key in expected_keys:
            assert key in summary, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_empty_backlog(self, sample_team):
        """Planning with an empty backlog should produce an empty sprint."""
        empty_backlog = ProductBacklog()
        planner = SprintPlanner(sample_team, empty_backlog)
        sprint = planner.plan_sprint()
        assert len(sprint.backlog.stories) == 0

    def test_single_member_team(self, sample_backlog):
        """Planning should work with a single-member team."""
        solo_team = Team(
            name="Solo",
            members=[TeamMember(name="Solo Dev", role=Role.DEVELOPER)],
        )
        planner = SprintPlanner(solo_team, sample_backlog)
        sprint = planner.plan_sprint()
        # All tasks should be assigned to the sole developer
        for story in sprint.backlog.stories:
            for task in story.tasks:
                assert task.assigned_to == "Solo Dev"

    def test_all_stories_already_done(self, sample_team, sample_stories):
        """If all stories are DONE, no stories should be selected."""
        for s in sample_stories:
            s.status = StoryStatus.DONE
        backlog = ProductBacklog(stories=sample_stories)
        planner = SprintPlanner(sample_team, backlog)
        sprint = planner.plan_sprint()
        assert len(sprint.backlog.stories) == 0

    def test_nearest_fibonacci(self):
        """Test the nearest Fibonacci rounding function."""
        assert nearest_fibonacci(1) == 1
        assert nearest_fibonacci(4) == 5
        assert nearest_fibonacci(6) == 5
        assert nearest_fibonacci(7) == 8
        assert nearest_fibonacci(10) == 8
        assert nearest_fibonacci(17) == 13
        assert nearest_fibonacci(20) == 21

    def test_custom_focus_factor(self, sample_team, sample_backlog):
        """A lower focus factor should reduce capacity."""
        planner_high = SprintPlanner(sample_team, sample_backlog, focus_factor=0.90)
        planner_low = SprintPlanner(sample_team, sample_backlog, focus_factor=0.50)
        assert planner_high.total_capacity_hours() > planner_low.total_capacity_hours()


# ---------------------------------------------------------------------------
# Backlog persistence (integration)
# ---------------------------------------------------------------------------

class TestBacklogPersistence:
    """Test saving and loading backlogs."""

    def test_save_and_load_roundtrip(self, sample_backlog, tmp_path):
        """Saving and loading should preserve story data."""
        filepath = str(tmp_path / "test_backlog.json")
        sample_backlog.save_to_json(filepath)

        loaded = ProductBacklog.load_from_json(filepath)
        assert len(loaded) == len(sample_backlog)
        assert loaded.total_points == sample_backlog.total_points

        for orig, loaded_s in zip(sample_backlog.stories, loaded.stories):
            assert orig.story_id == loaded_s.story_id
            assert orig.title == loaded_s.title
            assert orig.story_points == loaded_s.story_points

    def test_load_sample_backlog_file(self):
        """Test loading the actual sample backlog from the data directory."""
        sample_path = PROJECT_ROOT / "data" / "sample_backlog.json"
        if not sample_path.exists():
            pytest.skip("Sample backlog file not found")

        backlog = ProductBacklog.load_from_json(str(sample_path))
        assert len(backlog) == 20
        assert backlog.total_points > 0

    def test_load_nonexistent_file_raises(self):
        """Loading a non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ProductBacklog.load_from_json("/nonexistent/path.json")
