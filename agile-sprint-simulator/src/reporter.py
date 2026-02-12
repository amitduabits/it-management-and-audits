"""
reporter.py - Sprint Report Generation
========================================

Generates comprehensive sprint summary reports in two formats:
    - Markdown (.md) — for version control and documentation
    - HTML — for sharing with stakeholders

Reports include:
    - Sprint overview and goal
    - Velocity and completion metrics
    - Story-by-story breakdown
    - Team member performance
    - Burndown data summary
    - Blocker analysis
    - Retrospective highlights

Usage:
    from src.reporter import SprintReporter
    reporter = SprintReporter(sprint, retro_result)
    reporter.generate_markdown("output/sprint_report.md")
    reporter.generate_html("output/sprint_report.html")
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from .models import Sprint, StoryStatus
from .retrospective import RetroResult


class SprintReporter:
    """
    Generates sprint summary reports in Markdown and HTML.
    """

    def __init__(
        self,
        sprint: Sprint,
        retro_result: Optional[RetroResult] = None,
        burndown_image: Optional[str] = None,
    ):
        self.sprint = sprint
        self.retro = retro_result
        self.burndown_image = burndown_image

    # ======================================================================
    # MARKDOWN REPORT
    # ======================================================================

    def generate_markdown(self, output_path: str = "output/sprint_report.md") -> str:
        """Generate a full Markdown sprint report."""
        s = self.sprint
        lines: List[str] = []

        # Title
        lines.append(f"# {s.sprint_id} — Sprint Summary Report")
        lines.append(f"")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Sprint Dates:** {s.start_date.isoformat()} to {s.end_date.isoformat()}")
        lines.append(f"**Duration:** {s.duration_days} working days")
        lines.append(f"**Sprint Goal:** {s.goal}")
        if s.team:
            lines.append(f"**Team:** {s.team.name}")
        lines.append("")

        # -------------------------------------------------------------------
        lines.append("---")
        lines.append("")
        lines.append("## Sprint Metrics Overview")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Planned Velocity | {s.velocity} story points |")
        lines.append(f"| Committed Points | {s.backlog.total_points} |")
        lines.append(f"| Completed Points | {s.backlog.completed_points} |")
        lines.append(f"| Completion Rate | {s.backlog.completion_pct}% |")
        lines.append(f"| Stories Committed | {len(s.backlog.stories)} |")

        done_count = len(s.backlog.stories_by_status(StoryStatus.DONE))
        lines.append(f"| Stories Completed | {done_count} |")
        lines.append(f"| Total Task Hours | {round(s.backlog.total_hours_estimated, 1)} |")
        lines.append(f"| Remaining Hours | {round(s.backlog.total_hours_remaining, 1)} |")
        lines.append(f"| Blockers Logged | {len(s.blockers_log)} |")
        lines.append("")

        # -------------------------------------------------------------------
        lines.append("## Story Breakdown")
        lines.append("")
        lines.append("| ID | Title | Points | Priority | Status | Progress |")
        lines.append("|----|-------|--------|----------|--------|----------|")
        for story in s.backlog.stories:
            lines.append(
                f"| {story.story_id} | {story.title} | {story.story_points} | "
                f"{story.priority.value} | {story.status.value} | {story.progress_pct}% |"
            )
        lines.append("")

        # -------------------------------------------------------------------
        if s.team:
            lines.append("## Team Composition")
            lines.append("")
            lines.append("| Name | Role | Capacity (hrs/day) | Experience |")
            lines.append("|------|------|--------------------|------------|")
            for m in s.team.members:
                lines.append(
                    f"| {m.name} | {m.role.value} | {m.capacity_hours} | "
                    f"{m.experience_level} |"
                )
            lines.append("")

        # -------------------------------------------------------------------
        if self.retro:
            lines.append("## Retrospective Highlights")
            lines.append("")

            lines.append("### What Went Well")
            lines.append("")
            for item in self.retro.went_well:
                lines.append(f"- {item}")
            lines.append("")

            lines.append("### What To Improve")
            lines.append("")
            for item in self.retro.to_improve:
                lines.append(f"- {item}")
            lines.append("")

            lines.append("### Action Items")
            lines.append("")
            for i, item in enumerate(self.retro.action_items, 1):
                lines.append(f"{i}. {item}")
            lines.append("")

            lines.append(f"**Sprint Health Score:** {self.retro.health_score}/100")
            lines.append("")

        # -------------------------------------------------------------------
        if self.retro and self.retro.member_stats:
            lines.append("## Member Performance")
            lines.append("")
            lines.append("| Name | Role | Hours Worked | Tasks Done | Days Blocked | Score |")
            lines.append("|------|------|-------------|------------|--------------|-------|")
            for ms in self.retro.member_stats:
                lines.append(
                    f"| {ms['name']} | {ms['role']} | {ms['total_hours']} | "
                    f"{ms['tasks_completed']} | {ms['days_blocked']} | "
                    f"{ms['productivity_score']} |"
                )
            lines.append("")

        # -------------------------------------------------------------------
        if s.daily_logs:
            lines.append("## Daily Progress Log")
            lines.append("")
            lines.append("| Day | Date | Hours Remaining | Points Remaining | Stories Done | Blockers |")
            lines.append("|-----|------|-----------------|------------------|--------------|----------|")
            for log in s.daily_logs:
                lines.append(
                    f"| {log['day']} | {log.get('date', 'N/A')} | "
                    f"{log.get('hours_remaining', 'N/A')} | "
                    f"{log.get('points_remaining', 'N/A')} | "
                    f"{log.get('stories_done', 0)} | "
                    f"{log.get('active_blockers', 0)} |"
                )
            lines.append("")

        # -------------------------------------------------------------------
        if s.blockers_log:
            lines.append("## Blocker Log")
            lines.append("")
            lines.append("| Member | Blocker | Day Started | Expected Resolution | Severity |")
            lines.append("|--------|---------|-------------|---------------------|----------|")
            for b in s.blockers_log:
                lines.append(
                    f"| {b['member']} | {b['blocker'][:50]}... | "
                    f"Day {b['day_started']} | Day {b['expected_resolution_day']} | "
                    f"{b['severity']} |"
                )
            lines.append("")

        # -------------------------------------------------------------------
        if self.burndown_image:
            lines.append("## Burndown Chart")
            lines.append("")
            lines.append(f"![Burndown Chart]({self.burndown_image})")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Report generated by Agile Sprint Simulator v1.4.0*")
        lines.append("")

        content = "\n".join(lines)

        # Write to file
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(path.resolve())

    # ======================================================================
    # HTML REPORT
    # ======================================================================

    def generate_html(self, output_path: str = "output/sprint_report.html") -> str:
        """Generate a styled HTML sprint report."""
        s = self.sprint

        html_parts: List[str] = []

        html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{s.sprint_id} — Sprint Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f4f8;
            color: #1a202c;
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #2563eb, #1e40af);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .header p {{ opacity: 0.9; font-size: 0.95rem; }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #2563eb;
            font-size: 1.3rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        .metric-box {{
            background: #f7fafc;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            border-left: 4px solid #2563eb;
        }}
        .metric-box .value {{ font-size: 1.8rem; font-weight: 700; color: #2563eb; }}
        .metric-box .label {{ font-size: 0.85rem; color: #718096; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        th {{
            background: #edf2f7;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #cbd5e0;
        }}
        td {{
            padding: 0.65rem 0.75rem;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:hover {{ background: #f7fafc; }}
        .status-done {{ color: #22c55e; font-weight: 600; }}
        .status-progress {{ color: #3b82f6; font-weight: 600; }}
        .status-todo {{ color: #94a3b8; }}
        .status-blocked {{ color: #ef4444; font-weight: 600; }}
        .insight-list {{ list-style: none; padding: 0; }}
        .insight-list li {{
            padding: 0.5rem 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
        }}
        .went-well {{ background: #f0fdf4; border-left: 3px solid #22c55e; }}
        .to-improve {{ background: #fffbeb; border-left: 3px solid #f59e0b; }}
        .action-item {{ background: #eff6ff; border-left: 3px solid #3b82f6; }}
        .progress-bar {{
            background: #e2e8f0;
            border-radius: 4px;
            height: 8px;
            overflow: hidden;
        }}
        .progress-bar .fill {{
            background: #22c55e;
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s;
        }}
        .footer {{
            text-align: center;
            padding: 1.5rem;
            color: #94a3b8;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
<div class="container">
""")

        # Header
        html_parts.append(f"""
    <div class="header">
        <h1>{s.sprint_id} — Sprint Summary Report</h1>
        <p>Sprint Goal: {s.goal}</p>
        <p>{s.start_date.isoformat()} to {s.end_date.isoformat()} ({s.duration_days} days)
        {' | Team: ' + s.team.name if s.team else ''}</p>
    </div>
""")

        # Metrics cards
        done_count = len(s.backlog.stories_by_status(StoryStatus.DONE))
        html_parts.append(f"""
    <div class="card">
        <h2>Sprint Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-box">
                <div class="value">{s.backlog.completed_points}/{s.backlog.total_points}</div>
                <div class="label">Story Points Completed</div>
            </div>
            <div class="metric-box">
                <div class="value">{s.backlog.completion_pct}%</div>
                <div class="label">Completion Rate</div>
            </div>
            <div class="metric-box">
                <div class="value">{done_count}/{len(s.backlog.stories)}</div>
                <div class="label">Stories Completed</div>
            </div>
            <div class="metric-box">
                <div class="value">{s.velocity}</div>
                <div class="label">Planned Velocity</div>
            </div>
            <div class="metric-box">
                <div class="value">{len(s.blockers_log)}</div>
                <div class="label">Blockers Encountered</div>
            </div>
            <div class="metric-box">
                <div class="value">{round(s.backlog.total_hours_remaining, 1)}</div>
                <div class="label">Hours Remaining</div>
            </div>
        </div>
    </div>
""")

        # Story table
        story_rows = ""
        for story in s.backlog.stories:
            status_class = {
                "Done": "status-done",
                "In Progress": "status-progress",
                "To Do": "status-todo",
                "Blocked": "status-blocked",
            }.get(story.status.value, "")
            story_rows += f"""
            <tr>
                <td><strong>{story.story_id}</strong></td>
                <td>{story.title}</td>
                <td>{story.story_points}</td>
                <td>{story.priority.value}</td>
                <td class="{status_class}">{story.status.value}</td>
                <td>
                    <div class="progress-bar">
                        <div class="fill" style="width: {story.progress_pct}%"></div>
                    </div>
                    {story.progress_pct}%
                </td>
            </tr>"""

        html_parts.append(f"""
    <div class="card">
        <h2>Story Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Points</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Progress</th>
                </tr>
            </thead>
            <tbody>
                {story_rows}
            </tbody>
        </table>
    </div>
""")

        # Retrospective insights
        if self.retro:
            well_items = "\n".join(
                f'<li class="went-well">+ {item}</li>' for item in self.retro.went_well
            )
            improve_items = "\n".join(
                f'<li class="to-improve">- {item}</li>' for item in self.retro.to_improve
            )
            action_items = "\n".join(
                f'<li class="action-item">{i+1}. {item}</li>'
                for i, item in enumerate(self.retro.action_items)
            )

            html_parts.append(f"""
    <div class="card">
        <h2>Retrospective Highlights</h2>
        <h3 style="color:#22c55e; margin:1rem 0 0.5rem;">What Went Well</h3>
        <ul class="insight-list">{well_items}</ul>
        <h3 style="color:#f59e0b; margin:1rem 0 0.5rem;">What To Improve</h3>
        <ul class="insight-list">{improve_items}</ul>
        <h3 style="color:#3b82f6; margin:1rem 0 0.5rem;">Action Items</h3>
        <ul class="insight-list">{action_items}</ul>
        <p style="margin-top:1rem;"><strong>Sprint Health Score:</strong> {self.retro.health_score}/100</p>
    </div>
""")

        # Burndown image
        if self.burndown_image:
            html_parts.append(f"""
    <div class="card">
        <h2>Burndown Chart</h2>
        <img src="{self.burndown_image}" alt="Burndown Chart"
             style="max-width:100%; border-radius:8px;">
    </div>
""")

        # Footer
        html_parts.append(f"""
    <div class="footer">
        Report generated by Agile Sprint Simulator v1.4.0 on {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
</div>
</body>
</html>
""")

        content = "\n".join(html_parts)

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(path.resolve())
