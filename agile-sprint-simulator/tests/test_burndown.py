"""
test_burndown.py - Unit Tests for Burndown Chart Calculations
===============================================================

Tests cover:
    - Ideal burndown line calculation
    - Actual burndown tracking from daily logs
    - Trend analysis (ahead / behind / on track)
    - Daily velocity computation
    - Projected completion day estimation
    - Edge cases (no logs, single day, all work done early)
"""

import sys
import pytest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models import (
    Sprint, SprintBacklog, UserStory, Task, TaskStatus,
    StoryStatus, Priority, Team, TeamMember, Role,
)
from src.burndown import BurndownCalculator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_sprint() -> Sprint:
    """
    Create a sprint with known task hours for predictable calculations.
    2 stories, 5 tasks total, 50 hours estimated, 5-day sprint.
    """
    task1 = Task(title="Task A1", hours_estimated=10.0, hours_remaining=10.0)
    task2 = Task(title="Task A2", hours_estimated=10.0, hours_remaining=10.0)
    task3 = Task(title="Task B1", hours_estimated=10.0, hours_remaining=10.0)
    task4 = Task(title="Task B2", hours_estimated=10.0, hours_remaining=10.0)
    task5 = Task(title="Task B3", hours_estimated=10.0, hours_remaining=10.0)

    story_a = UserStory(
        story_id="TEST-A",
        title="Story A",
        description="Test story A",
        priority=Priority.MUST_HAVE,
        story_points=5,
        tasks=[task1, task2],
    )
    story_b = UserStory(
        story_id="TEST-B",
        title="Story B",
        description="Test story B",
        priority=Priority.SHOULD_HAVE,
        story_points=8,
        tasks=[task3, task4, task5],
    )

    backlog = SprintBacklog(stories=[story_a, story_b], capacity=13)

    sprint = Sprint(
        sprint_id="Test-Sprint",
        goal="Testing burndown calculations",
        start_date=date(2026, 3, 1),
        duration_days=5,
        backlog=backlog,
        velocity=13,
    )
    return sprint


@pytest.fixture
def sprint_with_logs(simple_sprint) -> Sprint:
    """
    Sprint with pre-populated daily logs simulating steady progress.
    50 hours total, burning ~10 hours per day.
    """
    simple_sprint.daily_logs = [
        {"day": 1, "hours_remaining": 40.0, "points_remaining": 13, "stories_done": 0, "active_blockers": 0},
        {"day": 2, "hours_remaining": 30.0, "points_remaining": 13, "stories_done": 0, "active_blockers": 0},
        {"day": 3, "hours_remaining": 18.0, "points_remaining": 8, "stories_done": 1, "active_blockers": 1},
        {"day": 4, "hours_remaining": 8.0, "points_remaining": 8, "stories_done": 1, "active_blockers": 0},
        {"day": 5, "hours_remaining": 0.0, "points_remaining": 0, "stories_done": 2, "active_blockers": 0},
    ]
    return simple_sprint


@pytest.fixture
def sprint_behind_schedule(simple_sprint) -> Sprint:
    """Sprint where team is falling behind."""
    simple_sprint.daily_logs = [
        {"day": 1, "hours_remaining": 48.0, "points_remaining": 13, "stories_done": 0, "active_blockers": 1},
        {"day": 2, "hours_remaining": 45.0, "points_remaining": 13, "stories_done": 0, "active_blockers": 2},
        {"day": 3, "hours_remaining": 42.0, "points_remaining": 13, "stories_done": 0, "active_blockers": 1},
    ]
    return simple_sprint


@pytest.fixture
def sprint_ahead_schedule(simple_sprint) -> Sprint:
    """Sprint where team is ahead of plan."""
    simple_sprint.daily_logs = [
        {"day": 1, "hours_remaining": 30.0, "points_remaining": 8, "stories_done": 1, "active_blockers": 0},
        {"day": 2, "hours_remaining": 15.0, "points_remaining": 5, "stories_done": 1, "active_blockers": 0},
        {"day": 3, "hours_remaining": 2.0, "points_remaining": 0, "stories_done": 2, "active_blockers": 0},
    ]
    return simple_sprint


# ---------------------------------------------------------------------------
# Ideal Burndown Tests
# ---------------------------------------------------------------------------

class TestIdealBurndown:
    """Tests for the ideal (linear) burndown calculation."""

    def test_ideal_starts_at_total(self, simple_sprint):
        """Ideal burndown should start at total estimated hours."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        data = calc.calculate()
        assert data["ideal"][0] == 50.0

    def test_ideal_ends_at_zero(self, simple_sprint):
        """Ideal burndown should reach 0 on the last day."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        data = calc.calculate()
        assert data["ideal"][-1] == 0.0

    def test_ideal_is_linear(self, simple_sprint):
        """Each day should burn the same amount in the ideal line."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        data = calc.calculate()
        ideal = data["ideal"]

        # With 50 hours over 5 days = 10 hours per day
        for i in range(1, len(ideal)):
            delta = round(ideal[i - 1] - ideal[i], 2)
            assert delta == 10.0

    def test_ideal_has_correct_length(self, simple_sprint):
        """Ideal line should have duration_days + 1 points (day 0 through day N)."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        data = calc.calculate()
        assert len(data["ideal"]) == simple_sprint.duration_days + 1

    def test_ideal_with_points_metric(self, simple_sprint):
        """Ideal burndown using story points should start at total points."""
        calc = BurndownCalculator(simple_sprint, metric="points")
        data = calc.calculate()
        assert data["ideal"][0] == 13  # 5 + 8
        assert data["ideal"][-1] == 0.0


# ---------------------------------------------------------------------------
# Actual Burndown Tests
# ---------------------------------------------------------------------------

class TestActualBurndown:
    """Tests for the actual burndown tracking."""

    def test_actual_starts_at_total(self, sprint_with_logs):
        """Actual burndown day 0 should equal total hours."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        data = calc.calculate()
        assert data["actual"][0] == 50.0

    def test_actual_follows_logs(self, sprint_with_logs):
        """Actual values should match the daily log data."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        data = calc.calculate()
        expected = [50.0, 40.0, 30.0, 18.0, 8.0, 0.0]
        assert data["actual"] == expected

    def test_actual_length_matches_days(self, sprint_with_logs):
        """Actual line should have one entry per day plus day 0."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        data = calc.calculate()
        assert len(data["actual"]) == sprint_with_logs.duration_days + 1

    def test_actual_with_no_logs(self, simple_sprint):
        """With no logs, actual should just be [total] padded."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        data = calc.calculate()
        # Day 0 = total, then padded with same value
        assert data["actual"][0] == 50.0
        assert all(v == 50.0 for v in data["actual"])

    def test_final_remaining(self, sprint_with_logs):
        """final_remaining should match the last actual value."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        data = calc.calculate()
        assert data["final_remaining"] == 0.0


# ---------------------------------------------------------------------------
# Velocity Per Day Tests
# ---------------------------------------------------------------------------

class TestVelocityPerDay:
    """Tests for daily burn rate calculation."""

    def test_velocity_has_correct_length(self, sprint_with_logs):
        """Should have one velocity entry per logged day."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        velocities = calc.velocity_per_day()
        assert len(velocities) == 5  # 5 days of logs

    def test_velocity_values_match_deltas(self, sprint_with_logs):
        """Each velocity should be the difference between consecutive actual values."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        velocities = calc.velocity_per_day()
        # Day 0->1: 50-40=10, Day 1->2: 40-30=10, Day 2->3: 30-18=12, etc.
        expected = [10.0, 10.0, 12.0, 10.0, 8.0]
        assert velocities == expected

    def test_velocity_all_positive_on_progress(self, sprint_with_logs):
        """When work is being done, all velocities should be positive."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        velocities = calc.velocity_per_day()
        assert all(v > 0 for v in velocities)

    def test_velocity_no_logs(self, simple_sprint):
        """With no logs, velocity should be empty or zeros."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        velocities = calc.velocity_per_day()
        # All padded values are same as total, so deltas are 0
        assert all(v == 0.0 for v in velocities)


# ---------------------------------------------------------------------------
# Trend Analysis Tests
# ---------------------------------------------------------------------------

class TestTrendAnalysis:
    """Tests for the trend analysis feature."""

    def test_completed_sprint_trend(self, sprint_with_logs):
        """A completed sprint should show trend as 'ahead'."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        trend = calc.trend_analysis()
        assert "overall" in trend
        # Sprint finishes at 0 on day 5, ideal also 0 — should be on track or ahead
        assert "Ahead" in trend["overall"] or "On track" in trend["overall"]

    def test_behind_schedule_trend(self, sprint_behind_schedule):
        """A sprint falling behind should show 'Behind' in trend."""
        calc = BurndownCalculator(sprint_behind_schedule, metric="hours")
        trend = calc.trend_analysis()
        assert "Behind" in trend["overall"]

    def test_ahead_schedule_trend(self, sprint_ahead_schedule):
        """A sprint progressing fast should show 'Ahead'."""
        calc = BurndownCalculator(sprint_ahead_schedule, metric="hours")
        trend = calc.trend_analysis()
        assert "Ahead" in trend["overall"]

    def test_trend_has_daily_comparison(self, sprint_with_logs):
        """Trend should include per-day comparison data."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        trend = calc.trend_analysis()
        assert "daily_comparison" in trend
        assert len(trend["daily_comparison"]) > 0

    def test_trend_daily_entry_structure(self, sprint_with_logs):
        """Each daily comparison entry should have expected keys."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        trend = calc.trend_analysis()
        entry = trend["daily_comparison"][0]
        for key in ["day", "ideal", "actual", "deviation", "status"]:
            assert key in entry

    def test_no_data_trend(self, simple_sprint):
        """With no log data, trend should still work without errors."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        trend = calc.trend_analysis()
        assert "overall" in trend


# ---------------------------------------------------------------------------
# Projected Completion Tests
# ---------------------------------------------------------------------------

class TestProjectedCompletion:
    """Tests for projected completion day estimation."""

    def test_projected_with_steady_progress(self, sprint_with_logs):
        """With steady progress, projected completion should be near day 5."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        projected = calc.projected_completion_day()
        assert projected is not None
        assert projected == 5  # Sprint completes exactly on schedule

    def test_projected_behind_schedule(self, sprint_behind_schedule):
        """Behind-schedule sprint should project beyond sprint duration."""
        calc = BurndownCalculator(sprint_behind_schedule, metric="hours")
        projected = calc.projected_completion_day()
        if projected is not None:
            assert projected > sprint_behind_schedule.duration_days

    def test_projected_ahead_schedule(self, sprint_ahead_schedule):
        """Ahead-schedule sprint should project before sprint end."""
        calc = BurndownCalculator(sprint_ahead_schedule, metric="hours")
        projected = calc.projected_completion_day()
        if projected is not None:
            assert projected <= sprint_ahead_schedule.duration_days

    def test_projected_with_no_data(self, simple_sprint):
        """With no logs, projection should return None."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        projected = calc.projected_completion_day()
        assert projected is None


# ---------------------------------------------------------------------------
# Metric Mode Tests
# ---------------------------------------------------------------------------

class TestMetricModes:
    """Test that hours and points metrics produce different results."""

    def test_hours_metric_total(self, sprint_with_logs):
        """Hours metric total should match sum of task hours."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        data = calc.calculate()
        assert data["total"] == 50.0

    def test_points_metric_total(self, sprint_with_logs):
        """Points metric total should match sum of story points."""
        calc = BurndownCalculator(sprint_with_logs, metric="points")
        data = calc.calculate()
        assert data["total"] == 13

    def test_metric_field_in_output(self, sprint_with_logs):
        """The metric field should reflect what was requested."""
        calc_h = BurndownCalculator(sprint_with_logs, metric="hours")
        calc_p = BurndownCalculator(sprint_with_logs, metric="points")
        assert calc_h.calculate()["metric"] == "hours"
        assert calc_p.calculate()["metric"] == "points"


# ---------------------------------------------------------------------------
# ASCII Chart Tests
# ---------------------------------------------------------------------------

class TestAsciiChart:
    """Tests for the ASCII chart fallback."""

    def test_ascii_chart_returns_string(self, sprint_with_logs):
        """ASCII chart should return a non-empty string."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        chart = calc.ascii_chart()
        assert isinstance(chart, str)
        assert len(chart) > 0

    def test_ascii_chart_contains_sprint_id(self, sprint_with_logs):
        """ASCII chart should include the sprint identifier."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        chart = calc.ascii_chart()
        assert sprint_with_logs.sprint_id in chart

    def test_ascii_chart_contains_legend(self, sprint_with_logs):
        """ASCII chart should include a legend."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        chart = calc.ascii_chart()
        assert "Ideal" in chart
        assert "Actual" in chart


# ---------------------------------------------------------------------------
# Data Structure Tests
# ---------------------------------------------------------------------------

class TestCalculateDataStructure:
    """Verify the shape and types of calculate() output."""

    def test_output_keys(self, simple_sprint):
        """calculate() should return all expected keys."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        data = calc.calculate()
        expected_keys = {"days", "ideal", "actual", "metric", "total", "final_remaining"}
        assert set(data.keys()) == expected_keys

    def test_days_list_is_sequential(self, simple_sprint):
        """Days should be [0, 1, 2, ..., N]."""
        calc = BurndownCalculator(simple_sprint, metric="hours")
        data = calc.calculate()
        expected = list(range(0, simple_sprint.duration_days + 1))
        assert data["days"] == expected

    def test_all_values_are_numeric(self, sprint_with_logs):
        """All ideal and actual values should be numbers."""
        calc = BurndownCalculator(sprint_with_logs, metric="hours")
        data = calc.calculate()
        for val in data["ideal"]:
            assert isinstance(val, (int, float))
        for val in data["actual"]:
            assert isinstance(val, (int, float))
