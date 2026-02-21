"""
Tests for the Incident Response Simulation Engine.

Validates scenario loading, decision tree structure, scoring logic,
and simulation result generation.
"""

import sys
import os
import pytest
from datetime import datetime

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Incident, Alert, Evidence, TimelineEvent, Action,
    SeverityLevel, IncidentStatus, IncidentCategory,
    ActionType, EvidenceType, ActionPriority,
)
from src.scenarios import get_scenario, list_scenarios, SCENARIO_REGISTRY
from src.scenarios.data_breach import DataBreachScenario
from src.scenarios.ransomware import RansomwareScenario
from src.scenarios.phishing_campaign import PhishingScenario
from src.scenarios.ddos_attack import DDoSScenario
from src.scenarios.insider_threat import InsiderThreatScenario
from src.simulator import SimulationResult
from src.timeline import TimelineGenerator
from src.evidence_tracker import EvidenceTracker


class TestScenarioRegistry:
    """Tests for scenario registration and retrieval."""

    def test_all_scenarios_registered(self):
        """All five scenario types should be registered."""
        expected = {"data_breach", "ransomware", "phishing", "ddos", "insider_threat"}
        assert set(SCENARIO_REGISTRY.keys()) == expected

    def test_get_scenario_valid(self):
        """get_scenario should return a valid scenario instance."""
        for name in SCENARIO_REGISTRY:
            scenario = get_scenario(name)
            assert scenario is not None
            assert hasattr(scenario, "name")
            assert hasattr(scenario, "title")
            assert hasattr(scenario, "description")
            assert hasattr(scenario, "get_phases")
            assert hasattr(scenario, "get_max_score")

    def test_get_scenario_invalid(self):
        """get_scenario should raise ValueError for unknown scenario names."""
        with pytest.raises(ValueError, match="Unknown scenario"):
            get_scenario("nonexistent_scenario")

    def test_list_scenarios_returns_all(self):
        """list_scenarios should return metadata for all registered scenarios."""
        scenarios = list_scenarios()
        assert len(scenarios) == 5
        for s in scenarios:
            assert "name" in s
            assert "title" in s
            assert "description" in s
            assert "severity" in s
            assert "estimated_duration" in s


class TestScenarioStructure:
    """Tests for scenario decision tree structure integrity."""

    @pytest.fixture(params=list(SCENARIO_REGISTRY.keys()))
    def scenario(self, request):
        """Parametrized fixture providing each scenario instance."""
        return get_scenario(request.param)

    def test_scenario_has_phases(self, scenario):
        """Every scenario must have at least 4 phases."""
        phases = scenario.get_phases()
        assert len(phases) >= 4, f"{scenario.name} has fewer than 4 phases"

    def test_phases_have_required_fields(self, scenario):
        """Each phase must have required fields."""
        for phase in scenario.get_phases():
            assert "phase" in phase, f"Missing 'phase' key in {scenario.name}"
            assert "phase_number" in phase
            assert "title" in phase
            assert "narrative" in phase
            assert "decisions" in phase
            assert isinstance(phase["decisions"], list)

    def test_decisions_have_choices(self, scenario):
        """Each decision point must have at least 2 choices."""
        for phase in scenario.get_phases():
            for decision in phase["decisions"]:
                assert "id" in decision
                assert "prompt" in decision
                assert "choices" in decision
                assert len(decision["choices"]) >= 2, (
                    f"Decision {decision['id']} in {scenario.name} has fewer than 2 choices"
                )

    def test_choices_have_required_fields(self, scenario):
        """Each choice must have id, text, score, and feedback."""
        for phase in scenario.get_phases():
            for decision in phase["decisions"]:
                for choice in decision["choices"]:
                    assert "id" in choice
                    assert "text" in choice
                    assert "score" in choice
                    assert "feedback" in choice
                    assert isinstance(choice["score"], (int, float))
                    assert choice["score"] >= 0

    def test_max_score_positive(self, scenario):
        """Max score must be a positive integer."""
        max_score = scenario.get_max_score()
        assert max_score > 0, f"{scenario.name} max score is not positive"

    def test_scoring_rubric_has_levels(self, scenario):
        """Scoring rubric must define performance levels."""
        rubric = scenario.get_scoring_rubric()
        assert "expert" in rubric
        assert "proficient" in rubric
        assert "developing" in rubric
        assert "novice" in rubric

    def test_optimal_choice_exists(self, scenario):
        """Each decision must have at least one choice with maximum score."""
        for phase in scenario.get_phases():
            for decision in phase["decisions"]:
                scores = [c["score"] for c in decision["choices"]]
                max_score = max(scores)
                assert max_score >= 8, (
                    f"Decision {decision['id']} in {scenario.name}: "
                    f"highest score is only {max_score}"
                )

    def test_has_initial_iocs(self, scenario):
        """Each scenario should have initial IOCs defined."""
        assert hasattr(scenario, "initial_iocs")
        assert len(scenario.initial_iocs) >= 2

    def test_has_affected_systems(self, scenario):
        """Each scenario should have affected systems defined."""
        assert hasattr(scenario, "affected_systems")
        assert len(scenario.affected_systems) >= 1


class TestSimulationResult:
    """Tests for SimulationResult scoring and metrics."""

    def test_initial_state(self):
        """New SimulationResult should have zero score."""
        result = SimulationResult("test_scenario", 100)
        assert result.total_score == 0
        assert result.max_score == 100
        assert result.get_percentage() == 0.0
        assert result.get_rating() == "Novice"

    def test_add_decision(self):
        """Adding a decision should increase total score."""
        result = SimulationResult("test", 100)
        result.add_decision("detection", "det_1", "a", 10, "Good job", "Validate alert")
        assert result.total_score == 10
        assert len(result.decisions_made) == 1

    def test_multiple_decisions(self):
        """Multiple decisions should accumulate scores."""
        result = SimulationResult("test", 100)
        result.add_decision("detection", "det_1", "a", 10, "Good", "Choice A")
        result.add_decision("triage", "tri_1", "a", 10, "Good", "Choice A")
        result.add_decision("containment", "con_1", "b", 5, "Partial", "Choice B")
        assert result.total_score == 25
        assert len(result.decisions_made) == 3

    def test_percentage_calculation(self):
        """Percentage should be calculated correctly."""
        result = SimulationResult("test", 80)
        result.add_decision("d", "d1", "a", 60, "f", "t")
        assert result.get_percentage() == 75.0

    def test_rating_expert(self):
        """Score >= 90% should rate as Expert."""
        result = SimulationResult("test", 100)
        result.add_decision("d", "d1", "a", 95, "f", "t")
        assert result.get_rating() == "Expert"

    def test_rating_proficient(self):
        """Score 70-89% should rate as Proficient."""
        result = SimulationResult("test", 100)
        result.add_decision("d", "d1", "a", 75, "f", "t")
        assert result.get_rating() == "Proficient"

    def test_rating_developing(self):
        """Score 50-69% should rate as Developing."""
        result = SimulationResult("test", 100)
        result.add_decision("d", "d1", "a", 55, "f", "t")
        assert result.get_rating() == "Developing"

    def test_rating_novice(self):
        """Score < 50% should rate as Novice."""
        result = SimulationResult("test", 100)
        result.add_decision("d", "d1", "a", 30, "f", "t")
        assert result.get_rating() == "Novice"

    def test_finalize(self):
        """Finalize should set end time."""
        result = SimulationResult("test", 100)
        assert result.end_time is None
        result.finalize()
        assert result.end_time is not None

    def test_duration(self):
        """Duration should be non-negative after finalize."""
        result = SimulationResult("test", 100)
        result.finalize()
        assert result.get_duration_minutes() >= 0

    def test_to_dict(self):
        """Serialization should produce valid dictionary."""
        result = SimulationResult("data_breach", 80)
        result.add_decision("detection", "det_1", "a", 10, "Good", "Validate")
        result.finalize()
        d = result.to_dict()
        assert d["scenario_name"] == "data_breach"
        assert d["total_score"] == 10
        assert d["max_score"] == 80
        assert "decisions" in d
        assert len(d["decisions"]) == 1

    def test_zero_max_score_percentage(self):
        """Percentage with zero max score should return 0."""
        result = SimulationResult("test", 0)
        assert result.get_percentage() == 0.0


class TestIncidentModel:
    """Tests for the Incident data model."""

    def test_incident_creation(self):
        """Incident should be created with default values."""
        incident = Incident(title="Test Incident")
        assert incident.title == "Test Incident"
        assert incident.status == IncidentStatus.NEW
        assert incident.severity == SeverityLevel.MEDIUM
        assert incident.incident_id.startswith("INC-")

    def test_severity_escalation(self):
        """Escalating severity should update and log a timeline event."""
        incident = Incident(title="Test")
        incident.escalate_severity(SeverityLevel.CRITICAL, "Confirmed exfiltration")
        assert incident.severity == SeverityLevel.CRITICAL
        assert len(incident.timeline) == 1
        assert "severity_change" in incident.timeline[0].event_type

    def test_status_advancement(self):
        """Advancing status should update and log a timeline event."""
        incident = Incident(title="Test")
        incident.advance_status(IncidentStatus.INVESTIGATING)
        assert incident.status == IncidentStatus.INVESTIGATING
        assert len(incident.timeline) == 1

    def test_close_incident(self):
        """Closing should set closed_at timestamp."""
        incident = Incident(title="Test")
        assert incident.closed_at is None
        incident.advance_status(IncidentStatus.CLOSED)
        assert incident.closed_at is not None

    def test_add_ioc(self):
        """IOCs should be properly added."""
        incident = Incident(title="Test")
        incident.add_ioc("ip", "192.168.1.1", "high")
        assert len(incident.iocs) == 1
        assert incident.iocs[0]["type"] == "ip"
        assert incident.iocs[0]["value"] == "192.168.1.1"

    def test_to_dict(self):
        """Serialization should produce a complete dictionary."""
        incident = Incident(
            title="Test Incident",
            category=IncidentCategory.DATA_BREACH,
            severity=SeverityLevel.HIGH,
        )
        d = incident.to_dict()
        assert d["title"] == "Test Incident"
        assert d["category"] == "data_breach"
        assert d["severity"] == "high"
        assert "incident_id" in d


class TestTimelineGenerator:
    """Tests for the timeline generator."""

    def test_generate_timeline(self):
        """Generated timeline should have events for all phases."""
        gen = TimelineGenerator()
        events = gen.generate_scenario_timeline()
        assert len(events) > 0

        phases = set(e.phase for e in events)
        expected_phases = {"detection", "triage", "containment", "eradication", "recovery", "post_incident"}
        assert phases == expected_phases

    def test_timeline_sorted(self):
        """Timeline events should be sorted by timestamp."""
        gen = TimelineGenerator()
        events = gen.generate_scenario_timeline()
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp

    def test_add_custom_event(self):
        """Custom events should be insertable."""
        gen = TimelineGenerator()
        gen.generate_scenario_timeline()
        event = gen.add_custom_event(
            description="Custom test event",
            phase="containment",
            actor="Test Analyst",
        )
        assert event in gen.events
        assert event.description == "Custom test event"

    def test_get_events_by_phase(self):
        """Phase filtering should return only events from that phase."""
        gen = TimelineGenerator()
        gen.generate_scenario_timeline()
        detection_events = gen.get_events_by_phase("detection")
        assert all(e.phase == "detection" for e in detection_events)

    def test_format_timeline(self):
        """Formatted timeline should be a non-empty string."""
        gen = TimelineGenerator()
        gen.generate_scenario_timeline()
        formatted = gen.format_timeline()
        assert isinstance(formatted, str)
        assert "INCIDENT TIMELINE" in formatted


class TestEvidenceTracker:
    """Tests for the evidence tracking system."""

    def test_register_evidence(self):
        """Registering evidence should create an item with an ID."""
        tracker = EvidenceTracker()
        ev = tracker.register_evidence(
            evidence_type="log_file",
            description="Web server access log",
            collected_by="Analyst A",
            source_system="web-prod-01",
            file_hash_sha256="abc123def456",
        )
        assert ev.evidence_id.startswith("EV-")
        assert ev.evidence_type == EvidenceType.LOG_FILE
        assert len(ev.chain_of_custody) == 1

    def test_transfer_custody(self):
        """Custody transfer should be recorded."""
        tracker = EvidenceTracker()
        ev = tracker.register_evidence(
            evidence_type="disk_image",
            description="Disk image",
            collected_by="Analyst A",
            source_system="server-01",
        )
        result = tracker.transfer_custody(ev.evidence_id, "Analyst A", "Analyst B", "For analysis")
        assert result is True
        assert len(ev.chain_of_custody) == 2

    def test_transfer_custody_invalid_id(self):
        """Custody transfer with invalid ID should return False."""
        tracker = EvidenceTracker()
        result = tracker.transfer_custody("FAKE-ID", "A", "B", "test")
        assert result is False

    def test_verify_integrity_pass(self):
        """Integrity check with matching hash should pass."""
        tracker = EvidenceTracker()
        ev = tracker.register_evidence(
            evidence_type="memory_dump",
            description="Memory dump",
            collected_by="Analyst A",
            source_system="server-01",
            file_hash_sha256="abc123",
        )
        result = tracker.verify_integrity(ev.evidence_id, "abc123", "sha256")
        assert result["verified"] is True

    def test_verify_integrity_fail(self):
        """Integrity check with mismatched hash should fail."""
        tracker = EvidenceTracker()
        ev = tracker.register_evidence(
            evidence_type="memory_dump",
            description="Memory dump",
            collected_by="Analyst A",
            source_system="server-01",
            file_hash_sha256="abc123",
        )
        result = tracker.verify_integrity(ev.evidence_id, "xyz789", "sha256")
        assert result["verified"] is False

    def test_get_evidence_by_type(self):
        """Filtering by type should return matching items."""
        tracker = EvidenceTracker()
        tracker.register_evidence("log_file", "Log 1", "A", "srv1")
        tracker.register_evidence("log_file", "Log 2", "A", "srv2")
        tracker.register_evidence("disk_image", "Disk 1", "A", "srv1")
        logs = tracker.get_evidence_by_type("log_file")
        assert len(logs) == 2

    def test_evidence_summary(self):
        """Summary should aggregate evidence metadata."""
        tracker = EvidenceTracker()
        tracker.register_evidence("log_file", "Log", "A", "srv1", file_hash_sha256="h1")
        tracker.register_evidence("disk_image", "Disk", "A", "srv2")
        summary = tracker.generate_evidence_summary()
        assert summary["total"] == 2
        assert "log_file" in summary["by_type"]
        assert summary["verified_count"] == 1

    def test_collection_order_guidance(self):
        """Collection order guidance should have 8 priority levels."""
        guidance = EvidenceTracker.get_collection_order_guidance()
        assert len(guidance) == 8
        assert guidance[0]["priority"] == "1 (Highest)"
        assert guidance[7]["priority"] == "8 (Lowest)"


class TestActionModel:
    """Tests for the Action data model."""

    def test_action_lifecycle(self):
        """Action should transition through start and complete states."""
        action = Action(
            title="Isolate network segment",
            action_type=ActionType.CONTAINMENT,
            priority=ActionPriority.IMMEDIATE,
        )
        assert action.status == "pending"

        action.start()
        assert action.status == "in_progress"
        assert action.started_at is not None

        action.complete("Network isolated successfully", effectiveness=0.9)
        assert action.status == "completed"
        assert action.completed_at is not None
        assert action.effectiveness_score == 0.9

    def test_effectiveness_clamping(self):
        """Effectiveness score should be clamped between 0 and 1."""
        action = Action(title="Test")
        action.start()
        action.complete("Done", effectiveness=1.5)
        assert action.effectiveness_score == 1.0

        action2 = Action(title="Test2")
        action2.start()
        action2.complete("Done", effectiveness=-0.5)
        assert action2.effectiveness_score == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
