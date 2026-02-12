"""
burndown.py - Burndown Chart Calculation & Visualization
=========================================================

Provides two main capabilities:
    1. Calculate ideal and actual burndown data from sprint logs.
    2. Render a burndown chart as a PNG image using matplotlib.

The burndown chart is one of the most important information radiators in
Scrum — it shows at a glance whether the team is on track to complete
the sprint goal.

Usage:
    from src.burndown import BurndownCalculator
    calc = BurndownCalculator(sprint)
    data = calc.calculate()
    calc.plot(output_path="output/burndown.png")
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple
from pathlib import Path

from .models import Sprint


class BurndownCalculator:
    """
    Computes ideal and actual burndown data, and optionally plots a chart.

    Attributes:
        sprint:  The sprint containing daily logs.
        metric:  What to track — "hours" or "points".
    """

    def __init__(self, sprint: Sprint, metric: str = "hours"):
        self.sprint = sprint
        self.metric = metric  # "hours" or "points"

    # -- Data calculation ---------------------------------------------------

    def calculate(self) -> Dict:
        """
        Calculate burndown data.

        Returns:
            {
                "days": [0, 1, 2, ...],
                "ideal": [total, ..., 0],
                "actual": [total, ..., remaining],
                "metric": "hours" | "points",
                "total": <initial total>,
                "final_remaining": <end value>,
            }
        """
        days = list(range(0, self.sprint.duration_days + 1))
        logs = self.sprint.daily_logs

        if self.metric == "hours":
            total = self.sprint.backlog.total_hours_estimated
            remaining_key = "hours_remaining"
        else:
            total = self.sprint.backlog.total_points
            remaining_key = "points_remaining"

        # Ideal burndown: linear from total to 0
        ideal = [round(total - (total / self.sprint.duration_days) * d, 2) for d in days]

        # Actual burndown: from logs
        actual = [total]  # Day 0 = full total
        for log in logs:
            value = log.get(remaining_key, total)
            actual.append(round(value, 2))

        # Pad if sprint is not yet complete
        while len(actual) < len(days):
            actual.append(actual[-1])

        final_remaining = actual[-1] if actual else total

        return {
            "days": days,
            "ideal": ideal,
            "actual": actual,
            "metric": self.metric,
            "total": total,
            "final_remaining": final_remaining,
        }

    # -- Derived metrics ----------------------------------------------------

    def velocity_per_day(self) -> List[float]:
        """
        Calculate how much work was burned down each day.
        Positive = progress, negative = scope increase.
        """
        data = self.calculate()
        actual = data["actual"]
        deltas = []
        for i in range(1, len(actual)):
            delta = round(actual[i - 1] - actual[i], 2)
            deltas.append(delta)
        return deltas

    def trend_analysis(self) -> Dict:
        """
        Analyze whether the team is ahead, behind, or on track.
        """
        data = self.calculate()
        ideal = data["ideal"]
        actual = data["actual"]

        # Compare at each logged day
        comparisons = []
        for i in range(min(len(ideal), len(actual))):
            diff = round(actual[i] - ideal[i], 2)
            status = "on track" if abs(diff) < data["total"] * 0.05 else (
                "behind" if diff > 0 else "ahead"
            )
            comparisons.append({
                "day": i,
                "ideal": ideal[i],
                "actual": actual[i],
                "deviation": diff,
                "status": status,
            })

        # Overall assessment
        if not comparisons:
            overall = "no data"
        else:
            last = comparisons[-1]
            if last["status"] == "behind":
                pct_behind = round((last["deviation"] / max(data["total"], 1)) * 100, 1)
                overall = f"Behind schedule by {pct_behind}%"
            elif last["status"] == "ahead":
                pct_ahead = round((abs(last["deviation"]) / max(data["total"], 1)) * 100, 1)
                overall = f"Ahead of schedule by {pct_ahead}%"
            else:
                overall = "On track"

        return {
            "overall": overall,
            "daily_comparison": comparisons,
            "total_work": data["total"],
            "remaining": data["final_remaining"],
        }

    def projected_completion_day(self) -> Optional[int]:
        """
        Based on the average burn rate so far, project which day the
        sprint work will reach zero. Returns None if not enough data.
        """
        data = self.calculate()
        actual = data["actual"]

        if len(actual) < 2:
            return None

        # Average daily burn rate
        daily_burns = self.velocity_per_day()
        if not daily_burns:
            return None

        avg_burn = sum(daily_burns) / len(daily_burns)
        if avg_burn <= 0:
            return None  # No progress or going backwards

        remaining = actual[-1]
        days_needed = remaining / avg_burn
        current_day = len(daily_burns)
        projected = current_day + days_needed

        return round(projected)

    # -- Plotting -----------------------------------------------------------

    def plot(
        self,
        output_path: str = "output/burndown.png",
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 7),
        show: bool = False,
    ) -> str:
        """
        Render the burndown chart to a PNG file.

        Args:
            output_path: Where to save the image.
            title:       Chart title (auto-generated if None).
            figsize:     Figure size in inches.
            show:        If True, also display the chart interactively.

        Returns:
            Absolute path to the saved image.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")  # Non-interactive backend
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
        except ImportError:
            raise ImportError(
                "matplotlib is required for chart generation. "
                "Install it with: pip install matplotlib"
            )

        data = self.calculate()
        days = data["days"]
        ideal = data["ideal"]
        actual = data["actual"]
        metric_label = "Hours" if self.metric == "hours" else "Story Points"

        chart_title = title or f"{self.sprint.sprint_id} — Burndown Chart ({metric_label})"

        fig, ax = plt.subplots(figsize=figsize)

        # Plot ideal line
        ax.plot(
            days, ideal,
            color="#94A3B8",
            linewidth=2,
            linestyle="--",
            label="Ideal Burndown",
            marker="o",
            markersize=4,
        )

        # Plot actual line
        ax.plot(
            days, actual,
            color="#3B82F6",
            linewidth=2.5,
            label="Actual Remaining",
            marker="s",
            markersize=5,
        )

        # Fill the area between ideal and actual
        ax.fill_between(
            days,
            ideal,
            actual,
            where=[a > i for a, i in zip(actual, ideal)],
            alpha=0.15,
            color="#EF4444",
            label="Behind Schedule",
        )
        ax.fill_between(
            days,
            ideal,
            actual,
            where=[a <= i for a, i in zip(actual, ideal)],
            alpha=0.15,
            color="#22C55E",
            label="Ahead of Schedule",
        )

        # Projected completion line
        projected_day = self.projected_completion_day()
        if projected_day and projected_day != self.sprint.duration_days:
            ax.axvline(
                x=projected_day,
                color="#F59E0B",
                linewidth=1.5,
                linestyle=":",
                label=f"Projected Completion (Day {projected_day})",
            )

        # Sprint end line
        ax.axvline(
            x=self.sprint.duration_days,
            color="#6B7280",
            linewidth=1,
            linestyle="-.",
            alpha=0.5,
        )

        # Styling
        ax.set_title(chart_title, fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Sprint Day", fontsize=11)
        ax.set_ylabel(f"Remaining {metric_label}", fontsize=11)
        ax.set_xlim(0, self.sprint.duration_days)
        ax.set_ylim(0, max(max(ideal), max(actual)) * 1.1)
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xticks(days)

        # Add annotation for final remaining
        if len(actual) > 1:
            last_day = len(actual) - 1
            last_val = actual[-1]
            ax.annotate(
                f"{last_val:.1f} {metric_label.lower()} left",
                xy=(last_day, last_val),
                xytext=(last_day - 2, last_val + data["total"] * 0.1),
                fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#3B82F6"),
                color="#3B82F6",
                fontweight="bold",
            )

        plt.tight_layout()

        # Save
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(out), dpi=150, bbox_inches="tight")

        if show:
            plt.show()
        else:
            plt.close(fig)

        return str(out.resolve())

    # -- ASCII fallback -----------------------------------------------------

    def ascii_chart(self, width: int = 60, height: int = 20) -> str:
        """
        Generate a simple ASCII burndown chart for terminal output.
        Useful when matplotlib is not available.
        """
        data = self.calculate()
        ideal = data["ideal"]
        actual = data["actual"]
        max_val = max(max(ideal), max(actual), 1)

        lines = []
        lines.append(f"  Burndown: {self.sprint.sprint_id} ({self.metric})")
        lines.append(f"  {'=' * (width + 4)}")

        for row in range(height, -1, -1):
            threshold = (row / height) * max_val
            label = f"{threshold:6.1f} |"
            chars = []
            for col in range(len(ideal)):
                i_val = ideal[col] if col < len(ideal) else 0
                a_val = actual[col] if col < len(actual) else 0

                # Scale column position
                pos = int((col / max(len(ideal) - 1, 1)) * width)

                i_here = abs(i_val - threshold) < (max_val / height / 2)
                a_here = abs(a_val - threshold) < (max_val / height / 2)

                if i_here and a_here:
                    chars.append("X")
                elif i_here:
                    chars.append("-")
                elif a_here:
                    chars.append("*")
                else:
                    chars.append(" ")

            line = label + "".join(chars[:width])
            lines.append(line)

        lines.append(f"       +{''.join(['-'] * width)}")
        day_labels = "        " + "".join(
            f"D{d:<4}" for d in range(0, self.sprint.duration_days + 1, 2)
        )
        lines.append(day_labels)
        lines.append(f"  Legend: - Ideal  * Actual  X Both")

        return "\n".join(lines)
