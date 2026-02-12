"""
Incident Response Scenarios
============================

Pre-built incident scenarios for simulation and training.
Each scenario module provides a complete scenario definition with
decision trees, scoring criteria, and realistic attack narratives.

Available Scenarios:
    data_breach     - Data exfiltration and unauthorized data access
    ransomware      - Ransomware encryption and extortion attacks
    phishing        - Targeted phishing campaigns and credential theft
    ddos            - Distributed denial-of-service volumetric attacks
    insider_threat  - Malicious or negligent insider activity
"""

from src.scenarios.data_breach import DataBreachScenario
from src.scenarios.ransomware import RansomwareScenario
from src.scenarios.phishing import PhishingScenario
from src.scenarios.ddos import DDoSScenario
from src.scenarios.insider_threat import InsiderThreatScenario

SCENARIO_REGISTRY = {
    "data_breach": DataBreachScenario,
    "ransomware": RansomwareScenario,
    "phishing": PhishingScenario,
    "ddos": DDoSScenario,
    "insider_threat": InsiderThreatScenario,
}


def get_scenario(name: str):
    """Retrieve a scenario class by name."""
    scenario_cls = SCENARIO_REGISTRY.get(name)
    if scenario_cls is None:
        raise ValueError(
            f"Unknown scenario: '{name}'. "
            f"Available scenarios: {', '.join(SCENARIO_REGISTRY.keys())}"
        )
    return scenario_cls()


def list_scenarios():
    """Return metadata for all available scenarios."""
    result = []
    for name, cls in SCENARIO_REGISTRY.items():
        instance = cls()
        result.append({
            "name": name,
            "title": instance.title,
            "description": instance.description,
            "severity": instance.default_severity,
            "estimated_duration": instance.estimated_duration_minutes,
        })
    return result
