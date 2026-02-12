"""
Interactive Incident Response Simulation Engine
=================================================

Presents scenario narratives, offers decision points, evaluates analyst
choices, tracks scoring, and provides detailed feedback. Designed for
tabletop exercises and individual IR training.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich import box

from src.models import (
    Incident, Alert, Evidence, TimelineEvent, Action,
    SeverityLevel, IncidentStatus, IncidentCategory,
    ActionType, EvidenceType,
)
from src.scenarios import get_scenario, list_scenarios
from src.timeline import TimelineGenerator
from src.severity_calculator import SeverityCalculator
from src.evidence_tracker import EvidenceTracker

console = Console()


class SimulationResult:
    """Stores the results of a completed simulation run."""

    def __init__(self, scenario_name: str, max_score: int):
        self.scenario_name = scenario_name
        self.max_score = max_score
        self.total_score = 0
        self.phase_scores: List[Dict[str, Any]] = []
        self.decisions_made: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.incident: Optional[Incident] = None

    def add_decision(self, phase: str, decision_id: str, choice_id: str,
                     score: int, feedback: str, choice_text: str) -> None:
        """Record a decision and its score."""
        self.decisions_made.append({
            "phase": phase,
            "decision_id": decision_id,
            "choice_id": choice_id,
            "choice_text": choice_text,
            "score": score,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
        })
        self.total_score += score

    def finalize(self) -> None:
        """Mark simulation as complete."""
        self.end_time = datetime.now()

    def get_percentage(self) -> float:
        """Calculate score as percentage."""
        if self.max_score == 0:
            return 0.0
        return round((self.total_score / self.max_score) * 100, 1)

    def get_rating(self) -> str:
        """Return performance rating based on score percentage."""
        pct = self.get_percentage()
        if pct >= 90:
            return "Expert"
        elif pct >= 70:
            return "Proficient"
        elif pct >= 50:
            return "Developing"
        else:
            return "Novice"

    def get_duration_minutes(self) -> int:
        """Return simulation duration in minutes."""
        end = self.end_time or datetime.now()
        return int((end - self.start_time).total_seconds() / 60)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result for reporting."""
        return {
            "scenario_name": self.scenario_name,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "percentage": self.get_percentage(),
            "rating": self.get_rating(),
            "duration_minutes": self.get_duration_minutes(),
            "decisions": self.decisions_made,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class IncidentSimulator:
    """Interactive incident response simulation engine."""

    def __init__(self):
        self.timeline_gen = TimelineGenerator()
        self.severity_calc = SeverityCalculator()
        self.evidence_tracker = EvidenceTracker()

    def run_simulation(self, scenario_name: str) -> SimulationResult:
        """Execute a full interactive simulation for the specified scenario."""
        scenario = get_scenario(scenario_name)
        result = SimulationResult(scenario_name, scenario.get_max_score())

        # Build the incident object
        incident = Incident(
            title=scenario.title,
            description=scenario.description,
            category=IncidentCategory(scenario.category),
            severity=SeverityLevel(scenario.default_severity),
            detected_at=datetime.now(),
            affected_systems=scenario.affected_systems,
            attack_vector=scenario.attack_vector,
        )
        for ioc in scenario.initial_iocs:
            incident.add_ioc(ioc["type"], ioc["value"], ioc.get("confidence", "high"))

        # Display scenario introduction
        self._display_intro(scenario, incident)

        # Run through each phase
        phases = scenario.get_phases()
        for phase_data in phases:
            phase_score = self._run_phase(phase_data, incident, result)
            result.phase_scores.append({
                "phase": phase_data["phase"],
                "title": phase_data["title"],
                "score": phase_score["earned"],
                "max_score": phase_score["max"],
            })

        # Finalize
        result.finalize()
        result.incident = incident
        incident.simulation_score = result.total_score

        # Display final results
        self._display_results(result, scenario)

        return result

    def _display_intro(self, scenario, incident: Incident) -> None:
        """Display the scenario introduction."""
        console.print()
        console.print(Panel(
            f"[bold white]{scenario.title}[/bold white]",
            style="red",
            box=box.DOUBLE,
            subtitle=f"Severity: {scenario.default_severity.upper()} | Est. Duration: {scenario.estimated_duration_minutes} min",
        ))
        console.print()

        console.print(Panel(
            scenario.description,
            title="[bold]SCENARIO BRIEFING[/bold]",
            style="yellow",
            box=box.ROUNDED,
        ))
        console.print()

        # Display affected systems
        systems_table = Table(title="Affected Systems", box=box.SIMPLE_HEAVY)
        systems_table.add_column("System", style="cyan")
        for system in scenario.affected_systems:
            systems_table.add_row(system)
        console.print(systems_table)
        console.print()

        # Display initial IOCs
        ioc_table = Table(title="Initial Indicators of Compromise", box=box.SIMPLE_HEAVY)
        ioc_table.add_column("Type", style="magenta", width=18)
        ioc_table.add_column("Value", style="white")
        ioc_table.add_column("Context", style="dim")
        for ioc in scenario.initial_iocs:
            ioc_table.add_row(ioc["type"], ioc["value"], ioc.get("context", ""))
        console.print(ioc_table)
        console.print()

        console.print("[bold green]The simulation will now begin. You will be presented with "
                      "decision points at each phase of the incident response.[/bold green]")
        console.print("[dim]Select the best response for each situation. Your choices will be scored.[/dim]")
        console.print()

    def _run_phase(self, phase_data: Dict[str, Any], incident: Incident,
                   result: SimulationResult) -> Dict[str, int]:
        """Execute a single phase of the simulation."""
        phase_earned = 0
        phase_max = 0

        # Phase header
        console.print(Panel(
            f"[bold]Phase {phase_data['phase_number']}: {phase_data['title']}[/bold]",
            style="blue",
            box=box.HEAVY,
        ))
        console.print()

        # Phase narrative
        console.print(Panel(
            phase_data["narrative"],
            title="[bold]SITUATION UPDATE[/bold]",
            style="white",
            box=box.ROUNDED,
        ))
        console.print()

        # Process each decision point
        for decision in phase_data["decisions"]:
            max_choice_score = max(c["score"] for c in decision["choices"])
            phase_max += max_choice_score

            score, feedback, choice_text = self._present_decision(decision)
            phase_earned += score

            result.add_decision(
                phase=phase_data["phase"],
                decision_id=decision["id"],
                choice_id="selected",
                score=score,
                feedback=feedback,
                choice_text=choice_text,
            )

            # Add timeline event for the decision
            incident.timeline.append(TimelineEvent(
                event_type="decision",
                description=f"[{phase_data['phase'].upper()}] {choice_text[:100]}",
                actor="analyst",
                phase=phase_data["phase"],
            ))

        # Phase summary
        pct = (phase_earned / phase_max * 100) if phase_max > 0 else 0
        color = "green" if pct >= 70 else "yellow" if pct >= 50 else "red"
        console.print(f"\n[{color}]Phase Score: {phase_earned}/{phase_max} ({pct:.0f}%)[/{color}]")
        console.print("=" * 60)
        console.print()

        return {"earned": phase_earned, "max": phase_max}

    def _present_decision(self, decision: Dict[str, Any]) -> tuple:
        """Present a decision point and collect the analyst's choice."""
        console.print(f"\n[bold yellow]DECISION POINT:[/bold yellow] {decision['prompt']}\n")

        # Display choices
        choices_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        choices_table.add_column("Option", style="bold cyan", width=4)
        choices_table.add_column("Action", style="white")

        choice_map = {}
        for i, choice in enumerate(decision["choices"]):
            letter = choice["id"].upper()
            choices_table.add_row(f"[{letter}]", choice["text"])
            choice_map[choice["id"]] = choice
            choice_map[letter] = choice
            choice_map[str(i + 1)] = choice

        console.print(choices_table)
        console.print()

        # Get user input
        valid_keys = [c["id"].upper() for c in decision["choices"]]
        while True:
            answer = Prompt.ask(
                f"[bold]Your choice[/bold] ({'/'.join(valid_keys)})",
            ).strip().upper()

            # Accept letter or number
            if answer in choice_map:
                selected = choice_map[answer]
                break
            elif answer.lower() in choice_map:
                selected = choice_map[answer.lower()]
                break
            else:
                console.print(f"[red]Invalid choice. Please enter one of: {', '.join(valid_keys)}[/red]")

        # Display feedback
        score = selected["score"]
        max_score = max(c["score"] for c in decision["choices"])

        if score == max_score:
            style = "green"
            icon = "[+]"
        elif score >= max_score * 0.5:
            style = "yellow"
            icon = "[~]"
        else:
            style = "red"
            icon = "[-]"

        console.print(Panel(
            f"{icon} Score: {score}/{max_score}\n\n{selected['feedback']}\n\n"
            f"[dim]What happens next: {selected.get('next_action', 'Proceeding to next step.')}[/dim]",
            title="[bold]FEEDBACK[/bold]",
            style=style,
            box=box.ROUNDED,
        ))

        return score, selected["feedback"], selected["text"]

    def _display_results(self, result: SimulationResult, scenario) -> None:
        """Display the final simulation results."""
        console.print()
        console.print(Panel(
            "[bold white]SIMULATION COMPLETE[/bold white]",
            style="blue",
            box=box.DOUBLE,
        ))
        console.print()

        # Score summary
        pct = result.get_percentage()
        rating = result.get_rating()

        if pct >= 90:
            rating_color = "green"
        elif pct >= 70:
            rating_color = "yellow"
        elif pct >= 50:
            rating_color = "bright_yellow"
        else:
            rating_color = "red"

        score_table = Table(title="Final Score Summary", box=box.DOUBLE_EDGE)
        score_table.add_column("Metric", style="bold")
        score_table.add_column("Value", justify="right")
        score_table.add_row("Total Score", f"{result.total_score}/{result.max_score}")
        score_table.add_row("Percentage", f"{pct}%")
        score_table.add_row("Rating", f"[{rating_color}]{rating}[/{rating_color}]")
        score_table.add_row("Duration", f"{result.get_duration_minutes()} minutes")
        score_table.add_row("Decisions Made", str(len(result.decisions_made)))
        console.print(score_table)
        console.print()

        # Phase breakdown
        phase_table = Table(title="Phase Breakdown", box=box.SIMPLE_HEAVY)
        phase_table.add_column("Phase", style="cyan")
        phase_table.add_column("Score", justify="right")
        phase_table.add_column("Percentage", justify="right")
        for ps in result.phase_scores:
            p_pct = (ps["score"] / ps["max_score"] * 100) if ps["max_score"] > 0 else 0
            p_color = "green" if p_pct >= 70 else "yellow" if p_pct >= 50 else "red"
            phase_table.add_row(
                ps["title"],
                f"{ps['score']}/{ps['max_score']}",
                f"[{p_color}]{p_pct:.0f}%[/{p_color}]",
            )
        console.print(phase_table)
        console.print()

        # Scoring rubric
        rubric = scenario.get_scoring_rubric()
        console.print("[bold]Scoring Rubric:[/bold]")
        for level, description in rubric.items():
            console.print(f"  {level.capitalize()}: {description}")
        console.print()

        # Areas for improvement
        weak_phases = [ps for ps in result.phase_scores
                       if ps["max_score"] > 0 and (ps["score"] / ps["max_score"]) < 0.7]
        if weak_phases:
            console.print("[bold yellow]Areas for Improvement:[/bold yellow]")
            for wp in weak_phases:
                console.print(f"  - Review the {wp['phase']} phase in the corresponding playbook")
            console.print()

    def list_available_scenarios(self) -> List[Dict[str, Any]]:
        """Return metadata for all available scenarios."""
        return list_scenarios()

    def display_scenario_list(self) -> None:
        """Display a formatted list of available scenarios."""
        scenarios = self.list_available_scenarios()

        table = Table(title="Available Incident Response Scenarios", box=box.DOUBLE_EDGE)
        table.add_column("Name", style="cyan", width=18)
        table.add_column("Title", style="white")
        table.add_column("Severity", style="red", width=10)
        table.add_column("Duration", justify="right", width=12)

        for s in scenarios:
            sev_color = {
                "critical": "red",
                "high": "bright_red",
                "medium": "yellow",
                "low": "green",
            }.get(s["severity"], "white")

            table.add_row(
                s["name"],
                s["title"],
                f"[{sev_color}]{s['severity'].upper()}[/{sev_color}]",
                f"{s['estimated_duration']} min",
            )

        console.print(table)
